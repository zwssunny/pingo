from .baseHandler import BaseHandler

class LogoutHandler(BaseHandler):
    def get(self):
        if self.isValidated():
            self.set_secure_cookie("validation", "")
        self.redirect("/login")