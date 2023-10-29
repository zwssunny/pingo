import os
import uuid
import edge_tts
import asyncio
from abc import ABCMeta, abstractmethod
from aip import AipSpeech
from common import utils
from common.log import logger
from config import conf, load_config
from robot.sdk import XunfeiSpeech

class AbstractTTS(object):
    """
    Generic parent class for all TTS engines
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
    def get_speech(self, phrase):
        pass

class BaiduTTS(AbstractTTS):
    """
    使用百度语音合成技术
    要使用本模块, 首先到 yuyin.baidu.com 注册一个开发者账号,
    之后创建一个新应用, 然后在应用管理的"查看key"中获得 API Key 和 Secret Key
    填入 config.yml 中.
    ...
        baidu_yuyin:
            appid: '9670645'
            api_key: 'qg4haN8b2bGvFtCbBGqhrmZy'
            secret_key: '585d4eccb50d306c401d7df138bb02e7'
            dev_pid: 1936
            per: 1
            lan: 'zh'
        ...
    """

    SLUG = "baidu-tts"

    def __init__(self, appid, api_key, secret_key, per=1, lan="zh", **args):
        super(self.__class__, self).__init__()
        self.client = AipSpeech(appid, api_key, secret_key)
        self.per, self.lan = str(per), lan

    @classmethod
    def get_config(cls):
        # Try to get baidu_yuyin config from config
        return conf().get("baidu_yuyin", {})

    def get_speech(self, phrase):
        if utils.getCache(phrase):
            temfile=utils.getCache(phrase)
            return tmpfile
        else:
            result = self.client.synthesis(phrase, self.lan, 1, {"per": self.per})
            # 识别正确返回语音二进制 错误则返回dict 参照下面错误码
            if not isinstance(result, dict):
                tmpfile = utils.write_temp_file(result, ".mp3")
                temfile=utils.saveCache(temfile,phrase)
                logger.info(f"{self.SLUG} 语音合成成功，合成路径：{tmpfile}")
                return tmpfile
            else:
                logger.critical(f"{self.SLUG} 合成失败！", stack_info=True)


class XunfeiTTS(AbstractTTS):
    """
    科大讯飞的语音识别API.
    """

    SLUG = "xunfei-tts"

    def __init__(self, appid, api_key, api_secret, voice="xiaoyan"):
        super(self.__class__, self).__init__()
        self.appid, self.api_key, self.api_secret, self.voice_name = (
            appid,
            api_key,
            api_secret,
            voice,
        )

    @classmethod
    def get_config(cls):
        # Try to get xunfei_yuyin config from config
        return conf().get("xunfei_yuyin", {})

    def get_speech(self, phrase):
        return XunfeiSpeech.synthesize(
            phrase, self.appid, self.api_key, self.api_secret, self.voice_name
        )

class EdgeTTS(AbstractTTS):
    """
    edge-tts 引擎
    voice: 发音人，默认是 zh-CN-XiaoxiaoNeural
        全部发音人列表：命令行执行 edge-tts --list-voices 可以打印所有语音
    """

    SLUG = "edge-tts"

    def __init__(self, voice="zh-CN-XiaoxiaoNeural", **args):
        super(self.__class__, self).__init__()
        self.voice = voice

    @classmethod
    def get_config(cls):
        # Try to get edge-tts config from config
        return conf().get("edge-tts", {})

    async def async_get_speech(self, phrase):
        try:
            if utils.getCache(phrase):  # 存在缓存
                tmpfile = utils.getCache(phrase)
            else:
                tmpfile = os.path.join(utils.TMP_PATH, uuid.uuid4().hex + ".mp3")
                tts = edge_tts.Communicate(text=phrase, voice=self.voice)
                await tts.save(tmpfile)   
                tmpfile = utils.saveCache(tmpfile, phrase) 
            logger.info(f"{self.SLUG} 语音合成成功，合成路径：{tmpfile}")
            return tmpfile
        except Exception as e:
            logger.critical(f"{self.SLUG} 合成失败：{str(e)}！", stack_info=True)
            return None

    def get_speech(self, phrase):
        event_loop = asyncio.new_event_loop()
        tmpfile = event_loop.run_until_complete(self.async_get_speech(phrase))
        event_loop.close()
        return tmpfile

def get_engine_by_slug(slug=None)->AbstractTTS:
    """
    Returns:
        A TTS Engine implementation available on the current platform

    Raises:
        ValueError if no speaker implementation is supported on this platform
    """

    if not slug or type(slug) is not str:
        raise TypeError("无效的 TTS slug '%s'", slug)

    selected_engines = list(
        filter(
            lambda engine: hasattr(engine, "SLUG") and engine.SLUG == slug,
            get_engines(),
        )
    )

    if len(selected_engines) == 0:
        raise ValueError(f"错误：找不到名为 {slug} 的 TTS 引擎")
    else:
        if len(selected_engines) > 1:
            logger.warning(f"注意: 有多个 TTS 名称与指定的引擎名 {slug} 匹配")
        engine = selected_engines[0]
        logger.info(f"使用 {engine.SLUG} TTS 引擎")
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
        for engine in list(get_subclasses(AbstractTTS))
        if hasattr(engine, "SLUG") and engine.SLUG
    ]
