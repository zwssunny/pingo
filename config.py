# encoding:utf-8

import json
import logging
import os
import pickle

from common.log import logger

has_init = False
# 将所有可用的配置项写在字典里, 请使用小写字母
# 此处的配置值无实际意义，程序不会读取此处的配置，仅用于提示格式，请将配置加入到config.json中
available_setting = {
    # openai api配置
    "debug":  False,  # openai api key
    "picovoice_api_key": "",  # 你的picovoice key
    "keyword_path": "",  # 你的唤醒词检测离线文件地址
    "model_path": "",   # 中文模型地址
    "sensitivity": 0.5,  # 噪音指数
    # azure 语音api配置， 使用azure语音识别和语音合成时需要
    "azure_api_key": "",  # 你的azure key
    "azure_region": "japaneast",  # 你的azure region
    "debug": True,
    "appdata_dir": "",
    "canpause": True,  # 是否可以暂停
    "ctlandtalk": True,  # 是否控制页面并解说内容
    "server": {
        "enable": True,
        "host": "0.0.0.0",  # ip 地址
        "port": 5001,  # 端口号
        "username": "pingo",  # 用户名
        # cookie 的 secret ，用于对 cookie 的内容进行加密及防止篡改
        # 建议使用 os.urandom(24) 生成一串随机字符串
        # 强烈建议修改!!!
        "cookie_secret": "__GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        # 密码的 md5，可以用 python3 main.py md5 "密码" 获得
        # 初始密码为 pingo@2023
        # 强烈建议修改!!!
        "validate": "2499d2e04e0f949927690d6375ce1a67"
    },
    "asr_engine": "baidu-asr",
    # baidu 语音api配置， 使用百度语音识别和语音合成时需要
    "baidu_yuyin": {
        "appid": "",  # 你的百度APP_ID
        "api_key": "",  # 你的百度API_KEY
        "secret_key": "",  # 你的百度SECRET_KEY
        "dev_pid": 1536,
        "per": 1,
        "lan": "zh"
    },
    "xunfei_yuyin": {
        "appid": "",  # 你的讯飞APP_ID
        "api_key": "",  # 你的讯飞API_KEY
        "api_secret": "",  # 你的讯飞SECRET_KEY
        "voice": "xiaoyan"  # 音调
    },
    "tts_engine": "edge-tts",
    "edge-tts": {
        "voice": "zh-CN-XiaoxiaoNeural"
    },
    "nlu_engine": "unit",
    # 百度Unit机器人
    "unit": {
        "service_id": "",  # "机器人ID"
        "api_key": "",
        "secret_key": ""
    },
    "pageintent": [
        "OPEN_PAGE",
        "CLOSE_PAGE"
    ],
    "systemintent": [
        "OPEN_SYSTEM",
        "CLOSE_SYSTEM"
    ],
    "highlightintent": [
        "OPEN_HIGHLIGHT",
        "CLOSE_HIGHLIGHT"
    ],
    "notbother": { #免打扰模式
        "enable": False,  # true: 开启; false: 关闭
        "since": 23,    # 开始时间
        "till": 9      # 结束时间，如果比 since 小表示第二天
    },
}


class Config(dict):
    def __init__(self, d=None):
        super().__init__()
        if d is None:
            d = {}
        for k, v in d.items():
            self[k] = v
        # user_datas: 用户数据，key为用户名，value为用户数据，也是dict
        self.user_datas = {}

    def __getitem__(self, key):
        if key not in available_setting:
            raise Exception("key {} not in available_setting".format(key))
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        if key not in available_setting:
            raise Exception("key {} not in available_setting".format(key))
        return super().__setitem__(key, value)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError as e:
            return default
        except Exception as e:
            raise e
    # Make sure to return a dictionary to ensure atomic

    def get_user_data(self, user) -> dict:
        if self.user_datas.get(user) is None:
            self.user_datas[user] = {}
        return self.user_datas[user]

    def load_user_datas(self):
        try:
            with open(os.path.join(get_appdata_dir(), "user_datas.pkl"), "rb") as f:
                self.user_datas = pickle.load(f)
                logger.info("[Config] User datas loaded.")
        except FileNotFoundError as e:
            logger.info("[Config] User datas file not found, ignore.")
        except Exception as e:
            logger.info("[Config] User datas error: {}".format(e))
            self.user_datas = {}

    def save_user_datas(self):
        try:
            with open(os.path.join(get_appdata_dir(), "user_datas.pkl"), "wb") as f:
                pickle.dump(self.user_datas, f)
                logger.info("[Config] User datas saved.")
        except Exception as e:
            logger.info("[Config] User datas error: {}".format(e))

    def getText(self):
        config_path = "./config.json"
        config_str = read_file(config_path)
        return config_str

    def dump(self, configStr):
        config_path = "./config.json"
        with open(config_path, mode="w", encoding="utf-8") as f:
            f.write(configStr)


config = Config()


def reload_config():
    """重新加载参数
    """
    global has_init
    has_init = False
    load_config()


def load_config():
    global config
    global has_init
    if has_init:
        return

    config_path = "./config.json"
    if not os.path.exists(config_path):
        logger.info("配置文件不存在，将使用config-template.json模板")
        config_path = "./config-template.json"

    config_str = read_file(config_path)
    logger.debug("[INIT] config str: {}".format(config_str))

    # 将json字符串反序列化为dict类型
    config = Config(json.loads(config_str))

    # override config with environment variables.
    # Some online deployment platforms (e.g. Railway) deploy project from github directly. So you shouldn't put your secrets like api key in a config file, instead use environment variables to override the default config.
    for name, value in os.environ.items():
        name = name.lower()
        if name in available_setting:
            logger.info(
                "[INIT] override config by environ args: {}={}".format(name, value))
            try:
                config[name] = eval(value)
            except:
                if value == "false":
                    config[name] = False
                elif value == "true":
                    config[name] = True
                else:
                    config[name] = value

    if config.get("debug", False):
        logger.setLevel(logging.DEBUG)
        logger.debug("[INIT] set log level to DEBUG")

    # logger.info("[INIT] load config: {}".format(config))

    has_init = True
    config.load_user_datas()


def get_root():
    return os.path.dirname(os.path.abspath(__file__))


def read_file(path):
    with open(path, mode="r", encoding="utf-8") as f:
        return f.read()


def conf():
    return config


def get_appdata_dir():
    data_path = os.path.join(get_root(), conf().get("appdata_dir", ""))
    if not os.path.exists(data_path):
        logger.info(
            "[INIT] data path not exists, create it: {}".format(data_path))
        os.makedirs(data_path)
    return data_path


def subscribe_msg():
    trigger_prefix = conf().get("single_chat_prefix", [""])[0]
    msg = conf().get("subscribe_msg", "")
    return msg.format(trigger_prefix=trigger_prefix)


# global plugin config
plugin_config = {}


def write_plugin_config(pconf: dict):
    """
    写入插件全局配置
    :param pconf: 全量插件配置
    """
    global plugin_config
    for k in pconf:
        plugin_config[k.lower()] = pconf[k]


def pconf(plugin_name: str) -> dict:
    """
    根据插件名称获取配置
    :param plugin_name: 插件名称
    :return: 该插件的配置项
    """
    return plugin_config.get(plugin_name.lower())


# 全局配置，用于存放全局生效的状态
global_config = {
    "admin_users": []
}
