#!coding:utf8

# from app_deamon import Client
# Client().run(__file__)

import json
import sys
import signal
sys.path.append("..")
try:
    # sudo python iotosEngine.py --u demo --p demo123456 --i d9bf4696bfaf11eb9a9f000c2988ff06
    reload(sys)
    sys.setdefaultencoding('utf-8')
except:
    pass
import time
from iotos import *

import argparse

parser = argparse.ArgumentParser(description='')
# 用户名
parser.add_argument('--u', type=str, default=None)
# 密码
parser.add_argument('--p', type=str, default=None)
# 网关uuid
parser.add_argument('--i', type=str, default=None)

# supervisord名称
parser.add_argument('--s', type=str, default=None)

# 服务器地址
try:
    parser.add_argument('--h', type=str, default=HTTP_HOST)
except:
    parser.add_argument('--h', type=str, default='http://sys.iotos.net.cn')
args = parser.parse_args()

username = args.u
password = args.p
uuid = args.i
host = args.h
s_name = args.s

# uuid = '383d5beeb41011e8af620242ac110002'
# devId = 'd81bc7aa'
# dataId = 'ba7a'
# point = uuid + '.' + devId + '.' + dataId
# points = [{'id':point,'value':124}]

# username,password,uuid = "huaihua", "123456", "5a9c961e32fe11eaaffe000c2988ff06"
import psutil
zm = IOTOSys()
zm.http_host = host
try:
    login = zm.Login(username, password, uuid, True, s_name, host)
    logging.debug(login)
    dataRet = json.loads(login)
except Exception as e:
    traceback.print_exc()
    logger.error("启动异常")
    import signal

    while True:
        try:
            os.kill(os.getpid(), signal.SIGKILL)
            break
        except AttributeError:
            sys.exit(-1)
        except:
            traceback.print_exc()

if dataRet['code'] != 0:
    # 重新登录前，需要先主动调用退出登录，避免服务器session信息不释放
    zm.Logout()
    if dataRet['msg'] == 'AccountNotRegister':
        time.sleep(99999999999)
    elif dataRet['msg'] == 'IONodeNotExist':
        # 这里pass，python进程会退出，从而直接让守护进程把当前驱动进程拉起来，从头开始，所以跟直接调用zm.exit_to_reboot()效果完全一样！
        # 这里当不存在点表，那么1小时候才重启，避免一些僵尸驱动（账号下网关已经删除了，但是驱动没有同步删除，导致不停加载重启）
        time.sleep(60 * 60)
    else:
        # 普通非点表不存在错误，延时5s自动重启，避免一些错误立即重复，导致反复登录，导致登录资源被占用消耗
        time.sleep(10)
        zm.exit_to_reboot()
else:
    zm.engineRun()

# zm.DevOnline([uuid + '.' + devId])
# time.sleep(8)
# # zm.DevOffline([uuid + '.' + devId])
# print zm.Logout()


# print zm.PubMsg(point,5.232)


# from sympy import *
# print solve(y * 3 - 6, y)
#
# y=Symbol('x * 2')


# logout = zm.Logout()
# print logout,222222222

# # 已验证
# valtmp = {dataId : 998}
# sendmsg = zm.SendMsg(uuid,json.dumps(valtmp))
# print 'sendmsg ======>>>>> ',sendmsg

# # 已验证
# DevOnline = zm.DevOnline([uuid + '.' + devId])
# JLib().debug(DevOnline)

# # 已验证
# DevOffine = zm.DevOffine(points)
# print DevOffine,5555555555

# # 已验证
# GetPlatformData = zm.GetPlatformData(point)
# JLib().debug(GetPlatformData)

# # 已验证
# GetDeviceData = zm.GetDeviceData(point)
# print "GetDeviceData ===========>>>",GetDeviceData

# 已验证
# SubMsg = zm.SubMsg(['7832cbf0-466e-11e7-9107-000c2977d5f6.7a502a16.b0e3e7e2'])
# pirnt SubMsg

