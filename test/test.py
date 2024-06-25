import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from robot.TTS import XunfeiTTS, SchatTTS
from config import conf, load_config
from robot import Player



if __name__ == '__main__':

    load_config()
    # Xunfei_APP_ID = conf().get("xunfei_yuyin")["appid"]
    # Xunfei_API_KEY = conf().get("xunfei_yuyin")["api_key"]
    # Xunfei_SECRET_KEY = conf().get("xunfei_yuyin")["api_secret"]
    # xfVoice = XunfeiTTS(Xunfei_APP_ID, Xunfei_API_KEY, Xunfei_SECRET_KEY)
    chatTTSconfig=conf().get("schat-tts")
    temperature = chatTTSconfig["temperature"]
    top_p = chatTTSconfig["top_p"]
    top_k = chatTTSconfig["top_k"]
    oral = chatTTSconfig["oral"]
    laugh = chatTTSconfig["laugh"]
    breaktype = chatTTSconfig["breaktype"]
    chat = SchatTTS(temperature, top_p, top_k, oral, laugh, breaktype)
    voice = chat.get_speech("您好，我是小智,很高兴见到您！")
    print(voice)
    player = Player.PGamePlayer()
    player.play(voice)
