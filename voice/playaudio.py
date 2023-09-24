# from winsound import PlaySound
import pygame  # 导入pygame，playsound报错或运行不稳定时直接使用
# from playsound import playsound # windows环境下playsound运行可能不稳定


def play_audio_with_pygame(audio_file_path):
    # pygame.init()
    pygame.mixer.init()
    pause = False
    pygame.mixer.music.load(audio_file_path)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        # for event in  pygame.event.get():
        #   if event.type == pygame.QUIT:
        #        pygame.quit()
        #   if event.type == pygame.KEYDOWN:
        #        if event.key == pygame.K_SPACE:
        #             pause = not pause
        #             if pause:
        #                 pygame.mixer.music.pause()
        #             else:
        #                 pygame.mixer.music.unpause()
        pygame.time.Clock().tick(10)
    pygame.mixer.quit()


if __name__ == '__main__':
    play_audio_with_pygame("./cach/20aec00ec4d73aebb0ef1aad03a84796.mp3")
