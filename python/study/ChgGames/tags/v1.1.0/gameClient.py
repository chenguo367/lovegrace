#coding:utf-8
__author__ = 'chenguo'

import StringIO
import threading
import select
import sys
from twisted.protocols import basic
from twisted.internet import protocol,reactor

from MsgParse import MsgParse,MsgConstruct
from utils import unjson,json


def write(b):
    if isinstance(b,str):
        b = b.decode(sys.stdout.encoding)
    sys.stdout.write((b+'\r\n').encode(sys.stdout.encoding))
    sys.stdout.flush()


class Py21PointGameClientsChannel(basic.LineReceiver):
    """ """
    def connectionMade(self):
         write("connected")

    def lineReceived(self, line):
        rh = ResponseHandle(line)
        rh.protcol = self
        rh.parse()


class Py21PointGameClientsFactory(protocol.ClientFactory):
    protocol = Py21PointGameClientsChannel

class ResponseHandle(object):
    protcol = None
    def __init__(self,line):
        self.msg = line
        self.stream = StreamInput()

    def parse(self):
        try:
            self.msg = unjson(self.msg)
        except:
            pass
        if isinstance(self.msg,str):
            write(self.msg)
            if self.msg.startswith("please input your name"):
                name = ""
                while not name:
                    name = self.stream.getData()
                req_str = MsgConstruct.build_login_request(name)
                self.protcol.sendLine(req_str)
        if isinstance(self.msg,dict):
            self.dostart()

    def dostart(self):
        msg_type = self.msg.get('msg_type')
        action = self.msg.get('msg_action')
        if msg_type!="response":
            print 'bad message:%s'%self.msg
        else:
            write(self.msg.get("msg_des","unknown info"))
        self.dist_path(action)

    def dist_path(self,action):
        data = self.msg.get('msg_data')
        ret = data.get('succeed',False)
        if action == "login":
            if not ret:
                self.msg = "please input your name:"
                self.parse()
            else:
                req_str = MsgConstruct.buil_start_request()
                self.protcol.sendLine(req_str)
        elif action == "start":
            write("your answer:")
            answer = self.stream.getData()
            self.send_answer(answer)
        elif action == "verify":
            if not ret:
                write("your answer:")
                answer = self.stream.getData()
                self.send_answer(answer)

    def send_answer(self,answer):
        req_str = MsgConstruct.buil_verify_request(answer)
        self.protcol.sendLine(req_str)

class StreamInput(object):


    data = ""
    t = None

    def getData(self,prompt=''):
        data = raw_input(prompt)
        return data
    # def getData(self,prompt=''):
    #
    #     self.data = sys.stdin.readline(False)

    # def getData(self,prompt=""):
    #     while 1:
    #         inputs, outputs, errors = select.select([sys.stdin], [], [],1)
    #         if sys.stdin in inputs:
    #             self.data = sys.stdin.readline()
    #             return self.data
    # def getData(self,prompt=""):
    #     if self.t and self.t.is_alive():
    #         raise Exception("123")
    #     self.t = threading.Thread(target=self.getInput, args=(prompt,))
    #     # self.t.setDaemon(True)
    #     self.t.start()
    #     self.t.join()
    #     if not self.data:
    #         self.getData("no input")
    #     return self.data
    #
    #
    # def getInput(self,prompt):
    #     try:
    #         if prompt:
    #             write(prompt)
    #         self.data =  sys.stdin.readline().strip()
    #         return self.data
    #     except KeyboardInterrupt,e:
    #         reactor.stop()
    #         sys.exit()


game_client = Py21PointGameClientsFactory()
reactor.connectTCP("127.0.0.1",9999, game_client)
reactor.run()
