# coding: utf-8
# !/usr/bin/env python3

"""VITS TTS API"""

import requests


def tts(text, server_url, api_key, speaker_id, length, noise, noisew, max, timeout):
    data = {
        "text": text,
        "id": speaker_id,
        "format": "wav",
        "lang": "auto",
        "length": length,
        "noise": noise,
        "noisew": noisew,
        "max": max
    }
    headers = {"api_key": api_key}
    res = requests.post(url=server_url, data=data, headers=headers, timeout=timeout)
    res.raise_for_status()
    return res.content
