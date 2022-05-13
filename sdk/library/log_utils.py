# coding=utf-8
import os
import logging
log_format = '%(asctime)s %(threadName)s %(levelname)s %(filename)s:%(lineno)d %(funcName)s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=log_format)


def new_logger(path=None, name=None):
    """实例化一个日志记录器"""
    assert name or path, 'path or name must select one'
    if path:
        name = os.path.abspath(__file__).replace(os.getcwd() + os.path.sep, '').replace('.py', '')
    logger = logging.getLogger(name)
    logger.setLevel(logging.ERROR)
    return logger


# 控制日志输出
logging.getLogger('requests').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)

