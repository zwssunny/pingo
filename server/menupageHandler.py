from .baseHandler import BaseHandler

class MenupageHandler(BaseHandler):
    def get(self):
        if not self.isValidated():
            self.redirect("/login")
        else:
            self.render("menu.html")