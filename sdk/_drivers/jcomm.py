# coding=utf-8

import gevent
from gevent.server import StreamServer
import traceback
import sys
from routelib.jlib import *
import threading

##tcp server
class TcpServer(StreamServer,JLib):
    def __init__(self, listener, **kwargs):
        self.port = int(listener[1])
        self.deviceSockets = []
        self.iotosAdmin = None          #数据回现，以及包括设备、master在内的群收、群发
        self.iotosProxy = None          #在admin基础上，不支持回显、与master隔离
        self.driver = None              #added by lrq 20200115 加上驱动实例
        StreamServer.__init__(self, listener,handle = self.echo, **kwargs)
        JLib.__init__(self)

    def setCallback(self,driver,cbData = None,cbEvent = None):
        self.driver = driver
        self.__callback = (cbData,driver.tcpCallback)[cbData == None]
        self.__connectEvent = (cbEvent, driver.connectEvent)[cbEvent == None]

    # this handler will be run for each incoming connection in a dedicated greenlet
    def echo(self, socket, address):
        self.deviceSockets.append(socket)
        serverInfo = 'server ' + str(self.port)

        #temp edit by lrq 20220501,avoid response mechanism
        #socket.sendall(b'welcome to iotos!.\r\n')

        # using a makefile because we want to use readline()
        self.warn(serverInfo +  ' client %s:%s connected.' % address)
        self.__connectEvent(True)
        rfileobj = socket.makefile(mode='rb')
        while True:
            try:
                line = None
                line = socket.recv(8192)
            except Exception as e:
                self.exception(e)
                self.driver.zm.exit_to_reboot()
                continue
            if not line:
                self.warn(serverInfo + 'client %s:%s disconnected!!' % address)
                if socket == self.iotosAdmin:
                    self.warn(u'IOTOS管理员退出！')
                    self.iotosAdmin = None
                elif socket == self.iotosProxy:
                    self.warn(u'IOTOS代理器退出！')
                    self.iotosProxy = None
                else:
                    #by lrq 20191020 下面有break，而且循环退出后面有调用断开事件，这里就重复了，屏蔽掉
                    # self.__connectEvent(False)
                    self.deviceSockets.remove(socket)
                break
            try:
                if line.strip().lower().find(b'this is iotos admin') >=0:
                    self.warn(u'IOTOS管理员进入.')
                    self.iotosAdmin = socket
                    socket.sendall(b'iotos admin recognized!')
                    self.deviceSockets.remove(socket)
                    continue
                if line.strip().lower().find(b'this is iotos proxy') >=0:
                    self.warn(u'IOTOS代理连入.')
                    self.iotosProxy = socket
                    socket.sendall(b'iotos proxy recognized!')
                    self.deviceSockets.remove(socket)
                    continue

                #如果是IOTOS管理员或者代理器，那么这个数据也会广播分发给其他各个设备！
                if socket == self.iotosAdmin or socket == self.iotosProxy:
                    self.send(line)
                    if socket == self.iotosProxy:   #仅仅是代理器的话，将不会跟master交互，发给设备后，continue掉！
                        continue
                # 设备那边发过来的数据，同时也会派发给到管理员，以及代理器
                else:
                    if self.iotosAdmin:
                        self.iotosAdmin.sendall(line)
                    if self.iotosProxy:
                        self.iotosProxy.sendall(line)

                #设备那边发过来的数据，进行处理（丢给虚拟串口modbus master）,管理员过来的数据也会给master
                if self.__callback is not None:
                    self.__callback(line)
                else:
                    self.warn('setting callback error!')

            except Exception as e:
                self.exception(e)

        rfileobj.close()
        self.__connectEvent(False)

    def send(self,value):
        #单独发送给连接进来的管理员
        try:
            if self.iotosAdmin:
                self.iotosAdmin.sendall(value)
        except Exception as e:
            traceback.print_exc(e)

        #广播连接到同个端口的多个设备
        try:
            for socket in self.deviceSockets:
                socket.sendall(value)
        except Exception as e:
            #连接断开时，tcp句柄清空！
            self.deviceSockets = []
            self.__connectEvent(False)
            self.exception(e)

    def open(self,ip_port = None):
        self.serve_forever()

########################################################################

##tcp server
class TcpServerThread(threading.Thread, JLib):
    def __init__(self, driver, param):
        super(TcpServerThread, self).__init__()
        JLib.__init__(self)
        self.driver = driver
        self.param = param

    def run(self):
        try:
            self.tcp = TcpServer(('0.0.0.0', int(self.param)))
            self.tcp.setCallback(self.driver)                               #要求调用者提供connectEvent和tcpCallback这两个方法用于回调！！！
            self.tcp.open()
        except:
            traceback.print_exc()

    def send(self, data):
        self.tcp.send(data)

########################################################################

