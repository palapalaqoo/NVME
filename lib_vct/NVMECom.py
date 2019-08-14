#-*- coding: utf-8 -*-

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

class TimedOutExc(Exception):
    pass

def deadline(timeout, *args):
    def decorate(f):
        def handler(signum, frame):
            #self.Print ("Timeout!: %ss, quit sub case test!"%timeout)
            raise TimedOutExc(timeout)

        def new_f(*args):
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(timeout)
            return f(*args)
            signal.alarm(0)

        new_f.__name__ = f.__name__
        return new_f
    return decorate    

   
        
class NVMECom():   
    mTestModeOn=False
    SubItemNumValue=0
    RecordCmdToLogFile=False
    LogName_summary="log"
    LogName_SummaryColor="log"
    LogName_CmdDetail="log"
    LogName_ConsoleOut="log"
    ScriptParserArgs=[]  
    def SubItemNum(self):
        self.SubItemNumValue+=1
        return self.SubItemNumValue
    

            
    def InitLogFile(self):
        # self.LogPath default ='Log\'
        # remove all dir
        if os.path.exists(self.LogPath):
            shutil.rmtree(self.LogPath) 
        # Create dir
        if not os.path.exists(self.LogPath):
            os.makedirs(self.LogPath)
        #create log
        NVMECom.LogName_Summary =  self.LogPath + "summary_"+time.strftime('%Y_%m_%d_%Hh%Mm%Ss')+".log"
        f = open(NVMECom.LogName_Summary, "w")
        f.close()
        #create color log
        NVMECom.LogName_SummaryColor = self.LogPath + "summary_color_"+time.strftime('%Y_%m_%d_%Hh%Mm%Ss')+".log"
        f = open(NVMECom.LogName_SummaryColor, "w")
        f.close()    
        #create command log for save all host command that issue to the controller 
        NVMECom.LogName_CmdDetail =  self.LogPath + "detail_cmd_"+time.strftime('%Y_%m_%d_%Hh%Mm%Ss')+".log"
        f = open(NVMECom.LogName_CmdDetail, "w")
        f.close() 
        #create command log for save all console output
        NVMECom.LogName_ConsoleOut =  self.LogPath + "console_out_"+time.strftime('%Y_%m_%d_%Hh%Mm%Ss')+".log"
        f = open(NVMECom.LogName_ConsoleOut, "w")
        f.close()     

        f.close() 
        #create readme file
        NVMECom.LogName_Readme =  self.LogPath + "readme.txt"
        f = open(NVMECom.LogName_Readme, "w") 
        mStr ="summary_xxx:        summary for regression tool \n" + \
                    "summary_color_xxx:    color summary log \n" + \
                    "detail_cmd_xxx:        all the commands issued in this test \n" + \
                    "console_out_xxx:    color console output  \n" 
        f.write(mStr)
        f.write("\n")        
        f.close()        
        
                
        # redirect console output to file by using tee class
        sys.stdout = NVMECom.tee(NVMECom.LogName_ConsoleOut)
        
    class tee(object):
        def __init__(self, logFile):
            self.terminal = sys.stdout
            self.log = open(logFile, "a")
        
        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)  
        
        def flush(self):
                #this flush method is needed for python 3 compatibility.
                #this handles the flush command by doing nothing.
                #you might want to specify some extra behavior here.
            pass 
        
                 
            
    def __init__(self, son):        
        # set NVMECom parameters from subclass
        self.device=son.dev
        self.device_port=son.dev[0:son.dev.find("nvme")+5]
        self.mTestModeOn=son.TestModeOn
        self.StartLocalTime=son.StartLocalTime
        self.SubCasePoint=son.SubCasePoint
        self.LogPath=son.LogPath if  son.LogPath!=None else  'Log/'  # default = 'Log/'
        self.LogPath='%s/'%self.LogPath if self.LogPath[-1]!='/' else self.LogPath # add / if forgot to add /
        self.LogPath=self.LogPath[1:] if self.LogPath[0]=='/' else self.LogPath # remove / if first char is /
        
        # if object is created in subcase of main script, then do not init log files
        self.InitLogFile() if not son.isSubCaseOBJ else None
        self.LastCmd="None"
        self.LBARangeDataStructure=LBARangeDataStructure_(self)
        self.timer=timer_()
              
        

    @property
    def Second(self):
        return int(time.time())       

    def shell_cmd(self, cmd, sleep_time=0):
        #print to command log
        if self.RecordCmdToLogFile:
            self.Logger(cmd, mfile="cmd")
        self.LastCmd=cmd        
        fd = os.popen(cmd)
        msg = fd.read().strip()
        fd.close()
        sleep(sleep_time)
        return msg 
    
    def get_reg(self, cmd, reg, gettype=0, nsSpec=True):
    #-- cmd = nvme command, show-regs, id-ctrl, id-ns
    #-- reg = register keyword in nvme command
    #-- gettype:
    #--     0:    string, ex. cc: 460001, return "100064"
    #--     1:    string, ex. cc: 460001, return "460001"
    #--     16:     int,  ex. lpa: 0xf,return 15
        if nsSpec:
            DEV=self.device
        else:
            DEV=self.device_port
        #DEV=self.device if cmd=="id-ns" else self.device_port
        mStr="nvme %s %s |grep '%s ' |cut -d ':' -f 2 |sed 's/[^0-9a-zA-Z]*//g'" %(cmd, DEV, reg)
        if gettype==0:
            return self.shell_cmd(mStr)[::-1]
        if gettype==1:
            return self.shell_cmd(mStr)
        elif gettype==16:
            return int(self.shell_cmd(mStr), 16)

    def str_reverse(self, mstr):
        return mstr[::-1]
    def get_log(self, log_id, size, StartByte=-1, StopByte=-1, NVMEobj=None):
    #-- return string byte[0]+byte[1]+byte[2]+ ...
    #-- ex. return string "0123" where byte[0] = 0x01, byte[1] = 0x23
    #-- size, size in bytes
        self.device = NVMEobj.device if NVMEobj!= None else self.device
        if (StartByte==-1 and StopByte==-1):
            return  self.shell_cmd(" nvme get-log %s --log-id=%s --log-len=%s -b 2>&1|xxd -ps |cut -d ':' -f 2|tr '\n' ' '|sed 's/[^0-9a-zA-Z]*//g'" %(self.device, log_id, size))
        else:
            mStr=self.shell_cmd(" nvme get-log %s --log-id=%s --log-len=%s -b 2>&1|xxd -ps |cut -d ':' -f 2|tr '\n' ' '|sed 's/[^0-9a-zA-Z]*//g'" %(self.device, log_id, size))
            return mStr[StartByte*2:(StopByte+1)*2]


    def get_log2byte(self, log_id, size):
    #-- return list [ byte[0], byte[1], byte[2], ... ]
    #-- size, size in bytes
    #-- usage: mStr=get_log2byte(7, 512)=[01, 23, 45, 67, 89]
    #-- mStr[0]='01' , mStr[1]='23'  
        line = self.get_log(log_id, size)
        n=2
        return [line[i:i+n] for i in range(0, len(line), n)]       
    
    def get_log_passthru(self, LID, size, RAE=0, LSP=0, LPO=0, ReturnType=0, BytesOfElement=1, NVMEobj=None):
    #-- return list [ byte[0], byte[1], byte[2], ... ] if ReturnType=0
    #-- BytesOfElement, cut BytesOfElement to lists, ex. BytesOfElement=2,  return list [ byte[1]+byte[0], byte[3]+byte[2], ... ] ,if ReturnType=0
    #-- return string byte[0] + byte[1] + byte[2] + ...  if ReturnType=1   
    #-- size, size in bytes
    #-- usage: mStr=get_log_passthru(7, 512, rae, lsp, lpo)=[01, 23, 45, 67, 89]
    #-- mStr[0]='01' , mStr[1]='23'  
    #--RAE: Retain Asynchronous Event
    #--LSP: Log Specific Field
    #--LPO: Log Page Offset in byte
        NUMDL=int(size/4-1) & 0xFFFF
        NUMDU=int(size/4-1) >>16
        CDW10_int= (NUMDL<<16) + (RAE<<15) + (LSP <<8) + LID
        CDW10= '0x{:02x}'.format(CDW10_int)
        
        LPOL=LPO & 0xFFFFFFFF
        LPOU= LPO >> 32
        
        #cmd="nvme admin-passthru %s --opcode=0x2 -r --cdw10=0x007F0008 -l 512 2>&1 "%mNVME.dev
        self.device = NVMEobj.device if NVMEobj!= None else self.device
        cmd="nvme admin-passthru %s --opcode=0x2 -r --cdw10=%s --cdw11=%s --cdw12=%s --cdw13=%s -l %s 2>&1 "%(self.device, CDW10, NUMDU, LPOL, LPOU, size)
        mbuf=self.shell_cmd(cmd)
        return self.AdminCMDDataStrucToListOrString(mbuf,ReturnType, BytesOfElement)
            
    def AdminCMDDataStrucToListOrString(self, strIn, ReturnType=0, BytesOfElement=1):
    # input admin-passthru command Returned Data Structure, not that command must have '2>&1' to check if command success or not
    # output list or string
    #-- return list [ byte[0], byte[1], byte[2], ... ] if ReturnType=0 where byte[] is string type
    #-- return string byte[0] + byte[1] + byte[2] + ...  if ReturnType=1 where byte[] is string type      
    #-- BytesOfElement, cut BytesOfElement to lists, ex. BytesOfElement=2,  return list [ byte[1]+byte[0], byte[3]+byte[2], ... ] 
        # if command success
        if re.search("NVMe command result:00000000", strIn):
            line="0"        
            patten=re.findall("\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}", strIn)            
            patten1= ''.join(patten)
            line=patten1.replace(" ", "")    
            if ReturnType==0:
                # return list
                # put patten in to list type
                n=2
                listBuf= [line[i:i+n] for i in range(0, len(line), n)] 
                
                # set bytes of element, ex. [0, 1, 2, 3, 4..] , BytesOfElement= 3, -> [210, 543, 876..]
                if BytesOfElement!=1:
                    n=BytesOfElement                    
                    listBuf=["".join(list(reversed(listBuf[i:i+n]))) for i in range(0, len(listBuf), n)]
                    
                return listBuf
                    
            elif ReturnType==1:
                # return string
                return line
        else:
            return None
    
     
    def str2int(self, strin):
    #-- return integer form string
    #-- ex. return intger 8976 if string = "0123" where byte[0] = 0x01, byte[1] = 0x23 (value = 0x2310)
        #check if string is legal or not
        if strin=="" or len(strin)%2!=0:
            mstr="00"
            self.Print("/lib_vct/NVMECom Error: input string for function str2int() is not legal where string = %s"%strin, "f")
        else:
            mstr=strin
        mstr0="".join(map(str.__add__, mstr[-2::-2] ,mstr[-1::-2]))
        return int(mstr0, 16)
    class color:
        BLACK   = '\033[30m'
        RED     = '\033[31m'
        GREEN   = '\033[32m'
        YELLOW  = '\033[33m'
        BLUE    = '\033[34m'
        MAGENTA = '\033[35m'
        CYAN    = '\033[36m'
        WHITE   = '\033[37m'
        RESET = '\033[0m'
        
    StringStyle = {
            'fore':
            {   # 前景色
                'black'    : 30,   #  黑色
                'red'      : 31,   #  红色
                'green'    : 32,   #  绿色
                'yellow'   : 33,   #  黄色
                'blue'     : 34,   #  蓝色
                'purple'   : 35,   #  紫红色
                'cyan'     : 36,   #  青蓝色
                'white'    : 37,   #  白色
            },
     
            'back' :
            {   # 背景
                'black'     : 40,  #  黑色
                'red'       : 41,  #  红色
                'green'     : 42,  #  绿色
                'yellow'    : 43,  #  黄色
                'blue'      : 44,  #  蓝色
                'purple'    : 45,  #  紫红色
                'cyan'      : 46,  #  青蓝色
                'white'     : 47,  #  白色
            },
     
            'mode' :
            {   # 显示模式
                'mormal'    : 0,   #  终端默认设置
                'bold'      : 1,   #  高亮显示
                'underline' : 4,   #  使用下划线
                'blink'     : 5,   #  闪烁
                'invert'    : 7,   #  反白显示
                'hide'      : 8,   #  不可见
            },
     
            'default' :
            {
                'end' : 0,
            },
    }
    def UseStringStyle(self, string, mode = '', fore = '', back = '', Identation = 0):
     
        mode = '%s' % self.StringStyle['mode'][mode] if self.StringStyle['mode'].has_key(mode) else ''
        fore = '%s' % self.StringStyle['fore'][fore] if self.StringStyle['fore'].has_key(fore) else ''
        back = '%s' % self.StringStyle['back'][back] if self.StringStyle['back'].has_key(back) else ''
        style = ';'.join([s for s in [mode, fore, back] if s])
        style = '\033[%sm' % style if style else ''
        end = '\033[%sm' % self.StringStyle['default']['end'] if style else ''
        strIdent = ""
        strIdent += " "* Identation
        return '%s%s%s%s' % (strIdent, style, string, end)     
       
    class lbafds:
    # LBA Format Data Structure    
        ID   = 0
        MS     = 1
        LBADS   = 2
        RP  = 3
        
    def WriteLogFile(self, mStr, mfile="default"):
    # append new lines
    # mfile: "default"= default summary log file, "color"= summary color log, "cmd"= command log
        if mfile=="color":
            f = open(NVMECom.LogName_SummaryColor, "a")
        elif mfile=="cmd":
            f = open(NVMECom.LogName_CmdDetail, "a")            
        else:
            f = open(NVMECom.LogName_Summary, "a")       
        
        f.write(mStr)
        f.write("\n")        
        f.close()
        
    def ReadLogFile(self, mfile="default"):
    # append new lines
    # mfile: "default"= default log file, "color"= color log, "cmd"= command log
        if mfile=="color":
            f = open(NVMECom.LogName_SummaryColor, "r")
        elif mfile=="cmd":
            f = open(NVMECom.LogName_CmdDetail, "a")          
        else:
            f = open(NVMECom.LogName_Summary, "r")       
        
        mStr = f.read()    
        f.close()   
        return mStr     
        
    
    def Print(self, msg, Ctype="d"):
        # split by '/n' and print rows one by one
        MsgList = msg.split("\n")        
        for mMsg in MsgList:
            self.Print1Row(mMsg, Ctype)
    
    def Print1Row(self, msg, Ctype="d"):
        # Ctype, consol type
        # p/P: pass, print msg with green color
        # f/F: false, print msg with red color
        # w/W: warnning, print msg with yellow color
        # d/D: Default mode, print msg without color
        # t/T: test mode, will not print anything
                
        # consol
        mStr=""
        if Ctype=="p" or Ctype=="P":   
            mStr = self.UseStringStyle(msg, fore="green")
            #mStr =  self.color.GREEN +"%s" %(msg)  +self.color.RESET
        elif Ctype=="f" or Ctype=="F":  
            mStr = self.UseStringStyle(msg, fore="red")
        elif Ctype=="w" or Ctype=="W":   
            mStr = self.UseStringStyle(msg, fore="yellow")       
        elif Ctype=="t" or Ctype=="T":  
            if self.mTestModeOn:
                mStr = self.UseStringStyle(msg, fore="cyan")
        elif Ctype=="d" or Ctype=="D":  
            mStr = self.UseStringStyle(msg)
        elif Ctype=="u" or Ctype=="U":
            # underline
            mStr = self.UseStringStyle(msg, mode="underline")
        elif Ctype=="i" or Ctype=="I":
            # invert
            mStr = self.UseStringStyle(msg, mode="invert")
        elif Ctype=="b" or Ctype=="B":
            # bold
            mStr = self.UseStringStyle(msg, mode="bold")            
                        
        print self.PrefixString()+mStr 
        
            
    def PrefixString(self):
        # local time
        Ltime=time.strftime("%Y%m%d_%H:%M:%S", time.localtime())
        # duration
        StartT=self.StartLocalTime
        StopT=time.time()
        TimeDiv=time.strftime("%H:%M:%S", time.gmtime(int(StopT-StartT)))
        DT="DT: %s"%TimeDiv
        # case number
        Case="Case: %s"%self.SubCasePoint
        
        return Ltime+" "+DT+" "+Case+"| "
    
    def Logger(self, msg, mfile="default", color="No"):
        # color: define at self.color or no color       
        # mfile: select default log or color log file( default/color )
        
        if color=="No":
            mStr = msg
        else:
            mStr = color + msg  +self.color.RESET
        
        if mfile=="default":
            pass
        else:
            mStr=self.PrefixString()+mStr
        # writ to Log file    
        self.WriteLogFile(  mStr, mfile=mfile )
        
    def AddParserArgs(self, optionName, optionNameFull, helpMsg, argType):
        # after set AddParserArgs, using GetDynamicArgs to get arg if element exist, else return None
        # ex.  self.AddParserArgs(optionName="x", optionNameFull="disablepwr", helpMsg="disable poweroff", argType=int) 
        #        self.DisablePwr = self.GetDynamicArgs(0)
        self.ScriptParserArgs.append([optionName, optionNameFull, helpMsg, argType])
        
    def ParserArgv(self, argv, SubCaseList=""):
        # argv[1]: device path, ex, '/dev/nvme0n1'
        # argv[2]: subcases, ex, '1,4,5,7'
        # argv[3]: script test mode on, ex, '-t'
        # common arg define
        parser = ArgumentParser(description=SubCaseList, formatter_class=RawTextHelpFormatter)
        parser.add_argument("dev", help="device, e.g. /dev/nvme0n1", type=str)
        parser.add_argument("subcases", help="sub cases that will be tested, e.g. '1 2 3'", type=str, nargs='?')
        parser.add_argument("-t", "--t", help="script test mode on", action="store_true")
        parser.add_argument("-d", "--d", help="script doc", action="store_true")
        parser.add_argument("-s", "--s", help="test time in seconds", type=int, nargs='?')
        parser.add_argument("-p", "--p", help="log path that store logs", type=str, nargs='?')
        # script arg define new args if overwrite in script
        for mArg in self.ScriptParserArgs:
            optionName=mArg[0]
            optionNameFull=mArg[1]
            helpMsg=mArg[2]
            argType=mArg[3]
            parser.add_argument("-%s"%optionName, "--%s"%optionNameFull, help=helpMsg, type=argType, nargs='?')
        

        args = parser.parse_args(args=argv)
        
        mDev=args.dev
        mTestModeOn=True if args.t else False
        mScriptDoc=True if args.d else False
        if args.subcases==None:
            mSubItems=[]
        else:
            # split ',' and return int[]
            mSubItems = [int(x) for x in args.subcases.split(',')]     
            
        mTestTime=None if args.s==None else args.s
            
        mLogPath=None if args.logpath==None else args.logpath
        
        # parse script args, and return by order
        mScriptParserArgs=[]
        for mArg in self.ScriptParserArgs:
            optionName=mArg[0]
            optionNameFull=mArg[1]
            helpMsg=mArg[2]
            argType=mArg[3]            
            value=None if args.__dict__[optionNameFull]==None else args.__dict__[optionNameFull]
            mScriptParserArgs.append(value)
        
        return mDev, mSubItems, mTestModeOn, mScriptDoc, mTestTime, mLogPath, mScriptParserArgs
        
    def GetPCIERegBase(self):
        # System Bus (PCI Express) Registers base offset in int format
        PMCAP=0
        MSICAP=0
        MSIXCAP=0
        PXCAP=0
        AERCAP=0
        SR_IOVCAP=0
        buf=self.shell_cmd("lspci -vv -s %s" %(self.pcie_port))
        
        mStr="Capabilities: \[(.+?)\] Power Management"
        if re.search(mStr, buf):
            PMCAP=int(re.search(mStr, buf).group(1),16)
            
        mStr="Capabilities: \[(.+?)\] MSI"
        if re.search(mStr, buf):
            MSICAP=int(re.search(mStr, buf).group(1),16)
            
        mStr="Capabilities: \[(.+?)\] Express (.*) Endpoint"    #group(2) is v1, v2, or none etc.
        if re.search(mStr, buf):
            PXCAP=int(re.search(mStr, buf).group(1),16)                       
            
        mStr="Capabilities: \[(.+?)\] MSI-X"
        if re.search(mStr, buf):
            MSIXCAP=int(re.search(mStr, buf).group(1),16)
            
        mStr="Capabilities: \[(.+?) v(\d)\] Advanced Error Reporting"
        if re.search(mStr, buf):
            AERCAP=int(re.search(mStr, buf).group(1),16)        

        mStr="Capabilities: \[(.+?) v(\d)\] Single Root I/O Virtualization"
        if re.search(mStr, buf):
            SR_IOVCAP=int(re.search(mStr, buf).group(1),16)   
            
        return PMCAP, MSICAP, PXCAP, MSIXCAP, AERCAP,SR_IOVCAP

    def isfileExist(self, filePath):
        if os.path.exists(filePath):
            return True
        else:
            return False

    def rmFile(self, filePath):
        if os.path.exists(filePath):
            os.remove(filePath)
            
    def isCMDExist(self, cmd):
        CMD= "command -v %s 2>&1 >/dev/null ; echo $?"%cmd
        if self.shell_cmd(CMD)=="0":
            return True
        else:
            return False    
   
    def readBinaryFileToList(self, filePath):
        mList=[]
        with open(filePath, "rb") as f:
            byteStr = f.read(1)
            while byteStr != "":
                # Do stuff with byte.
                byte = struct.unpack('b', byteStr)[0]
                mList.append(byte)
                
                byteStr = f.read(1)
        return mList
    
    def writeBinaryFileFromList(self, filePath, mList):            
        f = open(filePath, 'w+b')
        byte_arr = mList
        binary_format = bytearray(byte_arr)
        f.write(binary_format)
        f.close()                

      
    def isFileTheSame(self, F0, F1):
        # if the same, return None, else return int list
        #mStr = self.shell_cmd("diff %s %s 1> /dev/null; echo $?"%(F0, F1))
        mRt=[]
        # Output the (decimal) byte numbers and (octal) values of all differing bytes
        CMDrt = self.shell_cmd("cmp -l %s %s"%(F0, F1))
        if CMDrt =="":
            return None
        else:            
            mStr="^(\d*)\s*(\d*)\s*(\d*)"
            mSearch=re.search(mStr, CMDrt)
            if mSearch:
                Offset =int(mSearch.group(1))
                ValueF0 =int(mSearch.group(2),8)
                ValueF1 =int(mSearch.group(3),8)
                return [Offset, ValueF0, ValueF1]
            else:
                return None
    
    def PrintProgressBar(self, iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = 'x'):
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
        mstr = '%s |%s| %s%% %s' % (prefix, bar, percent, suffix)
        #mstr = '\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix)
        sys.stdout.write(u"\033[1000D" + self.PrefixString()+mstr)
        sys.stdout.flush()    
        # Print New Line on Complete
        if iteration == total: 
            print ""

    def KMGT(self, size):
    # ex. KMGT(1024), return "1K"
        Size=float(size)
        SizeF=""
        if Size>=1024*1024*1024*1024:
            SizeF="%sT"%(Size/(1024*1024*1024*1024))
        elif Size>=1024*1024*1024:
            SizeF="%sG"%(Size/(1024*1024*1024))
        elif Size>=1024*1024:
            SizeF="%sM"%(Size/(1024*1024))
        elif Size>=1024:
            SizeF="%sK"%(Size/(1024))            
        return SizeF
    def KelvinToC(self, K):
        return (K-273)
    def CToKelvin(self, C):
        return (C+273)



    def int2bytes(self,value,NthByte):
        target = value
        n = NthByte # N th byte
        goal = 0xFF << (8 * n)
        return int((target & goal) >> (8 * n))       

    def IsControllerName(self, name):
    # check if is specific Controller by it's name
        find=self.shell_cmd("nvme list |grep %s |grep %s"%(self.device, name))
        if find=="":
            return False
        else:
            return True

    def ReadCSVFile(self, mFile):
    # return identifys in csv file
        l =  list()
        try:
            csvfile = open(mFile, 'rt')
            csvReader = csv.reader(csvfile, delimiter=",")
            for row in csvReader:
                l.append(row)            
        except:
            self.Print("File not found","f")
            return None
        return l        
    
    def InitFolder(self, path):       
        # if folder exist, remove it    
        if os.path.exists(path):
            self.RmFolder(path) 
        # Create folder
        if not os.path.exists(path):
            os.makedirs(path)
            
    def RmFolder(self, path): 
        if os.path.exists(path):
            shutil.rmtree(path)
            
             


    def SMIScriptSubProcess(self, pyPath):
        scriptPath=pyPath[0:pyPath.find("/")]
        scriptName=pyPath[pyPath.find("/")+1:]        
        p = subprocess.Popen("cd %s; python %s /dev/nvme0n1"%(scriptPath, scriptName), stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True)           
        while p.poll() is None:
            sleep(0.5)
        retcode = p.returncode
        return retcode
        
    def RunSMIScript(self, scriptPath=None, scriptName=None, DevAndArgs="/dev/nvme0n1", LogPath="Log/SubLog/" ):
        # scriptPath:             ex. 'SMI_SubProcess/'
        # scriptName:             ex. 'SMI_Read.py'
        # DevAndArgs:    ex. '/dev/nvme0n1' for all subcase or '/dev/nvme0n1 1,3,4' for subcase1,3,4
        # LogPath:            log path that store logs
        # return retcode and fail case number[]
        
        FailCaseNum = []
        # format paths
        if scriptPath!=None:
            scriptPath='%s/'%scriptPath if scriptPath[-1]!='/' else scriptPath # add / if forgot to add /
            scriptPath=scriptPath[1:] if scriptPath[0]=='/' else scriptPath # remove / if first char is /        
            fullPath = scriptPath+scriptName
        else:
            fullPath=scriptName
            
        LogPath='%s/'%LogPath if LogPath[-1]!='/' else LogPath # add / if forgot to add /
        LogPath=LogPath[1:] if LogPath[0]=='/' else LogPath # remove / if first char is /        
                     
            
        # check if  python file exist or not
        if not self.shell_cmd("find %s 2> /dev/null |grep %s " %(fullPath,fullPath)):
            self.Print("Error at func RunSMIScript, no such file: %s"%fullPath, "f")
            return -1
          
        # set log files path
        DevAndArgs= DevAndArgs + " --p %s"%LogPath
        # set log summary path           
        logPathWithUniversalCharacter=LogPath+"summary_color_*.log"
                
        # if scriptPath, add cd to the directory
        CMD ="cd %s;"%scriptPath if scriptPath!=None else ""
        CMD = CMD + "python %s %s "%(fullPath, DevAndArgs)

        # start thread
        p = subprocess.Popen(CMD, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True)           
        cnt=0 
        # get log if any subcase finish, and print it to console while thread is ongoing
        while True:
            # if file exist    
            logPath=self.shell_cmd("find %s 2> /dev/null |grep %s " %(logPathWithUniversalCharacter,logPathWithUniversalCharacter))
            if logPath: 
                # print new line
                if self.isfileExist(logPath):            
                    count = len(open(logPath).readlines(  ))
                    if count>cnt:
                        for ptr in range(cnt, count):
                            linecache.clearcache()
                            line = linecache.getline(logPath, ptr+1)
                            # if fail, find case number
                            if re.search("CASE (\d+).*: Fail", line):                    
                                FailCase = re.search("CASE (\d+)", line).group(1)
                                FailCaseNum.append(FailCase)                                                 
                            sys.stdout.write(line)
                        cnt = count          
            if p.poll() is not None:
                break
            sleep(0.5)
        retcode = p.returncode
        return retcode, FailCaseNum

    def PrintSMIScriptConsoleOutput(self, LogPath="Log/SubLog/", SubCase=1 ):
        # after call RunSMIScript, can call PrintSMIScriptConsoleOutput for specific testcase console output
        # where LogPath = LogPath for PrintSMIScriptConsoleOutput and RunSMIScript
        
        # format paths            
        LogPath='%s/'%LogPath if LogPath[-1]!='/' else LogPath # add / if forgot to add /
        LogPath=LogPath[1:] if LogPath[0]=='/' else LogPath # remove / if first char is /        
                               
        # set log console path           
        logPathConsole=LogPath+"console_out_*.log"
                
        # if scriptPath, add cd to the directory
        logPath=self.shell_cmd("find %s 2> /dev/null |grep %s " %(logPathConsole,logPathConsole))
        # find  'Case: 1| ..................... to the end'
        mStr = "^.*(Case: %s\|.*$)"%SubCase
        if not logPath:
            self.Print("Can't file log file: %s"%logPath)
        else:
            f = open(logPath)
            while True:                
                line =f.readline()
                if not line:
                    break
                else:
                    if re.search(mStr, line):                    
                        caseOut = re.search(mStr, line).group(1) 
                        self.Print(caseOut)

    def isMainThreadAlive(self):        
        for i in threading.enumerate():
            if i.name == "MainThread":
                return True
        return False            
            
