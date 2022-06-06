from paho.mqtt.client import Client
# from dataclasses import dataclass, asdict


class MqttClient(Client):

    @property
    def client_id(self):
        return self._client_id.decode('utf-8')

class ShadowTopic:

    __topic = ''

    @property
    def topic(self):
        return self.__topic

    def __init__(self, topic):
        self.__topic = 'sys/things/' + topic + '/shadow'

    @property
    def get(self):
        return self.topic + '/get'

    @property
    def get_accepted(self):
        return self.topic + '/get/accepted'

    @property
    def update(self):
        return self.topic + '/update'


# @dataclass
class ShadowState:
    desired = {}
    reported = {}

# @dataclass
class Shadow:

    state = None
    metadata = {}
    version = 0
    clientToken = ''
    timestamp = 0

    def __post_init__(self):
        self.state = ShadowState(**self.state)

    def to_dice(self):
        return asdict(self)

class IotosShadow:

    __mqttClient = None

    @property
    def mqttClient(self):
        return self.__mqttClient

    def __init__(self, mqttClient):
        self.__mqttClient = mqttClient
