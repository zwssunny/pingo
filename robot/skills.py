# encoding:utf-8
"""技能知识库检索

聊天机器人兜底（NLU 找不到意图）时，从 `skills/<技能名>/` 目录读取 Markdown 资料，
按关键词命中情况挑出最相关的参考文件，拼成一段 system 消息注入聊天机器人，
让兜底回答有据可依、不编造数字、答不了就明说并引导到相关板块。

资料本身来自 Claude Code 的 skill 目录约定：
    skills/fusion-platform/SKILL.md          正文 + 「检索表」+「回答守则」
    skills/fusion-platform/references/*.md   各板块原文

本模块不依赖 config.json 是否加载过（未加载时按内置默认值工作），
因此可以直接 `python -m robot.skills "公交"` 调参。
"""

import os
import re
import time
import threading

from common.log import logger
from config import conf, get_root

# 默认配置，与 config.py 的 available_setting["skill"] 保持一致
DEFAULTS = {
    "enable": True,
    "root": "./skills",
    "name": "fusion-platform",
    "min_score": 2.0,
    "max_files": 2,
    "max_chars": 4000,
    "default_reference": "references/00-平台首页.md",
    "reload_interval": 5.0,
}

# 关键词权重：检索表 / 一级标题 / 二级标题
W_TABLE, W_TITLE, W_HEAD = 3.0, 3.0, 2.0
# 出现在多大比例的文档里的词算通用词，直接丢弃（如「首页」出现在每一行检索表里）
DF_DROP_RATIO = 0.6
# 关键词最短长度
MIN_TERM_LEN = 2
# 单篇文档最少给多少字符预算
MIN_DOC_CHARS = 300
# 单篇文档最多取几个章节
MAX_SECTIONS = 4
# 第二篇文档可用预算小于该值时不再注入
MIN_SECOND_DOC_CHARS = 300
# prompt 里参考资料之外的部分（角色、守则、规则、板块列表、标题）预留的长度上限
PROMPT_OVERHEAD = 900

# 关键词切分符：中文顿号/逗号/分号/斜杠/空白，SKILL.md 里用「/」做组内分隔（公交/地铁/巡游车）
_TERM_SPLIT_RE = re.compile(r"[、，,；;：:／/|｜\s]+")
# 行尾括号说明：「公交（二级页面）」-> 「公交」
_TAIL_PAREN_RE = re.compile(r"[（(][^）)]*[）)]\s*$")
# 文件名前缀：「01-城市交通」-> 「城市交通」
_FILE_PREFIX_RE = re.compile(r"^\d+[-_]\s*")

# 抽取「回答守则」失败时的兜底守则
FALLBACK_GUIDE = (
    "1. 忠于原文。平台功能、页面构成、数据指标一律以参考资料为准，不得添加资料里没有的功能、指标或数据。\n"
    "2. 不编造数字。数字只能引用参考资料中出现的，资料没写的一律不补。\n"
    "3. 标注出处。回答时指明来自哪个板块、哪个页面。\n"
    "4. 保留讲解口吻。语气专业、平实，以业务价值收尾。"
)

ROLE_TEXT = (
    '你是"广州市交通运输局融合平台"演示现场的语音讲解助手，'
    "你的回答会被语音合成后当场播报。"
)
EXTRA_RULES = (
    "- 语音友好：整段回答不超过 120 字，用完整短句；不要输出 Markdown 标记、表格、链接、"
    "emoji、标题符号或编号列表。\n"
    '- 资料未覆盖时：先明确说"这部分内容演示脚本里没有介绍"，再把用户引导到下方可选板块中'
    "相关的板块或页面，绝不自行发挥或估算。\n"
    "- 数字只使用参考资料中出现的，资料没写的数字一律不补。"
)


def _split_terms(text):
    """把一段关键词文本切分成词表"""
    text = text.replace("**", "").replace("＊", "")
    terms = []
    for item in _TERM_SPLIT_RE.split(text):
        item = item.strip().strip("　").strip()
        # 去掉「等」「、」之类的残渣和过短的词
        if len(item) < MIN_TERM_LEN:
            continue
        terms.append(item)
    return terms


