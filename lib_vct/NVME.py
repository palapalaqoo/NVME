'''
Created on Aug 3, 2018

@author: root
'''
import sys
import os
import threading
import math
import re
#import smi_comm
from time import sleep
from lib_vct.NVMECom import NVMECom
from lib_vct import ControllerRegister
from lib_vct import IdCtrl
from lib_vct import IdNs
from lib_vct.GetLog import GetLog
from lib_vct.Flow import Flow
from lib_vct.NVMECom import TimedOutExc
from lib_vct.NVMECom import deadline
import re
import time
from shutil import copyfile


def foo1():
    pass
    #self.Print ("foo!")
    
    
class NVME(object, NVMECom):
    
    
    def __init__(self, argv):
        # status
        self.status="normal"
        # init sub case
        self.CreateAbstractFuncAndVariablesForSonClassToOverride()
        # self.dev = /dev/nvme0n1
        
        # if object is created from main script , ex. DUT = SMI_SmartHealthLog(sys.argv )
        # then argv=sys.argv , thus remove argv[0] ='sysPath/SMI_SmartHealthLog.py', and pass to ParserArgv()
        # else if object is created in subcase of main script, ex. SubDUT = NVME(['/dev/nvme1n1']) in subcase1
        # the you can use SubDUT to control  /dev/nvme1n1, ex. using SubDUT.nvme_reset() to issue nvme reset for /dev/nvme1n1
        if argv[0] == sys.argv[0]:
            # created from main script
            self.isSubCaseOBJ=False
            mArgv = argv[1:]   # ['/dev/nvme0n1', subcase items and other parameters]
        else:
            # created in subcase
            self.isSubCaseOBJ=True
            mArgv = argv # ['/dev/nvme0n1'], only 1 args
        self.dev, self.UserSubItems, self.TestModeOn, self.mScriptDoc, self.mTestTime, self.LogPath =  self.ParserArgv(mArgv, self.CreateSubCaseListForParser())
        # check if self.dev = /dev/nvme*n*
        if not re.search("^/dev/nvme\d+n\d+$", self.dev):            
            print "Command parameter error!, run 'python %s -h' for more information"%os.path.basename(sys.argv[0])
            sys.exit(1)
        # self.dev_port = /dev/nvme0
        self.dev_port=self.dev[0:self.dev.find("nvme")+5]
        # self.dev_ns = 1
        self.dev_ns=self.dev[-1:]
        
        
        # final return code
        self.rtCode=0
        self.SubCase_rtCode=[]
        # Start Local Time
        self.StartLocalTime=time.time()
        self.SubCasePoint=0
        
              
        # the start 1G start block, middle and last, 
        self.start_SB=0
        self.middle_SB=0
        self.last_SB=0
        
        if self.ctrl_alive:  
            # init NVMECom
            NVMECom.__init__(self, self)            
            self.IdCtrl = IdCtrl.IdCtrl_(self)
            self.CNTLID=self.IdCtrl.CNTLID.int 
        else:
            self.Print("Error! Can't find device of %s"%self.dev_port, "f")
            self.Print( "Quit all the test items!", "f")
            sys.exit(1)       
        
        if self.dev_alive:
            self.init_parameters()
            self.status="normal"
        else:        
            self.Print("Device missing! try to reset namespace for %s"%self.dev, "f")
            self.ResetNS()
            if not self.dev_alive:
                self.Print( "Can't Reset Namespace, Exit!", "f")
                sys.exit(1)
            else:
                self.Print ("Reset namespace success")
                self.Print ("")
                self.init_parameters()
                self.status="normal"     
                
     
    # function for CreateAbstractFuncAndVariablesForSonClassToOverride
    def _function(self):
        pass
        
    def CreateAbstractFuncAndVariablesForSonClassToOverride(self): 
        #=======================================================================
        # abstract  function
        #     PreTest()                                                           :Override it for pretest, ex. check if controll support features, etc.
        #                                                                                :return true or false
        #     SubCase1() to SubCase32()                            :Override it for sub case 1 to sub case32
        #                                                                                :return 0=pass, 1=fals, 255=skip/notSupport
        #     PostTest()                                                         :Override it for post test, ex. check controll status, etc.
        #                                                                                :return true or false        
        # abstract  variables
        #     SubCase1Desc to SubCase32Desc                 :Override it for sub case 1 description to sub case32 description
        #     SubCase1KeyWord to SubCase32KeyWord   :Override it for sub case 1 keyWord to sub case32 keyWord
        #     SubCase1TimeOut to SubCase32TimeOut     :Override it for sub case 1 TimeOut to sub case32 TimeOut        
        #     self.ScriptName, self.Author, self.Version      :self.ScriptName, self.Author, self.Version
        #=======================================================================            
        
        # PreTest()
        exec("NVME.PreTest=self._function")
        
        # PostTest()
        exec("NVME.PostTest=self._function")        
        
        # generate dynamic function for SubCase1() to SubCase32() for sun class to override
        # e.g. 
        # |    def SubCase1(self):
        # |       pass
        self.SubCaseMaxNum=32        
        for x in range(1, self.SubCaseMaxNum+1): 
            exec("NVME.SubCase%s=self._function"%x)

        # generate dynamic variables: SubCase1Desc
        for x in range(1, self.SubCaseMaxNum+1): 
            setattr(NVME, "SubCase%sDesc"%x, "")
            
        # generate dynamic variables: SubCase1Keyword
        for x in range(1, self.SubCaseMaxNum+1): 
            setattr(NVME, "SubCase%sKeyWord"%x, "")        
        # print (dir(NVME))
        #  print (dir(self))       

        # generate dynamic variables: SubCase1TimeOut
        for x in range(1, self.SubCaseMaxNum+1): 
            setattr(NVME, "SubCase%sTimeOut"%x, "")        
                    
        # others
        NVME.ScriptName="Null"
        NVME.Author="Null"
        NVME.Version="Null"
                 
    def init_parameters(self):        
                
        self.CR = ControllerRegister.CR_(self)        
        self.IdNs = IdNs.IdNs_(self)
        self.GetLog = GetLog.GetLog_(self)
        self.Flow=Flow.Flow_(self)
        
        self.pcie_port = self.shell_cmd(" udevadm info %s  |grep P: |cut -d '/' -f 5" %(self.dev_port))         
        self.bridge_port = "0000:" + self.shell_cmd("echo $(lspci -t | grep : |cut -c 8-9):$(lspci -t | grep $(echo %s | cut -c6- |sed 's/:/]----/g') |cut -d '-' -f 2)" %(self.pcie_port))
        
        # get valume of ssd
        ncap=self.IdNs.NCAP.int
        # the start 1G start block
        self.start_SB=0
        # the middle 1G start block
        self.middle_SB=ncap/2-(1024*1024*2)
        # the last 1G start block
        self.last_SB=ncap-(1024*1024*2)
        
        self.MDTSinByte=int(math.pow(2, 12+self.CR.CAP.MPSMIN.int) * math.pow(2, self.IdCtrl.MDTS.int))
        self.MDTSinBlock=self.MDTSinByte/512
        
        # get System Bus (PCI Express) Registers, int format
        self.PMCAP, self.MSICAP, self.PXCAP, self.MSIXCAP, self.AERCAP, self.SR_IOVCAP=self.GetPCIERegBase()
        self.PCIHeader=0
        # Initiate Function Level Reset value        
        self.IFLRV= self.read_pcie(self.PXCAP, 0x9) + (1<<7)
        # Initial Commands Supported and Effects Log
        self._StrCSAEL=self.get_CSAEL() 
        
        # Controller registers are located in the MLBAR/MUBAR registers (PCI BAR0 and BAR1) that shall be mapped to a memory space that supports in-order access and variable access widths.
        self.MemoryRegisterBaseAddress=self.GetMRBA()        
        
        # save parameters for reset controller to the beginning state
        self.initial_FLBAS=self.IdNs.FLBAS.int

    def GetMRBA(self):
        # Memory Register Base Address
        MRBA=0x0
        # MLBAR start from 0x10
        for i in range(4):
            MRBA=MRBA+(self.read_pcie(self.PCIHeader, 0x10+i)<<(8*i))
        # mask lower 13bits
        MRBA = MRBA & 0xFFFFC000
        # MUBAR start from 0x14
        for i in range(4):
            MRBA=MRBA+(self.read_pcie(self.PCIHeader, 0x14+i)<<(8*i))     
        return MRBA   

    def IsMethodOverride (self, mtehodName):
    # check if mtehod is override by sun class
        method=mtehodName
        this_method = getattr(self, method)
        base_method = getattr(NVME, method)
        if this_method.__func__ is not base_method.__func__:
            return True
        else:
            return False
    
    def GetAbstractFunctionOrVariable(self, Num, Type):
    # return  abstract function or variable
        if Type=="subcase":
            return  getattr(self, "SubCase%s"%Num)
        elif Type=="pretest":
            return  getattr(self, "PreTest")        
        elif Type=="posttest":
            return  getattr(self, "PostTest")           
        elif Type=="description":
            return  getattr(self, "SubCase%sDesc"%Num)
        elif Type=="keyword":
            return  getattr(self, "SubCase%sKeyWord"%Num)
        elif Type=="timeout":
            return  getattr(self, "SubCase%sTimeOut"%Num)        
                
    def CreateSubCaseListForParser(self):
        mStr="Case List:\n"

        for SubCaseNum in range(1, self.SubCaseMaxNum+1):
            if self.IsMethodOverride("SubCase%s"%SubCaseNum):    
                # get subcase content
                SubCaseFunc = self.GetAbstractFunctionOrVariable(SubCaseNum, "subcase")
                Description=self.GetAbstractFunctionOrVariable(SubCaseNum, "description")
                SpecKeyWord=self.GetAbstractFunctionOrVariable(SubCaseNum, "keyword") 
                Timeout=self.GetAbstractFunctionOrVariable(SubCaseNum, "timeout")  
                mStr = mStr + "  Case %s : %s "%(SubCaseNum, Description) +"\n"

        return mStr
                
                          
    def RunScript(self):
        # if user issue command without subitem option, then test all items
        if len(self.UserSubItems)==0:
            for i in range(1, self.SubCaseMaxNum+1):
                self.UserSubItems.append(i)
        
        # print information
        self.PrintInfo()
        # print document only
        if self.mScriptDoc:
            return 0 
           
        
        # if override Pretest(), then run it, or PreTestIsPass= true
        if self.IsMethodOverride( "PreTest"):
            # enable RecordCmdToLogFile to recode command
            self.RecordCmdToLogFile=True             
            self.Logger("<PreTest> ----------------------------", mfile="cmd") 
                
            PreTest = self.GetAbstractFunctionOrVariable(0, "pretest")
            PreTestIsPass = PreTest()
            
            # disable RecordCmdToLogFile to recode command
            self.RecordCmdToLogFile=True             
            self.Logger("</PreTest> ----------------------------", mfile="cmd")       
            self.Logger("", mfile="cmd")            
        else:
            PreTestIsPass = True
        
        # <for function from SubCase1 to SubCaseX if function is overrided, where max SubCaseX=SubCase32>
        for SubCaseNum in range(1, self.SubCaseMaxNum+1):
            if self.IsMethodOverride("SubCase%s"%SubCaseNum):                
                
                # get subcase content
                SubCaseFunc = self.GetAbstractFunctionOrVariable(SubCaseNum, "subcase")
                Description=self.GetAbstractFunctionOrVariable(SubCaseNum, "description")
                SpecKeyWord=self.GetAbstractFunctionOrVariable(SubCaseNum, "keyword") 
                Timeout=self.GetAbstractFunctionOrVariable(SubCaseNum, "timeout") 
                # if not set timeout, then set default timeout=600(10minute)
                Timeout=600 if Timeout=="" else Timeout
                # if find subitem and PreTestIsPass=true, e.g. user assign it to run, then run it with time out=  timeOut, else return skip
                if SubCaseNum in self.UserSubItems and PreTestIsPass:
                    # set SubCasePoint for consol prefix
                    self.SubCasePoint=SubCaseNum
                    # print sub case titles
                    self.Print ("")
                    self.Print ("-- Case %s --------------------------------------------------------------------- timeout %s s --"%(SubCaseNum, Timeout), "b")
                    self.Print ("-- %s"%Description)
                    self.Print ("-- Keyword: %s"%SpecKeyWord)

                    # enable RecordCmdToLogFile to recode command
                    self.RecordCmdToLogFile=True             
                    self.Logger("<Case %s> ----------------------------"%SubCaseNum, mfile="cmd")                                         

                    # run script, 3th,4th line equal 1,2 line statements
                    #    @deadline(Timeout)
                    #    Code=SubCaseFunc()
                    SubCaseFuncWithTimeOut=deadline(Timeout)(SubCaseFunc)    
                    Code=None
                    
                    # sub case execption
                    try:
                        Code = SubCaseFuncWithTimeOut()    
                        
                    # timeout execption     
                    except TimedOutExc as e:              
                        self.Print ("")
                        self.Print( "Timeout!(%s seconds), quit Case %s test!"%(e, SubCaseNum), "f" )
                        self.Print( "Fail", "f" )
                        Code = 1               
                    # other execption
                    except Exception, error:
                        self.Print( "An exception was thrown and stop sub case, please check command log(%s)"%self.LogName_CmdDetail, "f" )
                        self.Print( "Exception message as below", "f" )
                        self.Print ("")
                        self.Print( "=====================================", "f" )
                        self.Print(str(error), "f" )
                        self.Print( "=====================================", "f" )
                        Code = 1
                    
                    #  prevent coding no return code, eg. 0/1/255
                    if Code ==None:
                        Code = 0
                        

                         
                    # disable RecordCmdToLogFile to recode command
                    self.RecordCmdToLogFile=True             
                    self.Logger("</Case %s> ----------------------------"%SubCaseNum, mfile="cmd")
                    self.Logger("", mfile="cmd")                             
                else:
                    # if user didn't assign subcase, return skip                              
                    Code = 255
                
                # save code to SubCase_rtCode
                self.SubCase_rtCode.append(Code)
                
                # write to log file    
                self.WriteSubCaseResultToLog(Code, SubCaseNum, Description)
        # </for function from SubCase1 to SubCaseX   >     

        # if override Posttest(), then run it, or PreTestIsPass= true
        if self.IsMethodOverride( "PostTest"):
            # enable RecordCmdToLogFile to recode command
            self.RecordCmdToLogFile=True             
            self.Logger("<PostTest> ----------------------------", mfile="cmd") 
                
            PostTest = self.GetAbstractFunctionOrVariable(0, "posttest")
            PostTestIsPass = PostTest()
            
            # disable RecordCmdToLogFile to recode command
            self.RecordCmdToLogFile=True             
            self.Logger("</PostTest> ----------------------------", mfile="cmd")       
            self.Logger("", mfile="cmd")            
        else:
            PostTestIsPass = True
        
        # get rtCode from SubCase_rtCode
        self.rtCode = self.GetrtCodeFrom_SubCase_rtCode()
        
        sleep(1)
        # reset controller to initial status
        self.ResetToInitStatus()
                
        # print ColorBriefReport
        self.PrintColorBriefReport()
        
        # copy log to ./Case_Summary.log
        copyfile(self.LogName_Summary, "Case_Summary.log")

    def GetrtCodeFrom_SubCase_rtCode(self):
        rt=0
        findWarnning=False
        findFail=False
        findPass=False
        for srtCode in self.SubCase_rtCode:
            if srtCode==255:
                findWarnning=True
            if srtCode==1:
                findFail=True                
            if srtCode==0:
                findPass=True      
         
        if findPass and not findFail:
            rt=0
        if not findPass and findWarnning and not findFail:
            rt=255
        if findFail:
            rt=1
            
        return rt
    
    def ResetToInitStatus(self):
        sleep(0.1)
        success=True
        self.Print("")
        printTag=True
        # if not only namespace 1 exist, e.g. /dev/nvmexn2 exist, then reset ns to namespace 1
        if self.dev_exist(2):
            if printTag:
                self.Print("== ResetToInitStatus ===========================", "p")
                printTag=False                
            self.Print("Reset all namespaces to namespace 1 and kill other namespaces")
            
            self.ResetNS()
            if not self.dev_exist(2):
                self.Print("Success", "p")
            else:    
                self.Print("Fail", "f")
                success=False
        
        # if initial_FLBAS !=0, format nsid 1 to initial_FLBAS, e.g. 512 or 4k etc.. 
        Init_FLBAS=self.initial_FLBAS    
        Now_FLBAS=self.IdNs.FLBAS.int
        if Init_FLBAS!=Now_FLBAS:  
            Init_lbaf=Init_FLBAS&0xF   
            Init_FLBAS_bit4 = 1 if (Init_FLBAS&0x10)>0 else 0     
                               
            nsid=1

            if printTag:
                self.Print("== ResetToInitStatus ===========================", "p")
                printTag=False                            
            self.Print("Format namespace 1 to previous format(Formatted LBA Size (FLBAS) field is %s)"%(hex(Init_FLBAS)))
            
            self.shell_cmd(" nvme format %s -n %s -l %s -s %s -p %s -i %s -m %s 2>&1" % (self.dev_port, nsid, Init_lbaf, 0, 0, 0, Init_FLBAS_bit4))
            Now_FLBAS=self.IdNs.FLBAS.int
            if Init_FLBAS==Now_FLBAS:  
                self.Print("Success", "p")
            else:    
                self.Print("Fail", "f")
                success=False        
                
        return success


        
    def WriteSubCaseResultToLog(self, Code, SubCaseNum, Description): 
        # get return code and print to log file
        if Code==0:
            rtMsg="Pass"
            color = self.color.GREEN
        elif Code==1:
            rtMsg="Fail"
            color = self.color.RED
            # set rtCode = 1
            self.rtCode=1
        elif Code==255:
            rtMsg="Skip"
            color = self.color.YELLOW
            # if rtCode = 0, then set rtCode = 255
            self.rtCode = 255 if self.rtCode==0 else self.rtCode
        else:
            rtMsg="Unknow"     
            color="No"               
        
        mStr = "CASE %s : %s : %s"%(SubCaseNum, Description, rtMsg)
        #print to default log
        self.Logger(mStr, mfile="default")        
        #print to color log
        self.Logger(mStr, mfile="color", color=color )        
        
    def PrintColorBriefReport(self):
        self.Print ("")
        self.Print ("== Brief report ================================", "p")
        print self.ReadLogFile(mfile="color")
        self.Print ("----------------------------------------------------------", "p")
        self.Print ("Overall return code: %s" %self.rtCode)
        self.Print ("Finish..")
        self.Print ("================================================",  "p")
        
    def Finish(self):
        sys.exit(self.rtCode)  
        
    def CSAEL(self, CMDType, Opcode, Field):
        # return int
        # CMDType = "admin", "io"
        # Field = CSUPP, LBCC, NCC, NIC, CCC, CSE
                
        if len(self._StrCSAEL)==2048:
            # from 0 to 255 is admin command, io command start from 256
            if CMDType=="admin":
                offset=Opcode
            else:
                offset=Opcode+0x100 
            mCSAEL=self._StrCSAEL    
            # every command have data structure which is 4 byte   
            mstruct=mCSAEL[offset*4:(offset+1)*4]
            
            if Field=="CSUPP":
                value = 1 if (int(mstruct[0],16) & 0b00000001)>=1 else 0
            elif Field=="LBCC":
                value = 1 if (int(mstruct[0],16) & 0b00000010)>=1 else 0    
            elif Field=="NCC":
                value = 1 if (int(mstruct[0],16) & 0b00000100)>=1 else 0
            elif Field=="NIC":
                value = 1 if (int(mstruct[0],16) & 0b00001000)>=1 else 0                            
            elif Field=="CCC":
                value = 1 if (int(mstruct[0],16) & 0b00010000)>=1 else 0
            elif Field=="CSE":
                value = 1 if (int(mstruct[2],16) & 0b00000111)>=1 else 0   
            else:
                value = 0             
                            
            return value
        else:
            return 0
    
    def read_pcie(self, base, offset):    
        # read pcie register, return byte data in int format       
        hex_str_addr=hex(base + offset)[2:]
        return int(self.shell_cmd("setpci -s %s %s.b " %(self.pcie_port, hex_str_addr)),16)
    def write_pcie(self, base, offset, value):    
        # write pcie register, ex. setpci -s 0000:02:00.0 79.b=A0    
        hex_str_addr=hex(base + offset)[2:]
        hex_str_value=hex(value)[2:]
        self.shell_cmd("setpci -s %s %s.b=%s " %(self.pcie_port, hex_str_addr, hex_str_value))
    

    @property
    def dev_alive(self):
        return self.dev_exist()    
    
    @property
    def ctrl_alive(self):
        return self.dev_exist(nsid=0)  


    def dev_exist(self, nsid=-1):
    #-- return boolean
    #-- default device=self.dev, ex. "/dev/nvme0n1        
        if nsid==-1:    # /dev/nvme0n1 exist?
            DEV=self.dev
        elif nsid==0:   # /dev/nvme0 exist?
            DEV=self.dev_port
        else:               # /dev/nvme0nX exist?
            DEV=self.dev_port+"n%s"%nsid
            
        buf=self.shell_cmd("find %s 2> /dev/null |grep %s " %(DEV,DEV))
        if not buf:
            return False
        else:
            return True
        

                
    def ns_exist(self, nsid):
    #-- check if name space exist or not 
    #-- return boolean
        buf=self.shell_cmd("nvme id-ns %s -n %s 2>&1 |grep INVALID_NS" %(self.dev_port,nsid))
        if buf:
            return False
        else:
            return True
        
   
    def DeleteNs(self, nsid):
    #-- Delete name space exist or not 
        self.shell_cmd("nvme delete-ns %s -n %s 2>&1 >/dev/null " %(self.dev_port,nsid))
        
    def CreateNs(self, SizeInBlock=2097152):
    #-- Create name space, default size = 1G
    #-- return created nsid
        SIB=SizeInBlock
        LBAx=0
        buf=self.shell_cmd("nvme create-ns %s -s %s -c %s -f %s -d 0 -m 0 2>&1" %(self.dev_port, SIB, SIB, LBAx))
        # create-ns: Success, created nsid:5
        mStr="created nsid:(\d+)"
        nsid=-1
        if re.search(mStr, buf):
            nsid=int(re.search(mStr, buf).group(1),16)    
        return nsid

        
        
    def AttachNs(self, nsid):
    #-- 
        self.shell_cmd("nvme attach-ns %s -n %s -c %s 2>&1 >/dev/null " %(self.dev_port,nsid, self.CNTLID))
    
    def DetachNs(self, nsid):
    #-- 
        self.shell_cmd("nvme detach-ns %s -n %s -c %s 2>&1 >/dev/null " %(self.dev_port,nsid, self.CNTLID))
    
    
    def get_CSAEL(self):
    #-- Get Log Page - Commands Supported and Effects Log
        if self.IdCtrl.LPA.bit(1)=="1":
            return self.get_log2byte(5,2048)
        else:
            return "0"
    
    def fio_write(self, offset, size, pattern, nsid=1, devPort=None, fio_direct=1):
        devPort=self.dev_port if devPort==None else devPort
        DEV=devPort+"n%s"%nsid 
        return self.shell_cmd("fio --direct=%s --iodepth=16 --ioengine=libaio --bs=64k --rw=write --filename=%s --offset=%s --size=%s --name=mdata \
        --do_verify=0 --verify=pattern --verify_pattern=%s" %(fio_direct, DEV, offset, size, pattern))
    
    def fio_isequal(self, offset, size, pattern, nsid=1, fio_bs="64k", devPort=None, fio_direct=1):
    #-- return boolean
        devPort=self.dev_port if devPort==None else devPort
        DEV=devPort+"n%s"%nsid 
        msg =  self.shell_cmd("fio --direct=%s --iodepth=16 --ioengine=libaio --bs=%s --rw=read --filename=%s --offset=%s --size=%s --name=mdata \
        --do_verify=1 --verify=pattern --verify_pattern=%s 2>&1 >/dev/null | grep 'verify failed at file\|bad pattern block offset\| io_u error' " %(fio_direct, fio_bs, DEV, offset, size, pattern))

        ret=False
        if msg:
            ret=False
        else:
            ret=True
     
        return ret      
    

    def Identify_command(self):
        return self.get_reg("id-ctrl", "nn")
        
    def write_SML_data(self,pattern, size="1M"):    
    #-- write 1G into SSD at start, midde and last address    
        # write data for testing(start, middle, last)
        self.fio_write(self.start_SB*512, size, pattern) 
        self.fio_write(self.middle_SB*512, size, pattern)
        self.fio_write(self.last_SB*512, size, pattern)
    
    # check  Logical Block Content Change
    def isequal_SML_data(self,pattern, size="1M"): 
    #-- check 1G data at start, midde and last address
        ret=False        
        if self.fio_isequal(self.start_SB*512,size, pattern):
            ret=True
        else:
            ret=False
            return ret 
                
        if self.fio_isequal(self.middle_SB*512,size, pattern):
            ret=True
        else:
            ret=False
            return ret 
            
        if self.fio_isequal(self.last_SB*512,size, pattern):
            ret=True
        else:
            ret=False
            return ret 
        return ret

    def set_feature(self, fid, value, SV=0, Data=None, nsid=0): 
    # feature id, value
    # Data example = '\\255\\255\\255\\000' or '\\xff\\xff'
    # if sv=1 and have data in
    # CMD = echo "\\255\\255\\255\\255\\255\\255" |nvme set-feature %s -f %s -n %s -v %s -s 2>&1
        
        CMD=""
        if Data!=None:
            CMD="echo -n -e \""+ Data + "\" | "
        
        CMD = CMD + "nvme set-feature %s -f %s -v %s " %(self.dev, fid, value)
                
        if SV!=0:
            CMD = CMD + "-s "         
        
        if nsid!=0:
            CMD = CMD +"-n %s "%nsid
            
        if Data!=None:
            CMD = CMD +"-l %s "%Data.count('\\')
        
        CMD = CMD +"2>&1 "

        return self.shell_cmd(CMD)
    
        
     
    def get_feature(self, fid, cdw11=0, sel=0, nsid=0, nsSpec=False): 
    # feature id, cdw11(If applicable)
        CMD=""
        
        if nsSpec:
            CMD = CMD + " nvme get-feature %s -f %s --cdw11=%s -s %s "%(self.dev_port, fid, cdw11, sel)
        else:
            CMD = CMD + " nvme get-feature %s -f %s --cdw11=%s -s %s "%(self.dev, fid, cdw11, sel)
        
        
        if nsSpec and nsid!=0:
            CMD = CMD +"-n %s "%nsid
        
        CMD = CMD +"2>&1 "
        return self.shell_cmd(" nvme get-feature %s -f %s --cdw11=%s -s %s -n %s 2>&1"%(self.dev, fid, cdw11, sel, nsid))

        
    def asynchronous_event_request(self): 
        # create thread for asynchronous_event_request_cmd        
        t = threading.Thread(target = self.asynchronous_event_request_cmd)
        t.start()        
        sleep(0.2)
        # raising critical waning
        # set Asynchronous Event Configuration (Feature Identifier 0Bh) bit0-7 to 1
        self.shell_cmd(" nvme set-feature %s -f 0xB -v 0xff"%(self.dev), 0.5)        
        # get log page and set 'Retain Asynchronous Event(RAE) = 0' 
        self.shell_cmd(" buf=$(nvme admin-passthru %s --opcode=0x2 -r --cdw10=0x2 -l 16 2>&1 >/dev/null)"%(self.dev), 0.5)         
        # Set TMPTH to 60 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 0)
        self.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x14D"%(self.dev), 0.5) 
        # Set TMPTH to 10 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 1)
        self.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x11B"%(self.dev), 0.5) 
        # Set TMPTH to 60 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 0)
        self.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x14D"%(self.dev), 0.5) 
        # get log page and set 'Retain Asynchronous Event(RAE) = 0' 
        self.shell_cmd(" buf=$(nvme admin-passthru %s --opcode=0x2 -r --cdw10=0x2 -l 16 2>&1 >/dev/null)"%(self.dev), 0.5)     
        # Set TMPTH to 10 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 1)
        self.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x11B"%(self.dev), 0.5)  
        # Set TMPTH to 60 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 0)
        self.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x14D"%(self.dev), 0.5)           
              
        # wait thread finish
        t.join()        
        return 0          
     
    def asynchronous_event_request_cmd(self): 
        return self.shell_cmd("  buf=$(nvme admin-passthru %s --opcode=0xC 2>&1 >/dev/null)"%(self.dev))

    def device_self_test(self):
        return self.shell_cmd(" nvme admin-passthru %s --opcode=0x14 --namespace-id=0xffffffff --data-len=0 --cdw10=0x1 -r -s 2>&1 > /dev/null"%(self.dev))
    def nvme_format(self):
        return self.shell_cmd("  nvme format %s 2>&1 > /dev/null"%(self.dev))
    def sanitize(self):
        self.shell_cmd("  nvme sanitize %s -a 0x02 2>&1 > /dev/null"%(self.dev))    
        sleep(0.1)
        # wait for sanitize command complate
        while self.GetLog.SanitizeStatus.SPROG != 65535 :
            sleep(0.5)
        return 0
    def flush(self):
        self.fio_write(self.start_SB*512, "1M", "0x11") 
        self.shell_cmd(" buf=$( nvme flush %s -n 1 2>&1 > /dev/null)"%(self.dev)) 
        return 0
    def write(self):
        self.fio_write(self.start_SB*512, "1M", "0x11") 
        return 0  
    def read(self):
        self.fio_isequal(0, "1M", "0x19")
        return 0     
    def write_unc(self, SLB=0, BlockCnt=127):
        self.shell_cmd("  buf=$(nvme write-uncor %s -s %s -n %s -c %s 2>&1 > /dev/null) "%(self.dev, SLB, self.dev_ns, BlockCnt)) 
        return 0      
    def compare(self):
        self.shell_cmd("  buf=$(dd if=/dev/zero bs=512 count=1 2>&1 > /dev/null | nvme compare %s  -s 0 -z 51200 -c 99 2>&1 > /dev/null) "%(self.dev)) 
        return 0   
    def write_zero(self):
        self.shell_cmd("  buf=$(nvme write-zeroes %s -s 0 -c 1 2>&1 > /dev/null) "%(self.dev)) 
        return 0     
    def dsm_deallo(self):
        self.shell_cmd("  buf=$(nvme dsm %s -s 0 -b 1 -d 2>&1 >  /dev/null) "%(self.dev)) 
        return 0     

    def nvme_reset(self):
        self.status="reset"    
        self.shell_cmd("  nvme reset %s "%(self.dev_port), 0.5) 
        sleep(1)
        self.status="normal"
        return 0     
    def subsystem_reset(self):
        self.status="reset"
        self.shell_cmd("  nvme subsystem-reset %s  "%(self.dev_port), 0.5) 
        self.shell_cmd("  rm -f %s* "%(self.dev_port))
        self.shell_cmd("  echo 1 > /sys/bus/pci/devices/%s/reset " %(self.pcie_port))  
        self.hot_reset() 
        self.status="normal"        
        return 0         
    def hot_reset(self):
        self.status="reset"
        self.shell_cmd("  echo 1 > /sys/bus/pci/devices/%s/remove " %(self.pcie_port), 0.1) 
        self.shell_cmd("  echo 1 > /sys/bus/pci/rescan ", 0.1)     
        self.shell_cmd("  echo -n '%s' > /sys/bus/pci/drivers/nvme/unbind" %(self.pcie_port), 0.1) 
        self.shell_cmd("  echo -n '%s' > /sys/bus/pci/drivers/nvme/bind" %(self.pcie_port), 0.1)    
        sleep(1)     
        self.status="normal"
        return 0         
    def link_reset(self):
        # Data Link Down
        # set secondary bus reset bit from 0x10 to 0x50
        self.status="reset"
        self.shell_cmd("  setpci -s %s 3E.b=50 " %(self.bridge_port), 0.5) 
        self.shell_cmd("  setpci -s %s 3E.b=10 " %(self.bridge_port), 0.5) 
        self.hot_reset()       
        self.status="normal"  
                
        '''
        self.status="reset"
        self.shell_cmd("  setpci -s %s 3E.b=50 " %(self.bridge_port), 0.5) 
        self.shell_cmd("  setpci -s %s 3E.b=10 " %(self.bridge_port), 0.5) 
        self.shell_cmd("  echo 1 > /sys/bus/pci/devices/%s/reset " %(self.bridge_port), 0.5) 
        self.shell_cmd("  rm -f %s* "%(self.dev_port))
        self.shell_cmd("  echo 1 > /sys/bus/pci/devices/%s/reset " %(self.pcie_port)) 
        self.hot_reset()
        self.status="normal"        
        '''
        return 0  
    def FunctionLevel_reset(self):
        '''
        self.status="reset"        
        self.write_pcie(self.PXCAP, 0x9, self.IFLRV)
        sleep(0.2)
        self.shell_cmd("  rm -f %s* "%(self.dev_port))
        self.shell_cmd("  echo 1 > /sys/bus/pci/devices/%s/reset " %(self.pcie_port))  
        self.hot_reset() 
        self.status="normal"
        return 0 
        '''
        self.status="reset"  
        self.write_pcie(self.PXCAP, 0x9, self.IFLRV)
        sleep(1)
        self.shell_cmd("  echo 1 > /sys/bus/pci/devices/%s/reset " %(self.pcie_port), 1) 
        self.status="normal"
        if self.dev_alive:            
            return 0        
        else:
            return 1        

        
    def por_reset(self):
        self.status="reset"
        self.shell_cmd("/usr/local/sbin/PWOnOff %s por off 2>&1 > /dev/null" %(self.dev_port), 0.1) 
        self.shell_cmd("/usr/local/sbin/PWOnOff %s por on 2>&1 > /dev/null" %(self.dev_port), 0.1) 
        self.status="normal"
        return 0            
    
    def spor_reset(self):
        self.status="reset"
        self.shell_cmd("/usr/local/sbin/PWOnOff %s spor off 2>&1 > /dev/null" %(self.dev_port), 0.1) 
        self.shell_cmd("/usr/local/sbin/PWOnOff %s spor on 2>&1 > /dev/null" %(self.dev_port), 0.1) 
        self.status="normal"
        return 0  
    
    def nvme_write_1_block(self, value, block, nsid=1):
        # write 1 block data, ex, nvme_write_1_block(0x32,0)
        # if csts.rdy=0, return false
        # value, value to write        
        # block, block to  write  
        '''
        oct_val=oct(value)[-3:]
        if self.dev_alive and self.status=="normal":
            self.shell_cmd("  buf=$(dd if=/dev/zero bs=512 count=1 2>&1   |tr \\\\000 \\\\%s 2>/dev/null | nvme write %s --start-block=%s --data-size=512 2>&1 > /dev/null) "%(oct_val, self.dev, block))   
        else:
            return False
        '''
        
        oct_val=oct(value)[-3:]
        #if self.dev_alive and self.status=="normal":  
        #if self.dev_alive :               
        if self.status=="normal":       
            slba=block
            cdw10=slba&0xFFFFFFFF
            cdw11=slba>>32    
            # if need to output write command status to output.log, unmark below
            #mStr=self.shell_cmd("dd if=/dev/zero bs=512 count=1 2>&1   |tr \\\\000 \\\\%s 2>/dev/null |nvme io-passthru %s -o 0x1 -n %s -l 512 -w --cdw10=%s --cdw11=%s 2>&1 | tee >> output.log"%(oct_val, self.dev, nsid, cdw10, cdw11))
            mStr=self.shell_cmd("dd if=/dev/zero bs=512 count=1 2>&1   |tr \\\\000 \\\\%s 2>/dev/null |nvme io-passthru %s -o 0x1 -n %s -l 512 -w --cdw10=%s --cdw11=%s 2>&1"%(oct_val, self.dev, nsid, cdw10, cdw11))
            #retCommandSueess=bool(re.search("NVMe command result:00000000", mStr))
            '''
            retCommandSueess=bool(re.search("ABORT_REQ", mStr))          
            if retCommandSueess==True:
                self.Print ("%s, abort at block %s" %(mStr,block))
            '''
        else:
            return False            
            
        
        return True   
    def nvme_write_blocks(self, value, sb, nob):
        # value, value to write        
        # sb, start block   
        # nob, number of block to write
        # ex, sb=0, nob=4, write 0, 1, 2, 3 blocks
        i=0
        while i<nob: 
            if self.nvme_write_1_block(value, sb+i):
                i=i+1
        
    def nvme_write_multi_thread(self, thread, sbk, bkperthr,value):
        #ex, nvme_write_multi_thread(2, 100, 200, 0x54)
        # thread0 write 200 blocks from 100th block
        # thread1 write 200 blocks from 300th block
        # total write (thread x  bkperthr)=2 x 200=400 blocks from 100th block to 500th block
        # ---------------------------------------
        # thread,  number of threads 
        # sbl,  start block 
        # bkperthr,  block per threads 
        # value,  value to write
        # ---------------------------------------
        # return thread can using following statement to check if all process is finished or not in main program
        #    mThreads=nvme_write_multi_thread(2, 100, 200, 0x54)
        #    for process in mThreads:
        #        process.join()  
        
        thread_w=thread
        block_w=bkperthr             
        RetThreads = []        
        for i in range(thread_w):                
            t = threading.Thread(target = self.nvme_write_blocks, args=(value, sbk+block_w*i, block_w,))
            t.start() 
            RetThreads.append(t)     
        return RetThreads
    
        
    def GetAllLbaf(self):
    # return LBAF[[0, MS, LBADS, RP], [1, MS, LBADS, RP].. ,[15, MS, LBADS, RP]] , all value is interger
        buf=self.shell_cmd(" nvme id-ns %s 2>&1"%(self.dev))
        LBAFs=[]
        for i in range(16):
            #LBA Format Data Structure
            # LFDS = [LBA Format, MS, LBADS, RP]
            LFDS=[]
            MS=0
            LBADS=0
            RP=0      
            
            # get LFDS
            try:
                mStr="lbaf\s+%s\s.+ms:(\d+).+lbads:(\d+).+rp:(\d+)"%i
                if re.search(mStr, buf):
                    MS=int(re.search(mStr, buf).group(1))
                    LBADS=int(re.search(mStr, buf).group(2))
                    RP=int(re.search(mStr, buf).group(3))           
            except Exception as error:        
                self.Print ("Got exception at LBAF%s"%i   )
             
            LFDS.extend([i, MS, LBADS, RP])
            LBAFs.append(LFDS)
        
        return LBAFs
    
    def ResetNS(self):
    # Reset all namespaces to namespace 1 and kill other namespaces"
        nn=self.IdCtrl.NN.int
        TNVMCAP=self.IdCtrl.TNVMCAP.int
        TotalBlocks=TNVMCAP/512
        
        for i in range(1, nn+1):        
            # delete NS
            #if self.ns_exist(i):
            self.DeleteNs(i)    
        self.shell_cmd("nvme reset %s"%self.dev_port)      
        # Create namespaces=1, and attach it
        i=1    
        sleep(0.2)
        CreatedNSID=self.CreateNs(TotalBlocks)        
        if CreatedNSID != i:
            self.Print ("create namespace error!"    )
            return False  
        else:            
            sleep(0.2)
            self.AttachNs(i)
            sleep(0.2)
            self.shell_cmd("  nvme reset %s " % (self.dev_port)) 
            sleep(1)
            return self.dev_exist() # if device exist, return true, else false                        
            
               
    def CreateMultiNs(self, NumOfNS=8, SizeInBlock=2097152):        
        # Create namespcaes form nsid 1 to nsid 8(default), size 1G(default), and attach to the controller
        # return MaxNs, ex, MaxNs=8, indicate the NS from 1 to 8
        # check if controller supports the Namespace Management and Namespace Attachment commands or not
        NsSupported=True if self.IdCtrl.OACS.bit(3)=="1" else False
        NN=self.IdCtrl.NN.int
        if not NsSupported:
            self.Print ("controller don't supports the Namespace Management and Namespace Attachment commands, quit")
            return 1
        else:
            #self.Print ("controller supports the Namespace Management and Namespace Attachment commands"            )
            # set max test namespace <=8(default)
            MaxNs=NumOfNS if NN>NumOfNS else NN
            self.Print(  "create namespcaes form nsid 1 to nsid %s, size 1G, and attach to the controller"%MaxNs )
            error=0            
            for i in range(1, NN+1):        
                # delete NS
                self.DeleteNs(i)    
            self.shell_cmd("nvme reset %s"%self.dev_port)           
            # Create namespaces, and attach it
            for i in range(1, MaxNs+1):
                sleep(0.2)
                CreatedNSID=self.CreateNs(SizeInBlock)        
                if CreatedNSID != i:
                    self.Print ("create namespace error!"    )
                    error=1
                    break
                else:
                    sleep(0.2)
                    self.AttachNs(i)
                    sleep(0.2)            
                    self.shell_cmd("  nvme reset %s " % (self.dev_port))     
                    
            # if creat ns error          
            if error==1:
                self.Print(  "create namespcaes Fail, reset to namespaces 1" ,"w")
                self.ResetNS()
                MaxNs=1
 
            return MaxNs

    def IsOpcodeSupported(self, CMDType, opcode):
        if self.IdCtrl.LPA.bit(1)=="1":
            return True if self.CSAEL(CMDType, opcode, "CSUPP")>=1 else False
        else:
            return True
        
    def IsCommandSupported(self, CMDType, opcode, LogPageID=0):
        # CMDType = "admin", "io"
        
        # get log command-Changed Namespace List
        if CMDType=="admin" and opcode==2 and (LogPageID==0x04):
            return True if self.IdCtrl.OAES.bit(8)=="1" else False   

        # get log command-Commands Supported and Effects
        elif CMDType=="admin" and opcode==2 and LogPageID==0x05:
            return True if self.IdCtrl.LPA.bit(1) == "1" else False
     
        # get log command-Device Self-test
        elif CMDType=="admin" and opcode==2 and LogPageID==0x06:
            return True if self.IdCtrl.OACS.bit(4) == "1" else False       
            
        # get log command-Telemetry Host-Initiated
        elif CMDType=="admin" and opcode==2 and LogPageID==0x7:
            return True if self.IdCtrl.LPA.bit(3)=="1" else False
        
        # get log command-Telemetry Controller-Initiated
        elif CMDType=="admin" and opcode==2 and LogPageID==0x8:
            return True if self.IdCtrl.LPA.bit(3)=="1" else False
        
        # get log command-reservation notification
        elif CMDType=="admin" and opcode==2 and LogPageID==0x80:
            return True if self.IdCtrl.ONCS.bit(5)=="1" else False
            
        # get log command-Sanitize Status
        elif CMDType=="admin" and opcode==2 and LogPageID==0x81:
            return True if int(self.IdCtrl.SANICAP.bit(2,0))>0 else False
            
        # others 
        else:
            return self.IsOpcodeSupported(CMDType, opcode)       
    


    def PrintInfo(self):
        self.Print ("")
        self.Print ("    =====================")
        self.Print ("    *ScriptName : %s"%self.ScriptName)
        self.Print ("    *Author : %s"%self.Author)
        self.Print ("    *Version : %s"%self.Version )
        self.Print ("    ====================="     )
        
        self.Print ("")
        self.Print ("  Sub Case list ---------------------------------")
        # print Descriptions
        cnt=1
        for SubCaseNum in range(1, self.SubCaseMaxNum+1):
            if self.IsMethodOverride("SubCase%s"%SubCaseNum):                
                
                # get subcase content
                Description=self.GetAbstractFunctionOrVariable(SubCaseNum, "description")
                self.Print ("  %s) %s"%(cnt, Description))
                cnt=cnt+1
        self.Print ("  End Sub Case list -------------------------------"     )
        self.Print (""    )
        
    def GetBlockSize(self):
        # get current block size, i.e. 512, 4096(4k) .. etc.
        Now_FLBAS=self.IdNs.FLBAS.int  
        Now_FLBAS_bit4 = 1 if (Now_FLBAS&0x10)>0 else 0  
        Now_LBAFinUse=self.IdNs.LBAFinUse
        Now_MS=Now_LBAFinUse[1]
        Now_LBADS=Now_LBAFinUse[2]   
        # if metadata is transferred at the end of the data LBA, e.g. Now_FLBAS_bit4 = 1
        if Now_FLBAS_bit4==0:                    
            sizePerBlock=512*pow(2,(Now_LBADS-9))
        else:            
            sizePerBlock=512*pow(2,(Now_LBADS-9)) + Now_MS        
        return sizePerBlock
        
    def MaxNLBofCDW12(self):   
        # ret maximum value of Number of Logical Blocks (NLB) in current format 
        return self.MDTSinByte/self.GetBlockSize()-1
            
            
    def WaitSanitizeFinish(self, timeout):
        # wait for recently sanitize finish
        per = self.GetLog.SanitizeStatus.SPROG
        if per != 65535:
            #self.Print ("Wait sanitize operation finish if there is a sanitize operation is currently in progress(Time out = %s)"%timeout)                       
            finish=True           
            WaitCnt=0
            while per != 65535:                
                per = self.GetLog.SanitizeStatus.SPROG
                WaitCnt = WaitCnt +1
                if WaitCnt ==timeout:
                    finish=False
                    break
                sleep(1)   
            if not finish: return False
        return True


# ==============================================================    
class DevWakeUpAllTheTime():
# make device wake up all the time
# issue compare command to make it wake up
# Usage:
#    DWUATT=DevWakeUpAllTheTime(mNVME)
#    DWUATT.Start()  
#    DWUATT.Stop()  

    def __init__(self, nvme):
        self._NVME = nvme
        self._Start = 0
        
    def _Read(self):
        while self._Start == 1:
            CMD="nvme read %s -s 0 -z 256000 -c 499  2>&1 >/dev/null "%self._NVME.dev         
            self._NVME.shell_cmd(CMD)            
                    
    def Start(self):
        self._Start = 1
        self._Thread = threading.Thread(target = self._Read)  
        self._Thread.start() 
            
    def Stop(self):    
        self._Start = 0
        sleep(0.2)










    
    
    
    
    
    
    
    
    
