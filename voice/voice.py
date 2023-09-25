"""
Voice service abstract class
"""


class Voice(object):
    def speech_to_text(self, audio_path: str = "test.wav", if_microphone: bool = True):
        """
        Send voice to voice service and get text
        """
        raise NotImplementedError

    def text_to_speech_and_play(self, text, canwait: bool = False):
        """
        Send text to voice service and get voice
        """
        raise NotImplementedError
