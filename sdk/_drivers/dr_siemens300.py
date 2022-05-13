#!coding:utf8

import sys
sys.path.append("..")
from driver import *
from HslCommunication import SoftBasic
from HslCommunication import SiemensPLCS
from HslCommunication import SiemensS7Net

from bitarray import bitarray

class S7Driver(IOTOSDriverI):
        # 1、通信初始化
    def InitComm(self, attrs):
        desc2data = {}
        for key,value in self.data2attrs.items():
            desc2data[value['description']] = key
        print desc2data

        siemens = SiemensS7Net(SiemensPLCS.S300, self.sysAttrs['config']['tcp'])
        if siemens.ConnectServer().IsSuccess == False:
            print("connect falied")
        else:
            self.online(True)
            # read block
            print("connect succeed!")
            counttmp = 0
            while True:
                counttmp += 1
                print '********* %d **********' % counttmp
                lentmp = 200
                read = siemens.Read('M0', lentmp)
                if read.IsSuccess:
                    for i in range(0, lentmp):
                        numtmp = read.Content[i]
                        if numtmp:
                            statusArray = bitarray(str(bin(numtmp))[2:])
                            statusArray.reverse()
                            lentmp = len(statusArray)
                            for tmp in range(0,8-lentmp):
                                statusArray.append(False)
                            index = 0
                            valtmp = []
                            for bitStatus in statusArray:
                                addrtmp = '%%M%d.%d' %(i,index)
                                if not desc2data.has_key(addrtmp):
                                    index += 1
                                    continue
                                # print '%%M%d.%d' %(i,index), bitStatus
                                self.setValue(self.name(desc2data[addrtmp]),bitStatus)
                                #valtmp.append({'id':self.pointId(desc2data[addrtmp]),'value':bitStatus})
                                index += 1
                            if len(valtmp) != 0:
                                self.setValues(valtmp)
                            # print '+++++++++++++++++++'
                        else:
                            valtmp = []
                            for index in range(0,8):
                                addrtmp = '%%M%d.%d' %(i,index)
                                if not desc2data.has_key(addrtmp):
                                    continue
                                # print addrtmp
                                self.setValue(self.name(desc2data[addrtmp]),False)
                                #valtmp.append({'id':self.pointId(desc2data[addrtmp]),'value':False})
                            if len(valtmp) != 0:
                                self.setValues(valtmp)
            else:
                print(read.Message)
            siemens.ConnectClose()

    # 2、采集引擎回调
    def Collecting(self, dataId):
        time.sleep(0xffff)
        '''*************************************************
        TODO
        **************************************************'''
        return ()

    # 3、控制
    # 广播事件回调，其他操作访问
    def Event_customBroadcast(self, fromUuid, type, data):
        '''*************************************************
        TODO 
        **************************************************'''
        return json.dumps({'code': 0, 'msg': '', 'data': ''})

    # 4、查询
    # 查询事件回调，数据点查询访问
    def Event_getData(self, dataId, condition):
        '''*************************************************
        TODO 
        **************************************************'''
        return json.dumps({'code': 0, 'msg': '', 'data': ''})

    # 5、控制事件回调，数据点控制访问
    def Event_setData(self, dataId, value):
        '''*************************************************
        TODO 
        **************************************************'''
        return json.dumps({'code': 0, 'msg': '', 'data': ''})

    # 6、本地事件回调，数据点操作访问
    def Event_syncPubMsg(self, point, value):
        '''*************************************************
        TODO 
        **************************************************'''
        return json.dumps({'code': 0, 'msg': '', 'data': ''})
