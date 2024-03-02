# Pingo

智能机器人
Pingo被唤醒后，用户的语音指令先经过 ASR 引擎进行 ASR 识别成文本，然后对识别到的文本进行 NLU 解析，再将解析结果进行技能匹配，交给适合处理该指令的技能插件去处理。插件处理完成后，得到的结果再交给 TTS 引擎合成语音，播放给用户。
比如页面导航功能,系统介绍等功能。

本机器人用百度UNIT机器人进行技能训练和识别

登录 https://ai.baidu.com/unit/home#/home
可以创建自己的机器人和训练自己的技能。

## 语音识别

BaiduASR,OpenaiASR,AzureASR,XunfeiASR,其它的可以加

## 语音合成

BaiduTTS,AzureTTS,EdgeTTS,XunfeiTTS，VITTS其它的可以加

VITS 语音合成
需要自行搭建vits-simple-api服务器：https://github.com/zwssunny/vits-simple-api

## 聊天机器人

unitRobot,Openai的Chatgpt,其它的可以加

## 运行环境

python版本>=3.10，ubutun22,windows11环境开发测试；其它平台还没测试，有测试过的小伙伴请通知一下！

系统需要安装ffmpeg工具，安装依赖库：pip install -r requirements.txt

## porcupine 离线唤醒

登录 https://console.picovoice.ai/
可以获取 access_key 和训练自己的唤醒词

## 缓存语音功能

cach目录是缓存历史的语音功能，可以减少语音合成次数调用，节省时间，提高效率。

## 系统演示功能
打开浏览器登录https://localhost:5001/
登录名pingo 密码 pingo@2023

可以完整演示整个平台，逐个页面切换展示，同时对页面内容进行介绍