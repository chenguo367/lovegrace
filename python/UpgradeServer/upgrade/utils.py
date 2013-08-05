#coding:utf-8

# /*************************************************************************
#  Copyright (C), 2013-2014, SHENZHEN GONGJIN ELECTRONICS. Co., Ltd.
#  module name: start
#  function: 工具函数库
#
#  Author: ATT development group
#  version: V1.0
#  date: 2013.06.20
#  change log:
#  cheng    20130623    created
# ***************************************************************************
"""
提供日志模块
提供python数据类型与Jason格式数据类型序列化/反序列化的转换接口
>>>from utils import Logger
>>>log = Logger().getLogger('upgradeserver')
>>>log.info("hello,world")
"""

__all__ = ["Logger","json","unjson"]

import logging
import os
import json as _json
import re

#设置日志目录
ROOT_DIR = os.path.split(os.path.dirname(__file__))[0]
LOG_DIR = os.path.join(ROOT_DIR, "log")
##

class Logger(object):
    logger = None

    levels = {"notset" : logging.NOTSET,
              "debug" : logging.DEBUG,
              "info" : logging.INFO,
              "warn" : logging.WARN,
              "error" : logging.ERROR,
              "critical" : logging.CRITICAL}

    log_level = "info"
    log_dir = LOG_DIR
    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)
    log_max_byte = 10 * 1024 * 1024
    log_backup_count = 5
    echolog = True

    def setLevel(self,level):
        self.log_level = self.levels.get(level,logging.INFO)

    def getLogger(self,lname = 'test',fname = ''):
        self.logname = lname
        if self.logger is not None:
            return self.logger
        import logging.handlers
        self.logger = UnicodeLogger(self.logname)
        # self.logger = logging.Logger(self.logname)
        if not fname:
            fname = self.logname
        log_handler = logging.handlers.RotatingFileHandler(filename = os.path.join(self.log_dir, fname+".log"),
                                                           maxBytes = self.log_max_byte,
                                                           backupCount = self.log_backup_count,)
                                                           # encoding = "utf8")
        log_fmt = logging.Formatter(
            "%(asctime)s %(levelname)s %(filename)s:%(lineno)d : %(message)s",
            "%Y-%m-%d %H:%M:%S")
        log_handler.setFormatter(log_fmt)
        self.logger.addHandler(log_handler)
        #add by chenguo 2013-7-18
        if self.echolog:
            import sys
            #create stream hander
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setFormatter(log_fmt)
            self.logger.addHandler(stream_handler)

        if not isinstance(self.log_level,int):
            self.logger.setLevel(self.levels.get(self.log_level))
        return self.logger

class UnicodeLogger(logging.Logger):
    def _log(self, level, msg, args, exc_info=None, extra=None):
        msg = str(msg)
        if isinstance(msg,str):
            msg = msg.decode('utf-8')
        logging.Logger._log(self, level, msg, args, exc_info, extra)


def _recursiveCaster(ob):
    if isinstance(ob, dict):
        result = {}
        for k, v in ob.iteritems():
            result[str(k)] = _recursiveCaster(v)
        return result
    elif isinstance(ob, list):
        return [_recursiveCaster(x) for x in ob]
    elif isinstance(ob, unicode):
        return str(ob)
    else:
        return ob


class StringifyingDecoder(_json.JSONDecoder):
    """
    Casts all unicode objects as strings. This is necessary until Zope is less
    stupid.
    """
    def decode(self, s):
        result = super(StringifyingDecoder, self).decode(s)
        return _recursiveCaster(result)

class JavaScript(object):
    """A simple class that represents a JavaScript literal that should not be JSON encoded."""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value

class JavaScriptRegex(JavaScript):
    """A simple class that represents a JavaScript Regex literal that should not be JSON encoded."""
    def __str__(self):
        return '/' + self.value + '/'

