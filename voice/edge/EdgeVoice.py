# -*- coding: utf-8 -*-

import asyncio
import time
from edge_tts import Communicate
from voice.playaudio import play_audio_with_pygame
from voice.voice import Voice
from common.tmp_dir import TmpDir
from common.utils import getCache, saveCache
from common.log import logger


class EdgeVoice(Voice):
    def __init__(self, voice_name: str = "zh-CN-YunjianNeural", rate: str = "+0%", volume: str = "+0%"):
        self.voice_name = voice_name
        self.rate = rate
        self.volume = volume

    async def async_text_to_speech_and_play(self, text, canwait: bool = False):
        # voices = await VoicesManager.create()
        # voice = voices.find(Gender="Female", Language="zh")
        # communicate = edge_tts.Communicate(text, random.choice(voice)["Name"])
        if getCache(text):  # 存在缓存
            fileName = getCache(text)
            play_audio_with_pygame(fileName, canwait)
        else:
            communicate = Communicate(text, self.voice_name)
            fileName = TmpDir().path() + "reply-" + str(int(time.time())) + \
                "-" + str(hash(text) & 0x7FFFFFFF) + ".mp3"
            await communicate.save(fileName)
            fileName = saveCache(fileName, text)
            play_audio_with_pygame(fileName, canwait)  # 注意pygame只能识别mp3格式

    def text_to_speech_and_play(self, text, canwait: bool = False):
        asyncio.run(self.async_text_to_speech_and_play(text, canwait))
