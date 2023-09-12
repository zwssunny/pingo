# -*- coding: utf-8 -*-

import asyncio
import pvporcupine
from pvrecorder import PvRecorder
from common.log import logger
from voice.voice2text import BaiduASR, AzureASR, OpenaiASR
from voice.text2voice import BaiduTTS, Pyttsx3TTS, AzureTTS, EdgeTTS
from voice.playaudio import play_audio_with_pygame
from config import conf, load_config
from bgunit import Bgunit
from common.utils import clean

def Orator():
    # load config
    load_config()
    PICOVOICE_API_KEY = conf().get("picovoice_api_key")
    keyword_path = conf().get("keyword_path")
    porcupine = pvporcupine.create(
        access_key=PICOVOICE_API_KEY,
        keyword_paths=[keyword_path]
    )
    Baidu_APP_ID = conf().get("baidu_app_id")
    Baidu_API_KEY = conf().get("baidu_api_key")
    Baidu_SECRET_KEY = conf().get("baidu_secret_key")
    asr = BaiduASR(Baidu_APP_ID, Baidu_API_KEY, Baidu_SECRET_KEY)
    # tts = BaiduTTS(Baidu_APP_ID, Baidu_API_KEY, Baidu_SECRET_KEY)
    tts = EdgeTTS()
    # 创建插件功能
    chat_module = Bgunit()
    asyncio.run(tts.text_to_speech_and_play("您好,我的名字叫Pingo,很高兴见到您！说话之前记得叫我 ‘Hey pingo!'"))

    recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
    recorder.start()

    try:
        while True:
            pcm = recorder.read()
            result = porcupine.process(pcm)
            if result >= 0:
                recorder.stop() #关闭麦克风的占用
                logger.info("嗯,我在,请讲！")
                # tts.text_to_speech_and_play("我在,请讲！")
                asyncio.run(tts.text_to_speech_and_play("我在,请讲！"))  # 如果用Edgetts需要使用异步执行
                chat_module.begin()
                num=4 #最多确认4次
                while not chat_module.conversation_is_complete() and num>0:
                    num=num-1
                    q = asr.speech_to_text()
                    logger.info("recognize_from_microphone, text= %s",q)
                    # 调用插件功能，返回意图结果
                    res = chat_module.chat_with_unit(q)
                    print(res)
                    # tts.text_to_speech_and_play(res)
                    asyncio.run(tts.text_to_speech_and_play(res))  # 如果用Edgetts需要使用异步执行
                chat_module.end()
                recorder.start() #启用麦克风
    except pvporcupine.PorcupineActivationError as e:
        logger.error("[Porcupine] AccessKey activation error", stack_info=True)
        raise e
    except pvporcupine.PorcupineActivationLimitError as e:
        logger.error(
            f"[Porcupine] AccessKey {PICOVOICE_API_KEY} has reached it's temporary device limit",
            stack_info=True,
        )
        raise e
    except pvporcupine.PorcupineActivationRefusedError as e:
        logger.error(
            "[Porcupine] AccessKey '%s' refused" % PICOVOICE_API_KEY, stack_info=True
        )
        raise e
    except pvporcupine.PorcupineActivationThrottledError as e:
        logger.error(
            "[Porcupine] AccessKey '%s' has been throttled" % PICOVOICE_API_KEY,
            stack_info=True,
        )
        raise e
    except pvporcupine.PorcupineError as e:
        logger.error("[Porcupine] 初始化 Porcupine 失败", stack_info=True)
        raise e
    except KeyboardInterrupt:
        logger.info("Stopping ...")
    finally:
        asyncio.run(tts.text_to_speech_and_play("好的，我退下了，再见！"))
        porcupine and porcupine.delete()
        recorder and recorder.delete()
        clean()


if __name__ == '__main__':
    Orator()
