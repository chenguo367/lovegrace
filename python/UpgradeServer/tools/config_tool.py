#!/usr/bin/python
#coding:utf-8
__author__ = 'chenguo'
__doc__ = """配置导入工具，提供对服务器权限管理进行命令行管理包括：
* 权限控制模块开关配置
* 可查询的默认版本配置
* 指定机器码的权限配置(增删改)
"""
import os
import sys
from optparse import OptionParser,OptionError

VERSION = 'v1.0.0'
NAME = 'Configuration import tool'

FILE_DIR = os.path.realpath(__file__)
ROOT_DIR = os.path.split(os.path.dirname(FILE_DIR))[0]
module_path = os.path.join(ROOT_DIR)
sys.path.insert(0,module_path)

from upgrade.config import *

class CmdParse(object):

    def __init__(self,):

        self.usage = "%prog [options]"
        self.args = []
        self.description =  "%s\nVersion : %s"%(NAME,VERSION)
        self.parser = None
        self.buildParser()
        self.buildOptions()
        self.parseOptions()

    def buildParser(self):
        """
        Create the options parser
        """
        #加载版本信息
        if not self.parser:
            self.parser = OptionParser(usage=self.usage,
                                       version=str(self.description))

    def buildOptions(self):
        """
        Basic options setup. Other classes should call this before adding
        more options
        """
        if self.parser is None:
            self.buildParser()

        self.parser.add_option("-d","--disable",
                               action="store_true",
                               default=False,
                               dest = "disable",
                               help="disable the access control module and exit")
        self.parser.add_option("-e","--enable",
                               action="store_true",
                               default=False,
                               dest = "enable",
                               help="enable the access control module")
        self.parser.add_option("-r","--run",
                               action="store_true",
                               default=False,
                               dest = "run",
                               help="run and parse the file cmds")
        self.parser.add_option("--show",
                               action="store_true",
                               default=False,
                               dest = "show",
                               help="show the detailed configuration information and exit")
        self.parser.add_option("-s","--set_default",
                               type="string",
                               default="",
                               dest = "default",
                               help="set the default version access(Alpha Beta Gamma Stable)")
        self.parser.add_option("-f", "--file",
                               type="string",
                               default="config.txt",
                               help="set the user interface configuration file name")


    def parseOptions(self):
        """
        Uses the optparse parse previously populated and performs common options.
        """
        if not self.args:
            args = sys.argv[1:]
        (self.options, self.args) = self.parser.parse_args(args=args)

    def run(self):
        cm = ConfigManager(self.options)
        setattr(cm,"sys",self)
        if not sys.argv[1:]:
            model = "cmd"
            #cmd 交互模式
            cm.log('welcome to cmd line model.\nType "help", "show" for more information.')
            while True:
                if 1:
                    sys.stdout.write(">"*3)
                    sys.stdout.flush()
                    uip = UserInterfaceParse(sys.stdin,model)
                    [line] = uip.lines
                    if line.strip() in ("quit","q"):
                        break
                    if not line.strip():
                        continue
                    if line.strip() == "show":
                        cm.show_info()
                    elif line.strip() == "help":
                        cm.log("usage:\nset [machine_num]  [alpha|beta|gamma|stable]\ndel [machine_num]")
                    else:
                        uip.parse_line(line)
                        jobs = uip.filter()
                        jobs_count = sum([len(i) for i in jobs.values()])
                        if 0 == jobs_count:
                            cm.log("无效的命令:%s"%line.strip())
                        cm.start_setting(jobs,model)
            cm.log("用户退出")
            self.stop()
        if cm.is_available():
            cm.process()

    def stop(self,):
        sys.exit()

