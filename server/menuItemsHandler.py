import json
import sqlite3
from urllib.parse import unquote
from .baseHandler import BaseHandler
from common.log import logger
from gvar import GVar


class MenuItemsHandler(BaseHandler):
    def get(self):
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            try:
                MenuID = self.get_argument("menuid", default=-1)
                MenuItems = []
                conn = sqlite3.connect(GVar.sysdb, check_same_thread=False)
                if MenuID and int(MenuID) > 0:
                    cursor = conn.execute(
                        "SELECT ID,NAME,ORDERNO,OPENEVENT,CLOSEEVENT,ENABLE,SLEEP, DESC FROM MENUITEM WHERE ID= ? ORDER BY ORDERNO", (MenuID, ))
                    Itemcursor = cursor.fetchone()
                    if Itemcursor:
                        itemjson = {"ID": Itemcursor[0], "NAME": Itemcursor[1], "ORDERNO": Itemcursor[2], "OPENEVENT": Itemcursor[3],  "CLOSEEVENT": Itemcursor[4],
                                    "ENABLE": Itemcursor[5], "SLEEP": Itemcursor[6], "DESC": Itemcursor[7]}
                        MenuItems.append(itemjson)
                else:
                    cursor = conn.execute(
                        "SELECT ID,NAME,ORDERNO,OPENEVENT,CLOSEEVENT,ENABLE,SLEEP, DESC FROM MENUITEM ORDER BY ORDERNO")
                    MenuItemscursor = cursor.fetchall()
                    for item in MenuItemscursor:
                        itemjson = {"ID": item[0], "NAME": item[1], "ORDERNO": item[2], "OPENEVENT": item[3], "CLOSEEVENT": item[4],
                                    "ENABLE": item[5], "SLEEP": item[6], "DESC": item[7]}
                        MenuItems.append(itemjson)
            except Exception as error:
                logger.error(error)
            finally:
                conn and conn.close()

            self.write(json.dumps(MenuItems))
        self.finish()
    # 更新节点

    def post(self):
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            try:
                id = self.get_argument("id")
                name = self.get_argument("name")
                orderno = self.get_argument("orderno")
                sleep = self.get_argument("sleep")
                openevent = self.get_argument("openevent")
                closeevent = self.get_argument("closeevent")
                desc = unquote(self.get_argument("desc"))
                conn = sqlite3.connect(GVar.sysdb, check_same_thread=False)
                cursor = conn.cursor()
                sql = "UPDATE MENUITEM SET NAME=?,ORDERNO=?, SLEEP=?,OPENEVENT=?,CLOSEEVENT=?,DESC=? WHERE ID=? "
                cursor.execute(sql, (name, orderno, sleep,
                               openevent, closeevent, desc, id,))
                conn.commit()
                res = {"code": 0, "itemid": id, "message": "更新节点"}
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
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            try:
                name = self.get_argument("name")
                orderno = self.get_argument("orderno")
                sleep = self.get_argument("sleep")
                openevent = self.get_argument("openevent")
                closeevent = self.get_argument("closeevent")
                desc = unquote(self.get_argument("desc"))
                conn = sqlite3.connect(GVar.sysdb, check_same_thread=False)
                cursor = conn.cursor()
                sql = "INSERT INTO MENUITEM(NAME,ORDERNO,SLEEP,OPENEVENT,CLOSEEVENT,DESC) VALUES(?,?,?,?,?,?) "
                cursor.execute(sql, (name, orderno, sleep,
                               openevent, closeevent, desc,))
                sql = "SELECT LAST_INSERT_ROWID()"
                cursor.execute(sql)
                newmenucursor = cursor.fetchone()
                if newmenucursor:
                    newmenuid = newmenucursor[0]
                    conn.commit()
                    res = {"code": 0, "itemid": newmenuid, "message": "新增节点"}
                else:
                    conn.rollback()
                    res = {"code": 1, "message": "新增节点出错"}
            except Exception as error:
                logger.error(error)
                conn and conn.rollback()
                res = {"code": 1, "message": "新增节点出错"}
            finally:
                conn and conn.close()

            self.write(json.dumps(res))
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
                # 先判断是被引用，则不能删除
                cursor = conn.execute(
                    "SELECT ID FROM BILLITEM WHERE TYPENAME=='MENUITEM' AND TYPEID= ? ", (id, ))
                Itemcursor = cursor.fetchone()
                if Itemcursor:
                    res = {"code": 1, "message": "该节点被演讲方案引用，不能删除！"}
                else:
                    cursor.execute("DELETE FROM MENUITEM WHERE ID=? ", (id,))
                    conn.commit()
                    res = {"code": 0, "message": "删除节点"}
            except Exception as error:
                logger.error(error)
                conn and conn.rollback()
                res = {"code": 1, "message": "删除节点出错"}
            finally:
                conn and conn.close()

            self.write(json.dumps(res))
        self.finish()
