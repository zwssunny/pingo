import tornado
from gvar import GVar

class BaseHandler(tornado.web.RequestHandler):
    def isValidated(self):
        if not self.get_secure_cookie("validation"):
            return False
        return str(
            self.get_secure_cookie("validation"), encoding="utf-8"
        ) == GVar.serverconf["validate"]

    def validate(self, validation):
        if validation and '"' in validation:
            validation = validation.replace('"', "")
        return validation == GVar.serverconf["validate"] or validation == str(
            self.get_cookie("validation")
        )