# -*- coding: utf-8 -*-

import hashlib
import os
import shutil
import tempfile
import _thread as thread
import time
from config import conf, load_config

APP_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
)
load_config()
CACH_PATH = os.path.join(APP_PATH, "cach", conf().get("edge-tts")["voice"])
TMP_PATH = os.path.join(APP_PATH, "tmp")
TEMPLATE_PATH = os.path.join(APP_PATH, "server", "templates")
DATA_PATH = os.path.join(APP_PATH, "static")

def getCache(msg):
    """获取缓存的语音"""
    md5 = hashlib.md5(msg.encode("utf-8")).hexdigest()
    cache_paths = [
        os.path.join(CACH_PATH, md5 + ext)
        for ext in [".mp3", ".wav", ".asiff"]
    ]
    return next((path for path in cache_paths if os.path.exists(path)), None)


def saveCache(voice, msg):
    """保存语音到缓存"""
    _, ext = os.path.splitext(voice)
    md5 = hashlib.md5(msg.encode("utf-8")).hexdigest()
    if not os.path.exists(CACH_PATH):
        os.makedirs(CACH_PATH)
    target = os.path.join(CACH_PATH, md5 + ext)
    shutil.copyfile(voice, target)
    return target

def clean():
    """清理垃圾数据"""
    temp = TMP_PATH
    temp_files = os.listdir(temp)
    for f in temp_files:
        if os.path.isfile(os.path.join(temp, f)): 
            os.remove(os.path.join(temp, f))

def write_temp_file(data, suffix, mode="w+b"):
    """
    写入临时文件

    :param data: 数据
    :param suffix: 后缀名
    :param mode: 写入模式，默认为 w+b
    :returns: 文件保存后的路径
    """
    with tempfile.NamedTemporaryFile(mode=mode, suffix=suffix, delete=False) as f:
        f.write(data)
        tmpfile = f.name
    return tmpfile   
         
def check_and_delete(fp, wait=0):
    """
    检查并删除文件/文件夹

    :param fp: 文件路径
    """

    def run():
        if wait > 0:
            time.sleep(wait)
        if isinstance(fp, str) and os.path.exists(fp):
            if os.path.isfile(fp):
                os.remove(fp)
            else:
                shutil.rmtree(fp)

    thread.start_new_thread(run, ())
    
def getPunctuations():
    return [",", "，", ".", "。", "?", "？", "!", "！", "\n"]


def stripPunctuation(s):
    """
    移除字符串末尾的标点
    """
    punctuations = getPunctuations()
    if any(s.endswith(p) for p in punctuations):
        s = s[:-1]
    return s


if __name__ == '__main__':
    msg="打牌"
    md5 = getCache(msg)
    print(md5)