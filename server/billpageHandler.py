from .baseHandler import BaseHandler
import sqlite3
from common.log import logger
from gvar import GVar

class BillpageHandler(BaseHandler):
    def get(self):
        if not self.isValidated():
            self.redirect("/login")
        else:
            try:
                bills = []
                conn = sqlite3.connect(GVar.sysdb, check_same_thread=False)
                cursor = conn.execute("SELECT ID, NAME,ISDEFAULT FROM BILL")
                billscursor = cursor.fetchall()
                for bill in billscursor:
                    billjson = {"ID": bill[0],
                                "NAME": bill[1], "ISDEFAULT": bill[2]}
                    bills.append(billjson)
            except Exception as error:
                logger.error(error)
            finally:
                conn and conn.close()
            self.render("bill.html", bills=bills)