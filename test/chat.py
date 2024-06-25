import os
import sys
import uuid
import torchaudio
import torch
# from IPython.display import Audio
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from common import utils
from dotenv import load_dotenv
load_dotenv("sha256.env")
import ChatTTS

chat = ChatTTS.Chat()
chat.load(compile=False)  # Set to True for better performance

texts = ["四川美食确实以辣闻名，但也有不辣的选择。比如甜水面、赖汤圆、蛋烘糕、叶儿粑等，这些小吃口味温和，甜而不腻，也很受欢迎。",]

wavs = chat.infer(texts, skip_refine_text=True,)
tmpfile = os.path.join(utils.TMP_PATH, uuid.uuid4().hex + ".wav")
torchaudio.save(tmpfile, torch.from_numpy(wavs[0]), 24000)
