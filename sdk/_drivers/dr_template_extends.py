#!coding:utf8
import json
import sys

sys.path.append("..")
from driver import *

import time
import serial
import signal
import traceback
from jcomm import *
import re
import struct
import math

class ModbusDriver(IOTOSDriverI):
    def __init__(self):
        IOTOSDriverI.__init__(self)
        self.sourceDataIn = []

    # 1、通信初始化
    def InitComm(self, attrs = None):
        try:
            #一、tcp端口监听
            self.__port = self.sysAttrs['config']['param']['tcp']
            self.__tcpServer = TcpServerThread(self,self.__port)
            self.__tcpServer.setDaemon(True)
            self.__tcpServer.start()
            self.debug(self.sysAttrs['name'] + u' TCP端口' + str(self.__port) + u"已启动监听！")

            #二、创建串口1 <=> 串口2
            serialtmp = self.sysAttrs['config']['param']['serial']
            self.__serial = SerialDtu(serialtmp)
            self.__serial.setCallback(self.serialCallback)
            self.__serial.open()

            self.zm.pause_collect = True

        except Exception,e:
            self.online(false)
            traceback.print_exc(u'通信初始化失败' + e.message)

    #四、串口2 <=> tcp
    #tcp => 串口2
    def tcpCallback(self,data):
        datastr = self.str2hex(data)
        self.sourceDataIn = data
        self.info("Master < < < < < < Device: " + datastr)
        self.__serial.send(data)

    #tcp <= 串口2
    def serialCallback(self,data):
        self.info("Master > > > > > > Device: " + self.str2hex(data))
        self.__tcpServer.send(data)

    #连接状态回调
    def connectEvent(self,state):
        self.online(state)
        try:
            if state == True:
                self.warn('连接成功，启动采集')
                self.zm.pause_collect = False
            else:
                self.warn('连接断开，将关闭采集！')
                self.zm.pause_collect = True
        except Exception,e:
            self.error(u'硬件心跳错误, ' + e.message)

    # 2、采集
    def Collecting(self, dataId):
        try:
            return ()   #注意，这种情况下不是采集错误，如果返回None，那么会当作采集错误处理，进行采集错误计数了！！
        except ModbusInvalidResponseError, e:
            self.error(u'MODBUS响应超时, ' + e.message)
            return None
        except Exception, e:
            traceback.print_exc(e.message)
            self.error(u'采集解析参数错误：' + e.message)
            return None

    # 3、控制
    # 事件回调接口，其他操作访问
    def Event_customBroadcast(self, fromUuid, type, data):
        '''************************************************* 

		TODO   

		**************************************************'''
        return json.dumps({'code': 0, 'msg': '', 'data': ''})

    # 事件回调接口，监测点操作访问
    def Event_getData(self, dataId, condition=''):


        return json.dumps({'code': 0, 'msg': '', 'data': new_val})

    # 事件回调接口，监测点操作访问
    def Event_setData(self, dataId, value):
        try:
            return json.dumps({'code': 0, 'msg': u'操作成功！', 'data': list(ret)})
        except Exception,e:
            return json.dumps({'code': 501, 'msg': u'操作失败，错误码501，' + e.message, 'data': None})

    # 事件回调接口，监测点操作访问
    def Event_syncPubMsg(self, point, value):
        '''*************************************************

		TODO 

		**************************************************'''
        return json.dumps({'code': 0, 'msg': '', 'data': ''})