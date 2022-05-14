#!coding:utf8
import json
import sys
sys.path.append("..")
from driver import *

class TemplateDriver(IOTOSDriverI):
	'''
	驱动派生类模板，直接编写设备子系统接入相关的接口协议转换代码

	1.属性：
		1.1	String sysId 
			设备实例全局标识

        1.2	Json sysAttrs
			设备实例配置属性
        
		1.3	Json data2attrs
			数据点与属性配置键值对
        
		1.4	Json data2subs
			数据点与被订阅设备列表键值对
		
		1.5	Json name2dataId
			数据点名称与对应标识键值对
	
	2.方法
		2.1 String getSysId()
			获取设备标识（参见1.1）

		2.2 Json getSysAttrs()
			获取设备配置（参见1.2）
		
		2.3 Json getData2attrs()
			获取数据点配置（参见1.3）
		
		2.4 Json getData2subs()
			获取数据被订阅信息（参见1.4）
		
		2.5 String id(String name)
			数据点名称转标识（参见1.5），将名称标识（方便阅读和修改的）换成ID标识（保证唯一性，方便驱动代码复用）
			注意，支持"[数据点名称]"或"[设备名称].[数据点名]"，暂不支持"全名称"（"[网关名称].[设备名称].[数据点名称]"）
		
		2.6	String name(String id)
			数据点标识转名称，将标识ID转成名称
			注意，支持"[数据点标识]"或"[设备标识].[数据点标识]"，暂不支持"全ID标识"（"[网关标识].[设备标识].[数据点标识]"）
		
		2.7 None setPauseCollect(Bool enable=True)
			传入True或False，设置3.3中Collecting()是否停止采集循环遍历，默认不启动。调用并传入False将启动采集循环（线程），
			按顺序自动从数据点表第一个到最后一个进行遍历传入，详见3.3。
		
		2.8 None setCollectingOneCircle(Bool enable=True)
			在2.7设置启用采集循环前提下，传入True或False，设置3.3中采集循环是周期循环遍历，还是初始化遍历完数据点表一次就退出（默认）
		
		2.9 String pointId(String dataId)
			根据当前设备下数据点由ID标识，获取带网关、设备的"全ID标识"（"[网关标识].[设备标识].[数据点标识]"）
			@param 
				dataId: String	数据点ID标识，如"0b2e"
        	@return String	全ID标识，如'9003f858c85011ecbb02525400ffc252.e2c4f6fe.0b2e'
		
		2.10 String(Json) setValue(String name=None,id=None, Bool/String/Int/Float value, Timestamp timestamp=time.time(), Bool auto_created=False)
			上报当前设备下单个数据点的值。注意name、id保证有任一传入即可，不要都传入。
			@param
				 name: String	数据点名称
				   id: String	数据点ID标识
				value: Bool/String/Int/Float	数据点上报值
			@return String	Json字符串：{"code": 0, "msg":"", "data":""}，返回格式及错误码详见README.md
		
		2.11 String(Json) setValues(Json data_values)
			批量上报数据点值。
			@param
				data_values: Json 多个数据点与值组成的json数组，比如[{"id": "数据点ID", "value": "数据点value"}, {"id": "数据点ID", "value": "数据点value"}]
			@return String 多个返回结构Json数组字符串，比如[{"code": 0, "msg":"", "data":""},{"code": 0, "msg":"", "data":""}]，返回格式及错误码详见README.md
		
		2.12 Bool/String/Int/Float valueTyped(String dataId,String strValue)
			将字符串类型的值按照点表类型转换成实际类型
			@param
				  dataId: String	数据点ID标识
				strValue: String	数据点值对应的字符串
			@return Bool/String/Int/Float	根据数据点的实际类型将字符串数值转换成实际类型
		
		2.13 Bool/String/Int/Float value(String name,String param='',String source='memory')
			获取数据点的当前值，包含从采集引擎缓存、平台数据库、以及设备当下最新这三种方式
			@param
				  name: String	数据点名称
				 param: String	查询条件，
				source: String	有'memory'、'device'、'platfrom'三个来源参数，简写m/M,d/D，p/P，分别是上次采集到引擎的数据、设备当前数据、上报到平台的数据三类
			@return Bool/String/Int/Float	按照实际类型返回数据点当前值

		2.14 String(Json) subscribers(self, dataId)
    		订阅了当前设备指定监测点的外部设备ID标识列表
			@param
				dataId: String	数据点ID标识
			@return String	返回Json数组字符串，比如["d8540013","36cb7dd8","82591776"]
		
		2.15 String(Json) online(Bool state)
		    上报平台设备上下线状态
			@param
				state: Bool	上线（True）/下线（False）
			@return String	参见详见README.md，通用数据返回结构

	'''
	'''
	3.服务（引擎回调，需用户重写实现的驱动代码）
		3.1 通信初始化：Bool InitComm(Json attrs)
		3.2 通信连接状态回调（非必要，结合jcomm.py）：None connectEvent(Bool state): 
		3.3 循环采集：Dict/Array Collecting(String dataId): 
		3.4 平台下发广播：String(Json) Event_customBroadcast(String fromUuid,String type,String data): 
		3.5 平台下发查询：String(Json) Event_getData(String dataId, string condition): 
		3.6 平台下发控制：String(Json) Event_setData(String dataId, Bool/String/Int/Float value): 
		3.7 订阅数据上报：String(Json) Event_syncPubMsg(String point, Bool/String/Int/Float value): 
	'''

	#3.1 通信初始化
	def InitComm(self,attrs):
		'''
		需要用户实现的设备通信初始化。
		Parameter
		  attrs: dict 点表json加载并补全（参见parent指向）后，当前设备下包括数据的部分，示例如下：
		  	{
				"id": 11,
				"device_oid": "d8540013",
				"gateway_uuid": null,
				"gateway_id": 8,
				"uid": 28,
				"config": {
					"driver": "python/dr_pingshanshuiwu.ZSWDriver"
				},
				"name": "水位尺",
				"type": "",
				"description": "河道水文监测站-水位尺",
				"timestamp": 1650774553.0,
				"on": false,
				"tpl_id": 9,
				"data": {
					"20bf": {
						"id": 877,
						"name": "msgId",
						"description": "流水号（累加）",
						"config": {},
						"defaultvalue": "",
						"readwrite": "1",
						"timestamp": 1651338138724,
						"valuetype": "STRING",
						"maxvalue": "999",
						"minvalue": "0",
						"sensibility": "0.1",
						"refreshcycle": "0",
						"unit": null,
						"tpl_id": 9,
						"regexp": "english",
						"value": null,
						"data_date": null,
						"data_oid": "20bf"
					},
				}
			}
		Return
		  bool: True/False
		'''
		'''
		
		TODO
		#self.setPauseCollect(True)
        #self.setCollectingOneCircle(False)
		#self.online(True)
		#self.setValue(u'demo_device.热水供水泵控制', True)
		
		''''
		return True

	#3.3 循环采集
	def Collecting(self, dataId):
		'''
		对点表自动遍历的采集循环，可开启或关闭（对于主动上报，不存在遍历采集的情况）
		Parameter
		  dataId: string 当前数据点全局标识id，示例如"0b2e"
		Return
		  tuple: () 元组类型返回，多个不同类型数据的顺序组合，比如modbus批量采集数据后多个值的返回。
			[*]应该支持多类型返回，常规数值类型，或元组都可以，目前直接返回dataId，报错；返回(dataId)报错；返回[dataId]才可以！
		'''
		'''

		TODO
		
		''''
		return ()

	#3.4 平台下发广播
	def Event_customBroadcast(self, fromUuid, type, data):
		'''
		高级用途，广播事件回调，其他操作访问，详略
		'''
		'''

		TODO 
		
		'''
		return json.dumps({'code':0, 'msg':'', 'data':''})

	#3.5 平台下发查询
	def Event_getData(self, dataId, condition):
		'''
		查询事件回调，数据点查询访问
		Parameter
			dataId: string 当前数据点全局标识id，示例如"0b2e"
			condition: string 结合驱动支持下发的自定义查询条件
		Return
		  	string: 查询结果转成string类型返回
		'''
		'''

		TODO 
		
		'''
		return json.dumps({'code':0, 'msg':'', 'data':''})

	#3.6 平台下发控制
	def Event_setData(self, dataId, value):
		'''
		控制事件回调，数据点控制访问
		Parameter
			dataId: string 当前数据点全局标识id，示例如"0b2e"
			value: 下发设备控制或写入的值，由数据点自身属性来决定类型，通常为Bool或String
		Return
		  	string: 执行结果转成string类型返回
		'''
		'''

		TODO 
		
		'''
		return json.dumps({'code':0, 'msg':'', 'data':''})

	#3.7 订阅数据上报
	def Event_syncPubMsg(self, point, value):
		'''
		数据订阅的事件回调。通常是同一个网关下不同设备上报的数据（兼容高级用途跨网关远程数据点订阅，略），常见订阅规则如下，
		在当下驱动对应的设备实例驱动根配置中，param.sub以数组形式订阅同一个网关下其他一个或多个设备上报到平台的数据，以
		[设备全局标识].[数据点全局标识]，其中数据点全局标识可以指定也可以用*代替，表明指定设备所有setValue上报的数据都会
		被订阅过来，在这里做数据处理，通过业务逻辑加工（常见是报文协议解析）后再做上报。
		{
			"driver": "python/dr_xxx.xxxDriver",
			"param": {
				"sub": [
						"1bcd6b35.*"
					],
			}
		}
		Parameter
			point: string 当前数据点全ID（网关标识.设备标识.数据点标识），示例如"9003f858c85011ecbb02525400ffc252.e2c4f6fe.0b2e"，id难以辨别可通过self.name()转换
			value: 上报对应的值，由数据点自身属性来决定类型，通常为Bool/String/Int/Float
		Return
		  	string: string类型返回。注意同网关下不同设备的订阅为异步，可以默认返回或不返。兼容高级用途跨网关远程数据点订阅，返回值解释略
		'''
		'''

		TODO 

		'''
		return json.dumps({'code':0, 'msg':'', 'data':''})