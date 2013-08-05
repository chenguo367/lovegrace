#!/usr/bin/python
#coding:utf-8

# /*************************************************************************
#  Copyright (C), 2013-2014, SHENZHEN GONGJIN ELECTRONICS. Co., Ltd.
#  module name: start
#  function: 升级服务器启动入口
#
#  Author: ATT development group
#  version: V2.0
#  date: 2013.06.20
#  change log:
#  cheng    20130705    created
#  cheng    20130723    changed 支持命令行参数，并可扩展
# ***************************************************************************

__doc__="""CmdParse
一个简单的命令行解析器
"""
import sys
from optparse import OptionParser,OptionError

from upgrade.UpgradeServerProperty import ProgramName,Version,log as history

class SoftWareDsc:
    def __init__(self,name,version):
        self.name = name
        self.version = version

    def __str__(self):
        return "%s\nVersion : %s"% (self.name,self.version)

upgradeServer = SoftWareDsc(ProgramName,Version)

class CmdParse(object):

    def __init__(self, ):

        self.usage = "%prog [options]"
        self.args = []
        self.description = upgradeServer
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
                                       version=str(self.description) )

    def buildOptions(self):
        """
        Basic options setup. Other classes should call this before adding
        more options
        """
        if self.parser is None:
            self.buildParser()
        self.parser.add_option("--history",
                               action="store_true",
                               default=False,
                               help="show version history and exit")

        self.parser.add_option("-d", "--debug",
                               action="store_true",
                               default=False,
                               help="start program in debug mode")

        self.parser.add_option("-p", "--port",
                               type=int,
                               default=8001,
                               help="set the listening port number must between 1024 and 65535")

        self.parser.add_option("--logname",
                               type=str ,
                               dest = "logFileName",
                               default='',
                               help="set the log file name (there can be no suffix)")

    def parseOptions(self):
        """
        Uses the optparse parse previously populated and performs common options.
        """
        if not self.args:
            args = sys.argv[1:]
        (self.options, self.args) = self.parser.parse_args(args=args)

    def run(self):
        #参数预处理
        import upgrade.utils as log_config
        if self.options.history:
            sys.stdout.write(("Version History:\n%s"%history).encode(sys.stdout.encoding))
            self.stop()
        if self.options.debug:
            log_config.Logger.log_level = "debug"
        if self.options.logFileName:
            mylog = log_config.Logger().getLogger(self.options.logFileName)
            log_config.Logger.logger = mylog
        if self.options.port < 1024 or self.options.port > 65535:
            ex = OptionError("invalid integer value: '%d' "
                             "port must between 1024 and 65535"%self.options.port,"-p|--port")
            self.parser.error(str(ex))
        #加载环境
        import upgrade.main as server
        server.start(self.options.port)

    def stop(self,):
        sys.exit()
if __name__ == "__main__":
    c = CmdParse()
    c.run()
