# -*- coding: UTF-8 -*-
import paho.mqtt.client as mqtt

def mqtt_run():
    client = mqtt.Client(client_id='x' * 128)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect('127.0.0.1', 1883, 600)  # 600为keepalive的时间间隔
    client.publish('fifa', payload=json.dumps(s), qos=0)
    client.loop_forever()


#完整的设计的包括上下文交互的格式
# s = {
#         "state": {
#             "desired": {
#                 "color": "RED",
#                 "sequence": ["RED", "GREEN", "BLUE"]
#             },
#             "reported": {
#                 "窗口上报": '0',
#                 "门锁上报": '1',
#                 "窗口读取": '2',
#                 "门锁读取": '3',
#             }
#         },
#         "metadata": {
#             "desired": {
#                 "color": {
#                     "timestamp": 12345
#                 },
#                 "sequence": {
#                     "timestamp": 12345
#                 }
#             },
#             "reported": {
#                 "color": {
#                     "timestamp": 12345
#                 }
#             }
#         },
#         "version": 10,
#         "clientToken": "UniqueClientToken",
#         "timestamp": 123456789
#     }

#简单上报的格式
s = {
        "state": {
            "reported": {
                "windowReport": 'hello windowReport',
                # "doorlockReoprt": 'hi doorlockReoprt',
                # "windowRead": 'how r u windowRead',
                # "doorlockRead": 'thanks doorlockRead',
            }
        }
    }

import json
import time

def on_connect(client, userdata, flags, rc):
    print("Connected with result code: " + str(rc))

def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))

if __name__ == '__main__':
    import uuid
    client_id = 'service_'  #设备id必须device_开头
    client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv5)
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set('zws', '123456')
    client.connect('121.36.162.174', 1883, 1)  # 600为keepalive的时间间隔
    client.subscribe('')
    client.loop_forever()
    while True:
        # s['timestamp'] = time.time()
        # ret = client.publish('sys/things/5a902e1c6f4211eab383000c2988ff06/742cd7d8/shadow/update', payload=json.dumps(s), qos=0)
        s = {
            'requestId': uuid.uuid4().__str__(),
            'requestTime': time.time() * 1000,
            'data': {
                "179f": dict(ts=time.time() * 1000, val=time.time())
            }
        }
        ret = client.publish('$iotos/device/sdk/c546586ee56911eba71dfa163e396af4/15f87154', payload=json.dumps(s), qos=0)
        print ret, json.dumps(s)

        time.sleep(1)