class ConfigManager(object):

    available = False
    def __init__(self,options):
        self.options = options
        if self.options:
            self.check_args()

    def check_args(self):
        if self.options.enable and self.options.disable:
            self.log("操作失败：不能同时开启和关闭权限控制模块")
            return
        self.available = True

    def is_available(self):
        return self.available

    def process(self):
        if self.options.show:
            self.show_info()
            self.sys.stop()

        if self.options.enable:
            self.enable_control()

        if self.options.disable:
            self.disable_control()
            self.sys.stop()

        if self.options.default:
            if self.options.default.lower() in ACCESSES:
                self.set_default_access()
            else:
                self.log("操作失败：默认版本只能是 Alpha Beta Gamma Stable 中的一个。")

        if self.options.run:
            os.chdir(os.path.dirname(FILE_DIR))
            if os.path.isfile(self.options.file):
                uip = UserInterfaceParse(self.options.file)
                #解析文件
                jobs = uip.compile()
                del uip
                os.chdir(ROOT_DIR)
                self.start_setting(jobs)
            else:
                self.log("操作失败：无效的文件路径")
                self.sys.stop()

    def show_info(self):
        status = config.get("VersionControl","enabled")
        default = config.get("VersionControl","default_version")
        self.log("当前模块的开关状态：\t%s"%status)
        self.log("当前默认可查询版本：\t%s"%default)

        _list = config.items("MachineAccess")
        if not _list:
            info = "None"
        else:
            info = "\n".join(["%s = %s"%i for i in _list])
        self.log("当前设置的机器码权限：\n%s"%info)
        self.log("="*20)

    def get_status(self):
        return config.get("VersionControl","enabled")

    def start_setting(self,jobs,model="text"):
        """
        设置机器码操作权限
        @param jobs:解析用户接口配置文件里的命令
        @return:None
        """
        result = {
            "suc" : [],
            "fail" : []
        }
        for cmds in jobs.values():
            #set cmds and del cmds
            for cmd in cmds:
                args = tuple(cmd[1:])
                ret_msg =self._set(*args)

                if ret_msg == "suc":
                    cmd.append("执行成功")
                    result["suc"].append(' '.join(cmd))
                else:
                    #put error info into list
                    cmd.append(ret_msg)
                    result["fail"].append(' '.join(cmd))
        self.commit()
        if model != "cmd":
            #批量解析命令打印
            suc_cmd = "\n".join(result["suc"])
            if not suc_cmd:
                suc_cmd = "None"
            failed_cmd = "\n".join(result["fail"])
            if not failed_cmd:
                failed_cmd = "None"
            self.log("成功执行命令：\n"+suc_cmd)
            self.log("执行命令失败：\n"+failed_cmd)
        else:
            #命令行解析命令结果打印
            for info in (info for info in [infos for infos in result.values() if infos] if info):
                self.log(info.pop())

    def _set(self,name,value=''):
        error_header = "|Error:%s"
        info = "init"
        has_machine = config.has_option("MachineAccess",name)
        if value:
            if value.lower() in ACCESSES:
                config.set("MachineAccess",name,value)
                info =  "suc"
            else:
                info = error_header%("无效的版本设置%s"%value)
        elif not value:
            if has_machine:
                config.remove_option("MachineAccess",name)
                info =  "suc"
            else:
                info = error_header%("删除失败，没有找到对应机器码%s"%name)
        return info


    def set_default_access(self,default = None):
        old_default = config.get("VersionControl","default_version").lower()
        if not default:
            dest_default = self.options.default.lower()
        else:
            dest_default = default
        if old_default == dest_default:
            self.log("操作失败：默认可查询版本已经是%s，系统什么也没做。"%dest_default)
        else:
            config.set("VersionControl","default_version",dest_default)
            self.log("操作成功：默认可查询版本设置为%s。"%dest_default)
            self.commit()

    def enable_control(self):
        if config.get("VersionControl","enabled").lower() != "on":
            config.set("VersionControl","enabled","on")
            self.log("操作成功：权限控制已开启。")
            self.commit()
        else:
            self.log("操作失败：权限控制已经是开启的，系统什么也没做。")

    def disable_control(self):
        if config.get("VersionControl","enabled").lower() != "off":
            config.set("VersionControl","enabled","off")
            self.log("操作成功：权限控制已关闭。")
            self.commit()
        else:
            self.log("操作失败：权限控制已经是关闭的，系统什么也没做。")

    def commit(self,file_path = CONF_FILE_PATH):
        fp = open(file_path,'w')
        config.write(fp)
        fp.close()

    def log(self,_str,encoding=''):
        if not encoding:
            encoding = sys.stdout.encoding
        if not isinstance(_str,unicode):
            _str = _str.decode('utf-8')
        print _str.encode(encoding)


