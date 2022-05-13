# -*- coding:utf-8 -*-
# author : jiji time 12/10/2021
# Modbus tcp server
import sys
import modbus_tk.modbus_tcp as modbus_tcp
from modbus_tk.exceptions import ModbusInvalidResponseError
reload(sys)
sys.setdefaultencoding('utf8')

sys.path.append("..")
from driver import *

# 补码转为负数
def Complement2Negative(int_data):
    data = '0b'
    bin_data = bin(int_data).split('0b')[1]
    print bin(int_data)
    if len(bin_data) < 16:
        return int_data
    else:
        for i in bin_data:
            if i == '1':
                data += '0'
            if i == '0':
                data += '1'
        return (int(data,2)+1)*-1

class ModbusTCPDriver(IOTOSDriverI):
    #1、通信初始化
    def InitComm(self,attrs):

        self._HOST = self.sysAttrs['config']['param']['HOST']
        self._PORT = self.sysAttrs['config']['param']['PORT']
        self._master = modbus_tcp.TcpMaster(host=self._HOST, port=int(self._PORT))
        self._master.set_timeout(5.0)
        self.setPauseCollect(False)
        self.setCollectingOneCircle(False)
        self.online(True)

    # #2、采集引擎回调，可也可以开启，也可以直接注释掉（对于主动上报，不存在遍历采集的情况）
    def Collecting(self, dataId):
        try:
            cfgtmp = self.data2attrs[dataId]['config']
            # 过滤非modbus tcp配置的点
            if not cfgtmp.has_key('param') or not cfgtmp.has_key('proxy'):
                return ()

            # 当是新一组功能号时；当没有proxy.pointer，或者有，但是值为null时，就进行采集！否则（有pointer且值不为null，表明设置了采集代理，那么自己自然就被略过了，因为被代理了）当前数据点遍历轮询会被略过！
            if 'pointer' not in cfgtmp['proxy'] or cfgtmp['proxy']['pointer'] == None or cfgtmp['proxy']['pointer'] == '':
                # 某些过滤掉不采集，因为有的地址的设备不在线，只要在proxy下面配置disabled:true，这样就不会轮训到它！
                if 'disabled' in cfgtmp['proxy'] and cfgtmp['proxy']['disabled'] == True:
                    return ()
                else:
                    self.warn(self.name(dataId))

            # 过滤非modbus rtu配置的点
            if not cfgtmp['param'].has_key('funid'):
                return ()

            # 功能码
            funid = cfgtmp['param']['funid']
            # 设备地址
            devid = cfgtmp['param']['devid']
            # 寄存器地址
            regad = cfgtmp['param']['regad']
            # 格式
            format = cfgtmp['param']['format']
            # 长度
            quantity = re.findall(r"\d+\.?\d*", format)
            if len(quantity):
                quantity = int(quantity[0])
            else:
                quantity = 1
            if format.lower().find('i') != -1:  # I、i类型数据为4个字节，所以n个数据，就是4n字节，除一般应对modbus标准协议的2字节一个数据的个数单位！
                quantity *= 4 / 2
            elif format.lower().find('h') != -1:
                quantity *= 2 / 2
            elif format.lower().find('b') != -1:
                quantity *= 1 / 2
            elif format.find('d') != -1:
                quantity *= 8 / 2
            elif format.find('f') != -1:
                quantity *= 4 / 2
            elif format.find(
                    '?') != -1:  # 对于功能号1、2的开关量读，开关个数，对于这种bool开关型，个数就不是返回字节数的两倍了！返回的字节个数是动态的，要字节数对应的位数总和，能覆盖传入的个数数值！
                quantity *= 1
                format = ''  # 实践发现，对于bool开关型，传入开关量个数就行，format保留为空！如果format设置为 "?"或"8?"、">?"等，都会解析不正确！！
            self.debug(
                '>>>>>>' + '(PORT-' + str(self._PORT) + ')' + str(devid) + ' ' + str(funid) + ' ' + str(regad) + ' ' + str(
                    quantity) + ' ' + str(format))
            rtu_ret = self._master.execute(devid, funid, regad, quantity, data_format=format)
            self.debug(rtu_ret)

            # 私有modbus解析
            if cfgtmp['param'].has_key('private'):
                # 温湿度传感器
                if cfgtmp['param']['private'] == 'Temp&Hum':
                    data_list = []
                    for i in rtu_ret:
                        data_list.append(Complement2Negative(i)*0.1)
                    rtu_ret = tuple(data_list)

            return rtu_ret
        except ModbusInvalidResponseError, e:
            self.error(u'MODBUS响应超时, ' + e.message)
            return None
        except Exception, e:
            traceback.print_exc(e.message)
            self.error(u'采集解析参数错误：' + e.message)
            return None