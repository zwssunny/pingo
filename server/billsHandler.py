import json
from urllib.parse import unquote
from .baseHandler import BaseHandler
import sqlite3
from common.log import logger
from gvar import GVar

class BillsHandler(BaseHandler):
    def get(self):
        if not self.isValidated():
            self.redirect("/login")
        else:
            try:
                billid = self.get_argument("billid", default=None)
                bills = []
                conn = sqlite3.connect(GVar.sysdb, check_same_thread=False)
                if billid is None:
                    cursor = conn.execute(
                        "SELECT ID, NAME,ISDEFAULT, DATETIME,DESC FROM BILL")
                else:
                    cursor = conn.execute(
                        "SELECT ID, NAME,ISDEFAULT,  DATETIME,DESC FROM BILL WHERE ID= ?", (billid,))
                billscursor = cursor.fetchall()
                for bill in billscursor:
                    billjson = {"ID": bill[0],
                                "NAME": bill[1], "ISDEFAULT": bill[2],  "DATETIME": bill[3], "DESC": bill[4]}
                    bills.append(billjson)
                self.write(json.dumps(bills))
            except Exception as error:
                logger.error(error)
            finally:
                conn and conn.close()
        self.finish()
    # 更新演讲方案

    def post(self):
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            try:
                id = self.get_argument("id")
                name = self.get_argument("name")
                isdefault = self.get_argument("isdefault")
                datetime = self.get_argument("datetime")
                desc = unquote(self.get_argument("desc"))
                conn = sqlite3.connect(GVar.sysdb, check_same_thread=False)
                cursor = conn.cursor()
                # 系统只能有一条记录是默认方案
                if int(isdefault) == 1:
                    sql = "UPDATE BILL SET isdefault=0 WHERE isdefault=1 and ID<>? "
                    cursor.execute(sql, (id,))
                sql = "UPDATE BILL SET  name=?,isdefault=?,datetime=?, DESC=? WHERE ID=? "
                cursor.execute(
                    sql, (name,  isdefault, datetime, desc, id,))
                conn.commit()
                res = {"code": 0, "message": "更新演讲方案"}
            except Exception as error:
                logger.error(error)
                conn and conn.rollback()
                res = {"code": 1, "message": "更新演讲方案出错"}
            finally:
                conn and conn.close()

            self.write(json.dumps(res))
        self.finish()
    # 克隆演讲方案

    def put(self):
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            try:
                id = self.get_argument("id")
                conn = sqlite3.connect(GVar.sysdb, check_same_thread=False)
                cursor = conn.cursor()
                sql = "INSERT INTO BILL(NAME,DATETIME,ISDEFAULT,DESC) SELECT  NAME||'-克隆',datetime(CURRENT_TIMESTAMP,'localtime'),0,DESC FROM BILL WHERE ID=? "
                cursor.execute(sql, (id,))
                sql = "SELECT LAST_INSERT_ROWID()"
                cursor.execute(sql)
                newbillcursor = cursor.fetchone()
                if newbillcursor:
                    newbillid = newbillcursor[0]
                    if int(newbillid) > 0:
                        sql = "INSERT INTO BILLITEM(BILLID,TYPENAME,TYPEID,ORDERNO,ENABLE,SLEEP,DESC) SELECT ?,TYPENAME,TYPEID,ORDERNO,ENABLE,SLEEP,DESC from BILLITEM WHERE BILLID=? "
                        cursor.execute(sql, (newbillid, id,))
                        conn.commit()
                        res = {"code": 0, "newbillid": newbillid,
                               "message": "克隆演讲方案"}
                else:
                    conn.rollback()
                    res = {"code": 1,  "message": "创建新演讲方案出错"}
            except Exception as error:
                logger.error(error)
                conn and conn.rollback()
                res = {"code": 1,  "message": "创建新演讲方案出错"}
            finally:
                conn and conn.close()

            self.write(json.dumps(res))
        self.finish()

    # 新建演讲方案
    def patch(self):
        if not self.validate(self.get_argument("validate", default=None)):
            res = {"code": 1, "message": "illegal visit"}
            self.write(json.dumps(res))
        else:
            try:
                conn = sqlite3.connect(GVar.sysdb, check_same_thread=False)
                cursor = conn.cursor()
                sql = "INSERT INTO BILL(NAME,DATETIME,ISDEFAULT,DESC) VALUES('新建演讲方案',datetime(CURRENT_TIMESTAMP,'localtime'),0,'请输入开场白')"
                cursor.execute(sql)
                sql = "SELECT LAST_INSERT_ROWID()"
                cursor.execute(sql)
                newbillcursor = cursor.fetchone()
                if newbillcursor:
                    newbillid = newbillcursor[0]
                    if int(newbillid) > 0:
                        sql = "INSERT INTO BILLITEM(BILLID,TYPENAME,TYPEID,ORDERNO,ENABLE,SLEEP,DESC) SELECT ?,'MENUITEM',ID,ORDERNO,ENABLE,SLEEP,DESC from MENUITEM"
                        cursor.execute(sql, (newbillid, ))
                        sql = "INSERT INTO BILLITEM(BILLID,TYPENAME,TYPEID,ORDERNO,ENABLE,SLEEP,DESC) SELECT ?,'OTHERSYSTEM',ID,ORDERNO,ENABLE,SLEEP,DESC from OTHERSYSTEM"
                        cursor.execute(sql, (newbillid, ))
                        sql = "INSERT INTO BILLITEM(BILLID,TYPENAME,TYPEID,ORDERNO,ENABLE,SLEEP,DESC) SELECT ?,'FEATURES',ID,ORDERNO,ENABLE,SLEEP,DESC from FEATURES"
                        cursor.execute(sql, (newbillid, ))
                        conn.commit()
                        res = {"code": 0, "newbillid": newbillid,
                               "message": "新建演讲方案"}
                    else:
                        conn.rollback()
                        res = {"code": 1,  "message": "新建演讲方案出错"}
                else:
                    conn.rollback()
                    res = {"code": 1,  "message": "找不到原演讲方案"}
            except Exception as error:
                logger.error(error)
                conn and conn.rollback()
                res = {"code": 1,  "message": "新建演讲方案出错"}
            finally:
                conn and conn.close()

            self.write(json.dumps(res))
        self.finish()
