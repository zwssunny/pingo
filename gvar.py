from config import conf, load_config


class GVar(object):
    # 会话,Conversation
    conversation = None
    # Pingo
    pingo = None
    load_config()
    serverconf = conf().get("server", {"host": "0.0.0.0", "port": "5001"})
    sysdb = "./db/pingo.db"
