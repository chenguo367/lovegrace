#!/usr/bin/python
#coding:utf-8
__author__ = 'chenguo'
__all__ = ["setting","setDefault","on","off"]
import config_tool as _

setting = _.setting
setDefault = _.setDefault
on = _.on
off = _.off
__doc__ = """以下函数提供对权限管理模块的配置文件进行配置的接口:
setting :%s
setDefault :%s
on :%s
off :%s
"""%(setting.__doc__,setDefault.__doc__,on.__doc__,off.__doc__)
print __doc__.decode("utf8")
