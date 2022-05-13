#!coding:utf8
import json
import sys

sys.path.append("..")
from driver import *

import time
import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus as modbus
import modbus_tk.modbus_rtu as modbus_rtu
from modbus_tk.exceptions import ModbusInvalidResponseError
import serial
import signal
import traceback
from jcomm import *
from jcomm import TcpServerThread
import re
import struct

class ModbusDriver(IOTOSDriverI):
    def __init__(self):
        IOTOSDriverI.__init__(self)
        self.master = None
        self.bitsState = [0,0,0,0,0,0,0,0]

    # 1、通信初始化
    def InitComm(self, attrs = None):
        try:
            #一、tcp端口监听
            self.__port = self.sysAttrs['config']['param']['tcp']
            self.__tcpServer = TcpServerThread(self,self.__port)
            self.__tcpServer.setDaemon(True)
            self.__tcpServer.start()
            self.info(self.sysAttrs['name'] + u' TCP端口' + str(self.__port) + u"已启动监听！")
            self.zm.pause_collect = True

        except Exception,e:
            self.online(False)
            traceback.print_exc(u'通信初始化失败' + e.message)

    def tcpCallback(self,data):
        datastr = self.str2hex(data)
        self.info("Master < < < < < < Device: " + datastr)
        self.debug(struct.unpack('B',data[11])[0])
        if len(data) >= 17 and struct.unpack('B',data[12])[0] == 3:      #modbus设备地址1，功能号3
            valuetmp = (struct.unpack('B', data[14])[0] * 256 + struct.unpack('B', data[15])[0]) / 10.0
            for dataId, attrs in self.data2attrs.items():
                try:
                    if attrs['config']['param'].has_key('devid') and attrs['config']['param']['devid'] == struct.unpack('B',data[11])[0]:
                        self.setValue(self.name(dataId), valuetmp)
                        self.info(valuetmp)
                        break
                except Exception, e:
                    traceback.print_exc(u'忽略异常数据：' + dataId)
        else:
            self.warn(u'忽略非业务数据！')

    #tcp <= 串口2
    def serialCallback(self,data):
        self.info("Master > > > > > > Device: " + self.str2hex(data))
        self.__tcpServer.send(data)

    #连接状态回调
    def connectEvent(self,state):
        self.online(state)
        try:
            if state == True:
                self.warn('连接成功，启动采集、心跳')
                self.zm.pause_collect = False
            else:
                self.warn('连接断开，将关闭采集和心跳！')
                self.startHeartbeat = False
        except Exception,e:
            self.error(u'硬件心跳错误, ' + e.message)

    # 2、采集
    def Collecting(self, dataId):
        time.sleep(999999)
        return ()

    # 3、控制
    # 事件回调接口，其他操作访问
    def Event_customBroadcast(self, fromUuid, type, data):
        '''*************************************************

		TODO 

		**************************************************'''
        return json.dumps({'code': 0, 'msg': '', 'data': ''})


    # # 事件回调接口，监测点操作访问
    # def Event_getData(self, dataId, condition=''):
    #     return json.dumps({'code': 0, 'msg': '', 'data': ''})

    # # 事件回调接口，监测点操作访问
    # def Event_setData(self, dataId, value):
    #     return json.dumps({'code': 0, 'msg': u'操作成功！', 'data': list()})


    # 事件回调接口，监测点操作访问
    def Event_syncPubMsg(self, point, value):
        '''*************************************************

		TODO 

		**************************************************'''
        return json.dumps({'code': 0, 'msg': '', 'data': ''})