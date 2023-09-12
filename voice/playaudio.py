# from winsound import PlaySound
import pygame # 导入pygame，playsound报错或运行不稳定时直接使用
# from playsound import playsound # windows环境下playsound运行可能不稳定


def play_audio_with_pygame( audio_file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(audio_file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.quit()

# def play_audio(audio_file_path):
#     PlaySound(audio_file_path)