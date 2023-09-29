import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from voice.xunfei.XunfeiVoice import XunfeiVoice
from config import conf, load_config





if __name__ == '__main__':

    load_config()
    Xunfei_APP_ID = conf().get("xunfei_app_id")
    Xunfei_API_KEY = conf().get("xunfei_api_key")
    Xunfei_SECRET_KEY = conf().get("xunfei_secret_key")
    xfVoice = XunfeiVoice(Xunfei_APP_ID, Xunfei_API_KEY, Xunfei_SECRET_KEY)
    xfVoice.text_to_speech_and_play("产品介绍")