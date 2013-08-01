#coding:utf-8
__author__ = 'chenguo'
__doc__ = """21点牌游戏网络版服务器
"""
__version__ = "v1.0.0"
_changeLog =\
"""2013-07-24： 21点网络版服务器开始
"""
import time

from twisted.protocols import basic
from twisted.internet import protocol,reactor

from game_start import  Py21PointGame
from MsgParse import MsgParse
class Py21PointGameServerChannel(basic.LineReceiver):
    """"""
    factory = None
    uid = ""

    def __init__(self):
        self.send = self.sendLine
        self.username = ''

    def sendLine(self, line):
        if isinstance(line,unicode):
            line = line.encode('utf8')
        return self.transport.write(line + self.delimiter)
    def connectionMade(self):
        self.send( "please input your name:")
        print "%d connected"%self.factory.connect_num

    def lineReceived(self, line):
        self.do_action(line)

    def do_action(self,line):
        mp = MsgParse(line,self)


    def connectionLost(self, reason):
        print 88
        self.factory.connect_num -= 1
        self.factory.cm.del_client(self.uid)
        if self.username:
            self.factory.cm.namelist.remove(self.username)
            self.factory.sendAll("%s exit"%self.username)


class Py21PointGameServer(protocol.ServerFactory):
    """网络版"""
    connect_num = 0
    protocol = Py21PointGameServerChannel
    cm = None
    gm = Py21PointGame()
    game_finish = True
    question = ''
    solution = ''
    def buildProtocol(self, addr):
        if self.cm is None:
            self.cm = ClientManage()
        print ("%s连接"%addr)
        p = self.protocol()
        p.factory = self
        p.uid = "%s:%s"%(addr.host,addr.port)
        Py21PointGame.send = p.send
        self.connect_num += 1
        self.cm.add_client(p.uid,p)
        return p

    def setTarget(self,num):
        self.gm.target = num

    def getGameQuestion(self):
        if not self.question:
            self.question,self.solution = self.gm.createQuestion(self.gm.pokercount)
        print self.solution
        return self.question.replace('\n',self.protocol.delimiter)

    def verifyAnswer(self,answer):
        return self.gm.verify(answer,self.solution)

    def notic(self,username):
        self.question = ''
        info = "%s has done,game will restart in 3 sec..."%username
        self.sendAll(info)
        reactor.callLater(3, self.restart)

    def restart(self,):
        self.sendAll("a new one...","start")

    def sendAll(self,data,action = None):
        for client in self.cm.client_pool.values():
            client.send(data)
            if action:
                mp = MsgParse("",client)
                do = getattr(mp,action,None)
                if do:
                    try:
                        do()
                    except Exception,e:
                        pass

class ClientManage(object):

    def __init__(self):
        self.client_pool = dict()
        self.namelist = list()

    def add_client(self,uid,clientprotocol):
        self.client_pool[uid] = clientprotocol

    def del_client(self,uid):
        client = self.client_pool.get(uid,None)
        if client is not None:
            self.client_pool.pop(uid)

game_server = Py21PointGameServer()
reactor.listenTCP(9999, game_server)
reactor.run()