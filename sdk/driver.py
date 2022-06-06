#!coding:utf8

from library.exception import DataNotExistError
from library.iotos_util import _unicode
from iotos import *
from routelib.jlib import *
import traceback


class RunLocalPubThread(threading.Thread):
    def __init__(self, ZMIotLib, event, devDriver, pointId, value):
        super(RunLocalPubThread, self).__init__()
        self.zm = ZMIotLib
        self.threadEvent = event
        self.driver = devDriver
        self.pointId = pointId
        self.value = value
    def run(self):
        try:
            self.driver.Event_syncPubMsg(self.pointId, self.value,)
        except:
            traceback.print_exc()

# 设备驱动/业务插件 接口类
class IOTOSDriverI(JLib):

    def __init__(self):
        JLib.__init__(self)
        self.zm = None 
        self.sysId = ''                     #设备实例全局标识
        self.sysAttrs = {}                  #设备实例配置属性
        self.data2attrs = {}                #数据点与属性配置键值对
        self.data2subs = {}                 #数据点与被订阅设备列表键值对
        self.name2dataId = {}               #数据点名称与对应标识键值对
        self.event = threading.Event()
        self.collectingOneCircle = False
        self.pauseCollect = True

    def __pubLocal(self, id, value):
        for systmp in self.data2subs[id]:
            t = RunLocalPubThread(self.zm, self.event, self.zm.m_dev2driver[self.zm.uuid + '.' + systmp],self.sysId + "." + id, value)
            t.setDaemon(True)
            t.start()

    #获取设备标识
    def getSysId(self):
        return self.sysId

    #获取设备配置
    def getSysAttrs(self):
        return json.dumps(self.sysAttrs)

    #获取数据点配置
    def getData2attrs(self):
        return json.dumps(self.data2attrs)

    #获取数据被订阅信息
    def getData2subs(self):
        return json.dumps(self.data2subs)

    #传入True或False，设置Collecting()是否停止采集循环遍历，默认不启动。调用并传入False将启动采集循环（线程），
    # 按顺序自动从数据点表第一个到最后一个进行遍历传入，详见Collecting()
    def setPauseCollect(self, enable=True):
        self.pauseCollect = enable

    #置启用采集循环前提下，传入True或False，设置3.3中采集循环是周期循环遍历，还是初始化遍历完数据点表一次就退出（默认）
    def setCollectingOneCircle(self, enable=True):
        self.collectingOneCircle = enable

    def pointId(self, dataId):
        '''
        根据当前设备下数据点由ID标识，获取带网关、设备的"全ID标识"（"[网关标识].[设备标识].[数据点标识]"）
        @param 
            dataId: String	数据点ID标识，如"0b2e"
        @return String	全ID标识，如'9003f858c85011ecbb02525400ffc252.e2c4f6fe.0b2e'
        '''
        if dataId in self.data2attrs:
            return self.zm.uuid + "." + self.sysId + "." + dataId
        else:
            self.error('dataId not recognized: ' + dataId)
            traceback.print_exc()
            return ''

    #数据点名称转标识，将名称标识（方便阅读和修改的）换成ID标识（保证唯一性，方便驱动代码复用），
    # 注意，支持"[数据点名称]"或"[设备名称].[数据点名]"，暂不支持"全名称"（"[网关名称].[设备名称].[数据点名称]"）
    def id(self, name):
        if type(name) == str:
            name = _unicode(name, "utf-8")

        try:
            ids = name.split('.')
            if len(ids) == 1:
                return self.name2dataId[name]
            elif len(ids) == 2:
                for devid, attr in self.zm.m_dev2attrs.items():
                    if attr['name'] == ids[0]:
                        return devid.split('.')[1] + '.' + self.zm.driver(devid).name2dataId[ids[1]]
            elif len(ids) == 3:
                return name
        except KeyError:
            msg = _unicode("数据点名称:", "utf-8") + name
            raise DataNotExistError(msg)

    #数据点标识转名称，将标识ID转成名称注意，支持"[数据点标识]"或"[设备标识].[数据点标识]"，暂不支持"全ID标识"（"[网关标识].[设备标识].[数据点标识]"）
    def name(self, id):
        ids = id.split('.')
        if len(ids) == 1:
            return self.data2attrs[id]['name']
        elif len(ids) == 2:
            return self.zm.m_dev2attrs[self.zm.uuid + '.' + ids[0]]['name'] + '.' + \
                   self.zm.m_point2attrs[self.zm.uuid + '.' + id]['name']
        elif len(ids) == 3:
            traceback.print_exception(value='id not valid!')
            return ''

    def setValue(self, name=None, value=None, id=None, timestamp=time.time(), auto_created=False):
        '''
        上报当前设备下单个数据点的值。注意name、id保证有任一传入即可，不需都传入。
        @param
                name: String	数据点名称
                  id: String	数据点ID标识
               value: Bool/String/Int/Float	数据点上报值
        @return String	Json字符串：{"code": 0, "msg":"", "data":""}，返回格式及错误码详见README.md
        '''
        try:
            return self.__setValue(name=name, value=value, timestamp=timestamp, id=id)
        except DataNotExistError as ex:
            if auto_created is False:
                raise ex

    def __setValue(self, name=None, value=None, timestamp=time.time(), id=None):
        """上报单个数据点值

        @type name: str
        @type value: object
        @type id: str
        @param name: 数据点名称,或者传id
        @param value: 数据点值,或者传name
        @param id: 数据点ID
        """
        assert (id or name), u'数据点ID或名称选传一个'
        assert value is not None, u'数据点值不能为None'
        if name:
            id = self.id(name)
        elif id:
            id = self.pointId(dataId=id)
        ids = id.split('.')
        if len(ids) == 1:
            if id in self.data2attrs:
                self.data2attrs[id]['memoryvalue'] = value
                self.__pubLocal(id, value)
                return self.zm.PubMsg(self.pointId(id), value, timestamp)
        elif len(ids) == 2:
            ret = self.zm.m_dev2driver[self.zm.uuid + '.' + ids[0]].Event_setData(ids[1], value)
            if json.loads(ret)['code'] == 0:
                return self.zm.PubMsg(self.zm.uuid + '.' + id, value, timestamp)
        elif len(ids) == 3:
            return self.zm.PubMsg(id, value)

    def setValues(self, values):
        """批量上报数据点
        @type values: list[dict[str, object]]
        @param values: list[{"id": "数据点ID", "value": "数据点value"}, {"id": "数据点ID", "value": "数据点value"}]
        """
        for valUnit in values:
            idtmp = valUnit['id'].split('.')[2]
            valtmp = valUnit['value']
            self.__pubLocal(idtmp, valtmp)
            self.data2attrs[idtmp]['memoryvalue'] = valtmp
        return self.zm.PubMsgs(values)

    # 将字符串类型的值按照点表类型转换成实际类型
    def valueTyped(self, dataId, strValue):
        '''
        将字符串类型的值按照点表类型转换成实际类型
        @param
              dataId: String	数据点ID标识
            strValue: String	数据点值对应的字符串
        @return Bool/String/Int/Float	根据数据点的实际类型将字符串数值转换成实际类型
        '''
        typetmp = self.data2attrs[dataId]['valuetype']
        if typetmp == 'INT':
            return int(strValue)
        elif typetmp == 'BOOL':
            return bool(strValue)
        elif typetmp == 'FLOAT':
            return float(strValue)
        elif typetmp == 'STRING':
            return str(strValue)

    def value(self, name, param='', source='memory'):
        '''
        获取数据点的当前值，包含从采集引擎缓存、平台数据库、以及设备当下最新这三种方式
        @param
                name: String	数据点名称
                param: String	查询条件，
            source: String	有'memory'、'device'、'platfrom'三个来源参数，简写m/M,d/D，p/P，分别是上次采集到引擎的数据、设备当前数据、上报到平台的数据三类
        @return Bool/String/Int/Float	按照实际类型返回数据点当前值
        '''
        id = self.id(name)
        ids = id.split('.')
        point_id = ''
        def adjustValueReturned(valtmp):
            if valtmp['code'] != 0:
                self.error(valtmp)
                return None
            else:
                return self.valueTyped(id, valtmp['data']['value'])  # 通过sdk返回过来的值，是字符串包裹着的！！
        # 1、对当前设备下的数据点查询
        if len(ids) == 1:
            if source.lower() == 'device' or source.lower() == 'd':
                return json.loads(self.Event_getData(id, param))['data']['value']
            elif source.lower() == 'memory' or source.lower() == 'm':
                # added by lrq20200114 当发现内存数据初始没有时，那么就转为去设备端获取！！
                if not self.data2attrs[id].has_key('memoryvalue'):
                    self.data2attrs[id]['memoryvalue'] = self.value(name, param, source='device')
                return self.data2attrs[id]['memoryvalue']
            elif source.lower() == 'platform' or source.lower() == 'p':
                point_id = self.pointId(id)
            else:
                assert 0
        # 2、对当前接入下其他设备下数据点查询
        elif len(ids) == 2:  # 1、对当前设备下的平台数据点查询
            drtmp = self.zm.m_dev2driver[self.zm.uuid + '.' + ids[0]]
            if source.lower() == 'device' or source.lower() == 'd':
                return json.loads(drtmp.Event_getData(ids[1], param))['data']['value']
            elif source.lower() == 'memory' or source.lower() == 'm':
                return drtmp.data2attrs[ids[1]]['memoryvalue']
            elif source.lower() == 'platform' or source.lower() == 'p':  # 2、对当前接入下其他设备下平台数据点查询
                point_id = self.zm.uuid + '.' + id
            else:
                assert 0
        # 3、对订阅的远程设备数据点的查询
        elif len(ids) == 3:  # 3、对订阅的远程设备平台数据点的查询
            if source.lower() == 'device' or source.lower() == 'd':  # 【带完善！！！】20200114 获取远程订阅的其他用户的数据，也分为对方采集引擎内存数据、平台数据、设备数据！！这里需要完善接口！！！！
                valtmp = json.loads(self.zm.GetDeviceData(id, param))
                if valtmp['code'] != 0:
                    self.error(valtmp)
                    return None
                else:
                    return valtmp['data']
        valtmp = json.loads(self.zm.GetPlatformData(point_id, param))
        if valtmp['code'] != 0:
            self.error(valtmp)
            return None
        else:
            typetmp = self.data2attrs[id]['valuetype']
            valtmp = valtmp['data']['value']  # 通过sdk返回过来的值，是字符串包裹着的！！
            if typetmp == 'INT':
                try:
                    return int(valtmp)
                except ValueError:
                    return None
            elif typetmp == 'BOOL':
                try:
                    return bool(valtmp)
                except ValueError:
                    return None
            elif typetmp == 'FLOAT':
                try:
                    return float(valtmp)
                except ValueError:
                    return None
            elif typetmp == 'STRING':
                return str(valtmp)

    # added by lrq 20200809 提供一个新的方法，用于统一返回字符串类型，给C++字符串类型数据传递
    def value_str_ret(self, name, param='', source='memory'):
        return str(self.value(name, param, source))


    def subscribers(self, dataId):
        '''
        订阅了当前设备指定监测点的外部设备ID标识列表
        @param
            dataId: String	数据点ID标识
        @return String	返回Json数组字符串，比如["d8540013","36cb7dd8","82591776"]
        '''
        return self.zm.m_point2subs[self.pointId(dataId)]

    # added by lrq 20200809 提供一个新的方法，用于统一返回字符串类型，给C++字符串类型数据传递
    def subscribers_str_ret(self, dataId):
        return json.dumps(self.subscribers(dataId))

    # 设备在线离线，即驱动sdk与实际设备的在线离线，可以是tcp通道，可以是串口连接等
    def online(self, state):
        '''
        上报平台设备上下线状态
        @param
            state: Bool	上线（True）/下线（False）
        @return String	参见详见README.md，通用数据返回结构
        '''
        devIdTmp = self.zm.uuid + '.' + self.sysId
        if state == True:
            return self.zm.DevOnline([devIdTmp])
        else:
            return self.zm.DevOffline([devIdTmp])


    # 通信初始化
    def InitComm(self, attrs):
        pass

    # 连接状态回调
    def connectEvent(self, state):
        self.online(state)
        if state == True:
            self.warn('device connected.')
            self.pauseCollect = False
        else:
            self.warn('device disconnected!')
            self.pauseCollect = True

    # 循环采集
    def Collecting(self, dataId):
        time.sleep(999999)
        return ()

    # 平台下发广播
    def Event_customBroadcast(self, fromUuid, type, data):
        pass

    # 平台下发查询
    def Event_getData(self, dataId, condition):
        pass

    # 平台下发控制
    def Event_setData(self, dataId, value):
        pass

    # 订阅数据上报
    def Event_syncPubMsg(self, point, value):
        pass
