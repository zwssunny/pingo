import json
import threading
import time
from .baseHandler import BaseHandler
from .chatWebSocketHandler import ChatWebSocketHandler
from gvar import GVar

class OperateHandler(BaseHandler):
    def onPlaybill(self, playstatus, billid, billitemid, msg):
        # 通过 ChatWebSocketHandler 发送给前端
        for client in ChatWebSocketHandler.clients:
            client.send_playstate(playstatus, billid, billitemid, msg)

    def post(self):
        if self.validate(self.get_argument("validate", default=None)):
            type = self.get_argument("type")
            if type in ["restart", "0"]:
                res = {"code": 0, "message": "ok"}
                self.write(json.dumps(res))
                self.finish()
                time.sleep(3)
                threading.Thread(target=lambda: GVar.pingo.restart()).start()
            elif type in ["play", "1"]:
                Billid = self.get_argument("billid")
                BillItemid = self.get_argument("billitemid", default=None)
                res = {"code": 0, "message": "play ok"}
                self.write(json.dumps(res))
                self.finish()
                # 考虑线程执行，否则会等很久
                if BillItemid and int(BillItemid) > 0:
                    threading.Thread(target=lambda: GVar.conversation.talkbillitem_byid(
                        billitemID=BillItemid, onPlaybill=lambda playstatus, billid, billitemid, msg: self.onPlaybill(
                            playstatus, billid, billitemid, msg))).start()
                else:
                    threading.Thread(target=lambda: GVar.conversation.billtalk(
                        billID=Billid, onPlaybill=lambda playstatus, billid, billitemid, msg: self.onPlaybill(
                            playstatus, billid, billitemid, msg))).start()

            elif type in ["pause", "2"]:
                res = {"code": 0, "message": "pause ok"}
                self.write(json.dumps(res))
                self.finish()
                threading.Thread(target=lambda: GVar.conversation.pause()).start()
            elif type in ["unpause", "3"]:
                res = {"code": 0, "message": "unpause ok"}
                self.write(json.dumps(res))
                self.finish()
                threading.Thread(target=lambda: GVar.conversation.unpause()).start()
            elif type in ["stop", "4"]:
                res = {"code": 0, "message": "stop ok"}
                self.write(json.dumps(res))
                self.finish()
                threading.Thread(
                    target=lambda: GVar.conversation.interrupt()).start()
            elif type in ["playstatus", "5"]:
                res = {"code": 0, "message": "get playstatus ok", "playstatus": GVar.conversation.introduction.playstatus,
                       "curbillid": GVar.conversation.introduction.curBillId, "curbillitemid": GVar.conversation.introduction.curBillItemId}
                self.write(json.dumps(res))
                self.finish()
            else:
                res = {"code": 1, "message": f"illegal type {type}"}
                self.write(json.dumps(res))
                self.finish()
        else:
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
            self.finish()