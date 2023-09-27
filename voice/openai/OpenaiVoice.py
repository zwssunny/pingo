# -*- coding: utf-8 -*-

import time
import requests
import speech_recognition as sr
from voice.voice import Voice
from common.tmp_dir import TmpDir


class OpenaiVoice(Voice):
    def __init__(self, API_KEY):
        self.API_KEY = API_KEY
        self.r = sr.Recognizer()

    # 从麦克风收集音频并写入文件
    def _record(self, if_cmu: bool = False, rate=16000):
        with sr.Microphone(sample_rate=rate) as source:
            print('您可以开始说话了')
            audio = self.r.listen(source, timeout=20, phrase_time_limit=5)

        file_name = TmpDir().path() + "speech-" + str(int(time.time())) + ".wav"
        with open(file_name, "wb") as f:
            f.write(audio.get_wav_data())

        if if_cmu:
            return audio
        else:
            return self._get_file_content(file_name)

    # 从本地文件中加载音频 作为后续百度语音服务的输入
    def _get_file_content(self, file_name):
        with open(file_name, 'rb') as f:
            audio_data = f.read()
        return audio_data

    def _get_speech_text(self, audio_file):
        print('调用用语音识别')
        url = 'https://api.openai.com/v1/audio/transcriptions'
        headers = {
            'Authorization': 'Bearer ' + self.API_KEY
        }
        files = {
            'file': ('./speech.wav', audio_file),
        }
        data = {
            'model': 'whisper-1',
        }
        response = requests.post(url, headers=headers, data=data, files=files)
        result = response.json()['text']
        # print(result)
        return result

    def speech_to_text(self, audio_path: str = "test.wav", if_microphone: bool = True):
        if if_microphone:
            result = self._get_speech_text(self._record())
        else:
            result = self._get_speech_text(audio_path)
        return result
