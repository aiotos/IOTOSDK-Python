#!coding:utf8
import json
import sys
sys.path.append("..")
from driver import *

class TemplateDriver(IOTOSDriverI):
	#1、通信初始化
	def InitComm(self,attrs):
		'''*************************************************
		TODO
		#self.setPauseCollect(True)
        #self.setCollectingOneCircle(False)
		#self.online(True)
		#self.setValue(u'demo_device.热水供水泵控制', True)
		**************************************************'''

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
		'''*************************************************
		TODO 
		**************************************************'''
		return json.dumps({'code':0, 'msg':'', 'data':''})

	# 6、本地事件回调，数据点操作访问
	def Event_syncPubMsg(self, point, value):
		'''*************************************************
		TODO 
		**************************************************'''
		return json.dumps({'code':0, 'msg':'', 'data':''})