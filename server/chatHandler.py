import base64
import json
import threading

from common import utils
from .baseHandler import BaseHandler
from .chatWebSocketHandler import ChatWebSocketHandler
from gvar import GVar

class ChatHandler(BaseHandler):
    def onResp(self, msg, audio, plugin):
        # logger.info(f"response msg: {msg}")
        res = {
            "code": 0,
            "message": "ok",
            "resp": msg,
            "audio": audio,
            "plugin": plugin,
        }
        try:
            self.write(json.dumps(res))
            self.flush()
        except:
            pass

    def onStream(self, data, uuid):
        # 通过 ChatWebSocketHandler 发送给前端
        for client in ChatWebSocketHandler.clients:
            client.send_response(data, uuid, "")

    def post(self):
        if self.validate(self.get_argument("validate", default=None)):
            if self.get_argument("type") == "text":
                query = self.get_argument("query")
                uuid = self.get_argument("uuid")
                if query == "":
                    res = {"code": 1, "message": "query text is empty"}
                    self.write(json.dumps(res))
                else:
                    t = threading.Thread(target=lambda:
                                         GVar.conversation.doResponse(
                                             query,
                                             uuid,
                                             onSay=lambda msg, audio, plugin: self.onResp(
                                                 msg, audio, plugin
                                             ),
                                             onStream=lambda data, resp_uuid: self.onStream(
                                                 data, resp_uuid)

                                         ))
                    t.start()

            elif self.get_argument("type") == "voice":
                voice_data = self.get_argument("voice")
                tmpfile = utils.write_temp_file(
                    base64.b64decode(voice_data), ".wav")
                # downsampling
                nfile = utils.sounddownsampling(tmpfile)
                # utils.check_and_delete(tmpfile)
                t = threading.Thread(target=lambda:
                                     GVar.conversation.doConverse(
                                         nfile,
                                         onSay=lambda msg, audio, plugin: self.onResp(
                                             msg, audio, plugin),
                                         onStream=lambda data, resp_uuid: self.onStream(
                                             data, resp_uuid)

                                     ))
                t.start()
            else:
                res = {"code": 1, "message": "illegal type"}
                self.write(json.dumps(res))
        else:
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        self.finish()