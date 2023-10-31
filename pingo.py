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
from server import server

class Pingo(object):
    _debug = False

    def __init__(self):
        # load config
        load_config()

    def init(self):
        self.detector = None
        self._interrupted = False
        serverhost=conf().get("server",{"host": "0.0.0.0","port": "5001"})
        print(
            """
            后台管理端：http://{}:{}
            如需退出，可以按 Ctrl+C 组合键

""".format(
                serverhost["host"],
                serverhost["port"],
            )
        )
        self.conversation = Conversation() 
        self.conversation.say("您好,我的名字叫Pingo,很高兴见到您！说话之前记得叫我 ‘Hey pingo!'") 
    
    def sigterm_handler_wrap(self, _signo):
        old_handler = signal.getsignal(_signo)
        self._interrupted = True
        def func(_signo, _stack_frame):
            logger.info("signal {} received, exiting...".format(_signo))
            conf().save_user_datas()
            utils.clean()  
            if callable(old_handler):  #  check old_handler
                return old_handler(_signo, _stack_frame)
            sys.exit(0)
        signal.signal(_signo, func)

    def _interrupt_callback(self):
        return self._interrupted
                   
    def run(self):
        try:
            self.init()
            # capture SIGINT signal, e.g., Ctrl+C
            # ctrl + c
            self.sigterm_handler_wrap(signal.SIGINT)
            # kill signal
            self.sigterm_handler_wrap(signal.SIGTERM)
            # 后台管理端
            server.run(self.conversation, self, debug=self._debug)
            # 初始化离线唤醒
            detector.initDetector(self)
        except Exception as e:
            logger.error("Pingo startup failed!")
            logger.exception(e)

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
        