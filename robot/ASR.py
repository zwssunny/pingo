import json
from aip import AipSpeech
from abc import ABCMeta, abstractmethod

import requests
from common import utils
from common.log import logger
from config import conf
from robot.sdk import XunfeiSpeech

from common import utils


class AbstractASR(object):
    """
    Generic parent class for all ASR engines
    """

    __metaclass__ = ABCMeta

    @classmethod
    def get_config(cls):
        return {}

    @classmethod
    def get_instance(cls):
        profile = cls.get_config()
        instance = cls(**profile)
        return instance

    @abstractmethod
    def transcribe(self, fp):
        pass


class AzureASR(AbstractASR):
    """
    微软的语音识别API
    """

    SLUG = "azure-asr"

    def __init__(self, secret_key, region, lang="zh-CN", **args):
        super(self.__class__, self).__init__()
        self.post_url = "https://<REGION_IDENTIFIER>.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1".replace(
            "<REGION_IDENTIFIER>", region
        )

        self.post_header = {
            "Ocp-Apim-Subscription-Key": secret_key,
            "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
            "Accept": "application/json",
        }

        self.post_param = {"language": lang, "profanity": "raw"}
        self.sess = requests.session()

    @classmethod
    def get_config(cls):
        # Try to get azure_yuyin config from config
        return conf().get("azure_yuyin", {})

    def transcribe(self, fp):
        # 识别本地文件
        pcm = utils.get_pcm_from_wav(fp)
        ret = self.sess.post(
            url=self.post_url,
            data=pcm,
            headers=self.post_header,
            params=self.post_param,
        )

        if ret.status_code == 200:
            res = ret.json()
            logger.info(f"{self.SLUG} 语音识别到了：{res['DisplayText']}")
            return "".join(res["DisplayText"])
        else:
            logger.info(f"{self.SLUG} 语音识别出错了: {res.text}")
            return ""


class BaiduASR(AbstractASR):
    """
    百度的语音识别API.
    dev_pid:
        - 1936: 普通话远场
        - 1536：普通话(支持简单的英文识别)
        - 1537：普通话(纯中文识别)
        - 1737：英语
        - 1637：粤语
        - 1837：四川话
    要使用本模块, 首先到 yuyin.baidu.com 注册一个开发者账号,
    之后创建一个新应用, 然后在应用管理的"查看key"中获得 API Key 和 Secret Key
    填入 config.xml 中.
    ...
        baidu_yuyin:
            appid: '9670645'
            api_key: 'qg4haN8b2bGvFtCbBGqhrmZy'
            secret_key: '585d4eccb50d306c401d7df138bb02e7'
        ...
    """

    SLUG = "baidu-asr"

    def __init__(self, appid, api_key, secret_key, dev_pid=1536, **args):
        super(self.__class__, self).__init__()
        self.client = AipSpeech(appid, api_key, secret_key)
        self.dev_pid = dev_pid

    @classmethod
    def get_config(cls):
        # Try to get baidu_yuyin config from config
        return conf().get("baidu_yuyin", {})

    def _get_file_content(self, file_name):
        with open(file_name, 'rb') as f:
            audio_data = f.read()
        return audio_data

    def transcribe(self, fp):
        # 识别本地文件
        wav = self._get_file_content(fp)
        res = self.client.asr(wav, "wav", 16000, {"dev_pid": self.dev_pid})
        if res["err_no"] == 0:
            logger.info(f"{self.SLUG} 语音识别到了：{res['result']}")
            return "".join(res["result"])
        else:
            logger.info(f"{self.SLUG} 语音识别出错了: {res['err_msg']}")
            if res["err_msg"] == "request pv too much":
                logger.info("       出现这个原因很可能是你的百度语音服务调用量超出限制，或未开通付费")
            return ""


class XunfeiASR(AbstractASR):
    """
    科大讯飞的语音识别API.
    """

    SLUG = "xunfei-asr"

    def __init__(self, appid, api_key, api_secret, **args):
        super(self.__class__, self).__init__()
        self.appid = appid
        self.api_key = api_key
        self.api_secret = api_secret

    @classmethod
    def get_config(cls):
        # Try to get xunfei_yuyin config from config
        return conf().get("xunfei_yuyin", {})

    def transcribe(self, fp):
        return XunfeiSpeech.transcribe(fp, self.appid, self.api_key, self.api_secret)


class WhisperASR(AbstractASR):
    """
    OpenAI 的 whisper 语音识别API
    """

    SLUG = "openai"

    def __init__(self, openai_api_key, **args):
        super(self.__class__, self).__init__()
        try:
            import openai

            self.openai = openai
            self.openai.api_key = openai_api_key
            print(openai_api_key)
        except Exception:
            logger.critical("OpenAI 初始化失败，请升级 Python 版本至 > 3.6")

    @classmethod
    def get_config(cls):
        return conf().get("openai", {})

    def transcribe(self, fp):
        if self.openai:
            try:
                with open(fp, "rb") as f:
                    result = self.openai.Audio.transcribe("whisper-1", f)
                    if result:
                        logger.info(f"{self.SLUG} 语音识别到了：{result.text}")
                        return result.text
            except Exception:
                logger.critical(f"{self.SLUG} 语音识别出错了", stack_info=True)
                return ""
        logger.critical(f"{self.SLUG} 语音识别出错了", stack_info=True)
        return ""


def get_engine_by_slug(slug=None) -> AbstractASR:
    """
    Returns:
        An ASR Engine implementation available on the current platform

    Raises:
        ValueError if no speaker implementation is supported on this platform
    """

    if not slug or type(slug) is not str:
        raise TypeError("无效的 ASR slug '%s'", slug)

    selected_engines = list(
        filter(
            lambda engine: hasattr(engine, "SLUG") and engine.SLUG == slug,
            get_engines(),
        )
    )

    if len(selected_engines) == 0:
        raise ValueError(f"错误：找不到名为 {slug} 的 ASR 引擎")
    else:
        if len(selected_engines) > 1:
            logger.warning(f"注意: 有多个 ASR 名称与指定的引擎名 {slug} 匹配")
        engine = selected_engines[0]
        logger.debug(f"使用 {engine.SLUG} ASR 引擎")
        return engine.get_instance()


def get_engines():
    def get_subclasses(cls):
        subclasses = set()
        for subclass in cls.__subclasses__():
            subclasses.add(subclass)
            subclasses.update(get_subclasses(subclass))
        return subclasses

    return [
        engine
        for engine in list(get_subclasses(AbstractASR))
        if hasattr(engine, "SLUG") and engine.SLUG
    ]
