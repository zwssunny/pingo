import os
import json
import time
import base64
import random
import hashlib
import asyncio
import requests
import markdown
import threading
import subprocess
import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver

from tornado.websocket import WebSocketHandler
from urllib.parse import unquote

from config import conf, load_config, read_file
from common.log import logger, readLog
from robot import History
from common import utils


conversation, pingo = None, None

suggestions = [
    "开始演示",
    "平台特点",
    "融合平台",
    "亮点场景",
    "相关系统",
    "打开综合交通",
    "打开首页",
    "打开公交",
]

#加载参数
load_config()
serverconf=conf().get("server")

class BaseHandler(tornado.web.RequestHandler):
    def isValidated(self):
        if not self.get_secure_cookie("validation"):
            return False
        return str(
            self.get_secure_cookie("validation"), encoding="utf-8"
        ) == serverconf["validate"]

    def validate(self, validation):
        if validation and '"' in validation:
            validation = validation.replace('"', "")
        return validation == serverconf["validate"] or validation == str(
            self.get_cookie("validation")
        )


class MainHandler(BaseHandler):
    def get(self):
        global conversation, pingo, suggestions
        if not self.isValidated():
            self.redirect("/login")
            return
        if conversation:
            suggestion = random.choice(suggestions)
            self.render(
                "index.html",
                suggestion=suggestion,
                location=self.request.host,
            )
        else:
            self.render("index.html")


class MessageUpdatesHandler(BaseHandler):
    """Long-polling request for new messages.

    Waits until new messages are available before returning anything.
    """

    async def post(self):
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            cursor = self.get_argument("cursor", None)
            history = History.History()
            messages = history.get_messages_since(cursor)
            while not messages:
                # Save the Future returned here so we can cancel it in
                # on_connection_close.
                self.wait_future = history.cond.wait(timeout=1)
                try:
                    await self.wait_future
                except asyncio.CancelledError:
                    return
                messages = history.get_messages_since(cursor)
            if self.request.connection.stream.closed():
                return
            res = {"code": 0, "message": "ok", "history": json.dumps(messages)}
            self.write(json.dumps(res))
        self.finish()

    def on_connection_close(self):
        self.wait_future.cancel()


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


class ChatHandler(BaseHandler):
    def onResp(self, msg, audio, plugin):
        logger.info(f"response msg: {msg}")
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
        global conversation
        if self.validate(self.get_argument("validate", default=None)):
            if self.get_argument("type") == "text":
                query = self.get_argument("query")
                uuid = self.get_argument("uuid")
                if query == "":
                    res = {"code": 1, "message": "query text is empty"}
                    self.write(json.dumps(res))
                else:
                    conversation.doResponse(
                        query,
                        uuid,
                        onSay=lambda msg, audio, plugin: self.onResp(
                            msg, audio, plugin
                        ),
                        onStream=lambda data, resp_uuid: self.onStream(data, resp_uuid),
                    )

            elif self.get_argument("type") == "voice":
                voice_data = self.get_argument("voice")
                tmpfile = utils.write_temp_file(base64.b64decode(voice_data), ".wav")
                # fname, suffix = os.path.splitext(tmpfile)
                # nfile = fname + "-16k" + suffix
                # downsampling
                # soxCall = "sox " + tmpfile + " " + nfile + " rate 16k"
                # subprocess.call([soxCall], shell=True, close_fds=True)
                # utils.check_and_delete(tmpfile)
                conversation.doConverse(
                    tmpfile,
                    onSay=lambda msg, audio, plugin: self.on_resp(msg, audio, plugin),
                    onStream=lambda data, resp_uuid: self.onStream(
                        data, resp_uuid)

                )
            else:
                res = {"code": 1, "message": "illegal type"}
                self.write(json.dumps(res))
        else:
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        self.finish()


class GetHistoryHandler(BaseHandler):
    def get(self):
        global conversation
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            res = {
                "code": 0,
                "message": "ok",
                "history": json.dumps(conversation.getHistory().cache),
            }
            self.write(json.dumps(res))
        self.finish()


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


class LogPageHandler(BaseHandler):
    def get(self):
        if not self.isValidated():
            self.redirect("/login")
        else:
            self.render("log.html")


