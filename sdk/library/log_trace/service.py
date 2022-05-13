# coding=utf-8
import requests
import traceback
import threading
from .dto import LogC
from library.log_utils import new_logger, logging
from multiprocessing import Queue

logger = new_logger(path=__file__)
logger.setLevel(logging.DEBUG)


class LogTrace(object):
    """日志追踪"""
    __logQueue = Queue()  # type: Queue
    __httpHost = None  # type: str

    def __init__(self, httpHost):
        assert httpHost, u'httpHost must'
        self.__httpHost = httpHost
        self.__logQueue = Queue()
        self.__taskThread = threading.Thread(target=self.loop_handle, name='IOTOS_LOG_TRACE')
        self.__taskThread.setDaemon(True)
        self.__taskThread.start()

    def loop_handle(self):
        while True:
            logC = self.__logQueue.get(block=True)
            if isinstance(logC, LogC) is False:
                continue
            self.__log_update(logC=logC)

    def put(self, logC):
        """上报数据"""
        assert isinstance(logC, LogC)
        try:
            self.__logQueue.put_nowait(logC)
        except Exception as full:
            logger.warning('log queue full', exc_info=True)

    def __log_update(self, logC):
        try:
            req = requests.post(url='%s/%s' % (self.__httpHost, 'log/'), json=logC.form_dict(), timeout=(1.5, 1.5))
            if req.status_code != 200:
                logger.error('status:%s', req.status_code)
        except requests.exceptions.ReadTimeout as ex:
            logger.error('log update ReadTimeout')
        except requests.exceptions.ConnectTimeout as ex:
            logger.error('log update read timeout')
        except Exception as ex:
            logger.error(u"日志上报失败", exc_info=True)
