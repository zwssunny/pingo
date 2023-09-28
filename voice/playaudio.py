import pygame  # 导入pygame，playsound报错或运行不稳定时直接使用
# from playsound import playsound # windows环境下playsound运行可能不稳定
# 注意pygame只能识别mp3格式 

def play_audio_with_pygame(audio_file_path, canwait: bool = False):
    if canwait:
        play_audio_can_wait(audio_file_path)
    else:
        play_audio_nowait(audio_file_path)


def play_audio_nowait(audio_file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(audio_file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.quit()


def play_audio_can_wait(audio_file_path):
    pygame.init()
    pygame.mixer.init()
    pause = False
    MUSIC_END = pygame.USEREVENT+1
    pygame.mixer.music.set_endevent(MUSIC_END)
    pygame.mixer.music.load(audio_file_path)
    pygame.mixer.music.play()
    # 设置主屏窗口
    screen = pygame.display.set_mode((200, 200))
    # 设置窗口的标题，即游戏名称
    pygame.display.set_caption('播放声音')

    while True:
        event = pygame.event.wait()
        if event.type == pygame.QUIT:
            pygame.quit()
            break
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                pause = not pause
                if pause:
                    pygame.mixer.music.pause()
                else:
                    pygame.mixer.music.unpause()
        if event.type == MUSIC_END:
            break
        # pygame.time.Clock().tick(10)
    pygame.mixer.quit()
    pygame.quit()


if __name__ == '__main__':
    play_audio_can_wait("./cach/20aec00ec4d73aebb0ef1aad03a84796.mp3")
