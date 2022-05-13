#!coding:utf8
import json
import winsound
import sys
sys.path.append("..")

from driver import *


class Serial2TcpDtuDriver(IOTOSDriverI):

	# #1、通信初始化
	# def InitComm(self,attrs):
	# 	pass
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

		bindtmp = self.sysAttrs['config']['bind']
		for tcp_ip,serial_port in bindtmp.items():
			tcp_ip = "tcp server." + tcp_ip
			serial_port = "serial server." + serial_port

			if self.name(point) == tcp_ip:
				self.setValue(serial_port, value)
			elif self.name(point) == serial_port:
				self.setValue(tcp_ip, value)

		print self.__class__.__name__, 'Event_syncPubMsg', self.sysAttrs['name'], self.name(point), value

		return json.dumps({'code': 0, 'msg': '', 'data': ''})
