# -*- coding: utf-8 -*-

# /*************************************************************************
#  Copyright (C), 2013-2014, SHENZHEN GONGJIN ELECTRONICS. Co., Ltd.
#  module name: msgdef
#  function: 定义升级服务器与客户端交互的消息结构和消息类型
#            
#  Author: ATT development group
#  version: V1.1
#  date: 2013.06.19
#  change log:
#  lana     20130619    created
#  cheng    20130702    changed
# ***************************************************************************


# 定义消息类型
MSG_TYPE_UPLOAD_INIT = "MSG_TYPE_UPLOAD_INIT"
MSG_TYPE_UPLOAD_FILE = "MSG_TYPE_UPLOAD_FILE"
MSG_TYPE_DOWNLOAD_FILE = "MSG_TYPE_DOWNLOAD_FILE"
MSG_TYPE_UPGRADE_INFO_QUERY = "MSG_TYPE_UPGRADE_INFO_QUERY"


# 定义事件类型
# 请求
MSG_EVENT_RQST = "MSG_EVENT_RQST"
# 成功回应
MSG_EVENT_SUC  = "MSG_EVENT_SUC"
# 失败回应
MSG_EVENT_FAIL = "MSG_EVENT_FAIL"


# 消息结构字段
KEY_MSG_TYPE = "KEY_MSG_TYPE"
KEY_MSG_EVENT = "KEY_MSG_EVENT"
KEY_MSG_PROPERTIES = "KEY_MSG_PROPERTIES"
KEY_MSG_DATA = "KEY_MSG_DATA"
#新增机器码字段，判断消息来源2013-7-18
KEY_MSG_MACHINE_NUM = "KEY_MSG_MACHINE_NUM"


# 消息属性字段子项，根据消息类型选择需要的字段组建成字典
TESTLIB_NAME = "TESTLIB_NAME"
TESTLIB_VERSION = "TESTLIB_VERSION"
BASED_ATTROBOT_VERSION = "BASED_ATTROBOT_VERSION"
DATA_LEN = "DATA_LEN"
ZIP_FILE_MD5 = "ZIP_FILE_MD5"
TRANSFER_SERIAL = "TRANSFER_SERIAL"
ERROR_INFO = "ERROR_INFO"
#add by chenguo
ZIP_FILE_PATH = "ZIP_FILE_PATH"
UPLOAD_TIME = "UPLOAD_TIME"
TESTLIB_REMOTE_FLAG="TESTLIB_REMOTE_FLAG"



# 消息结构
"""
msg_dict = {
    KEY_MSG_TYPE:""
    KEY_MSG_EVENT:""
    KEY_MSG_STRUCT: {}
    KEY_MSG_DATA:""    
}

# upload init rqst
msg_properties_dict = {
    TESTLIB_NAME = ""
    TESTLIB_VERSION = ""
    BASED_ATTROBOT_VERSION = ""
    DATA_LEN = ""
    ZIP_FILE_MD5 = ""
}

# upload init suc
msg_properties_dic = {
    TRANSFER_SERIAL = ""
}

"""
