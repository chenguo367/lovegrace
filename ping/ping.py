#coding:utf-8
__author__ = 'chenguo'
__doc__ = """实现windows下ping.exe功能
v1.0.0
"""
import os
import ip
import re
import select
import errno
import socket
import icmp
import time
# from twisted.internet import reactor, defer
__all__ = ["PingJob","Ping"]

isip = re.compile("^\d+\.\d+\.\d+\.\d+$").search

class PermissionError(Exception):
    """Not permitted to access resource."""

class PingJob(object):
    """
    Class representing a single target to be pinged.
    """

    def __init__(self, ipaddr):
        self.parent = False
        if isip(ipaddr):
            self.ipaddr = ipaddr
            # self.hostname = socket.gethostbyaddr(ipaddr)[0]
        else:
            self.ipaddr = socket.gethostbyname(ipaddr)
            # self.hostname = ipaddr
        self.reset()



    def reset(self):
        # self.deferred = defer.Deferred()
        self.rrt = 0
        self.start = 0
        self.sent = 0
        self.message = ""
        self.pingtype = "icmp"
        self.max_reply = 0
        self.min_reply = -1
        self.average = 0
        self.lost_count = 0
    def pingSuc(self):
        if self.min_reply <0:self.min_reply = self.rrt
        if self.rrt >self.max_reply:self.max_reply = self.rrt
        if self.rrt <self.min_reply:self.min_reply = self.rrt
        self.average = int(((self.average*(self.sent-self.lost_count-1))+self.rrt)/(self.sent-self.lost_count))
    def pingFail(self):
        self.lost_count+=1
    def pingFinish(self):
        print "\nPing statistics for %s:\n    Packets: Sent = %d, Received = %d, Lost = %d (%d"\
              %(self.ipaddr,self.sent,(self.sent-self.lost_count),self.lost_count,int((self.lost_count*100)/self.sent))+"% loss),"
        print "Approximate round trip times in milli-seconds:\n    Minimum = %dms, Maximum = %dms, Average = %dms"%\
              (self.min_reply,self.max_reply,self.average)



class Ping(object):

    def __init__(self,tries=4,timeout=4,sock =None):
        self.tries = tries
        self.timeout = timeout
        self.procId = os.getpid()
        self.pktdata = 'ping %s %s' % (socket.getfqdn(), self.procId)
        self.createPingSocket(sock)

    def createPingSocket(self, sock):
        """make an ICMP socket to use for sending and receiving pings"""
        socketargs = socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP
        if sock is None:
            try:
                s = socket
                self.pingsocket = s.socket(*socketargs)
            except socket.error, e:
                err, msg = e.args
                if err == errno.EACCES:
                    raise PermissionError("must be root to send icmp.")
                raise e
        else:
            self.pingsocket = socket.fromfd(sock, *socketargs)
            os.close(sock)
        self.pingsocket.setblocking(True)
    def start(self,pj):
        self.sendPacket(pj)
        pj.pingFinish()
    def sendPacket(self, pingJob):
        """Take a pingjob and send an ICMP packet for it"""
        #### sockets with bad addresses fail
        pkt = icmp.Echo(self.procId, pingJob.sent, self.pktdata)
        buf = icmp.assemble(pkt)
        print "Pinging %s with %d buf bytes of data:" % (pingJob.ipaddr,len(buf))
        for i in xrange(self.tries):
            try:
                pingJob.start = time.time()
                # print "send icmp to '%s'"% pingJob.ipaddr
                self.pingsocket.sendto(buf, (pingJob.ipaddr, 0))
                # reactor.callLater(self.timeout, self.checkTimeout, pingJob)
                pingJob.sent += 1
                self.recvPackets(pingJob)
            except (SystemExit, KeyboardInterrupt): raise
            except Exception, e:
                # pingJob.rtt = -1
                pingJob.message = "%s sendto error %s" % (pingJob.ipaddr, e)
                print pingJob.message
                # self.reportPingJob(pingJob)
            time.sleep(1)

    def recvPackets(self,pingJob):
        """receive a packet and decode its header"""
        while time.time() - pingJob.start<self.timeout:
            rl,wl,el = select.select([self.pingsocket],[],[],0)
            if self.pingsocket in rl:
                try:
                    data, (host, port) = self.pingsocket.recvfrom(1024)
                    if not data: return
                    ipreply = ip.disassemble(data)
                    try:
                        icmppkt = icmp.disassemble(ipreply.data)
                    except ValueError:
                        print ("checksum failure on packet %r", ipreply.data)
                        try:
                            icmppkt = icmp.disassemble(ipreply.data, 0)
                        except ValueError:
                            continue            # probably Unknown type
                    except Exception, ex:
                        print ("Unable to decode reply packet payload %s", ex)
                        continue
                    sip =  ipreply.src
                    if (icmppkt.get_type() == icmp.ICMP_ECHOREPLY and
                        icmppkt.get_id() == self.procId and
                        sip == pingJob.ipaddr):
                        pingJob.rrt = (time.time()-pingJob.start)*1000
                        if pingJob.rrt  < 1:
                            time_print = "time<1ms"
                        else:
                            time_print = "time=%dms"%(pingJob.rrt)
                        print "Reply from %s: bytes=%s %s TTL=%d"%(sip,ipreply.len,time_print,ipreply.ttl)
                        pingJob.pingSuc()
                    elif icmppkt.get_type() == icmp.ICMP_UNREACH:
                        try:
                            origpkt = icmppkt.get_embedded_ip()
                            dip = origpkt.dst
                            if (origpkt.data.find(self.pktdata) > -1
                                and dip == pingJob.ipaddr):
                                print ("pj fail for %s", pingJob.ipaddr)

                        except ValueError, ex:
                            print ("failed to parse host unreachable packet")
                    else:
                        pingJob.message = "unexpected pkt %s %s"% (sip, icmppkt)
                        continue
                    break
                except (SystemExit, KeyboardInterrupt): raise
                except socket.error, err:
                    errnum, errmsg = err.args
                    if errnum == errno.EAGAIN:
                        return
                    raise err
                except Exception, ex:
                    print ("receiving packet error: %s" % ex)
                    break
        else:
            print 'Request timed out.'
            pingJob.pingFail()

if __name__ == "__main__":
    pj = PingJob("172.16.28.68")
    Ping().start(pj)