#!coding:utf8
import json
import sys

sys.path.append("..")

from driver import *
import threading
import time
import MySQLdb
import pymssql
import datetime

class Demo(IOTOSDriverI):
    year = datetime.datetime.now().year
    month = datetime.datetime.now().month
    day = datetime.datetime.now().day
    if month < 10:
        samemonth = "0" + str(month)
        lastmonth = "0" + str(month - 1)
    else:
        samemonth = str(month)
        lastmonth = str(month - 1)
    def lastMouthPower(self):
        days = []
        theday = 31
        while theday> 0:
            if theday < 10:
                day2 ="0"+str(theday)
            else :
                day2 = str(theday)
            theday -= 1
            days.append(day2)
        sum = 0
        db = MySQLdb.connect("192.168.255.102", "root", "mysql", "BMAX4.0_Project_1_1", charset='utf8')
        cursor = db.cursor()
        for index in days:
            try:
                sql = "SELECT SUM(VALUE) FROM (SELECT VALUE FROM IO_TagValueHistory_%s%s%s WHERE VALUE !=0 AND tagid " \
                  "LIKE '03%%' GROUP BY tagid DESC) AS a" %(self.year,self.lastmonth,index)
                cursor.execute(sql)
                num = cursor.fetchone()
                sum = float(num[0]) + sum
            except:
                continue
        self.setValue(u'数据大屏.上月总电功', sum)
        db.close()
        self.timer7 = threading.Timer(5, self.lastMouthPower)
        self.timer7.start()

    def mouthPower(self):
        days = []
        sum = 0
        today = self.day
        while today>0:
            if today < 10:
                day2 = "0" + str(today)
            else:
                day2 = str(today)
            days.append(day2)
            today -= 1
        db = MySQLdb.connect("192.168.255.102", "root", "mysql", "BMAX4.0_Project_1_1", charset='utf8')
        cursor = db.cursor()
        for index in days:
            try:
                sql = "SELECT SUM(VALUE) FROM (SELECT VALUE FROM IO_TagValueHistory_%s%s%s WHERE VALUE !=0 AND tagid " \
                  "LIKE '03%%' GROUP BY tagid DESC) AS a" %(self.year,self.samemonth,index)
                cursor.execute(sql)
                num = cursor.fetchone()
                sum = float(num[0]) + sum
            except:
                continue
        self.setValue(u'数据大屏.当月总电功', sum)
        db.close()
        self.timer6 = threading.Timer(5, self.mouthPower)
        self.timer6.start()

    def equipment(self):
        db = MySQLdb.connect("192.168.255.102", "root", "mysql", "BMAX4.0_Project_1_1", charset='utf8')
        cursor = db.cursor()
        try:
            sql = "SELECT COUNT(DeviceID) FROM `IO_Tag` AS t INNER JOIN IO_TagValue AS v WHERE t.`ID`=v.`TagID` AND v.`Value`!=0 "
            cursor.execute(sql)
            online = cursor.fetchone()
            self.setValue(u'数据大屏.在线设备总数', int(online[0]))
            sql = "SELECT COUNT(*) FROM `IO_Tag`"
            cursor.execute(sql)
            sum = cursor.fetchone()
            self.setValue(u'数据大屏.设备总数', int(sum[0]))
        except:
            print "Error: unable to fecth data"
        db.close()
        self.timer5 = threading.Timer(5, self.equipment)
        self.timer5.start()

    def carPoint(self):
        connect = pymssql.connect('192.168.255.104', 'sa', '', 'pk')
        try:
            cursor = connect.cursor()
            sql = "select count(*) from Cpcv20_CarState"
            cursor.execute(sql)
            sum = cursor.fetchone()
            self.setValue(u'数据大屏.停车位总量', sum[0])
            sqls = "select count(*) from Cpcv20_CarState where P_CarSTATE = 2"
            cursor.execute(sqls)
            surplus = cursor.fetchone()
            self.setValue(u'数据大屏.剩余停车位', surplus[0])
        except:
            print "Error: unable to fecth data"
        connect.close()
        self.timer4 = threading.Timer(2, self.carPoint )
        self.timer4.start()

    def selectOnline(self):
        db = MySQLdb.connect("192.168.255.102", "root", "mysql", "BMAX4.0_Project_1_1", charset='utf8')
        cursor = db.cursor()
        id=['010001','020001','030001','030002','030003','030004','040001']
        results=[]
        try:
            for index in range(len(id)):
                sql = 'SELECT COUNT(DeviceID) FROM `IO_Tag` AS t INNER JOIN IO_TagValue AS v WHERE t.`ID`=v.`TagID` AND v.`Value`!=0 AND DeviceID = %s ' % (
                    id[index])
                cursor.execute(sql)
                result = cursor.fetchone()
                results.append(int(result[0]))
            self.setValue(u'数据大屏.门禁设备在线', results[0])
            self.setValue(u'数据大屏.广播设备在线', results[1])
            self.setValue(u'数据大屏.能耗13在线', results[2])
            self.setValue(u'数据大屏.能耗14在线', results[3])
            self.setValue(u'数据大屏.能耗18在线', results[4])
            self.setValue(u'数据大屏.能耗19在线', results[5])
            self.setValue(u'数据大屏.楼控设备在线', results[6])
        except:
            print "Error: unable to fecth data"
        db.close()
        self.timer2 = threading.Timer(5, self.selectOnline)
        self.timer2.start()


    def selectAll(self):
        db = MySQLdb.connect("192.168.255.102", "root", "mysql", "BMAX4.0_Project_1_1", charset='utf8')
        cursor = db.cursor()
        all = []
        try:
            sql = "SELECT COUNT(*) FROM `IO_Tag` GROUP BY DeviceID"
            cursor.execute(sql)
            results = cursor.fetchall()
            for row in results:
                all.append(int(row[0]))
            self.setValue(u'数据大屏.门禁设备总数', all[0])
            self.setValue(u'数据大屏.楼控设备总数', all[6])
            self.setValue(u'数据大屏.广播设备总数', all[1])
            self.setValue(u'数据大屏.能耗13总数', all[2])
            self.setValue(u'数据大屏.能耗14总数', all[3])
            self.setValue(u'数据大屏.能耗18总数', all[4])
            self.setValue(u'数据大屏.能耗19总数', all[5])
        except:
            print "Error: unable to fecth data"
        db.close()
        self.timer1 = threading.Timer(10, self.selectAll)
        self.timer1.start()

    def power(self):
        db = MySQLdb.connect("192.168.255.102", "root", "mysql", "BMAX4.0_Project_1_1", charset='utf8')
        cursor = db.cursor()
        id = ['0300010003', '0300010005', '0300010007', '0300010031', '0300010033', '0300010035', '0300010039',
              '0300010041'
            , '0300020003', '0300020005', '0300020007', '0300020031', '0300020033', '0300020035', '0300020039',
              '0300020041']
        results = []
        try:
            for index in range(len(id)):
                sql = 'SELECT VALUE FROM IO_Tag AS t INNER JOIN IO_TagValue AS v WHERE t.`ID`= v.`TagID` AND t.`ID` = %s ' % (
                    id[index])
                cursor.execute(sql)
                result = cursor.fetchone()
                results.append(float(result[0]))
            self.setValue(u'数据大屏.2A03-1-S-WL1北区商一 有功电度', results[0])
            self.setValue(u'数据大屏.2A03-2-S-WL2北区商二 有功电度', results[1])
            self.setValue(u'数据大屏.2A03-3-S-WL3北区商三 有功电度', results[2])
            self.setValue(u'数据大屏.2A06-2-S-WL4东区 有功电度', results[3])
            self.setValue(u'数据大屏.2A06-3-S-WL5东区 有功电度', results[4])
            self.setValue(u'数据大屏.2A06-4-S-WL6东区 有功电度', results[5])
            self.setValue(u'数据大屏.2A07-1-S-WL7东区 有功电度', results[6])
            self.setValue(u'数据大屏.2A07-2-S-WL8东区 有功电度', results[7])
            self.setValue(u'数据大屏.2A03-1-S-WL1北区商一2 有功电度', results[8])
            self.setValue(u'数据大屏.2A03-2-S-WL2北区商二2 有功电度', results[9])
            self.setValue(u'数据大屏.2A03-3-S-WL3北区商三2 有功电度', results[10])
            self.setValue(u'数据大屏.2A06-2-S-WL4东区2 有功电度', results[11])
            self.setValue(u'数据大屏.2A06-3-S-WL5东区2 有功电度', results[12])
            self.setValue(u'数据大屏.2A06-4-S-WL6东区2 有功电度', results[13])
            self.setValue(u'数据大屏.2A07-1-S-WL7东区2 有功电度', results[14])
            self.setValue(u'数据大屏.2A07-2-S-WL8东区2 有功电度', results[15])
        except:
            print "Error: unable to fecth data"
        db.close()
        self.timer3 = threading.Timer(3, self.power)
        self.timer3.start()

    # 1、通信初始化
    def InitComm(self, attrs):
        self.online(True)
        self.timer1 = threading.Timer(1, self.selectAll)
        self.timer1.start()
        self.timer2 = threading.Timer(1, self.selectOnline)
        self.timer2.start()
        self.timer3 = threading.Timer(1, self.power)
        self.timer3.start()
        self.timer4 = threading.Timer(1, self.carPoint)
        self.timer4.start()
        self.timer5 = threading.Timer(1, self.equipment)
        self.timer5.start()
        self.timer6 = threading.Timer(1, self.mouthPower)
        self.timer6.start()

        self.timer7 = threading.Timer(1, self.lastMouthPower)
        self.timer7.start()

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
        #winsound.Beep(500, 100)
        return json.dumps({'code': 0, 'msg': '', 'data': ''})

    # 事件回调接口，监测点操作访问
    def Event_syncPubMsg(self, point, value):
        return json.dumps({'code': 0, 'msg': '', 'data': ''})