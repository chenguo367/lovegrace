#coding:utf -8
__author__ = 'chenguo'

#
msg_types = ['request','response']
msg_actions = ['login','start',"verify"]
#
msg_data = 'msg_data'
msg_action = 'msg_action'
msg_type = 'msg_type'
msg_des = 'msg_des'

def buildMsg(data,action,type,des):
    msg = dict()
    msg [msg_data] = data
    msg [msg_action] = action
    msg [msg_type] = type
    msg [msg_des] = des
    return msg

def Msg_Login(username):
    data = dict()
    data["username"] = username
    return data


eg = \
{
    msg_data:Msg_Login('test'),
    msg_action:'login',
    msg_type:'request',
    msg_des:'this is the msg will print',
}