# -*- coding: utf-8 -*-

# /*************************************************************************
#  Copyright (C), 2013-2014, SHENZHEN GONGJIN ELECTRONICS. Co., Ltd.
#  module name: main
#  function: 升级服务器管理
#            
#  Author: ATT development group
#  version: V1.1
#  date: 2013.06.19
#  change log:
#  lana     20130619    created
#  cheng    20130627    changed
# ***************************************************************************
__all__ = ["start"]

import os
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import time
import atexit
import signal
import threading
from Queue import Queue as _queue
CUR_FILE_DIR = os.path.split(os.path.dirname(__file__))[0]
TWISTED_DIR = os.path.join(CUR_FILE_DIR, "vendor")
sys.path.insert(0, CUR_FILE_DIR)
sys.path.insert(0, TWISTED_DIR)


from twisted.internet import reactor
from twisted.web import http

import msgprocess
log = msgprocess.log

# UPGRADE_SERVER_PORT = 8001

class MyQueue(_queue):
    """
    消息队列处理类
    """

    isbusy = False
    _lock = threading.Condition()

    def lock(self):
        self._lock.acquire()
        while self.isbusy:
            self._lock.wait()
        self.isbusy = True

    def unlock(self):
        self.isbusy = False
        self._lock.notifyAll()
        self._lock.release()

    def clear(self):
        """
        每两小时清理一次队列
        """
        log.debug("清理过期的序列号")
        self.lock()
        serial_list = []
        count = 0
        while not self.empty():
            element = self.get()
            if not element:
                continue
            serial_no = element.popitem()[0]
            now = time.time()
            upload_time = time.mktime(time.strptime(serial_no,'%Y%m%d%H%M%S'))
            if now - upload_time < 3600:
                serial_list.append(element)
            else:
                log.debug("清理序列号%s"%serial_no)
                count+=1
        for serial in serial_list:
            self.put(serial)
        self.unlock()
        log.debug("%s个被清理，将在2小时后重新清理。"%count)
        reactor.callLater(2*3600, self.clear)
#消息队列，存放上传文件序列号对应的属性及路径

queue = MyQueue()

def root_dispath_event(conn,q):
    """
    """
    msg_handle = msgprocess.MsgProcess(conn,q)
    if msg_handle.is_available():
        try:
            msg_handle.parse_msg()
        except Exception,e:
            error_info = "there are some unknown wrong on the server:\n%s"%e
            log.exception(error_info)
            msg_handle.response_fail(error_info)



def handle_dispath_request(request):
    """
    """

    # msg = request.content.read()
    conn = request
    global queue
    t = threading.Thread(target=root_dispath_event, args=(conn,queue))
    t.setDaemon(True)
    t.start()
    log.debug("启动线程%s处理消息"%t.name)



class UpgradeHandleRequest(http.Request):
    """
    """
    # 定义了路径映射功能
    dict_page_handlers={
        "/upgrade"  :   handle_dispath_request,
        "/upload"   :   handle_dispath_request,
        "/download" :   handle_dispath_request,
    }

    def process(self):
        """
        """

        self.setHeader("Content-Type","text/html")
        log.debug("收到消息")
        if self.dict_page_handlers.has_key(self.path):
            handler=self.dict_page_handlers[self.path]
            handler(self)

        else:
            self.setResponseCode(http.NOT_FOUND)
            self.write("<h1>Not Found</h1>Sorry, no such page.")
            self.finish()
            self.transport.loseConnection()


class UpgradeHttpChannel(http.HTTPChannel):
    requestFactory=UpgradeHandleRequest

    def connectionLost(self, reason):
        sessionno = self.transport.sessionno
        log.info("连接断开(%s:%s)"%self.transport.client)
        http.HTTPChannel.connectionLost(self, reason)

    def lineReceived(self, line):
        # print line
        http.HTTPChannel.lineReceived(self,line)


class UpgradeHttpFactory(http.HTTPFactory):
    protocol = UpgradeHttpChannel
    def buildProtocol(self, addr):
        log.info("%s连接"%addr)
        p = http.HTTPFactory.buildProtocol(self,addr)
        return p

def start_upgrade_server(port):
    try:
        #启动时，根据当前存放文件结构初始化配置文件add by chenguo 07-08
        log.info("初始化配置文件...")
        msgprocess.XmlRepairer().reBuild()
        log.debug("初始化消息处理映射表...")
        msgprocess.MsgProcess.map_action_handle()
        log.debug("数据文件存放路径:%s"%os.path.abspath(msgprocess.DATA_DIR))
        reactor.listenTCP(port, UpgradeHttpFactory())
        log.info("启动升级服务器，端口%s..."%port)
        queue.clear()
        reactor.run()

    except Exception,e:
        err_info = "升级服务器启动异常: \n".decode("utf8")
        #windows 下 socket异常信息编码为gbk,这里讲需要打印的错误信息转为unicode
        log.exception(err_info + e.message.decode(sys.stderr.encoding))
        sys.exit()

def on_stop(signum, frame):
    log.info("升级服务器关闭中...")
    reactor.stop()
    log.info( "Server Stop!\n\n"+"*"*50)

@atexit.register
def stop_upgrade_server():
    #程序退出
    if 'nt' in sys.builtin_module_names:
        os.system("pause")

def start(port):
    signal.signal(signal.SIGTERM, on_stop)
    signal.signal(signal.SIGINT, on_stop)
    #检查配置文件是否加载
    if not msgprocess.CONF_OK:
        ex = IOError("配置文件无法被解析，请确认文件%s是否存在" % msgprocess.CONF_FILE_PATH)
        log.error(ex)
        log.info("下面一个配置文件部分内容的例子：%s"%msgprocess.data_path_config_eg)
        return 0
    #启动
    sys.stdout.write('\n'+"*"*50+'\n')
    log.debug("\n"+"debug model".center(50,'*'))
    log.info( "Server start!")


    start_upgrade_server(port)

# if __name__ == '__main__':
#     start(UPGRADE_SERVER_PORT)

