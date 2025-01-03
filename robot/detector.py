import time
from config import conf
from common.log import logger
from common import utils


def initDetector(conversation):
    """
    初始化离线唤醒热词监听器，支持 porcupine 引擎
    """

    import pvporcupine
    from pvrecorder import PvRecorder

    robot_name = conf().get("robot_name")
    pvconfig = conf().get("porcupine")
    call_keywords = pvconfig["keywords"]
    call_keyword_paths = pvconfig["keyword_paths"]
    access_key = pvconfig["access_key"]
    porcupine = pvporcupine.create(
        access_key=access_key,
        keyword_paths=call_keyword_paths,
        keywords=call_keywords,
        sensitivities=[conf().get("sensitivity", 0.5)] * len(call_keyword_paths),
    )
    # 问候语
    conversation.say(
        f"您好,我的名字叫{robot_name},很高兴见到您！说话之前记得叫我'{call_keywords}'"
    )
    # 录音监听器
    recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
    recorder.start()

    try:
        while True:
            pcm = recorder.read()

            result = porcupine.process(pcm)
            if result >= 0:
                kw = call_keyword_paths[result]
                logger.info(
                    "[porcupine] Keyword {} Detected at time {}".format(
                        kw,
                        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
                    )
                )
                # 判断是否在可使用时段
                if not utils.is_proper_time():
                    logger.warning("勿扰模式开启中")
                    continue
                # 交出麦克风使用权
                recorder.stop()
                logger.info("进入主动聆听...")
                # 中断原来会话
                conversation.interrupt()
                conversation.say("我在，请讲！", append_history=False)
                query = conversation.activeListen()
                conversation.doResponse(query)
                # 取回麦克风使用权
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
        logger.error("[Porcupine] AccessKey '%s' refused" % access_key, stack_info=True)
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
        conversation and conversation.quit()
