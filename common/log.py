import logging
import os
import sys

PAGE = 4096


def tail(filepath, n=10):
    """
    实现 tail -n
    """
    res = ""
    with open(filepath, "rb") as f:
        f_len = f.seek(0, 2)
        rem = f_len % PAGE
        page_n = f_len // PAGE
        r_len = rem if rem else PAGE
        while True:
            # 如果读取的页大小>=文件大小，直接读取数据输出
            if r_len >= f_len:
                f.seek(0)
                lines = f.readlines()[::-1]
                break

            f.seek(-r_len, 2)
            lines = f.readlines()[::-1]
            count = len(lines) - 1  # 末行可能不完整，减一行，加大读取量

            if count >= n:  # 如果读取到的行数>=指定行数，则退出循环读取数据
                break
            else:  # 如果读取行数不够，载入更多的页大小读取数据
                r_len += PAGE
                page_n -= 1

    for line in lines[:n][::-1]:
        res += line.decode("utf-8")
    return res


def _reset_logger(log):
    for handler in log.handlers:
        handler.close()
        log.removeHandler(handler)
        del handler
    log.handlers.clear()
    log.propagate = False
    console_handle = logging.StreamHandler(sys.stdout)
    console_handle.setFormatter(
        logging.Formatter(
            "[%(levelname)s][%(asctime)s][%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    file_handle = logging.FileHandler("pingo.log", encoding="utf-8")
    file_handle.setFormatter(
        logging.Formatter(
            "[%(levelname)s][%(asctime)s][%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    log.addHandler(file_handle)
    log.addHandler(console_handle)


def _get_logger():
    log = logging.getLogger("log")
    _reset_logger(log)
    log.setLevel(logging.INFO)
    return log


def readLog(lines=200):
    """
    获取最新的指定行数的 log

    :param lines: 最大的行数
    :returns: 最新指定行数的 log
    """
    app_path = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
)
    log_path = os.path.join(app_path, "pingo.log")
    if os.path.exists(log_path):
        return tail(log_path, lines)
    return ""


# 日志句柄
logger = _get_logger()
