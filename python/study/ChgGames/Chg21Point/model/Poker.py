#coding:utf-8
import random

from ui.cards import *


class PokerValueError(ValueError):
    """扑克参数异常"""
    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    @staticmethod # known case of __new__
    def __new__(S, *more): # real signature unknown; restored from __doc__
        """ T.__new__(S, ...) -> a new object with type S, a subtype of T """
        pass

class Poker:
    """扑克类，接受1-52的整数进行初始化"""
    suit_dict = {
        0 : u"黑桃",
        1 : u"红桃",
        2 : u"梅花",
        3 : u"方块",
    }
    len_A_K = 13
    def __init__(self,num):
        try:
            num = int(num)
        except TypeError,e:
            raise e
        if num < 1 or num > 52:
            raise PokerValueError(num,"is not allow to create Poker instance")
        quotient , self.value = num/self.len_A_K , num%self.len_A_K
        if self.value == 0:
            #K的情况
            quotient -= 1
            self.value = self.len_A_K
        self.suit = self.suit_dict.get(quotient)
        #扑克的显示A,2,3,4,5,6,7,8,9,10,J,QK
        self.show = str(self.value)
        if self.value == 1:
            self.show = 'A'
        elif self.value == 11:
            self.show = 'J'
        elif self.value == 12:
            self.show = 'Q'
        elif self.value == 13:
            self.show = 'K'
        self.title = ''.join([self.suit,self.show])
        self.show_pic = eval('card_%s'%self.show)
        # print self.show_pic
    def show(self):
        print self.title

    def __str__(self):
        return '\n'.join([self.title,str(self.show_pic)])

    def getValue(self):
        return self.value

class PokerPool:
    """扑克生成池"""
    #记录玩了几副牌
    index = 1
    def __init__(self):
        self.pool = range(1,53)

    def __len__(self):
        return len(self.pool)

    def reset(self):
        # print u"重新洗牌"
        del self.pool
        self.__init__()
        self.index+=1

    def getPokers(self,count = 4):
        pklist = []
        if len(self)==count:
            pklist = map(Poker,self.pool)
            self.reset()
            return pklist
        if len(self)<count:
            self.reset()
        while count>0:
            #在池里面随机抽4张牌
            pknum = self.pool[random.randint(0,len(self)-1)]
            self.pool.remove(pknum)
            pk = Poker(pknum)
            pklist.append(pk)
            count -= 1
        return pklist
