# encoding:utf-8
import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pagecontrol.pagecontrol import pagecontrol
from common.log import logger

sysdb = "./db/pingo.db"


class sysIntroduction:
    def __init__(self, conversation, pgectl: pagecontrol=None, ctlandtalk: bool=False):
        """
        系统介绍

        Args:
            tts (Voice): 语音实例。
            canpause (bool, optional): 是否可暂停. Defaults to False.
        """
        self.conn = sqlite3.connect(sysdb, check_same_thread=False)
        self.conversation = conversation
        self.is_stop=False
        self.ctlandtalk=ctlandtalk #是否控制页面跳转

        if pgectl:
            self.pagecontrol = pgectl  
        else:  
            self.pagecontrol = pagecontrol()

    def billtalk(self):
        """
        演示默认剧本
        """
        try:
            # 查询系统介绍内容
            self.is_stop=False
            cursor = self.conn.execute(
                "SELECT ID, NAME,VOICE, DESC FROM BILL WHERE ISDEFAULT=1")
            billcursor = cursor.fetchone()
            if billcursor:
                billdesc = billcursor[3]
                billid = billcursor[0]
                self.conversation.say(billdesc)
                self.talkAllBillItem(billid)
            else:
                self.conversation.say("找不到剧本")
        except sqlite3.Error as error:
            logger.error(error)

    def talkAllBillItem(self, billID):
        """ 解说的该剧本所有节点，并逐个解说页面

        Args:
            billID (integer): 剧本ID
        """        
        try:
            # 查询菜单记录
            cursor = self.conn.execute(
                "SELECT TYPENAME,TYPEID, ORDERNO FROM BILLITEM WHERE ENABLE=1 AND BILLID= ? ORDER BY ORDERNO", (billID,))
            itemcursor = cursor.fetchall()
            for row in itemcursor:
                if self.is_stop:
                    break
                typename = row[0]
                typeid = row[1]
                if typename == 'MENUITEM':
                    self.talkmenuitem_byid(typeid)
                elif typename == 'FEATURES':
                    self.talkfeature_byid(typeid)
                elif typename == 'OTHERSYSTEM':
                    self.talkothersystem_byid(typeid)
                elif typename == 'HIGHLIGHT':
                    self.talkhighlight_byid(typeid)
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
                prjdesc = prjcursor[2]
                self.conversation.say(prjdesc)
                self.talkallmenu()
            else:
                self.conversation.say("找不到该系统")
        except sqlite3.Error as error:
            logger.error(error)

    def talkallmenu(self):
        """
        解说整个系统的所有菜单页面
        """
        try:
            # 查询菜单记录
            self.is_stop=False
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO, OPENEVENT, DESC, CLOSEEVENT FROM MENUITEM ORDER BY ORDERNO")
            menucursor = cursor.fetchall()
            for row in menucursor:
                if self.is_stop:
                    break
                self.menuitemtalk(row)
        except sqlite3.Error as error:
            logger.error(error)

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
                "SELECT NAME, ORDERNO, OPENEVENT, DESC, CLOSEEVENT FROM MENUITEM WHERE NAME LIKE ?", (name_pattern,))
            menucursor = cursor.fetchone()
            if menucursor:
                self.menuitemtalk(menucursor)
        except sqlite3.Error as error:
            logger.error(error)

    def menuitemtalk(self, menuitem):
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
            # 介绍页面功能
            menuname = menuitem[0]
            menudesc = menuitem[3]
            logger.info("讲解" + menuname)
            self.conversation.say(menuname)
            self.conversation.say(menudesc)
             # 发送页面关闭指令
            # eventid = itemcursor[4]
            # self.pagecontrol.sendPageCtl("CLOSE_PAGE", eventid)             

    def talkmenuitem_byid(self, menuid):
        """
        解说某个菜单页面

        Args:
            menuid (integer): 菜单id
        """
        try:
            # 查询菜单记录
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO, OPENEVENT, DESC, CLOSEEVENT FROM MENUITEM WHERE ID = ?", (menuid,))
            menucursor = cursor.fetchone()
            if menucursor:
                self.menuitemtalk(menucursor)
        except sqlite3.Error as error:
            logger.error(error)

    def talkothersystem_byid(self, othersystemid):
        """
        解说某个第三方系统

        Args:
            othersystemid (integer): 第三方系统id
        """
        try:
            # 查询菜单记录
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO, OPENEVENT, DESC, CLOSEEVENT FROM OTHERSYSTEM WHERE  ID = ?", (othersystemid,))
            itemcursor = cursor.fetchone()
            if itemcursor:
                self.othersystemitemtalk(itemcursor)
        except sqlite3.Error as error:
            logger.error(error)

    def othersystemitemtalk(self, itemcursor):
        """介绍第三方系统

        Args:
            itemcursor (Cursor): 第三方系统记录
        """
        if itemcursor:
            # 发送页面切换指令
            if self.ctlandtalk:
                eventid = itemcursor[2]
                self.pagecontrol.sendPageCtl("OPEN_SYSTEM", eventid)
            # 介绍页面功能
            itemname = itemcursor[0]
            itemdesc = itemcursor[3]
            logger.info("讲解" + itemname)
            self.conversation.say(itemname)
            self.conversation.say(itemdesc)
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
                "SELECT NAME, ORDERNO, OPENEVENT, DESC, CLOSEEVENT FROM OTHERSYSTEM WHERE NAME LIKE ?", (name_pattern,))
            itemcursor = cursor.fetchone()
            if itemcursor:
                self.othersystemitemtalk(itemcursor)
        except sqlite3.Error as error:
            logger.error(error)

    def talkallothersystem(self):
        """
        解说某个第三方系统

        """
        try:
            self.is_stop=False
            # 查询记录
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO, OPENEVENT, DESC, CLOSEEVENT FROM OTHERSYSTEM ORDER BY ORDERNO")
            itemcursors = cursor.fetchall()
            for row in itemcursors:
                if self.is_stop:
                    break
                self.othersystemitemtalk(row)
        except sqlite3.Error as error:
            logger.error(error)

    def talkhighlight_byid(self, highlightid):
        """
        解说某个亮点场景

        Args:
            highlightid (integer): 亮点场景id
        """
        try:
            # 查询亮点场景记录
            cursor = self.conn.execute(
                "SELECT	H.NAME,	H.ORDERNO, OPENEVENT, DESC, CLOSEEVENT FROM HIGHLIGHT H LEFT JOIN MENUITEM M ON H.MENUITEMID = M.ID WHERE H.ID = ?", (highlightid,))
            highlightcursor = cursor.fetchone()
            if highlightcursor:
                self.highlightitemtalk(highlightcursor)
        except sqlite3.Error as error:
            logger.error(error)

    def highlightitemtalk(self, itemcursor):
        """解说某亮点场景

        Args:
            itemcursor (Cursor): 亮点场景记录
        """
        if itemcursor:
            # 发送页面切换指令
            if self.ctlandtalk:  
                eventid = itemcursor[2]
                self.pagecontrol.sendPageCtl("OPEN_HIGHLIGHT", eventid)
            # 介绍页面功能
            itemname = itemcursor[0]
            itemdesc = itemcursor[3]
            logger.info("讲解" + itemname)
            self.conversation.say(itemname)
            self.conversation.say(itemdesc)
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
                "SELECT	H.NAME,	H.ORDERNO, OPENEVENT, DESC, CLOSEEVENT FROM HIGHLIGHT H LEFT JOIN MENUITEM M ON H.MENUITEMID = M.ID WHERE H.NAME LIKE ?", (name_pattern,))
            highlightcursor = cursor.fetchone()
            if highlightcursor:
                self.highlightitemtalk(highlightcursor)
        except sqlite3.Error as error:
            logger.error(error)

    def talkallhighlight(self):
        """
        解说所有亮点场景

        """
        try:
            self.is_stop=False
            # 查询亮点场景记录
            cursor = self.conn.execute(
                "SELECT	H.NAME,	H.ORDERNO, OPENEVENT, DESC, CLOSEEVENT FROM HIGHLIGHT H LEFT JOIN MENUITEM M ON H.MENUITEMID = M.ID ORDER BY H.ORDERNO")
            highlightcursors = cursor.fetchall()
            for row in highlightcursors:
                if self.is_stop:
                    break
                self.highlightitemtalk(row)
        except sqlite3.Error as error:
            logger.error(error)

    def talkfeature_byid(self, featureid):
        """
        解说系统特点

        Args:
            featureid (integer): 系统特点id
        """
        try:
            # 查询菜单记录

            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO,  DESC FROM FEATURES WHERE ID = ?", (featureid,))
            itemcursor = cursor.fetchone()
            if itemcursor:
                self.featureitemtalk(itemcursor)
        except sqlite3.Error as error:
            logger.error(error)

    def featureitemtalk(self, itemcursor):
        if itemcursor:
            # 介绍页面功能
            itemname = itemcursor[0]
            itemdesc = itemcursor[2]
            logger.info("讲解" + itemname)
            self.conversation.say(itemname)
            self.conversation.say(itemdesc)

    def talkfeature_byname(self, featurename):
        """解说系统特点

        Args:
            featurename (Text): 系统特点名称
        """
        try:
            # 查询菜单记录
            name_pattern = "%" + featurename
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO,  DESC FROM FEATURES WHERE NAME LIKE ?", (name_pattern,))
            itemcursor = cursor.fetchone()
            if itemcursor:
                self.featureitemtalk(itemcursor)
        except sqlite3.Error as error:
            logger.error(error)
   
    def talkallfeature(self):
        """解说所有系统特点

        """
        try:
            self.is_stop=False
            # 查询记录
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO,  DESC FROM FEATURES ORDER BY ORDERNO")
            itemcursors = cursor.fetchall()
            for row in itemcursors:
                if self.is_stop:
                    break
                self.featureitemtalk(row)
        except sqlite3.Error as error:
            logger.error(error)

    def loadpageindex(self)-> dict:
        """
        返回系统的所有菜单页面对应的contrlindex
        """
        try:
            results={}
            # 查询菜单记录
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO, OPENEVENT, CLOSEEVENT FROM MENUITEM ORDER BY ORDERNO")
            menucursor = cursor.fetchall()
            for row in menucursor:
                results[row[0]]=row[2]

            return results
        except sqlite3.Error as error:
            logger.error(error)     

    def loadhighlightindex(self)-> dict:
        """
        返回系统的所有亮点页面对应的contrlindex
        """
        try:
            results={}
            # 查询菜单记录
            cursor = self.conn.execute(
                "SELECT	H.NAME,	H.ORDERNO, OPENEVENT, CLOSEEVENT FROM HIGHLIGHT H LEFT JOIN MENUITEM M ON H.MENUITEMID = M.ID ORDER BY H.ORDERNO")
            menucursor = cursor.fetchall()
            for row in menucursor:
                results[row[0]]=row[2]

            return results
        except sqlite3.Error as error:
            logger.error(error)     

    def loadothersystemindex(self)-> dict:
        """
        返回系统的所有第三方系统对应的contrlindex
        """
        try:
            results={}
            # 查询菜单记录
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO, OPENEVENT, CLOSEEVENT FROM OTHERSYSTEM ORDER BY ORDERNO")
            menucursor = cursor.fetchall()
            for row in menucursor:
                results[row[0]]=row[2]

            return results
        except sqlite3.Error as error:
            logger.error(error)    

    def stop(self):
         self.is_stop=True

if __name__ == '__main__':
    from config import load_config
    from robot.conversation import Conversation
    load_config()
    conversation=Conversation()
    sysIntro = sysIntroduction(conversation=conversation)
    # sysIntro.talkhighlight_byname("地铁运营监测")
    # sysIntro.talkhighlight_byid(1)
    # sysIntro.billtalk()  # 剧本
    sysIntro.talkallhighlight()
    # sysIntro.talkallfeature()
    # sysIntro.talkallothersystem()
    # sysIntro.talkallmenu() #所有大屏页面
    # sysIntro.talkmenuitem_byname("地铁")
    # sysIntro.talkothersystem_byname("智慧交通")
    # sysIntro.talkhighlight_byname("非现场执法")
