
import os
import re
import time
import uuid
import threading
import platform
import speech_recognition as sr
from common import utils
from common.tmp_dir import TmpDir
from config import conf, load_config
from orator.sysintroduction import sysIntroduction
from robot import AI, ASR, NLU, TTS, History, Player
from common.log import logger


class Conversation(object):
    def __init__(self):
        self.introduction, self.asr, self.tts, self.nlu = None, None, None, None
        self.reInit()
        # 历史会话消息
        self.history = History.History()
        self.hasPardon = False
        self.onSay = None
        self.onStream = None
        self.onPlaybill = None
        self.recognizer = sr.Recognizer()
        self.voices = {}
        self.activeThread = None

    def reInit(self):
        """重新初始化"""
        try:
            load_config()
            # intent
            self.pageintent = conf().get("pageintent")
            self.systemintent = conf().get("systemintent")
            self.highlightintent = conf().get("highlightintent")

            self.asr = ASR.get_engine_by_slug(
                conf().get("asr_engine", "baidu-asr"))
            self.tts = TTS.get_engine_by_slug(
                conf().get("tts_engine", "edge-tts"))
            self.nlu = NLU.get_engine_by_slug(conf().get("nlu_engine", "unit"))
            self.ai = AI.get_robot_by_slug(conf().get("robot", "unit"))

            system = platform.system()
            if system == "Windows":
                self.player = Player.PGamePlayer()
            else:
                self.player = Player.SoxPlayer()

            self.introduction = sysIntroduction(conversation=self)
        except Exception as e:
            logger.critical(f"对话初始化失败：{e}", stack_info=True)

    def quit(self):
        self.interrupt()

    def newvoice(self, tts_engine):
        """创建新声音，这是为应对演讲方案中个性化服务，
            系统的声音请在config.json系统参数中设置
            如果声音列表中已存在该声音列表，直接返回该语音合成引擎

        Args:
            voice (str): 声音名称,请参考EdgeTTS依赖库自带的声音列表，如果为None则返回系统设置的语音合成引擎

        Returns:
            tts: 语音合成引擎实例
        """
        if tts_engine is None:
            return self.tts
        if tts_engine not in self.voices:
            self.voices[tts_engine] = TTS.get_engine_by_slug(tts_engine)
        return self.voices[tts_engine]

    def testvoice(self, text, tts_engine=None):
        try:
            # 保存原来的tts
            oldtts = self.tts
            if tts_engine:
                self.tts = self.newvoice(tts_engine)
            self.say(text)
        except Exception as e:
            logger.error("测试语音出错{e}")
        finally:
            self.tts = oldtts

    def billtalk(self, billID=None, onPlaybill=None):
        """演讲传入的方案ID

        Args:
            billID (int, optional): 演讲方案ID.如果没有传入指定ID，则播放系统默认方案.
            onPlaybill (function, optional): 播放事件回调函数. Defaults to None.
        """
        if onPlaybill:
            self.onPlaybill = onPlaybill
        self.introduction.billtalk(billID, self.onPlaybill)

    def talkbillitem_byid(self, billitemID, onPlaybill=None):
        """演讲指定节点

        Args:
            billitemID (int): 节点ID
            onPlaybill (function, optional): 播放事件回调函数. Defaults to None.
        """
        if onPlaybill:
            self.onPlaybill = onPlaybill
        self.introduction.tallbllitem_byid(billitemID, self.onPlaybill)

    def getHistory(self):
        return self.history

    def interrupt(self, ispassive=False):
        """打断会话过程，不会恢复
        """
        if ispassive:
            self.appendHistory(0, "打断会话！")
            logger.info("打断会话！")

        if self.introduction:
            self.introduction.stop()
        if self.player:
            self.player.stop()

    def pause(self):
        """暂停会话，可以通过unpause()恢复
        """

        if self.player:
            self.player.pause()
        self.appendHistory(0, "暂停！")
        logger.info("暂停！")
        self.introduction.setplaystatusChange(2)

    def unpause(self):
        """继续播放声音
        """

        if self.player:
            self.player.resume()

        self.appendHistory(0, "继续！")
        logger.info("继续！")
        self.introduction.setplaystatusChange(1)

    def appendHistory(self, t, text, UUID="", plugin=""):
        """将会话历史加进历史记录"""
        if t in (0, 1) and text:
            if text.endswith(",") or text.endswith("，"):
                text = text[:-1]
            if (UUID is None) or (UUID == "") or (UUID == "null"):
                UUID = str(uuid.uuid1())
            # 将图片处理成HTML
            pattern = r"https?://.+\.(?:png|jpg|jpeg|bmp|gif|JPG|PNG|JPEG|BMP|GIF)"
            url_pattern = r"^https?://.+"
            imgs = re.findall(pattern, text)
            for img in imgs:
                text = text.replace(
                    img,
                    f'<a data-fancybox="images" href="{img}"><img src={img} class="img fancybox"></img></a>',
                )
            urls = re.findall(url_pattern, text)
            for url in urls:
                text = text.replace(
                    url, f'<a href={url} target="_blank">{url}</a>')
            self.history.add_message(
                {
                    "type": t,
                    "text": text,
                    "time": time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(time.time())
                    ),
                    "uuid": UUID,
                    "plugin": plugin,
                }
            )

    def say(self, msg,  plugin="", append_history=True):
        if not msg:
            return

        if append_history:
            self.appendHistory(1, msg, plugin=plugin)
        # msg = utils.stripPunctuation(msg).strip()
        if not msg:
            return
        voice = self.tts.get_speech(msg)
        # logger.info(f"TTS合成成功。msg: {msg}")
        self._befor_play(msg, [voice], plugin)
        self.player.play(voice)

        # logger.info(f"即将朗读语音：{msg}")
        # lines = re.split("。|！|？|\!|\?|\n", msg)
        # for line in lines:
        #     voice = self.tts.get_speech(line)
        #     self._befor_play(line, [voice], plugin)
        #     self.player.play(voice)

    def pardon(self):
        if not self.hasPardon:
            self.say("抱歉，刚刚没听清，能再说一遍吗？")
            self.hasPardon = True
        else:
            self.say("没听清呢")
            self.hasPardon = False

    def doConverse(self, fp, callback=None, onSay=None, onStream=None):
        # self.interrupt()
        try:
            query = self.asr.transcribe(fp)
        except Exception as e:
            logger.critical(f"ASR识别失败：{e}", stack_info=True)
        try:
            self.doResponse(query, callback, onSay, onStream)
        except Exception as e:
            logger.critical(f"回复失败：{e}", stack_info=True)

    def _befor_play(self, msg, audios, plugin=""):
        if self.onSay:
            serverhost = conf().get("server")
            cached_audios = [
                f"https://{serverhost['host']}:{serverhost['port']}/audio/{os.path.basename(voice)}"
                for voice in audios
            ]
            logger.debug(f"onSay: {msg}, {cached_audios}")
            self.onSay(msg, cached_audios, plugin=plugin)
            # self.onSay = None

    def doParse(self, query):
        args = conf().get("unit")
        return self.nlu.parse(query, **args)

    def doResponse(self, query, UUID="", onSay=None, onStream=None):
        """
        响应指令

        :param query: 指令
        :UUID: 指令的UUID
        """
        # 先打断前面播放事件
        self.interrupt()

        self.appendHistory(0, query, UUID)

        if onSay:
            self.onSay = onSay

        if onStream:
            self.onStream = onStream

        if query.strip() == "":
            self.pardon()
            return

        parsed = self.doParse(query)
        intent = self.nlu.getIntent(parsed)
        if intent:  # 找到意图
            logger.debug("找到意图 Intent= %s", intent)
            slots = self.nlu.getSlots(parsed, intent)
            soltslen = len(slots)

            if soltslen > 0:
                pagename = slots[0]['normalized_word']
            if intent in self.pageintent:
                self.activeThread = threading.Thread(
                    target=lambda: self.introduction.talkmenuitem_byname(pagename))
                self.activeThread.start()
            elif intent in self.systemintent:
                self.activeThread = threading.Thread(
                    target=lambda: self.introduction.talkothersystem_byname(pagename))
                self.activeThread.start()
            elif intent in self.highlightintent:
                self.activeThread = threading.Thread(
                    target=lambda: self.introduction.talkhighlight_byname(pagename))
                self.activeThread.start()
            elif "ORATOR" in intent:  # 演示系统默认方案
                self.activeThread = threading.Thread(
                    target=self.billtalk())
                self.activeThread.start()
            else:
                reply = self.nlu.getSay(parsed, intent)
                self.say(reply)
        else:  # 找不到意图，后续可以传给聊天机器人处理
            # self.pardon()
            msg = self.ai.chat(query, parsed)
            self.say(msg)

    # 从麦克风收集音频并写入文件
    def _record(self, rate=16000):
        with sr.Microphone(sample_rate=rate) as source:
            # 校准环境噪声水平的energy threshold
            # duration:用于指定计算环境噪声的持续时间（秒）。默认值为1秒。函数将等待指定时间来计算环境噪声水平，并相应地调整麦克风增益，以提高语音识别的准确性。如果噪声水平很高，则可以增加此值以获得更准确的噪声估计。
            # self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print('您可以开始说话了')
            # timeout 用于指定等待语音输入的最长时间（秒），如果没有检测到语音输入，则函数将返回None。默认值为 None，表示等待无限长的时间。如果指定了超时时间，则函数将在等待指定时间后自动返回。
            # phrase_time_limit：用于指定允许单次语音输入的最长时间（秒），如果超过这个时间，函数将自动停止录制，并返回None.默认值为 None，表示允许单次语音输入的时间没有限制。
            audio = self.recognizer.listen(
                source, timeout=20, phrase_time_limit=5)

        # Avoid the same filename under multithreading
        file_name = TmpDir().path() + "speech-" + str(int(time.time())) + ".wav"
        with open(file_name, "wb") as f:
            f.write(audio.get_wav_data())

        return file_name

    def activeListen(self):
        """
        主动问一个问题(适用于多轮对话)
        """
        voice = self._record()
        if voice:
            logger.info("调用ARS引擎")
            query = self.asr.transcribe(voice)
            return query

        return ""
