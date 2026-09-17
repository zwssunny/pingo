import os
import json
import requests
import httpx
import openai

from abc import ABCMeta, abstractmethod
from .sdk import baiduUnit
from common import utils
from common.log import logger
from common.error_handler import retry_on_error
from config import conf


class AbstractRobot(object):

    __metaclass__ = ABCMeta

    # 是否支持 system 消息（技能知识库注入）。UNIT 机器人不消费该参数
    SUPPORTS_SYSTEM_PROMPT = False

    @classmethod
    def get_instance(cls):
        profile = cls.get_config()
        instance = cls(**profile)
        return instance

    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def chat(self, texts, parsed, system_prompt=None):
        pass

    @abstractmethod
    def stream_chat(self, texts):
        pass


class UnitRobot(AbstractRobot):

    SLUG = "unit"

    def __init__(self):
        """
        百度UNIT机器人
        """
        super(self.__class__, self).__init__()
        self.unit = baiduUnit.baiduUnit()

    @classmethod
    def get_config(cls):
        return {}

    def chat(self, texts, parsed, system_prompt=None):
        """
        使用百度UNIT机器人聊天

        Arguments:
        texts -- user input, typically speech, to be parsed by a module

        system_prompt -- 技能知识库注入内容，UNIT 不支持，忽略即可
        """
        msg = "".join(texts)
        msg = utils.stripPunctuation(msg)
        try:
            result = self.unit.getSay(parsed)
            logger.info("{} 回答：{}".format(self.SLUG, result))
            return result
        except Exception:
            logger.critical(
                "UNIT robot failed to response for %r", msg, exc_info=True)
            return "抱歉, 百度UNIT服务回答失败"


class OPENAIRobot(AbstractRobot):

    SLUG = "openai"
    SUPPORTS_SYSTEM_PROMPT = True

    def __init__(
        self,
        openai_api_key,
        model,
        temperature,
        max_tokens,
        top_p,
        frequency_penalty,
        presence_penalty,
        stop_ai,
        prefix="",
        proxy="",
        api_base="",
        max_history_turns=10,
    ):
        """
        OpenAI机器人
        """
        super(self.__class__, self).__init__()
        self.client = None
        try:
            if not openai_api_key:
                openai_api_key = os.getenv("OPENAI_API_KEY")
            self.api_key = openai_api_key
            self.proxy = proxy
            self.model = model
            self.prefix = prefix
            self.temperature = temperature
            self.max_tokens = max_tokens
            self.top_p = top_p
            self.frequency_penalty = frequency_penalty
            self.presence_penalty = presence_penalty
            self.stop_ai = stop_ai
            self.api_base = api_base if api_base else "https://api.openai.com/v1"
            # 最多保留最近多少轮对话历史，避免上下文无限增长
            self.max_history_turns = max_history_turns
            self.context = []

            client_kwargs = {
                "api_key": self.api_key,
                "base_url": self.api_base,
                "timeout": 30.0,
            }
            if proxy:
                logger.debug(f"{self.SLUG} 使用代理：{proxy}")
                client_kwargs["http_client"] = httpx.Client(proxies=proxy)
            self.client = openai.OpenAI(**client_kwargs)
        except Exception as e:
            logger.critical(f"OpenAI 初始化失败，{e}")

    @classmethod
    def get_config(cls):
        # Try to get anyq config from config
        return conf().get("openai", {})

    def _trim_context(self, force_shrink=False):
        """裁剪上下文，只保留最近若干轮对话，避免无限增长"""
        limit = self.max_history_turns
        if force_shrink:
            limit = max(1, limit // 2)
        max_messages = 2 * limit
        if len(self.context) > max_messages:
            del self.context[: len(self.context) - max_messages]

    def _build_messages(self, system_prompt=None):
        """system 消息每次请求临时拼装，不写进 self.context，因此不会被 _trim_context 裁掉"""
        if system_prompt:
            return [{"role": "system", "content": system_prompt}] + list(self.context)
        return list(self.context)

    @retry_on_error(
        max_retries=2,
        delay=1.0,
        backoff=2.0,
        exceptions=(
            openai.APIConnectionError,
            openai.APITimeoutError,
            openai.RateLimitError,
        ),
    )
    def _create_completion(self, system_prompt=None):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(system_prompt),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            stop=self.stop_ai,
        )
        return response.choices[0].message.content

    def stream_chat(self, texts):
        """
        从ChatGPT API获取回复
        :return: 回复
        """

        msg = "".join(texts)
        msg = utils.stripPunctuation(msg)
        msg = self.prefix + msg  # 增加一段前缀
        logger.info("msg: " + msg)
        self.context.append({"role": "user", "content": msg})
        self._trim_context()

        header = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.api_key,
        }

        data = {"model": self.model,
                "messages": self.context, "stream": True}
        logger.info("开始流式请求")
        url = self.api_base + "/chat/completions"
        # 请求接收流式数据
        try:
            response = requests.request(
                "POST",
                url,
                headers=header,
                json=data,
                stream=True,
                proxies={"https": self.proxy} if self.proxy else None,
                timeout=(5, 60),
            )

            def generate():
                stream_content = str()
                one_message = {"role": "assistant", "content": stream_content}
                self.context.append(one_message)
                i = 0
                for line in response.iter_lines():
                    line_str = str(line, encoding="utf-8")
                    if line_str.startswith("data:") and line_str[5:]:
                        if line_str.startswith("data: [DONE]"):
                            break
                        line_json = json.loads(line_str[5:])
                        if "choices" in line_json:
                            if len(line_json["choices"]) > 0:
                                choice = line_json["choices"][0]
                                if "delta" in choice:
                                    delta = choice["delta"]
                                    if "role" in delta:
                                        role = delta["role"]
                                    elif "content" in delta:
                                        delta_content = delta["content"]
                                        i += 1
                                        if i < 40:
                                            logger.debug(delta_content, end="")
                                        elif i == 40:
                                            logger.debug("......")
                                        one_message["content"] = (
                                            one_message["content"] +
                                            delta_content
                                        )
                                        yield delta_content

                    elif len(line_str.strip()) > 0:
                        logger.debug(line_str)
                        yield line_str
                self._trim_context()

        except Exception as e:
            ee = e

            def generate():
                yield "request error:\n" + str(ee)

        return generate

    def chat(self, texts, parsed, system_prompt=None):
        """
        使用OpenAI机器人聊天

        Arguments:
        texts -- user input, typically speech, to be parsed by a module

        system_prompt -- 技能知识库检索到的资料，作为 system 消息参与本次请求，
                         不写入 self.context，所以不影响多轮历史
        """
        msg = "".join(texts)
        msg = utils.stripPunctuation(msg)
        msg = self.prefix + msg  # 增加一段前缀
        logger.info("msg: " + msg)

        self.context.append({"role": "user", "content": msg})
        self._trim_context()
        try:
            respond = self._create_completion(system_prompt)
        except openai.BadRequestError:
            logger.warning("token超出长度限制，裁剪历史后重试")
            self.context.pop()
            self._trim_context(force_shrink=True)
            self.context.append({"role": "user", "content": msg})
            try:
                respond = self._create_completion(system_prompt)
            except Exception:
                self.context.pop()
                logger.critical(
                    "openai robot failed to response for %r", msg, exc_info=True
                )
                return "抱歉，OpenAI 回答失败"
        except Exception:
            self.context.pop()
            logger.critical(
                "openai robot failed to response for %r", msg, exc_info=True
            )
            return "抱歉，OpenAI 回答失败"

        self.context.append({"role": "assistant", "content": respond})
        self._trim_context()
        return respond


