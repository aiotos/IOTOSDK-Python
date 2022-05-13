#!coding:utf8
import json
import sys
sys.path.append("..")
from driver import *
import threading

class Driver(IOTOSDriverI):
	#1、通信初始化
	def InitComm(self,attrs):

		def timerProcess():

			'''
			1、对应设备B数据点的全名称为"gate_y.dev_b.温度1"，目前跨网关的M2M通信不支持全名称，只支持全ID；
			2、默认source为platfrom，获取上报到平台的数据，这里要获取其他网关下设备的数据，需加上device参数；
			3、此外注意，当前是同一个账号下不同网关之间访问，可直接进行跨网关设备操作，如果是不同的账号，需要在
			控制台一方进行数据点发布，另一方进行数据点订阅，这样订阅方对数据点才有读、写（具体细分权限由发布者设置）操作权限
			'''
			valtmp = self.value('01f277fec35911eaa38e000c2988ff06.c502746c.2e5a',source = 'device')		#gate_y.dev_b.温度1
			print valtmp
			timertmp = threading.Timer(1, timerProcess)
			timertmp.start()

		timertmp = threading.Timer(1, timerProcess)
		timertmp.start()

		self.online(True)


	# #2、采集引擎回调，可也可以开启，也可以直接注释掉（对于主动上报，不存在遍历采集的情况）
	# def Collecting(self, dataId):
	# 	'''*************************************************
	# 	TODO
	# 	**************************************************'''
	# 	return ()

	#3、控制
	#广播事件回调，其他操作访问
	def Event_customBroadcast(self, fromUuid, type, data):
		'''*************************************************
		TODO 
		**************************************************'''
		return json.dumps({'code':0, 'msg':'', 'data':''})

	# 4、查询
	# 查询事件回调，数据点查询访问
	def Event_getData(self, dataId, condition):
		'''*************************************************
		TODO 
		**************************************************'''
		return json.dumps({'code':0, 'msg':'', 'data':''})

	# 5、控制事件回调，数据点控制访问
	def Event_setData(self, dataId, value):

		print 'from other device(B) setData request: ',dataId,value
		# self.setValue(dataId,value)

		return json.dumps({'code':0, 'msg':'', 'data':12121212})

	# 6、本地事件回调，数据点操作访问
	def Event_syncPubMsg(self, point, value):
		'''*************************************************
		TODO 
		**************************************************'''
		return json.dumps({'code':0, 'msg':'', 'data':''})