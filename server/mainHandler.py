import random
from .baseHandler import BaseHandler
from gvar import GVar

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

class MainHandler(BaseHandler):
    def get(self):
        if not self.isValidated():
            self.redirect("/login")
            return
        if GVar.conversation:
            suggestion = random.choice(suggestions)
            self.render(
                "index.html",
                suggestion=suggestion,
                location=self.request.host,
            )
        else:
            self.render("index.html")