class DeepseekRobot(AbstractRobot):

    SLUG = "deepseek"
    SUPPORTS_SYSTEM_PROMPT = True

    def __init__(
        self,
        api_key,
        model,
        max_tokens,
        stop_ai,
        prefix="",
        proxy="",
        api_base="",
        max_history_turns=10,
    ):
        """
        Deepseek机器人
        """
        super(self.__class__, self).__init__()
        self.client = None
        try:
            if not api_key:
                api_key = os.getenv("DEEPSEEK_API_KEY")
            self.api_key = api_key
            self.proxy = proxy
            self.model = model
            self.prefix = prefix
            self.max_tokens = max_tokens
            self.stop_ai = stop_ai
            self.api_base = api_base if api_base else "https://api.deepseek.com"
            # 最多保留最近多少轮对话历史，避免上下文无限增长
            self.max_history_turns = max_history_turns
            self.context = []

            client_kwargs = {
                "api_key": self.api_key,
                "base_url": self.api_base,
                "timeout": 30.0,
            }
            if proxy:
                logger.debug(f"{self.SLUG} 使用代理：{proxy}")
                client_kwargs["http_client"] = httpx.Client(proxies=proxy)
            self.client = openai.OpenAI(**client_kwargs)
        except Exception as e:
            logger.critical(f"deepseek 初始化失败，{e}")

    @classmethod
    def get_config(cls):
        # Try to get anyq config from config
        return conf().get("deepseek", {})

    def _trim_context(self, force_shrink=False):
        """裁剪上下文，只保留最近若干轮对话，避免无限增长"""
        limit = self.max_history_turns
        if force_shrink:
            limit = max(1, limit // 2)
        max_messages = 2 * limit
        if len(self.context) > max_messages:
            del self.context[: len(self.context) - max_messages]

    def _build_messages(self, system_prompt=None):
        """system 消息每次请求临时拼装，不写进 self.context，因此不会被 _trim_context 裁掉"""
        if system_prompt:
            return [{"role": "system", "content": system_prompt}] + list(self.context)
        return list(self.context)

    @retry_on_error(
        max_retries=2,
        delay=1.0,
        backoff=2.0,
        exceptions=(
            openai.APIConnectionError,
            openai.APITimeoutError,
            openai.RateLimitError,
        ),
    )
    def _create_completion(self, system_prompt=None):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(system_prompt),
            max_tokens=self.max_tokens,
            stop=self.stop_ai,
        )
        return response.choices[0].message.content

    def stream_chat(self, texts):
        """
        从ChatGPT API获取回复
        :return: 回复
        """

        msg = "".join(texts)
        msg = utils.stripPunctuation(msg)
        msg = self.prefix + msg  # 增加一段前缀
        logger.info("msg: " + msg)
        self.context.append({"role": "user", "content": msg})
        self._trim_context()

        header = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.api_key,
        }

        data = {"model": self.model,
                "messages": self.context, "stream": True}
        logger.info("开始流式请求")
        url = self.api_base + "/chat/completions"
        # 请求接收流式数据
        try:
            response = requests.request(
                "POST",
                url,
                headers=header,
                json=data,
                stream=True,
                proxies={"https": self.proxy} if self.proxy else None,
                timeout=(5, 60),
            )

            def generate():
                stream_content = str()
                one_message = {"role": "assistant", "content": stream_content}
                self.context.append(one_message)
                i = 0
                for line in response.iter_lines():
                    line_str = str(line, encoding="utf-8")
                    if line_str.startswith("data:") and line_str[5:]:
                        if line_str.startswith("data: [DONE]"):
                            break
                        line_json = json.loads(line_str[5:])
                        if "choices" in line_json:
                            if len(line_json["choices"]) > 0:
                                choice = line_json["choices"][0]
                                if "delta" in choice:
                                    delta = choice["delta"]
                                    if "role" in delta:
                                        role = delta["role"]
                                    elif "content" in delta:
                                        delta_content = delta["content"]
                                        i += 1
                                        if i < 40:
                                            logger.debug(delta_content, end="")
                                        elif i == 40:
                                            logger.debug("......")
                                        one_message["content"] = (
                                            one_message["content"] +
                                            delta_content
                                        )
                                        yield delta_content

                    elif len(line_str.strip()) > 0:
                        logger.debug(line_str)
                        yield line_str
                self._trim_context()

        except Exception as e:
            ee = e

            def generate():
                yield "request error:\n" + str(ee)

        return generate

    def chat(self, texts, parsed, system_prompt=None):
        """
        使用deepseek机器人聊天

        Arguments:
        texts -- user input, typically speech, to be parsed by a module

        system_prompt -- 技能知识库检索到的资料，作为 system 消息参与本次请求，
                         不写入 self.context，所以不影响多轮历史
        """
        msg = "".join(texts)
        msg = utils.stripPunctuation(msg)
        msg = self.prefix + msg  # 增加一段前缀
        logger.info("msg: " + msg)

        self.context.append({"role": "user", "content": msg})
        self._trim_context()
        try:
            respond = self._create_completion(system_prompt)
        except openai.BadRequestError:
            logger.warning("token超出长度限制，裁剪历史后重试")
            self.context.pop()
            self._trim_context(force_shrink=True)
            self.context.append({"role": "user", "content": msg})
            try:
                respond = self._create_completion(system_prompt)
            except Exception:
                self.context.pop()
                logger.critical(
                    "deepseek robot failed to response for %r", msg, exc_info=True
                )
                return "抱歉，Deepseek 回答失败"
        except Exception:
            self.context.pop()
            logger.critical(
                "deepseek robot failed to response for %r", msg, exc_info=True
            )
            return "抱歉，Deepseek 回答失败"

        self.context.append({"role": "assistant", "content": respond})
        self._trim_context()
        return respond


def get_robot_by_slug(slug):
    """
    Returns:
        A robot implementation available on the current platform
    """
    if not slug or type(slug) is not str:
        raise TypeError("Invalid slug '%s'", slug)

    selected_robots = list(
        filter(
            lambda robot: hasattr(
                robot, "SLUG") and robot.SLUG == slug, get_robots()
        )
    )
    if len(selected_robots) == 0:
        raise ValueError("No robot found for slug '%s'" % slug)
    else:
        if len(selected_robots) > 1:
            logger.warning(
                "WARNING: Multiple robots found for slug '%s'. "
                + "This is most certainly a bug." % slug
            )
        robot = selected_robots[0]
        logger.info(f"使用 {robot.SLUG} 对话机器人")
        return robot.get_instance()


def get_robots():
    def get_subclasses(cls):
        subclasses = set()
        for subclass in cls.__subclasses__():
            subclasses.add(subclass)
            subclasses.update(get_subclasses(subclass))
        return subclasses

    return [
        robot
        for robot in list(get_subclasses(AbstractRobot))
        if hasattr(robot, "SLUG") and robot.SLUG
    ]
