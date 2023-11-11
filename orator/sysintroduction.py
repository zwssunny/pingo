# encoding:utf-8
from common.log import logger
from pagecontrol.pagecontrol import pagecontrol
import sqlite3
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

sysdb = "./db/pingo.db"


class sysIntroduction:
    def __init__(self, conversation,  ctlandtalk: bool = False):
        """演讲功能

        Args:
            conversation (Conversation): 会话对象
            ctlandtalk (bool, optional): 是否控制页面. Defaults to False.
        """
        self.conn = sqlite3.connect(sysdb, check_same_thread=False)
        self.conversation = conversation
        self.pagecontrol = pagecontrol()
        self.is_stop = False
        self.ctlandtalk = ctlandtalk  # 是否控制页面跳转
        self.onPlaybill = None
        self.curBillId = None
        self.playstatus = 0

    def billtalk(self, billID=None):
        """ 演示剧本
            如果传入的方案为空，默认播放系统默认方案
        Args:
            billID (interget, optional): 方案ID. Defaults to None.
        """

        try:
            # 保存原来的tts
            oldtts = self.conversation.tts
            self.is_stop = False

            self.setplaystatusChange(1, "演示方案")
            # 查询系统介绍内容
            if billID:
                cursor = self.conn.execute(
                    "SELECT ID, NAME,VOICE, DESC FROM BILL WHERE ID= ?", (billID,))
            else:
                cursor = self.conn.execute(
                    "SELECT ID, NAME,VOICE, DESC FROM BILL WHERE ISDEFAULT=1")
            billcursor = cursor.fetchone()
            if billcursor:
                billdesc = billcursor[3]
                self.curBillId = billcursor[0]

                voice = billcursor[2]
                if voice:
                    self.conversation.tts = self.conversation.newvoice(voice)
                # 说说开场白
                self.conversation.say(billdesc)
                if self.is_stop: #监测停止标志
                    return
                # 开始演示所有节目
                self.talkAllBillItem(self.curBillId)
            else:
                self.conversation.say("找不到演讲方案")
        except sqlite3.Error as error:
            logger.error(error)
        finally:
            # 恢复原来声音
            self.conversation.tts = oldtts
            self.setplaystatusChange(4, "演示方案")

    def talkAllBillItem(self, billID):
        """ 解说的该剧本所有节点，并逐个解说页面

        Args:
            billID (integer): 剧本ID
        """
        try:
            # 查询菜单记录
            cursor = self.conn.execute(
                "SELECT TYPENAME,TYPEID, ORDERNO, SLEEP, DESC FROM BILLITEM WHERE ENABLE=1 AND BILLID= ? ORDER BY ORDERNO", (billID,))
            itemcursor = cursor.fetchall()
            for row in itemcursor:
                typename = row[0]
                typeid = row[1]
                # 演讲前等待时间
                itemsleep = int(row[3])
                itemdesc = row[4]

                if typename == 'MENUITEM':
                    self.talkmenuitem_byid(typeid, itemsleep, itemdesc)
                elif typename == 'FEATURES':
                    self.talkfeature_byid(typeid, itemsleep, itemdesc)
                elif typename == 'OTHERSYSTEM':
                    self.talkothersystem_byid(typeid, itemsleep, itemdesc)
                elif typename == 'HIGHLIGHT':
                    self.talkhighlight_byid(typeid, itemsleep, itemdesc)
                if self.is_stop:
                    break
            # 结束循环
        except sqlite3.Error as error:
            logger.error(error)

    def systalk(self):
        """
        演示整个系统
        """
        try:
            # 查询系统介绍内容
            cursor = self.conn.execute(
                "SELECT ID, NAME, DESC FROM PROJECT")
            prjcursor = cursor.fetchone()
            if prjcursor:
                self.setplaystatusChange(1, "系统介绍")  # 播放
                prjdesc = prjcursor[2]
                self.conversation.say(prjdesc)
                if self.is_stop: #监测停止标志
                    return
                self.talkallmenu()
            else:
                self.conversation.say("找不到该系统")
        except sqlite3.Error as error:
            logger.error(error)
        finally:
            self.setplaystatusChange(4, "系统介绍")  # 停止

    def talkallmenu(self):
        """
        解说整个系统的所有菜单页面
        """
        try:
            # 查询菜单记录
            self.is_stop = False
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO, OPENEVENT, DESC, CLOSEEVENT,SLEEP FROM MENUITEM ORDER BY ORDERNO")
            menucursor = cursor.fetchall()
            for row in menucursor:
                self.menuitemtalk(row)
                if self.is_stop:
                    break
        except sqlite3.Error as error:
            logger.error(error)
        finally:
            self.setplaystatusChange(4, "所有菜单")  # 播放状态停止

    def talkmenuitem_byname(self, menuname):
        """
        解说某个菜单页面

        Args:
            menuname (Text): 菜单名称
        """
        try:
            # 查询菜单记录
            name_pattern = "%" + menuname
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO, OPENEVENT, DESC, CLOSEEVENT,SLEEP FROM MENUITEM WHERE NAME LIKE ?", (name_pattern,))
            menucursor = cursor.fetchone()
            if menucursor:
                self.menuitemtalk(menucursor)
        except sqlite3.Error as error:
            logger.error(error)
        finally:
            self.setplaystatusChange(4, menuname)  # 播放状态停止

    def menuitemtalk(self, menuitem, itemsleep=None, itemdesc=None):
        """
        解说某个菜单页面

        Args:
            menuitem (Cursor): 菜单项记录
        """
        if menuitem:
            # 发送页面切换指令
            if self.ctlandtalk:
                eventid = menuitem[2]
                self.pagecontrol.sendPageCtl("OPEN_PAGE", eventid)

            if itemsleep is None:
                sleeptimes = int(menuitem[5])
            else:
                sleeptimes = itemsleep
            if sleeptimes > 0:
                time.sleep(sleeptimes)

            # 介绍页面功能
            menuname = menuitem[0]
            if itemdesc is None:
                menudesc = menuitem[3]
            else:
                menudesc = itemdesc

            self.setplaystatusChange(1, menuname)  # 播放
            logger.info("讲解" + menuname)
            self.conversation.say(menuname)
            self.conversation.say(menudesc)
            # 发送页面关闭指令
            # eventid = itemcursor[4]
            # self.pagecontrol.sendPageCtl("CLOSE_PAGE", eventid)

    def talkmenuitem_byid(self, menuid, itemsleep=None, itemdesc=None):
        """
        解说某个菜单页面

        Args:
            menuid (integer): 菜单id
        """
        try:
            # 查询菜单记录
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO, OPENEVENT, DESC, CLOSEEVENT,SLEEP FROM MENUITEM WHERE ID = ?", (menuid,))
            menucursor = cursor.fetchone()
            if menucursor:
                self.menuitemtalk(menucursor, itemsleep, itemdesc)
        except sqlite3.Error as error:
            logger.error(error)

    def talkothersystem_byid(self, othersystemid, itemsleep=None, itemdesc=None):
        """
        解说某个第三方系统

        Args:
            othersystemid (integer): 第三方系统id
        """
        try:
            # 查询菜单记录
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO, OPENEVENT, DESC, CLOSEEVENT,SLEEP FROM OTHERSYSTEM WHERE  ID = ?", (othersystemid,))
            itemcursor = cursor.fetchone()
            if itemcursor:
                self.othersystemitemtalk(itemcursor, itemsleep, itemdesc)
        except sqlite3.Error as error:
            logger.error(error)

    def othersystemitemtalk(self, itemcursor, itemsleep=None, itemdesc=None):
        """介绍第三方系统

        Args:
            itemcursor (Cursor): 第三方系统记录
        """
        if itemcursor:
            # 发送页面切换指令
            if self.ctlandtalk:
                eventid = itemcursor[2]
                self.pagecontrol.sendPageCtl("OPEN_SYSTEM", eventid)

            if itemsleep is None:
                sleeptimes = int(itemcursor[5])
            else:
                sleeptimes = itemsleep
            if sleeptimes > 0:
                time.sleep(sleeptimes)

            # 介绍页面功能
            itemname = itemcursor[0]
            if itemdesc is None:
                oitemdesc = itemcursor[3]
            else:
                oitemdesc = itemdesc
            self.setplaystatusChange(1, itemname)  # 播放
            logger.info("讲解" + itemname)
            self.conversation.say(itemname)
            self.conversation.say(oitemdesc)
            # 发送页面关闭指令
            if self.ctlandtalk:
                eventid = itemcursor[4]
                self.pagecontrol.sendPageCtl("CLOSE_SYSTEM", eventid)

    def talkothersystem_byname(self, othersystemname):
        """
        解说某个第三方系统

        Args:
            othersystemname (text): 第三方系统名称
        """
        try:
            # 查询菜单记录
            name_pattern = "%" + othersystemname
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO, OPENEVENT, DESC, CLOSEEVENT,SLEEP FROM OTHERSYSTEM WHERE NAME LIKE ?", (name_pattern,))
            itemcursor = cursor.fetchone()
            if itemcursor:
                self.othersystemitemtalk(itemcursor)
        except sqlite3.Error as error:
            logger.error(error)
        finally:
            self.setplaystatusChange(4)  # 播放状态停止

    def talkallothersystem(self):
        """
        解说某个第三方系统

        """
        try:
            self.is_stop = False
            # 查询记录
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO, OPENEVENT, DESC, CLOSEEVENT,SLEEP FROM OTHERSYSTEM ORDER BY ORDERNO")
            itemcursors = cursor.fetchall()
            for row in itemcursors:
                self.othersystemitemtalk(row)
                if self.is_stop:
                    break
        except sqlite3.Error as error:
            logger.error(error)
        finally:
            self.setplaystatusChange(4, "所有三方系统")

    def talkhighlight_byid(self, highlightid, itemsleep=None, itemdesc=None):
        """
        解说某个亮点场景

        Args:
            highlightid (integer): 亮点场景id
        """
        try:
            # 查询亮点场景记录
            cursor = self.conn.execute(
                "SELECT	H.NAME,	H.ORDERNO, OPENEVENT, DESC, CLOSEEVENT, M.SLEEP FROM HIGHLIGHT H LEFT JOIN MENUITEM M ON H.MENUITEMID = M.ID WHERE H.ID = ?", (highlightid,))
            highlightcursor = cursor.fetchone()
            if highlightcursor:
                self.highlightitemtalk(highlightcursor, itemsleep, itemdesc)
        except sqlite3.Error as error:
            logger.error(error)

    def highlightitemtalk(self, itemcursor, itemsleep=None, itemdesc=None):
        """解说某亮点场景

        Args:
            itemcursor (Cursor): 亮点场景记录
        """
        if itemcursor:
            # 发送页面切换指令
            if self.ctlandtalk:
                eventid = itemcursor[2]
                self.pagecontrol.sendPageCtl("OPEN_HIGHLIGHT", eventid)

            if itemsleep is None:
                sleeptimes = int(itemcursor[5])
            else:
                sleeptimes = itemsleep
            if sleeptimes > 0:
                time.sleep(sleeptimes)

            # 介绍页面功能
            itemname = itemcursor[0]
            if itemdesc is None:
                hitemdesc = itemcursor[3]
            else:
                hitemdesc = itemdesc

            self.setplaystatusChange(1, itemname)  # 播放
            logger.info("讲解" + itemname)
            self.conversation.say(itemname)
            self.conversation.say(hitemdesc)
            # 发送页面关闭指令
            # if self.ctlandtalk:
            # eventid = itemcursor[4]
            # self.pagecontrol.sendPageCtl("CLOSE_HIGHLIGHT", eventid)

    def talkhighlight_byname(self, highlightname):
        """
        解说某个亮点场景

        Args:
            highlightid (text): 亮点场景名称
        """
        try:
            # 查询亮点场景记录
            name_pattern = "%" + highlightname
            cursor = self.conn.execute(
                "SELECT	H.NAME,	H.ORDERNO, OPENEVENT, DESC, CLOSEEVENT, M.SLEEP FROM HIGHLIGHT H LEFT JOIN MENUITEM M ON H.MENUITEMID = M.ID WHERE H.NAME LIKE ?", (name_pattern,))
            highlightcursor = cursor.fetchone()
            if highlightcursor:
                self.highlightitemtalk(highlightcursor)
        except sqlite3.Error as error:
            logger.error(error)
        finally:
            self.setplaystatusChange(4, highlightname)  # 播放状态停止

    def talkallhighlight(self):
        """
        解说所有亮点场景

        """
        try:
            self.is_stop = False
            # 查询亮点场景记录
            cursor = self.conn.execute(
                "SELECT	H.NAME,	H.ORDERNO, OPENEVENT, DESC, CLOSEEVENT, M.SLEEP FROM HIGHLIGHT H LEFT JOIN MENUITEM M ON H.MENUITEMID = M.ID ORDER BY H.ORDERNO")
            highlightcursors = cursor.fetchall()
            for row in highlightcursors:
                self.highlightitemtalk(row)
                if self.is_stop:
                    break
        except sqlite3.Error as error:
            logger.error(error)
        finally:
            self.setplaystatusChange(4, "所有亮点场景")  # 停止

    def talkfeature_byid(self, featureid, itemsleep=None, itemdesc=None):
        """
        解说系统特点

        Args:
            featureid (integer): 系统特点id
        """
        try:
            # 查询菜单记录

            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO,  DESC,SLEEP FROM FEATURES WHERE ID = ?", (featureid,))
            itemcursor = cursor.fetchone()
            if itemcursor:
                self.featureitemtalk(itemcursor, itemsleep, itemdesc)
        except sqlite3.Error as error:
            logger.error(error)

    def featureitemtalk(self, itemcursor, itemsleep=None, itemdesc=None):
        if itemcursor:
            # 介绍页面功能
            if itemsleep is None:
                sleeptimes = int(itemcursor[3])
            else:
                sleeptimes = itemsleep
            if sleeptimes > 0:
                time.sleep(sleeptimes)

            itemname = itemcursor[0]
            if itemdesc is None:
                fitemdesc = itemcursor[2]
            else:
                fitemdesc = itemdesc

            self.setplaystatusChange(1, itemname)  # 播放

            logger.info("讲解" + itemname)
            self.conversation.say(itemname)
            self.conversation.say(fitemdesc)

    def talkfeature_byname(self, featurename):
        """解说系统特点

        Args:
            featurename (Text): 系统特点名称
        """
        try:
            # 查询菜单记录
            name_pattern = "%" + featurename
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO,  DESC, SLEEP FROM FEATURES WHERE NAME LIKE ?", (name_pattern,))
            itemcursor = cursor.fetchone()
            if itemcursor:
                self.featureitemtalk(itemcursor)
        except sqlite3.Error as error:
            logger.error(error)
        finally:
            self.setplaystatusChange(4, featurename)  # 播放状态停止

    def talkallfeature(self):
        """解说所有系统特点

        """
        try:
            self.is_stop = False
            # 查询记录
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO,  DESC, SLEEP FROM FEATURES ORDER BY ORDERNO")
            itemcursors = cursor.fetchall()
            for row in itemcursors:
                self.featureitemtalk(row)
                if self.is_stop:
                    break
        except sqlite3.Error as error:
            logger.error(error)
        finally:
            self.setplaystatusChange(4, "所有特点")  # 播放状态停止

    def loadpageindex(self) -> dict:
        """
        返回系统的所有菜单页面对应的contrlindex
        """
        try:
            results = {}
            # 查询菜单记录
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO, OPENEVENT, CLOSEEVENT FROM MENUITEM ORDER BY ORDERNO")
            menucursor = cursor.fetchall()
            for row in menucursor:
                results[row[0]] = row[2]

            return results
        except sqlite3.Error as error:
            logger.error(error)

    def loadhighlightindex(self) -> dict:
        """
        返回系统的所有亮点页面对应的contrlindex
        """
        try:
            results = {}
            # 查询菜单记录
            cursor = self.conn.execute(
                "SELECT	H.NAME,	H.ORDERNO, OPENEVENT, CLOSEEVENT FROM HIGHLIGHT H LEFT JOIN MENUITEM M ON H.MENUITEMID = M.ID ORDER BY H.ORDERNO")
            menucursor = cursor.fetchall()
            for row in menucursor:
                results[row[0]] = row[2]

            return results
        except sqlite3.Error as error:
            logger.error(error)

    def loadothersystemindex(self) -> dict:
        """
        返回系统的所有第三方系统对应的contrlindex
        """
        try:
            results = {}
            # 查询菜单记录
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO, OPENEVENT, CLOSEEVENT FROM OTHERSYSTEM ORDER BY ORDERNO")
            menucursor = cursor.fetchall()
            for row in menucursor:
                results[row[0]] = row[2]

            return results
        except sqlite3.Error as error:
            logger.error(error)

    def stop(self):
        self.is_stop = True
        self.setplaystatusChange(4)

    def setplaystatusChange(self, playstatus, msg=''):
        self.playstatus = playstatus
        if self.onPlaybill:
            self.onPlaybill(self.playstatus, msg)


if __name__ == '__main__':
    from config import load_config
    from robot.conversation import Conversation
    load_config()
    conversation = Conversation()
    sysIntro = sysIntroduction(conversation=conversation)
    # sysIntro.talkhighlight_byname("地铁运营监测")
    # sysIntro.talkhighlight_byid(1)
    # sysIntro.billtalk()  # 默认演讲方案
    sysIntro.talkAllBillItem(1) #编号为1的演讲方案
    # sysIntro.talkallhighlight() #所有亮点场景
    # sysIntro.talkallfeature() #所有平台特点
    # sysIntro.talkallothersystem() #所有第三方系统
    # sysIntro.talkallmenu() #所有大屏页面
    # sysIntro.talkmenuitem_byname("地铁") 
    # sysIntro.talkothersystem_byname("智慧交通")
    # sysIntro.talkhighlight_byname("非现场执法")
