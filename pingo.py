# -*- coding: utf-8 -*-

import hashlib
import os
import signal
import sys
import fire
from common import utils
from common.log import logger
from robot import detector
from config import conf, load_config
from robot.conversation import Conversation
# from server import server

class Pingo(object):
    _debug = False

    def __init__(self):
        # load config
        load_config()

    def init(self):
        self.detector = None
        self._interrupted = False
        self.conversation = Conversation() 
        self.conversation.say("您好,我的名字叫Pingo,很高兴见到您！说话之前记得叫我 ‘Hey pingo!'") 
    
    def _signal_handler(self, signal, frame):
        self._interrupted = True
        conf().save_user_datas()
        utils.clean()   
    
    def _interrupt_callback(self):
        return self._interrupted
                   
    def run(self):
        self.init()
        # capture SIGINT signal, e.g., Ctrl+C
        signal.signal(signal.SIGINT, self._signal_handler)
        # 后台管理端
        # server.run(self.conversation, self, debug=self._debug)
        try:
            # 初始化离线唤醒
            detector.initDetector(self)
        except AttributeError:
            logger.error("初始化离线唤醒功能失败", stack_info=True)
            pass

    def restart(self):
        """
        重启 pingo-robot
        """
        logger.critical("程序重启...")
        try:
            self.detector.terminate()
        except AttributeError:
            pass
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def md5(self, password):
        """
        计算字符串的 md5 值
        """
        return hashlib.md5(str(password).encode("utf-8")).hexdigest()
    def help(self):
        print(
            """=====================================================================================
    python pingo.py [命令]
    可选命令：
      md5                      - 用于计算字符串的 md5 值，常用于密码设置
====================================================================================="""
        )    

if __name__ == '__main__':
    if len(sys.argv) == 1:
        pingo= Pingo()
        pingo.run()
    elif "-h" in (sys.argv):
        pingo= Pingo()
        pingo.help()
    else:
        fire.Fire(Pingo)
        