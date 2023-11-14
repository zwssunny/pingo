
import json
from tornado.websocket import WebSocketHandler
from .baseHandler import BaseHandler

"""
负责跟前端通信，把机器人的响应内容传输给前端
"""
class ChatWebSocketHandler(WebSocketHandler, BaseHandler):
    clients = set()

    def open(self):
        self.clients.add(self)

    def on_close(self):
        self.clients.remove(self)

    def send_response(self, msg, uuid, plugin=""):
        response = {
            "action": "new_message",
            "type": 1,
            "text": msg,
            "uuid": uuid,
            "plugin": plugin,
        }
        self.write_message(json.dumps(response))

    def send_playstate(self, playstatus, billid=None, billitemid=None, msg=''):
        response = {
            "action": "playoperate",
            "playstatus": playstatus,
            "billid": billid,
            "billitemid": billitemid,
            "text": msg,
        }
        self.write_message(json.dumps(response))