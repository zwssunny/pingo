# encoding:utf-8
import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pagecontrol.pagecontrol import pagecontrol
from common.log import logger
from voice.voice import Voice

sysdb = "./db/pingo.db"


class sysIntroduction:
    def __init__(self, tts: Voice, pgectl: pagecontrol=None, canpause: bool = False):
        """
        系统介绍

        Args:
            tts (Voice): 语音实例。
            askcontinu (bool, optional): 是否要人为控制. Defaults to False.
        """
        self.conn = sqlite3.connect(sysdb)
        self.tts = tts
        self.canpause = canpause
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
            cursor = self.conn.execute(
                "SELECT ID, NAME,VOICE, DESC FROM BILL WHERE ISDEFAULT=1")
            billcursor = cursor.fetchone()
            if billcursor:
                billdesc = billcursor[3]
                billid = billcursor[0]
                self.tts.text_to_speech_and_play(billdesc)
                self.talkAllBillItem(billid)
            else:
                self.tts.text_to_speech_and_play("找不到剧本")
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
                # if self.askcontinu:
                #     willcontinue = input("继续演示吗？")
                #     if willcontinue == "n":
                #         return

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
                self.tts.text_to_speech_and_play(prjdesc)
                self.talkallmenu()
            else:
                self.tts.text_to_speech_and_play("找不到该系统")
        except sqlite3.Error as error:
            logger.error(error)

    def talkallmenu(self):
        """
        解说整个系统的所有菜单页面
        """
        try:
            # 查询菜单记录
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO, PAGEINDEX, DESC FROM MENUITEM ORDER BY ORDERNO")
            menucursor = cursor.fetchall()
            for row in menucursor:
                # if self.canpause:
                #     menuname = row[0]
                #     willcontinue = input("继续演示[" + menuname + "]吗？")
                #     if willcontinue == "n":
                #         return
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
                "SELECT NAME, ORDERNO, PAGEINDEX, DESC FROM MENUITEM WHERE NAME LIKE ?", (name_pattern,))
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
            pageindex = menuitem[2]
            self.pagecontrol.sendPageCtl("OPEN_PAGE", pageindex)
            # 介绍页面功能
            menuname = menuitem[0]
            menudesc = menuitem[3]
            logger.info("讲解" + menuname)
            self.tts.text_to_speech_and_play(menuname)
            self.tts.text_to_speech_and_play(menudesc, self.canpause)

    def talkmenuitem_byid(self, menuid):
        """
        解说某个菜单页面

        Args:
            menuid (integer): 菜单id
        """
        try:
            # 查询菜单记录
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO, PAGEINDEX, DESC FROM MENUITEM WHERE ID = ?", (menuid,))
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
                "SELECT NAME, ORDERNO, PAGEINDEX, DESC FROM OTHERSYSTEM WHERE  ID = ?", (othersystemid,))
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
            pageindex = itemcursor[2]
            self.pagecontrol.sendPageCtl("OPEN_SYSTEM", pageindex)
            # 介绍页面功能
            itemname = itemcursor[0]
            itemdesc = itemcursor[3]
            logger.info("讲解" + itemname)
            self.tts.text_to_speech_and_play(itemname)
            self.tts.text_to_speech_and_play(itemdesc, self.canpause)

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
                "SELECT NAME, ORDERNO, PAGEINDEX, DESC FROM OTHERSYSTEM WHERE NAME LIKE ?", (name_pattern,))
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
            # 查询记录
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO, PAGEINDEX, DESC FROM OTHERSYSTEM ORDER BY ORDERNO")
            itemcursors = cursor.fetchall()
            for row in itemcursors:
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
                "SELECT NAME, ORDERNO, PAGEINDEX, DESC FROM HIGHLIGHT WHERE ID = ?", (highlightid,))
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
            pageindex = itemcursor[2]
            self.pagecontrol.sendPageCtl("OPEN_HIGHLIGHT", pageindex)
            # 介绍页面功能
            itemname = itemcursor[0]
            itemdesc = itemcursor[3]
            logger.info("讲解" + itemname)
            self.tts.text_to_speech_and_play(itemname)
            self.tts.text_to_speech_and_play(itemdesc, self.canpause)

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
                "SELECT NAME, ORDERNO, PAGEINDEX, DESC FROM HIGHLIGHT WHERE NAME LIKE ?", (name_pattern,))
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
            # 查询亮点场景记录
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO, PAGEINDEX, DESC FROM HIGHLIGHT ORDER BY ORDERNO")
            highlightcursors = cursor.fetchall()
            for row in highlightcursors:
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
            self.tts.text_to_speech_and_play(itemname)
            self.tts.text_to_speech_and_play(itemdesc, self.canpause)

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
            # 查询记录
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO,  DESC FROM FEATURES ORDER BY ORDERNO")
            itemcursors = cursor.fetchall()
            for row in itemcursors:
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
                "SELECT NAME, ORDERNO, PAGEINDEX FROM MENUITEM ORDER BY ORDERNO")
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
                "SELECT NAME, ORDERNO, PAGEINDEX FROM HIGHLIGHT ORDER BY ORDERNO")
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
                "SELECT NAME, ORDERNO, PAGEINDEX FROM OTHERSYSTEM ORDER BY ORDERNO")
            menucursor = cursor.fetchall()
            for row in menucursor:
                results[row[0]]=row[2]

            return results
        except sqlite3.Error as error:
            logger.error(error)     

if __name__ == '__main__':
    from voice.edge.EdgeVoice import EdgeVoice
    from config import conf, load_config
    load_config()
    tts = EdgeVoice(voice=conf().get("voice","zh-CN-YunjianNeural"))
    sysIntro = sysIntroduction(tts=tts,canpause=False)
    sysIntro.billtalk()  # 剧本
    # sysIntro.talkallhighlight()
    # sysIntro.talkallfeature()
    # sysIntro.talkallothersystem()
    # sysIntro.talkallmenu() #所有大屏页面
    # sysIntro.talkmenuitem_byname("地铁")
    # sysIntro.talkothersystem_byname("智慧交通")
    # sysIntro.talkhighlight_byname("非现场执法")
