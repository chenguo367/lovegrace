# -*- coding: utf-8 -*-
# /*************************************************************************
#  Copyright (C), 2012-2013, SHENZHEN GONGJIN ELECTRONICS. Co., Ltd.
#  module name: pack
#  function: 测试库打包模块
#  Author: ATT development group
#  version: V1.0
#  date: 2013.5.21
#  change log:
#  lana       20130625    添加打包配置信息配置和svn check
#  
# ***************************************************************************

import os
import sys
import re 
import zipfile 
import shutil
import time
import datetime
import compileall
import cStringIO 
import imp

CUR_FILE_DIR = os.path.split(os.path.dirname(__file__))[0]
TWISTED_DIR = os.path.join(CUR_FILE_DIR, "vendor")
sys.path.insert(0, CUR_FILE_DIR)
sys.path.insert(0, TWISTED_DIR)
PROJECT_HOME = ""   
TESTLIB_NAME =  os.path.split(os.path.dirname(os.path.dirname(__file__)))[1]
    

class ATT_Error(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value


def walk_dir(dir,topdown=True):
    """
    遍历整个dir目录，返回dir下所有文件的全路径列表
    如果topdown为True,表示从上到下进行遍历，先返回父目录文件路径，再返回子目录文件路径
    如果topdown为False， 表示从下到上进行遍历，先返回子目录文件路径，再返回父目录文件路径
    """
    
    file_list = []
    for root, dirs, files in os.walk(dir, topdown):
        for name in files:
            file_list.append(os.path.join(root,name))
        
    return file_list


def zip_folder(folder_name, file_name, include_empty_dir=True):
    """
    将folder_name中的文件压缩成zip文件file_name
    """
    
    zip = zipfile.ZipFile(file_name, 'w', zipfile.ZIP_DEFLATED)   
    for root, dirs, files in os.walk(folder_name):  
        empty_dirs = []
        empty_dirs.extend([dir for dir in dirs if os.listdir(os.path.join(root, dir)) == []])   
        for name in files:  
            file_abs_path = os.path.join(os.path.join(root, name))
            file_rel_path = os.path.relpath(file_abs_path, folder_name)
            zip.write(file_abs_path, file_rel_path, zipfile.ZIP_DEFLATED)   
        if include_empty_dir:   
            for dir in empty_dirs:  
                empty_dir_abs_path = os.path.join(os.path.join(root, dir))
                empty_dir_rel_path = os.path.relpath(empty_dir_abs_path, folder_name)
                zif = zipfile.ZipInfo(empty_dir_rel_path + "/") 
                zip.writestr(zif, "")   
        empty_dirs = []   
    zip.close()  


def get_property_file_path(work_dir):
    """
    返回当前测试库的配置文件的路径
    """
    
    file_list = os.listdir(work_dir)
    for tmp_file in file_list:
        if tmp_file.find("Property.py") != -1:
            return os.path.join(work_dir, tmp_file)
    
    return None

    
class ClearTempFiles(object):
    """
    清零临时文件类
    """

    def clear_dir_tmp_files(self,work_dir):
        """
        删除临时文件
        """
        
        try:
            # 获取当前工作目录下的所有临时文件
            file_list = self.get_temp_files(walk_dir(work_dir))
            for file in file_list:
                # 删除文件
                os.remove(file)
                
        except Exception, e:
            err_info = u"删除临时文件出错，错误信息为: %s" % e.message
            raise ATT_Error, err_info
    
    
    def get_temp_files(self, all_file_list):
        """
        从文件列表all_file_list中过滤临时文件，然后返回临时文件列表
        """
        
        file_list = []
        for file in all_file_list:
            file_type = os.path.splitext(file)[1]
            
            #列举临时文件后缀
            if (file_type.lower() == ".pyc" or
                file_type.lower() == ".pyo" or
                file_type.lower() == ".bak"):
                
                file_list.append(file)
            else:
                pass
            
        return file_list
    
    
    def clear_dir_temp_dir(self, work_dir, remove_text):
        """
        清除work_dir中目录名包含remove_text的目录
        """
        
        try:
            list_dirs = os.walk(work_dir)
            for root, dirs, files in list_dirs:
                for d in dirs:
                    if d.find(remove_text) != -1:
                        _temp = os.path.join(root, d)
                        shutil.rmtree(_temp)
                        
        except Exception,e:
            err_info = u"删除含有 %s 的目录出错，错误信息为: %s" % (remove_text, e.message)
            raise ATT_Error, err_info
    
    
class CompileFiles(object):
    """
    打包文件类
    """
    
    def __init__(self, main_dir, debug=False, version_type="a", need_compile=True, need_upload=True):
        """
        initial variable
        """
        
        self.main_dir = main_dir
        self.debug = debug      # 如果debug为True，则不需要检查svn版本
        self.version_type = version_type
        self.need_compile = need_compile
        self.need_upload = need_upload        # 是否需要上传到升级服务器中
        
        self.version = ""
        self.temp_dir_name = "__att_temp_"
        self._zip_dir_name = "_INSTALL_"
        self.property_file_path = get_property_file_path(os.path.join(main_dir,'upgrade'))
    
    
    def init_compiler_dir(self, work_dir, compiler_dir):
        """
        初始化compiler目录，将需要编译的文件拷贝到compiler目录下
        """
        
        # 目标文件夹不存在，则新建
        if not os.path.exists(compiler_dir):
            os.mkdir(compiler_dir)
        
        # 获取work_dir下的所有文件    
        names = os.listdir(work_dir)
        
        # 遍历源文件夹中的文件与文件夹
        for name in names:
            work_dir_name = os.path.join(work_dir, name)
            compiler_dir_name = os.path.join(compiler_dir, name)
            try:
                # 是文件夹则递归调用本拷贝函数，否则直接拷贝文件
                if os.path.isdir(work_dir_name):   
                    # 如果是IDE或版本管理生成的目录，则忽略
                    if (name.lower() == ".komodotools" or
                        name.lower() == ".svn" or
                        name.lower() == ".git" or
                    #data 和 log 目录不打包
                        name.lower() == "data" or
                        name.lower() == "log" ):
                        pass
                    
                    # 忽略不需要编译的目录
                    elif (name == "pack" or
                         name == "_INSTALL_"):
                        pass
                    
                    # 忽略当前编译临时目录
                    elif work_dir_name == compiler_dir:
                        pass
                    
                    # 忽略未删除的之前的编译临时目录
                    elif name.find(self.temp_dir_name) != -1:
                        pass
                    
                    else:
                        self.init_compiler_dir(work_dir_name, compiler_dir_name)
                        
                else:
                    # 如果是IDE或版本管理生成的文件，或者是pyc和pyo文件，则忽略
                    if (os.path.splitext(name)[1].lower() == ".komodoproject" or
                        os.path.splitext(name)[1].lower() == ".buildpath" or
                        os.path.splitext(name)[1].lower() == ".project" or
                        os.path.splitext(name)[1].lower() == ".gitignore" or
                        os.path.splitext(name)[1].lower() == ".pyc" or
                        os.path.splitext(name)[1].lower() == ".pyo" or
                        os.path.splitext(name)[1] == ".IAB" or
                        os.path.splitext(name)[1] == ".IAD" or
                        os.path.splitext(name)[1] == ".IMB" or
                        os.path.splitext(name)[1] == ".IMD" or
                        os.path.splitext(name)[1] == ".PFI" or
                        os.path.splitext(name)[1] == ".PO" or
                        os.path.splitext(name)[1] == ".PR" or
                        os.path.splitext(name)[1] == ".PRI" or
                        os.path.splitext(name)[1] == ".PS" or
                        os.path.splitext(name)[1] == ".SearchResults" or
                        os.path.splitext(name)[1] == ".WK3" or
                        (work_dir_name == __file__ and self.need_compile == 1)):
                        pass
                    
                    elif (os.path.splitext(work_dir_name)[1].lower() == ".zip" and
                          os.path.split(work_dir_name)[1].find(TESTLIB_NAME) != -1 and
                          os.path.split(work_dir_name)[0] == os.path.join(self.main_dir)):
                        pass
                    
                    else:
                        shutil.copy2(work_dir_name, compiler_dir)
            except Exception, e:
                shutil.rmtree(compiler_dir)
                raise ATT_Error, e.message
    
    
    def check_svn_version(self):
        """
        检查当前工作目录中的文件版本是否与SVN库中的一致
        """
        try:
            import pysvn
        except ImportError,e:
            raise e
        client = pysvn.Client()
        changes = client.status(PROJECT_HOME)
        files_to_be_added = [f.path for f in changes if f.text_status == pysvn.wc_status_kind.added]
        files_to_be_removed = [f.path for f in changes if f.text_status == pysvn.wc_status_kind.deleted]
        files_that_have_changed = [f.path for f in changes if f.text_status == pysvn.wc_status_kind.modified]
        files_with_merge_conflicts = [f.path for f in changes if f.text_status == pysvn.wc_status_kind.conflicted]
        unversioned_files = [f.path for f in changes if f.text_status == pysvn.wc_status_kind.unversioned]
        
        if (files_to_be_added ==[] and
            files_to_be_removed == [] and
            files_with_merge_conflicts == []):
            pass
        else:
            err_info = u"当前目录存在修改，请将修改上传SVN后再进行打包操作，谢谢。"
            raise ATT_Error, err_info
        
        if files_that_have_changed == []:
            pass
        else:
            for file in files_that_have_changed:
                # 忽略pack.py的修改
                if file == os.path.join(self.main_dir, "pack", "pack.py"):
                    pass
                else:
                    err_info = u"当前目录存在修改，请将修改上传SVN后再进行打包操作，谢谢。"
                    raise ATT_Error, err_info
                    
            
        if unversioned_files == []:
            pass
        
        else:
            
            err_info = u"当前目录存在修改，请将修改上传SVN后再进行打包操作，谢谢。"
            raise ATT_Error, err_info
                    
        
        # 验证本地的版本和远端服务器上面版本一致，则开始获取版本号。
        print u'本地版本和服务器上版本一致，开始获取当前版本的版本信息。'
        entry = client.info(PROJECT_HOME)
        
        print u'SVN路径:',entry.url
        print u'最新版本:',entry.commit_revision.number
        print u'提交人员:',entry.commit_author
        print u'更新日期:', datetime.datetime.fromtimestamp(entry.commit_time)
            
        self.svn_commit_revision = entry.commit_revision.number
        self.svn_url = entry.url
        self.svn_commit_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(entry.commit_time))
        self.pack_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))   
        print u'本地版本和服务器上版本一致，获取当前版本的版本信息成功。'
    
    
    def get_version_info(self, path):
        """
        根据path导入TestCenterProperty模块，然后从模块中获取版本信息并返回
        """
        
        # 获取模块名
        dirpath, filename = os.path.split(path)
        modulename = os.path.splitext(filename)[0]
        
        # 查找模块是否存在
        try:
            file, imppath, description = imp.find_module(modulename, [dirpath])
        except ImportError, err:
            err_info = "Find test lib module '%s' failed:\n%s" % (path, err)
            print err_info
            raise ATT_Error, err_info
        
        # 导入模块
        try:
            module = imp.load_module(modulename, file, imppath, description)
            print u"当前版本：%s"% module.Version
            version_note = module.log
            if isinstance(version_note,str):
                version_note = version_note.decode('utf-8')
            print u"版本历史：%s"% version_note
        except Exception, err:
            err_info = "Importing  test lib  module '%s' failed:\n%s" % (path, err)
            print err_info
            raise ATT_Error, err_info
        finally:
            if file:
                file.close()
        testlib_ver_major=None
        testlib_ver_minor_number=None
        testlib_ver_revision_number=None
        import inspect
        LOAD_KEY_MAJOR_VERSION_NUMBER = "MAJOR_VERSION_NUMBER"
        LOAD_KEY_MINOR_VERSION_NUMBER = "MINOR_VERSION_NUMBER"
        LOAD_KEY_REVISION_NUMBER = "REVISION_NUMBER"

        members_list=inspect.getmembers(module)

        for members_node in members_list:
            if members_node[0] == LOAD_KEY_MAJOR_VERSION_NUMBER:
                testlib_ver_major=members_node[1]

            elif members_node[0] == LOAD_KEY_MINOR_VERSION_NUMBER:
                testlib_ver_minor_number=members_node[1]

            elif members_node[0] == LOAD_KEY_REVISION_NUMBER:
                testlib_ver_revision_number=members_node[1]
        assert (testlib_ver_major != None) and \
               (testlib_ver_minor_number != None) and \
               (testlib_ver_revision_number != None)
        return testlib_ver_major,testlib_ver_minor_number,testlib_ver_revision_number
    
    
    def init_version(self,compiler_dir):
        """
        初始化打包文件的版本号
        """
        
        # 设置编译版与非编译版标签
        if self.need_compile == 1:
            no_compile_tag = ''
        else:
            no_compile_tag = 'src_'
            
        # 从property文件中获取版本信息
        try:
            if self.property_file_path:
                MAJOR_VERSION_NUMBER, MINOR_VERSION_NUMBER, REVISION_NUMBER = self.get_version_info(self.property_file_path)
            else:
                err_info = u"未找到当前测试库的配置文件，请确认配置文件是否存在！"
                print err_info
                raise ATT_Error, err_info
            
        except Exception, e:
            raise ATT_Error, e.message
        
        if self.version_type == "a":
            _version_type = "%sa" % REVISION_NUMBER
        elif self.version_type == "b":
            _version_type = "%sb" % REVISION_NUMBER
        elif self.version_type == "g":
            _version_type = "%sr" % REVISION_NUMBER
        else:
            _version_type = REVISION_NUMBER
        
        self.version = "%sv%s.%s.%s"  % (no_compile_tag, 
                 MAJOR_VERSION_NUMBER, MINOR_VERSION_NUMBER,  _version_type)
        
        print u'当前打包版本版本号为： %s ' % self.version  
    
    
    def get_py_files(self, all_file_list):
        """
        从all_file_list中过滤所有以.py为后缀的文件
        """
        
        file_list = []
        for file in all_file_list:
            file_type = os.path.splitext(file)[1]
            if file_type.lower() == ".py":
                file_list.append(file)
            else:
                pass
        return file_list
    

    def main(self):
        """
        打包主流程
        """
        
        self.svn_commit_revision = 'debug_'
        self.svn_url = ""
        self.svn_commit_time = ""
        self.pack_time = ""
        
        print u"1、清除临时文件."
        try:
            clearobject=ClearTempFiles()
            clearobject.clear_dir_tmp_files(self.main_dir)        
        except Exception, e:
            print u"清除临时文件出错，错误信息为%s" % e
            return
        
        print u"2、清除上次打包的临时文件."
        try:
            clearobject.clear_dir_temp_dir(self.main_dir, self.temp_dir_name)
        except Exception, e:
            print u"清除上次打包的临时文件出错，错误信息为%s" % e
            return
        
        print u"3、清除打包后的结果文件."
        try:
            clearobject.clear_dir_temp_dir(self.main_dir, self._zip_dir_name)
        except Exception, e:
            print u"清除打包后的结果文件出错，错误信息为%s" % e
            return
        
        # 检查是否是debug模式
        if self.debug:
            print u"4、当前模式为DEBUG模式，不需要检查svn版本."
        
        else:
            print u"4、当前模式为非DEBUG模式，开始检查svn版本."
            
            try:
                self.check_svn_version()
            except Exception, e:
                err_info = u"检查svn版本出错，错误信息为：%s" % e
                print err_info
                return
                
            print u"获取当前目录svn版本号成功，svn版本号为：%s" % self.svn_commit_revision
        
        print u"5、开始复制目录."
        work_dir = os.path.join(self.main_dir)
        
        # 创建编译目录
        compiler_dir = os.path.join(self.main_dir, self.temp_dir_name + time.strftime('%Y%m%d%H%M%S__'))
        if not os.path.exists(compiler_dir):
            os.mkdir(compiler_dir)
        
        print u"当前打包文件临时目录为：%s"  % compiler_dir
        print u"开始复制目录%s 到 %s " % (work_dir, compiler_dir)
        
        try:
            self.init_compiler_dir(work_dir, compiler_dir)
        except Exception, e:
            err_info = u"复制目录出错，错误信息为：%s" % e
            print err_info
            return
            
        print u"6、开始组建版本信息！"
        try:
            self.init_version(compiler_dir)
        except Exception,e:
            print u"初始化版本号出错，错误信息为：%s" % e
            return
        
        
        if self.need_compile == True:
            
            print u"7、开始编译文件"
            
            try:
                #获取.py文件列表
                file_list = self.get_py_files(walk_dir(compiler_dir))
                
                #编译文件
                compileall.compile_dir(compiler_dir, 100, "", True, re.compile(r'____temp__temp____'), True)
                
                print u"编译.py文件成功"
                
                for file in file_list:
                    os.remove(file)
                
            except Exception, e:
                print u"编译文件出错，错误信息为: %s" % e
                return
            
        else:
            print u"7、设置为不编译文件"
        
        
        # 创建安装包目录
        print u"8、创建_INSTALL_文件夹"
        _install_dir = os.path.join(self.main_dir, "_INSTALL_" )
        if not os.path.exists(_install_dir):
            os.mkdir(_install_dir)
        
        # 组建安装包文件名
        install_dir = os.path.join(_install_dir, self.version )
        if not os.path.exists(install_dir):
            os.mkdir(install_dir)
        
        # 暂时不加版本号
        #install_file = os.path.join(install_dir, TESTLIB_NAME + "_" + self.version + ".zip")
        install_file = os.path.join(install_dir, "UpgradeServer"+'_'+self.version + ".zip")
        
        print (u"9、开始打包文件到：%s."% install_file)
        
        # 打包zip安装包
        try:
            zip_folder(compiler_dir, install_file)
        except Exception,e:
            print u"打包文件出错，错误信息为：%s" % e
            return
        
        # 删除编译目录
        print u"10、打包成功，开始删除临时文件；"
        shutil.rmtree(compiler_dir)
        
        print u"生成安装包成功，本地安装包路径为 %s ；" % (install_file)
        
        if self.need_upload:
            #TODO upload file to upgrade server
            pass
        else:
            pass
            #复制打包文件到packge/plugin下面
            # _INSTALL_PACKAGE_PATH= os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            # output=os.path.join(_INSTALL_PACKAGE_PATH, "package")
            #
            # if not os.path.exists(output):
            #     print "mkdir: %s"%(output)
            #     os.mkdir(output)
            #
            # output=os.path.join(output, "plugin")
            # if not os.path.exists(output):
            #     print "mkdir: %s"%(output)
            #     os.mkdir(output)
            #
        # shutil.copy2(install_file, output)
        # print u"复制 %s 到 %s ." % (install_file, output)
    

def pack():
    
    try:
        print("Welcome %s Packager!" % TESTLIB_NAME)
        
        # 选择当前模式是否为dubug模式
        user_input = raw_input("Do you want to check svn version?(y|n):")
        if user_input.lower() == "y":
            debug = False
        else:
            debug = True
        
        # 设置版本
        user_input = raw_input("which kind of version do you want to compile?(a:Alpha, b:Beta, g:Gamma, s:Stable): ")
        if user_input.lower() == "a":
            version_type = "a"
        elif user_input.lower() == "b":
            version_type = "b"
        elif user_input.lower() == "g":
            version_type = "g"
        else:
            version_type = "s"
        
        # 选择是否上传打包后的文件到升级服务器上

        need_upload = False
        need_compile = True
        
        # 设置打包主目录
        global PROJECT_HOME
        main_dir = os.path.dirname(os.path.dirname(__file__))
        PROJECT_HOME = main_dir
        
        # 开始打包
        compile_obj=CompileFiles(main_dir, debug, version_type, need_compile, need_upload)
        compile_obj.main()
       
        print("\n Exit %s Packager!" % TESTLIB_NAME)
    except Exception, e:
        print e.message
    os.system("pause")
    
    
if __name__ == '__main__':
    pack()
    