class JavaScriptEncoder(_json.JSONEncoder):
    """A JavaScript encoder based on JSON. It encodes like normal JSON except it passes JavaScript objects un-encoded."""

    _js_start = '__js_start__'
    _js_end = '__js_end__'
    _js_re = re.compile(r'\["%s", (.*?), "%s"\]' % (_js_start, _js_end))

    def default(self, obj):
        if isinstance(obj, JavaScript):
            return [self._js_start, str(obj), self._js_end]

        return _json.JSONEncoder.default(self, obj)

    def _js_clean(self, jsonstr):
        # This re replace is not ideal but at least the dirtyness of it is encapsulated in these classes
        # instead of plain str manipulation being done in the wild.
        def fix(matchobj):
            return _json.loads(matchobj.group(1))

        return self._js_re.sub(fix, jsonstr)

    def encode(self, obj):
        return self._js_clean(_json.JSONEncoder.encode(self, obj))

def _sanitize_value(value, errors='replace'):
    """
    JSONEncoder doesn't allow overriding the encoding of built-in types
    (in particular strings), and allows specifying an encoding but not
    a policy for errors when decoding strings to UTF-8. This function
    replaces all strings in a nested collection with unicode strings
    with 'replace' as the error policy.
    """
    newvalue = value
    if isinstance(value,str):
        newvalue = value.decode('utf8', errors)
    elif isinstance(value, dict):
        newvalue = {}
        for k, v in value.iteritems():
            if isinstance(v, (str,set,list,dict,tuple)):
                newvalue[k] = _sanitize_value(v)
            else:
                newvalue[k] = v
    elif isinstance(value,(list,tuple)):
        newvalue = []
        for v in value:
            if isinstance(v, (str,set,list,dict,tuple)):
                newvalue.append(_sanitize_value(v))
            else:
                newvalue.append(v)
    elif isinstance(value,set):
        newvalue = set()
        for v in value:
            if isinstance(v, (str,set,list,dict,tuple)):
                newvalue.add(_sanitize_value(v))
            else:
                newvalue.add(v)

    return newvalue

def json(value, **kw):
    """
    Serialize C{value} into a JSON string.

    If C{value} is callable, a decorated version of C{value} that serializes its
    return value will be returned.

        >>> value = (dict(a=1L), u"123", 123)
        >>> print json(value)
        [{"a": 1}, "123", 123]
        >>> @json
        ... def f():
        ...     return value
        ...
        >>> print f()
        [{"a": 1}, "123", 123]

    @param value: An object to be serialized
    @type value: dict, list, tuple, str, etc. or callable
    @return: The JSON representation of C{value} or a decorated function
    @rtype: str, func
    """
    if callable(value):
        # Decorate the given callable
        def inner(*args, **kwargs):
            val = value(*args, **kwargs)
            try:
                return _json.dumps(val)
            except UnicodeDecodeError:
                sanitized = _sanitize_value(val)
                return _json.dumps(sanitized)

        # Well-behaved decorators look like the decorated function
        inner.__name__ = value.__name__
        inner.__dict__.update(value.__dict__)
        inner.__doc__ = value.__doc__
        return inner
    else:
        # Simply serialize the value
        try:
            return _json.dumps(value, **kw)
        except UnicodeDecodeError:
            sanitized = _sanitize_value(value)
            return _json.dumps(sanitized, **kw)

def javascript(data):
    """A JavaScript encoder based on JSON. It encodes like normal JSON except it passes JavaScript objects un-encoded."""
    return json(data, cls=JavaScriptEncoder)

def unjson(value, **kw):
    """
    Create the Python object represented by the JSON string C{value}.

        >>> jsonstr = '[{"a": 1}, "123", 123]'
        >>> print unjson(jsonstr)
        [{'a': 1}, '123', 123]

    @param value: A JSON string
    @type value: str
    @return: The object represented by C{value}
    """
    if 'cls' not in kw:
        kw['cls'] = StringifyingDecoder
    return _json.loads(value, **kw)

#额，写完这个函数发现os.makedirs也能完成该功能，所以这个函数扔这不用了
def win_mkdir(path, mode=0777):
    """
    windows下os.mkdir()不支持一次性创建多层次结构的目录。
    用此函数实现linux下一次创建多级目录
    @param path:目录名
    @return:True
    >>>path = '/'.join([str(i) for i in xrange(0,5)])
    >>>win_mkdir('D:/'+path)
    True
    """
    try:
        if not os.path.exists(path):
            #上层文件夹
            ex_path = os.path.split(path)[0]
            if win_mkdir(ex_path):
                os.mkdir(path)
        return True
    except Exception,e:
        return False

# os.makedirs(name='')