#== end NVMECom =================================================

class timer_():

    def __init__(self):
        self.time=0
        self._StartT=0
        self._StopT=0
    def start(self):
        self._StartT=time.time()
    def stop(self):
        self._StopT=time.time()  
        self.time=format(self._StopT - self._StartT, '.6f')




class LBARangeDataStructure_():
# usage
# mNVME.LBARangeDataStructure.Type=0x2
# mNVME.LBARangeDataStructure.Attributes=0x1
# mNVME.LBARangeDataStructure.SLBA=0x5432
# mNVME.LBARangeDataStructure.NLB=7
# mNVME.LBARangeDataStructure.CreatePattern()
# print mNVME.LBARangeDataStructure.Pattern
    def __init__(self, obj):
        self._mNVME=obj
        self.Type = 0
        self.Attributes = 0
        self.SLBA = 0
        self.NLB = 0
        self.GUID = 0
        self.Pattern = ""        

    
    def _CreateZeroPattern(self, cnt):
        mStr=""
        for i in range(cnt):
            mStr = mStr + self._FormatByte(0)
        return mStr
    
    def _FormatByte(self, value):
        #return "\\\\" + str(value).zfill(3)
        return "\\\\" +"x" + str(hex(value)[2:])

    def CreatePattern(self):
        # byte 0, Type
        Pat = self._FormatByte(self.Type)
        
        # byte 1,Attributes
        Pat = Pat + self._FormatByte(self.Attributes)
        
        # byte 2~15,Reserved
        Pat = Pat + self._CreateZeroPattern(14)
        
        # byte 16~23,SLBA
        for i in range(8):
            Pat = Pat +self._FormatByte(self._mNVME.int2bytes(self.SLBA,i))

        # byte 24~31,NLB
        for i in range(8):
            Pat = Pat +self._FormatByte(self._mNVME.int2bytes(self.NLB,i))   

        # byte 32~47,GUID
        for i in range(16):
            Pat = Pat + self._FormatByte(self._mNVME.int2bytes(self.GUID,i))     
              
        # byte 48~63,Reserved
        Pat = Pat + self._CreateZeroPattern(16)
        
        self.Pattern=Pat
        
