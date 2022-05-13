# coding=utf-8
"""不向对外"""
import os
import sys
import Ice
import time
import signal
import logging
import traceback
import requests
from library.dto import *
from library.exception import *
from urllib3.exceptions import ResponseError
from .log_trace import LogTrace, LogC
from .log_utils import logging, new_logger
sdk_logger = new_logger(name='iotos_sdk')
sdk_logger.setLevel(logging.ERROR)


logService = None  # type: LogTrace

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3


def sig_kill():
    """杀死自己"""
    try:
        os.kill(os.getpid(), signal.SIGKILL)
    except AttributeError:
        find_kill = 'taskkill -f -pid %s' % os.getpid()
        result = os.popen(find_kill)
        sdk_logger.info(result)


def get_value(obj, name):
    if isinstance(obj, dict) and name in obj:
        return obj[name]
    elif isinstance(obj, object) and hasattr(obj, name):
        return getattr(obj, name)
    else:
        raise ValueError(obj)


def service_monit(func):
    def _service_monit(*args, **kwargs):
        func_ex = None
        raw_ret = None
        try:
            raw_ret = func(*args, **kwargs)
        except (RequestNotAuthError, NoWebSerError, SelfOfflineError, ObjectOfflineError, GatewayNotExistError, UnknownError) as ex:
            sdk_logger.error("Response exception", exc_info=True)
            sig_kill()
            sys.exit(-1)
        except Ice.Exception as ex:
            sdk_logger.error("Ice exception", exc_info=True)
            sig_kill()
            sys.exit(-1)
        except ValueError as ex:
            sdk_logger.error("ValueError exception", exc_info=True)
            sig_kill()
            sys.exit(-1)
        except ResponseError as ex:
            sdk_logger.error("ResponseError exception", exc_info=True)
            sig_kill()
            sys.exit(-1)
        except Exception as ex:
            sdk_logger.error("UnknownError exception", exc_info=True)
            if isinstance(ex, requests.exceptions.RequestException):
                sig_kill()
                sys.exit(-1)
            else:
                raise func_ex

        return_obj = None
        try:
            if raw_ret is None:
                return None
            if isinstance(raw_ret, str):
                return_obj = json.loads(raw_ret)
            else:
                return_obj = raw_ret
        except Exception as e:
            sdk_logger.error("json.loads exception:%S", raw_ret, exc_info=True)

        try:
            if isinstance(return_obj, list) and len(return_obj) > 0 and isinstance(return_obj[0], dict):
                return_obj = return_obj[0].copy()  # type: dict
        except Exception as ex:
            sdk_logger.error("return_obj exception:%S", return_obj, exc_info=True)

        try:
            code = None
            code = get_value(return_obj, 'code')
            if code and code != 0:
                msg = get_value(return_obj, 'msg')
                sdk_logger.error('function=%s, code=%s, msg=%s, raw=%s', func.__name__, code, msg, raw_ret)
                # if code == 107:
                #     logger.info(args)
                #     logger.info(kwargs)
                # 6 WebIce网关掉线， 107，用户没有注册, 108, 网关不存在
                if code in[6, 107, 108]:
                    sig_kill()
                    sys.exit(-1)
                # else:
                #     logger.error('function=%s, code=%s, msg=%s, raw=%s', func.__name__, code, msg, raw_ret)
        except (RequestNotAuthError, NoWebSerError, SelfOfflineError, ObjectOfflineError, GatewayNotExistError, UnknownError) as ex:
            sdk_logger.error("Response exception", exc_info=True)
            sig_kill()
            sys.exit(-1)
        except Ice.Exception as ex:
            sdk_logger.error("Ice exception", exc_info=True)
            sig_kill()
            sys.exit(-1)
        except ValueError as ex:
            sdk_logger.error("ValueError exception", exc_info=True)
            sig_kill()
            sys.exit(-1)
        except Exception as ex:
            sdk_logger.error("UnknownError exception", exc_info=True)

        return raw_ret

    return _service_monit


def point_run_time(app=None):
    """计算接口处理时间，并上报到日志平台

    :type app: str
    :param app: 应用名称, 默认自己获取
    :rtype: function
    """

    def _point_run_time(func):

        def processingTime(*args, **kwargs):
            return func(*args, **kwargs)
        return processingTime
    return _point_run_time


