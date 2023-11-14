import json
from .baseHandler import BaseHandler
from gvar import GVar

class VoiceHandler(BaseHandler):
    def post(self):
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            voice = self.get_argument("voice", default=None)
            if voice:
                GVar.conversation.testvoice(voice=voice, text="您好，您听到的是方案设定声音")
            else:
                GVar.conversation.testvoice(text="您好，您听到的是系统默认声音")
            res = {"code": 0, "message": "音调测试"}
            self.write(json.dumps(res))
        self.finish()