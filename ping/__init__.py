#coding :utf-8

__author__ = 'chenguo'

import os
import sys
ROOT_DIR = os.path.split(os.path.dirname(__file__))[0]
EXT_LIBS_DIR = os.path.join(ROOT_DIR,'externallibs')
if not EXT_LIBS_DIR in sys.path:
    sys.path.insert(0,EXT_LIBS_DIR)