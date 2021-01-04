#!/usr/bin/env python
# -*- coding: utf-8 -*-
from _ctypes import sizeof
from sepolgen.refparser import success
from blivet.devices.device import Device

# Import python built-ins
'''
Created on Aug 3, 2018

@author: root
'''
import sys
import os
import threading
import math
import re
import traceback
import signal
import logging
import string
from time import sleep
#import smi_comm

import re
import time
from shutil import copyfile
import subprocess
import types


import os
from time import sleep
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter
import re
import sys
import signal
import time
import shutil
import csv
import struct
import subprocess
import threading
import linecache
import ConfigParser
import StringIO

def foo1():
    pass
    #self.Print ("foo!")
    
    
class SATA_c(object):
    
    
    def __init__(self, argv):
        self.mArgv = argv[1:]   # ['/dev/nvme0n1', subcase items and other parameters]
        self.ScriptParserArgs=[]  
    
        self.dev, self.UserSubItems, self.DynamicArgs \
        =  self.ParserArgv(self.mArgv, self.CreateSubCaseListForParser())    
        

    
    
    def CreateSubCaseListForParser(self):
        return ""    
    
    
    
    
    
    def shell_cmd(self, cmd, sleep_time=0):    
        fd = os.popen(cmd)
        msg = fd.read().strip()
        fd.close()
        sleep(sleep_time)
        return msg     

    def shell_cmd_with_sc(self, cmd, sleep_time=0):
        # return command info(string) and status code(int)
        cmd = cmd + "; echo $?"
        mStr = self.shell_cmd(cmd, sleep_time)        
        SC = int(mStr.split()[-1])# last line is status code
        value = mStr.rsplit("\n",1)[0]# after remove the last line, is return value
        # if command fail and is nvme cli command
        if SC!=0:
            mStr="NVMe\s+Status.+\((\w+)\)" # ex. NVMe Status:INVALID_NS(b) NVMe\s+Status.+\((\w+)\)
            if re.search(mStr, value, re.IGNORECASE):
                SC = re.search(mStr, value, re.IGNORECASE).group(1)  
                SC = int(SC, 16)
                SC = SC&0xFF
        
        return value, SC
    
    def ata_cmd(self, cmd, sleep_time=0):   
        cmd = cmd + " 2>&1"
        rtStr, SC = self.shell_cmd_with_sc(cmd, sleep_time)
        ATADescriptor = ATADescriptorReturn_c()
        ATADescriptor.CmdRtStr = rtStr
        ATADescriptor.CmdRtCode = SC

        # get Raw sense data from return string, start from 'Raw sense data (in hex):'
        startPtr = rtStr.find('Raw sense data (in hex):')
        if startPtr!=-1:
            SenseDataStr = rtStr[startPtr + 24: -1] # substring without 'Raw sense data (in hex):'
            mstr = '\s\w{2}'
            SenseData = re.findall(mstr, SenseDataStr, re.IGNORECASE)
            if len(SenseData)==22:
                ATADescriptor.ResponseCode = int(SenseData[0],16)
                ATADescriptor.SenseKey = int(SenseData[1],16)
                ATADescriptor.AdditionalSenseCode = int(SenseData[2],16)
                ATADescriptor.AdditionalSenseQualifier = int(SenseData[3],16)
                ATADescriptor.DescriptorCode = int(SenseData[8],16)
                ATADescriptor.AdditionalDescriptorLength = int(SenseData[9],16)
                ATADescriptor.Extend = int(SenseData[10],16)
                ATADescriptor.Error = int(SenseData[11],16)
                ATADescriptor.SecotrCount = int(SenseData[13],16)
                ATADescriptor.LBA_Low = int(SenseData[15],16)
                ATADescriptor.LBA_Mid = int(SenseData[17],16)
                ATADescriptor.ResponseCode = int(SenseData[0],16)
                ATADescriptor.LBA_High = int(SenseData[19],16)
                ATADescriptor.Device = int(SenseData[20],16)
                ATADescriptor.Status = int(SenseData[21],16)
            

        return ATADescriptor
        
        
    
    def ParserArgv(self, argv, SubCaseList=""):
        # argv[1]: device path, ex, '/dev/nvme0n1'
        # argv[2]: subcases, ex, '1,4,5,7'
        # argv[3]: script test mode on, ex, '-t'
        # common arg define
        parser = ArgumentParser(description=SubCaseList, formatter_class=RawTextHelpFormatter)
        parser.add_argument("dev", help="device, e.g. /dev/nvme0n1", type=str)
        parser.add_argument("subcases", help="sub cases that will be tested, e.g. '1 2 3'", type=str, nargs='?')

        # script arg define new args if overwrite in script
        for mArg in self.ScriptParserArgs:
            optionName=mArg[0]
            optionNameFull=mArg[1]
            helpMsg=mArg[2]
            argType=mArg[3]
            default=mArg[4] 
            parser.add_argument("-%s"%optionName, "--%s"%optionNameFull, help=helpMsg, type=argType, nargs='?')
        # Display help message with python argparse when script is called without any arguments
        if len(argv)==0:
            parser.print_help(sys.stderr)
            sys.exit(1)
        # parser here
        args = parser.parse_args(args=argv)
        
        mDev=args.dev

        if args.subcases==None:
            mSubItems=[]
        else:
            # split ',' and return int[]
            mSubItems = [int(x) for x in args.subcases.split(',')]     
            
        
        # parse script args, and return by order
        mScriptParserArgs=[]
        for mArg in self.ScriptParserArgs:
            optionName=mArg[0]
            optionNameFull=mArg[1]
            helpMsg=mArg[2]
            argType=mArg[3]
            default=mArg[4]            
            value=None if args.__dict__[optionNameFull]==None else args.__dict__[optionNameFull] # get by dictionary
            value = value if value != None else default # if user not input arg, then use default
            mScriptParserArgs.append(value)
        
        #mCheckSmart=True if args.checksmart else False
        
        return mDev, mSubItems, mScriptParserArgs
    
    def SetDynamicArgs(self, optionName, optionNameFull, helpMsg, argType, default=None,\
                        iniFileName=None, iniSectionName=None, iniOptionName=None):
        # after SetDynamicArgs, using GetDynamicArgs to get arg if element exist, else return None
        # ex.  self.AddParserArgs(optionName="x", optionNameFull="disablepwr", helpMsg="disable poweroff", argType=int) 
        #        self.DisablePwr = self.GetDynamicArgs(0)
        # default value priority is iniFileName>default
        
        # if iniFileName!=None, using ini file to set default value and show in helpMsg
        if iniFileName!=None:
            config = self.getConfigParser(iniFileName)
            SectionName = "None" if iniSectionName==None else iniSectionName # if iniSectionName=None, set SectionName = 'None' string
            if config.has_option(SectionName, iniOptionName):    
                if argType==int:
                    default = config.getint(SectionName, iniOptionName) 
                if argType==float:
                    default = config.getfloat(SectionName, iniOptionName)           
                if argType==str:
                    default = config.get(SectionName, iniOptionName)
                    
                helpMsg += "\n%s"%self.HighLightRed("Default(%s): %s"%(iniFileName, default))
            else:    
                helpMsg += "\n%s"%self.HighLightRed("option(%s) in %s is missing, set Default: %s"%(iniOptionName, iniFileName, default))                     
            
                     
        # set ScriptParserArgs
        helpMsg += "\n "
        self.ScriptParserArgs.append([optionName, optionNameFull, helpMsg, argType, default])

    def PrintProgressBar(self, iteration, total, prefix = '', suffix = '', decimals = 1, length = 50, fill = 'x', showPercent=True):
    # Print iterations progress
    # Usage:  mNVME.PrintProgressBar(i + 1, 100, prefix = 'Progress:', suffix = 'Complete', length = 50)
        """
        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
        """

        
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        if showPercent:
            mstr = '%s |%s| %s%% %s' % (prefix, bar, percent, suffix)
        else:
            mstr = '%s |%s| %s' % (prefix, bar, suffix)
        #mstr = '\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix)
        '''
        sys.stdout.write(u"\033[1000D" + self.PrefixString()+mstr)
        sys.stdout.flush() 
        self.stdoutBk.write(u"\033[1000D" + self.PrefixString()+mstr)
        self.stdoutBk.flush()         
        '''
        # remove string  > console width
        try: # if using eclipse to debug, then set col to 40
            self.RecordCmdToLogFile = False # no need to record command
            columns = self.shell_cmd("tput cols")
            self.RecordCmdToLogFile = True
        except:
            columns = 40
        mStr = mstr
        
        sys.stdout.write(u"\u001b[s") # saves the current cursor position
        sys.stdout.write(u"\033[0J") # clear all string after courser
        sys.stdout.write(mStr) # write
        sys.stdout.flush() 
        sys.stdout.write(u"\u001b[u") # restores the cursor to the last saved position
   
        # Print New Line on Complete

        if iteration == total: 
            print "\r"
        
    
class ATADescriptorReturn_c():
    # sam define
    CmdRtStr = None
    CmdRtCode = None
    
    # spec define
    ResponseCode = None #0
    SenseKey = None #1
    AdditionalSenseCode = None #2
    AdditionalSenseQualifier = None # 3
    AdditionalLength = None #7
    DescriptorCode = None #8
    AdditionalDescriptorLength = None #9
    Extend = None #10
    Error = None #11
    SecotrCount = None #12,13
    LBA_Low = None #14,15
    LBA_Mid = None #16,17
    LBA_High = None #18,19
    Device = None #20
    Status = None    #21
    
    
    
    
    
