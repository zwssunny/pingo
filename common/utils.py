# -*- coding: utf-8 -*-

import hashlib
import os
import shutil
from config import conf, load_config

APP_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
)
load_config()
CACH_PATH = os.path.join(APP_PATH, "cach/"+conf().get("voice","zh-CN-YunjianNeural"))
TMP_PATH = os.path.join(APP_PATH, "tmp")

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

if __name__ == '__main__':
    msg="打牌"
    md5 = getCache(msg)
    print(md5)