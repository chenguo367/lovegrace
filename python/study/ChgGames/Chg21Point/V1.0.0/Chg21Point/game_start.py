#coding:utf-8
__author__ = 'chenguo'
__doc__ = """21点牌游戏界面逻辑。
"""
__version__ = "v1.0.0"
_changeLog =\
"""2013-07-16： 21点单机版功能完成
"""

import re
import time
import sys
reload(sys)
sys.setdefaultencoding('GB2312')

from ui.window import *
from core.py_21_point import count_21_point
from model.Poker import PokerPool

class Py21PointGame:
    """单机版，可扩展为网络版"""
    target = 21
    #显示花色
    show_suit = True
    #统计数据
    show_audit = True
    def __init__(self,pokercount = 4):
        self.audit_dict = {
            'Right' : 0,
            'Error' : 0,
            'Average' : '',
            'pack of poker': 1,
        }
        self.pkp = PokerPool()
        self.wantexit = False
        self.introduce()
        self.start(pokercount)

    def introduce(self):
        """介绍规则"""
        self.send("")
        self.show_suit = self.getConfData(u"是否需要显示扑克花色?")
        self.show_audit = self.getConfData(u"是否需要统计数据?")
        self.getData(u"按任意键开始...")

    def createQuestion(self,pokercount):
        """出题"""
        pklist = self.pkp.getPokers(pokercount)
        card_list = [pk.show_pic for pk in pklist]
        table_window = window_v1(7,pokercount * 6)
        for index in range(pokercount):
            table_window.append(card_list[index], [1, index * 6 + 1])
        args = [pk.value for pk in pklist]
        sys.stdout.write("loading...\n")
        solution = count_21_point(self.target,True,tuple(args))
        if not solution :
            table_window,solution = self.createQuestion(pokercount)
            return table_window,solution

        if self.show_suit:
            suit_info = [pk.title for pk in pklist]
            table_window = ' '+' '.join(suit_info)+str(table_window)
        return table_window,solution

    def start(self,pokercount):
        while not self.wantexit:
            question,solution = self.createQuestion(pokercount)
            #统一sendAsk出口为utf-8
            if isinstance(question,unicode):
                question = question.encode('utf-8')
            self.sendAsk(str(question))
            starttime = time.time()
            while True:
                answer = self.getData("input your answer:\n")
                if answer and self.verify(answer,solution):
                    spend_time = self.getTotalTime(starttime)
                    info = "good job."
                    if self.show_audit:
                        info += "spend time : %ds"%int(spend_time)
                    self.send(info)
                    break
                else:
                    self.send( "your answer:'%s' is not correct."%answer)
                    retry = self.getConfData("want retry?")
                    if retry:
                        continue
                    else:
                        self.showAnswer(solution)
                        break
            goon = self.getConfData("want next one?:")
            if not goon:
                self.wantexit = True
            else:
                continue
        else:
            self.stop()

    def stop(self):
        """程序退出"""
        self.send("88")
        sys.exit()


    def getTotalTime(self,starttime):
        return time.time() - starttime

    def sendAsk(self,ask_data):
        return self.send(ask_data)

    def send(self,data):
        """overwrite it"""
        #统一出口为unicode
        if isinstance(data,str):
            data = data.decode("utf-8")
        print data
        return len(data)

    def getData(self,prompt):
        quit_flags = ['q','quit()','exit','exit()']
        if isinstance(prompt,str):
            prompt = prompt.decode("utf-8")
        try:
            data = raw_input(prompt)
            if data.lower() in quit_flags:
                self.stop()
            return data
        except Exception,e:
            self.send('\nuser cancels..')
            self.stop()

    def getConfData(self,prompt,defaultYes = True):
        notic = "(Y/n)"
        if not defaultYes:
            notic = "(N/y)"
        conf = self.getData(prompt+notic)
        if defaultYes:
            if conf.lower()!='n':
                return True
            else:
                return False
        else:
            if conf.lower()!='y':
                return False
            else:
                return True

    def verify(self,rcv_data,solution):
        """验证结果"""
        rcv_data = rcv_data.lower()
        rcv_data = rcv_data.replace("a","1")
        rcv_data = rcv_data.replace("j","11")
        rcv_data = rcv_data.replace("q","12")
        rcv_data = rcv_data.replace("k","13")
        regex = r"[+/()\-\*]+"
        sep = '_'
        try:
            result = eval(rcv_data)
            if result != self.target:
                raise
        except:
            return 0
        user_input = re.sub(regex, sep, rcv_data)
        if isinstance(solution,list):
            solution = solution[0]
        benchmark = re.sub(regex, sep, solution)
        user_input = user_input.strip(sep).split(sep)
        benchmark = benchmark.strip(sep).split(sep)
        for num in user_input:
            if num not in benchmark:
                return 0
            benchmark.remove(num)
        return 1

    def showAnswer(self,solution):
        """显示答案"""
        return self.send( "the solution : "+' or '.join(solution))

class Py21PointGameServer(Py21PointGame):
    """网络版"""
    pass


if __name__ == '__main__':
    p = Py21PointGame(4)