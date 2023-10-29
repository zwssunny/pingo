# encoding:utf-8
import os
import uuid
import json
import requests
import datetime
from uuid import getnode as get_mac
from common.log import logger

def get_token(api_key, secret_key):
    """获取访问百度UUNIT 的access_token
    #param api_key: UNIT apk_key
    #param secret_key: UNIT secret_key
    Returns:
        string: access_token
    """
    url = "https://aip.baidubce.com/oauth/2.0/token?client_id={}&client_secret={}&grant_type=client_credentials".format(
        api_key, secret_key)
    payload = ""
    headers = {"Content-Type": "application/json",
                "Accept": "application/json"}

    response = requests.request("POST", url, headers=headers, data=payload)

    # print(response.text)
    return response.json()["access_token"]


def getUnit(query, service_id, api_key, secret_key):
    """
    NLU 解析

    :param query: 用户的指令字符串
    :param service_id: UNIT 的 service_id
    :param api_key: UNIT apk_key
    :param secret_key: UNIT secret_key
    :returns: UNIT 解析结果。如果解析失败，返回 None
    """
    access_token = get_token(api_key, secret_key)
    url = (
        "https://aip.baidubce.com/rpc/2.0/unit/service/chat?access_token="
        + access_token
    )
    request = {"query": query, "user_id": str(get_mac())[:32]}
    body = {
        "log_id": str(uuid.uuid1()),
        "version": "2.0",
        "service_id": service_id,
        "session_id": str(uuid.uuid1()),
        "request": request,
    }
    try:
        headers = {"Content-Type": "application/json"}
        request = requests.post(url, json=body, headers=headers)
        return json.loads(request.text)
    except Exception:
        return None


def getIntent(parsed):
    """
    提取意图

    :param parsed: UNIT 解析结果
    :returns: 意图数组
    """
    if parsed and "result" in parsed and "response_list" in parsed["result"]:
        try:
            return parsed["result"]["response_list"][0]["schema"]["intent"]
        except Exception as e:
            logger.warning(e)
            return ""
    else:
        return ""


def hasIntent(parsed, intent):
    """
    判断是否包含某个意图

    :param parsed: UNIT 解析结果
    :param intent: 意图的名称
    :returns: True: 包含; False: 不包含
    """
    if parsed and "result" in parsed and "response_list" in parsed["result"]:
        response_list = parsed["result"]["response_list"]
        for response in response_list:
            if (
                "schema" in response
                and "intent" in response["schema"]
                and response["schema"]["intent"] == intent
            ):
                return True
        return False
    else:
        return False


def getSlots(parsed, intent=""):
    """
        提取某个意图的所有词槽

        :param parsed: UNIT 解析结果
        :param intent: 意图的名称
        :returns: 词槽列表。你可以通过 name 属性筛选词槽，
    再通过 normalized_word 属性取出相应的值
    """
    if parsed and "result" in parsed and "response_list" in parsed["result"]:
        response_list = parsed["result"]["response_list"]
        if intent == "":
            try:
                return parsed["result"]["response_list"][0]["schema"]["slots"]
            except Exception as e:
                logger.warning(e)
                return []
        for response in response_list:
            if (
                "schema" in response
                and "intent" in response["schema"]
                and "slots" in response["schema"]
                and response["schema"]["intent"] == intent
            ):
                return response["schema"]["slots"]
        return []
    else:
        return []


def getSlotWords(parsed, intent, name):
    """
    找出命中某个词槽的内容

    :param parsed: UNIT 解析结果
    :param intent: 意图的名称
    :param name: 词槽名
    :returns: 命中该词槽的值的列表。
    """
    slots = getSlots(parsed, intent)
    words = []
    for slot in slots:
        if slot["name"] == name:
            words.append(slot["normalized_word"])
    return words


def getSlotOriginalWords(parsed, intent, name):
    """
    找出命中某个词槽的原始内容

    :param parsed: UNIT 解析结果
    :param intent: 意图的名称
    :param name: 词槽名
    :returns: 命中该词槽的值的列表。
    """
    slots = getSlots(parsed, intent)
    words = []
    for slot in slots:
        if slot["name"] == name:
            words.append(slot["original_word"])
    return words


def getSayByConfidence(parsed):
    """
    提取 UNIT 置信度最高的回复文本

    :param parsed: UNIT 解析结果
    :returns: UNIT 的回复文本
    """
    if parsed and "result" in parsed and "response_list" in parsed["result"]:
        response_list = parsed["result"]["response_list"]
        answer = {}
        for response in response_list:
            if (
                "schema" in response
                and "intent_confidence" in response["schema"]
                and (
                    not answer
                    or response["schema"]["intent_confidence"]
                    > answer["schema"]["intent_confidence"]
                )
            ):
                answer = response
        return answer["action_list"][0]["say"]
    else:
        return ""


def getSay(parsed, intent=""):
    """
    提取 UNIT 的回复文本

    :param parsed: UNIT 解析结果
    :param intent: 意图的名称
    :returns: UNIT 的回复文本
    """
    if parsed and "result" in parsed and "response_list" in parsed["result"]:
        response_list = parsed["result"]["response_list"]
        if intent == "":
            try:
                return response_list[0]["action_list"][0]["say"]
            except Exception as e:
                logger.warning(e)
                return ""
        for response in response_list:
            if (
                "schema" in response
                and "intent" in response["schema"]
                and response["schema"]["intent"] == intent
            ):
                try:
                    return response["action_list"][0]["say"]
                except Exception as e:
                    logger.warning(e)
                    return ""
        return ""
    else:
        return ""


if __name__ == "__main__":
    parsed = getUnit(
        "今天的天气",
        "S13442",
        "w5v7gUV3iPGsGntcM84PtOOM",
        "KffXwW6E1alcGplcabcNs63Li6GvvnfL",
    )
    print(parsed)
