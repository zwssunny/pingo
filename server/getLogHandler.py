import json

from common.log import readLog
from .baseHandler import BaseHandler

class GetLogHandler(BaseHandler):
    def get(self):
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            lines = self.get_argument("lines", default=200)
            res = {"code": 0, "message": "ok", "log": readLog(lines)}
            self.write(json.dumps(res))
        self.finish()