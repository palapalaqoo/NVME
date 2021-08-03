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
import ConfigParser
import StringIO

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
    LogName_Id=0    # start from 0
    ScriptParserArgs=[]  
    LastProgress=None
    ''' for self.Print()
        self.Print() will print self.PrefixString() + PrintOffset + mMsg
    '''
    PrintLoop = None # Loop that will be shown in PrefixString() if PrintLoop != None, "Loop: %s"%self.PrintLoop
    PrintOffset = ""     # using SetPrintOffset(self, offset) to set self.PrintOffsetValue to generate spaces, ex. self.PrintOffsetValue=2, PrintOffset='  '
    PrintOffsetValue = 0 #
    
    def SubItemNum(self):
        self.SubItemNumValue+=1
        return self.SubItemNumValue
    
    def UsingCurrentLogFile(self):
        # try to find all logfiles in /Log/
        # self.LogPath default ='Log/'
        self.LogPath='%s/'%self.LogPath if self.LogPath[-1]!='/' else self.LogPath # add / if forgot to add /
        self.LogPath=self.LogPath[1:] if self.LogPath[0]=='/' else self.LogPath # remove / if first char is /
        
        mStr = self.shell_cmd("ls %s 2> /dev/null |grep summary_regress "%self.LogPath)
        if(mStr ==""):
            self.InitLogFile()
            return False
        else:
            NVMECom.LogName_Summary =  self.LogPath + mStr
            
        mStr = self.shell_cmd("ls %s|grep summary_color"%self.LogPath)
        if(mStr ==""):
            self.InitLogFile()
            return False
        else:
            NVMECom.LogName_SummaryColor =  self.LogPath + mStr
            
        mStr = self.shell_cmd("ls %s|grep detail_cmd"%self.LogPath)
        if(mStr ==""):
            self.InitLogFile()
            return False
        else:
            NVMECom.LogName_CmdDetail =  self.LogPath + mStr
            NVMECom.LogName_CmdDetail += "_%s"%NVMECom.LogName_Id # with id
            
        mStr = self.shell_cmd("ls %s|grep console_out"%self.LogPath)
        if(mStr ==""):
            self.InitLogFile()
            return False
        else:
            NVMECom.LogName_ConsoleOut =  self.LogPath + mStr     
            NVMECom.LogName_ConsoleOut += "_%s"%NVMECom.LogName_Id # with id
        
    def SplitLog(self):
    # LogName_Id +=1, and split CmdDetail, ConsoleOut
        NVMECom.LogName_Id +=1
        NVMECom.LogName_CmdDetail = self.LogPath + "detail_cmd"+ "_%s"%NVMECom.LogName_Id +".log"
        NVMECom.LogName_ConsoleOut = self.LogPath + "console_out"+ "_%s"%NVMECom.LogName_Id +".log"
        
        # redirect stdout to LogName_ConsoleOut
        sys.stdout.close()
        sys.stdout = NVMECom.tee(NVMECom.LogName_ConsoleOut)
                    
    def InitLogFile(self):
        # self.LogPath default ='Log/'
        self.LogPath='%s/'%self.LogPath if self.LogPath[-1]!='/' else self.LogPath # add / if forgot to add /
        self.LogPath=self.LogPath[1:] if self.LogPath[0]=='/' else self.LogPath # remove / if first char is /         
        
        # remove all dir
        if os.path.exists(self.LogPath):
            shutil.rmtree(self.LogPath) 
        # Create dir
        if not os.path.exists(self.LogPath):
            os.makedirs(self.LogPath)
        #create log
        # NVMECom.LogName_Summary =  self.LogPath + "summary_regress_"+time.strftime('%Y_%m_%d_%Hh%Mm%Ss')+".log"
        NVMECom.LogName_Summary =  self.LogPath + "summary_regress"+".log"
        f = open(NVMECom.LogName_Summary, "w")
        f.close()
        #create color log
        NVMECom.LogName_SummaryColor = self.LogPath + "summary_color"+".log"
        f = open(NVMECom.LogName_SummaryColor, "w")
        f.close()    
        #create command log for save all host command that issue to the controller 
        NVMECom.LogName_CmdDetail =  self.LogPath + "detail_cmd" + "_%s"%NVMECom.LogName_Id +".log"
        f = open(NVMECom.LogName_CmdDetail, "w")
        f.close() 
        #create command log for save all console output
        NVMECom.LogName_ConsoleOut =  self.LogPath + "console_out"+ "_%s"%NVMECom.LogName_Id +".log"
        f = open(NVMECom.LogName_ConsoleOut, "w")
        f.close()     

        f.close() 
        #create readme file
        NVMECom.LogName_Readme =  self.LogPath + "readme.txt"
        f = open(NVMECom.LogName_Readme, "w") 
        mStr ="summary_regress_xxx:        summary for regression tool \n" + \
                    "summary_color_xxx:    color summary log \n" + \
                    "detail_cmd_xxx:        all the commands issued in this test \n" + \
                    "console_out_xxx:    color console output  \n" + \
                    "%s:    last smart check output(if avaliable)  \n"%(self._NVME.SmartCheck.pathLog) + \
                    "%s:    smart check history(if avaliable) \n"%(self._NVME.SmartCheck.historyLogDir)
        f.write(mStr)
        f.write("\n")        
        f.close()        
    
    def FlushConsoleMsg(self):
    # flush all console messages to log file
        sys.stdout.flush()
        #sleep(1)
        
    class tee(object):
    # if need to flush all console messages to log, below syntax will call NVMECom.tee.flush()  to do it
    # if need to roll back, using close()
    # sys.stdout.flush()
        def __init__(self, logFile):
            self.terminal = sys.stdout
            self.mLogFile=logFile
            self.log = open(self.mLogFile, "a")
            # handle progress bar
            self.isProgress = False
            self.ProgressMsg=None
           
        
        def write(self, message):
            self.terminal.write(message)
            
            if self.isProgress:
                pass
            else:
                # if last write is progress bar and it is finished, then print to log file
                if self.ProgressMsg!=None:
                    self.log.write(self.ProgressMsg)  
                    self.log.write("\n")
                    self.ProgressMsg=None
                # print current message to log file
                self.log.write(message)  
                
        
        def flush(self):
                #this flush method is needed for python 3 compatibility.
                #this handles the flush command by doing nothing.
                #you might want to specify some extra behavior here.
            self.terminal.flush()
            self.log.flush()
            #self.log.close()
            #self.log = open(self.mLogFile, "a")
            
        def close(self):
        # flush then roll back to original stdout
            self.flush()
            sys.stdout = self.terminal
             
        
       
            
    def __init__(self, son):        
        self._NVME = son
        # set NVMECom parameters from subclass
        self.device=son.dev
        self.device_port=son.dev[0:son.dev.find("nvme")+5]
        self.mTestModeOn=son.TestModeOn
        self.StartLocalTime=son.StartLocalTime
        self.SubCasePoint=son.SubCasePoint
        self.LogPath=son.LogPath if  son.LogPath!=None else  'Log/'  # default = 'Log/'
        self.LogPath='%s/'%self.LogPath if self.LogPath[-1]!='/' else self.LogPath # add / if forgot to add /
        self.LogPath=self.LogPath[1:] if self.LogPath[0]=='/' else self.LogPath # remove / if first char is /
        
        # if object is created in subcase of main script, and not reboot test, then do not init log files
        if not son.isSubCaseOBJ and son.ResumeSubCase==None:
            self.InitLogFile()
        else:
            self.UsingCurrentLogFile()
        #self.InitLogFile() if not son.isSubCaseOBJ else None
        self.LastCmd="None"
        self.LBARangeDataStructure=LBARangeDataStructure_(self)
        self.timer=timer_()
        self.timeEventTerminate = False
        
    def threadTimeEvent(self, seconds, eventFunc = None, printProgressBar = False, printProgressBarPeriod = 0.5):
    # ex. self.threadTimeEvent(seconds=10, eventFunc = myFunc, printProgressBar = True, printProgressBarPeriod = 0.5):
    # seconds: timer in seconds
    # eventFunc: when time is up, run eventFunc()
    # printProgressBar: if True, show timer ProgressBar every printProgressBarPeriod second
    # can Terminate thread using 'self.timeEventTerminate = True'
        self.timeEventTerminate = False
        self.timer.start("float")
        secondsInUs = seconds*1000000 #seconds in microsceonds
        printProgressBarPeriodInUs = printProgressBarPeriod*1000000 #seconds in microsceonds
        printProgressTimeGap = 0
        while True:
            CurrTime = self.timer.time # CurrTime is 6 decimal points
            CurrTimeInUs = CurrTime*1000000 #seconds in microsceonds
            
            # time up, show 100% progress bar
            if CurrTimeInUs > secondsInUs:     
                self.PrintProgressBar(secondsInUs, secondsInUs, suffix = "Time: %s s / %s s"%(seconds, seconds), length = 40)             
                break 
            
            # if timeEventTerminate
            if self.timeEventTerminate:
                self.timeEventTerminate = False
                break
                
            # if printProgressBar
            if printProgressBar and CurrTimeInUs > printProgressTimeGap:
                printProgressTimeGap = printProgressTimeGap + printProgressBarPeriodInUs
                self.PrintProgressBar(CurrTimeInUs, secondsInUs, suffix = "Time: %s s / %s s"%(CurrTime, seconds), length = 40)                
            
        if eventFunc != None and not self.timeEventTerminate:
            eventFunc()
            
              
    def timeEvent(self, seconds, eventFunc = None, printProgressBar = False):  
    # seconds: timer in seconds
    # eventFunc: when time is up, run eventFunc()
    # printProgressBar: if True, show timer ProgressBar every 1 second
    # can Terminate thread using 'self.timeEventTerminate = True'
        self.timeEventTerminate = False
        t = threading.Thread(target = self.threadTimeEvent, args=(seconds, eventFunc, printProgressBar,))
        #t.daemon = True # The entire Python program exits when no alive non-daemon threads are left.
        t.start()
        return t 
            
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
        
    def getLsDev(self):
    # get ls -l for /dev/nvme0n1
        LsDev=""
        CMD = "ls -l %s* | grep %s"%(self._NVME.dev_port, self._NVME.dev) # ls -l /dev/nvme0* |grep /dev/nvme0n1
        # ex. brw-rw----. 1 root disk 259, 0 Sep  9 12:57 /dev/nvme0n1, get brw-rw----. 1 root disk 259
        # ex. -rw-r--r--. 1 root root      0 Sep  9 14:56 /dev/nvme0n1, here is fail pattern that will return all fail pattern
        mStr="(.+)," 
        rtStr = self.shell_cmd(CMD)
        if re.search(mStr, rtStr):
            LsDev = re.search(mStr, rtStr).group(1)  
        else:
            LsDev = rtStr

        return LsDev
            
    def yield_shell_cmd(self, cmd):
        # like shell_cmd(), but it will yield new line
        #---------------------------------------------------------------------------------------
        # usage: issue FIO command and get console output one by on
        # EX.
        #    CMD = "fio --direct=1 --iodepth=1 --ioengine=libaio --bs=512 --rw=write --numjobs=1 --size=100M --offset=0 --filename=/dev/nvme0n1 --name=mdata"
        #    for line in self.yield_shell_cmd(CMD):
        #        self.Print( line)
        #---------------------------------------------------------------------------------------        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, universal_newlines=True)                        
        while True:
            line = process.stdout.readline().rstrip()
            if not line:
                break
            yield line
            
            # check if main thread is stop
            for i in threading.enumerate():
                if i.name == "MainThread":
                    # print i.is_alive() 
                    if not i.is_alive(): process.kill()
                             
        # get return status    
        out, err = process.communicate()
        yield out  
            
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
    def get_log(self, log_id, size, StartByte=-1, StopByte=-1, NVMEobj=None, Offset=0):
    #-- return string byte[0]+byte[1]+byte[2]+ ...
    #-- ex. return string "0123" where byte[0] = 0x01, byte[1] = 0x23
    #-- size, size in bytes
        self.device = NVMEobj.device if NVMEobj!= None else self.device
        if (StartByte==-1 and StopByte==-1):
            return  self.shell_cmd(" nvme get-log %s --log-id=%s --log-len=%s -b -o %s 2>&1"\
                                   "|xxd -ps |cut -d ':' -f 2|tr '\n' ' '|sed 's/[^0-9a-zA-Z]*//g'" %(self.device, log_id, size, Offset))
        else:
            mStr=self.shell_cmd(" nvme get-log %s --log-id=%s --log-len=%s -b -o %s  2>&1"\
                                "|xxd -ps |cut -d ':' -f 2|tr '\n' ' '|sed 's/[^0-9a-zA-Z]*//g'" %(self.device, log_id, size, Offset))
            return mStr[StartByte*2:(StopByte+1)*2]


    def get_log2byte(self, log_id, size, offset=0):
    #-- return list [ byte[0], byte[1], byte[2], ... ]
    #-- size, size in bytes
    #-- usage: mStr=get_log2byte(7, 512)=[01, 23, 45, 67, 89]
    #-- mStr[0]='01' , mStr[1]='23'  
        line = self.get_log(log_id=log_id, size=size, Offset=offset)
        n=2
        return [line[i:i+n] for i in range(0, len(line), n)]       
    
    def get_log_passthru(self, LID, size, RAE=0, LSP=0, LPO=0, ReturnType=0, BytesOfElement=1, NVMEobj=None, LSI=0):
    #-- return list [ byte[0], byte[1], byte[2], ... ] if ReturnType=0, ex, byte[0]=0x89, byte[1]=0xab, return ["89", "ab"]
    #-- return list [ byte[0], byte[1], byte[2], ... ] if ReturnType=2, ex, byte[0]=0x89, byte[1]=0xab, return [0x89, 0xab]
    #-- BytesOfElement, cut BytesOfElement to lists, ex. BytesOfElement=2,  return list [ byte[1]+byte[0], byte[3]+byte[2], ... ] ,if ReturnType=0
    #-- return string byte[0] + byte[1] + byte[2] + ...  if ReturnType=1   
    #-- size, size in bytes
    #-- usage: mStr=get_log_passthru(7, 512, rae, lsp, lpo)=[01, 23, 45, 67, 89]
    #-- mStr[0]='01' , mStr[1]='23'  
    #--RAE: Retain Asynchronous Event
    #--LSP: Log Specific Field
    #--LPO: Log Page Offset in byte
    #--LSI: Log Specific Identifier in cdw11[31:16]
        NUMDL=int(size/4-1) & 0xFFFF
        NUMDU=int(size/4-1) >>16
        CDW11 = NUMDU+LSI<<16
        CDW10_int= (NUMDL<<16) + (RAE<<15) + (LSP <<8) + LID
        CDW10= '0x{:02x}'.format(CDW10_int)
        
        LPOL=LPO & 0xFFFFFFFF
        LPOU= LPO >> 32
        
        #cmd="nvme admin-passthru %s --opcode=0x2 -r --cdw10=0x007F0008 -l 512 2>&1 "%mNVME.dev
        self.device = NVMEobj.device if NVMEobj!= None else self.device
        cmd="nvme admin-passthru %s --opcode=0x2 -r --cdw10=%s --cdw11=%s --cdw12=%s --cdw13=%s -l %s 2>&1 "\
        %(self.device, CDW10, CDW11, LPOL, LPOU, size)
        mbuf, sc=self.shell_cmd_with_sc(cmd)
        if sc!=0: # cmd fail
            return None
        else:
            return self.AdminCMDDataStrucToListOrString(mbuf,ReturnType, BytesOfElement)

    def GetPCIe4096ByteRegister(self):
    #-- return list [ byte[0], byte[1], byte[2], ... ]
        strIn=self.shell_cmd("lspci -xxxx -s %s" %(self.pcie_port))
        
        patten=re.findall("\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}", strIn)            
        patten1= ''.join(patten)  
        line=patten1.replace(" ", "")  
        # put patten in to list type
        n=2
        listBuf= [line[i:i+n] for i in range(0, len(line), n)] 
        # to int
        listBuf = [int(i, 16) for i in listBuf]        
            
        return listBuf
    
    def GetPCIeCapIDlist(self):
    # return list,  [[CapID 0, offset], [CapID 1, offset] ..]
    # and byte list, raw data
        mList = []
        data = self.GetPCIe4096ByteRegister()
        if len(data)!=4096:
            self.Print("Error!, size of GetPCIe4096ByteRegister() != 4096, curr = %s"%len(data))
        CapabilitiesPointer = data[0x34] # pcie spec
        ptr = CapabilitiesPointer # start from CapabilitiesPointer        
        while True:
            CapID = data[ptr]
            mList.append([CapID, ptr])
            NextCapabilityPointer = data[ptr+1]
            if NextCapabilityPointer==0:
                break
            else:
                ptr = NextCapabilityPointer
                
        return mList, data
            
   
            
    def AdminCMDDataStrucToListOrString(self, strIn, ReturnType=0, BytesOfElement=1):
    # input admin-passthru command Returned Data Structure, not that command must have '2>&1' to check if command success or not
    # output list or string
    #-- return list [ byte[0], byte[1], byte[2], ... ] if ReturnType=0 where byte[] is string type
    #-- return string byte[0] + byte[1] + byte[2] + ...  if ReturnType=1 where byte[] is string type   
    #-- return list [ byte[0], byte[1], byte[2], ... ] if ReturnType=2 where byte[] is int type  
    #-- BytesOfElement, cut BytesOfElement to lists, ex. BytesOfElement=2,  return list [ byte[1]+byte[0], byte[3]+byte[2], ... ] 
        # if command success
        if re.search("NVMe command result:00000000", strIn):
            line="0"        
            #patten=re.findall("\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}", strIn)            
            patten=re.findall("\w+:(.+) \".+\"", strIn) # 0050: 32 36 35 4b 48 20 20 20 20 20 20 20 20 20 20 20 "265KH..........."
            patten1= ''.join(patten)
            line=patten1.replace(" ", "")    
            if ReturnType==0 or ReturnType==2:
                # return list
                # put patten in to list type
                n=2
                listBuf= [line[i:i+n] for i in range(0, len(line), n)] 
                
                # set bytes of element, ex. [0, 1, 2, 3, 4..] , BytesOfElement= 3, -> [210, 543, 876..]
                if BytesOfElement!=1:
                    n=BytesOfElement                    
                    listBuf=["".join(list(reversed(listBuf[i:i+n]))) for i in range(0, len(listBuf), n)]
                    
                if ReturnType==2:
                    listBuf = [int(i, 16) for i in listBuf]
                    
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
                'overline'  : 53, # 使用overline划线
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
        
    
    def SetPrintOffset(self, offset, mode="normal"):     
    # normal: will set to offset 
    # add: will add offset permanently in subcase, i.e. set to self.GetPrintOffset()+offset  
        self.PrintOffset = ""
        if mode=="normal":
            self.PrintOffsetValue = offset
        elif mode=="add":
            self.PrintOffsetValue = self.GetPrintOffset()+offset
            self.PrintOffsetValue = 0 if self.PrintOffsetValue<0 else self.PrintOffsetValue
        else:
            return False
                    
        for i in range(self.PrintOffsetValue):
            self.PrintOffset = self.PrintOffset + " "
        return True
    def GetPrintOffset(self):   
        return self.PrintOffsetValue
    
    def Print(self, msg, Ctype="d", offsetR=None):
        # offsetR: relatively offset
        # split by '/n' and add PrintOffset then, print rows one by one
        MsgList = msg.split("\n")
        if offsetR!=None: # set offset
            offsetBK = self.GetPrintOffset()
            self.SetPrintOffset(offsetBK + offsetR)
                
        for mMsg in MsgList:
            mMsg = self.PrintOffset + mMsg
            self.Print1Row(mMsg, Ctype)
            
        if offsetR!=None: # clear offset
            self.SetPrintOffset(offsetBK)    
                
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
        # Loop, or any prefix string
        Loop = ""
        if self.PrintLoop!=None:
            if type(self.PrintLoop)==int:
                Loop = "Loop: %s"%self.PrintLoop
                if self.PrintLoop%2==0:
                    Loop = self.UseStringStyle(Loop, fore="white", back="black")
            if type(self.PrintLoop)==str:
                Loop = self.PrintLoop
                Loop = self.UseStringStyle(Loop, fore="white", back="black")
        
        return Ltime+" "+DT+" "+Case +" " +Loop+"| "
    
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
        
    def SetDynamicArgs(self, optionName, optionNameFull, helpMsg, argType, default=None,\
                        iniFileName=None, iniSectionName=None, iniOptionName=None):
        # after SetDynamicArgs, using GetDynamicArgs to get arg if element exist, else return None
        # ex.  self.AddParserArgs(optionName="x", optionNameFull="disablepwr", helpMsg="disable poweroff", argType=int) 
        #        self.DisablePwr = self.GetDynamicArgs(0)
        # default value priority is iniFileName>default
        
        # if iniFileName!=None, using ini file to set default value and show in helpMsg
        # else show default in helpMsg if defalut is not None
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
        else:
            if default!=None: helpMsg += "\n%s"%self.HighLightRed("Default: %s"%(default))
                                 
            
                     
        # set ScriptParserArgs
        helpMsg += "\n "
        self.ScriptParserArgs.append([optionName, optionNameFull, helpMsg, argType, default])
    def GetDynamicArgs(self, select):
    # after SetDynamicArgs, using GetDynamicArgs to get arg if element exist, else return None
    # len(self.ScriptParserArgs) = len(self.DynamicArgs)
        value = None
        if select<len(self.DynamicArgs):
            value = self.DynamicArgs[select]
        return value      
        
    def ParserArgv(self, argv, SubCaseList=""):
        # argv[1]: device path, ex, '/dev/nvme0n1'
        # argv[2]: subcases, ex, '1,4,5,7'
        # argv[3]: script test mode on, ex, '-t'
        # common arg define
        parser = ArgumentParser(description=SubCaseList, formatter_class=RawTextHelpFormatter)
        parser.add_argument("dev", help="device, e.g. /dev/nvme0n1", type=str)
        parser.add_argument("subcases", help="sub cases that will be tested, e.g. '1 2 3'", type=str, nargs='?')
        parser.add_argument("-t", "--t", help="script test mode on", action="store_true")
        parser.add_argument("-d", "--d", help="print script doc and flow if acceptable", action="store_true")        
        parser.add_argument("-s", "--s", help="test time in seconds", type=int, nargs='?')
        parser.add_argument("-p", "--p", help="log path that store logs, default='.\Log', ex. '-p \'/Log/SubCase\''", type=str, nargs='?')
        parser.add_argument("-r", "--r", help="reboot parameters, please do not set it\n ", type=int, nargs='?')
        parser.add_argument("-iknowwhatiamdoing", "--iknowwhatiamdoing", help="Warring!!, use option 'iknowwhatiamdoing' if applicable", action="store_true")
        #parser.add_argument("-checksmart", "--checksmart", help="check smart log using SMART.ini and SmartCheck module, e.x. '-checksmart'", action="store_true")
        
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
        mTestModeOn=True if args.t else False                
        mScriptDoc=True if args.d else False
        mIknowwhatiamdoing=True if args.iknowwhatiamdoing else False
        if args.subcases==None:
            mSubItems=[]
        else:
            # split ',' and return int[]
            mSubItems = [int(x) for x in args.subcases.split(',')]     
            
        mTestTime=None if args.s==None else args.s            
        mLogPath=None if args.p==None else args.p
        mRebootP=None if args.r==None else int(args.r)
        
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
        
        return mDev, mSubItems, mTestModeOn, mScriptDoc, mTestTime, mLogPath, mScriptParserArgs, mRebootP, mIknowwhatiamdoing#, mCheckSmart
        
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

    def read1ByteFromFile(self, filename, offset):
        byte = 0
        success = False
        with open(filename, "rb") as infile:  # rb = read binary
            infile.seek(offset, 0)           # 0 = start of file, optional in this case, offset in byte
            byteStr = infile.read(0x1)
            if byteStr != "":
                byte = struct.unpack('b', byteStr)[0]      
                success = True
        if not success:
            self.Print( "read file fail, filename = %s, offset = %s"%(filename, offset), "f") 
        return byte 
    
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
        mStr = self.PrefixString()+self.PrintOffset+mstr
        mStr = mStr[:int(columns)-1]
        
        sys.stdout.isProgress=True
        sys.stdout.write(u"\u001b[s") # saves the current cursor position
        sys.stdout.write(u"\033[0J") # clear all string after courser
        sys.stdout.write(mStr) # write
        sys.stdout.ProgressMsg=mStr # save to ProgressMsg for save to log file after progress is finished 
        sys.stdout.flush() 
        sys.stdout.write(u"\u001b[u") # restores the cursor to the last saved position
        sys.stdout.isProgress=False     
        # Print New Line on Complete

        if iteration == total: 
            print "\r"


    def KMGT(self, size):
    # ex. KMGT(1024), return "1K"
        Size=float(size)
        SizeF="%s"%size
        if Size>=1024*1024*1024*1024:
            SizeF="%sT"%(Size/(1024*1024*1024*1024))
        elif Size>=1024*1024*1024:
            SizeF="%sG"%(Size/(1024*1024*1024))
        elif Size>=1024*1024:
            SizeF="%sM"%(Size/(1024*1024))
        elif Size>=1024:
            SizeF="%sK"%(Size/(1024))            
        return SizeF
    
    def KMGT_reverse(self, size, sectorSize=512):
    # convert string to number of blocks
    # ex. KMGT_reverse(4k), return 8 if sectorSize=512, return 1 if sectorSize=4096,
    #  KMGT_reverse(2), return int 0
        size= size.upper()
        
        value = size
        unit=1
        mStr = "(.*)K"        
        if re.search(mStr, size): 
            value = re.search(mStr, size).group(1)
            unit=1024
        mStr = "(.*)M"        
        if re.search(mStr, size): 
            value = re.search(mStr, size).group(1)
            unit=1024*1024
        mStr = "(.*)G"        
        if re.search(mStr, size): 
            value = re.search(mStr, size).group(1)
            unit=1024*1024*1024         
    
        value=float(value)
        # ex. 0-> 0, 1-> 1, 2-> 1 ....  512-> 1, 513 -> 2
        if (value*unit)%sectorSize!=0:
            value=int(value*unit/sectorSize)
            value=value+1
        else:
            value=int(value*unit/sectorSize)
            
        return value    
    
    def KelvinToC(self, K):
        return (K-273)
    def CToKelvin(self, C):
        return (C+273)



    def int2bytes(self,value,NthByte):
        target = value
        n = NthByte # N th byte
        goal = 0xFF << (8 * n)
        return int((target & goal) >> (8 * n))       
    
    def byte2List(self, byteIn):
        byteIn
        mList=[]
        mList.append(1 if byteIn&(1<<0) >0 else 0)
        mList.append(1 if byteIn&(1<<1) >0 else 0)
        mList.append(1 if byteIn&(1<<2) >0 else 0)
        mList.append(1 if byteIn&(1<<3) >0 else 0)
        mList.append(1 if byteIn&(1<<4) >0 else 0)
        mList.append(1 if byteIn&(1<<5) >0 else 0)
        mList.append(1 if byteIn&(1<<6) >0 else 0)
        mList.append(1 if byteIn&(1<<7) >0 else 0)    
        return mList

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
    
    def WriteCSVFile(self, fileNameFullPath, mData): 
    # if need to clear file, use self.rmFile()
    # fileNameFullPath: ex. './CSV/Out/mOut.csv'
    # mData: list type, ex. [name, value]
        # If ./CSV not exist, Create it
        if not os.path.exists("./CSV"):
            os.makedirs("./CSV")        
        # If ./CSV/In not exist, Create it
        if not os.path.exists("./CSV/In"):
            os.makedirs("./CSV/In")
        # If ./CSV/Out not exist, Create it       
        if not os.path.exists("./CSV/Out"):
            os.makedirs("./CSV/Out")  
            
        # if file not exist, then create it
        if not os.path.exists(fileNameFullPath):
            f = open(fileNameFullPath, "w")
            f.close()            
        
        # write
        with open(fileNameFullPath, 'a') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(mData)  
    
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
        # scriptPath:             ex. 'SMI_SubProcess/' or None(current dir)
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
        DevAndArgs= DevAndArgs + " --p=%s"%LogPath
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
            
          

    class FIOcmdWithPyPlot_():
        lock=threading.Lock() 
        Msg=[]
        def __init__(self,obj):
            self.OBJ=obj
            self.Msg = []   
            self.killProcess  = False
            self.mNVME = obj

        def RunFIOcmdWithConsoleOutAndPyplot(self, CMDlist, maxPlot = 100, printInfo=False):
        # maxPlot: number of plots that will be drawn
        # printInfo: print fio console output
        # return average bw list in Mib/s for every command
            #init averageBwList
            averageBwList= [0]*len(CMDlist) 
            doLastParseMsg=False             
            #   using pyplot      
            import matplotlib.pyplot as plt      
            plt.ion()
            fig = plt.figure()                
            # thread id start form 0
            idThread=0  
            devName=[]
            fioRW=[]
            timeList = []
            bwList = []
            mThreads = []
            axList=[]
            # init thread to issue cmd and pull msg out
            for CMD in CMDlist:           
                # parse CMD to get device name
                if re.search("dev\/(\w*)", CMD):
                    mStr=re.search("dev\/(\w*)", CMD).group(1)
                    devName.append(mStr)  
                    
                # parse CMD to check if is read or write        
                if re.search("--rw=(\w*)", CMD):
                    mStr=re.search("--rw=(\w*)", CMD).group(1)
                    fioRW.append(mStr)
                else:
                    self.Print("Error!, func RunFIOcmdWithConsoleOutAndPyplot, FIO command can't find --rw=(\w*)","f")
                    return False
                
                # add fio options for fio test
                command = CMD + " --write_bw_log=bwOut%s --log_avg_msec=1000 --per_job_logs=0"%idThread                
                # set timeList and bwList
                timeList.append([0]*maxPlot )
                bwList.append( [0]*maxPlot )
                
                # add subplot
                ax = fig.add_subplot(len(CMDlist), 1, idThread+1)   # subplot start from1, ex. 4 cmds, add_subplot(4, 1, 1) add_subplot(4, 1, 2) .., to add_subplot(4, 1, 4)
                ax.autoscale(enable=True, axis="both", tight=None)   
                axList.append(ax)     
    
                # issue command and parser console out
                t = threading.Thread(target = self.RunOneFIOcmdWithConsoleOutThread, args=(idThread, command, printInfo,))
                t.start()                 
                mThreads.append(t)
                idThread = idThread +1  
                              
            # check if all process finished 
            while True:
                allfinished=1
                for process in mThreads:
                    if process.is_alive():
                        allfinished=0
                        break      
                # if all process finished and last parsing msg is done then quit while loop
                if allfinished==1 and doLastParseMsg==True:        
                    break
                else:
                    # if is doing last parsing msg 
                    if allfinished==1:
                        doLastParseMsg=True
                    # parse Msg------------------------------------------------
                    # copy Msg from thread output(self.Msg) and clear
                    self.lock.acquire()
                    MsgCopy = self.Msg
                    self.Msg=[]
                    self.lock.release()                          
                    # if new msg
                    if len(MsgCopy)!=0:
                        for mStr in MsgCopy:
                            # parse msg
                            # MutexThreadOut [type, idThread, time, readBW, writeBW, eta], type0 = RunTimeBW, 1=FinalAverageBW
                            mtype = mStr[0]
                            idThread = mStr[1]
                            time = mStr[2]
                            readBW = mStr[3]
                            writeBW = mStr[4]  
                            eta = mStr[5]     
                            
                            # check is read / write fio test
                            if fioRW[idThread]=="read":
                                bw=readBW
                            else:
                                bw=writeBW                                
                            if mtype==0: # if get RunTimeBW
                                # if > max size, remove old one 
                                if len(timeList[idThread]) >maxPlot:
                                    del timeList[idThread][0]
                                    del bwList[idThread][0]
                                timeList[idThread].append(time)
                                bwList[idThread].append(bw)
                                # update -----------
                                # clear
                                #plt.cla()        
                                # target ax
                                targetAx = axList[idThread]
                                targetAx.clear()
                                # set lables                        
                                targetAx.title.set_text("%s(%s), estimated time: %s"%(devName[idThread], fioRW[idThread], eta))  # nvme0n1(read), estimated time: 1m:10s
                                #targetAx.set_xlabel("Time(s)")
                                targetAx.set_ylabel("MiB/s")     
                                # set plot                       
                                targetAx.plot(timeList[idThread], bwList[idThread], 'b-')
                                # set y min=0
                                targetAx.set_ylim(bottom=0)               
                                # draw
                                fig.canvas.draw() 
                                fig.canvas.flush_events() 
                                # end of update    
                                 
                            if mtype==1: # if get FinalAverageBW 
                                averageBwList[idThread]=bw 
                    sleep(0.5) 
                    # end of parse Msg------------------------------------------------   
            return averageBwList           
        
        def BW_KMGtoM(self, value, unit):
        # format KMG to M, e.g. format giga to maga
            if unit=="K":    #KiB/s
                value=float(value)/1024
            if unit=="M":    #MiB/s
                value=float(value)                 
            if unit=="G":    #GiB/s
                value=float(value*1024)  
            return value

        def RunOneFIOcmdWithProgressStatus(self, command):
            # 
            MaxETA = 0
            if command.find("rw=read")!=-1:
                type = "read"
            elif command.find("rw=write")!=-1:
                type = "write"
            else:
                return False
            
            percent = 0
            # issue command and parser console out
            for line in self.RunFIOgetRealTimeConsoleOut(command):                
                # report for runtime bw
                # ex, Jobs: 1 (f=1): [W(1)][60.0%][r=0KiB/s,w=48.8MiB/s][r=0,w=99.9k IOPS][eta 00m:02s]
                mStr = "^Jobs: .*\[(.+)%\]\[r=([0-9.]*)([A-Z])iB/s.*w=([0-9.]*)([A-Z])iB/s.*\[eta (.*)\]"
                findRunTimeBW=bool(re.search(mStr, line))
                if findRunTimeBW:
                    percent = float(re.search(mStr, line).group(1))
                    Rvalue = float(re.search(mStr, line).group(2))
                    Runit =  re.search(mStr, line).group(3)
                    Wvalue = float(re.search(mStr, line).group(4))
                    Wunit =  re.search(mStr, line).group(5)                    
                    # read bw format to Mega
                    readBW = self.BW_KMGtoM(Rvalue, Runit)
                    # write bw format to Mega
                    writeBW = self.BW_KMGtoM(Wvalue, Wunit)
                    # ETA
                    eta =  re.search(mStr, line).group(6)
                    
                    
                    
                    #update progress bar
                    if type=="read":
                        PREFIX = "Read BW: %s Mb, eta: %s"%(readBW, eta)
                    else:
                        PREFIX = "Write BW: %s Mb, eta: %s"%(writeBW, eta)
                        
                    percent=int(percent)
                    
                    self.mNVME.PrintProgressBar(percent, 100, suffix = PREFIX, length = 20) 
                    
                # find write Average BW?
                mStr = "WRITE: bw=([0-9.]*)([A-Z])iB/s"
                findFinalAverageBWwrite=bool(re.search(mStr, line))             
                # find read Average BW?
                mStr = "READ: bw=([0-9.]*)([A-Z])iB/s"
                findFinalAverageBWread=bool(re.search(mStr, line))                                 
                # if find read or write, then save to Msg and set percent=100       
                if (findFinalAverageBWread or findFinalAverageBWwrite) and (percent!=100):   
                    self.mNVME.PrintProgressBar(100, 100, suffix = PREFIX, length = 20)
                    percent=100
                     
            return True        
            
        def RunOneFIOcmdWithConsoleOutThread(self, idThread, command, printInfo=False):
            # timer
            Tcnt=0
            # issue command and parser console out
            for line in self.RunFIOgetRealTimeConsoleOut(command):
                if printInfo:
                    self.OBJ.Print( line)    #print console out for testing only
                
                # report for runtime bw
                # ex, Jobs: 1 (f=1): [W(1)][60.0%][r=0KiB/s,w=48.8MiB/s][r=0,w=99.9k IOPS][eta 00m:02s]
                mStr = "^Jobs: .*r=([0-9.]*)([A-Z])iB/s.*w=([0-9.]*)([A-Z])iB/s.*\[eta (.*)\]"
                findRunTimeBW=bool(re.search(mStr, line))
                if findRunTimeBW:
                    Rvalue = float(re.search(mStr, line).group(1))
                    Runit =  re.search(mStr, line).group(2)
                    Wvalue = float(re.search(mStr, line).group(3))
                    Wunit =  re.search(mStr, line).group(4)                    
                    # read bw format to Mega
                    readBW = self.BW_KMGtoM(Rvalue, Runit)
                    # write bw format to Mega
                    writeBW = self.BW_KMGtoM(Wvalue, Wunit)
                    # ETA
                    eta =  re.search(mStr, line).group(5)    
                
                    # pyplot
                    time = Tcnt
                    Tcnt = Tcnt+1                  
                    # write info to mutex variable
                    self.lock.acquire()
                    # MutexThreadOut [type, idThread, time, readBW, writeBW, eta], type0 = RunTimeBW, 1=FinalAverageBW
                    self.Msg.append([0, idThread, time, readBW, writeBW, eta])                
                    self.lock.release()
                    
                # final report for average bw 
                #Run status group 0 (all jobs):
                #WRITE: bw=51.1MiB/s (53.6MB/s), 51.1MiB/s-51.1MiB/s (53.6MB/s-53.6MB/s), io=255MiB (268MB), run=5001-5001msec  
                #READ: bw=879MiB/s (922MB/s), 879MiB/s-879MiB/s (922MB/s-922MB/s), io=8791MiB (9218MB), run=10001-10001msec  
                readBW=0
                writeBW=0            
                # find write Average BW?
                mStr = "WRITE: bw=([0-9.]*)([A-Z])iB/s"
                findFinalAverageBWwrite=bool(re.search(mStr, line))
                if findFinalAverageBWwrite:                  
                    value = float(re.search(mStr, line).group(1))
                    unit =  re.search(mStr, line).group(2)   
                    writeBW = self.BW_KMGtoM(value, unit) 
                # find read Average BW?
                mStr = "READ: bw=([0-9.]*)([A-Z])iB/s"
                findFinalAverageBWread=bool(re.search(mStr, line))                     
                if findFinalAverageBWread:                  
                    value = float(re.search(mStr, line).group(1))
                    unit =  re.search(mStr, line).group(2)                
                    readBW = self.BW_KMGtoM(value, unit) 
                    
                # if find read or write, then save to Msg       
                if findFinalAverageBWread or findFinalAverageBWwrite:
                    eta =  0        
                    time = 0
                    # write info to mutex variable
                    self.lock.acquire()
                    # MutexThreadOut [type, idThread, time, readBW, writeBW, eta], type0 = RunTimeBW, 1=FinalAverageBW
                    self.Msg.append([1, idThread, time, readBW, writeBW, eta])                                      
                    self.lock.release()
    
        def RunFIOgetRealTimeConsoleOut(self, command):
            #---------------------------------------------------------------------------------------
            # usage: issue FIO command and get console output one by on
            # EX.
            #    CMD = "fio --direct=1 --iodepth=1 --ioengine=libaio --bs=512 --rw=write --numjobs=1 --size=100M --offset=0 --filename=/dev/nvme0n1 --name=mdata"
            #    for path in self.RunFIOgetRealTimeConsoleOut(CMD):
            #        self.Print( path)
            #---------------------------------------------------------------------------------------
            # must set --eta=always
            commandWith_etaIsalways = command + " --eta=always"
            #print to command log
            if self.mNVME.RecordCmdToLogFile:
                self.mNVME.Logger(command, mfile="cmd")              
            process = subprocess.Popen(commandWith_etaIsalways, stdout=subprocess.PIPE, shell=True, universal_newlines=True)                        
            self.process = process
            while True:
                if self.killProcess == True:
                    process.kill()
                    self.killProcess = False
                    return
                
                line = process.stdout.readline().rstrip()
                if not line:
                    break
                yield line
            # get return status    
            out, err = process.communicate()
            yield out                
    # end of class FIOcmdWithPyPlot_():
        
            

            
    def DrawFIO(self, FilePath):          
    #draw fio using fio log file whick log file format is 'time (msec), value, data direction, block size (bytes), offset (bytes)'
    # e.g. fio cmd with --write_bw_log=bwOut
        maxSize = 10
        timeList = [0]*maxSize 
        bwList = [0]*maxSize         
        
        #   using pyplot
        import matplotlib.pyplot as plt
        plt.ion()
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.autoscale(enable=True, axis="both", tight=None)
        ax.plot(timeList, bwList, 'b-')
        # init canvas, must do 3 time up   
 
        for i in range(4):
            fig.canvas.draw()

        lineNo = 0 
        noNewLineCnt=0
        while True:
            sleep(1)
            
            # read file
            LineList = self.ReadFileFromLineToEnd(FilePath, lineNo)
            if len(LineList)==0:
                noNewLineCnt=noNewLineCnt+1
                # if more then 3 times no new line, then break
                if noNewLineCnt>=10:
                    break
            else:
                # reset noNewLineCnt
                noNewLineCnt=0
                
                # parse new lines
                for line in LineList:
                    lineNo = lineNo+1
                    find=bool(re.search("(\d*), (\d*)", line))
                    if not find:
                        self.Print("file format error, expect 'date, bw'", "f")
                    else:
                        time = int(re.search("(\d*), (\d*)", line).group(1))
                        bw = int(re.search("(\d*), (\d*)", line).group(2))
                        # if > max size, remove old one 
                        if len(timeList) >100:
                            del timeList[0]
                            del bwList[0]
                        timeList.append(time)
                        bwList.append(bw)
                        # update
                        ax.plot(timeList, bwList, 'b-')
                        fig.canvas.draw() 
                        fig.canvas.draw()      
                        # end of update
                        
                    


            
            
            
    def ReadFileFromLineToEnd(self, FilePath, startLine):
    # read file from line number=startLine to the end of file
        cnt=startLine 
        rTList=[]
        if self.isfileExist(FilePath):            
            count = len(open(FilePath).readlines(  ))
            if count>cnt:
                for ptr in range(cnt, count):
                    linecache.clearcache()
                    line = linecache.getline(FilePath, ptr+1)
                    rTList.append(line)
                cnt = count       
        return rTList       
    
    def GetStrFromREsearchByShellCMD(self, shellCMD, searchPattern):
    # return string
        rtStr = self.shell_cmd(shellCMD)
        try:
            if re.search(searchPattern, rtStr):
                return re.search(searchPattern, rtStr).group(1)   
            else:
                return None # cant find
        except:
            self.Print("Fail at GetStrFromREsearchByShellCMD()", "f")
            self.Print("shellCMD: %s"%shellCMD, "f")
            self.Print("searchPattern: %s"%searchPattern, "f")
            return None
        
    def HighLightRed(self, mStr):
        return self.UseStringStyle(mStr, mode="bold", fore = "red")

    def getConfigParser(self, ini_path):
    # config file must have section header, e.x. '[setup]' where section header is setup
    # If no section header, set section header to [None]
    # ini_path: ex. 'SMIPowerCycleTest.ini'
    # example for get ENABLE_UGSD_IO_AMOUNT_MIN_MB in setup.ini of SMI_Power_Cycle_Test (window tool)
    #     config = self.getConfigParser('Setup.ini')
    #     config.get('Setup', 'ENABLE_UGSD_IO_AMOUNT_MIN_MB')
    # example for get UGSDTimerMin in SMIPowerCycleTest.ini of SMI_Power_Cycle_Test (window tool)
    #     config = self.getConfigParser('SMI_Power_Cycle_Test.ini')
    #     config.get('None', 'UGSDTimerMin')  # SMIPowerCycleTest have no section header, so using None to get value
    # refer to ConfigParser library
    
        config = ConfigParser.RawConfigParser()
        try:
            config.read(ini_path)    
        except Exception, error:
            # config file must have section header, e.x. '[setup]' where section header is setup
            # If no section header, error string will be 'MissingSectionHeaderError: File contains no section headers.'
            if type(error) == ConfigParser.MissingSectionHeaderError:
                # if error type is MissingSectionHeaderError, try to add section header('None') and read again
                ini_str = '[None]\n' + open(ini_path, 'r').read()
                ini_fp = StringIO.StringIO(ini_str)
                config = ConfigParser.RawConfigParser()
                config.readfp(ini_fp)                             
            else:
                self.Print( "Exception occor for getConfigParser(), ini file may lose(%s)"%ini_path, "f" )
                self.Print ("Exception info as below")
                self.Print(str(error), "f" )
        return config
    
    def GetAutoAlignStringFromList(self, mList, padding=2):
        # ex, mList = [['a', 'b', 'c'], ['aaaaaaaaaa', 'b', 'c'], ['a', 'bbbbbbbbbb', 'c']]
        mStr=""
        col_width = max(len(word) for row in mList for word in row) + padding  # padding
        for row in mList:
            mStr += "".join(word.ljust(col_width) for word in row) + "\n"       
        return mStr

    def GetAlignStringWithList(self,listIn="", alignLengthList=None, alignType="left"):
    # S0/S1: string 0, string 1
    # S0alignType/S1alignType: align to left or right
    # S0length/S1length: offset for strings        
        type = "<" if alignType=="left" else ">"
        rtStr = ""
        i=0
        if alignLengthList!= None and len(alignLengthList)!=len(listIn): # if input alignLengthList then len(alignLengthList) must =  len(listIn)
            return False
        for mStr in listIn:            
            length = 8 if alignLengthList == None else alignLengthList[i] # default value if not input alignLengthList, else using alignLengthList
            i = i+1
            buf = "{:%s%ss}"%(type, length)
            buf = buf.format("%s"%mStr) # format to string
            rtStr = rtStr + buf
        return rtStr
    
    def GetAlignString(self,S0="", S0length=40, S0alignType="left", S1="", S1length=40, S1alignType="left"):    
    # S0/S1: string 0, string 1
    # S0alignType/S1alignType: align to left or right
    # S0length/S1length: offset for strings
        # mStr = "{:<25}{:<40}".format(S0, S1)
        S0type = "<" if S0alignType=="left" else ">"
        S1type = "<" if S1alignType=="left" else ">"
        mStr = "{:%s%ss}{:%s%ss}"%(S0type, S0length, S1type, S1length)
        mStr = mStr.format("%s"%S0, "%s"%S1)
        return mStr

    def GetBytesFromList(self, listRawData, stopByteOffet, startByteOffet, isString=False):
    # return value of specific offset in listRawData, note, refer to self.convert
    # ex, listRawData = [1, 2, 3, 4, 5, 6], GetBytes(listRawData, 3, 1), return 2<<0 + 3<<8 + 4<<(8*2)
    # if isString, return string
        if not isString:
            value = 0
            x256 = 0
            for i in range(startByteOffet, stopByteOffet+1):
                value = value + (int(listRawData[i])<<(x256 * 8))
                x256 += 1
            return value
        else:
            value = ""
            for i in range(startByteOffet, stopByteOffet+1):
                value = value + chr(listRawData[i])
            return value   

    def PrintClass(self, mClass, S0length=40, S1length=40):
    # print class with it's attributes name and it's value
        attrs = vars(mClass)
        for item in attrs.items():
            mList = list(item)
            if mList[0][0] =="_": continue  # if is buildin name, skip it, ex. '__module__': '__main__'
            # align and print it
            mStr = self.GetAlignString(S0=mList[0], S0length=S0length, S1=mList[1], S1length=S1length)
            self.Print(mStr)
            
    def PrintListWithAlign(self, List, S0length=40, S1length=40, Ctype="d"):
    # print list that is similar to [[A, B], [C, D], ..], that will force A/B/C/D to str type
        for mList in List:
            mStr = self.GetAlignString(S0=str(mList[0]), S0length=S0length, S1=str(mList[1]), S1length=S1length)
            self.Print(mStr, Ctype)

    def hexdump(self, src, length=16): 
    # input is binary, ex, src = "\x15\xab\x33", self.hexdump(src)
    # 16 byte per line
        FILTER = ''.join([(len(repr(chr(x))) == 3) and chr(x) or '.' for x in range(256)])
        lines = []
        for c in xrange(0, len(src), length):
            chars = src[c:c+length]
            hex = ' '.join(["%02x" % ord(x) for x in chars])
            printable = ''.join(["%s" % ((ord(x) <= 127 and FILTER[ord(x)]) or '.') for x in chars])
            lines.append("%04x  %-*s  %s\n" % (c, length*3, hex, printable))
        return ''.join(lines)
    
    def HexListToStr(self, rawDataList):
    # support string and int type, ex, rawDataList=[0x15, 0x39], rawDataList=['15', '39']
        T = rawDataList[0]
        if type(T)==str:
            mStr = ''.join([chr(int(x, 16)) for x in rawDataList])
        else:
            mStr = ''.join([chr(x) for x in rawDataList])
        return mStr
    
    def ByteListToLongInt(self, byteList, byteorder = "little"):
        result = 0
        if byteorder == "little":
            i = 0
            for b in byteList:
                result = result + (int(b) <<( i*8 ))
                i +=1
        else:
            for b in byteList:
                result = result * 256 + int(b)            
        return result
    
    def PrintList(self, mList, addOffset = 4, numberPerLine = 16):
    # print int list with offset, where mList = [int, int ,int ..]
        mStr = ""
        currBk = self.PrintOffsetValue
        self.SetPrintOffset(currBk + addOffset)
        maxV = max(mList)
        maxV = "0x%X "%maxV
        maxLength = len(maxV)+1
        cnt = 0
        lineList = []
        for value in mList:  
            lineList.append(value)
            cnt +=1
            if cnt==numberPerLine:
                mStr = ""
                for V in lineList:
                    Vstr = "0x%X "%V
                    mStr = mStr+"{:<{x}}".format(Vstr, x=maxLength)
                self.Print(mStr)
                cnt=0
                lineList = []
            
        if mStr!=0:
            self.Print(mStr)    
        self.SetPrintOffset(currBk)         

    def RaisingTempture(self, TargetTemp, TimeOut):
    # TimeOut = time limit in secend
    # TargetTemp =temp in Kelvin degree
    # Return last tempture read from controller
        TimeCnt=0
        aa=time.time()
        TempNow=0
        while True:                     
            # writing
            mThreads=self.nvme_write_multi_thread(thread=4, sbk=0, bkperthr=512, value=0x5A)
            for process in mThreads:   
                process.join()
            
            TimeCnt= int(time.time()-aa) 
            PS = self.GetPS()    
            TempNow = self.GetLog.SMART.CompositeTemperature
            mSuffix="Temperature: %s C, Power State: %s"%(self.KelvinToC(TempNow), PS)
            
            # progressbar
            if TimeCnt<TimeOut:
                self.PrintProgressBar(TimeCnt, TimeOut, prefix = 'Time Usage:', suffix = mSuffix, length = 50)
            else:
                self.PrintProgressBar(TimeOut, TimeOut, prefix = 'Time Usage:', suffix = mSuffix, length = 50)
                self.Print ("After %s s, time out !,  stop to increase temperature !"%TimeOut)
                break
                    
            if TempNow>=TargetTemp: 
                self.Print ("")
                self.Print ("After %s s, temperature is large then target temperature now, stop to increase temperature !"%TimeCnt)
                break
    
        return TempNow

    def backUpClass(self, clsIn):
    # copy all clsIn class to CopyOfClk, including static members and dynamic members
    # ex. A=myClass(), A.value="valueA", B=backUpClass(A)
        CopyOfClk = type('CopyOfClk', clsIn.__bases__, dict(clsIn.__dict__))
        inst=CopyOfClk
        return inst
    
    def getFormatTime(self, Timestamp):
        #      localtime or gmtime
        mStr=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime((Timestamp&0xFFFFFFFFFFFF)/1000)) # remove byte 6 ( TimestampOrigin and Synch)
        return  mStr
    
    def find_sub_list(self, l, sl):
    # e.x.  A_list=["123", "abc", "456", "def", "abc", "456"]
    #         B_list=[ "abc", "456"]
    #         C= self.find_sub_list(A_list, B_list)
    #         return [(1, 2), (4, 5)] 
        results=[]
        sll=len(sl)
        for ind in (i for i,e in enumerate(l) if e==sl[0]):
            if l[ind:ind+sll]==sl:
                results.append((ind,ind+sll-1))    
        return results
    
    def findStopAddrForFIFOList(self, NewList, OldList):
    # return -1 if not find
    # return stop address for NewList compare with OldList(FIFO list)
        rtNewStop = -1
        N_len = len(NewList)
        O_len = len(OldList)
        for i in range(O_len):     
            O_subList = OldList[0:O_len-i]   
            findList= self.find_sub_list(NewList, O_subList)
            if len(findList)!=0: # if find
                lastFind=findList[-1]        
                start = lastFind[0]
                stop=lastFind[1]
                # if find sublist, old list start < new list and old list stop = last (new list) and is not the same(NewList and OldList)
                if start<N_len and stop==N_len-1 and start!=0:
                    rtNewStop = start-1
        return rtNewStop    
