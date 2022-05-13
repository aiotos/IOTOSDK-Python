#!coding:utf8
from datetime import datetime
from driver import IOTOSDriverI
import json, time, random
from library.exception import DataNotExistError
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# 继承官方驱动类（ZMIotDriverI）
class HelloWorldDriver(IOTOSDriverI):

    # 1、通信初始化
    def InitComm(self, attrs):
        self.online(True)
        logger.info("deviceId=" + self.sysId)
        logger.debug("deviceId=" + self.sysId)
        # self.setValue(value='auto_created', name='CLI_auto_created')
        self.pauseCollect = False
        # self.collectingOneCircle = True
        self.collectingOneCircle = False

    firstId = None
    pollTime = None

    # 2、采集
    def Collecting(self, dataId):
        if self.firstId is None:
            self.firstId = dataId
            self.pollTime = time.time()
        elif self.firstId == dataId:
            poll_time = time.time() - self.pollTime
            date = datetime.fromtimestamp(self.pollTime)
            logger.info('id=%s, device=%s, firstId=%s, time=%s, len=%s, avg=%.4f, date=%s', self.sysId,
                        self.sysAttrs['name'], dataId, poll_time, len(self.data2attrs),
                        poll_time / len(self.data2attrs), date)
            self.pollTime = time.time()
        '''*************************************************
        TODO
        **************************************************'''
        try:
            # 通过数据点ID获取数据点属性字典
            data_attr = self.data2attrs[dataId]
            value_type = data_attr["valuetype"]
            try:
                if 'minvalue' in data_attr and data_attr['minvalue']:
                    min_value = float(data_attr['minvalue'])
            except:
                min_value = -999
                logger.error('minvalue', exc_info=1)

            try:
                if 'maxvalue' in data_attr and data_attr['maxvalue']:
                    max_value = float(data_attr['maxvalue'])
            except:
                logger.error('maxvalue', exc_info=1)
                max_value = 999

            if value_type == u'BOOL':
                new_value = bool(random.randint(0, 1))
            elif value_type == u'INT':
                new_value = int(random.uniform(min_value, max_value))
            elif value_type == u'FLOAT':
                new_value = float(random.uniform(min_value, max_value))
            else:
                new_value = time.time()
            # logger.info('data=%s, value=%s', dataId, new_value)
            return (new_value,)
        except DataNotExistError as e:
            logger.error(e)
            return None

    # 3、控制
    # 事件回调接口，其他操作访问
    def Event_customBroadcast(self, fromUuid, type, data):
        '''*************************************************

        TODO
        **************************************************'''
        return json.dumps({'code': 0, 'msg': '', 'data': ''})

    # 3、查询
    # 事件回调接口，监测点操作访问
    def Event_getData(self, dataId, condition):
        '''*************************************************
        TODO
        **************************************************'''
        return json.dumps({'code': 0, 'msg': '', 'data': ''})

    # 事件回调接口，监测点操作访问
    def Event_setData(self, dataId, value):
        '''*************************************************
        TODO
        **************************************************'''
        logger.error('dataId=%s, value=%s', dataId, value)
        return json.dumps({'code': 0, 'msg': '', 'data': dict(response_time=time.time())})

    # 事件回调接口，监测点操作访问
    def Event_syncPubMsg(self, point, value):
        '''*************************************************
        TODO
        **************************************************'''
        return json.dumps({'code': 0, 'msg': '', 'data': ''})
