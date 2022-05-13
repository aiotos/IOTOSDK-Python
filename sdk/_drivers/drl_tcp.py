#!coding:utf8
import json
import sys
sys.path.append("..")
from driver import *
from jcomm import *

class TCPDriver(IOTOSDriverI):
	#1、通信初始化
	# def __init__(self):
	# 	super(TCPDriver, self).__init__()
	# 	self.__tcpServer = None
	# 	self.__port = None
	def send(self,data):
		try:
			self.__tcpServer.send(data)
		except Exception as e:
			traceback.print_exc(u'发送失败：' + e.message)

	def InitComm(self,attrs):
		try:
			self.__port = self.sysAttrs['config']['param']['port']
			self.__tcpServer = TcpServerThread(self, self.__port)
			self.__tcpServer.setDaemon(True)
			self.__tcpServer.start()
			self.warn(self.sysAttrs['name'] + u' TCP端口' + str(self.__port) + u"已启动监听！")
			self.setPauseCollect(True)
			# self.setCollectingOneCircle(True)
		except Exception as e:
			self.online(False)
			traceback.print_exc(u'通信初始化失败' + e.message)

	#2、采集引擎回调，可也可以开启，也可以直接注释掉（对于主动上报，不存在遍历采集的情况）
	def Collecting(self, dataId):
		'''*************************************************
		TODO
		**************************************************'''
		return ()

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
		if self.name(dataId) ==  'rawData':
			self.__tcpServer.send(value)
		return json.dumps({'code':0, 'msg':'', 'data':''})

	# 6、本地事件回调，数据点操作访问
	def Event_syncPubMsg(self, point, value):
		'''*************************************************
		TODO 
		**************************************************'''
		return json.dumps({'code':0, 'msg':'', 'data':''})

	#tcp数据回调
	def tcpCallback(self, data):
		datastr = self.str2hex(data)
		self.info("Master < < < < < < Device: " + datastr)
		self.setValue('rawData',data)

	# 连接状态回调
	def connectEvent(self, state):
		super(TCPDriver, self).connectEvent(state)
		self.setPauseCollect(True)
		# self.setCollectingOneCircle(True)
