import os

import markdown

from common import utils
from config import read_file
from .baseHandler import BaseHandler

class APIHandler(BaseHandler):
    def get(self):
        if not self.isValidated():
            self.redirect("/login")
        else:
            content = ""
            # 直接读本地文档
            # r = requests.get("/api.md")
            filepath = os.path.join(utils.TEMPLATE_PATH, "api.md")
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