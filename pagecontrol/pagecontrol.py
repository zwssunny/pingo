# encoding:utf-8

import json
import threading
import websocket
from config import conf
from common.log import logger


class pagecontrol(object):
    def __init__(self):
        try:
            pgconf = conf().get("pagecontrol", {"enable": False,
                                                "websocketurl": "ws://10.201.63.153:8081/daasPortal/websocket/", "screenid": "dbe5b0425026446fb52437e8e58ed73f"})
            # websocket
            self.enablecontrol = pgconf["enable"]
            self.websocketurl = pgconf["websocketurl"]
            self.screenid = pgconf["screenid"]
            logger.info("[pagecontrol] inited")
        except Exception as e:
            logger.warn("[pagecontrol] init failed ")
            raise e

    def sendPageCtl(self, intent, eventid):
        """
        创建websocket链接，并发送消息,创建线程，主要考虑不想等待

        :param intent 意图 OPEN_PAGE,OPEN_SYSTEM,OPEN_HIGHLIGHT,CLOSE_PAGE,CLOSE_SYSTEM,CLOSE_HIGHTLIGHT
        :param pageindex 事件编号,如：1，2，3..... 具体看配置

        """
        if self.enablecontrol:
            threading.Thread(target=lambda: self.__sendMessage(
                intent, eventid)).start()

    def __sendMessage(self, intent, eventid):
        """
        创建websocket链接，并发送消息

        :param intent 意图 OPEN_PAGE,OPEN_SYSTEM,OPEN_HIGHLIGHT,CLOSE_PAGE,CLOSE_SYSTEM,CLOSE_HIGHTLIGHT
        :param pageindex 事件编号,如：1，2，3..... 具体看配置

        """
        try:
            # 创建websocket链接
            uri = self.websocketurl + self.screenid
            ws = websocket.WebSocket()
            ws.connect(uri)  # , timeout=6, close_timeout=6
            if ws.connected:
                # 发送控制消息
                sendmsg = {"intent": intent, "pageIndex": eventid}
                msg = json.dumps(sendmsg)
                logger.info(msg)
                ws.send(msg)
                ws.close()
        except Exception as e:
            logger.error(e)
