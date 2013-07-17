#coding:utf-8
__doc__ = """进度条(http://blog.chinaunix.net/uid-23504396-id-267420.html)
"""

import sys
class ProcessSchedule(object):
    """
    This class use to print porecess schedule
    ImgLong usr to define max long of img and it will be set as 20 or  n*50
    """
    def  __init__(self,maxid =1,ImgLong=50,startPercent = 0):
        """self.percenct is the cur percence of porcess"""
        self.percnet = startPercent
        self.ImgLong = ImgLong
        self.maxid = maxid

    def PrintSchedule(self,curid):
        if curid > self.maxid:
            self.PrintSchedule(self.maxid)
        if self.ImgLong < 50:
            self.ImgLong = 20
        if self.ImgLong > 50:
            self.ImgLong = (int(self.ImgLong/50))*50
        self.percent = int((curid*100)/self.maxid)
        rangeStep = int(100/self.ImgLong)
        if rangeStep == 0:rangeStep =1
        i = self.percent
        count = int((i*self.ImgLong)/100)
        img = '#' * count
        nul = ' ' * (self.ImgLong - count)
        if self.percent < 10:
            sys.stdout.write(img + nul + "  " + str(self.percent) + '%')
        if self.percent >= 10 and self.percent < 100:
            sys.stdout.write(img + nul + " " +str(self.percent) + '%')
        if self.percent == 100:
            sys.stdout.write(img + nul + '100%')
            #
            sys.stdout.write('\ncompleted!\n')
        sys.stdout.write('\r')
        sys.stdout.flush()

if __name__ == '__main__':
    i=0
    done = False
    while not done and i<100:
        ProcessSchedule(100).PrintSchedule(i)
        i+=1
        import time
        time.sleep(0.12)
    else:
        ProcessSchedule(100).PrintSchedule(i)
        done = True

