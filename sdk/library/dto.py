# coding=utf-8
# 定义常用数据结构
import json
from enum import Enum


class JSONEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, object):
            return o.__dict__
        else:
            return super(JSONEncoder, self).default(o)


def json_dumps(obj):
    return json.dumps(obj=obj, cls=JSONEncoder)


def for_data(data):
    for k, v in data.items():
        if isinstance(v, object) and hasattr(v, '__dict__'):
            data[k] = for_data(v.__dict__)
    return data


class __DTO(object):

    def to_dict(self):
        data = self.__dict__
        return for_data(data)

    def __str__(self): return json_dumps(self.__dict__)

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        pass


class WebLoginParam(__DTO):
    username = None
    password = None
    httpHost = None
    uuid = None

    def __init__(self, username, password, httpHost, uuid, **kwargs):
        self.username = username
        self.password = password
        self.httpHost = httpHost
        self.uuid = uuid
        super(WebLoginParam, self).__init__(**kwargs)


class RouterConfig(__DTO):
    routerPrxPort = None
    remoteAdapterPort = None
    iotrouterIP = None


class LogTraceT(__DTO):
    httpHost = None  # type: str


class LoginResp(__DTO):
    code = None
    data = None
    heartbeat = None
    msg = None
    product_list = None
    retry = None
    router_config = RouterConfig()  # type: RouterConfig
    logTrace = None  # type: LogTraceT
    time = None
    token = None
    user_id = None

    def __init__(self, router_config=None, logTrace=None, **kwargs):
        if router_config:
            self.router_config = RouterConfig(**router_config)
        if logTrace:
            self.logTrace = LogTraceT(**logTrace)
        super(LoginResp, self).__init__(**kwargs)


class Result(__DTO):
    code = None
    msg = None
    data = dict()
    handle_time = None

    def __init__(self, code, msg, data=None, **kwargs):
        self.code = code
        self.msg = msg
        self.data = data
        super(Result, self).__init__(**kwargs)


class Heartbeat(Result):
    servertime = None

    def __init__(self, code, msg, data=None, servertime=None, **kwargs):
        super(Heartbeat, self).__init__(code, msg, data, **kwargs)
        self.servertime = servertime


class ErrorEnum(Enum):
    SelfOffline = 2  # 自己已掉线
    ObjectOffline = 3  # 对方已掉线
    NoWebSer = 6  # 没有web服务器接入
    Unknown = 101  # 未知错误
    GatewayNotExist = 108  # 网关不存在
    DeviceNotExist = 109  # 设备不存在
    DataNotExist = 110  # 监测点不存在
    RequestNotAuth = 112  # 请求授权失效


class DataDto(__DTO):

    description = None  # type: str
    readwrite = None  # type: int
    timestamp = None  # type: float
    defaultvalue = None  # type: str
    maxvalue = None  # type: float
    minvalue = None  # type: float
    value = None  # type: str
    data_date = None  # type: str
    valuetype = None  # type: str
    refreshcycle = None  # type: int
    tpl_id = None  # type: int
    data_oid = None  # type: str
    regexp = None  # type: str
    sensibility = None  # type: float
    config = None  # type: dict[str, dict]
    id = None  # type int
    unit = None  # type str
    name = None  # type str

    @property
    def ts(self):
        return self.timestamp

    @ts.setter
    def ts(self, v):
        self.timestamp = v

    @property
    def oid(self):
        return self.data_oid

    @oid.setter
    def oid(self, v):
        self.data_oid = v


# ICE异常枚举
# 来源文件
# import Ice_LocalException_ice
class IceExceptionEnum(Enum):
    # level warn
    # This exception indicates a connection establishment timeout condition.
    ConnectTimeoutException = 'Ice::ConnectTimeoutException'
    # level warn
    # This exception indicates a timeout condition.
    TimeoutException = 'Ice::TimeoutException'
    CloseTimeoutException = 'Ice::CloseTimeoutException'
    # level error 致命错误，需要重建通信服务。
    # This exception is raised if the Communicator has been destroyed.
    CommunicatorDestroyedException = 'Ice::CommunicatorDestroyedException'


if __name__ == '__main__':
    s = '中以中模压' + 'asdfas'
    print (s)
