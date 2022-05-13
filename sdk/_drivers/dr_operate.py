#!coding:utf8
import json
import sys

sys.path.append("..")
from driver import *
import threading
import time
import MySQLdb

class Demo(IOTOSDriverI):

    def user(self):
        db = MySQLdb.connect(host='172.20.0.2', port=3307, db='jshop', user='root', passwd='123456', charset='utf8')
        cursor = db.cursor()
        sql = "SELECT count(*) FROM `jshop_user` group by grade"
        try:
            cursor.execute(sql)
            results = cursor.fetchall()
            all = int(results[0][0]) + int(results[1][0])
            self.setValue(u'数据大屏运营.普通会员', int(results[0][0]))
            self.setValue(u'数据大屏运营.高级会员', int(results[1][0]))
            self.setValue(u'数据大屏运营.会员总数', all)
        except:
            print "Error: unable to fecth data"
        db.close()
        self.timer5 = threading.Timer(10, self.user)
        self.timer5.start()

    # 1、通信初始化
    def InitComm(self, attrs):
        self.online(True)
        self.timer1 = threading.Timer(1, self.user)
        self.timer1.start()


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
        # winsound.Beep(500, 100)
        return json.dumps({'code': 0, 'msg': '', 'data': ''})


    # 事件回调接口，监测点操作访问
    def Event_syncPubMsg(self, point, value):
        return json.dumps({'code': 0, 'msg': '', 'data': ''})
