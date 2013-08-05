# -*- coding: utf-8 -*-

# /*************************************************************************
#  Copyright (C), 2013-2014, SHENZHEN GONGJIN ELECTRONICS. Co., Ltd.
#  module name: xmloperate
#  function: 设置全局变量，配置文件目录
#
#  Author: ATT development group
#  version: V1.0
#  date: 2013.07.19
#  change log:
#  cheng    20130719    created
# ***************************************************************************

import os
import ConfigParser

from utils import Logger

log = Logger().getLogger('upgradeserver')

#开始设置全局变量
#程序根目录
ROOT_DIR = os.path.split(os.path.dirname(__file__))[0]
os.chdir(ROOT_DIR)
#文件目录配置开始
#数据文件路径在配置文件中定义
#add by cheng 2013-07-19
#配置文件名
config_file_name = "upgrade.cgf"
#程序配置文件信息
conf_dir = os.path.join(ROOT_DIR, 'config')
if not os.path.exists(conf_dir):os.makedirs(conf_dir)
CONF_FILE_PATH = os.path.join(conf_dir, config_file_name)
#清除win32下notepad编辑系统配置文件后，在文件头添加的BOM信息
from codecs import BOM_UTF8
def clean_bom(_file):
    with open(_file,'rb') as f:
        data = f.read()
        f.close()
    if data[:3] == BOM_UTF8:
        data = data[3:]
        wf = open(_file, 'wb')
        wf.write(data)
        wf.close()
    return _file

#这是以前版本的文件目录设置，直接写死。
DATA_DIR = os.path.join(ROOT_DIR, 'data','upgrade')

#配置文件解析
def load_config(files):
    c = ConfigParser.ConfigParser()
    if isinstance(files,str):
        files = [files]
    if isinstance(files,list):
        for f in files:
            clean_bom(f)
        ret = c.read(files)
    return c

config = load_config(CONF_FILE_PATH)
CONF_OK = 0
try:
    DATA_DIR = config.get("FileData","path")
    DATA_DIR = os.path.join(DATA_DIR,'upgrade')
    if not os.path.isdir(DATA_DIR):
        os.makedirs(DATA_DIR)
    CONF_OK = 1
except Exception,e:
    log.exception(e)
    #配置文件解析失败后，程序直接退出。
#end

XML_FILE_DIR = os.path.join(DATA_DIR, 'config')
ZIP_FILE_DIR = os.path.join(DATA_DIR, 'zippackage')
if not os.path.exists(XML_FILE_DIR):os.makedirs(XML_FILE_DIR)
if not os.path.exists(ZIP_FILE_DIR):os.makedirs(ZIP_FILE_DIR)

#一级xml配置文件名
ROOT_FILE = 'main_property.xml'
#远程库文件名后缀
REMOTE_SEP = "-remote"
#帮助信息
data_path_config_eg = """
========upgrade.cgf=========
[FileData]
path = E:\ATT\Python\Robot\ATMS\Trunk\data
=============end============
"""

#定义版本权限与版本对应关系
#版本权限向上兼容，如:ALPHA权限可以查询所有版本，BETA权限可以查询除ALPHA版本外的所有版本
ALPHA   = 0
BETA    = 10
GAMMA   = 20
STABLE  = 30
#大写的定义为权限值，小写的定义为版本名称
alpha   = "alpha"
beta    = "beta"
gamma   = "gamma"
stable  = "stable"

ACCESSES = {
    alpha    : ALPHA,
    beta     : BETA,
    gamma    : GAMMA,
    stable   : STABLE,
}

def reverse_dict(input_dict):
    k_v = input_dict.items()
    v_k = [(item[1],item[0]) for item in k_v]
    return dict(v_k)
def get_name_by_access(access):
    """通过权限值获取对应版本名称
    >>>get_name_by_access(DEFAULT_ACCESS)
    >>>"gamma"
    """
    return reverse_dict(ACCESSES).get(access,"unknown")
#设置默认权限为gamma版本
DEFAULT_ACCESS = GAMMA
#设置权限控制模块开关
ENABLE_ACCESS = True

