# encoding:utf-8

import json
import logging
import os
import pickle

from common.log import logger

# 将所有可用的配置项写在字典里, 请使用小写字母
# 此处的配置值无实际意义，程序不会读取此处的配置，仅用于提示格式，请将配置加入到config.json中
available_setting = {
    "debug":  False,  # 是否调式模式
    "picovoice_api_key": "",  # 你的picovoice key
    "keyword_path": "",  # 你的唤醒词检测离线文件地址
    "model_path": "",   # 中文模型地址
    "sensitivity": 0.5,  # 噪音指数
    "appdata_dir": "", #用户数据保存路径
    "notbother": {  # 免打扰模式
        "enable": False,  # true: 开启; false: 关闭
        "since": 23,    # 开始时间
        "till": 9      # 结束时间，如果比 since 小表示第二天
    },
    #后台控制管理服务器
    "server": {
        "enable": True,
        "host": "0.0.0.0",  # ip 地址
        "port": 5001,  # 端口号
        "username": "pingo",  # 用户名
        # cookie 的 secret ，用于对 cookie 的内容进行加密及防止篡改
        # 建议使用 os.urandom(24) 生成一串随机字符串
        # 强烈建议修改!!!
        "cookie_secret": "__GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        # 密码的 md5，可以用 python3 pingo.py md5 "密码" 获得
        # 初始密码为 pingo@2023
        # 强烈建议修改!!!
        "validate": "2499d2e04e0f949927690d6375ce1a67"
    },
    #识别引擎配置
    "asr_engine": "baidu-asr",
    # azure 语音api配置， 使用azure语音识别和语音合成时需要
    "azure_yuyin": {
        "api_key": "",  # 你的azure key
        "region": "japaneast",  # 你的azure region
        "lang": "zh-CN",  #语言
        "voice": "zh-CN-XiaoxiaoNeural" #语音
    },
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
    #文字转语音配置
    "tts_engine": "edge-tts",
    "edge-tts": {
        "voice": "zh-CN-XiaoxiaoNeural"
    },
    "VITS": {  # 需要自行搭建vits-simple-api服务器：https://github.com/zwssunny/vits-simple-api
        "server_url": "http://127.0.0.1:23456",  # 服务器url
        "api_key": "api_key",  # 若服务器配置了API Key，在此填入
        "speaker_id": 0,  # 说话人ID，由所使用的模型决定
        "length": 1.0,  # 调节语音长度，相当于调节语速，该数值越大语速越慢。
        "noise": 0.667,  # 噪声
        "noisew": 0.8,  # 噪声偏差
        "max": 50,  # 分段阈值，按标点符号分段，加起来大于max时为一段文本。max<=0表示不分段。
        "timeout": 60  # 响应超时时间（秒），根据vits-simple-api服务器性能不同配置合理的超时时间。
    },
    #NLU解析引擎
    "nlu_engine": "unit",
    # 百度Unit机器人
    "unit": {
        "service_id": "",  # "机器人ID"
        "api_key": "",
        "secret_key": ""
    },
    # 聊天机器人
    "robot": "unit",
    #OpenAI聊天机器人
    "openai": {
        "openai_api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxx",
        # 参数指定将生成文本的模型类型。目前支持 gpt-3.5-turbo 和 gpt-3.5-turbo-0301 两种选择
        "model": "gpt-3.5-turbo",
        # 在前面加的一段前缀
        "prefix": "请用200字回答：",
        # 该temperature参数可以设置返回内容地多样性。值越大意味着该模型更有可能产生创造性的东西，设置为 1 意味着模型将返回它不确定的结果；相比之下，将此参数设置为 0 意味着模型将返回它几乎可以肯定的结果。
        "temperature": 1,
        # 该max_tokens参数指定模型允许生成的最大字符数量作为其输出的一部分。您需要为生成的更多字符付费，因此请务必小心使用此参数。
        "max_tokens": 2000,
        # 一个可用于代替 temperature 的参数，对应机器学习中 nucleus sampling，如果设置 0.1 意味着只考虑构成前 10% 概率质量的 tokens
        "top_p": 1.0,
        # -2.0 ~ 2.0 之间的数字，正值会根据新 tokens 在文本中的现有频率对其进行惩罚，从而降低模型逐字重复同一行的可能性
        "frequency_penalty": 0.0,
        # -2.0 ~ 2.0 之间的数字，正值会根据到目前为止是否出现在文本中来惩罚新 tokens，从而增加模型谈论新主题的可能性
        "presence_penalty": 0.0,
        "stop_ai": "stop"
        # 如果需要代理，反注释下面的配置进行修改
        # proxy: '127.0.0.1:1080'
        # 如果需要更换 api_base ，反注释下面的配置进行修改
        # api_base: "https://api.openai.com/v1/chat"
    },
    # 演讲和页面控制配置参数
    "pagecontrol": {  # 大屏页面控制
        "enable": False,
        "websocketurl": "ws://10.201.63.153:8081/daasPortal/websocket/",  # websocket服务地址
        "screenid": "dbe5b0425026446fb52437e8e58ed73f"  # 大屏ID
    },
    "pageintent": [ #页面控制事件
        "OPEN_PAGE",
        "CLOSE_PAGE"
    ],
    "systemintent": [ #第三方系统控制事件
        "OPEN_SYSTEM",
        "CLOSE_SYSTEM"
    ],
    "highlightintent": [ #亮点场景控制事件
        "OPEN_HIGHLIGHT",
        "CLOSE_HIGHLIGHT"
    ],

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
has_init = False


def reload_config():
    """重新加载参数
    """
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
