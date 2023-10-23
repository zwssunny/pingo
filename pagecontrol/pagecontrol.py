# encoding:utf-8
import json
import os
import json
import websocket
from common.log import logger

class pagecontrol(object):
    def __init__(self):
        try:
            conf = self.loadconfig("config.json")
            if not conf:
                raise Exception("config.json not found")
            # websocket
            self.websocketurl = conf["websocketurl"]
            self.screenid = conf["screenid"]
            logger.info("[pagecontrol] inited")
        except Exception as e:
            logger.warn("[pagecontrol] init failed ")
            raise e
    
    def sendPageCtl(self, intent, eventid):
        """
        创建websocket链接，并发送消息
        
        :param intent 意图 OPEN_PAGE,OPEN_SYSTEM,OPEN_HIGHLIGHT,CLOSE_PAGE,CLOSE_SYSTEM,CLOSE_HIGHTLIGHT
        :param pageindex 事件编号,如：1，2，3..... 具体看配置

        """
        try:
            # 创建websocket链接
            uri = self.websocketurl+self.screenid
            ws = websocket.WebSocket()
            ws.connect(uri, timeout=6, close_timeout=6)
            # 发送控制消息
            sendmsg = {"intent": intent, "pageIndex": eventid}
            msg = json.dumps(sendmsg)
            logger.info(msg)
            ws.send(msg)
        except Exception as e:
            logger.warning(e)

    def loadconfig(self, configfile) -> dict:  # 读取配置参数文件
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