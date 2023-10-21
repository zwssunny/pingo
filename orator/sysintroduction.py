# encoding:utf-8
import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from voice.voice import Voice
from common.log import logger
from pagecontrol.pagecontrol import pagecontrol


sysdb = "./db/pingo.db"


class sysIntroduction:
    def __init__(self, tts: Voice, askcontinu: bool = False):
        """
        系统介绍

        Args:
            tts (Voice): 语音实例。
            askcontinu (bool, optional): 是否要人为控制. Defaults to False.
        """
        self.conn = sqlite3.connect(sysdb)
        self.tts = tts
        self.askcontinu = askcontinu
        self.pagecontrol = pagecontrol()

    def billtalk(self):
        """
        演示整个系统
        """
        try:
            # 查询系统介绍内容
            cursor = self.conn.execute(
                "SELECT ID, NAME,VOICE, DESC FROM BILL WHERE ISDEFAULT=1")
            billcursor = cursor.fetchone()
            if billcursor:
                billdesc = billcursor[3]
                billid=billcursor[0]
                self.tts.text_to_speech_and_play(billdesc)
                self.talkAllBillItem(billid)
            else:
                self.tts.text_to_speech_and_play("找不到剧本")
        except sqlite3.Error as error:
            logger.error(error)

    def talkAllBillItem(self,billID):
        """
        解说的该剧本所有内容
        """
        try:
            # 查询菜单记录
            cursor = self.conn.execute(
                "SELECT TYPENAME,TYPEID, ORDERNO FROM BILLITEM WHERE ENABLE=1 AND BILLID= ? ORDER BY ORDERNO",(billID,))
            itemcursor = cursor.fetchall()
            for row in itemcursor:
                # if self.askcontinu:
                #     willcontinue = input("继续演示吗？")
                #     if willcontinue == "n":
                #         return
                    
                typename=row[0]
                typeid=row[1]
                if typename=='MENUITEM':
                    self.talkitem_byid(typeid)
                elif typename=='FEATURES':
                    self.talkfeature_byid(typeid)
                elif typename=='OTHERSYSTEM':
                    self.talkothersystem_byid(typeid)
                elif typename=='HIGHLIGHT':
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
                self.menutalk()
            else:
                self.tts.text_to_speech_and_play("找不到该系统")
        except sqlite3.Error as error:
            logger.error(error)

    def menutalk(self):
        """
        解说整个系统的所有菜单页面
        """
        try:
            # 查询菜单记录
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO, PAGEINDEX, DESC FROM MENUITEM ORDER BY ORDERNO")
            menucursor = cursor.fetchall()
            for row in menucursor:
                if self.askcontinu:
                    menuname = row[0]
                    willcontinue = input("继续演示[" + menuname + "]吗？")
                    if willcontinue == "n":
                        return
                self.menuitemtalk(row)
        except sqlite3.Error as error:
            logger.error(error)

    def talkitem_byname(self, menuname):
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

    def talkitem_byid(self, menuid):
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
                "SELECT NAME, ORDERNO, PAGEINDEX, DESC FROM OTHERSYSTEM WHERE ID = ?", (othersystemid,))
            itemcursor = cursor.fetchone()
            if itemcursor:
                # 发送页面切换指令
                pageindex = itemcursor[2]
                self.pagecontrol.sendPageCtl("OPEN_SYSTEM", pageindex)
                # 介绍页面功能
                itemname = itemcursor[0]
                itemdesc = itemcursor[3]
                logger.info("讲解" + itemname)
                self.tts.text_to_speech_and_play(itemname)
                self.tts.text_to_speech_and_play(itemdesc, self.askcontinu)
        except sqlite3.Error as error:
            logger.error(error)

    def talkhighlight_byid(self, highlightid):
        """
        解说某个亮点场景

        Args:
            highlightid (integer): 亮点场景id
        """
        try:
            # 查询菜单记录
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO, PAGEINDEX, DESC FROM HIGHTLIGHT WHERE ID = ?", (highlightid,))
            highlightcursor = cursor.fetchone()
            if highlightcursor:
                # 发送页面切换指令
                pageindex = highlightcursor[2]
                self.pagecontrol.sendPageCtl("OPEN_HIGHLIGHT", pageindex)
                # 介绍页面功能
                itemname = highlightcursor[0]
                itemdesc = highlightcursor[3]
                logger.info("讲解" + itemname)
                self.tts.text_to_speech_and_play(itemname)
                self.tts.text_to_speech_and_play(itemdesc, self.askcontinu)
        except sqlite3.Error as error:
            logger.error(error)

    def talkfeature_byid(self, featureid):
        """
        解说某个第三方系统

        Args:
            othersystemid (integer): 第三方系统id
        """
        try:
            # 查询菜单记录
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO,  DESC FROM FEATURES WHERE ID = ?", (featureid,))
            itemcursor = cursor.fetchone()
            if itemcursor:
                # 介绍页面功能
                itemname = itemcursor[0]
                itemdesc = itemcursor[2]
                logger.info("讲解" + itemname)
                self.tts.text_to_speech_and_play(itemname)
                self.tts.text_to_speech_and_play(itemdesc, self.askcontinu)
        except sqlite3.Error as error:
            logger.error(error)

    def menuitemtalk(self, menuitem):
        """
        解说某个菜单页面

        Args:
            menuitem (Cursor): 菜单项记录
        """
        if not menuitem:
            return
        # 发送页面切换指令
        pageindex = menuitem[2]
        self.pagecontrol.sendPageCtl("OPEN_PAGE", pageindex)
        # 介绍页面功能
        menuname = menuitem[0]
        menudesc = menuitem[3]
        logger.info("讲解" + menuname)
        self.tts.text_to_speech_and_play(menuname)
        self.tts.text_to_speech_and_play(menudesc, self.askcontinu)


if __name__ == '__main__':
    from voice.edge.EdgeVoice import EdgeVoice
    tts = EdgeVoice()
    sysIntro = sysIntroduction(tts, False)
    sysIntro.billtalk() #剧本
    # sysIntro.menutalk() #所有大屏页面
    # sysIntro.talkitem_byname("城市交通.地铁")
