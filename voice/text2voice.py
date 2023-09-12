# -*- coding: utf-8 -*-

import asyncio
import os
import time
import sys
from aip import AipSpeech
import azure.cognitiveservices.speech as speechsdk
import pyttsx3
from edge_tts import Communicate
from .playaudio import play_audio_with_pygame
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from common.tmp_dir import TmpDir
from common.log import logger
from common.utils import getCache, saveCache

class BaiduTTS:
    def __init__(self, APP_ID, API_KEY, SECRET_KEY):
        self.APP_ID = APP_ID
        self.API_KEY = API_KEY
        self.SECRET_KEY = SECRET_KEY
        self.client = AipSpeech(self.APP_ID, self.API_KEY, self.SECRET_KEY)

    def text_to_speech_and_play(self, text=""):
        if text is None:
            return
        
        if getCache(text): #存在缓存
            fileName=getCache(text)
            play_audio_with_pygame(fileName)
        else:
            result = self.client.synthesis(text, 'zh', 1, {
                'spd': 5,  # 语速
                'pit': 5,
                'vol': 5,  # 音量大小
                'per': 1  # 发声人 男生
            })  # 得到音频的二进制文件

            if not isinstance(result, dict):
                fileName = TmpDir().path() + "reply-" + str(int(time.time())) + \
                             "-" + str(hash(text) & 0x7FFFFFFF) + ".mp3"
                
                with open(fileName, "wb") as f:
                    f.write(result)
                fileName=saveCache(fileName,text)
                logger.info(
                    "[Baidu] text2voice text={} voice file name={}".format(text, fileName))
                # playsound('./audio.mp3')  # playsound无法运行时删去此行改用pygame，若正常运行择一即可
                play_audio_with_pygame(fileName)  # 注意pygame只能识别mp3格式
            else:
                print("语音合成失败", result)


class Pyttsx3TTS:
    def __init__(self):
        pass

    def text_to_speech_and_play(self, text=""):
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()


class AzureTTS:
    def __init__(self, AZURE_API_KEY, AZURE_REGION):
        self.AZURE_API_KEY = AZURE_API_KEY
        self.AZURE_REGION = AZURE_REGION
        self.speech_config = speechsdk.SpeechConfig(
            subscription=AZURE_API_KEY, region=AZURE_REGION)
        self.speech_config = speechsdk.SpeechConfig(
            subscription=AZURE_API_KEY, region=AZURE_REGION)
        self.audio_config = speechsdk.audio.AudioOutputConfig(
            use_default_speaker=True)
        # The language of the voice that speaks.
        self.speech_config.speech_synthesis_voice_name = "zh-CN-XiaoyiNeural"
        self.speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config,
                                                              audio_config=self.audio_config)

    def text_to_speech_and_play(self, text):
        # Get text from the console and synthesize to the default speaker.
        speech_synthesis_result = self.speech_synthesizer.speak_text_async(
            text).get()

        if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("Speech synthesized for text [{}]".format(text))
        elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_synthesis_result.cancellation_details
            print("Speech synthesis canceled:{}".format(
                cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                if cancellation_details.error_details:
                    print("Error details :{}".format(
                        cancellation_details.error_details))
                    print("Didy you set the speech resource key and region values?")


class EdgeTTS:
    def __init__(self, voice: str = "zh-CN-YunjianNeural", rate: str = "+0%", volume: str = "+0%"):
        self.voice = voice
        self.rate = rate
        self.volume = volume

    async def text_to_speech_and_play(self, text):
        # voices = await VoicesManager.create()
        # voice = voices.find(Gender="Female", Language="zh")
        # communicate = edge_tts.Communicate(text, random.choice(voice)["Name"])
        if getCache(text): #存在缓存
            fileName=getCache(text)
            play_audio_with_pygame(fileName)
        else:
            communicate = Communicate(text, self.voice)
            fileName = TmpDir().path() + "reply-" + str(int(time.time())) + \
                "-" + str(hash(text) & 0x7FFFFFFF) + ".mp3"
            await communicate.save(fileName)
            fileName=saveCache(fileName,text)
            # playsound('./audio.wav') # playsound无法运行时删去此行改用pygame，若正常运行择一即可
            play_audio_with_pygame(fileName)  # 注意pygame只能识别mp3格式


if __name__ == '__main__':
    # sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    # from config import conf, load_config
    # load_config()
    # Baidu_APP_ID = conf().get("baidu_app_id")
    # Baidu_API_KEY = conf().get("baidu_api_key")
    # Baidu_SECRET_KEY = conf().get("baidu_secret_key")
    # baidutts = BaiduTTS(Baidu_APP_ID, Baidu_API_KEY, Baidu_SECRET_KEY)
    # baidutts.text_to_speech_and_play("您好,我的名字叫Pingo,很高兴见到您！说话之前记得叫我 ‘Hey pingo!'")
    #
    # pyttsx3tts = Pyttsx3TTS()
    # pyttsx3tts.text_to_speech_and_play('春天来了，每天的天气都很好！')
    #
    # AZURE_API_KEY = ""
    # AZURE_REGION = ""
    # azuretts = AzureTTS(AZURE_API_KEY, AZURE_REGION)
    # azuretts.text_to_speech_and_play("嗯，你好，我是你的智能小伙伴，我的名字叫Murphy，你可以和我畅所欲言，我是很会聊天的哦！")
    edgetts = EdgeTTS()
    asyncio.run(edgetts.text_to_speech_and_play(
        "您好，我是你的智能小伙伴，我的名字叫Pingo，你可以和我畅所欲言，我是很会聊天的哦！"))
