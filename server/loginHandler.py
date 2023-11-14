import hashlib
from .baseHandler import BaseHandler
from common.log import logger
from gvar import GVar

class LoginHandler(BaseHandler):
    def get(self):
        if self.isValidated():
            self.redirect("/")
        else:
            self.render("login.html", error=None)

    def post(self):
        if self.get_argument("username") == GVar.serverconf["username"] and hashlib.md5(
            self.get_argument("password").encode("utf-8")
        ).hexdigest() == GVar.serverconf["validate"]:
            logger.info("login success")
            self.set_secure_cookie("validation", GVar.serverconf["validate"])
            self.redirect("/")
        else:
            self.render("login.html", error="登录失败")