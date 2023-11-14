import json
import sqlite3
from urllib.parse import unquote
from .baseHandler import BaseHandler
from common.log import logger
from gvar import GVar

class BillItemsHandler(BaseHandler):
    def get(self):
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            try:
                billID = self.get_argument("billid")
                itemID = self.get_argument("itemid", default=None)
                billItems = []
                conn = sqlite3.connect(GVar.sysdb, check_same_thread=False)
                if billID and itemID:
                    cursor = conn.execute("SELECT *, (CASE WHEN TYPENAME=='MENUITEM' THEN (SELECT NAME FROM MENUITEM WHERE ID=TYPEID)"
                                          " WHEN TYPENAME=='OTHERSYSTEM' THEN (SELECT NAME FROM OTHERSYSTEM WHERE ID=TYPEID)"
                                          " ELSE (SELECT NAME FROM FEATURES WHERE ID=TYPEID) END ) AS NAME FROM BILLITEM WHERE BILLID= ? AND ID= ? ORDER BY ORDERNO", (billID, itemID,))
                    Itemcursor = cursor.fetchone()
                    if Itemcursor:
                        itemjson = {"ID": Itemcursor[0], "BILLID": Itemcursor[1], "TYPENAME": Itemcursor[2], "TYPEID": Itemcursor[3],
                                    "ORDERNO": Itemcursor[4], "ENABLE": Itemcursor[5], "DESC": Itemcursor[6], "NAME": Itemcursor[8], "SLEEP": Itemcursor[7]}
                        billItems.append(itemjson)
                else:
                    cursor = conn.execute("SELECT *, (CASE WHEN TYPENAME=='MENUITEM' THEN (SELECT NAME FROM MENUITEM WHERE ID=TYPEID)"
                                          " WHEN TYPENAME=='OTHERSYSTEM' THEN (SELECT NAME FROM OTHERSYSTEM WHERE ID=TYPEID)"
                                          " ELSE (SELECT NAME FROM FEATURES WHERE ID=TYPEID) END ) AS NAME FROM BILLITEM WHERE BILLID= ? ORDER BY ORDERNO", (billID,))
                    billItemscursor = cursor.fetchall()
                    for item in billItemscursor:
                        itemjson = {"ID": item[0], "BILLID": item[1], "TYPENAME": item[2], "TYPEID": item[3],
                                    "ORDERNO": item[4], "ENABLE": item[5], "DESC": item[6], "NAME": item[8], "SLEEP": item[7]}
                        billItems.append(itemjson)
            except Exception as error:
                logger.error(error)
            finally:
                conn and conn.close()

            self.write(json.dumps(billItems))
        self.finish()
    # 更新节点

    def post(self):
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            try:
                id = self.get_argument("id")
                orderno = self.get_argument("orderno")
                sleep = self.get_argument("sleep")
                desc = unquote(self.get_argument("desc"))
                conn = sqlite3.connect(GVar.sysdb, check_same_thread=False)
                cursor = conn.cursor()
                sql = "UPDATE BILLITEM SET ORDERNO=?, SLEEP=?,DESC=? WHERE ID=? "
                cursor.execute(sql, (orderno, sleep, desc, id,))
                conn.commit()
                res = {"code": 0, "message": "更新节点"}
            except Exception as error:
                logger.error(error)
                conn and conn.rollback()
                res = {"code": 1, "message": "更新节点错误"}
            finally:
                conn and conn.close()

            self.write(json.dumps(res))
        self.finish()
    # 新增节点

    def put(self):
        # pass
        self.finish()
    # 删除节点

    def delete(self):
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            try:
                id = self.get_argument("id")
                conn = sqlite3.connect(GVar.sysdb, check_same_thread=False)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM BILLITEM WHERE ID=? ", (id,))
                conn.commit()
                # logger.log(desc)
                res = {"code": 0, "message": "删除节点"}
            except Exception as error:
                logger.error(error)
                conn and conn.rollback()
                res = {"code": 1, "message": "删除节点出错"}
            finally:
                conn and conn.close()

            self.write(json.dumps(res))
        self.finish()
