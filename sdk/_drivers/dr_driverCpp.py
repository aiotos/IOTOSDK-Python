#!coding:utf8
import json
import sys
sys.path.append("..")
from driver import *
import threading
import random
from ctypes import *

import DriverCpp


class Driver(IOTOSDriverI):
	#1、通信初始化
	def InitComm(self,attrs):

		def timerProcess():
			valtmp = self.setValue('01f277fec35911eaa38e000c2988ff06.a009e9c9.04b7', random.randint(50, 100))		#gate_x.dev_a.篮球1
			print valtmp
			timertmp = threading.Timer(1, timerProcess)
			timertmp.start()

		timertmp = threading.Timer(1, timerProcess)
		# timertmp.start()

		# ------------------------测试接口作为回调，本地测试调用---------------------------
		# def callback1111(abc,d):
		# 	print "callback1111 say : {0}".format(abc),d
		# 	return "111111"
		# def callback2222(abc):
		# 	print "callback2222 say : {0}".format(abc)
		# 	return "222222"
		# CMPFUNC = CFUNCTYPE(c_char_p, c_char_p, c_char_p)
		# _callback1111 = CMPFUNC(callback1111)
		# CMPFUNC = CFUNCTYPE(c_char_p, c_char_p)
		# _callback2222 = CMPFUNC(callback2222)
		# DriverCpp.setCallback("callback1111",_callback1111)
		# DriverCpp.setCallback("callback2222",_callback2222)
		# self.warn(DriverCpp.testCallback('callback1111','abcd','hello234'))
		# self.warn(DriverCpp.testCallback('callback2222', 'hello,iotos'))

		# ------------------------实际驱动基类接口作为回调，本地测试调用---------------------------
		CMPFUNC = CFUNCTYPE(c_char_p, c_char_p)
		DriverCpp.setCallback("pointId", CMPFUNC(self.pointId))
		# self.warn(DriverCpp.testCallback('pointId','c5d7'))

		CMPFUNC = CFUNCTYPE(c_char_p, c_char_p)
		DriverCpp.setCallback("name",CMPFUNC(self.name))
		# self.warn(DriverCpp.testCallback('name', 'c5d7'))

		CMPFUNC = CFUNCTYPE(c_char_p, c_char_p)
		DriverCpp.setCallback("id",CMPFUNC(self.id))
		# self.warn(DriverCpp.testCallback('id', '液位4'))

		CMPFUNC = CFUNCTYPE(c_char_p, c_bool)
		DriverCpp.setCallback("online",CMPFUNC(self.online))
		# self.warn(DriverCpp.testCallback('online', True))

		CMPFUNC = CFUNCTYPE(c_char_p, c_char_p, c_char_p)
		DriverCpp.setCallback("setValue",CMPFUNC(self.setValue))
		# self.warn(DriverCpp.testCallback('setValue','输入2',"true"))

		#【待支持】20200809 c++ sdk暂不支持批量上报，需要完善这里
		# CMPFUNC = CFUNCTYPE(c_char_p, c_char_p)
		# DriverCpp.setCallback("setValues",CMPFUNC(self.setValues))
		# self.warn(DriverCpp.testCallback('setValues',{}))

		CMPFUNC = CFUNCTYPE(c_char_p, c_char_p, c_char_p, c_char_p)
		DriverCpp.setCallback("value",CMPFUNC(self.value_str_ret))
		# self.warn(DriverCpp.testCallback('value','输入2','','p'))
		# self.warn(self.value('液位3', '', 'p'))
		# self.warn(self.value_str_ret('输入1', '', 'p'))

		CMPFUNC = CFUNCTYPE(c_char_p, c_char_p)
		DriverCpp.setCallback("subscribers",CMPFUNC(self.subscribers_str_ret))
		# self.warn(DriverCpp.testCallback('subscribers',self.id('输入2')))

		#--------------- 属性读写给C++扩展模块 ------------------
		CMPFUNC = CFUNCTYPE(c_char_p)
		DriverCpp.setCallback("getSysId", CMPFUNC(self.getSysId))
		# self.warn(DriverCpp.testCallback('getSysId'))

		CMPFUNC = CFUNCTYPE(c_char_p)
		DriverCpp.setCallback("getSysAttrs", CMPFUNC(self.getSysAttrs))
		# self.warn(DriverCpp.testCallback('getSysAttrs'))

		CMPFUNC = CFUNCTYPE(c_char_p)
		DriverCpp.setCallback("getData2attrs", CMPFUNC(self.getData2attrs))
		# self.warn(DriverCpp.testCallback('getData2attrs'))

		CMPFUNC = CFUNCTYPE(c_char_p)
		DriverCpp.setCallback("getData2subs", CMPFUNC(self.getData2subs))
		# self.warn(DriverCpp.testCallback('getData2subs'))

		CMPFUNC = CFUNCTYPE(None,c_bool)
		DriverCpp.setCallback("setCollectingOneCircle", CMPFUNC(self.setCollectingOneCircle))
		# self.warn(DriverCpp.testCallback('setCollectingOneCircle',True))

		CMPFUNC = CFUNCTYPE(None,c_bool)
		DriverCpp.setCallback("setPauseCollect", CMPFUNC(self.setPauseCollect))
		# self.warn(DriverCpp.testCallback('setPauseCollect',False))

		# ------------------------python调用，C++模块内实现的函数框架---------------------------
		DriverCpp.InitComm(json.dumps(attrs))
		# self.online(True)

	#2、采集引擎回调，可也可以开启，也可以直接注释掉（对于主动上报，不存在遍历采集的情况）
	def Collecting(self, dataId):
		return tuple([self.valueTyped(dataId, DriverCpp.Collecting(dataId))])	#这里需要返回tuple类型()，但是注意，不能直接以（val）的方式提供，但是list可也，所以[val]，再用tuple(list)，就可以转换成tuple!

	#3、控制
	#广播事件回调，其他操作访问
	def Event_customBroadcast(self, fromUuid, type, data):
		return DriverCpp.Event_customBroadcast(fromUuid, type, str(data))

	# 4、查询
	# 查询事件回调，数据点查询访问
	def Event_getData(self, dataId, condition):
		return DriverCpp.Event_getData(dataId, condition)

	# 5、控制事件回调，数据点控制访问
	def Event_setData(self, dataId, value):
		return DriverCpp.Event_setData(dataId, str(value))		#给到c++，全部都用字符串类型标识值，让其结合数据点的类型属性来自己做转换，避免各种类型的函数原型重载

	# 6、本地事件回调，数据点操作访问
	def Event_syncPubMsg(self, point, value):
		return DriverCpp.Event_syncPubMsg(point, str(value))