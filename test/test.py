import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from robot.TTS import XunfeiTTS
from robot import Player
from config import conf, load_config





if __name__ == '__main__':

    load_config()
    Xunfei_APP_ID = conf().get("xunfei_yuyin")["appid"]
    Xunfei_API_KEY = conf().get("xunfei_yuyin")["api_key"]
    Xunfei_SECRET_KEY = conf().get("xunfei_yuyin")["api_secret"]
    xfVoice = XunfeiTTS(Xunfei_APP_ID, Xunfei_API_KEY, Xunfei_SECRET_KEY)
    voice=xfVoice.get_speech("产品介绍")
    print(voice)
    player=Player.PGamePlayer()
    player.play(voice)
    