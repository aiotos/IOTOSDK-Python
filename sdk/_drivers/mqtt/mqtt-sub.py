# -*- coding: UTF-8 -*-
import paho.mqtt.client as mqtt
import json

def on_disconnect(client, userdata, flags, rc=None):
    print("disconnect with result code: " + str(rc))


def on_connect(client, userdata, flags, rc):
    print("Connected with result code: " + str(rc))


def on_message(client, userdata, msg):
    print(msg.topic, json.loads(msg.payload))


def on_subscribe(client, userdata, mid, reasonCodes, properties=None):
    print(client, userdata, mid, reasonCodes, properties)


s = {
    "state" : {
        "desired" : {
          "color" : "RED",
          "sequence" : [ "RED", "GREEN", "BLUE" ]
        },
        "reported" : {
          "color" : "GREEN"
        }
    },
    "metadata" : {
        "desired" : {
            "color" : {
                "timestamp" : 12345
            },
            "sequence" : {
                "timestamp" : 12345
            }
        },
        "reported" : {
            "color" : {
                "timestamp" : 12345
            }
        }
    },
    "version" : 10,
    "clientToken" : "UniqueClientToken",
    "timestamp": 123456789
}
if __name__ == '__main__':
    import uuid
    client = mqtt.Client(client_id=uuid.uuid4().__str__())
    client.username_pw_set('zws', '123456')
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe
    client.connect('mqtt.aiotos.net', 1883, 600)  # 600为keepalive的时间间隔
    client.subscribe('$iotos/device/sdk/c546586ee56911eba71dfa163e396af4/15f87154', qos=0)
    client.loop_forever()  # 保持连接
