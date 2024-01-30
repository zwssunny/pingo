import os
import threading
import ssl
import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver

from common.log import logger

from common import utils
from .apiHandler import APIHandler
from .billItemsHandler import BillItemsHandler
from .billpageHandler import BillpageHandler
from .billsHandler import BillsHandler
from .chatHandler import ChatHandler
from .chatWebSocketHandler import ChatWebSocketHandler
from .configHandler import ConfigHandler
from .configPageHandler import ConfigPageHandler
from .getHistoryHandler import GetHistoryHandler
from .getLogHandler import GetLogHandler
from .logPageHandler import LogPageHandler
from .loginHandler import LoginHandler
from .logoutHandler import LogoutHandler
from .mainHandler import MainHandler
from .messageUpdatesHandler import MessageUpdatesHandler
from .operateHandler import OperateHandler
from .switchEnableStatusHandler import SwitchEnableStatusHandler
from .voiceHandler import VoiceHandler
from .menuHandler import MenuHandler
from .menuItemsHandler import MenuItemsHandler
from .menupageHandler import MenupageHandler

from gvar import GVar

webApp=None


settings = {
    "cookie_secret": GVar.serverconf["cookie_secret"],
    "template_path": os.path.join(utils.APP_PATH, "server", "templates"),
    "static_path": os.path.join(utils.APP_PATH, "server", "static"),
    "login_url": "/login",
    "debug": False,
}
#新增的接口在这里注册
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
        (r"/menu", MenuHandler),
        (r"/menuitems", MenuItemsHandler),
        (r"/menupage", MenupageHandler),
        (
            r"/photo/(.+\.(?:png|jpg|jpeg|bmp|gif|JPG|PNG|JPEG|BMP|GIF))",
            tornado.web.StaticFileHandler,
            {"path": os.path.join(utils.APP_PATH,"server","static")},
        ),
        (
            r"/audio/(.+\.(?:mp3|wav|pcm))",
            tornado.web.StaticFileHandler,
            {"path": os.path.join(utils.CACH_PATH, utils.VOICENAME)},
        ),
        (r"/static/(.*)", tornado.web.StaticFileHandler,
         {"path": os.path.join(utils.APP_PATH,"server","static")}),
    ],
    **settings,
)


def start_server():
    global webApp
    if GVar.serverconf["enable"]:
        port = GVar.serverconf["port"]
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


def run(debug=False):
    settings["debug"] = debug
    threading.Thread(target=lambda: start_server()).start()


def stop():
    if webApp:
        webApp.stop()
        tornado.ioloop.IOLoop.current().close()
