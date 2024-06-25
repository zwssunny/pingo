import sys
import ChatTTS
import os
import uuid
import wave
import edge_tts
import asyncio
import nest_asyncio
import numpy as np
import torch

from abc import ABCMeta, abstractmethod
from aip import AipSpeech
import requests
from xml.etree import ElementTree

import torchaudio

from common import utils
from common.log import logger
from config import conf
from .sdk import XunfeiSpeech, VITSClient

from dotenv import load_dotenv
load_dotenv("sha256.env")


nest_asyncio.apply()


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


class SchatTTS(AbstractTTS):
    """
        使用chatTTS合成语音
    """

    SLUG = "schat-tts"

    def __init__(self, temperature, top_p, top_k, oral, laugh, breaktype, voice="chattts", **args) -> None:
        super(self.__class__, self).__init__()

        self.chat = ChatTTS.Chat()
        self.chat.load_models(compile=sys.platform != 'win32')

        rand_spk = self.chat.sample_random_speaker()
        self.params_infer_code = self.chat.InferCodeParams(
            spk_emb=rand_spk,
            temperature=temperature,
            top_P=top_p,
            top_K=top_k,
        )
        self.oral, self.laugh, self.breaktype = oral, laugh, breaktype
        self.voice = voice

    @classmethod
    def get_config(cls):
        # Try to get schat-tts config from config
        return conf().get("schat-tts", {})

    def get_speech(self, phrase):
        if utils.getCache(phrase, self.voice):  # 存在缓存
            tmpfile = utils.getCache(phrase, self.voice)
            return tmpfile
        else:
            texts = [phrase,]
            # For sentence level manual control.
            # use oral_(0-9), laugh_(0-2), break_(0-7)
            # to generate special token in text to synthesize.

            # params_refine_text = self.chat.RefineTextParams(
            #     prompt="[oral_2][laugh_0][break_6]",
            # )

            wavs = self.chat.infer(texts, skip_refine_text=True,
                                   params_infer_code=self.params_infer_code,
                                   stream=False,)

            tmpfile = os.path.join(utils.TMP_PATH, uuid.uuid4().hex + ".wav")
            torchaudio.save(tmpfile, torch.from_numpy(wavs[0]), 24000)
            tmpfile = utils.saveCache(tmpfile, phrase, self.voice)
            logger.debug(f"{self.SLUG} 语音合成成功，合成路径：{tmpfile}")
            return tmpfile


class AzureTTS(AbstractTTS):
    """
    使用微软语音合成技术
    """

    SLUG = "azure-tts"

    def __init__(
        self, secret_key, region, lang="zh-CN", voice="zh-CN-XiaoxiaoNeural", **args
    ) -> None:
        super(self.__class__, self).__init__()
        self.post_url = "https://INSERT_REGION_HERE.tts.speech.microsoft.com/cognitiveservices/v1".replace(
            "INSERT_REGION_HERE", region
        )

        self.post_header = {
            "Ocp-Apim-Subscription-Key": secret_key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
            "User-Agent": "curl",
        }
        self.voice = voice
        self.sess = requests.session()
        body = ElementTree.Element("speak", version="1.0")
        body.set("xml:lang", "en-us")
        vc = ElementTree.SubElement(body, "voice")
        vc.set("xml:lang", lang)
        vc.set("name", self.voice)
        self.body = body
        self.vc = vc

    @classmethod
    def get_config(cls):
        # Try to get baidu_yuyin config from config
        return conf().get("azure_yuyin", {})

    def get_speech(self, phrase):
        if utils.getCache(phrase, self.voice):  # 存在缓存
            tmpfile = utils.getCache(phrase, self.voice)
            return tmpfile
        else:
            self.vc.text = phrase
            result = self.sess.post(
                self.post_url,
                headers=self.post_header,
                data=ElementTree.tostring(self.body),
            )
            # 识别正确返回语音二进制,http状态码为200
            if result.status_code == 200:
                tmpfile = utils.write_temp_file(result.content, ".mp3")
                tmpfile = utils.saveCache(tmpfile, phrase, self.voice)
                logger.info(f"{self.SLUG} 语音合成成功，合成路径：{tmpfile}")
                return tmpfile
            else:
                logger.critical(f"{self.SLUG} 合成失败！", stack_info=True)


