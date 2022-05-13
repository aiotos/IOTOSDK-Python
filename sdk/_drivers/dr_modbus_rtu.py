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
import re
import struct
import math

#硬件心跳线程
class RunHardwareHeartbeatThread(threading.Thread,JLib):
    def __init__(self, driver):
        threading.Thread.__init__(self)
        JLib.__init__(self)
        self.driver = driver
    def run(self):
        statetmp = False
        dataIdTmp = ''
        recycletmp = 0
        for dataId,attrs in self.driver.data2attrs.items():
            if 'param' not in attrs['config']:
                self.error(attrs['config'])
                break
            if 'hbt' in attrs['config']['param']:
                dataIdTmp = dataId
                recycletmp = attrs['config']['param']['hbt']
                break
        while True:
            try:
                if not self.driver.startHeartbeat:
                    return

                #状态反转及延时
                if statetmp == False:
                    statetmp = True
                else:
                    statetmp = False
                time.sleep(recycletmp)

                # self.warn('HARDWARE HEATBEAT ' + dataIdTmp + u'硬件心跳：' + str(statetmp))
                #控制执行
                rettmp = ''
                if statetmp:
                    rettmp = self.driver.Event_setData(dataIdTmp,'true')
                else:
                    rettmp = self.driver.Event_setData(dataIdTmp,'false')
                if json.loads(rettmp)["code"] == 0:
                    self.driver.setValue(self.driver.name(dataIdTmp), statetmp)
            except Exception,e:
                traceback.print_exc(e.message)
                continue