# # 已验证
# PubMsg = zm.PubMsg(point, True)
# JLib().debug(PubMsg)


# import pty
# import os
# import select
#
# def mkpty():
#     #打开伪终端
#     master1, slave = pty.openpty()
#     slaveName1 = os.ttyname(slave)
#
#     master2, slave = pty.openpty()
#     slaveName2 = os.ttyname(slave)
#
#     print '\nslavedevice names: ', slaveName1, slaveName2
#     return master1, master2
#
# if __name__ == "__main__":
#
#     master1, master2 = mkpty()
#     while True:
#         rl, wl, el = select.select([master1,master2], [], [], 1)
#         for master in rl:
#             data = os.read(master, 128)
#             print "read %d data." % len(data)
#             if master==master1:
#                 os.write(master2, data)
#             else:
#                 os.write(master1, data)


# # 已验证
# PubMsgs = zm.PubMsgs(points)
# print PubMsgs


# text = json.dumps(text)
# # # 已验证
# # engineInit = zm.engineInit(text)

# zm.engineRun()
# time.sleep(3)
# sendmsg = zm.SendMsg('377ee948-7b59-11e7-bc9f-000c2977d5f6','aaa')

# count = zm.count()
# print count,2222222222222

# print zm.m_devlist
# [u'377ee948-7b59-11e7-bc9f-000c2977d5f6.d9c05ecb', u'377ee948-7b59-11e7-bc9f-000c2977d5f6.8ee79805']

# print zm.m_dev2attrs
# {u'377ee948-7b59-11e7-bc9f-000c2977d5f6.d9c05ecb': {u'timestamp': 1502437422.321, u'config': {u'type': u'serialport', u'param': {u'parity': u'N', u'baudrate': u'9600', u'byteSize': 8, u'xonxoff': 0, u'stopbits': 1, u'port': u'COM1'}, u'parentId': u''}, u'description': u'', u'name': u'agv_01'}, u'377ee948-7b59-11e7-bc9f-000c2977d5f6.8ee79805': {u'timestamp': 1502437422.214, u'config': {'param': {u'parity': u'N', u'baudrate': u'9600', u'byteSize': 8, u'xonxoff': 0, u'stopbits': 1, u'port': u'COM1'}, u'parentId': u'd9c05ecb'}, u'description': u'', u'name': u'agv_02'}}

# print zm.m_dev2points
# {u'377ee948-7b59-11e7-bc9f-000c2977d5f6.d9c05ecb': [u'377ee948-7b59-11e7-bc9f-000c2977d5f6.d9c05ecb.e513dee0', u'377ee948-7b59-11e7-bc9f-000c2977d5f6.d9c05ecb.e5132311', u'377ee948-7b59-11e7-bc9f-000c2977d5f6.d9c05ecb.8637dec2', u'377ee948-7b59-11e7-bc9f-000c2977d5f6.d9c05ecb.8637dec3'], u'377ee948-7b59-11e7-bc9f-000c2977d5f6.8ee79805': [u'377ee948-7b59-11e7-bc9f-000c2977d5f6.8ee79805.55f37d1e']}


