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

    # 1、通信初始化
    def InitComm(self, attrs):

        self.online(True)

        # self.setValue('zkys-SimuDev.字符串1', "zws")
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
        ionode_uuid = attrs.get('gateway_uuid')
        device_oid = attrs.get('device_oid')
        client_id = 'device_' + ionode_uuid + '_' + device_oid

        self.logger.info(('clientId', client_id))
        self.__mqttClient = MqttClient(client_id=client_id)
        self.mqttClient.connect('mqtt.iot-os.net', 1883, 600)  # 600为keepalive的时间间隔
        self.__shadowTopic = ShadowTopic(ionode_uuid + '/' + device_oid)
        self.mqttClient.subscribe(self.shadowTopic.update, qos=0)
        print self.shadowTopic.update
        self.mqttClient.subscribe(self.shadowTopic.get, qos=0)
        print self.shadowTopic.get
        # self.__mqttClient.on_log = self.mqtt_on_log
        self.mqttClient.on_message = self.mqtt_on_message
        self.mqttClient.loop_start()  # 保持连接

    def mqtt_on_log(self, client, userdata, level, buf):
        self.logger.info((client, userdata, level, buf))

    def mqtt_on_message(self, client, userdata, message):
        # self.logger.info((message.qos, message.topic, json.dumps(message.payload)))
        self.logger.info(client.client_id)
        self.logger.info(message.topic)
        self.logger.info(json.dumps(message.payload,indent=3))

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

    # # 2、采集
    # def Collecting(self, dataId):
    #     return None
    #     return (time.time(),)

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
