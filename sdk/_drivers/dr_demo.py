#!coding:utf8
import json
import string
#import winsound
import sys
sys.path.append("..")

from driver import *
import threading
import time

class DemoDriver(IOTOSDriverI):
	#1、通信初始化
	def InitComm(self,attrs):
		self.setPauseCollect(True)
		self.setCollectingOneCircle(True)

		self.online(True)
		ret = self.setValue(u'字符数据', 'hello iotos!')
		self.warn(ret)
		ret = self.setValue(u'开关数据', True)
		self.warn(ret)
		ret = self.setValue(u'整数数据', 781)
		self.warn(ret)
		ret = self.setValue(u'浮点数据', 3.14)
		self.warn(ret)

	#2、采集
	def Collecting(self, dataId):
		'''*************************************************

		TODO

		**************************************************'''
		return ()


	#3、控制
	#事件回调接口，其他操作访问
	def Event_customBroadcast(self, fromUuid, type, data):
		'''*************************************************

		TODO 

		**************************************************'''
		return json.dumps({'code':0, 'msg':'', 'data':''})

	# 3、查询
	# 事件回调接口，监测点操作访问
	def Event_getData(self, dataId, condition):
		'''*************************************************

		TODO 

		**************************************************'''
		data=None
		return json.dumps({'code':0, 'msg':'', 'data':data})


	# 事件回调接口，监测点操作访问
	def Event_setData(self, dataId, value):

		#winsound.Beep(500,100)
		self.warn(dataId + ":")
		self.warn(value)


		return json.dumps({'code':0, 'msg':'', 'data':''})


	# 事件回调接口，监测点操作访问
	def Event_syncPubMsg(self, point, value):

		return json.dumps({'code':0, 'msg':'', 'data':''})