# coding=utf-8
import Glacier2
import requests
import sys
import os
import json
from routelib.Callback_ice import *
from Ice_Identity_ice import *
import threading
import traceback
import time
from urllib3.exceptions import ResponseError
from library.log_trace import LogTrace
from library.iotos_util import sdk_logger as logger
from library import iotos_util
from library.iotos_util import point_run_time
from library.iotos_util import service_monit

from library.dto import WebLoginParam, Result, LoginResp, Heartbeat
from library.iotos_util import error_check


class PubThread(threading.Thread):
    _self = None
    tmp = Glacier2.RouterPrx

    def setMonitor(self, obj):
        self.tmp = obj

    def run(self):
        self.tmp.refreshSession()
        time.sleep(5)


def Ice_connent(communicator, CallbackReceiverI, uuidsession, ex_type, server_ip, server_port, _logger=None):
    raise NotImplementedError()
    username = "adminfrtttf"
    password = "sdfsdfsdfsdf"

    defaultRouter = communicator.stringToProxy("DemoGlacier2/router:ssl -p 4064 -h " + server_ip)
    router = Glacier2.RouterPrx.uncheckedCast(defaultRouter.ice_secure(True))
    try:
        session = router.createSession("IOTCC", "iotccpasword")  # 创建基于密码方式的session
        category = router.getCategoryForClient()
    except Exception as e:
        traceback.print_exc()
        try:
            communicator.destroy()
            communicator.waitForShutdown()
        except Exception as ex:
            traceback.print_exc(ex)

        raise Exception("通信服务创建失败")

    acmTimeout = router.getACMTimeout()
    if acmTimeout > 0:
        conn = router.ice_getCachedConnection()

        adapter = communicator.stringToProxy("iotroute:tcp -h %s -p %s" % (server_ip, server_port))

        prx = CallbackPrx.uncheckedCast(adapter)

        iotrouteWebSer = communicator.stringToProxy("iotrouteWebSer:tcp -h %s -p %s" % (server_ip, server_port))
        prxWebSer = CallbackForWebSerPrx.uncheckedCast(iotrouteWebSer)

        communicator.setDefaultRouter(router)

        adapter2 = communicator.createObjectAdapter(
            "")  # communicator.createObjectAdapterWithRouter("Callback.Client", router);

        ident = Ice.Identity()
        ident.name = Ice.generateUUID()
        ident.category = ""

        ident_data = Ice.Identity()
        ident_data.name = Ice.generateUUID()
        ident_data.category = ""

        callbackReceiverI = CallbackReceiverI
        adapter2.add(callbackReceiverI, ident)

        adapter2.activate()
        prx.ice_getConnection().setAdapter(adapter2)
        prx.addClient(uuidsession, ident)
        pt = PubThread()
        pt.setMonitor(router)
        pt.setDaemon(True)
        pt.start()

        if ex_type:
            return prx, communicator
        return prx, prxWebSer