##带自动重连功能的tcp client!!
import socket
import time
class TcpClient(threading.Thread,JLib):
    def __init__(self, server_params = None, **kwargs):
        self.ip_port = server_params
        self.clientSocket = socket.socket()
        threading.Thread.__init__(self)
        self.dataRecv = None
        self.connected = False
        JLib.__init__(self)

    def setCallback(self,callback):
        self.__callback = callback

    def run(self):
        while True:
            try:
                if not self.connected:
                    self.__connect()
                self.dataRecv = self.clientSocket.recv(8192)
                if not self.dataRecv:
                    self.warn('connection closed!')
                    self.connected = False
                else:
                    self.__callback(self.dataRecv)
            except socket.error:
                self.error('connection lost! reconnecting...')
                self.__connect()

    def __connect(self):
            self.connected = False
            self.clientSocket = socket.socket()
            while not self.connected:
                try:
                    self.warn('connecting...')
                    self.clientSocket.connect(self.ip_port)
                    self.connected = True
                    self.notify_connected()
                    self.warn('connect successful!')
                except socket.error:
                    self.error(socket.error)
                    self.error('connect failed,retrying…')
                    time.sleep(2)

    def notify_connected(self):
        pass

    def send(self,value):
        try:
            if not self.connected:
                self.info(u'send failed!not connected！')
                return False
            else:
                self.info('<<------',''.join(format(x, ' 02x') for x in value))
                rt = False
                try:
                    rt = self.clientSocket.send(value)
                except Exception as e:
                    traceback.print_exc(e)
                return rt
        except Exception as e:
            traceback.print_exc(e)
            return False

    def open(self,ip_port):
        self.ip_port = ip_port
        self.setDaemon(True)
        self.start()

########################################################################

#虚拟串口
import platform
sys = platform.system()
if sys == "Windows":
    pass
elif sys == "Linux":
    import pty
else:
    pass

import os
import select

class ExchangeDataThread(threading.Thread,JLib):
    def __init__(self, m, m2):
        super(ExchangeDataThread, self).__init__()
        self.__m = m
        self.__m2 = m2

    def run(self):
        while True:
            try:
                rl, wl, el = select.select([self.__m, self.__m2], [], [], 1)
                for master in rl:
                    data = os.read(master, 128)
                    # self.info("exchange %d data." % len(data))
                    if master == self.__m:
                        os.write(self.__m2, data)
                    else:
                        os.write(self.__m, data)
            except Exception as e:
                traceback.print_exc(e)

##串口类
#注意，虽然导入时serial，但是必须有安装pyserial模块！！不是仅仅serial就行的！
import serial
class SerialDtu(threading.Thread,JLib):
    def __init__(self, serial_params = None):
        JLib.__init__(self)
        threading.Thread.__init__(self)
        self.__saveConverted(serial_params)
        self.serial = None

    def setCallback(self,callback):
        self.__callback = callback

    def portName(self):
        return self.slaveName

    def __commInit(self):
        self.info('create serial port…')

        master, slave = pty.openpty()
        self.slaveName = os.ttyname(slave)

        master2, slave = pty.openpty()
        self.slaveName2 = os.ttyname(slave)

        self.info(self.slaveName + ' < - > ' + self.slaveName2)

        self.serial = self.openSerialPort(self.slaveName)
        self.serial2 = self.openSerialPort(self.slaveName2)
        if self.serial == None or self.serial2 == None:
            time.sleep(5)
            self.__commInit()

        t = ExchangeDataThread(master,master2)
        t.setDaemon(True)
        t.start()

        self.info('open succeed!')

    def openSerialPort(self,name):
        try:
            return serial.Serial(name,                                       #串口
                                 int(self.serial_params[1]),                 #波特率    9600
                                 parity = self.serial_params[2],             #奇偶校验  N
                                 bytesize= int(self.serial_params[3]),       #位数     8
                                 stopbits = int(self.serial_params[4]))      #停止位   1
        except Exception as e:
            self.error('open failed!' + str(e) + '.retrying…')
            return None

    def run(self):
        while True:
            dataHex = bytes()
            try:
                n = self.serial2.inWaiting()
                if n:
                    dataHex += self.serial2.read(n)
                    # self.info('------>>' + ''.join(format(x, ' 02x') for x in dataHex))
                    self.__callback(dataHex)
            except Exception as e:
                traceback.print_exc(e)

    def send(self,value):
        if self.serial2 is None:
            self.info('port not opend!send failed!')
            return False
        # self.info('<<------'.join(format(x, ' 02x') for x in value))
        return self.serial2.write(bytes(value))

    def __saveConverted(self,params):
        if params:
            self.serial_params = [param for param in params.strip().split(',')]
            self.info(u'串口参数：' + params)

    def open(self,serial_params = None):
        self.__saveConverted(serial_params)
        self.__commInit()
        self.setDaemon(True)
        self.start()


########################################################################


if __name__ == '__main__':
    #tcp服务器
    s = TcpServer(('0.0.0.0',4001))
    s.open()

    #tcp客户端
    # cl = TcpClient(('192.168.199.226',7070))
    # cl.open()
    # while not cl.connected:
    #     pass
    #
    # while True:
    #     print(cl.send('hello world!'.encode('utf-8')))
    #     time.sleep(1)

    # #串口
    # s = SerialDtu()
    # s.open(('COM3',38400,7,'E',1))
    # while True:
    #     s.send('hello world'.encode('utf-8'))
    #     time.sleep(3)
    #     pass