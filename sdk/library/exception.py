# coding=utf-8


# 服用会话授权过期
class RequestNotAuthError(RuntimeError):
    pass


# 对方已掉线
class ObjectOfflineError(RuntimeError):
    pass


# 没有web服务器接入
class NoWebSerError(RuntimeError):
    pass


# ICE服务丢线了
class SelfOfflineError(RuntimeError):
    pass


class DeviceNotExistError(RuntimeError):
    """设备不存在:109"""
    def __init__(self, msg):
        super(DeviceNotExistError, self).__init__(u'设备不存在,' + msg)


class GatewayNotExistError(RuntimeError):
    """网关不存在:108"""
    def __init__(self, msg):
        super(GatewayNotExistError, self).__init__(u'网关不存在,' + msg)


class DataNotExistError(RuntimeError):
    """设备数据点不存在:110"""
    def __init__(self, msg):
        super(DataNotExistError, self).__init__(u'设备数据点不存在,' + msg)


class UnknownError(RuntimeError):
    """未知错误:101"""
    def __init__(self, msg):
        super(UnknownError, self).__init__(u'未知错误,' + msg)
