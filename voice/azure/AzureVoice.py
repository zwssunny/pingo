# -*- coding: utf-8 -*-

import speech_recognition as sr
from voice.voice import Voice
from common.tmp_dir import TmpDir
import azure.cognitiveservices.speech as speechsdk


class AzureVoice(Voice):
    def __init__(self, AZURE_API_KEY, AZURE_REGION):
        self.AZURE_API_KEY = AZURE_API_KEY
        self.AZURE_REGION = AZURE_REGION
        self.speech_config = speechsdk.SpeechConfig(
            subscription=AZURE_API_KEY, region=AZURE_REGION)
        self.audio_config = speechsdk.audio.AudioOutputConfig(
            use_default_speaker=True)
        # The language of the voice that speaks.
        self.speech_config.speech_synthesis_voice_name = "zh-CN-XiaoyiNeural"
        self.speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config,
                                                              audio_config=self.audio_config)

    def speech_to_text(self, audio_path: str = "test.wav", if_microphone: bool = True):
        self.speech_config.speech_recognition_language = "zh-CN"
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config, audio_config=audio_config)
        print("Speak into your microphone.")
        speech_recognition_result = speech_recognizer.recognize_once_async().get()

        if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print("Recognized:{}".format(speech_recognition_result.text))
            return speech_recognition_result.text
        elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
            print("No speech could be recognized :{}".format(
                speech_recognition_result.no_match_details))
        elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_recognition_result.cancellation_details
            print("Speech Recognition canceled:{}".format(
                cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Error details:{}".format(
                    cancellation_details.error_details))
                print("Did you set the speech resource key and region values?")
        return None

    def text_to_speech_and_play(self, text, canwait: bool = False):
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
