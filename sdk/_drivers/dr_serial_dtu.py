#!coding:utf8
import json
import winsound
import sys

sys.path.append("..")
from driver import *

import base64
import serial

class SerialDtuDriver(IOTOSDriverI):

	data2serial = {}

	class SerialRcvThread(threading.Thread):
		def __init__(self, dr,did,cfg):
			threading.Thread.__init__(self)
			self.dataId = did
			self.driver = dr
			self.serial = serial.Serial(port = cfg['port'],
										baudrate = cfg['baudrate'],
										bytesize = cfg['byteSize'],
										parity = cfg['parity'],
										stopbits = cfg['stopbits'],
										xonxoff = cfg['xonxoff'])

		lock = threading.Lock()
		def run(self):
			while True:
				dataHex = bytes()
				dataStr = ''
				n = self.serial.inWaiting()
				if n:
					dataHex += self.serial.read(n)
					if self.driver.data2attrs[self.dataId]['valuetype'] == 'BLOB':
						dataStr = base64.b64encode(dataHex).decode()
					else:
						dataStr = str(dataHex).encode('utf-8')
				if dataStr != '':  # 本地串口下发的数据，转发到路由设备代理
					try:
						self.driver.setValue(self.driver.name(self.dataId), dataStr)
					except Exception as e:
						traceback.print_exc()
						print 'send failed:', e.message
						try:
							self.lock.acquire()
							self.InitComm(None)
						finally:
							self.lock.release()

		def send(self,value):
			return self.serial.write(bytes(value))


	#1、通信初始化
	def InitComm(self,attrs):
		for dataId,attrs in self.data2attrs.items():
			try:
				cfgtmp = attrs['config']['param']
				if not self.data2serial.has_key(dataId):
					# to make the server use SSL, pass certfile and keyfile arguments to the constructor
					serialtmp = self.SerialRcvThread(self,dataId,cfgtmp)
					serialtmp.send(cfgtmp['port'] + ' connected!')
					self.data2serial.update({dataId: serialtmp})
					serialtmp.start()
					#print self.sysAttrs['name'], 'open port', cfgtmp['port']
			except Exception as e:
				print traceback.print_exc()
				print 'serial dtu', self.sysId, 'drive init error', e.message
	# #2、采集
	# def Collecting(self, dataId):
	# 	return "ewd"

	#3、控制
	#事件回调接口，其他操作访问
	def Event_customBroadcast(self, fromUuid, type, data):

		# tabletmp = {}
		# tabletmp[self.sysId] = self.sysAttrs
		# tabletmp[self.sysId]['data'] = self.data2attrs
		# print json.dumps(tabletmp),'\r\n'

		return json.dumps({'code':0, 'msg':'', 'data':''})


	# 事件回调接口，监测点操作访问
	def Event_getData(self, dataId, condition = ''):
		configtmp = self.data2attrs[dataId]['config']

		return json.dumps({'code':0, 'msg':'', 'data':''})


	# 事件回调接口，监测点操作访问
	def Event_setData(self, dataId, value):

		if self.data2attrs[dataId]['valuetype'] == 'BLOB':
			value = base64.b64decode(value)
		try:
			retmsg = None
			codetmp = 1
			retmsg = self.data2serial[dataId].send(value)
			if retmsg > 0:
				codetmp = 0
			print self.__class__.__name__, 'Event_setData', self.sysAttrs['name'], self.name(dataId), value
		except Exception as e:
			print traceback.print_exc()
			print 'serial.send', e.message
			self.InitComm(None)



		return json.dumps({'code':codetmp, 'msg':'', 'data':retmsg})


	# 事件回调接口，监测点操作访问
	def Event_syncPubMsg(self, point, value):
		'''*************************************************

		TODO 

		**************************************************'''
		return json.dumps({'code':0, 'msg':'', 'data':''})