def point_run_time2(app=None):
    """计算接口处理时间，并上报到日志平台

    :type app: str
    :param app: 应用名称, 默认自己获取
    :rtype: function
    """

    def _point_run_time(func):

        def processingTime(*args, **kwargs):
            local_time = time.time()
            response_trace = None  # type: Exception
            response_status = None  # type: str
            ex = None
            r = None
            try:
                r = func(*args, **kwargs)  # type: function
            except Exception as _ex:
                ex = _ex
                response_status = _ex.__class__.__name__
                response_trace = _ex.__str__()
            if func.__name__ == '_service_monit':
                if ex:
                    raise ex
                else:
                    return r
            try:
                if r is None:
                    pass
                else:
                    if isinstance(r, dict):
                        if 'code' in r:
                            response_status = r.get('code')
                        if response_status is not None and response_status != 0 and 'msg' in r:
                            response_trace = r.get('msg')
                    elif isinstance(r, object):
                        if hasattr(r, 'code'):
                            response_status = getattr(r, 'code', None)
                        if response_status is not None and response_status != 0 and hasattr(r, 'msg'):
                            response_trace = getattr(r, 'msg')
                    else:
                        sdk_logger.info('%s, %s', type(r), r)
            except Exception as _ex:
                traceback.print_exc()
            handle_time = time.time() - local_time
            obj = args[0]  # type: object
            func_code = func.func_code
            filepath = func_code.co_filename.replace(os.getcwd() + os.sep, '').replace(os.sep, '/')
            filename = os.path.basename(func_code.co_filename)
            fileline = func_code.co_firstlineno
            tag = '%s.%s' % (obj.__class__.__name__, func.__name__)
            extra = dict()
            if obj.__class__.__name__ in ['CallbackI', 'IceService'] and func.__name__ == 'syncPubMsg':
                total = 0
                try:
                    points = json.loads(kwargs['points'])
                except KeyError:
                    points = json.loads(args[1])
                extra = dict(size=0, avg=0)
                for node in points:
                    devices = node['properties']  # type: dict
                    for v in devices.values():
                        total += len(v['data'])
                extra['size'] = total
                extra['avg'] = handle_time / total

            sdk_logger.debug('-> %s:%s -> %s.%s：%.3f, %s', filename, fileline, obj.__class__.__name__,
                         func.__name__,
                         handle_time, extra)

            if func_code.co_filename.find('iotos_sdk') > -1:
                app = 'iotos_sdk_v2'
            else:
                app = 'iotos_sdk_v1'
            try:
                if logService:
                    logService.put(
                        logC=LogC(app=app, filepath=filepath, fileline=fileline, handle_time=handle_time, tag=tag,
                                  extra=extra,
                                  group=logService.group,
                                  response_status=response_status,
                                  response_trace=response_trace.__str__()))
            except Exception as lex:
                sdk_logger.error("", exc_info=True)
            if ex is None:
                return r
            else:
                raise ex

        return processingTime

    return _point_run_time


try:
    _unicode = unicode
except NameError:
    def _unicode(value='', encoding=None, errors='strict'):
        return str(value)


# code=0返回空
# 统一检查返回结果，非零报异常
def error_check(result):
    if isinstance(result, dict):
        result = Result(**result)

    if result.code == 0:
        return
    if result.code == ErrorEnum.RequestNotAuth.value:
        raise RequestNotAuthError(result.__str__())
    elif result.code == ErrorEnum.NoWebSer.value:
        raise NoWebSerError(result.__str__())
    elif result.code == ErrorEnum.SelfOffline.value:
        raise SelfOfflineError(result.__str__())
    elif result.code == ErrorEnum.ObjectOffline.value:
        raise ObjectOfflineError(result.__str__())
    elif result.code == ErrorEnum.GatewayNotExist.value:
        raise GatewayNotExistError(result.__str__())
    elif result.code == ErrorEnum.DeviceNotExist.value:
        raise DeviceNotExistError(result.__str__())
    elif result.code == ErrorEnum.DataNotExist.value:
        raise DataNotExistError(result.__str__())
    raise UnknownError(result.__str__())


# 通信服务异常统一检查处理函数
def ice_ecxception_check(ice_exception, ice_service):
    if ice_exception.ice_name() in [IceExceptionEnum.CommunicatorDestroyedException.value]:
        # 致命异常，需要重启通信服务
        sdk_logger.warning("通信服务连接断开,准备重新连接:%s", ice_exception.__class__.__name__)
        ice_service.login()
        sdk_logger.warn("通信服务连接断开,重新连接成功:%s", ice_exception.__class__.__name__)
    elif ice_exception.ice_name() in [IceExceptionEnum.ConnectTimeoutException.value,
                                      IceExceptionEnum.TimeoutException.value]:
        sdk_logger.warn("通信网络超时,非致命可忽略,等待网络恢复:%s", ice_exception.__class__.__name__)
    else:
        sdk_logger.warn("通信未知异常:%s", ice_exception.__class__.__name__)


def for_data(data):
    for k, v in data.items():
        if isinstance(v, object) and hasattr(v, '__dict__'):
            data[k] = for_data(v.__dict__)
    return data


def to_dict(obj):
    return for_data(obj)


def loop_stop(sig, action):
    try:
        os.kill(os.getpid(), signal.SIGKILL)
        sys.exit(-1)
    except AttributeError:
        sys.exit(-1)
    except:
        sdk_logger.error("", exc_info=True)


signal.signal(signal.SIGINT, loop_stop)