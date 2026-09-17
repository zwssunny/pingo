# encoding:utf-8
"""技能知识库检索自测：不需要网络、不需要密钥、不依赖 config.json

运行：python test/test_skills.py
"""

import os
import sys
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from robot import skills  # noqa: E402

# 问句 -> 期望命中的参考文件（顺序敏感，第一篇必须一致）
HIT_CASES = [
    ("公交的亮点场景是什么", "references/01-城市交通.md"),
    ("网约车有多少辆", "references/01-城市交通.md"),
    ("共享单车的配额是多少", "references/01-城市交通.md"),
    ("地铁客流怎么监测", "references/01-城市交通.md"),
    ("停车场的分布怎么看", "references/01-城市交通.md"),
    ("两客一危一重是什么", "references/02-道路运输.md"),
    ("驾培行业管哪些内容", "references/02-道路运输.md"),
    ("客运执法主要查什么", "references/03-交通执法.md"),
    ("一超四罚指什么", "references/03-交通执法.md"),
    ("可网办率是多少", "references/04-电子政务.md"),
    ("电子证照双公示是什么", "references/04-电子政务.md"),
    ("白云机场的运力监测怎么做", "references/05-综合交通.md"),
    ("节假日交通场景讲什么", "references/05-综合交通.md"),
    ("十四五规划了哪些项目", "references/06-基础设施.md"),
    ("路政占道施工怎么管", "references/06-基础设施.md"),
]

# 与平台无关的问句：不应注入任何资料
MISS_CASES = ["今天天气怎么样", "帮我写一首诗", "1加1等于几"]


def main():
    retriever = skills.SkillRetriever()
    retriever.reload_if_changed(force=True)
    pack = retriever._pack
    assert pack is not None, "技能资料未加载：{}".format(retriever.skill_dir)
    assert len(pack.docs) == 7, "参考文件数量不对：{}".format(len(pack.docs))
    assert pack.guide and len(pack.guide) > 40, "回答守则未抽取到"
    assert pack.triggers, "触发词未抽取到"
    print("加载 OK：{} 个参考文件、{} 个触发词".format(len(pack.docs), len(pack.triggers)))

    # 1. 命中用例
    for query, expected in HIT_CASES:
        prompt, hits = retriever.retrieve(query)
        assert hits, "未命中：{}".format(query)
        assert hits[0] == expected, "{} 期望 {}，实际 {}".format(query, expected, hits)
        assert prompt, "命中但 prompt 为空：{}".format(query)
        print("  命中 {:<28} -> {}".format(query, "、".join(hits)))

    # 2. 无关问句不注入
    for query in MISS_CASES:
        assert skills.system_prompt_for(query) == "", "无关问句被注入了：{}".format(query)
    print("  无关问句不注入 OK：{}".format("、".join(MISS_CASES)))

    # 3. 领域内提问但没命中具体文件 -> 回退平台首页
    prompt = retriever.retrieve("融合平台一共有几个板块")[0]
    assert "references/00-平台首页.md" in prompt, "未回退到平台首页"
    print("  领域回退平台首页 OK")

    # 4. DF 过滤生效：通用词「首页」不应出现在任何文档的关键词里
    for doc in pack.docs:
        assert "首页" not in doc.terms, "{} 仍保留了通用词「首页」".format(doc.rel_path)
    print("  DF 过滤 OK")

    # 5. 预算上界
    limit = int(retriever.cfg["max_chars"]) + skills.PROMPT_OVERHEAD
    for query, _ in HIT_CASES:
        prompt, _ = retriever.retrieve(query)
        assert len(prompt) <= limit, "{} 注入超长：{}".format(query, len(prompt))
    print("  长度上界 OK（<= {} 字）".format(limit))

    # 6. 检索只带来片段，不是整篇原文
    doc_01 = pack.docs[1]
    full_len = len(doc_01.preamble) + sum(
        len(s.heading) + len(s.body) for s in doc_01.sections
    )
    prompt_len = len(retriever.retrieve("共享单车的配额是多少")[0])
    assert prompt_len < full_len, "整篇原文都被注入了，检索没有起作用"
    print("  定向截取 OK（{} 字 vs 整篇 {} 字）".format(prompt_len, full_len))

    # 7. 并发调用稳定（会话线程与唤醒词线程可能同时提问）
    errors = []

    def worker(q):
        try:
            for _ in range(20):
                skills.system_prompt_for(q)
        except Exception as e:  # pragma: no cover
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(q,)) for q, _ in HIT_CASES[:4]]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors, "并发检索异常：{}".format(errors)
    print("  并发检索 OK")

    # 8. 技能目录不存在时安全降级
    missing = skills.SkillRetriever({"root": "./no-such-dir", "name": "nothing"})
    missing.reload_if_changed(force=True)
    assert missing.system_prompt_for("共享单车的配额是多少") == "", "资料缺失时不应注入"
    print("  资料缺失降级 OK")

    print("\n全部通过 ✅")


if __name__ == "__main__":
    main()
