import json
from .baseHandler import BaseHandler
from gvar import GVar

class GetHistoryHandler(BaseHandler):
    def get(self):
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            res = {
                "code": 0,
                "message": "ok",
                "history": json.dumps(GVar.conversation.getHistory().cache),
            }
            self.write(json.dumps(res))
        self.finish()