import time
from config import conf
from common.log import logger
from common import utils
from pingo import Pingo

detector = None
recorder = None
porcupine = None


def initDetector(pingo: Pingo):
    """
    初始化离线唤醒热词监听器，支持 snowboy 和 porcupine 两大引擎
    """
    global porcupine, recorder, detector

    import pvporcupine
    from pvrecorder import PvRecorder
    access_key = conf().get("picovoice_api_key")
    keyword_paths = conf().get("keyword_path")

    porcupine = pvporcupine.create(
        access_key=access_key,
        keyword_paths=[keyword_paths],
        sensitivities=[conf().get("sensitivity", 0.5)]
    )

    recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
    recorder.start()

    try:
        while True:
            pcm = recorder.read()

            result = porcupine.process(pcm)
            if result >= 0:
                kw = keyword_paths[result]
                logger.info(
                    "[porcupine] Keyword {} Detected at time {}".format(
                        kw,
                        time.strftime(
                            "%Y-%m-%d %H:%M:%S", time.localtime(time.time())
                        ),
                    )
                )
                if not utils.is_proper_time():
                    logger.warning("勿扰模式开启中")
                    continue
                recorder.stop()
                logger.info("进入主动聆听...")
                pingo.conversation.interrupt()
                pingo.conversation.say("我在，请讲！", append_history=False)
                num = 3  # 最多循环确认4次
                pingo.conversation.begin()
                while not pingo.conversation.conversation_is_complete() and num > 0:
                    num = num - 1
                    query = pingo.conversation.activeListen()
                    pingo.conversation.doResponse(query)

                pingo.conversation.end()
                recorder.start()
    except pvporcupine.PorcupineActivationError as e:
        logger.error("[Porcupine] AccessKey activation error", stack_info=True)
        raise e
    except pvporcupine.PorcupineActivationLimitError as e:
        logger.error(
            f"[Porcupine] AccessKey {access_key} has reached it's temporary device limit",
            stack_info=True,
        )
        raise e
    except pvporcupine.PorcupineActivationRefusedError as e:
        logger.error(
            "[Porcupine] AccessKey '%s' refused" % access_key, stack_info=True
        )
        raise e
    except pvporcupine.PorcupineActivationThrottledError as e:
        logger.error(
            "[Porcupine] AccessKey '%s' has been throttled" % access_key,
            stack_info=True,
        )
        raise e
    except pvporcupine.PorcupineError as e:
        logger.error("[Porcupine] 初始化 Porcupine 失败", stack_info=True)
        raise e
    except KeyboardInterrupt:
        logger.info("Stopping ...")
    finally:
        porcupine and porcupine.delete()
        recorder and recorder.delete()
        pingo and pingo.conversation and pingo.conversation.quit()