class UserInterfaceParse(object):
    cmd_key = ["set","del"]
    note = "--"
    def __init__(self,file_name,model = "text"):
        """
        用户接口命令解析
        @param file_name: 写有命令的文件或者是一个有readlines方法的对象
        @param model:用户接口解析类型：cmd 单命令行解析，text 文本解析（多行命令批量解析），
        """
        if hasattr(file_name,"readlines"):
            self.file = file_name
        else:
            self.file = open(clean_bom(file_name),"rb")
        if model != 'cmd':
            self.lines = self.file.readlines()
        else:
            #命令行单行解析
            self.lines = [self.file.readline()]
        self.model = model
        self.jobs = dict().fromkeys(self.cmd_key,None)
        for k in self.jobs.keys():
            self.jobs[k]=[]

    #批量解析命令接口
    def compile(self,lines = list()):
        """
        >>>import StringIO
        >>>uip = UserInterfaceParse(StringIO.StringIO())
        >>>jobs = uip.compile(lines) #这里参数为需要解析的命令行列表
        >>>ConfigManager(list()).start_setting(jobs)#调用ConfigManager的配置方法进行配置
        @return:解析后的命令行
        """
        if 0 ==  len(lines):
            lines = self.lines
        for line in lines:
            self.parse_line(line)
        return self.filter()

    #解析单条命令接口
    def parse_line(self, line):
        """
        将命令行解析后，放进jobs字典中
        >>>import StringIO
        >>>uip = UserInterfaceParse(StringIO.StringIO())
        >>>uip.parse_line(line)#这里参数为需要解析的一条命令行
        >>>jobs = uip.jobs
        >>>ConfigManager(list()).start_setting(jobs,"cmd")#调用ConfigManager的配置方法进行配置
        @param line:一条命令
        @return:None
        """
        if line.startswith(self.note): return
        _line = line.strip()
        cmd_args = _line.split()
        if len(cmd_args) == 1 or len(cmd_args) > 3:
            return
        cmd = cmd_args[0]
        args = cmd_args[1:]
        #不支持大小写使用，必须小写
        if cmd not in self.cmd_key:
            return
        else:
            self.jobs[cmd].append(cmd_args)


    def filter(self):
        filter_set = lambda x:len(x)==3
        filter_del = lambda x:len(x)==2
        self.jobs["set"] = filter(filter_set,self.jobs["set"])
        self.jobs["del"] = filter(filter_del,self.jobs["del"])
        return self.jobs

#配置接口
def setting(cmd):
    """
    配置命令接口，执行配置命令
    @param cmd:配置命令或命令行列表
    @return:
    """
    model = 'text'
    if isinstance(cmd,basestring):
        cmd = [cmd]
        model = 'cmd'
    cm = ConfigManager(list())
    import StringIO
    uip = UserInterfaceParse(StringIO.StringIO())
    jobs = uip.compile(cmd)#这里参数为需要解析的一条命令行
    cm.start_setting(jobs,model)#调用ConfigManager的配置方法进行配置
    if 'on' != cm.get_status():
        cm.log("权限控制模块没有开启，配置将在模块开关开启后生效。")

def on():
    """
    开启权限控制
    @return:
    """
    ConfigManager(list()).enable_control()

def off():
    """
    关闭权限控制
    @return:
    """
    ConfigManager(list()).disable_control()

def setDefault(default):
    """
    设置默认可查询版本
    @param default:版本(Alpha Beta Gamma Stable)
    @return:
    """
    cm = ConfigManager(list())
    cm.set_default_access(default)
    if 'on' != cm.get_status():
        cm.log("权限控制模块没有开启，配置将在模块开关开启后生效。")

def test():
    off()
    setting(['set a gamma','set b gamma'])
    setting('set c gamma')


if __name__ == "__main__":
    c = CmdParse()
    c.run()
    # test()