# print zm.m_point2attrs
# {u'377ee948-7b59-11e7-bc9f-000c2977d5f6.d9c05ecb.e5132311': {u'description': u'\u53c2\u6570\u63cf\u8ff0', u'readwrite': u'0', u'timestamp': 1502438647.763, u'defaultvalue': u'', u'maxvalue': u'', u'minvalue': u'', u'refreshcycle': 10, u'regexp': u'', u'sensibility': u'', u'config': {u'type': u'modbus_rtu', u'param': {u'regad2': 8, u'devid12': 2, u'funid23': 3}, u'parentId': u''}, u'valuetype': u'BOOL', u'unit': u'', u'name': u'params'}, u'377ee948-7b59-11e7-bc9f-000c2977d5f6.d9c05ecb.8637dec3': {u'description': u'', u'readwrite': u'1', u'timestamp': 1502438647.763, u'defaultvalue': u'', u'maxvalue': u'', u'minvalue': u'', u'refreshcycle': 1000, u'regexp': u'', u'sensibility': u'', u'config': {u'param': {u'regad2': 8912, u'devid12': 2, u'funid': 3, u'devid': 2, u'regad': 900, u'funid23': 3, u'test': 10010}, u'parentId': u'8637dec2'}, u'valuetype': u'BOOL', u'unit': u'', u'name': u'params2'}, u'377ee948-7b59-11e7-bc9f-000c2977d5f6.d9c05ecb.8637dec2': {u'description': u'', u'readwrite': u'1', u'timestamp': 1502438647.763, u'defaultvalue': u'', u'maxvalue': u'', u'minvalue': u'', u'refreshcycle': 1000, u'regexp': u'', u'sensibility': u'', u'config': {u'param': {u'regad2': 8, u'devid12': 2, u'funid': 3, u'devid': 2, u'regad': 9, u'funid23': 3}, u'parentId': u'e513dee0'}, u'valuetype': u'BOOL', u'unit': u'', u'name': u'params2'}, u'377ee948-7b59-11e7-bc9f-000c2977d5f6.8ee79805.55f37d1e': {u'description': u'\u63cf\u8ff0xxx', u'readwrite': u'2', u'timestamp': 1502438647.763, u'defaultvalue': u'', u'maxvalue': u'', u'minvalue': u'', u'refreshcycle': 300, u'regexp': u'', u'sensibility': u'', u'config': {u'type': u'modbus_rtu', u'param': {u'regad': 0, u'funid': 2, u'devid': 1}, u'parentId': u''}, u'valuetype': u'INT', u'unit': u'', u'name': u'params'}, u'377ee948-7b59-11e7-bc9f-000c2977d5f6.d9c05ecb.e513dee0': {u'description': u'\u53c2\u6570\u63cf\u8ff0', u'readwrite': u'0', u'timestamp': 1502438647.763, u'defaultvalue': u'', u'maxvalue': u'', u'minvalue': u'', u'refreshcycle': 10, u'regexp': u'', u'sensibility': u'', u'config': {u'type': u'modbus_rtu', u'param': {u'regad2': 8, u'devid12': 2, u'funid': 3, u'devid': 2, u'regad': 4, u'funid23': 3}, u'parentId': u'e5132311'}, u'valuetype': u'BOOL', u'unit': u'', u'name': u'params'}}


# print zm.RunCollecting()


# import OpenOPC
#
# opc_server = 'DSxPOpcSimulator.TSxOpcSimulator.1'
# opc_host='127.0.0.1'
#
# opc = OpenOPC.client()
# print opc.servers() 	 											# 列出本机中所有opc server清单
# # [u'DSxPOpcSimulator.TSxOpcSimulator.1']  							# 返回的，opc server名称
# opc.connect(opc_server)  									# 从opc server清单中选择需要连接的服务
# print opc.write(('Simulation Items.String.Str_03','hello world!'))
# while True:
# 	print opc.read('Simulation Items.String.Str_03', sync=True)
# 	time.sleep(1)


# import time
# import modbus_tk
# import modbus_tk.defines as cst
# import modbus_tk.modbus as modbus
# import modbus_tk.modbus_rtu as modbus_rtu
# import serial
#
# serial = serial.Serial(port='COM4', baudrate=9600, bytesize=8, parity='N', stopbits=1, xonxoff=0)
# master = modbus_rtu.RtuMaster(serial)
# master.set_timeout(10.0)
# master.set_verbose(True)
#
# rtu_ret = master.execute(4, cst.READ_HOLDING_REGISTERS, 32, 16)
# print 'rtu_ret', len(rtu_ret), rtu_ret
