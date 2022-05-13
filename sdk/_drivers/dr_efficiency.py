#!coding:utf8
import json
import winsound
import sys
sys.path.append("..")

from driver import *
import threading


class EfficiencyDriver(IOTOSDriverI):
	p1val = 0
	c1val = 0
	f1val = 0
	ctime = 0
	flag = True

	def func(self):
		if self.flag == False:
			self.flag = True
		else:
			self.flag = False
		print self.setValue(u'modbus devices5050.o8', self.flag),self.flag,88888888
		self.timer = threading.Timer(30, self.func)
		self.timer.start()

	#1、通信初始化
	def InitComm(self,attrs):
		self.timer = threading.Timer(30, self.func)
		self.timer.start()

	#
	# #2、采集
	# def Collecting(self, dataId):
	# 	'''*************************************************
    #
	# 	TODO
    #
	# 	**************************************************'''
	# 	return 0


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

		winsound.Beep(1000,500)


		return json.dumps({'code':0, 'msg':'', 'data':''})


	# 事件回调接口，监测点操作访问
	def Event_syncPubMsg(self, point, value):

		#液位
		if self.name(point) == u'modbus devices5051.f1':
			self.f1val = float(value)

		#温度
		inctmp = 0
		if self.name(point) == u'modbus devices5051.p1':
			# if float(value) > 40:
			# 	self.setValue(u'modbus devices5051.o1',0)


			ttmp = time.time()
			inctmp = ttmp - self.ctime
			# if inctmp < 60:
			# 	return json.dumps({'code':0, 'msg':'', 'data':''})
			self.ctime = ttmp

			warterQuality = (0.186 * self.f1val - 0.698) * 3.14 * 0.15 * 0.15 * 1000 * 4.2 * 1000
			temperatureDiff = float(value) - self.p1val
			print temperatureDiff,int(inctmp),555555555
			self.p1val = float(value)

			energeHeat = warterQuality * temperatureDiff
			energeElec = 1500 * int(inctmp)

			#self.setValue(u'ef',energeHeat / energeElec)
			#self.setValue(u'ef',40 * (self.f1val - 3.84) * temperatureDiff / int(inctmp))
			self.setValue(u'ef', 590 * (self.f1val - 3.84) * temperatureDiff / int(inctmp) / 3)

		#电流
		if self.name(point) == u'modbus devices5051.c1':
			self.c1val = float(value)

		return json.dumps({'code':0, 'msg':'', 'data':''})