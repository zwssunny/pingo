# encoding:utf-8
import json
import os
import uuid
from uuid import getnode as get_mac
import requests
from common.log import logger
from pagecontrol.pagecontrol import pagecontrol
from orator.sysintroduction import sysIntroduction
from voice.voice import Voice
from config import conf, load_config

"""利用百度UNIT实现智能对话
    如果命中意图，返回意图对应的回复
    页面操控，系统演示这些技能需要在百度UNIT技能中进行训练
"""


class bgunit:
    def __init__(self, tts: Voice):
        try:
            bgconf = self.loadpageconfig("config.json")
            if not bgconf:
                raise Exception("config.json not found")
            self.service_id = bgconf["service_id"]
            self.api_key = bgconf["api_key"]
            self.secret_key = bgconf["secret_key"]
            self.canpause = conf().get("canpause")
            self.ctlandtalk = conf().get("ctlandtalk")
            # intent
            self.pageintent = bgconf["pageintent"]
            self.systemintent = bgconf["systemintent"]
            self.highlightintent = bgconf["highlightintent"]
            # pagecontrol
            self.pagecontrol = pagecontrol()
            # tts
            self.tts = tts
            #orator
            self.sysIntro = sysIntroduction(tts, self.pagecontrol, self.canpause)
            # pageindex
            # self.pages = self.loadpageconfig("pageindex.json")
            # self.othersystems = self.loadpageconfig("systemindex.json")
            # self.highlights = self.loadpageconfig("highlightindex.json")
            self.pages=self.sysIntro.loadpageindex()
            self.othersystems = self.sysIntro.loadothersystemindex()
            self.highlights=self.sysIntro.loadhighlightindex()

            #UNIT token
            self.access_token = self.get_token()
            self.isConversationcomplete = False  # 该会话是否完成
            logger.info("[BGunit] inited")
        except Exception as e:
            logger.warn("[BGunit] init failed, ignore ")
            raise e

    def chat_with_unit(self, query):
        logger.debug("[BGunit] query: %s" % query)
        parsed = self.getUnit2(query)
        intent = self.getIntent(parsed)
        self.isConversationcomplete = False
        if intent:  # 找到意图
            logger.debug("[BGunit] Baidu_AI Intent= %s", intent)
            reply = self.getSay(parsed)
            print(reply)
            self.tts.text_to_speech_and_play(reply)
            self.isConversationcomplete = True
            slots = self.getSlots(parsed, intent)
            soltslen = len(slots)
            if soltslen > 0:
                if (intent in self.pageintent) or (intent in self.systemintent) or (intent in self.highlightintent):
                    # 查找页面
                    pagename = slots[0]['normalized_word']
                    pageindex = self.getIntentPageindex(intent, pagename)
                    if pageindex > -1:  # 找到页面，就发送消息
                        if self.ctlandtalk: #是否需要解说
                            if intent in self.pageintent:
                                self.sysIntro.talkmenuitem_byname(pagename)
                            elif intent in self.systemintent:
                                self.sysIntro.talkothersystem_byname(pagename)
                            elif intent in self.highlightintent:
                                self.sysIntro.talkhighlight_byname(pagename)
                        else:
                            self.pagecontrol.sendPageCtl(intent, pageindex)
                    else:
                        logger.info("[BGunit] pagename not found!")
                elif "ORATOR" in intent:  # 演示整个系统
                    # platformname = slots[0]['normalized_word']
                    # self.sysIntro.systalk()
                    self.sysIntro.billtalk()
                elif "FAQ_FOUND" in intent and soltslen < 2:  # 问题解答
                    self.isConversationcomplete = False  # 问题不明确
            else:
                self.isConversationcomplete = False  # 词槽不明确
        else:
            reply = "刚才没听清楚,请再说一遍！"
            print(reply)
            self.tts.text_to_speech_and_play(reply)

    def get_help_text(self, **kwargs):
        help_text = "本插件返回对话中意图和词槽，可以操控大屏页面，或者系统演示\n"
        return help_text

    def begin(self):
        self.isConversationcomplete = False

    def end(self):
        self.isConversationcomplete = True

    def conversation_is_complete(self) -> bool:
        return self.isConversationcomplete

    def get_token(self):
        """获取访问百度UUNIT 的access_token
        #param api_key: UNIT apk_key
        #param secret_key: UNIT secret_key
        Returns:
            string: access_token
        """
        url = "https://aip.baidubce.com/oauth/2.0/token?client_id={}&client_secret={}&grant_type=client_credentials".format(
            self.api_key, self.secret_key)
        payload = ""
        headers = {"Content-Type": "application/json",
                   "Accept": "application/json"}

        response = requests.request("POST", url, headers=headers, data=payload)

        # print(response.text)
        return response.json()["access_token"]

    def getUnit(self, query):
        """
        NLU 解析version 3.0
        :param query: 用户的指令字符串
        :returns: UNIT 解析结果。如果解析失败，返回 None
        """

        url = "https://aip.baidubce.com/rpc/2.0/unit/service/v3/chat?access_token=" + \
            self.access_token
        request = {
            "query": query,
            "user_id": str(get_mac())[:32],
            "terminal_id": "88888",
        }
        body = {
            "log_id": str(uuid.uuid1()),
            "version": "3.0",
            "service_id": self.service_id,
            "session_id": str(uuid.uuid1()),
            "request": request,
        }
        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=body, headers=headers)
            return json.loads(response.text)
        except Exception:
            return None

    def getUnit2(self, query):
        """
        NLU 解析 version 2.0

        :param query: 用户的指令字符串
        :returns: UNIT 解析结果。如果解析失败，返回 None
        """
        url = "https://aip.baidubce.com/rpc/2.0/unit/service/chat?access_token=" + self.access_token
        request = {"query": query, "user_id": str(get_mac())[:32]}
        body = {
            "log_id": str(uuid.uuid1()),
            "version": "2.0",
            "service_id": self.service_id,
            "session_id": str(uuid.uuid1()),
            "request": request,
        }
        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=body, headers=headers)
            return json.loads(response.text)
        except Exception:
            return None

    def getIntent(self, parsed):
        """
        提取意图

        :param parsed: UNIT 解析结果
        :returns: 意图数组
        """
        if parsed and "result" in parsed and "response_list" in parsed["result"]:
            try:
                return parsed["result"]["response_list"][0]["schema"]["intent"]
            except Exception as e:
                logger.warning(e)
                return ""
        else:
            return ""

    def hasIntent(self, parsed, intent):
        """
        判断是否包含某个意图

        :param parsed: UNIT 解析结果
        :param intent: 意图的名称
        :returns: True: 包含; False: 不包含
        """
        if parsed and "result" in parsed and "response_list" in parsed["result"]:
            response_list = parsed["result"]["response_list"]
            for response in response_list:
                if "schema" in response and "intent" in response["schema"] and response["schema"]["intent"] == intent:
                    return True
            return False
        else:
            return False

    def getSlots(self, parsed, intent=""):
        """
            提取某个意图的所有词槽

            :param parsed: UNIT 解析结果
            :param intent: 意图的名称
            :returns: 词槽列表。你可以通过 name 属性筛选词槽，
        再通过 normalized_word 属性取出相应的值
        """
        if parsed and "result" in parsed and "response_list" in parsed["result"]:
            response_list = parsed["result"]["response_list"]
            if intent == "":
                try:
                    return parsed["result"]["response_list"][0]["schema"]["slots"]
                except Exception as e:
                    logger.warning(e)
                    return []
            for response in response_list:
                if "schema" in response and "intent" in response["schema"] and "slots" in response["schema"] and response["schema"]["intent"] == intent:
                    return response["schema"]["slots"]
            return []
        else:
            return []

    def getSlotWords(self, parsed, intent, name):
        """
        找出命中某个词槽的内容

        :param parsed: UNIT 解析结果
        :param intent: 意图的名称
        :param name: 词槽名
        :returns: 命中该词槽的值的列表。
        """
        slots = self.getSlots(parsed, intent)
        words = []
        for slot in slots:
            if slot["name"] == name:
                words.append(slot["normalized_word"])
        return words

    def getSayByConfidence(self, parsed):
        """
        提取 UNIT 置信度最高的回复文本

        :param parsed: UNIT 解析结果
        :returns: UNIT 的回复文本
        """
        if parsed and "result" in parsed and "response_list" in parsed["result"]:
            response_list = parsed["result"]["response_list"]
            answer = {}
            for response in response_list:
                if (
                    "schema" in response
                    and "intent_confidence" in response["schema"]
                    and (not answer or response["schema"]["intent_confidence"] > answer["schema"]["intent_confidence"])
                ):
                    answer = response
            return answer["action_list"][0]["say"]
        else:
            return ""

    def getSay(self, parsed, intent=""):
        """
        提取 UNIT 的回复文本

        :param parsed: UNIT 解析结果
        :param intent: 意图的名称
        :returns: UNIT 的回复文本
        """
        if parsed and "result" in parsed and "response_list" in parsed["result"]:
            response_list = parsed["result"]["response_list"]
            if intent == "":
                try:
                    return response_list[0]["action_list"][0]["say"]
                except Exception as e:
                    logger.warning(e)
                    return ""
            for response in response_list:
                if "schema" in response and "intent" in response["schema"] and response["schema"]["intent"] == intent:
                    try:
                        return response["action_list"][0]["say"]
                    except Exception as e:
                        logger.warning(e)
                        return ""
            return ""
        else:
            return ""

    def loadpageconfig(self, configfile) -> dict:  # 读取配置参数文件
        """
        加载配置文件，返回词典
        :param configfile 配置文件名称，当前目录中找
        :returns 词典key-value对
        """
        curdir = os.path.dirname(__file__)
        config_path = os.path.join(curdir, configfile)
        bconf = None
        if os.path.exists(config_path):  # 如果存在
            with open(config_path, "r", encoding="UTF-8") as fr:
                bconf = json.load(fr)
        return bconf

    def getIntentPageindex(self, intent, pagename) -> int:
        """
        返回页面编号
        :param intent 意图：OPEN_PAGE,CLOSE_PAGE,......
        :param pagename 页面名称或者菜单名称
        :returns 页面编号
        """
        pageindex = -1
        if intent in self.pageintent:  # 在页面中查找
            pageindex = self.pages.get(pagename, -1)
        elif intent in self.systemintent:  # 在第三方系统菜单中查找
            pageindex = self.othersystems.get(pagename, -1)
        elif intent in self.highlightintent:  # 在亮点场景中查找
            pageindex = self.highlights.get(pagename, -1)
        return pageindex
