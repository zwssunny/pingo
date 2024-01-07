# -*- coding: utf-8 -*-
import subprocess
import os
import signal

from pydub import AudioSegment
from pydub import playback
from contextlib import contextmanager
from ctypes import CFUNCTYPE, c_char_p, c_int, cdll
import pygame
from common.log import logger


def py_error_handler(filename, line, function, err, fmt):
    pass


ERROR_HANDLER_FUNC = CFUNCTYPE(
    None, c_char_p, c_int, c_char_p, c_int, c_char_p)

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)


@contextmanager
def no_alsa_error():
    try:
        asound = cdll.LoadLibrary("libasound.so")
        asound.snd_lib_error_set_handler(c_error_handler)
        yield
        asound.snd_lib_error_set_handler(None)
    except:
        yield
        pass

def play(fname):
    player = getPlayerByFileName(fname)
    player.play(fname)


def getPlayerByFileName(fname):
    foo, ext = os.path.splitext(fname)
    if ext in [".mp3", ".wav"]:
        return SoxPlayer()
    
class AbstractPlayer(object):
    def __init__(self, **kwargs):
        super(AbstractPlayer, self).__init__()

    def play(self):
        pass

    def stop(self):
        pass

    def resume(self):
        pass

    def pause(self):
        pass

    def is_playing(self):
        return False
    
    def is_pausing(self):
        return False
    
    def join(self):
        pass

    def quit(self):
        pass
class SoxPlayer(AbstractPlayer):
    SLUG = "SoxPlayer"

    def __init__(self, **kwargs):
        super(SoxPlayer, self).__init__(**kwargs)
        self.playing = False
        self.pausing = False
        self.proc = None

    def doPlay(self, src):
        # song=AudioSegment.from_file(src)
        # playback.play(song)
        PLAYER=playback.get_player_name()
        cmd=[PLAYER, "-nodisp", "-autoexit", "-hide_banner", src]
        self.proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        self.playing = True
        self.proc.wait()
        self.playing = False
        logger.info(f"播放完成：{src}")
        return self.proc and self.proc.returncode

    def play(self, src):
        if src and (os.path.exists(src) or src.startswith("http")):
            self.doPlay(src)
        else:
            logger.critical(f"path not exists: {src}", stack_info=True)

    def stop(self):
        if self.proc:
            self.proc.terminate()
            self.proc.kill()
            self.proc = None
            self.playing = False

    def pause(self):
        logger.debug("SoxPlayer pause")
        self.pausing = True
        if self.proc:
            os.kill(self.proc.pid, signal.SIGSTOP) #(POSIX)

    def resume(self):
        logger.debug("SoxPlayer resume")
        self.pausing = False
        if self.proc:
            os.kill(self.proc.pid, signal.SIGCONT) #(POSIX)

    def is_playing(self):
        return self.playing 
    
    def is_pausing(self):
        return self.pausing
    

class PGamePlayer(AbstractPlayer):
    SLUG = "PGamePlayer"

    def __init__(self,**kwargs):
        super(PGamePlayer, self).__init__(**kwargs)
        pygame.init()
        pygame.mixer.init()
        self.is_pause = False
        self.MUSIC_END = pygame.USEREVENT+1
        pygame.mixer.music.set_endevent(self.MUSIC_END)
        self.music = pygame.mixer.music

    def play(self, audio_file_path):
        self.stop() #先停止前一个播放

        self.is_pause = False
        self.music.load(audio_file_path)
        self.music.play()
        while True:
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                break
            if event.type == self.MUSIC_END:
                break
            pygame.time.Clock().tick(10)

    def pause(self):
        if self.is_pause == False:
            self.music.pause()
            self.is_pause = True

    def resume(self):
        if self.is_pause == True:
            self.music.unpause()
            self.is_pause = False

    def stop(self):
        self.is_pause = False
        self.music.stop()

    def is_playing(self):
        return self.music.get_busy()
    
    def is_pausing(self):
        return self.pausing
    
    def quit(self):
        pygame.mixer.quit()
        pygame.quit()