#== end of NVMECom =================================================

class timer_():
# use: start() and time
# no need to stop()
    def __init__(self):
        self._StartT=0
        self._StopT=0
        self.returnType = "string"
    def start(self, returnType = "string"):     #string/int/float
        self._StartT=time.time()
        self.returnType = returnType
    def stop(self):
        self._StopT=time.time()
    @property
    def time(self): 
        self._StopT=time.time()
        if self.returnType == "string":
            return format(self._StopT - self._StartT, '.6f')
        elif self.returnType == "int":
            return int(self._StopT - self._StartT)
        elif self.returnType == "float":
            return round(self._StopT - self._StartT, 6)        
        else:
            return 0
        




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
        

# below for create ordered attribute in a class
''' usage: 
    from lib_vct.NVMECom import OrderedAttributeClass
    class Ordered(OrderedAttributeClass):
        x = OrderedAttributeClass.MyOrderedField((1, 2))    # where (1, 2) is tuple that you can use later(any value, if not used, () instead )
        z = OrderedAttributeClass.MyOrderedField((3, 4, 5))
        b = OrderedAttributeClass.MyOrderedField(())        # not use tuple
        a = OrderedAttributeClass.MyOrderedField(())

    ordered = Ordered()
    allList = ordered.ordered_fields    # here allList is initial list that will be [['x', (1, 2)], ['z', (3, 4, 5)], ('b', ()), ('a', ())]
    note using getOrderedAttributesList_init to get allList(ordered_fields)
    note using getOrderedAttributesList to get current value after modify it!, e.g. [[name, value of name].......]
    note using setOrderedAttributesList_init to set initial list(), ex, ordered.setOrderedAttributesList_init("TNEV", 88888) and data will change in
            getOrderedAttributesList_init()
    
    if need to print, can use PrintListWithAlign(), e.x
    self.PrintListWithAlign(Ordered.getOrderedAttributesList())

'''


