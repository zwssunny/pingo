# -*- coding: utf-8 -*-

import hashlib
import os
import shutil
import tempfile
import _thread as thread
import time
from pydub import AudioSegment
from common.tmp_dir import TmpDir
from config import conf, load_config

APP_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
)
load_config()
VOICENAME = conf().get("edge-tts")["voice"]
CACH_PATH = os.path.join(APP_PATH, "cach")
TMP_PATH = os.path.join(APP_PATH, "tmp")
TEMPLATE_PATH = os.path.join(APP_PATH, "server", "templates")
DATA_PATH = os.path.join(APP_PATH, "static")


def getCache(msg, voicename=None):
    """获取缓存的语音"""
    md5 = hashlib.md5(msg.encode("utf-8")).hexdigest()
    if voicename is None:
        voicename = VOICENAME
    cache_paths = [
        os.path.join(CACH_PATH, voicename, md5 + ext)
        for ext in [".mp3", ".wav", ".asiff"]
    ]
    return next((path for path in cache_paths if os.path.exists(path)), None)


def saveCache(voice, msg, voicename=None):
    """保存语音到缓存"""
    _, ext = os.path.splitext(voice)
    md5 = hashlib.md5(msg.encode("utf-8")).hexdigest()
    if voicename is None:
        voicename = VOICENAME
    voicename_path = os.path.join(CACH_PATH, voicename)
    if not os.path.exists(voicename_path):
        os.makedirs(voicename_path)
    target = os.path.join(voicename_path, md5 + ext)
    shutil.copyfile(voice, target)
    return target


def sounddownsampling(audiofile, sample_rate=16000, format="wav"):
    """降低录制声音的采样率

    Args:
        audiofile (str): 输入声音文件
        sample_rate (int, optional): 输出频率. Defaults to 16000.
        format (str, optional): 输出格式. Defaults to "wav".

    Returns:
        str: 返回处理后的文件
    """    
    sound = AudioSegment.from_file(audiofile)
    sound = sound.set_frame_rate(16000)
    sound = sound.set_channels(1)
    sound = sound.set_sample_width(2)
    fname, suffix = os.path.splitext(audiofile)
    nfile = fname +"-"+str(sample_rate) + suffix
    sound = sound.export(nfile, format=format)
    return nfile


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
    tmpfile = TmpDir().path() + "speech-" + str(int(time.time())) + suffix
    with open(tmpfile, mode) as f:
        f.write(data)

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
    msg = "打牌"
    md5 = getCache(msg)
    print(md5)
