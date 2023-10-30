
import os
import re
import time
import uuid
import speech_recognition as sr
from common import utils
from common.tmp_dir import TmpDir
from config import conf, load_config
from orator.sysintroduction import sysIntroduction
from robot import ASR, NLU, TTS, History, Player
from common.log import logger


class Conversation(object):
    def __init__(self):
        self.introduction, self.asr, self.tts, self.nlu = None, None, None, None
        self.reInit()
        # 历史会话消息
        self.history = History.History()
        self.isConversationcomplete =False
        self.isRecording = False
        self.hasPardon = False
        self.onSay = None
        self.onStream = None
        self.recognizer = sr.Recognizer()

    def reInit(self):
        """重新初始化"""
        try:
            load_config()
            # intent
            self.pageintent = conf().get("pageintent")
            self.systemintent = conf().get("systemintent")
            self.highlightintent = conf().get("highlightintent")
            self.ctlandtalk = conf().get("ctlandtalk")

            self.asr = ASR.get_engine_by_slug(conf().get("asr_engine", "baidu-asr"))
            self.tts = TTS.get_engine_by_slug(conf().get("tts_engine", "edge-tts"))
            self.nlu = NLU.get_engine_by_slug(conf().get("nlu_engine", "unit"))
            self.player = Player.Player()
            self.introduction = sysIntroduction(conversation=self, ctlandtalk=self.ctlandtalk)
        except Exception as e:
            logger.critical(f"对话初始化失败：{e}", stack_info=True)
    
    def quit(self):
        if self.player:
            self.player.quit()

    def getHistory(self):
        return self.history
    
    def interrupt(self):
        """打断会话过程，不会恢复
        """        
        if self.introduction:
            self.introduction.stop()
        if self.player and self.player.is_playing():
            self.player.stop()

    def pause(self):
        """暂停会话，可以通过unpause()恢复
        """        
        if self.player and self.player.is_playing():
            self.player.pause()

    def unpause(self):
        """继续播放声音
        """        
        if self.player:
            self.player.unpause()

    def appendHistory(self, t, text, UUID="", plugin=""):
        """将会话历史加进历史记录"""
        if t in (0, 1) and text:
            if text.endswith(",") or text.endswith("，"):
                text = text[:-1]
            if UUID == "" or UUID == None or UUID == "null":
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
                text = text.replace(url, f'<a href={url} target="_blank">{url}</a>')
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
     

        voice = self.tts.get_speech(msg)
        # logger.info(f"TTS合成成功。msg: {msg}")
        self.player.play_audio(voice)

        self._after_play(msg, voice, plugin)

    def pardon(self):
        if not self.hasPardon:
            self.say("抱歉，刚刚没听清，能再说一遍吗？")
            self.hasPardon = True
        else:
            self.say("没听清呢")
            self.hasPardon = False

    def doConverse(self, fp, callback=None, onSay=None, onStream=None):
        self.interrupt()
        try:
            query = self.asr.transcribe(fp)
        except Exception as e:
            logger.critical(f"ASR识别失败：{e}", stack_info=True)
        try:
            self.doResponse(query, callback, onSay, onStream)
        except Exception as e:
            logger.critical(f"回复失败：{e}", stack_info=True)

    def _after_play(self, msg, audios, plugin=""):
        serverhost=conf().get("server")
        cached_audios = [
            f"http://{serverhost['host']}:{serverhost['port']}/audio/{os.path.basename(voice)}"
            for voice in audios
        ]
        if self.onSay:
            logger.info(f"onSay: {msg}, {cached_audios}")
            self.onSay(msg, cached_audios, plugin=plugin)
            self.onSay = None

    def doParse(self, query):
        args = conf().get("unit")
        return self.nlu.parse(query, **args)
    
    def doResponse(self, query, UUID="",onSay=None, onStream=None):
        """
        响应指令

        :param query: 指令
        :UUID: 指令的UUID
        """
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
            reply = self.nlu.getSay(parsed, intent)
            print(reply)
            self.say(reply)
            self.isConversationcomplete = True
            slots = self.nlu.getSlots(parsed, intent)
            soltslen = len(slots)
            if soltslen > 0:
                if (intent in self.pageintent) or (intent in self.systemintent) or (intent in self.highlightintent):
                    # 查找页面
                    pagename = slots[0]['normalized_word']
                    if intent in self.pageintent:
                        self.introduction.talkmenuitem_byname(pagename)
                    elif intent in self.systemintent:
                        self.introduction.talkothersystem_byname(pagename)
                    elif intent in self.highlightintent:
                        self.introduction.talkhighlight_byname(pagename)
                elif "ORATOR" in intent:  # 演示整个系统
                    self.introduction.billtalk()
                elif "FAQ_FOUND" in intent and soltslen < 2:  # 问题解答
                    self.isConversationcomplete = False  # 问题不明确
            else:
                self.isConversationcomplete = False  # 词槽不明确
        else:
            self.pardon()
    # 从麦克风收集音频并写入文件
    def _record(self, rate=16000):
        with sr.Microphone(sample_rate=rate) as source:
            # 校准环境噪声水平的energy threshold
            # duration:用于指定计算环境噪声的持续时间（秒）。默认值为1秒。函数将等待指定时间来计算环境噪声水平，并相应地调整麦克风增益，以提高语音识别的准确性。如果噪声水平很高，则可以增加此值以获得更准确的噪声估计。
            # self.r.adjust_for_ambient_noise(source, duration=1)
            print('您可以开始说话了')
            # timeout 用于指定等待语音输入的最长时间（秒），如果没有检测到语音输入，则函数将返回None。默认值为 None，表示等待无限长的时间。如果指定了超时时间，则函数将在等待指定时间后自动返回。
            # phrase_time_limit：用于指定允许单次语音输入的最长时间（秒），如果超过这个时间，函数将自动停止录制，并返回None.默认值为 None，表示允许单次语音输入的时间没有限制。
            audio = self.recognizer.listen(
                source, timeout=20, phrase_time_limit=4)

        # Avoid the same filename under multithreading
        file_name = TmpDir().path() + "speech-" + str(int(time.time())) + ".wav"
        with open(file_name, "wb") as f:
            f.write(audio.get_wav_data())

        return file_name

    
    def begin(self):
        self.isConversationcomplete = False

    def end(self):
        self.isConversationcomplete = True

    def conversation_is_complete(self) -> bool:
        return self.isConversationcomplete   
    
    def activeListen(self):
        """
        主动问一个问题(适用于多轮对话)
        """
        voice=self._record()
        if voice:
            logger.info("调用ARS引擎")
            query = self.asr.transcribe(voice)
            return query
        
        return ""