def _heading_terms(heading):
    """章节标题 -> 关键词集合，如「公交（二级页面）」-> {公交（二级页面）, 公交}"""
    terms = set()
    heading = heading.strip()
    if len(heading) >= MIN_TERM_LEN:
        terms.add(heading)
    stripped = _TAIL_PAREN_RE.sub("", heading).strip()
    if len(stripped) >= MIN_TERM_LEN:
        terms.add(stripped)
    return terms


def _len_bonus(term):
    """长词加权：2字 1.0、3字 1.25、4字 1.5、6字及以上 2.0

    用于消歧：问「客运执法」时应命中交通执法，而不是被道路运输的「客运」抢走。
    """
    return 1.0 + 0.25 * min(max(len(term) - 2, 0), 4)


def _score_terms(terms, query):
    """中文不需要分词，直接用子串匹配"""
    score = 0.0
    for term, weight in terms.items():
        if term in query:
            score += weight * _len_bonus(term)
    return score


def _parse_frontmatter(text):
    """极简 frontmatter 解析（只有 name / description 两个单行字段），不引入 yaml 依赖"""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    meta = {}
    for line in text[3:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
    return meta, text[end + 4:].lstrip("\n")


def _parse_index_table(skill_md):
    """解析 SKILL.md 里的「检索表」：关键词 -> 参考文件相对路径"""
    lines = skill_md.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("#") and "检索表" in line:
            start = i + 1
            break
    if start is None:
        return {}
    mapping = {}
    for line in lines[start:]:
        line = line.strip()
        if not line:
            continue
        if not line.startswith("|"):
            if mapping:  # 表格结束
                break
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2 or set(cells[0]) <= set("-: "):
            continue
        path_match = re.search(r"\((references/[^)]+)\)", cells[1])
        if not path_match:
            continue
        rel_path = path_match.group(1).strip()
        terms = _split_terms(cells[0])
        if terms:
            mapping.setdefault(rel_path, []).extend(terms)
    return mapping


def _extract_section(skill_md, title_keyword):
    """抽取 SKILL.md 里某个二级标题下的正文"""
    lines = skill_md.splitlines()
    body = []
    collecting = False
    for line in lines:
        if line.startswith("## "):
            if collecting:
                break
            collecting = title_keyword in line
            continue
        if collecting:
            body.append(line)
    text = "\n".join(body).strip()
    # 去掉多余空行
    return re.sub(r"\n{3,}", "\n\n", text)


def _extract_triggers(meta):
    """从 frontmatter 的 description 里取「触发词：」之后的部分"""
    desc = meta.get("description", "")
    pos = desc.rfind("触发词")
    if pos == -1:
        return []
    tail = desc[pos:]
    tail = tail.split("：", 1)[1] if "：" in tail else tail
    return _split_terms(tail)


class SkillSection(object):
    """参考文件里的一个 `## ` 章节"""

    __slots__ = ("heading", "body", "terms")

    def __init__(self, heading, body):
        self.heading = heading
        self.body = body.strip()
        self.terms = {term: W_HEAD for term in _heading_terms(heading)}


class SkillDoc(object):
    """一个参考文件"""

    def __init__(self, rel_path, title, preamble, sections):
        self.rel_path = rel_path
        self.title = title
        self.preamble = preamble.strip()
        self.sections = sections
        self.terms = {}  # term -> 权重

    def add_terms(self, terms, weight):
        """同名词取较大权重，避免标题与检索表重复累加"""
        for term in terms:
            if len(term) < MIN_TERM_LEN:
                continue
            if weight > self.terms.get(term, 0):
                self.terms[term] = weight

    def score(self, query):
        return _score_terms(self.terms, query)

    def _heading_score(self, section, query):
        return _score_terms(section.terms, query)

    def _body_score(self, section, query):
        """问句里的检索表关键词在该章节正文中出现了几次，用于标题没直接命中时选章节"""
        score = 0.0
        for term, weight in self.terms.items():
            if weight >= W_TABLE and term in query and term in section.body:
                score += 0.5 * weight * _len_bonus(term)
        return score

    def render(self, query, budget):
        """按预算渲染正文：先纲要，再取最相关的几个章节（保持原文顺序）。返回 (正文, 是否截断)"""
        if budget <= 0:
            return "", True
        # 优先按标题选章节（资料里每个「## XX（二级页面）」就是一个主题）；
        # 标题都没命中时才退而看正文提到过什么
        hits = [(section, self._heading_score(section, query)) for section in self.sections]
        hits = [(section, score) for section, score in hits if score > 0]
        if not hits:
            hits = [(section, self._body_score(section, query)) for section in self.sections]
            hits = [(section, score) for section, score in hits if score > 0]

        if hits:
            hits.sort(key=lambda item: -item[1])
            keep = {id(section) for section, _ in hits[:MAX_SECTIONS]}
            # 恢复原文顺序，读起来才像讲解词
            picked = [section for section in self.sections if id(section) in keep]
        else:
            # 只命中了检索表里的宏观词，按原文顺序取
            picked = list(self.sections)

        parts = []
        used = 0
        if self.preamble:
            parts.append(self.preamble)
            used += len(self.preamble)
        truncated = False
        for section in picked:
            block = "{}\n{}".format(section.heading, section.body).strip()
            if not block:
                continue
            if used + len(block) > budget:
                truncated = True
                if not parts:
                    # 一段正文都还没放，硬截一段，保证有内容可答
                    remain = budget - used
                    if remain > 60:
                        parts.append(block[:remain])
                break
            parts.append(block)
            used += len(block)
        return "\n\n".join(parts).strip(), truncated


class SkillPack(object):
    """一个技能目录（skills/fusion-platform）"""

    def __init__(self, name, triggers, guide, board_titles, docs, default_doc, fingerprint):
        self.name = name
        self.triggers = triggers
        self.guide = guide
        self.board_titles = board_titles
        self.docs = docs
        self.default_doc = default_doc
        self.fingerprint = fingerprint

    @classmethod
    def load(cls, skill_dir, default_reference=""):
        fingerprint = _fingerprint(skill_dir)
        skill_md_path = os.path.join(skill_dir, "SKILL.md")
        with open(skill_md_path, "r", encoding="utf-8") as f:
            skill_md = f.read()

        meta, body = _parse_frontmatter(skill_md)
        name = meta.get("name") or os.path.basename(skill_dir)
        triggers = _extract_triggers(meta)

        guide = _extract_section(body, "回答守则")
        if len(guide) < 40:
            logger.warning("[skill] 未能从 SKILL.md 抽取「回答守则」，使用内置守则")
            guide = FALLBACK_GUIDE

        table = _parse_index_table(body)  # rel_path -> [关键词]

        docs = []
        refs_dir = os.path.join(skill_dir, "references")
        filenames = sorted(os.listdir(refs_dir)) if os.path.isdir(refs_dir) else []
        for filename in filenames:
            if not filename.lower().endswith(".md"):
                continue
            rel_path = "references/" + filename
            try:
                doc = _load_doc(refs_dir, filename, rel_path, table.get(rel_path, []))
            except Exception as e:
                logger.warning("[skill] 参考文件读取失败，已跳过：%s（%s）", rel_path, e)
                continue
            if doc:
                docs.append(doc)

        _apply_df_filter(docs)

        default_doc = None
        if default_reference:
            for doc in docs:
                if doc.rel_path == default_reference:
                    default_doc = doc
                    break
        if default_doc is None and docs:
            default_doc = docs[0]

        logger.info(
            "[skill] 加载技能 %s：%d 个参考文件，%d 个触发词",
            name, len(docs), len(triggers),
        )
        return cls(name, triggers, guide, [d.title for d in docs], docs, default_doc, fingerprint)

    def match(self, query):
        """返回按得分降序排列的 (文档, 得分)"""
        scored = [(doc, doc.score(query)) for doc in self.docs]
        scored.sort(key=lambda item: -item[1])
        return scored


def _load_doc(refs_dir, filename, rel_path, table_terms):
    path = os.path.join(refs_dir, filename)
    if os.path.getsize(path) > 1024 * 1024:
        logger.warning("[skill] 参考文件过大，已跳过：%s", rel_path)
        return None
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    lines = text.splitlines()
    title = ""
    start = 0
    for i, line in enumerate(lines):
        if line.startswith("# "):
            title = line[2:].strip()
            start = i + 1
            break

    preamble_lines = []
    sections = []
    current = None
    for line in lines[start:]:
        if line.startswith("## "):
            current = SkillSection(line[3:], "")
            sections.append(current)
            continue
        if line.startswith("# "):
            continue
        if current is None:
            preamble_lines.append(line)
        else:
            current.body += line + "\n"

    if not title:
        title = _FILE_PREFIX_RE.sub("", os.path.splitext(filename)[0])

    doc = SkillDoc(rel_path, title, "\n".join(preamble_lines), sections)
    doc.add_terms([title, _FILE_PREFIX_RE.sub("", os.path.splitext(filename)[0])], W_TITLE)
    doc.add_terms(table_terms, W_TABLE)
    for section in sections:
        doc.add_terms(section.terms.keys(), W_HEAD)
    return doc


def _apply_df_filter(docs):
    """丢掉过于通用的词，否则「首页」这类词会把所有文档同时抬过阈值"""
    if not docs:
        return
    limit = max(2, int(len(docs) * DF_DROP_RATIO + 0.999))
    df = {}
    for doc in docs:
        for term in doc.terms:
            df[term] = df.get(term, 0) + 1
    dropped = [term for term in df if df[term] >= limit]
    for doc in docs:
        for term in dropped:
            doc.terms.pop(term, None)


def _fingerprint(skill_dir):
    """技能目录下所有 md 文件的 (相对路径, mtime)，用于判断资料是否变化"""
    items = []
    for dirpath, _dirnames, filenames in os.walk(skill_dir):
        for filename in filenames:
            if not filename.lower().endswith(".md"):
                continue
            path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(path, skill_dir).replace("\\", "/")
            try:
                items.append((rel_path, os.path.getmtime(path)))
            except OSError:
                items.append((rel_path, None))
    items.sort()
    return tuple(items)


class SkillRetriever(object):
    def __init__(self, cfg=None):
        if cfg is None:
            try:
                cfg = conf().get("skill", {})
            except Exception:
                cfg = {}
        # 环境变量覆盖可能把该配置塞成字符串，这里兜一下
        if not isinstance(cfg, dict):
            logger.warning("[skill] 配置 skill 不是字典，已忽略并使用默认值")
            cfg = {}
        self.cfg = {key: cfg.get(key, value) for key, value in DEFAULTS.items()}
        self._pack = None
        self._last_check = 0.0
        self._load_error_logged = False
        self._lock = threading.Lock()

        root = self.cfg["root"]
        if not os.path.isabs(root):
            root = os.path.join(get_root(), root)
        self.skill_dir = os.path.join(root, str(self.cfg["name"]))

    @property
    def enabled(self):
        return bool(self.cfg["enable"])

    def warmup(self):
        """预加载，避免第一次提问时才读盘"""
        if not self.enabled:
            logger.info("[skill] 技能知识库未启用")
            return
        self.reload_if_changed(force=True)

    def reload_if_changed(self, force=False):
        if not self.enabled:
            return
        now = time.time()
        if not force and now - self._last_check < float(self.cfg["reload_interval"]):
            return
        self._last_check = now

        try:
            fingerprint = _fingerprint(self.skill_dir)
        except Exception as e:
            self._log_load_error(e)
            return
        if not force and self._pack is not None and fingerprint == self._pack.fingerprint:
            return
        if not fingerprint:
            # 技能目录不存在或为空
            self._log_load_error(FileNotFoundError(self.skill_dir), once_only=True)
            return

        try:
            pack = SkillPack.load(self.skill_dir, self.cfg["default_reference"])
        except Exception as e:
            # 构建失败时保留上一份可用资料，不影响对话
            self._log_load_error(e)
            return

        self._pack = pack  # 原子替换，读取方拿到的始终是一份完整快照
        self._load_error_logged = False

    def _log_load_error(self, error, once_only=False):
        if self._load_error_logged:
            logger.debug("[skill] 技能资料不可用：%s", error)
            return
        self._load_error_logged = True
        if once_only:
            logger.info("[skill] 技能资料不存在或为空：%s", self.skill_dir)
        else:
            logger.critical("[skill] 技能资料加载失败，将不注入知识：%s", error, stack_info=True)

    def retrieve(self, query):
        """返回 (system 消息, 命中的参考文件列表)；没有命中返回 ("", [])"""
        pack = self._pack
        if pack is None or not query or not query.strip():
            return "", []

        scored = pack.match(query)
        top_score = scored[0][1] if scored else 0.0
        min_score = float(self.cfg["min_score"])

        picked = [doc for doc, score in scored if score >= min_score]
        picked = picked[: max(1, int(self.cfg["max_files"]))]
        if len(picked) > 1 and scored[1][1] < 0.5 * top_score:
            # 第二篇跟首篇差距太大，不要混杂进来
            picked = picked[:1]

        if not picked:
            # 领域内提问但没命中具体文件（如"一共有几个板块"），回退到平台首页
            domain_hit = any(term in query for term in pack.triggers) or top_score > 0
            if domain_hit and pack.default_doc is not None:
                picked = [pack.default_doc]
            else:
                return "", []

        return _build_prompt(pack, picked, query, int(self.cfg["max_chars"])), \
            [doc.rel_path for doc in picked]

    def system_prompt_for(self, query):
        """聊天机器人兜底时调用，任何异常都降级为「不注入」"""
        if not self.enabled or not query:
            return ""
        try:
            self.reload_if_changed()
            prompt, hits = self.retrieve(query)
            if prompt:
                logger.info(
                    "[skill] 命中 %s -> %s（%d 字）", query, "、".join(hits), len(prompt)
                )
            else:
                logger.debug("[skill] 未命中：%s", query)
            return prompt
        except Exception:
            logger.critical("[skill] 检索失败，降级为普通聊天", exc_info=True)
            return ""


def _build_prompt(pack, picked, query, max_chars):
    refs = []
    remaining = max_chars
    for i, doc in enumerate(picked):
        docs_left = len(picked) - i
        budget = min(remaining, max(remaining // docs_left, MIN_DOC_CHARS))
        if i > 0 and budget < MIN_SECOND_DOC_CHARS:
            break
        text, truncated = doc.render(query, budget)
        if not text:
            continue
        block = "### {}（来源：{}）\n{}".format(doc.title, doc.rel_path, text)
        if truncated:
            block += "\n（原文较长，此处截断）"
        refs.append(block)
        remaining -= len(block)
    if not refs:
        return ""

    prompt = "\n\n".join([
        "【系统角色】" + ROLE_TEXT,
        "【回答守则】\n" + pack.guide,
        "在上述守则之外，额外遵守：\n" + EXTRA_RULES,
        "【可选板块】" + "、".join(pack.board_titles),
        "【参考资料】\n" + "\n\n".join(refs),
    ])
    # 最后一道保险：整体长度兜底
    limit = max_chars + PROMPT_OVERHEAD
    if len(prompt) > limit:
        prompt = prompt[:limit] + "\n（原文较长，此处截断）"
    return prompt


_lock = threading.Lock()
_retriever = None


def _get_retriever():
    global _retriever
    if _retriever is None:
        with _lock:
            if _retriever is None:
                try:
                    _retriever = SkillRetriever()
                except Exception:
                    logger.critical("[skill] 技能知识库初始化失败", exc_info=True)
                    return None
    return _retriever


def warmup():
    """对话初始化时预加载技能资料"""
    retriever = _get_retriever()
    if retriever is None:
        return
    try:
        retriever.warmup()
    except Exception:
        logger.critical("[skill] 技能知识库预加载失败", exc_info=True)


def system_prompt_for(query):
    """按用户问句取知识库 system 消息；未命中或未启用返回空字符串"""
    retriever = _get_retriever()
    if retriever is None:
        return ""
    try:
        return retriever.system_prompt_for(query)
    except Exception:
        logger.critical("[skill] 技能知识库检索异常", exc_info=True)
        return ""


if __name__ == "__main__":
    import sys

    _retriever = SkillRetriever()
    _retriever.reload_if_changed(force=True)
    _queries = sys.argv[1:] or ["融合平台有哪些板块", "共享单车的配额是多少", "今天天气怎么样"]
    _pack = _retriever._pack
    if _pack is None:
        print("技能资料未加载：{}".format(_retriever.skill_dir))
        sys.exit(1)
    print("技能：{}  资料文件：{}".format(_pack.name, len(_pack.docs)))
    for _query in _queries:
        print("\n问：{}".format(_query))
        for _doc, _score in _pack.match(_query):
            print("   {:>6.2f}  {}".format(_score, _doc.rel_path))
        _prompt, _hits = _retriever.retrieve(_query)
        print("   -> {}  {} 字".format("、".join(_hits) or "（未命中，不注入）", len(_prompt)))
