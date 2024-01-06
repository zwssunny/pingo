from contextlib import contextmanager
from ctypes import CFUNCTYPE, c_char_p, c_int, cdll
import pygame


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


class Player:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.is_pause = False
        self.MUSIC_END = pygame.USEREVENT+1
        pygame.mixer.music.set_endevent(self.MUSIC_END)
        self.music = pygame.mixer.music

    def play_audio(self, audio_file_path):
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

    def play_audio_control(self, audio_file_path):
        self.stop() #先停止前一个播放

        self.is_pause = False
        self.music.load(audio_file_path)
        self.music.play()
        # 设置主屏窗口
        pygame.display.set_mode((200, 200))
        # 设置窗口的标题，即游戏名称
        pygame.display.set_caption('播放声音')
        while True:
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.is_pause = not self.is_pause
                    if self.is_pause:
                        self.music.pause()
                    else:
                        self.music.unpause()
            if event.type == self.MUSIC_END:
                break
            pygame.time.Clock().tick(10)
        pygame.display.quit()

    def pause(self):
        if self.is_pause == False:
            self.music.pause()
            self.is_pause = True

    def unpause(self):
        if self.is_pause == True:
            self.music.unpause()
            self.is_pause = False

    def stop(self):
        self.is_pause = False
        self.music.stop()

    def is_playing(self):
        return self.music.get_busy()

    def quit(self):
        pygame.mixer.quit()
        pygame.quit()
