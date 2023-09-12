# Pingo

智能音箱
调用百度UNIT机器人进行对话，实现插件调用机器人返回的用户的意图，在调用第三方系统接口，从而可以实现想要的功能；比如页面导航功能

登录 https://ai.baidu.com/unit/home#/home，可以创建自己的机器人和训练自己的技能。

## 语音识别

BaiduASR,OpenaiASR,AzureASR,其它的可以加

## 语音合成

BaiduTTS,Pyttsx3TTS,AzureTTS,EdgeTTS,其它的可以加

## 运行环境

python版本>=3.0，windows11环境开发测试；其它平台还没测试，有测试过的小伙伴请通知一下！

## porcupine 离线唤醒

登录 https://console.picovoice.ai/
可以获取 access_key 和训练自己的唤醒词

## 缓存语音功能

cach目录是缓存历史的语音功能，可以减少语音合成次数调用，节省时间，提高效率。如果转换人声语调和转换语音合成引擎，可以删除该目录下文件。