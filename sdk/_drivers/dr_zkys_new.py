#!coding:utf8
import json
import sys
sys.path.append("..")
from driver import *
from jcomm import *
import struct

class MyDriver(IOTOSDriverI):
	#1、通信初始化
	def InitComm(self,attrs):
		try:
			# 一、tcp端口监听
			self.__port = self.sysAttrs['config']['param']['tcp']
			self.__tcpServer = TcpServerThread(self, self.__port)
			self.__tcpServer.setDaemon(True)
			self.__tcpServer.start()
			self.debug(self.sysAttrs['name'] + u' TCP端口' + str(self.__port) + u"已启动监听！")

		except Exception, e:
			self.online(false)
			traceback.print_exc(u'通信初始化失败' + e.message)

	# #2、采集引擎回调，可也可以开启，也可以直接注释掉（对于主动上报，不存在遍历采集的情况）
	# def Collecting(self, dataId):
	# 	'''*************************************************
	# 	TODO
	# 	**************************************************'''
	# 	return ()

	def tcpCallback(self, data):
		try:
			datastr = ''
			#截取中间4个字节
			idHexTmp = data[6:10]
			#将这4个字节转成无符号整型数
			idNumTmp = struct.unpack('>I', idHexTmp)[0]
			#截取索引从0开始的第27个开始，到末尾的变长的数据部分（从1数起，第26、27两个字节形成的整数，就是后面变长数据的长度，并且最末并没有校验码什么！）
			infomation = data[27:]

			self.info('correct information >>>>>>>>>'  + self.str2hex(infomation))
			for dataId, attrs in self.data2attrs.items():
				if 'param' not in attrs['config']:
					self.error(attrs['config'])
					break
				paramtmp = attrs['config']['param']
				if 'sensorId' in paramtmp and 'dataField' in paramtmp  :
					sensorId = paramtmp['sensorId']
					dataField = paramtmp['dataField']
					if sensorId == idNumTmp:
						self.info(" ID >>>>>>>>> " + str(sensorId))
						if 'infochioce' in paramtmp:
							infochioce = paramtmp['infochioce']
							if infochioce == 10 :
								self.info('data>>>>>>>>>>>>>>>>>>>>' + self.str2hex(infomation) )
								tmptur = struct.unpack('>h', infomation[3:5])[0]  # 一共四个字节，打包起来16进制数乘以0.1
								tmpture = float(tmptur) * 0.1
								if dataField == 0:
									self.info('dosome>>>>>>>>>>>>>>>>>')
									self.setValue(self.name(dataId), float(tmpture))
								if dataField == 1:
									'''
									TODO
									'''
						#其他节点数据分析
						if struct.unpack('B',data[-1])[0] == 0:	#如果最后一个为0x00，那么最后字符串转float会报错！
							infomation = data[27:-1]
						datastr = infomation.decode('ascii')
						tempertmp = datastr.split('.')[0] + '.' + datastr.split('.')[1][0:2]
						voltagetmp = datastr.split(tempertmp)[1]
						if dataField == 0:
							self.setValue(self.name(dataId),float(tempertmp))
						if dataField == 1:
							self.setValue(self.name(dataId),float(voltagetmp))
				if 'devid' in paramtmp :
					devid = paramtmp['devid']



		except Exception, e:
			traceback.print_exc(e.message)

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