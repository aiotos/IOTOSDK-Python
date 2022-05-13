#!coding:utf8
import json
# import winsound
import sys

sys.path.append("..")

from driver import *
import threading
import time
import random
import math


class Demo(IOTOSDriverI):
    alarm = 0
    fancheNum = 120
    rate = 0.1
    collectValue = []
    flag1 = False
    flag2 = True
    start = 690
    angle1 = 0
    angle2 = 1014
    control = False
    angle = -1 * math.pi / 2
    acceleration = math.pi / 200

    def initialization(self):
        self.setValue(u'实体设备.V1', self.start)
        self.setValue(u'实体设备.V2', self.angle1)
        self.setValue(u'实体设备.V3', self.angle2)
        self.setValue(u'实体设备.V4', self.control)
        self.timer6 = threading.Timer(0.001, self.initialization)
        self.timer6.start()

    def controls(self):
        # self.setValue(u'实体设备.V1', self.start)
        # self.setValue(u'实体设备.V2', self.angle1)
        # self.setValue(u'实体设备.V3', self.angle2)
        # self.setValue(u'实体设备.V4', self.control)
        if self.start == 965:
            while self.angle1 < 21:
                self.angle1 += 7
                self.angle2 -= 4
                self.setValue(u'实体设备.V2', self.angle1)
                self.setValue(u'实体设备.V3', self.angle2)
                time.sleep(1)
            time.sleep(2)
            self.control = True
            self.setValue(u'实体设备.V4', self.control)
            if (self.control):
                self.timer4 = threading.Timer(1, self.smooth)
                self.timer4.start()
        else:
            self.start += 55
            self.timer = threading.Timer(1, self.controls)
            self.timer.start()

    def state(self):
        if self.flag1 == False:
            self.flag1 = True
        else:
            self.flag1 = False
        self.setValue(u'实体设备.翻车机_正翻', self.flag1)
        time.sleep(15)
        if self.flag2 == False:
            self.flag2 = True
        else:
            self.flag2 = False
        self.setValue(u'实体设备.翻车机_停止', self.flag2)
        self.timer5 = threading.Timer(5, self.state)
        self.timer5.start()

    def fanche(self):
        kaoche = random.sample(range(300, 500), 4)
        yache = random.sample(range(300, 500), 4)
        self.setValue(u'实体设备.靠车压力1', kaoche[0])
        self.setValue(u'实体设备.靠车压力2', kaoche[1])
        self.setValue(u'实体设备.靠车压力3', kaoche[2])
        self.setValue(u'实体设备.靠车压力4', kaoche[3])
        self.setValue(u'实体设备.压车压力1', yache[0])
        self.setValue(u'实体设备.压车压力2', yache[1])
        self.setValue(u'实体设备.压车压力3', yache[2])
        self.setValue(u'实体设备.压车压力4', yache[3])
        self.timer3 = threading.Timer(3, self.fanche)
        self.timer3.start()

    def proportional(self):
        proportionalValue = random.sample(range(20, 30), 5)
        i = 0
        while i < 5:
            self.collectValue = [round(random.uniform(0.6, 1), 2), round(random.uniform(0.6, 1), 2),
                                 round(random.uniform(0.6, 1), 2), round(random.uniform(0.6, 1), 2)
                , round(random.uniform(0.6, 1), 2)]
            i += 1
        self.setValue(u'实体设备.比例数值1', proportionalValue[0])
        self.setValue(u'实体设备.比例数值2', proportionalValue[1])
        self.setValue(u'实体设备.比例数值3', proportionalValue[2])
        self.setValue(u'实体设备.比例数值4', proportionalValue[3])
        self.setValue(u'实体设备.比例数值5', proportionalValue[4])
        self.setValue(u'实体设备.采集比例1', self.collectValue[0])
        self.setValue(u'实体设备.采集比例2', self.collectValue[1])
        self.setValue(u'实体设备.采集比例3', self.collectValue[2])
        self.setValue(u'实体设备.采集比例4', self.collectValue[3])
        self.setValue(u'实体设备.采集比例5', self.collectValue[4])
        self.timer2 = threading.Timer(3, self.proportional)
        self.timer2.start()

    def other(self):
        speed = random.sample(range(120, 200), 1)
        deceleration = random.sample(range(30, 110), 1)
        conversion = random.sample(range(10, 100), 1)
        self.alarm += 5
        self.fancheNum += 5
        self.rate += 0.1
        if (self.rate >= 1):
            self.rate = 0.1
        if (self.alarm >= 140):
            self.alarm = 0
        if (self.fancheNum >= 200):
            self.fancheNum = 120
        self.setValue(u'实体设备.24小时内报警次数', self.alarm)
        self.setValue(u'实体设备.速度', speed[0])
        self.setValue(u'实体设备.减速时间', deceleration[0])
        self.setValue(u'实体设备.变频器转速', conversion[0])
        self.setValue(u'实体设备.单次翻转率', self.rate)
        self.setValue(u'实体设备.单次翻转率百分比', self.rate * 100)
        self.setValue(u'实体设备.今日翻车量', self.fancheNum)
        self.timer1 = threading.Timer(3, self.other)
        self.timer1.start()

    def smooth(self):
        self.angle += self.acceleration  # 总共走 pi/2
        radian = int(((math.sin(self.angle) + 1) * 10000) * 85)  # 72.5
        self.setValue(u'实体设备.翻转角度', radian)

        if math.sin(self.angle) + 1 == 0.0:
            self.timer4.cancel();
            self.control = False
            time.sleep(5)
            self.start = 690
            self.angle1 = 0
            self.angle2 = 1014
            # self.angle = -1 * math.pi / 2
            self.setValue(u'实体设备.V1', self.start)
            self.setValue(u'实体设备.V2', self.angle1)
            self.setValue(u'实体设备.V3', self.angle2)
            self.setValue(u'实体设备.V4', self.control)
            self.controls()
        else:
            self.timer4 = threading.Timer(0.01, self.smooth)
            self.timer4.start()

    # 1、通信初始化
    def InitComm(self, attrs):
        self.online(True)
        self.timer6 = threading.Timer(0.01, self.initialization)
        self.timer6.start()
        self.timer = threading.Timer(1, self.controls)
        self.timer.start()
        self.timer1 = threading.Timer(1, self.other)
        self.timer1.start()
        self.timer2 = threading.Timer(1, self.proportional)
        self.timer2.start()
        self.timer3 = threading.Timer(1, self.fanche)
        self.timer3.start()
        # self.timer4 = threading.Timer(0.01, self.smooth)
        # self.timer4.start()
        self.timer5 = threading.Timer(1, self.state)
        self.timer5.start()

    # 2、采集
    def Collecting(self, dataId):
        time.sleep(0xfffff)
        '''*************************************************
		TODO
		**************************************************'''
        return 0

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
        data = None
        return json.dumps({'code': 0, 'msg': '', 'data': data})

    # 事件回调接口，监测点操作访问
    def Event_setData(self, dataId, value):
        # winsound.Beep(500,100)
        return json.dumps({'code': 0, 'msg': '', 'data': ''})

    # 事件回调接口，监测点操作访问
    def Event_syncPubMsg(self, point, value):
        return json.dumps({'code': 0, 'msg': '', 'data': ''})
