import json
from urllib.parse import unquote
from config import conf
from .baseHandler import BaseHandler

class ConfigHandler(BaseHandler):
    def get(self):
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            key = self.get_argument("key", default="")
            res = ""
            if key == "":
                res = {
                    "code": 0,
                    "message": "ok",
                    "config": conf().getText(),
                    "sensitivity": conf().get("sensitivity", 0.5),
                }
            else:
                res = {"code": 0, "message": "ok", "value": conf().get(key)}
            self.write(json.dumps(res))
        self.finish()

    def post(self):
        if self.validate(self.get_argument("validate", default=None)):
            configStr = self.get_argument("config")
            try:
                configStr = unquote(configStr)
                conf().dump(configStr)
                res = {"code": 0, "message": "ok"}
                self.write(json.dumps(res))
            except:
                res = {"code": 1, "message": "json解析失败，请检查内容"}
                self.write(json.dumps(res))
        else:
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        self.finish()
