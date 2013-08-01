#coding:utf-8
__author__ = 'chenguo'

from utils import unjson,json
from gameProtocol import *
class MsgParse(object):
    msg = ''
    def __init__(self,data,client):
        try:
            self.msg = unjson(data)
        except:
            pass
        self.client = client
        self.factory = client.factory
        self.send = client.send
        if self.msg and isinstance(self.msg,dict) and self.msg[msg_type] == "request":
            self.parse()

    def parse(self):
        for cg in [1]:
            _action = self.msg.get(msg_action)
            action = getattr(self,_action,None)
            if not action:
                res_str = MsgConstruct.build_fail_response(self.msg,"no action:%s"%_action)
                self.send(res_str)
                break
            action()

    def login(self):
        def check_username(self,name):
            if not self.client.username:
                if name not in self.factory.cm.namelist:
                    self.client.username = name
                    info = "hello : %s"%name
                    welcome = "welcome new player:%s"%name
                    self.factory.sendAll(welcome)
                    res_str = MsgConstruct.build_suc_response(self.msg,self.msg[msg_data],info)
                    self.send(res_str)
                    self.factory.cm.namelist.append(name)
                else:
                    res_str = MsgConstruct.build_fail_response(self.msg,"the name is already exists")
                    self.send(res_str)
        if self.client.username:
            res_str = MsgConstruct.build_fail_response(self.msg,"you already have a name :%s"%self.client.username)
            self.send(res_str)
        username = self.msg.get(msg_data).get("username","")
        if not username :
            res_str = MsgConstruct.build_fail_response(self.msg,"must have a name")
            self.send(res_str)
        check_username(self,username)

    def start(self):
        question = self.factory.getGameQuestion()
        if not self.msg:
            self.msg = buildMsg({},'start',"request",question)
        res_str = MsgConstruct.build_suc_response(self.msg,self.msg[msg_data],question)
        self.send(res_str)

    def verify(self):
        user_answer = self.msg.get(msg_data).get("user_answer","")
        if not user_answer:
            #client judge
            pass
        if self.factory.verifyAnswer(user_answer):
            res_str = MsgConstruct.build_suc_response(self.msg,self.msg[msg_data],"good job")
            self.send(res_str)
            #notic server
            self.factory.notic(self.client.username)
        else:
            res_str = MsgConstruct.build_fail_response(self.msg,"you are wrong")
            self.send(res_str)

class MsgConstruct(object):
    def __init__(self,):
        pass

    @staticmethod
    def build_fail_response(request_msg,des):
        _msg_data = request_msg [msg_data]
        _msg_action = request_msg [msg_action]
        response_msg_data = _msg_data
        response_msg_action = _msg_action
        response_msg_type = 'response'
        response_msg_des = des
        response_msg_data['succeed'] = False
        res_msg = buildMsg(response_msg_data,response_msg_action,response_msg_type,response_msg_des)
        return json(res_msg)

    @staticmethod
    def build_suc_response(request_msg,data,des,):
        _msg_action = request_msg [msg_action]
        response_msg_data = data
        response_msg_action = _msg_action
        response_msg_type = 'response'
        response_msg_des = des
        response_msg_data['succeed'] = True
        res_msg = buildMsg(response_msg_data,response_msg_action,response_msg_type,response_msg_des)
        return json(res_msg)

    @staticmethod
    def build_login_request(name ):
        data = Msg_Login(name)
        action = "login"
        msg_type_ = "request"
        des = ""
        res_msg = buildMsg(data,action,msg_type_,des)
        return json(res_msg)

    @staticmethod
    def buil_start_request():
        data = {}
        action = "start"
        msg_type_ = "request"
        des = ""
        res_msg = buildMsg(data,action,msg_type_,des)
        return json(res_msg)

    @staticmethod
    def buil_verify_request(answer):
        data = {}
        action = "verify"
        msg_type_ = "request"
        des = ""
        data["user_answer"] = answer
        res_msg = buildMsg(data,action,msg_type_,des)
        return json(res_msg)