# coding=utf-8
from library.dto import WebLoginParam
from library.exception import RequestNotAuthError, SelfOfflineError, NoWebSerError
from library.iotos_util import error_check, ice_ecxception_check, _unicode
from routelib import ice_connent
from routelib.Callback_ice import *
from routelib.ice_connent import IceService
from routelib.jlib import *
from library.iotos_util import point_run_time
import time
import uuid as _uuid
import requests
import json
import sys
import Ice
import os
import threading
import copy
import traceback
from library.iotos_util import sig_kill, service_monit

device_dir = os.path.join(os.path.dirname(os.getcwd()), '_drivers')
sys.path.append(device_dir)


# 心跳维持
class HeartBeatThread(threading.Thread):
    __iceService = IceService()
    name = u'通信SDK心跳服务'

    @property
    def server_time(self):
        return self.__iceService.heartbeat

    def __init__(self, iceService, server_time):
        super(HeartBeatThread, self).__init__()
        logger.info('start...')
        self.__iceService = iceService
        self.sync_time(server_time)

    def sync_time(self, server_time):
        # 路由心跳中时间周期同步，相差60s时进行本地与服务器对时
        try:
            if time.time() - server_time > 60:
                date_str = 'date ' + time.strftime("%Y-%m-%d", time.localtime(server_time))
                time_str = 'time ' + time.strftime("%H:%M:%S", time.localtime(server_time))
                os.system(date_str)
                os.system(time_str)
        except Exception as ex:
            # 忽略操作系统平台
            pass

    # 心跳维持
    def run(self):

        while 1:
            try:
                time.sleep(5)
                resultDto = self.__iceService.heartbeat()
                logger.debug(u"路由心跳:%s", resultDto)
                # resultDto = self.__iceService.webHeartbeat()
                # logger.debug(u"WebIce心跳:%s", resultDto)
                self.__iceService.refreshSession()
            except Ice.Exception as ex:
                ice_ecxception_check(ice_exception=ex, ice_service=self.__iceService)
            except SelfOfflineError as ex:
                logger.warning("通信服务断开，准备重连...")
                res = self.__iceService.login()
                logger.warning("通信服务断开，重连成功. retsult:%s", res.__str__())
            except Exception as e:
                logger.error(u"心跳 error:%s", e.__class__.__name__)


def driver_manage(func):
    """驱动管理"""

    def _driver_manage(self, ZMIotLib, iceService, event, devid):
        """

        @type self: RunCollectingThread
        @param ZMIotLib:
        @param iceService:
        @param event:
        @param devid:
        @return:
        """
        try:
            new_obj = func(self, ZMIotLib, iceService, event, devid)  # type: RunCollectingThread
            # device_name = self.zm.m_dev2attrs[devid]['name']
            # self.setName(u'%s_Driver' % (device_name))
            return new_obj
        except Exception as ex:
            raise ex

    return _driver_manage