class ModbusDriver(IOTOSDriverI):
    def __init__(self):
        IOTOSDriverI.__init__(self)
        self.master = None
        # 心跳开关
        self.startHeartbeat = False
        self.bitsState = [0,0,0,0,0,0,0,0]
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

            #三、串口1 <=> modbus_tk
            self.master = modbus_rtu.RtuMaster(self.__serial.serial)
            self.master.set_timeout(5)
            self.master.set_verbose(False)
            self.debug(self.sysAttrs['name'] + u' 串口' + self.__serial.portName() + u'已打开！')

            self.zm.pauseCollect = True
            # 实例化硬件心跳线程
            RunHardwareHeartbeatThread(self).start()

        except Exception,e:
            self.online(False)
            traceback.print_exc(u'通信初始化失败' + e.message)

    #四、串口2 <=> tcp
    #tcp => 串口2
    def tcpCallback(self,data):
        datastr = self.str2hex(data)
        self.sourceDataIn = data
        self.info("Master < < < < < < Device: " + datastr)
        self.__serial.send(data)
        # if datastr[0] == '1' or datastr[0] == '2' or datastr[0] == '7':
        #     # self.__serial.send(data)
        #     pass
        # else:
        #     self.warn(u'modbus设备地址位为1、2以外的都作为非法数据，返回数将忽略.' + str(datastr[0]))

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
                self.pauseCollect = False
                #启动软件看门狗
                self.startHeartbeat = True
            else:
                self.warn('连接断开，将关闭采集和心跳！')
                self.startHeartbeat = False
                self.pauseCollect = True
        except Exception,e:
            self.error(u'硬件心跳错误, ' + e.message)

    # 2、采集
    def Collecting(self, dataId):
        try:
            rtu_ret = ()
            cfgtmp = self.data2attrs[dataId]['config']

            #added by lrq，过滤非modbus rtu配置的点
            if not cfgtmp.has_key('param') or not cfgtmp.has_key('proxy'):
                return ()

            #当是新一组功能号时；当没有proxy.pointer，或者有，但是值为null时，就进行采集！否则（有pointer且值不为null，表明设置了采集代理，那么自己自然就被略过了，因为被代理了）当前数据点遍历轮询会被略过！
            if 'pointer' not in cfgtmp['proxy'] or cfgtmp['proxy']['pointer'] == None or cfgtmp['proxy']['pointer'] == '':

                #added by lrq，某些过滤掉不采集，因为有的地址的设备不在线，只要在proxy下面配置disabled:true，这样就不会轮训到它！
                if 'disabled' in cfgtmp['proxy'] and cfgtmp['proxy']['disabled'] == True:
                    return ()
                else:
                    self.warn(self.name(dataId))

                # added by lrq，过滤非modbus rtu配置的点
                if not cfgtmp['param'].has_key('funid'):
                    return ()

                funid = cfgtmp['param']['funid']
                devid = cfgtmp['param']['devid']
                regad = cfgtmp['param']['regad']
                format = cfgtmp['param']['format']
                quantity = re.findall(r"\d+\.?\d*", format)
                if len(quantity):
                    quantity = int(quantity[0])
                else:
                    quantity = 1
                if format.lower().find('i') != -1:       #I、i类型数据为4个字节，所以n个数据，就是4n字节，除一般应对modbus标准协议的2字节一个数据的个数单位！
                    quantity *= 4/2
                elif format.lower().find('h') != -1:
                    quantity *= 2/2
                elif format.lower().find('b') != -1:
                    quantity *= 1/2
                elif format.find('d') != -1:
                    quantity *= 8/2
                elif format.find('f') != -1:
                    quantity *= 4/2
                elif format.find('?') != -1:           #对于功能号1、2的开关量读，开关个数，对于这种bool开关型，个数就不是返回字节数的两倍了！返回的字节个数是动态的，要字节数对应的位数总和，能覆盖传入的个数数值！
                    quantity *= 1
                    format = ''                        #实践发现，对于bool开关型，传入开关量个数就行，format保留为空！如果format设置为 "?"或"8?"、">?"等，都会解析不正确！！
                self.debug('>>>>>>' + '(PORT-' + str(self.__port) + ')' + str(devid) + ' ' + str(funid) + ' ' + str(regad) + ' ' + str(quantity) + ' ' + str(format))
                rtu_ret = self.master.execute(devid, funid, regad, quantity,data_format=format)

                #added by lrq 20200116 私有modbus解析支持，煤矸石项目
                if cfgtmp['param'].has_key('private'):
                    #1、煤矸石项目modbus私有解析
                    if cfgtmp['param']['private'] == 'wendu_meiganshi_zhenzhou':
                        bytestmp = self.sourceDataIn[3:-2]
                        listtmp = []
                        for i in range(len(bytestmp) / 8):
                            datatmp = bytestmp[i*8 + 4 : i*8 + 6]
                            valueParserTmp = struct.unpack('>h', datatmp)[0] / 10.0
                            if valueParserTmp < -300:       #added by lrq，对于掉线情况下，默认会给一个负几千的值，这个会记录到数据库，
                                                            # 不利于历史曲线对比分析，所以转换成一个差别不是特别大的负数，而且是场景不会发生的，替代这个大的负值，让曲线整体的波动有辨识度！
                                valueParserTmp = -50
                            listtmp.append(valueParserTmp)
                        rtu_ret = tuple(listtmp)
                        self.warn(rtu_ret)
                    #2、煤矸石项目气体-温度独立模块测试
                    if cfgtmp['param']['private'] == 'separated_test':
                        bytestmp = self.sourceDataIn[3:-2]
                        listtmp = []
                        for i in range(len(bytestmp) / 4):  #4个字节一个数据，前两字节是整数，后两字节是小数点位数（1，那么整数/10;2，那么整数/100）
                            valueParserTmp = struct.unpack('>h', bytestmp[i * 4: i * 4 + 2])[0]     #前面两字节
                            valueDecCountsTmp = struct.unpack('>h', bytestmp[i * 4 + 2: i * 4 + 4])[0]  #后面两字节
                            self.debug('val head: ' + str(valueParserTmp) + '; val tail: ' + str(valueDecCountsTmp))
                            listtmp.append(valueParserTmp * 1.0 / math.pow(10,valueDecCountsTmp))
                        rtu_ret = tuple(listtmp)
                        self.warn(rtu_ret)

                    #3、added by lrq 20200904 液体ph值传感温度解析，4字节的浮点数数据比如ABCD，低两位与高两位替换：CDAB，然后再参与浮点数格式的4字节计算！
                    if cfgtmp['param']['private'] == 'lowDoubleByteExchange':
                        h_bytes = self.sourceDataIn[3:5]                        #python字节下标切片[a:b]，那么是从索引a开始（包括），一直到下标为b（不包括）为止！所以这里3:5，那么就是下标为3、4两个字节！
                        l_bytes = self.sourceDataIn[5:7]
                        new_bytes = l_bytes + h_bytes                           #字节直接合并
                        self.warn(self.str2hex(h_bytes))
                        self.warn(self.str2hex(l_bytes))
                        self.warn(self.str2hex(new_bytes))
                        rtu_ret = tuple([struct.unpack('>f', new_bytes)[0]])    #只返回一个数据时，需要tuple([val])，来实现单个数据的Collecting返回！



                    #4、遥感测距距离模块测试
                    if cfgtmp['param']['private'] == 'distancetest' :
                        self.info('data>>>>>>>>>>>' + self.str2hex(self.sourceDataIn))
                        bytes_tmp = self.sourceDataIn[3:7]
                        tmptur = struct.unpack('>i', bytes_tmp)[0]  # 一共四个字节，打包起来16进制数乘以0.1
                        value_new = tmptur * 0.1
                        self.info("float info >>>>>>>>>>>>" + str(value_new))
                        rtu_ret = tuple([value_new])    #只返回一个数据时，需要tuple([val])，来实现单个数据的Collecting返回！

                    if cfgtmp['param']['private'] == 'gas':
                        self.info('data>>>>>>>>>>>' + str(self.sourceDataIn))
                        bytes_tmp = self.sourceDataIn[3:]
                        tes = struct.unpack('>h', bytes_tmp)[0]
                        self.info("float info >>>>>>>>>>>>" + str(tes))
                        rtu_ret = tuple([tes])    #只返回一个数据时，需要tuple([val])，来实现单个数据的Collecting返回！



                else:
                    if funid == 3:
                        retlist = []
                        for i in range(len(rtu_ret)):
                            retlist.append(rtu_ret[i])
                        rtu_ret = tuple(retlist)

                #周期查询的开关量输出状态进行备份，用来给控制用
                if funid == 1:
                    self.bitsState = list(rtu_ret)
                self.debug(rtu_ret)
                return rtu_ret
            # 一组功能号内的数据点，不进行遍历采集！跳过！
            else:
                return ()   #注意，这种情况下不是采集错误，如果返回None，那么会当作采集错误处理，进行采集错误计数了！！
        except ModbusInvalidResponseError, e:
            self.error(u'MODBUS响应超时, ' + e.message)
            return None
        except Exception, e:
            traceback.print_exc(e.message)
            self.error(u'采集解析参数错误：' + e.message)
            return None

    # 3、控制 数据点配置
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
        self.warn(value)
        try:
            if self.master == None:
                self.InitComm()
            data_config = self.data2attrs[dataId]['config']
            bit = 0
            if 'proxy' in data_config.keys() and 'pointer' in data_config['proxy'] and data_config['proxy']['pointer'] != None:
                bit = data_config['proxy']['index']
            if self.valueTyped(dataId,value) == True:
                self.bitsState[bit] = 1
            else:
                self.bitsState[bit] = 0
            self.warn(self.bitsState)

            #注意，这里地址是1，但是再huaihua等用了3合一设备的，地址是2，接下来需要这里也做个区分，按照当前操作的数据点对应的实际数据点来！
            ret = self.master.execute(1, cst.WRITE_MULTIPLE_COILS, 0, output_value=self.bitsState)
            self.warn(ret)
            return json.dumps({'code': 0, 'msg': u'操作成功！', 'data': list(ret)})
        except Exception,e:
            return json.dumps({'code': 501, 'msg': u'操作失败，错误码501，' + e.message, 'data': None})

    # 事件回调接口，监测点操作访问
    def Event_syncPubMsg(self, point, value):
        '''*************************************************

		TODO 

		**************************************************'''
        return json.dumps({'code': 0, 'msg': '', 'data': ''})