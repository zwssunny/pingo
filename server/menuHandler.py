import json
import threading
import sqlite3
from .baseHandler import BaseHandler
from common.log import logger
from gvar import GVar

class MenuHandler(BaseHandler):
    #播放控制
    def post(self):
        if self.validate(self.get_argument("validate", default=None)):
            type = self.get_argument("type")
            if type in ["play", "1"]:
                MenuItemid = self.get_argument("menuitemid", default=None)
                res = {"code": 0, "message": "play ok"}
                self.write(json.dumps(res))
                if MenuItemid and int(MenuItemid) > 0:
                    threading.Thread(target=lambda: GVar.conversation.introduction.talkmenuitem_byid(MenuItemid)).start()
            elif type in ["stop", "4"]:
                res = {"code": 0, "message": "stop ok"}
                self.write(json.dumps(res))
                threading.Thread(
                    target=lambda: GVar.conversation.interrupt()).start()
        else:
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        self.finish()
        
    # 禁用状态变换
    def put(self):
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            try:
                id = self.get_argument("id")
                enable = self.get_argument("enable")
                conn = sqlite3.connect(GVar.sysdb, check_same_thread=False)
                cursor = conn.cursor()
                sql = "UPDATE MENUITEM SET ENABLE=? WHERE ID=? "
                cursor.execute(sql, (enable, id,))
                conn.commit()
                res = {"code": 0, "message": "更新节点"}
            except Exception as error:
                logger.error(error)
                conn and conn.rollback()
                res = {"code": 1, "message": "更新节点出错"}
            finally:
                conn and conn.close()

            self.write(json.dumps(res))
        self.finish()