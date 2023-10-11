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
    def __init__(self, tts: Voice, askcontinu: bool = False):
        self.conn = sqlite3.connect(sysdb)
        self.tts = tts
        self.askcontinu = askcontinu
        self.pagecontrol = pagecontrol()

    def systalk(self):
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
        try:
            # 查询菜单记录
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO, PAGEINDE, DESC FROM MENUITEM ORDER BY ORDERNO")
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
        try:
            # 查询菜单记录
            name_pattern = "%" + menuname
            cursor = self.conn.execute(
                "SELECT NAME, ORDERNO, PAGEINDE, DESC FROM MENUITEM WHERE NAME LIKE ?", (name_pattern,))
            menucursor = cursor.fetchone()
            if menucursor:
                self.menuitemtalk(menucursor)
        except sqlite3.Error as error:
            logger.error(error)

    def menuitemtalk(self, menuitem):
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
    sysIntro.menutalk()
    # sysIntro.talkitem_byname("城市交通.道路运行")
