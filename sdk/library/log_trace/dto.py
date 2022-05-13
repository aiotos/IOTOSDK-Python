# coding=utf-8
"""日志结构体"""
import time


class LogT(object):
    app = None  # type: str
    tag = None  # type: str
    request_id = None  # type: str
    request_time = None  # type: float
    request_token = None  # type: str
    gateway_uuid = None  # type: str
    response_status = None  # type: str
    response_trace = None  # type: str
    response_id = None  # type: str
    response_time = None  # type: float
    handle_time = None  # type:float
    local_time = None  # type:float
    filepath = None
    fileline = None
    extra = None  # type:dict


class LogC(LogT):

    def __init__(self, app, group, tag, handle_time, filepath, fileline, request_id=None, gateway_uuid=None,
                 request_token=None, response_status=None, response_trace=None,
                 extra=None):
        self.app = app
        self.tag = tag
        self.group = group
        self.handle_time = handle_time
        self.local_time = time.time()
        self.filepath = filepath
        self.fileline = fileline
        self.request_id = request_id
        self.request_token = request_token
        self.gateway_uuid = gateway_uuid
        self.response_status = response_status
        self.response_trace = response_trace
        self.extra = extra

    def form_dict(self):
        return self.__dict__


class RequestT(object):
    id = None  # type: str
    uuid = None  # type: str
    user = None  # type: str
    token = None  # type: str
    user_id = None  # type: int
    host = None  # type: str
    gateway_name = None  # type: str


class RequestC(RequestT):

    @property
    def log_group(self):
        return '%s/%s/%s' % (self.host, self.user, self.gateway_name)
