#!coding:utf8

from library.exception import DataNotExistError
from library.iotos_util import _unicode
from iotos import *
from routelib.jlib import *

'''*************************************************
到驱动这里的监测点ID、不应该是全的ID，而应该是去掉了接入点ID、设备ID之后的！所以这里建立关系的时候，SDK路由寻址到后，
路由将前面的就可以剥离掉了，给驱动的应该就是单一ID就ok，这样也能让驱动对应的设备完整属性（包括监测点）的部分可以复用！！

之前SDK1.5.1、2.0，都是给接入点开发用的，所有id都是全ID，而接入点的开发现在都是封装到SDK里的，给用户的都是设备驱动的开发，
所以这里再次封装形成的接口才是面向用户的！
不过也不全对，应该是对自己的点表操作，只用数据点id即可（监测点id为全id，数据点id为局部id），而要访问不是自己监测点而是订阅的，
那么该调用啥接口，该传入啥呢？是否要提示使用该驱动时要用户自己去订阅相应的点？就相当于让用户自己去下载依赖包？
**************************************************'''
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
            self.driver.Event_syncPubMsg(self.pointId, self.value)
        except:
            traceback.print_exc()


# 设备驱动/业务插件 接口类
class IOTOSDriverI(JLib):

    def __init__(self):

        JLib.__init__(self)
        self.zm = None # type: IOTOSys # SDK接口实例
        self.sysId = ''  # 当前系统ID	------------------------- 关联到不同设备，随设备不同而不同
        self.sysAttrs = {}  # 当前系统属性 ------------------------ 系统属性（不包括数据点），属于驱动的属性，初次关联到新建设备时，需要还原。注意问题：如果设备已经设置了属性，是覆盖替换吗？
        self.data2attrs = {}  # 当前系统下的数据点及对应属性字典 ------- 数据点及属性，同样属于驱动的属性，初次关联到新建设备时，需要还原。注意问题，如果设备下数据点不为空或者有属性，是覆盖替换吗？
        self.data2subs = {}
        self.name2dataId = {}
        self.event = threading.Event()
        self.collectingOneCircle = False  # 20200114 by lrq 采集循环仅执行一次就退出，不循环采集，用户遍历一次点表！
        self.pauseCollect = True  # added by lrq 20200711 区别于全局zmiot中的pause_collect，为每个驱动实例都单独加上采集控制，避免某一个设备上线启动采集，导致全局让所有设备驱动都执行采集，包括未上线的设备！

    ################ 1、属性GET/SET方法，用于给非py的其他语言的扩展包调用 ##################

    def getSysId(self):
        return self.sysId

    def getSysAttrs(self):
        return json.dumps(self.sysAttrs)

    def getData2attrs(self):
        return json.dumps(self.data2attrs)

    def getData2subs(self):
        return json.dumps(self.data2subs)

    def setCollectingOneCircle(self, enable=True):
        self.collectingOneCircle = enable

    def setPauseCollect(self, enable=True):
        self.pauseCollect = enable

    ################################ 2、成员方法 ######################################
    # added by lrq 独立抽出本地发布
    def pubLocal(self, id, value):
        for systmp in self.data2subs[id]:
            t = RunLocalPubThread(self.zm, self.event, self.zm.m_dev2driver[self.zm.uuid + '.' + systmp],
                                  self.sysId + "." + id, value)
            t.setDaemon(True)
            t.start()

    # 认定数据点方式访问的，都是对当前设备下的，如果对其他设备的数据点进行访问，需要带上其设备id!
    def pointId(self, dataId):
        """获取三段式ID

        @type dataId: str
        @param dataId: 数据点ID: 'XXXXX'
        @return: '网关ID.设备ID.数据点ID'
        """
        if dataId in self.data2attrs:
            return self.zm.uuid + "." + self.sysId + "." + dataId
        else:
            self.error('dataId not recognized: ' + dataId)
            traceback.print_exc()
            return ''

    # 将名称标识（方便人读和写）换成ID标识（保证唯一性，方便驱动执行可复用性），注意，是不包括接入点id的最多后两段
    def id(self, name):

        # added by lrq 20200809 为兼容str类型中文字符传参，统一转为unicode utf-8
        # 正常情况下type(name)为unicode，所以当如果不是时，用utf-8解码，统一成格式，这样传参带不带u，都能支持了！
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
                # edit by lrq 202007 为了兼容setValue()、value()中本地名称转为id，这里传入3段全id时，也会到这里来，直接返回即可，默认是数据点的3段“全id”，暂不支持“全名称”
                # traceback.print_exception(value='name not valid!')
                return name
        except KeyError:
            msg = _unicode("数据点名称:", "utf-8") + name
            raise DataNotExistError(msg)

    # 将id标识换成名称标识，注意，是不包括接入点id的最多后两段
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

    # 合并PubMsg()、Event_syncPubMsg()以及Event_syncPubMsg()，注意，是不包括接入点id的最多后两段
    # 默认接受name标识，而不是id标识，方便编写程序调试，到发布的时候再去参数中变量变成id，然后加上self.name()来变成名称
    def setValue(self, name=None, value=None, id=None, timestamp=time.time(), auto_created=False):
        """上报单个数据点值

        @type name: str
        @type value: object
        @type id: str
        @param name: 数据点名称,或者传id
        @param value: 数据点值,或者传name
        @param id: 数据点ID(dataId)
        """
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

        # 1、如果当前设备插件业务中调用的是设备插件本身发布的点，那么就是与路由打交道，
        # 同时启动本地多线程派发，
        # 【临时】每个监测点都派发给所有的设备驱动，接下来需要做本地订阅限定工作
        if name:
            id = self.id(name)
        elif id:
            id = self.pointId(dataId=id)
        ids = id.split('.')
        # 对当前设备下的数据点进行pub操作
        if len(ids) == 1:
            if id in self.data2attrs:
                # added by lrq 20200114 上报自己的数据，存储引擎缓存！对于二级、三级等对其他设备数据的setValue，就不是上报了，而是控制，这时候不存入对方驱动实例对应的缓存中！！！
                self.data2attrs[id]['memoryvalue'] = value

                # 每个数据采集变化上报，都会到本地所有的订阅了这个数据点的设备驱动，不包括当前设备本身驱动，因为当前设备驱动数据上报的时候就可以做逻辑处理，没必要又转到自己的上报处理区中！
                self.pubLocal(id, value)

                return self.zm.PubMsg(self.pointId(id), value, timestamp)
        # 2、如果数据点不是当前设备下的，那么可能是本地订阅的其他驱动的处理，
        # 对当前接入下其他设备下数据点进行pub
        elif len(ids) == 2:
            ret = self.zm.m_dev2driver[self.zm.uuid + '.' + ids[0]].Event_setData(ids[1], value)
            if json.loads(ret)['code'] == 0:
                return self.zm.PubMsg(self.zm.uuid + '.' + id, value, timestamp)

        # 3、也可能是自己订阅的远程点的上报
        # 订阅的远程设备数据点的pub上报
        elif len(ids) == 3:

            return self.Event_syncPubMsg(id, value)

    # 批量上报时，如果做到批量到云平台，同时支持本地发布订阅
    def setValues(self, values):
        """批量上报数据点

        @type values: list[dict[str, object]]
        @param values: list[{"id": "数据点ID", "value": "数据点value"}, {"id": "数据点ID", "value": "数据点value"}]
        """
        for valUnit in values:
            idtmp = valUnit['id'].split('.')[2]
            valtmp = valUnit['value']
            self.pubLocal(idtmp, valtmp)
            # 批量不理解为批量控制，而统一作批量上报自己的数据来处理！！！explained by lrq 20200114
            self.data2attrs[idtmp]['memoryvalue'] = valtmp
        return self.zm.PubMsgs(values)

    # 将字符串类型的值按照点表类型转换成实际类型
    def valueTyped(self, dataId, strValue):
        typetmp = self.data2attrs[dataId]['valuetype']
        if typetmp == 'INT':
            return int(strValue)
        elif typetmp == 'BOOL':
            return bool(strValue)
        elif typetmp == 'FLOAT':
            return float(strValue)
        elif typetmp == 'STRING':
            return str(strValue)

    # 本地订阅的监测点暂不支持全局订阅派发（与当前V2.0平台订阅下默认都是全局订阅派发相反），注意，是不包括接入点id的最多后两段
    # 合并GetDeviceData()、GetPlatformData()以及Event_getData
    # 默认接受name标识，而不是id标识，方便编写程序调试，到发布的时候再去参数中变量变成id，然后加上self.name()来变成名称
    # source有'memory'、'device'、'platfrom'三个来源参数，简写m/M,d/D，p/P，分别是上次采集到引擎的数据、设备当前数据、上报到平台的数据，三类！！！
    def value(self, name, param='', source='memory'):
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

    # 订阅了当前设备某个监测点的外部设备id，好在监测点变化时候找到他通知过去
    # 【注意】本地订阅，当前是以整个设备来订阅，接下来会支持以监测点为单元来订阅
    def subscribers(self, dataId):
        return self.zm.m_point2subs[self.pointId(dataId)]

    # added by lrq 20200809 提供一个新的方法，用于统一返回字符串类型，给C++字符串类型数据传递
    def subscribers_str_ret(self, dataId):
        return json.dumps(self.subscribers(dataId))

    # 设备在线离线，即驱动sdk与实际设备的在线离线，可以是tcp通道，可以是串口连接等
    def online(self, state):
        devIdTmp = self.zm.uuid + '.' + self.sysId
        if state == True:
            return self.zm.DevOnline([devIdTmp])
        else:
            return self.zm.DevOffline([devIdTmp])

    ############################# 3、由用户实现的重写函数 ######################################

    # 1、通信初始化
    # 传入的attrs是点表补全后，当前设备下的部分，包括数据点
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
            self.zm.pauseCollect = True

    # 2、采集
    def Collecting(self, dataId):
        time.sleep(999999)
        return ()

    # 3、控制
    # 事件回调接口，其他操作访问
    def Event_customBroadcast(self, fromUuid, type, data):
        pass

    # 事件回调接口，监测点操作访问
    def Event_getData(self, dataId, condition):
        pass

    # 事件回调接口，监测点操作访问
    def Event_setData(self, dataId, value):
        pass

    # 账户下订阅的所有监测点进行pub时，会到所有接入点的所有设备驱动中走一遍！这个时候是监测点全id了！！
    def Event_syncPubMsg(self, point, value):
        pass
