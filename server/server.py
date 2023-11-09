import os
import json
import time
import base64
import random
import hashlib
import asyncio
import sqlite3
import markdown
import threading
import ssl
import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver

from tornado.websocket import WebSocketHandler
from urllib.parse import unquote
from common.tmp_dir import TmpDir

from config import conf, load_config, read_file
from common.log import logger, readLog
from robot import History
from common import utils


conversation, pingo, webApp = None, None, None

suggestions = [
    "开始演示",
    "平台特点",
    "融合平台",
    "亮点场景",
    "智慧交通",
    "打开综合交通",
    "打开首页",
    "打开公交",
]

sysdb = "./db/pingo.db"
# 加载参数
load_config()
serverconf = conf().get("server")


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

    def send_playstate(self, playstatus, msg=""):
        response = {
            "action": "playoperate",
            "playstatus": playstatus,
            "text": msg,
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

    def onPlaybill(self, playstatus, msg):
        # 通过 ChatWebSocketHandler 发送给前端
        for client in ChatWebSocketHandler.clients:
            client.send_playstate(playstatus, msg)

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
                    t = threading.Thread(target=lambda:
                                         conversation.doResponse(
                                             query,
                                             uuid,
                                             onSay=lambda msg, audio, plugin: self.onResp(
                                                 msg, audio, plugin
                                             ),
                                             onStream=lambda data, resp_uuid: self.onStream(
                                                 data, resp_uuid),
                                             onPlaybill=lambda playstatus, msg: self.onPlaybill(
                                                 playstatus, msg)
                                         ))
                    t.start()

            elif self.get_argument("type") == "voice":
                voice_data = self.get_argument("voice")
                # tmpfile = utils.write_temp_file(
                #     base64.b64decode(voice_data), ".wav")
                tmpfile = TmpDir().path() + "speech-" + str(int(time.time())) + ".wav"
                with open(tmpfile, "wb") as f:
                    f.write(base64.b64decode(voice_data))
                # fname, suffix = os.path.splitext(tmpfile)
                # nfile = fname + "-16k" + suffix
                # downsampling
                # soxCall = "sox " + tmpfile + " " + nfile + " rate 16k"
                # subprocess.call([soxCall], shell=True, close_fds=True)
                # utils.check_and_delete(tmpfile)
                t = threading.Thread(target=lambda:
                                     conversation.doConverse(
                                         tmpfile,
                                         onSay=lambda msg, audio, plugin: self.onResp(
                                             msg, audio, plugin),
                                         onStream=lambda data, resp_uuid: self.onStream(
                                             data, resp_uuid),
                                         onPlaybill=lambda playstatus, msg: self.onPlaybill(
                                             playstatus, msg)

                                     ))
                t.start()
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
        global conversation, pingo
        if self.validate(self.get_argument("validate", default=None)):
            type = self.get_argument("type")
            if type in ["restart", "0"]:
                res = {"code": 0, "message": "ok"}
                self.write(json.dumps(res))
                self.finish()
                time.sleep(3)
                threading.Thread(target=lambda: pingo.restart()).start()
            elif type in ["play", "1"]:
                Billid = self.get_argument("billid")
                res = {"code": 0, "message": "play ok"}
                self.write(json.dumps(res))
                self.finish()
                # 考虑线程执行，否则会等很久
                t = threading.Thread(target=lambda: conversation.billtalk(
                    billID=Billid))
                t.start()
            elif type in ["pause", "2"]:
                res = {"code": 0, "message": "pause ok"}
                self.write(json.dumps(res))
                self.finish()
                threading.Thread(target=lambda: conversation.pause()).start()
            elif type in ["unpause", "3"]:
                res = {"code": 0, "message": "unpause ok"}
                self.write(json.dumps(res))
                self.finish()
                threading.Thread(target=lambda: conversation.unpause()).start()
            elif type in ["stop", "4"]:
                res = {"code": 0, "message": "stop ok"}
                self.write(json.dumps(res))
                self.finish()
                threading.Thread(
                    target=lambda: conversation.interrupt()).start()
            elif type in ["playstatus", "5"]:
                res = {"code": 0, "message": "get playstatus ok", "playstatus": conversation.introduction.playstatus,
                       "curbillid": conversation.introduction.curBillId}
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


class APIHandler(BaseHandler):
    def get(self):
        if not self.isValidated():
            self.redirect("/login")
        else:
            content = ""
            # 直接读本地文档
            # r = requests.get("/api.md")
            filepath = os.path.join(utils.APP_PATH, "server/templates/api.md")
            rtext = read_file(filepath)
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


class BillpageHandler(BaseHandler):
    def get(self):
        if not self.isValidated():
            self.redirect("/login")
        else:
            bills = []
            conn = sqlite3.connect(sysdb, check_same_thread=False)
            cursor = conn.execute("SELECT ID, NAME,ISDEFAULT FROM BILL")
            billscursor = cursor.fetchall()
            for bill in billscursor:
                billjson = {"ID": bill[0],
                            "NAME": bill[1], "ISDEFAULT": bill[2]}
                bills.append(billjson)
            conn.close()
            self.render("bill.html", bills=bills)


class BillsHandler(BaseHandler):
    def get(self):
        if not self.isValidated():
            self.redirect("/login")
        else:
            billid = self.get_argument("billid", default=None)
            bills = []
            conn = sqlite3.connect(sysdb, check_same_thread=False)
            if billid is None:
                cursor = conn.execute(
                    "SELECT ID, NAME,ISDEFAULT, VOICE, DATETIME,DESC FROM BILL")
            else:
                cursor = conn.execute(
                    "SELECT ID, NAME,ISDEFAULT, VOICE, DATETIME,DESC FROM BILL WHERE ID= ?", (billid,))
            billscursor = cursor.fetchall()
            for bill in billscursor:
                billjson = {"ID": bill[0],
                            "NAME": bill[1], "ISDEFAULT": bill[2], "VOICE": bill[3], "DATETIME": bill[4], "DESC": bill[5]}
                bills.append(billjson)
            conn.close()
            self.write(json.dumps(bills))
        self.finish()
    # 更新演讲方案

    def post(self):
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            id = self.get_argument("id")
            name = self.get_argument("name")
            isdefault = self.get_argument("isdefault")
            voice = self.get_argument("voice")
            datetime = self.get_argument("datetime")
            desc = unquote(self.get_argument("desc"))
            conn = sqlite3.connect(sysdb, check_same_thread=False)
            cursor = conn.cursor()
            # 默认只能有一条记录
            if int(isdefault) == 1:
                sql = "UPDATE BILL SET isdefault=0 WHERE isdefault=1 and ID<>? "
                cursor.execute(sql, (id,))
            sql = "UPDATE BILL SET  name=?,voice=?,isdefault=?,datetime=?, DESC=? WHERE ID=? "
            cursor.execute(sql, (name, voice, isdefault, datetime, desc, id,))
            conn.commit()
            conn.close()
            # logger.log(desc)
            res = {"code": 0, "message": "更新演讲方案"}
            self.write(json.dumps(res))
        self.finish()
    # 克隆演讲方案

    def put(self):
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            id = self.get_argument("id")
            conn = sqlite3.connect(sysdb, check_same_thread=False)
            cursor = conn.cursor()
            sql = "INSERT INTO BILL(NAME,VOICE,DATETIME,ISDEFAULT,DESC) SELECT  NAME||'-克隆',VOICE,datetime(CURRENT_TIMESTAMP,'localtime'),0,DESC FROM BILL WHERE ID=? "
            cursor.execute(sql, (id,))
            sql = "SELECT LAST_INSERT_ROWID()"
            cursor.execute(sql)
            newbillcursor = cursor.fetchone()
            if newbillcursor:
                newbillid = newbillcursor[0]
                if int(newbillid) > 0:
                    sql = "INSERT INTO BILLITEM(BILLID,TYPENAME,TYPEID,ORDERNO,ENABLE,SLEEP,DESC) SELECT ?,TYPENAME,TYPEID,ORDERNO,ENABLE,SLEEP,DESC from BILLITEM WHERE BILLID=? "
                    cursor.execute(sql, (newbillid, id,))
                    conn.commit()
            else:
                conn.rollback()
            conn.close()

            res = {"code": 0, "newbillid": newbillid, "message": "克隆演讲方案"}
            self.write(json.dumps(res))
        self.finish()


class BillItemsHandler(BaseHandler):
    def get(self):
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            billID = self.get_argument("billid")
            itemID = self.get_argument("itemid", default=None)
            billItems = []
            if billID and itemID:
                conn = sqlite3.connect(sysdb, check_same_thread=False)
                cursor = conn.execute("SELECT *, (CASE WHEN TYPENAME=='MENUITEM' THEN (SELECT NAME FROM MENUITEM WHERE ID=TYPEID)"
                                      " WHEN TYPENAME=='OTHERSYSTEM' THEN (SELECT NAME FROM OTHERSYSTEM WHERE ID=TYPEID)"
                                      " ELSE (SELECT NAME FROM FEATURES WHERE ID=TYPEID) END ) AS NAME FROM BILLITEM WHERE BILLID= ? AND ID= ? ORDER BY ORDERNO", (billID, itemID,))
                Itemcursor = cursor.fetchone()
                if Itemcursor:
                    itemjson = {"ID": Itemcursor[0], "BILLID": Itemcursor[1], "TYPENAME": Itemcursor[2], "TYPEID": Itemcursor[3],
                                "ORDERNO": Itemcursor[4], "ENABLE": Itemcursor[5], "DESC": Itemcursor[6], "NAME": Itemcursor[8], "SLEEP": Itemcursor[7]}
                    billItems.append(itemjson)
                conn.close()
            else:
                conn = sqlite3.connect(sysdb, check_same_thread=False)
                cursor = conn.execute("SELECT *, (CASE WHEN TYPENAME=='MENUITEM' THEN (SELECT NAME FROM MENUITEM WHERE ID=TYPEID)"
                                      " WHEN TYPENAME=='OTHERSYSTEM' THEN (SELECT NAME FROM OTHERSYSTEM WHERE ID=TYPEID)"
                                      " ELSE (SELECT NAME FROM FEATURES WHERE ID=TYPEID) END ) AS NAME FROM BILLITEM WHERE BILLID= ? ORDER BY ORDERNO", (billID,))
                billItemscursor = cursor.fetchall()
                for item in billItemscursor:
                    itemjson = {"ID": item[0], "BILLID": item[1], "TYPENAME": item[2], "TYPEID": item[3],
                                "ORDERNO": item[4], "ENABLE": item[5], "DESC": item[6], "NAME": item[8], "SLEEP": item[7]}
                    billItems.append(itemjson)
                conn.close()

            self.write(json.dumps(billItems))
        self.finish()
    # 更新节点

    def post(self):
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            id = self.get_argument("id")
            orderno = self.get_argument("orderno")
            sleep = self.get_argument("sleep")
            desc = unquote(self.get_argument("desc"))
            conn = sqlite3.connect(sysdb, check_same_thread=False)
            cursor = conn.cursor()
            sql = "UPDATE BILLITEM SET ORDERNO=?, SLEEP=?,DESC=? WHERE ID=? "
            cursor.execute(sql, (orderno, sleep, desc, id,))
            conn.commit()
            # logger.log(desc)
            res = {"code": 0, "message": "更新节点"}
            self.write(json.dumps(res))
        self.finish()
    # 新增节点

    def put(self):
        # pass
        self.finish()
    # 删除节点

    def delete(self):
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            id = self.get_argument("id")
            conn = sqlite3.connect(sysdb, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM BILLITEM WHERE ID=? ", (id,))
            conn.commit()
            # logger.log(desc)
            res = {"code": 0, "message": "删除节点"}
            self.write(json.dumps(res))
        self.finish()


class VoiceHandler(BaseHandler):
    def post(self):
        global conversation
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            voice = self.get_argument("voice", default=None)
            if voice:
                conversation.testvoice(voice=voice, text="您好，您听到的是方案设定声音")
            else:
                conversation.testvoice(text="您好，您听到的是系统默认声音")
            res = {"code": 0, "message": "删除节点"}
            self.write(json.dumps(res))
        self.finish()


class SwitchEnableStatusHandler(BaseHandler):
    # 更新节点
    def post(self):
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            id = self.get_argument("id")
            enable = self.get_argument("enable")
            conn = sqlite3.connect(sysdb, check_same_thread=False)
            cursor = conn.cursor()
            sql = "UPDATE BILLITEM SET ENABLE=? WHERE ID=? "
            cursor.execute(sql, (enable, id,))
            conn.commit()
            # logger.log(desc)
            res = {"code": 0, "message": "更新节点"}
            self.write(json.dumps(res))
        self.finish()


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
        (r"/bills", BillsHandler),
        (r"/billpage", BillpageHandler),
        (r"/billitems", BillItemsHandler),
        (r"/switchenable", SwitchEnableStatusHandler),
        (r"/voice", VoiceHandler),
        (
            r"/photo/(.+\.(?:png|jpg|jpeg|bmp|gif|JPG|PNG|JPEG|BMP|GIF))",
            tornado.web.StaticFileHandler,
            {"path": "server/static"},
        ),
        (
            r"/audio/(.+\.(?:mp3|wav|pcm))",
            tornado.web.StaticFileHandler,
            {"path": os.path.join(utils.CACH_PATH, utils.VOICENAME)},
        ),
        (r"/static/(.*)", tornado.web.StaticFileHandler,
         {"path": "server/static"}),
    ],
    **settings,
)


def start_server(con, pg):
    global conversation, pingo
    global webApp
    conversation = con
    pingo = pg
    if serverconf["enable"]:
        port = serverconf["port"]
        try:

            # 启用 SSL/TLS
            ssl_path_crt = os.path.join(utils.APP_PATH, 'pem', 'pingo.crt')
            ssl_path_key = os.path.join(utils.APP_PATH, 'pem', 'pingo.key')
            ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_ctx.load_cert_chain(
                certfile=ssl_path_crt, keyfile=ssl_path_key)

            webApp = tornado.httpserver.HTTPServer(
                application, ssl_options=ssl_ctx)
            webApp.listen(int(port))
            tornado.ioloop.IOLoop.current().start()
        except Exception as e:
            logger.critical(f"服务器启动失败: {e}", stack_info=True)


def run(conversation, pingo, debug=False):
    settings["debug"] = debug
    threading.Thread(target=lambda: start_server(conversation, pingo)).start()


def stop():
    global webApp
    if webApp:
        webApp.stop()
        tornado.ioloop.IOLoop.current().close()
