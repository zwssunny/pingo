# -*- coding: utf-8 -*-

import time
import speech_recognition as sr
from voice.voice import Voice
from common.tmp_dir import TmpDir
from . import XunfeiSpeech

class XunfeiVoice(Voice):
    def __init__(self, appid, api_key, api_secret):
        self.appid = appid
        self.api_key = api_key
        self.api_secret = api_secret
        self.recognizer = sr.Recognizer()

    # 从麦克风收集音频并写入文件
    def _record(self, if_cmu: bool = False, rate=16000):
        with sr.Microphone(sample_rate=rate) as source:
            # 校准环境噪声水平的energy threshold
            # duration:用于指定计算环境噪声的持续时间（秒）。默认值为1秒。函数将等待指定时间来计算环境噪声水平，并相应地调整麦克风增益，以提高语音识别的准确性。如果噪声水平很高，则可以增加此值以获得更准确的噪声估计。
            # self.r.adjust_for_ambient_noise(source, duration=1)
            print('您可以开始说话了')
            # timeout 用于指定等待语音输入的最长时间（秒），如果没有检测到语音输入，则函数将返回None。默认值为 None，表示等待无限长的时间。如果指定了超时时间，则函数将在等待指定时间后自动返回。
            # phrase_time_limit：用于指定允许单次语音输入的最长时间（秒），如果超过这个时间，函数将自动停止录制，并返回None.默认值为 None，表示允许单次语音输入的时间没有限制。
            audio = self.recognizer.listen(
                source, timeout=20, phrase_time_limit=6)

        # Avoid the same filename under multithreading
        file_name = TmpDir().path() + "speech-" + str(int(time.time())) + ".wav"
        with open(file_name, "wb") as f:
            f.write(audio.get_wav_data())
        return file_name

    # 从本地文件中加载音频 作为后续百度语音服务的输入
    def _get_file_content(self, file_name):
        with open(file_name, 'rb') as f:
            audio_data = f.read()
        return audio_data

    def speech_to_text(self, audio_path: str = "test.wav", if_microphone: bool = True):
        # 麦克风输入 采样频率必须为8的倍数 我们使用16000和上面保持一致
        if if_microphone:
            return XunfeiSpeech.transcribe(
                self._record(), self.appid, self.api_key, self.api_secret)
        # 从文件中读取
        else:
            return XunfeiSpeech.transcribe(audio_path, self.appid, self.api_key, self.api_secret)