# 设备驱动/业务插件 接口类
class RunCollectingThread(threading.Thread, JLib):
    __iceService = IceService

    @property
    def iceService(self):
        return self.__iceService

    @driver_manage
    def __init__(self, ZMIotLib, iceService, event, devid):
        threading.Thread.__init__(self)
        JLib.__init__(self)
        self.zm = ZMIotLib
        self.__iceService = iceService
        self.threadEvent = event
        self.devid = devid
        devCfg = self.zm.m_dev2attrs[self.devid]['config']
        self.proxyIndex2DataId = {}
        self.collecting_continuous_failed_count = 0

        device_name = self.zm.m_dev2attrs[devid]['name']
        self.setName(u'%s_Driver' % (device_name))

        try:
            # 实例化设备驱动
            driverInstance = None
            if 'driver' in devCfg:
                nameGroupTmp = devCfg['driver'].split('.')
                importcfg = (nameGroupTmp[0]).split("/")
                if importcfg != '' and importcfg[0] == 'python':
                    try:
                        m = __import__(importcfg[1])  # 注意，模块在子目录中，与当前py主脚本不再同一目录下，需要这样！
                        drtmp = getattr(m, nameGroupTmp[1])
                        driverInstance = drtmp()  # 根据类再要创建实例！
                        driverInstance.zm = self.zm
                        driverInstance.sysId = devid.split('.')[1]
                        driverInstance.sysAttrs = self.zm.m_dev2attrs[devid]

                        for point in self.zm.m_dev2points[devid]:
                            dataIdtmp = point.split('.')[2]
                            attrtmp = self.zm.m_point2attrs[point]
                            attrtmp['memoryvalue'] = attrtmp['value']
                            driverInstance.data2attrs.update({dataIdtmp: attrtmp})
                            driverInstance.name2dataId.update({attrtmp['name']: dataIdtmp})
                            driverInstance.data2subs.update({dataIdtmp: self.zm.m_point2subs[point]})

                        # 设备驱动（通信）初始化，改放到了线程中!
                        # driverInstance.InitComm()  									# 调用类的成员！！
                        self.zm.m_dev2driver.update({devid: driverInstance})
                    # print self.zm.m_dev2driver
                    except Exception as e:
                        traceback.print_exc()
                        pass
                else:
                    print(u'device' + devid + u'config error!')
            else:
                print(u'device' + devid + u'no driver found!')

        except Exception as e:
            traceback.print_exc()
            pass

    def stop(self):
        self.zm.eventcount = self.zm.eventcount - 1
        if self.zm.eventcount < 0:
            self.zm.eventcount = 0
        self.stopt = False

    def run(self):
        while True:
            try:  
                self.zm.eventcount = self.zm.eventcount + 1
                if self.devid in self.zm.m_dev2driver:
                    self.stopt = True
                    drtmp = self.zm.driver(self.devid)
                    attrstmp = drtmp.sysAttrs
                    attrstmp.update({'data': drtmp.data2attrs})
                    try:
                        drtmp.InitComm(attrstmp)
                    except Exception as dr_ex:
                        logger.error(u'%s,驱动初始化异常', attrstmp['name'], exc_info=True)
                        sig_kill()
                        sys.exit(-1)
                    while True:
                        if self.stopt == False:
                            logger.warn(u'采集线程检测到标记，准备退出! ' + drtmp.sysId)
                            break
                        self.m_dev2points_copy = copy.deepcopy(self.zm.m_dev2points)
                        data_id_list = self.m_dev2points_copy[self.devid]
                        for point_id in data_id_list:
                            if self.zm.restor_collect:
                                break
                            while drtmp.pauseCollect:
                                pass

                            dataId = point_id.split('.')[2]

                            try:
                                refreshCycletmp = int(drtmp.data2attrs[dataId]['refreshcycle']) / 1000.0
                                if refreshCycletmp:
                                    logger.info(u'----------	 according to config, will sleep for ' + str(
                                        refreshCycletmp) + 's ... 	--------------')
                                    time.sleep(refreshCycletmp)
                                if 'disabled' in drtmp.data2attrs[dataId]['config']:
                                    if drtmp.data2attrs[dataId]['config']['disabled'] == True:
                                        self.warn('data disabled: ' + dataId + '\n')
                                        continue
                            except Exception as e:
                                raise e
                                traceback.print_exc(e)

                            valret = drtmp.Collecting(dataId)
                            try:
                                if valret is not None and len(valret):  # 否则，返回值为None或空()
                                    self.collecting_continuous_failed_count = 0  # 设备采集正常返回，复位连续采集错误计数
                                    if len(valret) == 1:  # 返回一个值，就调用pubMsg()
                                        rettmp = drtmp.setValue(drtmp.name(dataId), valret[0])
                                        error_check(rettmp)
                                    else:  # len(valret) >= 2:					#返回多个值，就调用pubMsgs()
                                        self.info('pub mutiple data...')
                                        value_list = []  # 要批量上报的值结构，其中返回的值元组中第一个就是采集点自身的值，所以先append走一个！
                                        value_list.append({'id': drtmp.pointId(dataId), 'value': valret[0]})
                                        for i in range(1, len(
                                                valret)):  # 遍历每个值，去找被代理的数据点，注意去掉起始点，因为规定默认第一个值就是采集点（代理其他点采集值的）自身的值！
                                            id_tobe_find_tmp = ''
                                            proxyedId = dataId + '.' + str(i)
                                            if proxyedId in self.proxyIndex2DataId.keys():  # 如果此前有记录对应这个
                                                id_tobe_find_tmp = self.proxyIndex2DataId[proxyedId]
                                            else:
                                                for idtmp, attrtmp in drtmp.data2attrs.items():
                                                    try:
                                                        proxyId = attrtmp['config']['proxy']['pointer']
                                                        if proxyId == dataId:  # 遍历到当前数据点的proxy.pointer是当前采集的点，那么就是说返回的值有他被代理的一份！！
                                                            indexId = attrtmp['config']['proxy']['index']
                                                            tmpid = dataId + '.' + str(indexId)
                                                            if tmpid not in self.proxyIndex2DataId.keys():  # 如果目前这个点的代理id在记录中，那么肯定不是要找的点，因为前面查过！如果不在，那么可能是要找的，也可能是被代理的兄弟点，总之先保存记录“包裹”领了再说！
                                                                self.proxyIndex2DataId[tmpid] = idtmp
                                                                if int(
                                                                        indexId) == i:  # 再来判断当前点的代理索引index，如果和采集点返回的数字元组的索引对应，那么就是他了！
                                                                    id_tobe_find_tmp = idtmp
                                                                    break
                                                    except Exception as e:
                                                        self.warn(u"忽略" + idtmp, e)
                                                        continue
                                            if id_tobe_find_tmp != '':
                                                value_list.append(
                                                    {'id': drtmp.pointId(id_tobe_find_tmp), 'value': valret[i]})
                                            else:
                                                self.error(u'未找到批量返回值对应的数据点：' + dataId + "." + str(i))
                                        jsmsg = []
                                        self.info('pub multiple datas...')
                                        rettmp = json.loads(drtmp.setValues(value_list)) 
                                        if type(rettmp).__name__ == 'dict':
                                            tmp = []
                                            tmp.append(json.loads(drtmp.setValues(value_list)))
                                            rettmp = tmp
                                        iserror = False
                                        if type(rettmp).__name__ == 'list':
                                            for item in rettmp:
                                                for key, value in item.items():
                                                    if key == 'msg':
                                                        jsmsg.append(value)
                                        else:
                                            iserror = True
                                            jsmsg = rettmp
                                        # self.info(json.dumps(jsmsg) + '\n')
                                        self.info('\r\n')
                                        if iserror:
                                            self.zm.exit_to_reboot()
                                            continue
                                elif valret == None:
                                    self.collecting_continuous_failed_count += 1
                                    logger.warn(u'连续采集错误计数 ' + str(self.collecting_continuous_failed_count))
                                    if self.collecting_continuous_failed_count >= 30:
                                        logger.warn(u'连续采集错误超过限定次数（30）,将复位采集引擎！')
                                        self.zm.exit_to_reboot()

                            except NoWebSerError as e:
                                logger.debug(u"等待WebICE重启")
                                continue
                            except RequestNotAuthError as e:
                                self.iceService.loginWeb()
                            except SelfOfflineError as e:
                                self.iceService.login()
                            except Ice.SocketException as e:
                                # 可以忽略网络类异常
                                logger.warning(u"网络类异常:%s", e.__class__.__name__)
                            except Ice.Exception as e:
                                ice_ecxception_check(ice_exception=e, ice_service=self.__iceService)
                            except Exception as e:
                                logger.warning(u"未知异常:%s", e.__class__.__name__, exc_info=True)
                                raise e
                        if drtmp.collectingOneCircle:
                            break
                    if drtmp.collectingOneCircle:
                        logger.warning(u'单次遍历完毕，采集循环退出！')
                        break
                else:
                    raise Exception(u'设备驱动实例不存在！')
                    time.sleep(60)
                    self.zm.exit_to_reboot()
            except Exception as e:
                traceback.print_exc()
                raise e

