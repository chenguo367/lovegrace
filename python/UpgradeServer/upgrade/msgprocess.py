# -*- coding: utf-8 -*-

# /*************************************************************************
#  Copyright (C), 2013-2014, SHENZHEN GONGJIN ELECTRONICS. Co., Ltd.
#  module name: msgprocess
#  function: 处理服务器收到的各种消息
#            
#  Author: ATT development group
#  version: V1.1
#  date: 2013.06.19
#  change log:
#  lana     20130619    created
#  cheng    20130625    changed
# ***************************************************************************
import os
import time
import threading

import msgdef
import versionmanager as version_manager
from xmloperate import *
#以下用到的变量在 xmloperate 里面已经定义了
# config模块的全部变量包括但不限于：
# CONF_OK
# CONF_FILE_PATH
# DATA_DIR = config.get("FileData","path")
# CUR_FILE_DIR = os.path.split(os.path.dirname(__file__))[0]
# ZIP_FILE_DIR = os.path.join(CUR_FILE_DIR, 'zippackage')
# log = Logger().getLogger('upgradeserver')

MSG_PROCESS_SUC = 0
MSG_PROCESS_FAIL = -1


def create_transfer_serial():
    """
    根据当前系统时间生成唯一序列号
    """
    
    return time.strftime('%Y%m%d%H%M%S')

def construct_message_dict(msg_type, msg_event, msg_property={}, msg_data=""):
    """
    构造消息字典
    """
    dict_msg=dict()

    dict_msg[msgdef.KEY_MSG_TYPE] = msg_type
    dict_msg[msgdef.KEY_MSG_EVENT] = msg_event
    dict_msg[msgdef.KEY_MSG_PROPERTIES] = msg_property
    dict_msg[msgdef.KEY_MSG_DATA] = msg_data

    return dict_msg


