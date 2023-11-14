from .baseHandler import BaseHandler

class LogPageHandler(BaseHandler):
    def get(self):
        if not self.isValidated():
            self.redirect("/login")
        else:
            self.render("log.html")