class BaiduTTS(AbstractTTS):
    """
    使用百度语音合成技术
    要使用本模块, 首先到 yuyin.baidu.com 注册一个开发者账号,
    之后创建一个新应用, 然后在应用管理的"查看key"中获得 API Key 和 Secret Key
    填入 config.json 中.
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
        if utils.getCache(phrase, str(self.per)):
            temfile = utils.getCache(phrase, str(self.per))
            return tmpfile
        else:
            result = self.client.synthesis(
                phrase, self.lan, 1, {"per": self.per})
            # 识别正确返回语音二进制 错误则返回dict 参照下面错误码
            if not isinstance(result, dict):
                tmpfile = utils.write_temp_file(result, ".mp3")
                temfile = utils.saveCache(temfile, phrase, str(self.per))
                logger.debug(f"{self.SLUG} 语音合成成功，合成路径：{tmpfile}")
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
        if utils.getCache(phrase, self.voice_name):  # 存在缓存
            tmpfile = utils.getCache(phrase, self.voice_name)
        else:
            tmpfile = XunfeiSpeech.synthesize(
                phrase, self.appid, self.api_key, self.api_secret, self.voice_name)
            tmpfile = utils.saveCache(tmpfile, phrase, self.voice_name)
        return tmpfile


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
            if utils.getCache(phrase, self.voice):  # 存在缓存
                tmpfile = utils.getCache(phrase, self.voice)
            else:
                tmpfile = os.path.join(
                    utils.TMP_PATH, uuid.uuid4().hex + ".mp3")
                tts = edge_tts.Communicate(text=phrase, voice=self.voice)
                await tts.save(tmpfile)
                tmpfile = utils.saveCache(tmpfile, phrase, self.voice)
                logger.debug(f"{self.SLUG} 语音合成成功，合成路径：{tmpfile}")
            return tmpfile
        except Exception as e:
            logger.critical(f"{self.SLUG} 合成失败：{str(e)}！", stack_info=True)
            return None

    def get_speech(self, phrase):
        # event_loop = asyncio.new_event_loop()
        # tmpfile = event_loop.run_until_complete(self.async_get_speech(phrase))
        # event_loop.close()
        tmpfile = asyncio.run(self.async_get_speech(phrase))
        return tmpfile


class VITS(AbstractTTS):
    """
    VITS 语音合成
    需要自行搭建vits-simple-api服务器：https://github.com/zwssunny/vits-simple-api
    server_url : 服务器url，如http://127.0.0.1:23456/voice/vits
    api_key : 若服务器配置了API Key，在此填入
    speaker_id : 说话人ID，由所使用的模型决定
    length : 调节语音长度，相当于调节语速，该数值越大语速越慢。
    noise : 噪声
    noisew : 噪声偏差
    max : 分段阈值，按标点符号分段，加起来大于max时为一段文本。max<=0表示不分段。
    timeout: 响应超时时间，根据vits-simple-api服务器性能不同配置合理的超时时间。
    """

    SLUG = "VITS"

    def __init__(self, server_url, api_key, speaker_id, length, noise, noisew, max, timeout, **args):
        super(self.__class__, self).__init__()
        self.server_url, self.api_key, self.speaker_id, self.length, self.noise, self.noisew, self.max, self.timeout = (
            server_url, api_key, speaker_id, length, noise, noisew, max, timeout)

    @classmethod
    def get_config(cls):
        return conf().get("VITS", {})

    def get_speech(self, phrase):
        if utils.getCache(phrase, str(self.speaker_id)):  # 存在缓存
            tmpfile = utils.getCache(phrase, str(self.speaker_id))
        else:
            result = VITSClient.tts(phrase, self.server_url, self.api_key, self.speaker_id, self.length, self.noise,
                                    self.noisew, self.max, self.timeout)
            tmpfile = utils.write_temp_file(result, ".wav")
            logger.info(f"{self.SLUG} 语音合成成功，合成路径：{tmpfile}")
            tmpfile = utils.saveCache(tmpfile, phrase, str(self.speaker_id))
        return tmpfile


def get_engine_by_slug(slug=None) -> AbstractTTS:
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
        logger.debug(f"使用 {engine.SLUG} TTS 引擎")
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
