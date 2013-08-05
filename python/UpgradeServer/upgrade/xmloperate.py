# -*- coding: utf-8 -*-

# /*************************************************************************
#  Copyright (C), 2013-2014, SHENZHEN GONGJIN ELECTRONICS. Co., Ltd.
#  module name: xmloperate
#  function: 处理xml文件的创建和xml节点的创建，以及xml文件的解析
#
#  Author: ATT development group
#  version: V1.1
#  date: 2013.06.20
#  change log:
#  lana     20130619    created
#  cheng    20130625    changed
# ***************************************************************************

import time
import hashlib
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement

#将各全局变量初始化单独到config模块里
from config import *
from msgdef import *
from utils import json,unjson


def create_empty_xml_file(file_path, root):
    """
    生成一个空的xml文件,只包含root一个根元素
    """

    # 添加根元素对象
    root_obj = Element(root)

    # 创建树对象
    tree = ElementTree(root_obj)

    # 写xml文件
    tree.write(file_path, encoding='utf-8', xml_declaration=True)


def create_single_element(name, value="", attr={}):
    """
    创建一个单独的元素，返回元素对象
    """

    element = Element(name, attrib=attr)
    if value:
        element.text = value

    return element


def add_xml_element(file_path, element, parent=None):
    """
    添加xml element到父节点下
    """
    if parent is not None:
        assert isinstance(parent,Element)
    else:
        parent = ET.parse(file_path).getroot()
    parent.append(element)
    tree = ElementTree(parent)
    tree.write(file_path, encoding='utf-8', xml_declaration=True)


# def parse_xml_file(file_path):
#     """
#     解析xml文件,返回所有子元素的[name,value,attr]列表
#     """
#
#     root = ET.parse(file_path).getroot()
#
#     return get_children_value(root)
#
#
# def get_children_value(element_object):
#     """
#     返回所有子元素的[name,value,attr]列表
#     """
#
#     tmp_list = []
#
#     children_element_list = element_object.getchildren()
#     if len(children_element_list) == 0:
#         log.debug("element_object have no children")
#         return None
#     for element in children_element_list:
#         sub_children_list = element.getchildren()
#         if len(sub_children_list) == 0:
#             tmp_list.append([element.tag, element.text, element.attrib])
#         else:
#             tmp_list.append([element.tag, get_children_value(element)])
#
#     return tmp_list

######################################
#一级文件(main_property.xml)操作接口
######################################
def insert_lib_node(xml_path, name, path=''):
    """
    main.xml插入一条测试库新记录
    @param xml_path:   xml文件路径
    @param name:        节点name属性值
    @param path:        节点path属性值
    @return:            None
    """
    if not path: path = _getPathByName(name)
    root = ET.parse(xml_path).getroot()
    libinfo = {
        "name": name,
        #这里存放的path没有实际用到
        "path": path
    }
    element1 = create_single_element("testlib", attr=libinfo)
    add_xml_element(xml_path, element1, root)
    log.debug("%s插入测试库信息%s" % (os.path.basename(xml_path), libinfo))


def find_element(file_path, name, parent=None):
    """
    在main.xml的root节点下查找"name"属性为name的节点
    @param file_path:   xml文件路径
    @param name:        查找的子节点name属性的值
    @param parent:      在该父节点下进行查找，默认root节点
    @return:            查找到则返回True，否则反悔False
    """
    if parent is not None:
        assert isinstance(parent,Element)
    else:
        parent = ET.parse(file_path).getroot()
    children = list(parent)
    for child in children:
        if name == child.attrib.get("name", ""):
            return True
    return False


def get_all_libinfos(file_path,args):
    """
    获取所有测试库信息
    @param file_path:   main.xml文件路径
    @param args:字典键
    @return:
    """
    root = ET.parse(file_path).getroot()
    #取出所有测试库名字
    libs = root.getchildren()
    libname_list = []
    for lib in libs:
        lib_name = lib.attrib.get("name", "")
        if lib_name:
            libname_list.append(lib_name)
    result = dict().fromkeys(libname_list, [])
    for lib_name in libname_list:
        #处理2级文件
        lib_info = get_nodes_info(getLibXmlPath(lib_name),args)
        result[lib_name] = lib_info
    return result

