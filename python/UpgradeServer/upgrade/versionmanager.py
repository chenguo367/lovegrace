# -*- coding: utf-8 -*-

# /*************************************************************************
#  Copyright (C), 2013-2014, SHENZHEN GONGJIN ELECTRONICS. Co., Ltd.
#  module name: msgprocess
#  function: 各类测试库及平台的版本管理，不同机器号的权限管理
#            
#  Author: ATT development group
#  version: V1.0
#  date: 2013.07.26
#  change log:
#  cheng     20130726    created
# ***************************************************************************

from config import *


#读取配置文件工具函数。
def get_default_access():
    """
    获取可查询的默认版本,如果权限开关关闭，默认全部版本对所有人开放，返回最高权限alpha
    @return: int权限
    """
    global DEFAULT_ACCESS,ENABLE_ACCESS
    try:
        config = load_config(CONF_FILE_PATH)
        enable = config.get("VersionControl","enabled").lower()
        if enable == 'off':
            log.warn("权限控制模块关闭")
            DEFAULT_ACCESS =  ALPHA
            ENABLE_ACCESS = False
        elif enable == 'on':
            #默认开关为on
            ENABLE_ACCESS = True
            default = config.get("VersionControl","default_version").lower()
            if default in ACCESSES.keys():
                DEFAULT_ACCESS =  ACCESSES.get(default)
            else:
                log.warn("未识别的默认版本设置，系统将设置默认版本为：%s"%get_name_by_access(DEFAULT_ACCESS))
        else:
            log.info("版本权限控制开关配置解析失败，系统默认开启。")
            ENABLE_ACCESS = True
    except Exception,e:
        log.exception("配置文件：获取默认版本权限失败:\n%s"%e)
    if ENABLE_ACCESS : log.debug("系统默认可查询的版本为：%s"%get_name_by_access(DEFAULT_ACCESS))
    return DEFAULT_ACCESS


def get_all_accesses():
    """
    获取各个权限下所配置的机器码列表的字典,如果解析失败，抛出异常
    @return:{
        'alpha':['machine_num1','machine_num1',...,],
        'beta':['machine_num3','machine_num4',...,],
        'gamma':['machine_num5','machine_num6',...,],
        'stable':['machine_num7','machine_num8',...,],
    }
    """

    def process(string, delimiter=','):
        """
        将配置文件里的机器码列表字符串解析为机器码列表,分隔符默认为半角逗号,
        @param string:
        @param delimiter:机器码间的分隔符:
        @return:list
        """
        string = string.lower()
        return list(set([s.strip() for s in string.split(delimiter) if s]))

        #配置文件关键字
    section = "MachineAccess"
    delimiter = ','

    config = load_config(CONF_FILE_PATH)
    result = dict()

    tmp_str = config.get(section, alpha)
    result[alpha] = process(tmp_str, delimiter)
    result[beta] = process(config.get(section, beta), delimiter)
    result[gamma] = process(config.get(section, gamma), delimiter)
    result[stable] = process(config.get(section, stable), delimiter)
    return result


def get_version_access( version):
    """
    根据版本号，获取版本类型,返回该版本类型的权限值
    @param version:版本号
    @return:int
    >>>get_version_access('v1.1.0r')
    >>>20
    >>>get_version_access('v1.1.0')
    >>>30
    >>>get_version_access('v1.1.0a')
    >>>0
    >>>get_version_access('v1.1.0b')
    >>>10
    """
    #定义版本命名的解析规则
    VER_ACCESS = {
        'a' :   ALPHA,
        'b' :   BETA,
        'r' :   GAMMA,
    }
    access = STABLE
    for k,v in VER_ACCESS.items():
        if version.endswith(k):
            access = v
    return access


class VersionManager(object):

    def __init__(self,machine_num):
        global ENABLE_ACCESS
        self.default = get_default_access()
        self.uid = machine_num
        if not ENABLE_ACCESS:
            self.access = ALPHA
        else:
            log.debug("开始对机器码：%s 进行版本控制"%machine_num)
            self.access = self.get_self_access_()
            log.info("当前权限：%s"%get_name_by_access(self.access))

    # def get_self_access(self):
    #     """
    #     两种保存形式之一
    #     @return:
    #     """
    #     user_access = self.default
    #     key = self.uid.lower()
    #     try:
    #         access_data = get_all_accesses()
    #         #从低权限到高权限解析（版本向上兼容）
    #         found = 0
    #         if key in access_data[stable]:
    #             user_access = ACCESSES.get(stable)
    #             found +=1
    #         if key in access_data[gamma]:
    #             user_access = ACCESSES.get(gamma)
    #             found +=1
    #         if key in access_data[beta]:
    #             user_access = ACCESSES.get(beta)
    #             found +=1
    #         if key in access_data[alpha]:
    #             user_access = ACCESSES.get(alpha)
    #             found +=1
    #         if not found:
    #             return self.get_self_access_()
    #     except:
    #         log.exception("获取权限信息异常，将使用系统默认权限")
    #     return user_access

    def get_self_access_(self):
        """
        两种保存形式之二,使用这种形式保存，便于解析和人查看
        @return:
        """
        default = self.default
        config = load_config(CONF_FILE_PATH)
        try:
            version = config.get("MachineAccess",self.uid)
            access = ACCESSES.get(version.lower(),None)
            if not access:
                log.warn("无效的权限定义%s，使用默认权限%s"%(version,get_name_by_access(default)))
                access = default
        except:
            log.info("未定义%s的权限，使用默认权限%s"%(self.uid,get_name_by_access(default)))
            access = default
        return access

#test
# print VersionManager('a').access
# print VersionManager('b').access
# print VersionManager('c').access
# print VersionManager('d').access