import time
import numpy as np
import pyaudio
from config import conf
from common.log import logger
from common import utils

# openWakeWord 官方推荐的帧长：80ms，对应 16kHz 采样率下的 1280 个采样点
FRAME_LENGTH = 1280
SAMPLE_RATE = 16000


def initDetector(conversation):
    """
    初始化离线唤醒热词监听器，使用 openWakeWord 引擎（完全本地运行，无需在线激活）
    """

    from openwakeword.model import Model

    robot_name = conf().get("robot_name")
    owwconfig = conf().get("openwakeword")
    model_paths = owwconfig["model_paths"]
    threshold = owwconfig.get("threshold", 0.5)
    inference_framework = owwconfig.get("inference_framework", "onnx")

    model = Model(wakeword_models=model_paths, inference_framework=inference_framework)

    # 问候语
    conversation.say(
        f"您好,我的名字叫{robot_name},很高兴见到您！说话之前记得叫我的唤醒词"
    )

    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=FRAME_LENGTH,
    )

    try:
        while True:
            pcm = stream.read(FRAME_LENGTH, exception_on_overflow=False)
            audio_frame = np.frombuffer(pcm, dtype=np.int16)

            prediction = model.predict(audio_frame)
            detected = [name for name, score in prediction.items() if score > threshold]
            if detected:
                logger.info(
                    "[openwakeword] Keyword {} Detected at time {}".format(
                        detected,
                        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
                    )
                )
                # 判断是否在可使用时段
                if not utils.is_proper_time():
                    logger.warning("勿扰模式开启中")
                    continue
                # 交出麦克风使用权
                stream.stop_stream()
                logger.info("进入主动聆听...")
                # 中断原来会话
                conversation.interrupt()
                conversation.say("我在，请讲！", append_history=False)
                query = conversation.activeListen()
                conversation.doResponse(query)
                # 取回麦克风使用权前重置预测缓冲区，避免刚结束的对话残留分数影响下一次唤醒判断
                model.reset()
                stream.start_stream()
    except KeyboardInterrupt:
        logger.info("Stopping ...")
    except Exception as e:
        logger.error("[openwakeword] 唤醒检测出错", stack_info=True)
        raise e
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        conversation and conversation.quit()
