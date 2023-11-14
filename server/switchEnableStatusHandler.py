
import json
from urllib.parse import unquote
from .baseHandler import BaseHandler
import sqlite3
from common.log import logger
from gvar import GVar

class SwitchEnableStatusHandler(BaseHandler):
    # 更新节点
    def post(self):
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            try:
                id = self.get_argument("id")
                enable = self.get_argument("enable")
                conn = sqlite3.connect(GVar.sysdb, check_same_thread=False)
                cursor = conn.cursor()
                sql = "UPDATE BILLITEM SET ENABLE=? WHERE ID=? "
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