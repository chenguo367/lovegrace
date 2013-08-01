#coding:utf8
__author__ = 'chenguo'


from twisted.internet import defer,reactor
import time
class test:

    def start(self):
        self.d = defer.maybeDeferred(self.getdata)
        return self.d
    def getdata(self):
        return raw_input("123123")

def process(data):
    print data
    reactor.stop()


d = test().start()
print str(d)
d.addCallback(process)

print 123
reactor.run()