######################
#二级xml文件操作接口
######################
def insert_sub_node(file_path, kw):
    """
    在对应测试库xml文件中插入一条节点信息，如果没有该xml文件，则创建
    @param file_path:   测试库.xml文件路径
    @param kw:      节点信息
    @return:
    """
    #changed by chenguo7-8
    #该函数功能被ZipFile.update_xml方法替代
    pass
    # libfile_path =  kw.get(ZIP_FILE_PATH,'')
    # ZipFile(libfile_path).update_xml()
    #log.info("这里新建节点")
    # if not os.path.exists(file_path):
    #     open(file_path, 'wb').close()
    #     create_empty_xml_file(file_path, "root")
    # node = create_single_element("node")
    # for k, v in kw.items():
    #     sub_node = SubElement(node, k)
    #     # 对非字符串值处理
    #     sub_node.text = json(v)
    # #增加时间标签(也要jason序列化)
    # SubElement(node, UPLOAD_TIME).text = json(time.strftime('%Y-%m-%d %H:%M:%S'))
    # add_xml_element(file_path, node)

def get_nodes_info(file_path,args=()):
    """
    获取2级xml文件所有节点的属性。
    @param file_path:
    @param args:需要返回的字典关键字tuple
    @return:[{'md5': 'FBD7894B3CB89DD90E98F5FEADF805F6',
                'time': '2013-06-25 14:38:37',
                'version': 'V1.0.1'},...,{}
            ]
    """
    root = ET.parse(file_path).getroot()
    nodes = root.findall('node')
    nodes_info_dict = []
    for node in nodes:
        #获取每个节点的标签和值
        if args:
            # condition = lambda n,: n.tag
            # filter()
            property_list = [(c.tag, unjson(c.text)) for c in node.getchildren() if c.tag in args]
        else:
            property_list = [(c.tag, unjson(c.text)) for c in node.getchildren()]
        #反序列化
        node_info = dict(property_list)
        version = node_info.get(TESTLIB_VERSION, '')
        if not version:
            continue
        nodes_info_dict.append(node_info)
    return nodes_info_dict

#################################
#私有方法(测试库二级xml配置文件命名规则)
#################################
def _getPathByName(libname):
    """
    @param libname: 测试库名
    @return:        测试库xml文件名
    """
    return '.'.join([libname, 'xml']).lower()

#########
#公共方法
#########
def getLibXmlPath(libname=''):
    """
    获取测试库二级xml配置文件的全路径,无参数则返回一级xml文件(main_property.xml)
    @param libname: 测试库名
    @return:        测试库二级xml配置文件全路径
    """
    if not libname :
        return  os.path.join(XML_FILE_DIR, ROOT_FILE)
    return os.path.join(XML_FILE_DIR,_getPathByName(libname))

def update_config(name,node_info):

    root_xml_path = getLibXmlPath()
    if not os.path.exists(root_xml_path):
        XmlRepairer().reBuild()
        return None
    #changed by chenguo 7-4
    #这个函数功能用ZipFile.update_xml()方法实现

    #判断main.xml是否存在记录
    # if not find_element(root_xml_path, name):
    #     不存在该测试库节点，允许上传,并更新1级xml文件
    #     insert_lib_node(root_xml_path, name, path='')
    #找到二级xml文件路径
    # libfile_path = getLibXmlPath(name)
    #在二级xml文件里插入节点
    # insert_sub_node(libfile_path, node_info)
    zip_file_path =  node_info.get(ZIP_FILE_PATH,'')
    assert zip_file_path
    ZipFile(zip_file_path).update_xml()

def get_file_md5(data):
    """
    获取md5
    @param data: str object
    @return: MD5值字符串
    """
    md5o = hashlib.md5()
    md5o.update(data)
    return  md5o.hexdigest()