class BaseWithOrderedFields(type):
    """ Metaclass, which provides an attribute "ordered_fields", being an ordered
          list of class attributes that have a "creation_counter" attribute. """

    def __new__(cls, name, bases, attrs):
        new_class = super(BaseWithOrderedFields, cls).__new__(cls, name, bases, attrs)
        # Add an attribute to access ordered, orderable fields
        new_class.ordered_fields = [[name, attrs.pop(name)] for name, obj in attrs.items()
                                        if hasattr(obj, "creation_counter")]
        new_class.ordered_fields.sort(key=lambda item: item[1].creation_counter)
        
        return new_class

        
class OrderedAttributeClass(object): # snchan       
    __metaclass__ = BaseWithOrderedFields
    # For print dynamic OrderedAttributeClass list
    dynamicList = None
    
    class MyOrderedField(tuple): # input parameter must tuple
        creation_counter = 0
        
        def __init__(self, ArgTuple):
            # Set the instance's counter, to keep track of ordering
            self.creation_counter = OrderedAttributeClass.MyOrderedField.creation_counter
            # Increment the class's counter for future instances
            OrderedAttributeClass.MyOrderedField.creation_counter += 1
    '''        
    def addfieldTest(self, ArgTuple):
        bb = self.ordered_fields  
        self.ordered_fields.append(ArgTuple)
        bb = self.ordered_fields  
        return bb          
    '''
    def getOrderedAttributesList_curr(self):
        # read name and current value, ex, if after setting A=0x1, B=0x2, return [[A, 0x1], [C, 0x2], ..]
        listBuf = []
        for mList in self.ordered_fields: # ordered_fields is initial value = [['x', (1, 2)], ['z', (3, 4, 5)], ('b', ()), ('a', ())]
            name = mList[0]
            listBuf.append([name, getattr(self, name)])
        
        if self.dynamicList!=None:
            for mList in self.ResetInformationList:
                AttrList= mList.getOrderedAttributesList_curr()
                listBuf.extend(AttrList)            
 
        return listBuf
    
    def setDynamicList(self, mList):
        self.dynamicList = mList
    
    @classmethod
    def getOrderedAttributesList_init(cls):
        # read name and initial value , return [['x', (1, 2)], ['z', (3, 4, 5)], ('b', ()), ('a', ())]
        return cls.ordered_fields
    
    @classmethod
    def setOrderedAttributesList_init(cls, name, newValue):
    # find element in cls.ordered_fields and set it
        for n, nameAndValue in enumerate(cls.ordered_fields):
            if nameAndValue[0] == name: # nameAndValue[0] is name
                nameAndValue[1] = newValue # nameAndValue[1] is value, set it to new one
    
    
    