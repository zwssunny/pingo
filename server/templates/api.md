# 后台 API

[TOC]

## 鉴权

所有接口都需要带上 `validate` 参数，该参数值和配置文件中的 `server["validate"]` 参数值相同。示例：

``` sh
$ curl localhost:5001/history?validate=2499d2e04e0f949927690d6375ce1a67
```

接口返回：

```
{"code": 0, "message": "ok","history":[...]}
```

## 管理

用于管理 Bingo-robot ，包括重启/播放/获取播放状态。

- url：/operate
- method: POST
- 参数：

| 参数名 |  是否必须 | 说明  |
| ---   | ------- | ----- |
| validate | 是 | 参见 [鉴权](#_1) |
| type  | 是 |  管理类型类型。详见 [管理类型取值](#管理类型取值) |
| billid  | 是 | 如果type=1,必须传递演讲方案ID，如果没有指定特定billitemid,则播放该方案下所有节目 |
| billitemid  | 否|  演讲节点ID，如果billitemid>0 将忽略billid值 |


### 管理类型取值

| 取值 | 说明 |
| ---- |  ---- |
| 0    | 重启 Bingo-robot |
| 1    | 播放 |
| 2    | 暂停播放 |
| 3    | 继续播放 |
| 4    | 停止播放 |
| 5    | 获取播放状态 |

- 示例：

``` sh
$ curl -X POST localhost:5001/operate -d "type=restart&validate=f4bde2a342c7c75aa276f78b26cfbd8a"
```

- 返回：

| 字段名 |  说明  |
| ---   | ----- |
| code  | 返回码。0：成功；1：失败 |
| message | 结果说明 |

## 日志

用于查看 Bingo-robot 保存的日志。出于性能上的考虑，默认只返回最后 200 行的内容，相当于做了一次 `tail -n 200` 。

- url：/log
- method: GET
- 参数：

| 参数名 |  是否必须 | 说明  |
| ---   | ------- | ----- |
| validate | 是 | 参见 [鉴权](#_1) |
| lines | 可选 | 最大读取的日志行数。默认值为 200  |

- 示例：

``` sh
$ curl localhost:5001/log?validate=f4bde2a342c7c75aa276f78b26cfbd8a&lines=10
```

- 返回：

| 字段名 |  说明  |
| ---   | ----- |
| code  | 返回码。0：成功；1：失败 |
| message | 结果说明 |
| log | 日志内容 |


## 对话

### 发起对话

用于发起一次对话。

- url：/chat
- method: POST
- 参数：

| 参数名 |  是否必须 | 说明  |
| ---   | ------- | ----- |
| validate | 是 | 参见 [鉴权](#_1) |
| type  | 是 |  query 类型。 "text": 文本型 query ； "voice"：语音型 query |
| query | 仅当 type 为 "text" 时需要 |  发起对话的内容的 urlencode 后的值。例如 ”现在几点？“ 的 urlencode 结果 | 
| uuid  | 仅当 type 为 "text" 时需要 |  为这个文本 query 赋予的一个 uuid。例如可以使用随机字符+时间戳。|
| voice | 仅当 type 为 "voice" 时需要  | 语音。需为 单通道，采样率为 16k 的 wav 格式语音的 base64 编码。 |

- 示例：

``` sh
$ curl -X POST localhost:5001/chat -d "type=text&query=%E7%8E%B0%E5%9C%A8%E5%87%A0%E7%82%B9&validate=f4bde2a342c7c75aa276f78b26cfbd8a&uuid=chated17be5d-0240-c9ba-2b2e-7eb98588cf34"
```

- 返回：

| 参数名 |  说明  |
| ---   | ----- |
| code  | 返回码。0：成功；1：失败 |
| message | 结果说明 |

### 对话历史

用于查看 Bingo-robot 启动到现在的所有会话记录。

- url：/history
- method: GET
- 参数：

| 参数名 |  是否必须 | 说明  |
| ---   | ------- | ----- |
| validate | 是 | 参见 [鉴权](#_1) |

- 示例：

``` sh
$ curl localhost:5001/history?validate=f4bde2a342c7c75aa276f78b26cfbd8a
```

- 返回：

| 字段名 |  说明  |
| ---   | ----- |
| code  | 返回码。0：成功；1：失败 |
| message | 结果说明 |
| history | 会话历史 |

## 配置

### 查看配置

用于查看 Bingo-robot 现有的配置。

- url：/config
- method: GET
- 参数：

| 参数名 |  是否必须 | 说明  |
| ---   | ------- | ----- |
| validate | 是 | 参见 [鉴权](#_1) |
| key | 可选 | 某个配置的键值。例如：`robot_name_cn` 。如果要key的对应多子节点，则使用 server={'host': '0.0.0.0','port': '5001'} 的形式，例如 `server["host"]` 可以取 `server` 的 `host` 配置。 |

- 示例：

``` sh
$ curl localhost:5001/config?validate=f4bde2a342c7c75aa276f78b26cfbd8a\&key=server
```

- 返回：

| 字段名 |  说明  |
| ---   | ----- |
| code  | 返回码。0：成功；1：失败 |
| message | 结果说明 |
| config | 全部的配置，仅当不传 `key` 参数时提供 |
| value | `key` 提供的配置，仅当传 `key` 参数时提供；如果找不到这个 `key`，则返回 `null` |

### 修改配置

用于配置 Bingo-robot 。

- url：/config
- method: POST
- 参数：

| 参数名 |  是否必须 | 说明  |
| ---   | ------- | ----- |
| validate | 是 | 参见 [鉴权](#_1) |
| config | 是 | 配置内容，必须为 json 可解析的文本经过 urlencode 后的值 |

- 示例：


- 返回：

| 字段名 |  说明  |
| ---   | ----- |
| code  | 返回码。0：成功；1：失败 |
| message | 结果说明 |


## 演讲

### 获取演讲方案列表

用于获取系统已存在的演讲方案 。

- url：/bills
- method: GET
- 参数：

| 参数名 |  是否必须 | 说明  |
| ---   | ------- | ----- |
| validate | 是 | 参见 [鉴权](#_1) |
| billid | 否 | 如果提供特定的方案ID，则返回当前剧本记录，否则返回所有方案列表 |

- 返回：

| 字段名 |  说明  |
| ---   | ----- |
| code  | 返回码。0：成功；1：失败 |
| message | 结果说明 |
| bills | 返回记录列表，一条或者多条 |


### 获取节目列表

用于获取系统已存在的演讲节目 。

- url：/billitems
- method: GET
- 参数：

| 参数名 |  是否必须 | 说明  |
| ---   | ------- | ----- |
| validate | 是 | 参见 [鉴权](#_1) |
| billid | 是 | 提供特定的演讲方案ID |
| itemid | 否 | 如果提供特定的节点ID，则返回该条记录，否则返回该方案billid下所有节点|

- 返回：

| 字段名 |  说明  |
| ---   | ----- |
| code  | 返回码。0：成功；1：失败 |
| message | 结果说明 |
| billItems | 返回记录列表，一条或者多条 |


### 更新节点

用于更新系统已存在的节目 。

- url：/billitems
- method: POST
- 参数：

| 参数名 |  是否必须 | 说明  |
| ---   | ------- | ----- |
| validate | 是 | 参见 [鉴权](#_1) |
| id | 是 | 提供特定的节点ID |
| orderno | 是 | 演示顺序号|
| sleep | 是 | 演讲前等待时间，秒|
| desc | 是 | 演讲词|

- 返回：

| 字段名 |  说明  |
| ---   | ----- |
| code  | 返回码。0：成功；1：失败 |
| message | 结果说明 |