class MsgProcess(object):
    """
    服务器消息处理类
    """
    #消息类型，与处理函数映射表
    hash_table = {}

    #命令数据最大长度
    head_lenth = 512
    #配置文件操作结果：0表示更新成功
    xml_operate_ret = 0
    def __init__(self, conn,queue):
        """
        新增权限管理，
         版本权限值            用户权限值
            30  ------stable
                            ------  25  stable

            20  ------gamma
                            ------  15  gamma

            10  ------beta
                            ------  5   beta

            0   ------alpha
                            ------  -5  alpha
        用户可以获取版本权限值比自己的用户权限值大的所有版本。
        """
        
        self.conn = conn
        self.q = queue
        try:
            recv_data = self.conn.content.read(self.head_lenth)
            data_end_index = recv_data.rfind('}')
            log.debug("数据长度 %s"%(data_end_index+1))
            # self.conn.write("hello world!")
            # self.conn.finish()
            if (not recv_data) or (data_end_index == -1):
                log.error("消息为空或消息格式不合法。")
                raise
            self.dict_msg = eval(recv_data[:data_end_index+1])
            #在这里打印消息来源方机器码,增加一个消息字段KEY_MSG_MACHINE_NUM在msgdef中
            source = self.dict_msg.get(msgdef.KEY_MSG_MACHINE_NUM,"火星")
            log.info("收到消息，来自:%s"%source)
            #这里单独把机器码采集在一个文件中
            _ = Logger()
            _.echolog = False
            machine_recorder = _.getLogger("machine_num")
            machine_recorder.info("发现连接：机器码-%s-,IP地址[%s]"%(source,self.conn.transport.client[0]))
            # 根据机器码获取版本请求权限
            self.vm = version_manager.VersionManager(source)
            #将用户相应权限下调5
            self.access = self.vm.access - 5
            self.source = source
            #消息解析完成，准备好了。
            self.ready = True
        except Exception,e:
            log.exception("读取数据失败:\n%s"%e)
            #todo 这里加上非法消息的错误回复，需要定义一个消息类型在msgdef中
            self.response_fail("Warning: illegal information",msg_type='')
            self.ready = False

    def is_available(self):
        """
        返回消息是否可以被解析
        @return: bool
        """
        return self.ready

    @staticmethod
    def map_action_handle():
        """
        消息处理映射初始化，新的消息类型将在这里注册新的处理函数
        供服务器启动时调用
        """
        MsgProcess.register_handle(msgdef.MSG_TYPE_UPLOAD_INIT,
                                   'handle_upload_init')
        MsgProcess.register_handle(msgdef.MSG_TYPE_UPLOAD_FILE,
                                   'handle_upload_file')
        MsgProcess.register_handle(msgdef.MSG_TYPE_DOWNLOAD_FILE,
                                   'handle_download_file')
        MsgProcess.register_handle(msgdef.MSG_TYPE_UPGRADE_INFO_QUERY,
                                   'handle_upgrade_info_query')
        #add more handle

    @staticmethod
    def register_handle(msg_type,handle):
        """
        注册某消息类型的处理函数，注册后服务器收到该消息，将使用注册的处理函数进行处理
        @param msy_type:消息类型
        @param handle: 处理函数
        @return:None
        """
        assert hasattr(MsgProcess,handle)
        MsgProcess.hash_table[msg_type] = getattr(MsgProcess,handle)

    def parse_msg(self):
        """
        解析消息体，先解析出消息类型，
        根据消息类型分发消息到不同的处理函数中
        """
        # 这里代码重构,不再使用if语句轮询事件类型 2013-7-30 by cheng
        # 根据消息类型分发消息
        msg_type = self.dict_msg.get(msgdef.KEY_MSG_TYPE)
        log.info( "当前消息类型为 %s" % msg_type)
        log.debug( "当前消息内容为 %s" % self.dict_msg.get(msgdef.KEY_MSG_PROPERTIES))

        handle = self.hash_table.get(msg_type,None)
        if handle:
            handle(self)
        else:
            err_info = "unsupported message type: %s !" % msg_type
            log.error(err_info)
            self.response_fail(err_info)
        
    
    def handle_upload_init(self):
        """
        处理upload_init消息，解析出消息事件，根据消息事件，
        分发消息到不同的处理函数中
        """
        
        # 解析消息事件
        msg_event = self.dict_msg.get(msgdef.KEY_MSG_EVENT)
        log.debug( "当前消息事件为 %s" % msg_event)
        
        if msg_event == msgdef.MSG_EVENT_RQST:
            self.handle_upload_init_request()
        else:
            err_info = "unsupported message event: %s !" % msg_event
            self.response_fail(err_info)
        
    
    def handle_upload_init_request(self):
        """
        处理upload init rqst事件，解析出KEY_MSG_PROPERTIES的值，
        生成唯一序列号，以序列号为key值，保存属性子字段的值，
        同时，以序列号为key值，保存上传的文件在本地的存储路径，
        然后将序列号，返回给客户端，以便客户端携带该序列号传输zip文件
        """
        
        # 解析消息属性
        msg_properties = self.dict_msg.get(msgdef.KEY_MSG_PROPERTIES)

        
        # 从属性字段中读取测试库名称和版本号
        testlib_name = msg_properties.get(msgdef.TESTLIB_NAME)
        testlib_version = msg_properties.get(msgdef.TESTLIB_VERSION)
        attrobot_version = msg_properties.get(msgdef.BASED_ATTROBOT_VERSION)
        #是否是远程库
        is_remote = msg_properties.get(msgdef.TESTLIB_REMOTE_FLAG)
        # 根据版本号,是否是远程库组建上传文件在本地存储的文件名
        if is_remote:
            file_name = "%s%s.zip" % (testlib_version,REMOTE_SEP)
        else:
            file_name = "%s.zip" % testlib_version
        
        # 根据测试库名，组建测试库文件的保存路径
        #changed by chenguo 7-5
        #存放文件路径修改为相对路径
        #目录结构改成#changed by chenguo 7-8
    #    package
	#       |
    #       库/包名
	# 	        |
	# 	        基础版本号1/基础版本号2
	# 		            |
    # 			        版本1/版本2
        # testlib_path = os.path.join(ZIP_FILE_DIR,attrobot_version ,testlib_name)
        testlib_path = os.path.join(testlib_name,attrobot_version)
        testlib_full_path = os.path.join(ZIP_FILE_DIR,testlib_path)
        # 如果当前测试库还没有目录，则创建一个新的目录
        if not os.path.exists(testlib_full_path):
            #层级创建目录
            os.makedirs(testlib_full_path)
            log.info("创建目录%s"%testlib_full_path)
            # if win_mkdir(testlib_path):
            #     log.info("创建目录%s"%testlib_path)
            # else:
            #     log.error("Failed:创建目录%s"%testlib_path)

        # 如果当前版本已经存在，则返回失败
        if file_name in os.listdir(testlib_full_path):
            err_info = "%s is existed in server!" % ' '.join([testlib_name,testlib_version])
            log.warn(err_info)
            self.response_fail(err_info)
            return
        
        # 如果当前版本不存在，生成序列号
        serial_num = create_transfer_serial()

        file_path = os.path.join(testlib_path, file_name)
        #文件属性，文件相对路径
        serial_info = {serial_num:
                           {'serial_properties':msg_properties,
                            'serial_zipfile':file_path
                           }
                    }
        self.q.lock()
        self.q.put(serial_info)
        self.q.unlock()
        
        # 组建消息发送response给客户端，告诉客户端可以上传文件了
        msg_type = self.dict_msg.get(msgdef.KEY_MSG_TYPE)
        dict_resp_msg = construct_message_dict(msg_type, msgdef.MSG_EVENT_SUC,
                                               msg_property = {msgdef.TRANSFER_SERIAL:serial_num})
        log.info("允许上传，生成序列号%s"%serial_num)
        self.send_response_msg(str(dict_resp_msg))
        
    
    def handle_upload_file(self):
        """
        处理upload file消息，解析出消息事件，根据消息事件，
        分发消息到不同的处理函数中
        """
        def construct_upload_zipfile_response_suc(serial_no):
            """
            构造上传成功响应消息体
            """
            property_dict=dict()
            property_dict[msgdef.TRANSFER_SERIAL] = serial_no
            msg_dict=construct_message_dict(msgdef.MSG_TYPE_UPLOAD_FILE,
                                            msgdef.MSG_EVENT_SUC,
                                            property_dict,
                                            None)
            msg_str=str(msg_dict)
            return msg_str
        # 解析消息事件
        msg_event = self.dict_msg.get(msgdef.KEY_MSG_EVENT)
        log.debug( "当前消息事件为 %s" % msg_event)
        
        if msg_event == msgdef.MSG_EVENT_RQST:
            serial_no = self.handle_upload_file_request()
            if serial_no:
                self.send_response_msg(construct_upload_zipfile_response_suc(serial_no))
            else:
                self.response_fail("upload file failed")
        else:
            err_info = "unsupported message event: %s !" % msg_event
            self.response_fail(err_info)
        
    
    def handle_upload_file_request(self):
        """
        处理upload file rqst事件
        returne 返回str类型 serial_no 失败则返回''
        """
        #获取序列号
        serial_no = self.dict_msg.get(msgdef.KEY_MSG_PROPERTIES).get(msgdef.TRANSFER_SERIAL,'')
        md5_str = self.dict_msg.get(msgdef.KEY_MSG_PROPERTIES).get(msgdef.ZIP_FILE_MD5,'')
        #在队列中获取序列号存放的对应信息
        tmplist = []
        found = False
        self.q.lock()
        while not (self.q.empty() or found):
            serial_info = self.q.get()
            if serial_no in serial_info.keys():
                file_info = serial_info[serial_no].get('serial_properties','')
                file_path = serial_info[serial_no].get('serial_zipfile','')
                found = True
            else:
                tmplist.append(serial_info)
        for i in tmplist:
            self.q.put(i)
        self.q.unlock()
        del tmplist
        if not found:
            log.error("上传失败，没有找到对应的文件信息或路径。序列号：%s"%serial_no)
            return ''

        #upload
        finish = False
        #将相对路径换成绝对路径
        file_path = os.path.join(ZIP_FILE_DIR,file_path)
        with open(file_path,"wb") as f:
            data = ''
            while not finish:
                data_buff = self.conn.content.read(1024*1024)
                if data_buff:
                    data +=data_buff
                    continue
                finish = True

            #校验文件md5
            if get_file_md5(data).lower() != md5_str.lower():
                err_info = "文件%sMD5校验不通过"%os.path.basename(file_path)
                log.error(err_info)
                f.close()
                return ''
            f.write(data)
            del data
            f.close()

        #上传完后更新xml文件
        testlib_name = file_info.pop(msgdef.TESTLIB_NAME)
        file_info[msgdef.ZIP_FILE_MD5] = md5_str
        file_info[msgdef.ZIP_FILE_PATH] = os.path.normpath(file_path)
        log.info("文件上传至路径%s完成，开始更新xml文件"%file_path)
        #启动线程更新配置文件，当配置失败后，线程退出并释放xml文件句柄，以便后面xml修复使用。
        uc = threading.Thread(target=self.operate_xml,args=(update_config,testlib_name,file_info))
        uc.start()
        uc.join()
        if self.xml_operate_ret>0:
            XmlRepairer().reBuild()
            log.debug("系统发现xml文件损坏，现已经修复。")
            # update_config(testlib_name,file_info)
        return serial_no

    def operate_xml(self,func,*args):
        """
        操作配置文件中间函数，供thread调用
        @param func: 操作函数
        @param args: 参数
        @return:
        """
        assert callable(func)
        #用来保存执行结果
        self.result =None
        try:
            self.result = func(*args)
            self.xml_operate_ret = 0
            log.info("更新/读取xml文件成功")
        except Exception,e:
            log.info("xml更新/读取失败:%s"%e)
            self.xml_operate_ret += 1

    def handle_download_file(self):
        """
        处理download file消息，解析出消息事件，根据消息事件，
        分发消息到不同的处理函数中
        """
        
        # 解析消息事件
        msg_event = self.dict_msg.get(msgdef.KEY_MSG_EVENT)
        log.debug( "当前消息事件为 %s" % msg_event)
        
        if msg_event == msgdef.MSG_EVENT_RQST:
            self.handle_download_file_request()
        else:
            err_info = "unsupported message event: %s !" % msg_event
            self.response_fail(err_info)
        
    
    def handle_download_file_request(self):
        """
        处理download file rqst事件
        """
        def construct_download_zipfile_response(property_dict):
            """
            构造下载响应消息体
            """
            msg_dict=construct_message_dict(msgdef.MSG_TYPE_DOWNLOAD_FILE,
                                            msgdef.MSG_EVENT_SUC,
                                            property_dict,
                                            None)
            msg_str=str(msg_dict)
            return msg_str

        msg_properties = self.dict_msg.get(msgdef.KEY_MSG_PROPERTIES)

        # 从请求属性字段中读取测试库名称和版本号
        testlib_name = msg_properties.get(msgdef.TESTLIB_NAME)
        testlib_version = msg_properties.get(msgdef.TESTLIB_VERSION)
        #文件版本所需的权限
        file_access = version_manager.get_version_access(testlib_version)
        if file_access < self.access:
            err_info = "Permission denied:机器码%s没有权限下载版本为%s的文件"%\
                       (self.source,get_name_by_access(file_access))
            log.error(err_info)
            self.response_fail("permission denied")
            return None
        #获取测试库文件路径
        xmlfile_path = getLibXmlPath(testlib_name)
        if not os.path.isfile(xmlfile_path):
            err_info = "请求的测试库%s不存在"%testlib_name
            log.warn(err_info)
            self.response_fail("can't find the file")
            return None

        # 读取该库所有版本属性
        t = threading.Thread(target=self.operate_xml,args=(get_nodes_info,xmlfile_path))
        t.start()
        t.join()
        if self.xml_operate_ret == 0:
            testlib_info = self.result
        else:
            XmlRepairer().reBuild()
            testlib_info = get_nodes_info(xmlfile_path)
            log.debug("系统发现xml文件损坏，现已经修复。")
        file_path = ''

        #筛选版本
        for t in testlib_info:
            version_name =  t.get(msgdef.TESTLIB_VERSION,'')
            if version_name == testlib_version:
                file_path = t.get(msgdef.ZIP_FILE_PATH,'')
                #add by chenguo 7-5
                #相对路径转换为绝对路径
                file_path = os.path.join(DATA_DIR,file_path)
                #取出md5，平台版本信息用来返回
                msg_properties[msgdef.BASED_ATTROBOT_VERSION] = t.get(msgdef.BASED_ATTROBOT_VERSION)
                msg_properties[msgdef.ZIP_FILE_MD5] = t.get(msgdef.ZIP_FILE_MD5)
                break

        log.info("收到下载请求:%s"%file_path)
        if not file_path:
            err_info = "找不到库%s的文件%s"%(testlib_name,testlib_version)
            log.warn(err_info)
            self.response_fail("can't find the file")
            return None

        # self.conn.setHeader('Content-type','application/octet-stream')
        # self.conn.setHeader('Content-Disposition',
        #                         'inline;filename=%s' % file_name)

        #构造返回信息:
        msg_data = construct_download_zipfile_response(msg_properties).ljust(512,'\0')
        with open(file_path,'rb') as f:
            self.conn.write(msg_data)
            data = f.read(1024*50)
            file_len = len(data)
            while data:
                self.conn.write(data)
                data = f.read(1024*50)
                file_len += len(data)
            self.conn.finish()
            f.close()

        log.info("发送文件%s完成,文件大小:%s"%(file_path,file_len))
    
    def handle_upgrade_info_query(self):
        """
        处理upgrade info query消息，解析出消息事件，根据消息事件，
        分发消息到不同的处理函数中
        """
        
        # 解析消息事件
        msg_event = self.dict_msg.get(msgdef.KEY_MSG_EVENT)
        log.debug( "当前消息事件为 %s" % msg_event)
        
        if msg_event == msgdef.MSG_EVENT_RQST:
            self.handle_upgrade_info_query_request()
        else:
            err_info = "unsupported message event: %s !" % msg_event
            self.response_fail(err_info)
        
    
    def handle_upgrade_info_query_request(self):
        """
        处理upgrade info query rqst事件
        """
        self.query_xml_ret = 0
        root_xml_path = getLibXmlPath()
        #要查询的属性名称
        keys = (msgdef.TESTLIB_VERSION,
                msgdef.BASED_ATTROBOT_VERSION,
                msgdef.TESTLIB_REMOTE_FLAG,
            )

        # 查询全部配置文件信息
        t = threading.Thread(target=self.operate_xml,args=(get_all_libinfos,root_xml_path,keys))
        t.start()
        t.join()

        if self.xml_operate_ret == 0:
            result = self.result
        else:
            XmlRepairer().reBuild()
            result = get_all_libinfos(root_xml_path,keys)
            log.debug("系统发现xml文件损坏，现已经修复。")
        #add by cheng 2103-07-26
        # check version permission
        def version_filter(lib_info):
            """版本过滤规则"""
            version = lib_info.get(msgdef.TESTLIB_VERSION, "")
            if version:
                file_permission = version_manager.get_version_access(version)
                if file_permission>self.access:
                    return True
            else:
                version = "未知"
            log.debug("没有权限查询版本： %s"%(version))
            return False

        if version_manager.ENABLE_ACCESS:
            for lib,infos in result.items():
                log.debug("过滤测试库%s"%lib)
                result[lib] = filter(version_filter,infos)
        #end
        msg_type = self.dict_msg.get(msgdef.KEY_MSG_TYPE)
        msg_event = msgdef.MSG_EVENT_SUC
        dict_resp_msg = construct_message_dict(msg_type, msg_event, msg_property=result, msg_data="")
        log.info("升级查询完成")
        self.send_response_msg(str(dict_resp_msg))


    def response_fail(self, err_info,msg_type = ''):
        """
        向客户端回应失败，err_info指明失败原因
        """
        if not msg_type:
            msg_type = self.dict_msg.get(msgdef.KEY_MSG_TYPE)
        msg_event = msgdef.MSG_EVENT_FAIL
        msg_pro = {msgdef.ERROR_INFO:err_info}
        
        dict_resp_msg = construct_message_dict(msg_type, msg_event, msg_property=msg_pro)
        
        self.send_response_msg(str(dict_resp_msg))
        

    def send_response_msg(self, resp_msg):
        """
        发送响应消息给客户端
        """
        
        ret = MSG_PROCESS_SUC
        err_info = "发送回应消息!"
        try:
            self.conn.write(resp_msg)
            self.conn.finish()
            log.info(err_info)
        except Exception,e:
            ret =  MSG_PROCESS_FAIL
            log.exception("发送回应消息发生异常:%s\n"%e)

        return ret
        
