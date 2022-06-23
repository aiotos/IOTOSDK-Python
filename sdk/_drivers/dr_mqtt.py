#!coding:utf8
from requests import Session
import requests
import time
import threading
from driver import *
from paho.mqtt.client import MQTTMessage, MQTTMessageInfo
import paho.mqtt.client as mqtt
import json
import sys

sys.path.append("..")
from mqtt.iotos_shadow import ShadowTopic, Shadow, MqttClient

class MqttDriver(IOTOSDriverI):
    __mqttClient = None
    __shadowTopic = None
    __pointList = []

    # 1、通信初始化
    def InitComm(self, attrs):

        self.online(True)        
        t = threading.Thread(target=self.mqtt_run,
                             args=(attrs,), name='mqtt-server')
        t.start()

    def name_to_uuid(self, name):
        data_oid = self.id(name)
        return self.zm.uuid + '.' + self.sysId + '.' + data_oid

    @property
    def mqttClient(self):
        return self.__mqttClient

    @property
    def shadowTopic(self):
        return self.__shadowTopic

    def mqtt_run(self, attrs):
        ionode_uuid = attrs['gateway_uuid']
        device_oid = attrs['device_oid']
        client_id = 'device_' + ionode_uuid + '_' + device_oid

        self.logger.info(('clientId', client_id))
        self.__mqttClient = MqttClient(client_id=client_id)
        self.__mqttClient.username_pw_set('admin', 'public')
        self.__mqttClient.connect('sys.aiotos.net', 1883, 600)  # 600为keepalive的时间间隔
        self.__shadowTopic = ShadowTopic(ionode_uuid + '/' + device_oid)
        self.__mqttClient.on_connect  = self.mqtt_on_connect 
        self.__mqttClient.on_disconnect = self.mqtt_on_disconnect
        self.__mqttClient.on_log = self.mqtt_on_log
        self.__mqttClient.loop_start()  # 保持连接

    def mqtt_on_log(self, client, userdata, level, buf):
        # self.logger.info((client, userdata, level, buf))
        pass

    def mqtt_on_connect(self,client, userdata, flag, rc):
        if rc == 0:
            # 连接成功
            self.warn("Connection successful")
            self.mqttClient.subscribe(self.shadowTopic.update, qos=0)
            self.warn(self.shadowTopic.update)
            self.mqttClient.subscribe(self.shadowTopic.get, qos=0)
            self.warn(self.shadowTopic.get)

            #初始遍历一次，实现逐个数据点订阅
            self.setPauseCollect(False)
            self.setCollectingOneCircle(True)
        
            self.mqttClient.on_message = self.mqtt_on_message
            self.mqttClient.on_subscribe = self.mqtt_on_subscribe
            self.mqttClient.on_unsubscribe = self.mqtt_on_unsubscribe
        
        elif rc == 1:
            # 协议版本错误
            self.warn("Protocol version error")
        elif rc == 2:
            # 无效的客户端标识
            self.warn("Invalid client identity")
        elif rc == 3:
            # 服务器无法使用
            self.warn("server unavailable")
        elif rc == 4:
            # 错误的用户名或密码
            self.warn("Wrong user name or password")
        elif rc == 5:
            # 未经授权
            self.warn("unaccredited")
        self.warn("Connect with the result code " + str(rc)) 
        
    def mqtt_on_disconnect(self,client, userdata, rc):
        # rc == 0回调被调用以响应disconnect（）调用
        # 如果以任何其他值断开连接是意外的，例如可能出现网络错误。
        if rc != 0:
            self.warn("Unexpected disconnection %s" % rc) 
        self.error('MQTT Disconnected!') 
        self.__mqttClient.connect('sys.aiotos.net', 1883, 600)  # 600为keepalive的时间间隔
            
    def mqtt_on_subscribe(self,client, userdata, mid, granted_qos):
        self.warn("on_Subscribed: 订阅成功" + str(mid) + " " + str(granted_qos))
        
    def mqtt_on_unsubscribe(self,client, userdata, mid):
        self.warn("on_unsubscribe, mid: " + str(mid)) 

    def mqtt_on_message(self, client, userdata, message):
        # self.logger.info((message.qos, message.topic, json.dumps(message.payload)))
        self.logger.info(client.client_id)
        self.logger.info(message.topic)
        self.warn(message.payload)
        # self.logger.info(json.dumps(message.payload,indent=3))

        if message.topic == self.shadowTopic.get:
            new_data = {}

            for data_oid, data in self.data2attrs.items():
                uuid = self.zm.uuid + '.' + self.sysId + '.' + data_oid
                res = self.zm.GetPlatformData(uuid)
                res = json.loads(res)
                new_data.setdefault(
                    data.get('name'), res.get('data').get('value'))
                self.logger.info(res)
            showad = {
                "state": {
                    "reported": new_data
                }
            }
            res = self.mqttClient.publish(self.shadowTopic.get_accepted, payload=json.dumps(showad))
            self.logger.info((res))

        elif self.shadowTopic.update == message.topic:
            payload = json.loads(message.payload)
            # shadow = Shadow(**payload)
            device = dict()
            if client.client_id[0:7] == 'device_':
                device = payload['state']['reported']
            else:
                self.logger.info('not device report???')
                raise SyntaxWarning('由设备负责响应处理字段')
                device = payload['state']['desired']
            if len(device) == 0:
                pass
            elif len(device) == 1:
                key, value = device.items()[0]
                res = self.setValue(name=key, value=value)
                self.logger.info(res)
            else:
                value_list = []  # 要批量上报的值结构，其中返回的值元组中第一个就是采集点自身的值，所以先append走一个！
                for key, value in device.items():
                    value_list.append(
                        {'id': self.name_to_uuid(key), 'value': value})
                res = self.setValues(value_list)
                self.logger.info(res)
                
        elif self.__pointList.index(message.topic) != -1:
            self.warn(message.topic + ':' + str(message.payload))
            try:
                self.warn(self.setValue(message.topic, self.valueTyped(message.topic.split('.')[2],str(message.payload, encoding='utf-8'))))
            except Exception as e:
                self.warn(self.setValue(message.topic, self.valueTyped(message.topic.split('.')[2],str(message.payload))))

    # 2、采集
    def Collecting(self, dataId):
        
        pointtmp = self.pointId(dataId)
        self.mqttClient.subscribe(pointtmp, qos=0)
        self.__pointList.append(pointtmp)
        
        return ()

    # 3、控制
    # 事件回调接口，其他操作访问
    def Event_customBroadcast(self, fromUuid, type, data):
        '''*************************************************

        TODO

        **************************************************'''
        return json.dumps({'code': 0, 'msg': '', 'data': ''})

    # 3、查询
    # 事件回调接口，监测点操作访问
    def Event_getData(self, dataId, condition):
        '''*************************************************

        TODO

        **************************************************'''
        data = None
        return json.dumps({'code': 0, 'msg': '', 'data': data})

    # 事件回调接口，监测点操作访问
    def Event_setData(self, dataId, value):

        # winsound.Beep(500,100)

        return json.dumps({'code': 0, 'msg': '', 'data': ''})

    # 事件回调接口，监测点操作访问
    def Event_syncPubMsg(self, point, value):

        return json.dumps({'code': 0, 'msg': '', 'data': ''})
