#!coding:utf8
import json
import sys
sys.path.append("..")
from driver import *

class Thales800(IOTOSDriverI):
	#1、通信初始化
	def InitComm(self,attrs):
		try:
			# 一、tcp端口监听
			self.__port = self.sysAttrs['config']['param']['tcp']
			self.__tcpServer = TcpServerThread(self, self.__port)
			self.__tcpServer.setDaemon(True)
			self.__tcpServer.start()
			self.info(self.sysAttrs['name'] + u' TCP端口' + str(self.__port) + u"已启动监听！")
		except Exception, e:
			self.online(false)
			traceback.print_exc(u'通信初始化失败' + e.message)

	def tcpCallback(self, data):
		datastr = self.str2hex(data)
		self.info("HEX Master < < < < < < Device: " + datastr)
		self.info("STRING Master < < < < < < Device: " + data)
		# self.debug(struct.unpack('B', data[11])[0])
		# if len(data) >= 17 and struct.unpack('B', data[12])[0] == 3:  # modbus设备地址1，功能号3
		# 	valuetmp = (struct.unpack('B', data[14])[0] * 256 + struct.unpack('B', data[15])[0]) / 10.0
		# 	for dataId, attrs in self.data2attrs.items():
		# 		try:
		# 			if attrs['config']['param'].has_key('devid') and attrs['config']['param']['devid'] == \
		# 					struct.unpack('B', data[11])[0]:
		# 				self.setValue(self.name(dataId), valuetmp)
		# 				self.info(valuetmp)
		# 				break
		# 		except Exception, e:
		# 			traceback.print_exc(u'忽略异常数据：' + dataId)
		# else:
		# 	self.warn(u'忽略设备地址为1的正常数据以外的数据！')

	#2、采集引擎回调
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