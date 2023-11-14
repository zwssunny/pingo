from config import conf
from .baseHandler import BaseHandler

class ConfigPageHandler(BaseHandler):
    def get(self):
        if not self.isValidated():
            self.redirect("/login")
        else:
            self.render("config.html", sensitivity=conf().get("sensitivity"))