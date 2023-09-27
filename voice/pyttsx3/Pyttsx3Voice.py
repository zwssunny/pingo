# -*- coding: utf-8 -*-

import pyttsx3
from voice.voice import Voice


class Pyttsx3TTS(Voice):
    def __init__(self):
        pass

    def text_to_speech_and_play(self, text=""):
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
