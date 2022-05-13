#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import time
import traceback
import sys
from zmiot import RunCollectingThread


class Config(object):
    pass


class DeviceConfig(Config):
    pass


class Group(object):

    def __init__(self, device):
        self.device = device

    @property
    def name(self):
        if 'type' not in self.device.config:
            return None
        dev_type = self.device.config['type']
        obj = getattr(self, dev_type)
        return '%s_%s' % (dev_type, obj())

    def serialport(self):
        dev_config = self.device.config
        dev_param = dev_config['param']
        dev_parentId = dev_config['parentId']
        dev_port = dev_param['port']

        if dev_parentId == None:
            group_name = '%s_%s' % (self.device.oid, dev_port)
        else:
            group_name = '%s_%s' % (dev_parentId, dev_port)
        return group_name

    def modbus_net(self):
        dev_config = self.device.config
        dev_param = dev_config['param']
        dev_parentId = dev_config['parentId']
        if dev_parentId == None:
            dev_oid = self.device.oid
        else:
            dev_oid = dev_parentId
        md_port = dev_param['port']
        md_host = dev_param['host']
        group_name = '{dev_oid}_{md_host}_{md_port}'.format(dev_oid=dev_oid, md_host=md_host, md_port=md_port)
        return group_name


class Device(object):

    __device = None

    def __init__(self, device):
        self.__device = device

        self.ionode_uuid, self.oid = device['id'].split('.')

    @property
    def config(self):
        return self.__device['config']

    # 采集分组名
    @property
    def collect_group_name(self):
        return Group(device=self).name

import traceback
import json
import sys
import time
from datetime import datetime
import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_tcp
logger = modbus_tk.utils.create_logger("console")


class TcpMaster(modbus_tcp.TcpMaster):
    def _recv(self, expected_length=-1):
        return self._sock.recv(expected_length).strip()

    def execute(self, *args, **kwargs):
        self.open()
        # super(TcpMaster, self).execute()
        msg = {'args': args, 'kwargs': kwargs}
        msg = json.dumps(msg)
        # logger.info(('exc.param', args, kwargs))
        self._send(msg)
        # super(TcpMaster, self).execute()

        recv = self._recv(1024)
        if recv == '':
            return None
        # logger.info(('recv', recv))
        recv = json.loads(recv)
        return recv['result']




modbus_funs = {cst.READ_COILS: cst.WRITE_SINGLE_COIL}
# modbus 网络透传
class ModbusNetCollect(RunCollectingThread):

    # 实例化设备连接
    def new_dev(self, config):
        if 'timeout' not in config:
            config['timeout'] = 10
        self.master = TcpMaster(host=config['host'], port=config['port'], timeout_in_sec=config['timeout'])
        self.master.set_verbose(True)
        logger.info("connected")
        return self.master

    def execute(self, *args, **kwargs):
        return self.master.execute(*args, **kwargs)

    def set_value(self, data_config, value):
        print 'data.config',  data_config
        print 'modbus', modbus_funs[data_config['funid']]
        return self.execute(data_config['devid'], modbus_funs[data_config['funid']], data_config['regad'], output_value=value)

    def get_value(self, param):
        print 'get.value.param', param
        value = self.execute(param['devid'], param['funid'], param['regad'], param['quantity'])
        print 'get.value', value, value[0:param['quantity']]
        return value[0:param['quantity']][0]

    def fetch_value(self, param):
        pass


    collect_group = {"default": []}

    def run(self):
        self.zm.eventcount = self.zm.eventcount + 1
        self.stopt = True

        while self.stopt:
            # collect_group 批量采集分组,
            # group_name = 'default' 默认单独上报

            collect_group = self.zm.m_itemGroup.copy()

            # 单独上报
            data_id_list = []
            if 'default' in collect_group:
                data_id_list = collect_group['default']
                del collect_group['default']
            for point_id in data_id_list:
                if self.zm.restor_collect:
                    break
                if self.zm.pause_collect:
                    self.threadEvent.wait()
                pointValueTmp = self.m_zmCollEngine.collecting(self.zm.m_point2attrs[point_id])

                r = self.zm.PubMsg(point_id, pointValueTmp)

            # 批量上报
            for group_name, dev_param in collect_group.items():
                value_list = self.betch_collecting(dev_param)
                if value_list == None:
                    continue

                r = self.zm.PubMsgs(value_list)
                r = json.loads(r)
                print datetime.now(), 'betch push', r
            time.sleep(60)

    def collecting(self):
        pass

    def betch_collecting(self, dev_param):
        try:
            value_list = []
            quantity = len(dev_param['data_list']) * dev_param['quantity']
            rtu_ret = self.master.execute(dev_param['devid'], dev_param['funid'], dev_param['regad'], quantity)

            setp = 0
            for data_id, q in dev_param['data_list']:
                val = rtu_ret[setp:dev_param['quantity'] + setp]
                setp += dev_param['quantity']
                value_list.append({'id': data_id, 'value': val[0]})

            return value_list

        except Exception as e:
            print traceback.print_exc()
            return None


# modbus rtu
class ModbusRtuCollect(RunCollectingThread):




    collect_group = {"default": []}

    def run(self):
        self.zm.eventcount = self.zm.eventcount + 1
        self.stopt = True

        while self.stopt:
            # collect_group 批量采集分组,
            # group_name = 'default' 默认单独上报

            collect_group = self.zm.m_itemGroup.copy()

            # 单独上报
            data_id_list = []
            if 'default' in collect_group:
                data_id_list = collect_group['default']
                del collect_group['default']
            for point_id in data_id_list:
                if self.zm.restor_collect:
                    break
                if self.zm.pause_collect:
                    self.threadEvent.wait()
                pointValueTmp = self.m_zmCollEngine.collecting(self.zm.m_point2attrs[point_id])

                r = self.zm.PubMsg(point_id, pointValueTmp)

            # 批量上报
            for group_name, dev_param in collect_group.items():
                value_list = self.m_zmCollEngine.betch_collecting(dev_param)

                if value_list == None:
                    continue

                r = self.zm.PubMsgs(value_list)
                r = json.loads(r)
                print 'betch push', r['msg']



class Demo(object):

    @property
    def name(self):
        return 'zeng'

    def __getattr__(self, item):
        print '__getattr__', item
        return None

if __name__ == '__main__':
    demo = Demo()
    print 'name', demo.name


