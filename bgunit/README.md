## 插件说明

利用百度UNIT实现智能对话，返回意图和词槽

- 操控页面：打开首页，导航到综合交通
- 利用unit机器人返回的意图，调用平台接口进行页面操控，这些技能需要用户训练的

## 使用说明

### 获取apikey

在百度UNIT官网上自己创建应用，申请百度机器人,可以把预先训练好的模型导入到自己的应用中，

see https://ai.baidu.com/unit/home#/home?track=61fe1b0d3407ce3face1d92cb5c291087095fc10c8377aaf 
https://console.bce.baidu.com/ai平台申请

### 配置文件

将文件夹中`config.json.template`复制为`config.json`。

在其中填写百度UNIT官网上获取应用列表中的API Key和Secret Key
注意，service_id填写是自己创建的机器人ID，s开头，不是应用列表中的APPID
``` json
    {
    "service_id": "s...", #"机器人ID"
    "api_key": "",
    "secret_key": "",
    "pageintent": ["OPEN_PAGE","CLOSE_PAGE"], #页面操作意图
    "systemintent": ["OPEN_SYSTEM","CLOSE_SYSTEM"], #相关系统操作意图
    "highlightintent": ["OPEN_HIGHLIGHT","CLOSE_HIGHLIGHT"] #亮点场景操作意图
    }
```