class ZipFile(object):
    """
    zip压缩文件对象
    """
    lib_name = ""
    lib_version = ""
    att_version = ""
    upload_time = ""
    md5 = ""
    is_remote = False
    def __init__(self,abspath):
        assert os.path.isfile(abspath)
        self.abspath = abspath
        dir_index = abspath.find('zippackage')
        if dir_index > 0:
            self.path = abspath[dir_index:]
        else:
            log.error("文件存放路径[%s]出错，无法解析"%abspath)
            self.path = abspath
        self.init_info()
        self.info = {
            BASED_ATTROBOT_VERSION : self.att_version,
            ZIP_FILE_PATH :self.path,
            ZIP_FILE_MD5 : self.md5,
            TESTLIB_VERSION :self.lib_version,
            UPLOAD_TIME : self.upload_time,
            TESTLIB_REMOTE_FLAG : self.is_remote,
        }

    def init_info(self):
        curdir,filename = os.path.split(self.abspath)
        #目录结构被修改成先库名，再平台版本
        _ ,self.att_version = os.path.split(curdir)
        _ ,self.lib_name = os.path.split(_)
        with open(self.abspath,"rb") as f:
            self.md5 = get_file_md5(f.read())
        f.close()
        self.upload_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(os.path.getmtime(self.abspath)))
        file_split = filename.split(REMOTE_SEP)
        if len(file_split) == 2:
            self.is_remote = True
            self.lib_version = file_split[0]
        else:
            self.lib_version = os.path.splitext(filename)[0]


    def update_xml(self):
        """
        将文件信息更新至xml配置文件
        """
        root_config = getLibXmlPath()
        #先检查一级xml配置文件是否有该文件对应库的信息
        if not find_element(root_config, self.lib_name):
            insert_lib_node(root_config, self.lib_name)
        #在二级xml配置文件中插入信息
        lib_config = getLibXmlPath(self.lib_name)
        if not os.path.exists(lib_config):
            open(lib_config, 'wb').close()
            create_empty_xml_file(lib_config, "root")
            log.debug("更新库%s的xml配置文件"%self.lib_name)
        node = create_single_element("node")
        for k, v in self.info.items():
            sub_node = SubElement(node, k)
            sub_node.text = json(v)
        add_xml_element(lib_config, node)


class XmlRepairer(object):
    """
    xml文件维护类
    """
    #待修复文件列表
    def __init__(self,root_file_path = ZIP_FILE_DIR):
        self.filelist = []
        if not os.path.exists(root_file_path):
            os.mkdir(root_file_path)
        self.root_file_path = root_file_path
        self.root_xml_path = getLibXmlPath()

    def __del__(self):
        del self

    def listAll(self,path=''):
        """
        返回目录下所有zip文件对象
        @param path:
        @return:
        """
        if not path:
            path = self.root_file_path
        for filedir,_,filenames in os.walk(path):
            if not len(filenames):
                continue
            for filename in filenames:
                if os.path.splitext(filename)[1] != ".zip":
                    continue
                self.filelist.append(ZipFile(os.sep.join([filedir,filename])))

    def reBuild(self):
        """
        开始维护
        @return:
        """
        #重置所有xml配置文件
        from shutil import rmtree
        def onerror(*args):
            log.exception("对'%s'执行%s时出错:\n"%(args[1],args[0].__name__))
        rmtree(XML_FILE_DIR,False,onerror)
        log.debug("重建xml配置文件目录")
        os.mkdir(XML_FILE_DIR)
        #重建一级xml配置文件
        open(self.root_xml_path, 'wb').close()
        create_empty_xml_file(self.root_xml_path, "root")
        log.debug("创建一级xml文件%s"%os.path.basename(self.root_xml_path))
        self.listAll(self.root_file_path)
        for f in self.filelist:
            f.update_xml()
        #重建完重置待修复文件列表
        self.filelist = []
if __name__ == '__main__':
    # name = 'test'
    # node_info = {'version': 'V1.0.1', 'md5': 'FBD7894B3CB89DD90E98F5FEADF805F6'}
    # update_config(name,node_info)
    log.setLevel(10)
    xr = XmlRepairer()
    xr.reBuild()