class OperateHandler(BaseHandler):
    def post(self):
        global pingo
        if self.validate(self.get_argument("validate", default=None)):
            type = self.get_argument("type")
            if type in ["restart", "0"]:
                res = {"code": 0, "message": "ok"}
                self.write(json.dumps(res))
                self.finish()
                time.sleep(3)
                pingo.restart()
            else:
                res = {"code": 1, "message": f"illegal type {type}"}
                self.write(json.dumps(res))
                self.finish()
        else:
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
            self.finish()


class ConfigPageHandler(BaseHandler):
    def get(self):
        if not self.isValidated():
            self.redirect("/login")
        else:
            self.render("config.html", sensitivity=conf().get("sensitivity"))


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
                cfg = unquote(configStr)
                # cfg=yaml.safe_load(cfg)
                cfg=json.loads(cfg)
                conf().dump(cfg)
                res = {"code": 0, "message": "ok"}
                self.write(json.dumps(res))
            except:
                res = {"code": 1, "message": "json解析失败，请检查内容"}
                self.write(json.dumps(res))
        else:
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        self.finish()



class APIHandler(BaseHandler):
    def get(self):
        if not self.isValidated():
            self.redirect("/login")
        else:
            content = ""
            #直接读本地文档
            # r = requests.get("/api.md")
            filepath=os.path.join(utils.APP_PATH, "server/templates/api.md")
            rtext=read_file(filepath)
            content = markdown.markdown(
                rtext,
                extensions=[
                    "codehilite",
                    "tables",
                    "fenced_code",
                    "meta",
                    "nl2br",
                    "toc",
                ],
            )
            self.render("api.html", content=content)

class LoginHandler(BaseHandler):
    def get(self):
        if self.isValidated():
            self.redirect("/")
        else:
            self.render("login.html", error=None)

    def post(self):
        if self.get_argument("username") == serverconf["username"] and hashlib.md5(
            self.get_argument("password").encode("utf-8")
        ).hexdigest() == serverconf["validate"]:
            logger.info("login success")
            self.set_secure_cookie("validation", serverconf["validate"])
            self.redirect("/")
        else:
            self.render("login.html", error="登录失败")


class LogoutHandler(BaseHandler):
    def get(self):
        if self.isValidated():
            self.set_secure_cookie("validation", "")
        self.redirect("/login")


settings = {
    "cookie_secret": serverconf["cookie_secret"],
    "template_path": os.path.join(utils.APP_PATH, "server/templates"),
    "static_path": os.path.join(utils.APP_PATH, "server/static"),
    "login_url": "/login",
    "debug": False,
}

application = tornado.web.Application(
    [
        (r"/", MainHandler),
        (r"/login", LoginHandler),
        (r"/history", GetHistoryHandler),
        (r"/chat", ChatHandler),
        (r"/websocket", ChatWebSocketHandler),
        (r"/chat/updates", MessageUpdatesHandler),
        (r"/config", ConfigHandler),
        (r"/configpage", ConfigPageHandler),
        (r"/operate", OperateHandler),
        (r"/logpage", LogPageHandler),
        (r"/log", GetLogHandler),
        (r"/logout", LogoutHandler),
        (r"/api", APIHandler),
        (
            r"/photo/(.+\.(?:png|jpg|jpeg|bmp|gif|JPG|PNG|JPEG|BMP|GIF))",
            tornado.web.StaticFileHandler,
            {"path": "server/static"},
        ),
        (
            r"/audio/(.+\.(?:mp3|wav|pcm))",
            tornado.web.StaticFileHandler,
            {"path": utils.CACH_PATH},
        ),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "server/static"}),
    ],
    **settings,
)


def start_server(con, pg):
    global conversation, pingo
    conversation = con
    pingo = pg
    if serverconf["enable"]:
        port =serverconf["port"]
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
            application.listen(int(port))
            tornado.ioloop.IOLoop.instance().start()
        except Exception as e:
            logger.critical(f"服务器启动失败: {e}", stack_info=True)


def run(conversation, pingo, debug=False):
    settings["debug"] = debug
    t = threading.Thread(target=lambda: start_server(conversation, pingo))
    t.start()
