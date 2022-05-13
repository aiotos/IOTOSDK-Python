#!coding:utf8
import json
import sys
from bitarray import bitarray

sys.path.append("..")
from driver import *

import base64
import gevent
from gevent.server import StreamServer

from jcomm import *
import re
import struct

class AonengDriver(IOTOSDriverI):
	m_hbt = False
	#校验码，所有字节对应的二进制相加，超出0xff的，取剩余8位，也就是总和对2^8取余！
	def check(self,ar):
		sumtmp = 0
		artmp = ar
		for obj in ar:
			sumtmp += obj
		self.debug(sumtmp)
		sumtmp %= 256
		return sumtmp

	#tcp数据回调
	def tcpCallback(self, data):
		try:
			self.info("> > > > > >: " + self.str2hex(data) + " ------ " + str(len(data)))
			hbtflag = (0xA5, 0x00, 0x12, 0x59, 0x4A)
			if len(data) >= 5 and struct.unpack('BBBBB',data[:5]) == hbtflag: # and data[-1] == 0xBE:
				devmac = data[5:len(data) - 1]
				self.warn(u'---硬件心跳：' + self.str2hex(devmac))
				hbtdata = list(hbtflag)
				hbtdata.extend(devmac)
				hbtdata.append(0xBE)
				# self.warn(self.str2hex(hbtdata))
				self.__tcpServer.send(bytearray(hbtdata))
				self.m_hbt = not self.m_hbt
				self.warn(self.setValue(u'心跳', self.m_hbt))

			# self.__tcpServer.send(bytearray([0xA5, 0x00, 0x1D, 0x50, 0xF6, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0xCC,
			# 	 0xDD, 0xA1, 0x02, 0x00, 0xC8, 0x00, 0x04, 0x00, 0x04, 0x0D,
			# 	self.check([0xA5, 0x00, 0x1D, 0x50, 0xF6, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0xCC,
			# 	 0xDD, 0xA1, 0x02, 0x00, 0xC8, 0x00, 0x04, 0x00, 0x04, 0x0D])]))

			datarcv = []
			if self.unpack('B',data[0]) == 0xa5 and struct.unpack('BB',data[3:5]) == (0x53,0x43):
				self.warn(u'数据上报！')
				lentmp = self.unpack('>h',data[1:3])
				datarcv = data[17: -1]
				self.errlog(self.str2hex(datarcv))

				# if struct.unpack('BBB',datarcv[0:3]) != (0xee,0xff,0x01):
				# 	self.error(u'未知数据')
				# 	return

				#继电器状态
				valtmp = self.unpack('>h',datarcv[3:5])
				pointArrTmp = [u'输出1',u'输出2',u'输出3',u'输出4']
				for pointtmp in pointArrTmp:
					self.errlog(self.setValue(pointtmp, valtmp % 2))
					valtmp /= 2

				#开关量输入
				valtmp = self.unpack('>h',datarcv[5:7])
				pointArrTmp = [u'输入1', u'输入2', u'输入3', u'输入4']
				for pointtmp in pointArrTmp:
					self.errlog(self.setValue(pointtmp, valtmp % 2))
					valtmp /= 2

				# 温度
				pointArrTmp = [u'温度1', u'温度2', u'温度3', u'温度4']
				for pointtmp in pointArrTmp:
					indextmp = pointArrTmp.index(pointtmp)

					#温度零下等特殊情况暂不支持
					# symboltmp = (self.unpackByte(datarcv[7 + 2 * indextmp]) >> 7) % 2 * (-1)
					# valtmp = symboltmp * (self.unpackByte(datarcv[7 + 2 * indextmp]) & 0x7F * 256 + self.unpackByte(datarcv[8 + 2 * indextmp])) / 10.0

					valtmp = (self.unpackByte(datarcv[7 + 2 * indextmp]) * 256 + self.unpackByte(datarcv[8 + 2 * indextmp])) / 10.0
					self.debug(valtmp)
					self.errlog(self.setValue(pointtmp, valtmp))

				# 液位
				pointArrTmp = [u'液位1', u'液位2', u'液位3', u'液位4']
				for pointtmp in pointArrTmp:
					indextmp = pointArrTmp.index(pointtmp)
					indextmp -= 1	# added by lrq 20200829 现场反应实际硬件液位这里端子跟数据点错位了一个，端子2为数据点1、端子3为数据点2，依次这样。所以这里处理，索引依次往前减1
					valtmp = (self.unpackByte(datarcv[15 + 2 * indextmp]) * 256 + self.unpackByte(datarcv[16 + 2 * indextmp])) * 1000 / (150 * 100.00)
					self.debug(valtmp)
					self.errlog(self.setValue(pointtmp, valtmp))

				# 电流
				pointArrTmp = [u'电流1', u'电流2', u'电流3', u'电流4', u'电流5', u'电流6']
				for pointtmp in pointArrTmp:
					indextmp = pointArrTmp.index(pointtmp)
					valtmp = (self.unpackByte(datarcv[23 + 2 * indextmp]) * 256 + self.unpackByte(datarcv[24 + 2 * indextmp])) / 10.00
					self.errlog(self.setValue(pointtmp, valtmp))


				# cop能效 added by lrq 20200903
				T = 60
				T1 = self.value(u'温度1','m')
				V = 10

				h = self.value(u'液位1','m')
				h = h/20 #temp 临时除以20，因为目前过来的数据是46m，这个是悬空的，不合理的

				s = 7
				w = 7300
				t1 = 0 		#启动时间（电流之和大于5A）
				t2 = 3600   #关闭时间（电流之和小于5A）
				cop = (T - T1) * (V - h*s) * 1000 * 4200 / w * (t2 - t1)
				self.warn('T1: ' + str(T1))
				self.warn('h: ' + str(h)) 
				self.setValue(self.name('47b0'), str(cop))
			else:
				self.warn("非数据上报！")

		except Exception, e:
			traceback.print_exc(u'数据解析失败' + e.message)

	#1、通信初始化
	def InitComm(self,attrs):
		try:
			# 一、tcp端口监听
			self.__port = self.sysAttrs['config']['param']['port']
			self.__tcpServer = TcpServerThread(self, self.__port)
			self.__tcpServer.setDaemon(True)
			self.__tcpServer.start()
			self.info(self.sysAttrs['name'] + u' TCP端口' + str(self.__port) + u"已启动监听！")
			self.zm.pause_collect = True
		except Exception, e:
			self.online(False)
			traceback.print_exc(u'通信初始化失败' + e.message)

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
		# configtmp = self.data2attrs[dataId]['config']

		return json.dumps({'code':0, 'msg':'', 'data':''})


	# 事件回调接口，监测点操作访问
	def Event_setData(self, dataId, value):

		# if self.data2attrs[dataId]['valuetype'] == 'BLOB':
		# 	_value = value
		# 	value = base64.b64decode(value)
		# 	print 'value', value, _value
		# try:
		# 	codetmp = 1
		# 	retmsg = None
		# 	retmsg = self.data2server[dataId].send(value)
		# 	if retmsg is None:
		# 		return json.dumps({'code': codetmp, 'msg': 'TCP not 连接 not is 异常！', 'data': retmsg})
		# 	elif retmsg == '0':
		# 		codetmp = 0
		# 	print self.__class__.__name__, 'Event_setData', self.sysAttrs['name'], self.name(dataId), value
		# except Exception as e:
		# 	traceback.print_exc()
		self.debug(u'参数下发：' + self.name(dataId) + '(' + dataId + ')' + ' : ' + str(value))
		artmp = [u'输出1',u'输出2',u'输出3',u'输出4']
		try:
			indextmp = artmp.index(self.name(dataId))
			H_ctrltmp = 0
			L_ctrltmp = 0x01 << indextmp
			if value == 'true':
				H_ctrltmp = 0x01 << indextmp
			cmd = bytearray([0xa5,0,0x25,0x50,0xf6,1,2,3,4,5,6,1,2,3,4,5,6,0xcc,0xdd,0xa1,0x01,0,H_ctrltmp,0,L_ctrltmp,0x0d])
			cmd.append(self.check(cmd))

			# 这里需要加上阻塞等待操作成功返回！！？？？？？？？？？？
			self.__tcpServer.send(cmd)
			self.warn(u'下发控制：' + self.str2hex(str(cmd)))
		except Exception, e:
			traceback.print_exc(u'下发控制失败：' + e.message)

		return json.dumps({'code':0, 'msg':'', 'data':''})

	# 事件回调接口，监测点操作访问
	def Event_syncPubMsg(self, point, value):
		'''*************************************************

		TODO

		**************************************************'''
		return json.dumps({'code':0, 'msg':'', 'data':''})