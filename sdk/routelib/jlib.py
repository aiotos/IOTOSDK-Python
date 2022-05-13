# coding=utf-8


import time
import struct
import sys
import json
import traceback

import logging
from logging.handlers import TimedRotatingFileHandler
from logging.handlers import RotatingFileHandler

import re
from library.iotos_util import sdk_logger as logger

# 心跳维持
class JLib(object):
    def __init__(self):
        self.logger = logger
        #日志交给supervisor守护进程来做，他可以设置日志文件大小参数，以及日志文件个数，自动清理，并且可以通过通过web来查看滚动日志！
        # # 创建TimedRotatingFileHandler对象
        # rht = TimedRotatingFileHandler(filename="./iotos.log", when="D", interval=1, backupCount=7)
        # rht.suffix = "% Y - % m - % d_ % H - % M.log"
        # rht.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}.log$")
        # # fmt = logging.Formatter("%(asctime)s %(pathname)s %(filename)s %(funcName)s %(lineno)s %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
        # self.logger.addHandler(rht)

        #no print???? edit by lrq 220513
        # self.debug = self.logger.debug
        # self.info = self.logger.info
        # self.warn = self.logger.warn
        # self.error = self.logger.error
        # self.critical = self.logger.critical
        # self.exception = self.logger.exception

        # replace by:
        self.debug = logging.debug
        self.info = logging.info
        self.warn = logging.warn
        self.error = logging.error
        self.critical = logging.critical
        self.exception = logging.exception

    def str2hex(self,s):
        return ' '.join([hex(ord(c)).replace('0x', '') for c in s])

    def hex2str(self,s):
        return ''.join([chr(i) for i in [int(b, 16) for b in s.split(' ')]])

    def str2bin(self,s):
        return ' '.join([bin(ord(c)).replace('0b', '') for c in s])

    def bin2str(self,s):
        return ''.join([chr(i) for i in [int(b, 2) for b in s.split(' ')]])

    def pack(self,expression,data):
        return struct.pack(expression,data)[0]

    def unpack(self,expression,data):
        if type(data) is int:
            data = data.to_bytes(length=1, byteorder='big')
        return struct.unpack(expression,data)[0]

    def unpackByte(self,bt):
        return struct.unpack('B',bt)[0]

    def errlog(self,dt):
        try:
            jsobj = json.loads(dt)
            if jsobj and jsobj['code'] != 0:
                traceback.print_exc(jsobj['msg'])
        except Exception as e:
            pass

    def print_hex(self,out):
        print(out.hex())
        #print(''.join(format(x, ' 02x') for x in out))

    def flags_extract(self,data,beginFlag,endFlag):
        ex = self.FlagsExtract()
        return ex.extract(data,beginFlag,endFlag)

    class FlagsExtract():
        def __init__(self):
            self.__beforeLeft = bytearray()
            self.__nextLeft = bytearray()
            self.__packagelist = []
            self.__data = None
            self.__flagBegin = None,
            self.__flagEnd = None

        def extract(self,data,flagBegin,flagEnd):
            self.__data = data
            self.__flagBegin = flagBegin
            self.__flagEnd = flagEnd
            self.__parser(data,flagBegin,flagEnd)
            return (self.__beforeLeft,self.__packagelist,self.__nextLeft)

        def __append_and_check(self,data):
            innerdatatmp = data[1:len(data) - 1]
            assert innerdatatmp.find(self.__flagBegin) == -1 and innerdatatmp.find(self.__flagEnd) == -1
            self.__packagelist.append(data)

        def __parser(self,data,flagBegin,flagEnd):
            beginIndex = data.find(flagBegin)
            endIndex = data.find(flagEnd)

            #既没有头标记也没有尾标记，那么久放到前一次遗留中
            if beginIndex == -1 and endIndex == -1:
                self.__beforeLeft = data
                return

            #没有找到当头标记时，不管后面有没末尾标记，整个数据都当作是上次开始未结束的!!!!???
            if beginIndex == -1:
                #头都找不到，那么要么也不存在尾标记，要么尾标记就在末尾！
                assert endIndex == len(data) - 1
                self.__beforeLeft = data
                return
            #当找不到末尾了，那么要么也找不到起始标记，如果有，一定是在当头
            if endIndex == -1:
                assert beginIndex == 0
                self.__nextLeft = data
                return

            #到这里，那么必然包头和包尾都存在！
            #包头存在，且不是第一个字节时，包头前面的部分存到前剩余里
            #包头和包尾是紧挨着的，所以包头前面一个必然是上一个包的包尾
            realEndIndex = 0
            if beginIndex == 0:
                #这个时候存在的结束标记肯定不会再开始标记之前！
                self.__append_and_check(data[beginIndex:endIndex + 1])
                realEndIndex = endIndex
            else:
                #如果结束标记只有一个
                self.__beforeLeft = data[:beginIndex]
                if data.count(flagEnd) == 1:
                    assert data[beginIndex -1] == flagEnd
                    self.__nextLeft = data[beginIndex:]
                    return
                else:
                    #如果不止一个结束标记，那么就用第二个，且第二个的索引必然在开始标记之后!
                    itmp = data.find(flagEnd)
                    #其中第一个标记一定是在起始标记前一位
                    assert itmp == beginIndex -1
                    itmp2 = data[itmp + 1:].find(flagEnd)
                    realEndIndex = itmp + itmp2 + 1
                    assert realEndIndex > beginIndex
                    self.__append_and_check(data[beginIndex:realEndIndex + 1])
            if realEndIndex != len(data) - 1:
                assert data[realEndIndex + 1] == flagBegin
                self.__parser(data[realEndIndex + 1:],flagBegin,flagEnd)


if __name__ == '__main__':
    dt = bytearray([0x31,0x32,0x44,0x41,0x41,0x45,0x43,0x41,0x51,0x59,0x41])
    j = JLib()
    rt = j.flags_extract(dt,0x02,0x03)
    print(rt)