class WebSessionRefreshThread(threading.Thread):
    iceService = None
    log = None
    serverTime = None

    def __init__(self, iceService):
        super(WebSessionRefreshThread, self).__init__()
        self.iceService = iceService
        self.serverTime = time.time()
        self.log = logger

    def run(self):
        while True:
            try:
                time.sleep(25 * 60)
                while True:
                    loginResp = None
                    try:
                        loginResp = self.iceService.loginWeb()
                        if loginResp.code != 0:
                            logger.error(u"刷新 web session error, time:%s, ret:%s",
                                         (time.time() - self.serverTime) / 60, loginResp)
                            time.sleep(5)
                        else:
                            logger.warn(u"刷新 web session successful, time:%s, ret:%s",
                                        (time.time() - self.serverTime) / 60, loginResp)
                            break
                    except Exception as e:
                        traceback.print_exc(e)
                        logger.error(u"刷新 web session error, time:%s, ret:%s", (time.time() - self.serverTime) / 60,
                                     loginResp)
                        time.sleep(5)

            except Exception as ex:
                traceback.print_exc(ex)


class IOTOSys(CallbackReceiver, JLib):
    iceService = IceService()
    webSessionRefreshThread = None

    @property
    def uuidsession(self):
        return self.iceService.uuidSession
    m_table = None  # type: dict
    def __init__(self):
        CallbackReceiver.__init__(self)
        JLib.__init__(self)
        self.m_devlist = []
        self.m_dev2attrs = {}
        self.m_dev2points = {}
        self.m_point2attrs = {}
        self.m_point2subs = {}
        self.m_dev2driver = {}
        self.devsId = []
        self.m_table = None
        self.s_name = ''
        self.uuid = ''
        self.http_host = ''
        self.server_time = ''
        self.comm = None
        self.communicator = None
        self.server_ip = None
        self.server_port = None
        self.username = ''
        self.password = ''
        self.hb = None
        self.strat_collect = True
        self.pause_collect = False 
        self.restor_collect = False
        self.strat_connect = True
        self.event = threading.Event()
        self.threading_list = []
        self.eventcount = 0
        self.iceService = IceService()
        self.webSessionRefreshThread = WebSessionRefreshThread(iceService=self.iceService)
        self.webSessionRefreshThread.start()

    @property
    def prx(self):
        return self.iceService.callbackPrx

    # 上传驱动
    class DriveUploadFile(threading.Thread):
        def __init__(self, drive_file, drive_id, device_id):
            super(DriveUploadFile, self).__init__()
            self.drive_file = drive_file
            self.drive_id = drive_id
            self.device_id = device_id

        def run(self):
            r = requests.post(self.http_host + "/backstage/drive_upload/",
                              files={'content': open(self.drive_file, 'rb')},
                              data={'drive_id': self.drive_id, 'device_id': self.device_id})

    # 下载驱动
    class DriveDownloadFile(threading.Thread):

        def __init__(self, drive_file_url):
            super(DriveDownloadFile, self).__init__()
            self.drive_file_url = drive_file_url

        def run(self):
            down_url = self.http_host + self.drive_file_url
            filename = self.drive_file_url.split("/")[-1]
            r = requests.get(down_url)
            if r.status_code == 200:
                with open(device_dir + "/" + filename, 'wb') as f:
                    f.write(r.content)

    # locked = False
    def exit_to_reboot(self, msg=''):
        self.Logout()
        sig_kill()
        sys.exit(-1)

    def driver(self, devid):
        return self.m_dev2driver[devid]

    def callback(self, fromUuid, data, current=None):
        if self.m_table is None:
            logger.error(U'SDK未初始化完成,')
            return json.dumps(dict(code=1, msg=u'SDK未初始化完成', data=None))
        run_time = time.time()
        ex = None
        rs = None
        try:
            rs = self.__callback(fromUuid, data, current)
            logger.info('time:%.4f', time.time() - run_time)
        except Exception as _ex:
            ex = _ex
            logger.error('time:%.4f', time.time() - run_time, exc_info=True)
        if ex:
            raise ex
        return rs

    def __callback(self, fromUuid, data, current=None):
        info = json.loads(data)
        info_type = info['type']
        result = {'code': 0, 'msg': 'OK', 'data': info}
        if self.prx:
            # 连接网络，连接复位
            if info_type == "ioServerConnectServer" or info_type == "ioServerReConnectServer":
                self.strat_connect = True

            if self.strat_connect == False:
                return json.dumps({'code': 101, 'msg': 'Network disconnection', 'data': info})
            # 断开网络
            if info_type == "ioServerDisconnectServer":
                self.strat_connect = False

            # 启动采集，停止采集，采集复位
            if info_type == "devStartCollect":
                self.strat_collect = True
                self.pause_collect = False
                self.restor_collect = False
                self.event.set()

            if info_type == "devPauseCollect":
                self.strat_collect = False
                self.pause_collect = True
                self.restor_collect = False

            if info_type == "devResetCollect":
                self.strat_collect = False
                self.pause_collect = False
                self.restor_collect = True

            # 主要是m_dev2driver[devid]可能空
            if self.strat_collect:

                if info_type == "getData" or info_type == "setData" or info_type == "syncPubMsg":

                    points = info['body']
                    ionode_id = points["id"]
                    device_id = None
                    data_id = None
                    request_id = None
                    request_time = None
                    try:
                        request_id = points['request_id']
                        request_time = points['request_time']
                    except KeyError:
                        pass
                        #logger.error("", exc_info=True)

                    try:
                        for i, j in points["properties"].items():
                            device_id = i
                            data_id = list(j["data"].keys())[0]

                        point = ionode_id + '.' + device_id + '.' + data_id
                        devid = ionode_id + '.' + device_id
                        data_value = points["properties"][device_id]["data"][data_id]["value"]
                    except KeyError:
                        logger.error(info, exc_info=True)
                    # 读写属性
                    readwrite = None
                    val_type = None
                    # 获取点表详情来判断读写属性
                    logger.info(self.uuid == ionode_id)
                    point_detail_json = None
                    if self.uuid != ionode_id:
                        uuidsession = ionode_id + "?" + self.uuidsession.split("?")[1]
                        point_detail = self.prx.getTableDetail(uuidsession)
                        point_detail_json = json.loads(point_detail)
                        if int(point_detail_json["code"]) != 0:
                            return point_detail
                        point_detail_json = point_detail_json['data'].copy()
                    else:
                        point_detail_json = self.m_table

                    try:
                        readwrite = point_detail_json["properties"][device_id]["data"][data_id]["readwrite"]
                        val_type = point_detail_json["properties"][device_id]["data"][data_id]["valuetype"]
                    except KeyError:
                        logger.error(info, exc_info=True)

                    if info_type == "getData":
                        if int(readwrite) == 2:
                            return json.dumps({"code": 515, "msg": "PropertyNotValid", "data": None})
                        try:
                            result = self.driver(devid).Event_getData(data_id, data_value)
                            # 检查用户返回格式
                            ret = self._ret(result)
                            ret_info = json.loads(ret)
                            if int(ret_info["code"]) != 0:
                                return json.dumps(ret_info)

                            result = self._cmd_data(point, result)
                        except Exception as e:
                            raise e
                    if info_type == "setData":
                        if int(readwrite) == 1:
                            return json.dumps({"code": 515, "msg": "PropertyNotValid", "data": None})
                        response_id = _uuid.uuid4().__str__().replace('-', '')
                        response_time = time.time()
                        try:
                            result = self.driver(devid).Event_setData(data_id, data_value)
                        except Exception as ex:
                            logger.error(u'SDK调用设备下发失败', exc_info=True)
                            return json.dumps(dict(code=1, msg=u'SDK调用设备下发失败'))
                        try:
                            # 检查用户返回格式
                            ret = self._ret(result)
                            ret_info = json.loads(ret)
                            if int(ret_info["code"]) != 0:
                                result['request_id'] = request_id
                                result['request_time'] = request_time
                                result['response_id'] = response_id
                                result['response_time'] = response_time
                                return json.dumps(ret_info)

                            result = self._cmd_data(point, result)
                            if isinstance(result, dict) is False:
                                result = json.loads(result)
                            result['request_id'] = request_id
                            result['request_time'] = request_time
                            result['response_id'] = response_id
                            result['response_time'] = response_time
                            result = json.dumps(result)
                        except Exception as e:
                            logger.error("", exc_info=True)
                            raise e
                    if info_type == 'syncPubMsg':
                        # 如果存在config中的filter则过滤只要他
                        try:
                            cfg = self.m_dev2attrs[device_id]['config']['param']['filter']
                            for i in cfg:
                                io_id, de_id, da_id = cfg.split('.')
                                if de_id == '*':
                                    for did, devdr in self.m_dev2driver.items():
                                        if devdr is not None:
                                            result = self.driver(did).Event_syncPubMsg(point, data_value)
                                            # 检查用户返回格式
                                            ret = self._ret(result)
                                            ret_info = json.loads(ret)
                                            if int(ret_info["code"]) != 0:
                                                return json.dumps(ret_info)
                                else:
                                    if da_id == '*':
                                        result = self.driver(io_id + "." + de_id).Event_syncPubMsg(point, data_value)
                                    else:
                                        result = self.driver(io_id + "." + de_id).Event_syncPubMsg(
                                            io_id + "." + de_id + "." + da_id, data_value)

                        except Exception as e:
                            raise e
                            for did, devdr in self.m_dev2driver.items():
                                if devdr is not None:
                                    result = self.driver(did).Event_syncPubMsg(point, data_value)
                                    # 检查用户返回格式
                                    ret = self._ret(result)
                                    ret_info = json.loads(ret)
                                    if int(ret_info["code"]) != 0:
                                        return json.dumps(ret_info)

                        result = self._cmd_data(point, result)

                if info_type == 'notify':
                    body = info['body']
                    # web修改点的属性通知客户端下拉点表
                    if body['notify_type'] == 'data_update':
                        self.exit_to_reboot()

                    # 驱动发布通知客户端上传驱动
                    if body['notify_type'] == 'upload_drive':
                        language = body['language']
                        import_name = body['import_name']
                        drive_id = body['drive_id']
                        device_id = body['device_id']
                        if language != 'PYTHON':
                            result = {'code': 520, 'msg': 'Language error', 'data': None}
                        drive_file = os.path.dirname(os.getcwd()) + "/_drivers/" + import_name + ".py"
                        t = self.DriveUploadFile(drive_file, drive_id, device_id)
                        t.start()
                    # 通知接口主动下载
                    if body['notify_type'] == 'down_drive':
                        drive_file_url = body['drive_file_url']
                        t = self.DriveDownloadFile(drive_file_url)
                        t.start()

                if info_type == "sendMsg":
                    retArray = []
                    for did, devdr in self.m_dev2driver.items():
                        if devdr is not None:
                            retArray.append({did: devdr.Event_customBroadcast(fromUuid, info_type, info['body'])})
                    result['data'] = retArray

            return json.dumps(result)

    # 判断返回结果里面是否在value中存在cmd指令,存在则拿出来
    def _cmd_data(self, point, result):
        if type(result) != dict:
            point_data = json.loads(result)
        else:
            point_data = result
        point_data_json = point_data["data"]
        ionode_id, device_id, data_id = point.split(".")
        try:
            cmd = point_data_json['properties'][device_id]["data"][data_id]["value"]["_cmd"]
            data = point_data_json['properties'][device_id]["data"][data_id]["value"]["data"]
            del point_data_json['properties'][device_id]["data"][data_id]["value"]
            point_data_json['properties'][device_id]["data"][data_id]['_cmd'] = cmd
            point_data_json['properties'][device_id]["data"][data_id]['data'] = data
            result = {"code": point_data["code"], "msg": point_data["msg"], "data": point_data_json}
        except:
            pass
        return result

    def _get_communicator(self):
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
        self.communicator = Ice.initialize(sys.argv, initData)
        return self.communicator

    # 解析uuidsession
    def _loads_uuidSession(self):
        try:
            session = self.uuidsession.split('?')[1]
        except Exception as e:
            return ''
        return session.split("=")[1]

    # 网络请求
    @service_monit
    def _post_requests(self, url, data):
        url_path = self.http_host + url
        req = requests.post(url_path, data=data)
        result = req.json()
        return result

    # 解析数据
    def _get_point(self, idinfo, value="", timestamp=time.time(), auto_created=False):
        points = []
        ionode_uuid, device_oid, data_oid = idinfo.split(".")
        ionodes = {}
        devices = {}
        d = {}
        datas = {}

        if ionode_uuid == self.m_table['id'] or ionode_uuid == self.m_table['gateway_uuid']:
            if hasattr(self.m_table, 'pk'):
                ionodes['pk'] = self.m_table['pk']
        ionodes["id"] = ionode_uuid
        point = {"value": str(value), "timestamp": timestamp}
        if auto_created:
            point['auto_created'] = auto_created
        d[data_oid] = point
        datas["data"] = d
        devices[device_oid] = datas
        ionodes["properties"] = devices
        points.append(ionodes)
        return json.dumps(points)

    '''
        作者：lrq
        日期：20200409
        功能：当个的数据点jsons数组进行通个网关、同网关同设备进行合并，将某些数组元素合并到元素对象中去
        输入参数：如下格式的json数组
            [
                {
                    "id": "73eca5dc254d11eaa4fb000c2988ff06", 
                    "properties": {
                        "5d53ff0f": {
                            "data": {
                                "f551": {
                                    "timestamp": 1586408231.330443,
                                    "value": "339.0"
                                }
                            }
                        }
                    }
                },
            ]
      返回值：合并后的json数组
    修改记录：
    '''
    def _points_merged(self, pointsArr):
        mergedArr = []

        def has_uuid(uuid):  # mergedArr合并后数组中是否有指定接入点网关uuid，有则返回index索引，没有就是-1
            for index, item in enumerate(mergedArr):
                if item['id'] == uuid:
                    return index
            return -1

        def has_dev(uuidIndex, devid):  # 是否有指定的网关和设备id，有则返回true，没有就是false
            for key, value in mergedArr[uuidIndex]['properties'].items():
                if key == devid:
                    return True
            return False

        for point in pointsArr:
            uuidxtmp = point['id']
            devinfo = point['properties'].items()[0]  # items()返回元素key-value的元组列表
            # print(point['properties'][devinfo[0]])
            datainfo = point['properties'][devinfo[0]]['data'].items()[0]
            uuidIndex = has_uuid(uuidxtmp)
            if uuidIndex != -1:  # 合并数组中已经有了接入点网关id
                if has_dev(uuidIndex, devinfo[0]):
                    mergedArr[uuidIndex]['properties'][devinfo[0]]['data'][datainfo[0]] = datainfo[
                        1]  # 同网关、同设备下，数据点追加元素
                else:
                    mergedArr[uuidIndex]['properties'][devinfo[0]] = devinfo[1]  # 同网关不同设备下，追加设备
            else:  # 数组中没有这个id的，那么就整个加入到数组中，说明是新的
                mergedArr.append(point)
        return mergedArr

    # 初始链接
    def _init_connent(self):

        print("self.server_ip = ", self.server_ip)

        print("self.server_port = ", self.server_port)
        self.prx, self.comm = ice_connent.Ice_connent(self.communicator, self, self.uuid, False, self.server_ip,
                                                      self.server_port)

    # 递归补全
    def _ParseTableData(self, id, data):
        try:
            param = data[id]
            if param['config'] and param['config'] != '{}':
                try:
                    parentId = param['config']["parentId"]
                except Exception as e:
                    try:
                        parentId = param['config']["parentid"]
                        param['config']["parentId"] = parentId
                        del param['config']["parentid"]
                    except Exception as e:
                        param['config']["parentId"] = None
                        parentId = None
                if parentId == None:
                    return data[id]
                top_param = self._ParseTableData(parentId, data)
                if top_param != {}:
                    old_param = data[id]
                    data[id]['config']['param'] = dict(top_param['config']['param'], **old_param['config']['param'])
                return data[id]
            else:
                return {}
        except Exception as e:
            pass

    def _get_group(self, infos, device_id, data_id, group):
        for device_id2, device2 in infos["properties"].items():
            try:
                for device_data in device2["config"]["param"]["sub"]:
                    if len(device_data.split(".")) == 2:
                        sub_device_id, sub_data_id = device_data.split(".")
                        if sub_device_id == device_id:
                            if sub_data_id == '*' or sub_data_id == data_id:
                                if device_id2 not in group:
                                    group.append(device_id2)
                    if len(device_data.split(".")) == 3:
                        self.SubMsg([device_data])
            except Exception as e:
                pass
        return group

    # 获取设备Id列表
    def _get_devlist(self, infos):
        m_devlist = []
        m_dev2points = {}
        m_dev2attrs = {}
        m_point2attrs = {}
        m_point2subs = {}  # 每个监测点被哪些设备做了本地订阅（监测点所属的本设备除外，也不包括间接订阅）！！

        ionode_id = infos["gateway_uuid"]
        for device_id, device in infos["properties"].items():
            dev2points = []
            idinfo = ionode_id + "." + device_id
            m_devlist.append(idinfo)
            m_dev2attrs[idinfo] = device
            for data_id, data in device["data"].items():
                dev2points.append(idinfo + "." + data_id)
                m_point2attrs[idinfo + "." + data_id] = data
                group = []
                group_list = self._get_group(infos, device_id, data_id, group)

                m_point2subs[idinfo + "." + data_id] = group_list

            m_dev2points[idinfo] = dev2points
        # 去掉data属性，为什么前面么有直接去掉，是因为后面还有data循环，去掉循环为None
        for device_id, device in m_dev2attrs.items():
            device.pop("data")
        return m_devlist, m_dev2attrs, m_dev2points, m_point2attrs, m_point2subs

    # 获取监测点列表
    def _get_dev2points(self, info):
        ionode_id = info["gateway_uuid"]
        pointslist = []
        for device_id, device in info["properties"].items():
            for data_id, data in info["properties"][device_id]["data"].items():
                pointslist.append(ionode_id + "." + device_id + "." + data_id)
        return pointslist, info

    # 检测用户返回是不是符合规定
    def _ret(self, data):
        try:
            info = json.loads(data)
            code = info["code"]
            msg = info["msg"]
            data = info["data"]
        except Exception as e:
            traceback.print_exc()
            return json.dumps(
                {"code": 517, "msg": "Format return error. eg:{'code':'1001','msg':'msg info','data':data}",
                 "data": None})
        if code > 1000:
            return json.dumps({"code": 517, "msg": "Code need greater than 1000", "data": None})
        return json.dumps({"code": 0, "msg": "OK", "data": None})

    # 登入
    def Login(self, username, password, uuid, update=False, s_name=None, host=None):
        self.username = username
        self.password = password
        self.uuid = uuid
        self.s_name = s_name
        self.http_host = host
        data = {'username': self.username, 'password': self.password, 'uuid': self.uuid, 'httpHost': self.http_host}

        try:
            self.info('HTTP_HOST: ' + host + ' logining...')
            r = self.iceService.login(webLoginParam=WebLoginParam(**data), callBackReceiver=self)
            r = r.to_dict()
            result = json.dumps({'code': 0, 'msg': 'OK'})
            if int(r['code']) == 0:
                # if self.communicator:
                # 	self.iceService.destroy(communicator=self.communicator)
                # self.communicator = self._get_communicator()

                # 如果传了host，那self.server_ip直接用host
                self.info('login succeed!')
                self.server_ip = str(r["router_config"]["iotrouterIP"])
                if host:
                    if host[-1] == "/":
                        host = host[:-1]
                    if host.startswith("http://"):
                        host = host.replace("http://", '')
                    if host.startswith("https://"):
                        host = host.replace("https://", '')
                    self.server_ip = host
                self.server_port = str(r["router_config"]["remoteAdapterPort"])
                self.s = int(r["heartbeat"])
                self.retry = r["retry"]
                self.server_time = r["time"]
                # self._init_connent()
                # 开启线程来维持心跳
                # self.hb.set_param(self.prx, self.communicator, self, self.uuid, self.server_ip,self.server_port, self.s, self.retry, self.username, self.password, self.server_time)
                # if not self.hb.isAlive():
                # 	self.hb.start()
                info = None
                table_info_bd = None
                try:
                    with open(uuid + ".tb", "r") as f:
                        info = f.read()
                    table_info_bd = json.loads(info)
                except Exception as e:
                    with open(uuid + ".tb", "w") as f:
                        pass
                # 获取后台点表数据
                self.info('querying tablelist...')
                table_info_ice = self.iceService.getTableDetail()
                table_info_ice = json.loads(table_info_ice)
                if int(table_info_ice["code"]) != 0:
                    self.info('querying faied!')
                    return json.dumps(table_info_ice)
                self.info('checking version...')
                self.m_table = table_info_ice = table_info_ice["data"].copy()
                if not table_info_bd or 'gateway_uuid' in table_info_bd and table_info_bd["gateway_uuid"] != \
                        table_info_ice["gateway_uuid"]:
                    self.m_table = table_info_ice
                    with open(uuid + ".tb", "wb") as f:
                        f.write((json.dumps(self.m_table, ensure_ascii=False, indent=4)).encode('utf8'))
                else:
                    # 本地最新
                    if table_info_bd["timestamp"] > table_info_ice["timestamp"]:
                        r = self.iceService.updateTable(json.dumps(table_info_bd))
                        json_data = json.loads(r)
                        self.m_table = json_data["data"]
                    # 平台
                    if table_info_bd["timestamp"] < table_info_ice["timestamp"] or table_info_bd["timestamp"] == \
                            table_info_ice["timestamp"]:
                        self.m_table = table_info_ice
                        with open(uuid + ".tb", "wb") as f:
                            f.write((json.dumps(self.m_table, ensure_ascii=False, indent=4)).encode('utf8'))
                self.info('init engine...')
                result = self.engineInit(json.dumps(self.m_table))
                self.hb = HeartBeatThread(iceService=self.iceService, server_time=table_info_ice["timestamp"])
                self.hb.start()
            # print json.dumps(self.m_table)
            else:
                del r["data"]
                result = json.dumps(r)

        except Exception as e:
            logger.error("", exc_info=True)
            raise e
        return result

    # 登出
    def Logout(self):
        if self.prx:
            result = self.iceService.logout()
            result = json.loads(result)
            if int(result["code"]) == 0:
                self.engineStop()
                self.iceService.destroy(communicator=self.communicator)
                return json.dumps({'code': 0, 'msg': 'OK', 'data': None})
            else:
                return json.dumps({"code": result['code'], "msg": result['msg'], "data": None})
        else:
            return json.dumps({'code': 0, 'msg': 'warning: self.prx has not been initialized!', 'data': None})

    # 点对点通信(向指定用户发送消息)
    def SendMsg(self, toUuid, data):
        return self.prx.sendMsg(self.uuid, toUuid, data)

    # 订阅
    def SubMsg(self, idlist=[]):

        for i in idlist:
            try:
                point = self._get_point(i)
                result = self.prx.subMsg(self.uuidsession, point)
                result = json.loads(result)
                if int(result['code']) != 0:
                    return json.dumps(result)
            except Exception as e:
                traceback.print_exc()
                return json.dumps({'code': 514, 'msg': 'Argument error', 'data': ''})

        return json.dumps({'code': 0, 'msg': 'OK', 'data': None})

    # 批量发布
    def PubMsgs(self, values):
        if self.strat_connect == False:
            return json.dumps({'code': 501, 'msg': 'Network disconnection', 'data': None})
        values_new = []
        vallisttmp = []
        is_evaled = False
        try:
            for i in values:
                value = i["value"]
                # 如果存在表达式equation，则计算表达式
                try:
                    if 'param' in self.m_point2attrs[i["id"]]['config'].keys():
                        paramtmp = self.m_point2attrs[i["id"]]['config']['param']
                        if 'equation' in paramtmp.keys():
                            equation = paramtmp['equation']
                            x = float(value)
                            value = eval(equation)
                            is_evaled = True
                except Exception as e:
                    self.error(values)
                    traceback.print_exc()
                vallisttmp.append(value)
                point = json.loads(self._get_point(i["id"], value))[0]
                values_new.append(point)

            if is_evaled:
                self.info(_unicode('value adjusted according to equation:') + json.dumps(tuple(vallisttmp)))

            # send to ice
            self.info('------>multi send to route...')
            result = self.iceService.syncPubMsg(json.dumps(
                self._points_merged(values_new)))  # tip by lrq 如果不用self._points_merged()进行合并转换，那么批量上报的，会让路由逐个点转发推送！
            self.info('<------back from route')

            retbak = result.copy()
            try:
                if type(result) == list:
                    result = result[0]
                if int(result['code']) == 0:
                    # rettmp = []
                    # for i in range(1,len(retbak)):
                    # 	tmp = retbak[i]
                    # 	rettmp.append({"id": tmp["body"]["id"], "code": tmp["code"], "msg": tmp["msg"], "data": tmp["data"]})
                    # return json.dumps(rettmp)
                    return json.dumps(retbak, indent=3)
                else:
                    self.error(u'PubMsgs 上报数据失败，将复位：')
                    self.error(json.dumps(result))
                    self.exit_to_reboot()
            except Exception as e:
                traceback.print_exc(e.message)
                return json.dumps({'code': 501, 'msg': e.message, 'data': retbak})
        except Exception as e:
            traceback.print_exc(e.message)
            return json.dumps({'code': 514, 'msg': 'Argument error', 'data': e.message})

    # 单个发布
    @point_run_time()
    def PubMsg(self, idinfo, value, timestamp=time.time()):
        if self.strat_connect == False:
            return json.dumps({'code': 101, 'msg': 'Network disconnection', 'data': None})
        # 校验
        try:
            obj_type = self.m_point2attrs[idinfo]['valuetype']
            if obj_type == 'INT':
                if type(value) != int:
                    pass
                # self.info('type mismatched and will be auto converted: ')
                # self.info(type(value))
                # self.error(type(value))
                # return json.dumps({'code': 516, 'msg': u'TypeNotValid', 'data': 'INT'})

                # edit by lrq 20200809 自动兼容类型转换，同时加上类型不匹配警告
                # if type(value) == float:
                value = int(value)
            if obj_type == 'BOOL':
                if type(value) != bool and type(value) != int:
                    pass
                # self.info('type mismatched and will be auto converted: ')
                # self.info(type(value))
                # self.error(type(value))
                # return json.dumps({'code': 516, 'msg': u'TypeNotValid', 'data': 'BOOL'})

                # add by lrq 2019.0509
                if type(value) == str or type(value) == _unicode:
                    vl = value.lower()
                    if vl == 'false' or vl == '0' or vl == '':
                        value = 0  # 发现用False/True，反倒web上数值不变！
                    elif vl == 'true' or vl == '1':
                        value = 1
                    else:
                        return json.dumps({'code': 516, 'msg': u'TypeNotValid', 'data': 'BOOL'})
                else:
                    value = int(value)
            # self.warn('BOOL value change to int:' + str(value))
            if obj_type == 'FLOAT':
                if type(value) != float:
                    pass
                # self.info('type mismatched and will be auto converted: ')
                # self.info(type(value))
                # self.error(type(value))
                # return json.dumps({'code': 516, 'msg': u'TypeNotValid', 'data': 'FLOAT'})

                # if type(value) == int:
                value = float(value)

            if obj_type == 'STRING':
                if type(value) != str and type(value) != _unicode:
                    pass
                # self.info('type mismatched and will be auto converted: ')
                # self.info(type(value))
            # self.error(type(value))
            # return json.dumps({'code': 516, 'msg': u'TypeNotValid', 'data': 'STRING'})
        except Exception as e:
            raise e
        # 如果存在表达式equation，则计算表达式
        if obj_type == 'INT' or obj_type == 'FLOAT':
            paramtmp = None
            try:
                paramtmp = self.m_point2attrs[idinfo]['config']['param']
            except KeyError:
                pass
            if paramtmp:
                try:
                    if 'equation' in paramtmp.keys():
                        equation = paramtmp['equation']
                        x = int(value)
                        value = eval(equation)
                except Exception as e:
                    raise e
        try:
            point = self._get_point(idinfo, value, timestamp)
            # self.info('------>single send to route...')
            result = self.iceService.syncPubMsg(point)
            # self.info('<------back from route')
            return result
        except Exception as e:
            raise e

    # 设备上线上报
    @point_run_time()
    def DevOnline(self, devsId=[]):
        self.devsId = devsId
        # 接入点上线查询是否有驱动，本地没有去服务器下载，若没有则提示找不到，本地有驱动就用本地驱动
        try:
            for i in devsId:
                ionode_uuid, device_oid = i.split(".")
                if ionode_uuid not in self.uuidsession:
                    return json.dumps({'code': 508, 'msg': 'IONodeNotExist', 'data': None})
                r = self.prx.devOnline(self.uuidsession, device_oid)
                result = json.loads(r)
                if int(result["code"]) != 0:
                    return r
        except Exception as e:
            traceback.print_exc()
            return json.dumps({'code': 514, 'msg': 'Argument error', 'data': e.message})
        # 下载驱动
        # for device_id, j in (self.m_dev2attrs).items():
        #     try:
        #         driver = j["config"]["driver"]
        #         language, pythondesc = driver.split("/")
        #         if language == 'python':
        #             import_name, class_name = pythondesc.split(".")
        #             # 判断本地有没有对于驱动
        #             if not os.path.exists(device_dir + "/" + import_name + ".py"):
        #                 t = self.DriveDownloadFile("/uploads/drivefile/" + import_name + ".py")
        #                 t.start()
        #     except Exception as e:
        #         logger.error("", exc_info=True)
        return json.dumps({'code': 0, 'msg': 'OK', 'data': None})

    # 设备下线上报
    def DevOffline(self, devsId=[]):
        try:
            for i in devsId:
                ionode_uuid, device_oid = i.split(".")
                r = self.prx.devOffline(self.uuidsession, device_oid)
                result = json.loads(r)
                if int(result["code"]) != 0:
                    return r
        except Exception as e:
            traceback.print_exc()
            return json.dumps({'code': 514, 'msg': 'Argument error', 'data': ''})
        return json.dumps({'code': 0, 'msg': 'OK', 'data': None})

    # 获取监测点在平台数据中间件的值
    def GetPlatformData(self, point, param=''):
        try:
            ionode_uuid, device_oid, data_oid = point.split(".")
            point = self._get_point(point, param)
            info = self.prx.getPlatformData(self.uuidsession, point)
            info = json.loads(info)
            if 'code' in info.keys():
                return json.dumps(info)
            data = info["properties"][device_oid]["data"][data_oid]
            return json.dumps({'code': 0, 'msg': 'OK', 'data': data})
        except:
            traceback.print_exc()
            return json.dumps({'code': 514, 'msg': 'Argument error', 'data': ''})

    # 获取监测点设备的值
    def GetDeviceData(self, point, param=''):
        try:
            ionode_uuid, device_oid, data_oid = point.split(".")
            point = self._get_point(point, param)
            info = self.prx.getDeviceData(self.uuidsession,
                                          point)  # 【待修复 202007】返回的数据经过2次dumps导致解析的时候第一次得到的还是json字符串，再进行一次才是数据
            info = json.loads(json.loads(info))
            if int(info["code"]) == 0:
                try:
                    info = info[0]
                except Exception as e:
                    pass
                try:
                    data = info["data"]["body"]["properties"][device_oid]["data"][data_oid]
                except Exception as e:
                    data = info["data"]
                return json.dumps({'code': info["code"], 'msg': info["msg"], 'data': data})
            else:
                return json.dumps({'code': info["code"], 'msg': info["msg"], 'data': ''})
        except:
            traceback.print_exc()
            return json.dumps({'code': 514, 'msg': 'Argument error', 'data': ''})

    # 解析单张表数据
    def engineInit(self, text):
        try:
            info = json.loads(text)
            if info == None:
                self.error(u'点表错误，解析为空：' + text)
                return json.dumps({'code': 514, 'msg': 'Table empty??', 'data': text})

            if 'gateway_uuid' in info is False or 'name' not in info or 'description' not in info \
                    or 'timestamp' not in info or 'longitude' not in info \
                    or 'latitude' not in info or 'owner' not in info \
                    or 'config' not in info or 'properties' not in info:
                return json.dumps({'code': 514, 'msg': 'Table format invalid', 'data': ''})

            devices = info["properties"]

            # 修改设备config
            if devices:
                for device_id, device_info in devices.items():
                    # 补全设备config
                    if 'name' not in device_info or 'description' not in device_info \
                            or 'timestamp' not in device_info or 'config' not in device_info \
                            or 'data' not in device_info:
                        return json.dumps({'code': 514, 'msg': 'Table format invalid', 'data': ''})
                    self._ParseTableData(device_id, devices)

                    # 补全data config
                    if device_info['data']:
                        for data_id, data_info in device_info['data'].items():

                            if 'name' not in data_info or 'description' not in data_info \
                                    or 'refreshcycle' not in data_info or 'readwrite' not in data_info \
                                    or 'timestamp' not in data_info or 'defaultvalue' not in data_info \
                                    or 'maxvalue' not in data_info or 'minvalue' not in data_info \
                                    or 'regexp' not in data_info or 'sensibility' not in data_info \
                                    or 'config' not in data_info or 'valuetype' not in data_info \
                                    or 'unit' not in data_info:
                                return json.dumps({'code': 514, 'msg': 'Table format invalid', 'data': ''})
                            self._ParseTableData(data_id, device_info['data'])
        except Exception as e:
            traceback.print_exc()
            return json.dumps({'code': 514, 'msg': 'Table format invalid', 'data': ''})
        infos = copy.deepcopy(info)

        self.m_devlist, self.m_dev2attrs, self.m_dev2points, self.m_point2attrs, self.m_point2subs = self._get_devlist(
            infos)

        self.threading_list = []

        for i in self.m_devlist:
            device_config = self.m_dev2attrs[i]['config']  # type: dict
            if 'enabled' in device_config and device_config.get('enabled') is False:
                continue
            t = RunCollectingThread(self, self.iceService, self.event, i)
            self.threading_list.append(t)

        return json.dumps({'code': 0, 'msg': 'OK', 'data': 'data table init succeed!'})

    # 开始采集
    def engineRun(self):
        self.warn(u'驱动采集引擎启动..') 
        for i in self.threading_list:
            i.setDaemon(True)
            i.start()
        self.warn('ok!')
        return json.dumps({'code': 0, 'msg': 'OK', 'data': None})

    # 退出采集
    def engineStop(self):
        for i in self.threading_list:
            i.stop()
        return json.dumps({'code': 0, 'msg': 'OK', 'data': None})

    # 线程个数
    def count(self):
        return self.eventcount