class IceService(object):
    webLoginParam = WebLoginParam(None, None, None, None)
    callBackReceiver = None
    # 心跳时间
    __heartbeatTime = 60

    @property
    def heartbeatTime(self):
        return self.__heartbeatTime

    __routerPrx = None

    @property
    def routerPrx(self):
        return self.__routerPrx

    __callbackPrx = None
    __prxWebSer = None

    @property
    def callbackPrx(self):
        return self.__callbackPrx

    __communicator = Ice.initialize()

    # return Ice.initialize
    @property
    def communicator(self):
        return self.__communicator

    @property
    def uuid(self):
        return self.webLoginParam.uuid

    # 统一管理，方便重新登录更新此值
    __uuidSession = None

    @property
    def uuidSession(self):
        return self.__uuidSession

    def __init__(self):
        self.webLoginParam = None
        self.callBackReceiver = None
        self.__communicator = None
        self.__prxWebSer = None
        self.__callbackPrx = None
        self.__routerPrx = None

    def login(self, webLoginParam=None, callBackReceiver=None):
        if (webLoginParam is None and callBackReceiver is None) is False:
            self.webLoginParam = webLoginParam
            self.callBackReceiver = callBackReceiver
        assert self.webLoginParam is None or "webLoginParam is None"
        assert self.callBackReceiver is None or "callBackReceiver is None"
        loginResp = self.loginWeb()
        self.destroy()
        self.__get_communicator()
        self.__ice_connent(loginResp.router_config, self.callBackReceiver)
        return loginResp

    def __ice_connent(self, router_config, callBackReceiver):
        username = "adminfrtttf"
        password = "sdfsdfsdfsdf"

        stringToProxy = "DemoGlacier2/router:ssl -p 4064 -h " + router_config.iotrouterIP

        defaultRouter = self.__communicator.stringToProxy(str(stringToProxy))
        router = Glacier2.RouterPrx.uncheckedCast(defaultRouter.ice_secure(True))
        try:
            session = router.createSession("IOTCC", "iotccpasword")  # 创建基于密码方式的session
            category = router.getCategoryForClient()
        except Exception as e:
            traceback.print_exc()
            self.destroy()
            raise Exception("通信服务创建失败")

        acmTimeout = router.getACMTimeout()
        if acmTimeout > 0:
            conn = router.ice_getCachedConnection()
            stringToProxy = ("iotroute:tcp -h %s -p %s" % (router_config.iotrouterIP, router_config.remoteAdapterPort))
            adapter = self.communicator.stringToProxy(str(stringToProxy))

            prx = CallbackPrx.uncheckedCast(adapter)

            stringToProxy = "iotrouteWebSer:tcp -h %s -p %s" % (
            router_config.iotrouterIP, router_config.remoteAdapterPort)
            iotrouteWebSer = self.communicator.stringToProxy(str(stringToProxy))
            self.__prxWebSer = CallbackForWebSerPrx.uncheckedCast(iotrouteWebSer)

            self.communicator.setDefaultRouter(router)

            adapter2 = self.communicator.createObjectAdapter(
                "")  # communicator.createObjectAdapterWithRouter("Callback.Client", router);

            ident = Ice.Identity()
            ident.name = Ice.generateUUID()
            ident.category = ""

            ident_data = Ice.Identity()
            ident_data.name = Ice.generateUUID()
            ident_data.category = ""

            callbackReceiverI = callBackReceiver
            adapter2.add(callbackReceiverI, ident)

            adapter2.activate()
            prx.ice_getConnection().setAdapter(adapter2)
            prx.addClient(self.uuidSession, ident)
            pt = PubThread()
            pt.setMonitor(router)
            pt.setDaemon(True)
            pt.start()
            self.__routerPrx = router
            self.__callbackPrx = prx

    @point_run_time()
    def loginWeb(self, webLoginParam=None):
        if webLoginParam is None:
            webLoginParam = self.webLoginParam
        else:
            self.webLoginParam = webLoginParam
        assert webLoginParam is None or "web登录信息不能为空"
        data = {'username': webLoginParam.username, 'psw': webLoginParam.password, 'uuid': webLoginParam.uuid}
        result = self.__post_requests(url=webLoginParam.httpHost + '/api/login', data=data)
        if result.logTrace:
            try:
                iotos_util.logService = LogTrace(httpHost=result.logTrace.httpHost)
                iotos_util.logService.group = '%s/%s/%s' % (
                result.router_config.iotrouterIP, webLoginParam.username, result.data[0]['name'])
            except Exception as ex:
                logger.error(u'读取日志追踪配置失败', exc_info=True)
        self.__uuidSession = result.data[0].get("tableId")
        self.__heartbeatTime = result.heartbeat
        # 如果传了host，那self.server_ip直接用host
        host = webLoginParam.httpHost # type: str
        if host:
            if host[-1] == "/":
                host = host[:-1]
            if host.startswith("http://"):
                host = host.replace("http://", '')
            if host.startswith("https://"):
                host = host.replace("https://", '')
            if len(host.split(":")) > 1:
                host = host.split(":")[0]
            result.router_config.iotrouterIP = host
        return result

    @point_run_time()
    @service_monit
    def sendMsg(self, toUuidSession, data):
        return self.__callbackPrx.sendMsg(self.uuidSession, toUuidSession, data)

    @point_run_time()
    @service_monit
    def addClient(self, uuidSession, callbackIdent):
        return self.__callbackPrx.addClient(self.uuidSession, callbackIdent)

    @point_run_time()
    @service_monit
    def subMsg(self, points):
        return self.__callbackPrx.subMsg(points)

    @point_run_time()
    @service_monit
    def syncPubMsg(self, points):
        retJson = self.__callbackPrx.syncPubMsg(self.uuidSession, points)
        result = json.loads(retJson)
        if isinstance(result, list):
            if len(result) != 1:
                raise ValueError("返回数据结构异常:" + retJson)
            for r in result:
                r = Result(**r)
                error_check(r)
            return result[0]
        else:
            result = Result(**result)
            error_check(result)
            return result.to_dict()

    @service_monit
    def alarm(self, points):
        return self.alarm(self.uuidSession, points)

    # @service_monit
    def logout(self):
        return self.__callbackPrx.logout(self.uuidSession)

    @point_run_time()
    def getTableDetail(self):
        return self.__callbackPrx.getTableDetail(self.uuidSession)

    def deleteTable(self):
        return self.deleteTable(self.uuidSession)

    def updateTable(self, tableJsonData):
        return self.updateTable(self.uuidSession, tableJsonData)

    def getDeviceData(self, points):
        return self.__callbackPrx.getDeviceData(self.uuidSession, points)

    def getPlatformData(self, points):
        return self.__callbackPrx.getPlatformData(self.uuidSession, points)

    @point_run_time()
    @service_monit
    def devOnline(self, devId):
        return self.__callbackPrx.devOnline(self.uuidSession, devId)

    @point_run_time()
    @service_monit
    def webHeartbeat(self):
        retJson = None
        try:
            retJson = self.__callbackPrx.devOnline(self.uuidSession, 'webHeartbeat')
            result = json.loads(retJson)
            result = Result(**result)
            error_check(result)
            self.__routerPrx.refreshSession()
        except Exception as e:
            logger.error(u"数据解析异常：%s", retJson)
            raise e
        return result

    @point_run_time()
    @service_monit
    def devOffline(self, devId):
        return self.__callbackPrx.devOffline(self.uuidSession, devId)

    @point_run_time()
    @service_monit
    def heartbeat(self):
        retJson = None
        try:
            retJson = self.__callbackPrx.heartbeat()
            result = json.loads(retJson)
            result = Heartbeat(**result)
            error_check(result)
            self.__routerPrx.refreshSession()
        except Exception as e:
            logger.error(u"数据解析异常：%s", retJson)
            raise e
        return result

    @point_run_time()
    @service_monit
    def refreshSession(self):
        return self.__routerPrx.refreshSession()

    # 网络请求
    @service_monit
    def __post_requests(self, url, data):
        url_path = url
        req = None
        try:
            req = requests.post(url_path, data=data)
            if req.status_code != 200:
                raise ResponseError(req)
            result = req.json()
        except Exception as e:
            if req is not None:
                logger.error(u'返回错误:%s', req.content)
            else:
                logger.error(u'返回错误', exc_info=True)
            raise e
        return LoginResp(**result)

    def __get_communicator(self):
        initData = Ice.InitializationData()
        initData.properties = Ice.createProperties(sys.argv)
        initData.properties.setProperty("Ice.Plugin.IceSSL", "IceSSL:createIceSSL")
        initData.properties.setProperty("IceSSL.DefaultDir", os.getcwd() + "/certs")
        initData.properties.setProperty("IceSSL.CAs", "cacert.pem")
        initData.properties.setProperty("IceSSL.CertFile", "client.p12")
        initData.properties.setProperty("IceSSL.Password", "password")
        initData.properties.setProperty("IceSSL.Keychain", "client.keychain")
        initData.properties.setProperty("IceSSL.KeychainPassword", "password")
        initData.properties.setProperty("Ice.ACM.Server", "0")
        initData.properties.setProperty("Ice.ACM.Client", "0")
        initData.properties.setProperty("Ice.Override.ConnectTimeout", "10000")
        initData.properties.setProperty("Ice.Override.Timeout", "30000")
        initData.properties.setProperty("Ice.ThreadPool.Client.Size", "2")
        initData.properties.setProperty("Ice.ThreadPool.Client.SizeMax", "10")
        initData.properties.setProperty("Ice.MessageSizeMax", "10240")
        self.__communicator = Ice.initialize(sys.argv, initData)
        return self.__communicator

    # 全局销毁ICE服务进程
    def destroy(self, communicator=None):
        if communicator is not None:
            self.__communicator = communicator

        if self.communicator is None:
            return
        try:
            self.communicator.destroy()
        except Exception as e:
            pass
            # logger.warn(u"销毁通信服务:%s", e.__class__.__name__)

        try:
            self.communicator.waitForShutdown()
        except Exception as e:
            pass
            # logger.warn(u"销毁通信服务:%s", e.__class__.__name__)

        del self.__communicator
        del communicator


if __name__ == '__main__':
    loginParam = WebLoginParam(username="test", password='123456', httpHost='http://192.168.189.128:8000',
                               uuid='941958b2beb411ebb37e000c293f95db')
    iceService = IceService()
    result = iceService.loginWeb(webLoginParam=loginParam)

    print (iceService.uuid)
    print (iceService.uuidSession)
