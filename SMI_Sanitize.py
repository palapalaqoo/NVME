#!/usr/bin/env python
# -*- coding: utf-8 -*-

        #=======================================================================
        # abstract  function
        #     SubCase1() to SubCase32()                            :Override it for sub case 1 to sub case32
        # abstract  variables
        #     SubCase1Desc to SubCase32Desc                 :Override it for sub case 1 description to sub case32 description
        #     SubCase1Keyword to SubCase32Keyword    :Override it for sub case 1 keyword to sub case32 keyword
        #     self.ScriptName, self.Author, self.Version      :self.ScriptName, self.Author, self.Version
        #=======================================================================     
        
# Import python built-ins
import sys
import time
from time import sleep
import threading
import re
from random import randint

# Import VCT modules
from lib_vct.NVME import NVME
from lib_vct.Flow.Sanitize import FlowSanitizeMode, FlowSanitizeStatus

class SMI_Sanitize(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_Sanitize.py"
    Author = "Sam Chan"
    Version = "20210324"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
  
    

    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def Block0IsEqual(self, value, nsid=1):
        # check if block 0 is equal pattern or not
        return self.fio_isequal(0, self.OneBlockSize, value, nsid, self.OneBlockSize)
    
    def SendTestCommand(self, *args): 
        global CMD_Result
        
    
        
        CMDType=args[0]
        Opcode=args[1]
        LogPageID=args[2]
        
        
            
        
        if CMDType == "admin":
            if Opcode==0x2:
                CMD="nvme admin-passthru %s -opcode=%s --cdw10=%s -r -l 16 2>&1 | sed '2,$d' "%(self.dev, Opcode, LogPageID)
                CMD_Result = self.shell_cmd(CMD)   
            elif Opcode==0xC:          # Asynchronous              
                # create thread for asynchronous_event_request_cmd        
                t = threading.Thread(target = self.asynchronous_event_request_cmd)
                t.start()        
                sleep(0.5)   
                self.nvme_reset()        
                t.join(10)
            else:  
                CMD="nvme admin-passthru %s -opcode=%s 2>&1"%(self.dev, Opcode)
                CMD_Result = self.shell_cmd(CMD)
        elif CMDType == "io":
            CMD="nvme io-passthru %s -opcode=%s 2>&1"%(self.dev, Opcode)
            CMD_Result = self.shell_cmd(CMD)
    
    def StartTestFlowSanitize(self, CMDType, Opcode, ExpectedResult, LogPageID=0):  
            self.Flow.Sanitize.ShowProgress=False   
            self.Flow.Sanitize.SetEventTrigger(self.SendTestCommand, CMDType, Opcode, LogPageID)
            self.Flow.Sanitize.SetOptions("-a %s"%self.SANACT)
            # 0< Threshold <65535
            self.Flow.Sanitize.Mode=FlowSanitizeMode.KeepSanitizeInProgress
            Status = self.Flow.Sanitize.Start()
            # if error
            if Status != FlowSanitizeStatus.Success:
                if Status==FlowSanitizeStatus.CommandError:
                    self.Print("Sanitize status: CommandError", "f")
                if Status==FlowSanitizeStatus.ExceptionOccured:
                    self.Print("Sanitize status: ExceptionOccured", "f")
                if Status==FlowSanitizeStatus.TimeOut:
                    self.Print("Sanitize status: TimeOut", "f")
                if Status==FlowSanitizeStatus.SprogCountError:
                    self.Print("Sanitize status: SprogCountError", "f")                                    
                if Status==FlowSanitizeStatus.OverWriteCompletedPassesCountCountError:
                    self.Print("Sanitize status: OverWriteCompletedPassesCountCountError", "f")
                #if Status==FlowSanitizeStatus.SanitizeGoFinishAfterEventTriger: implement at hot reset
                    #self.Print("Sanitize status: SanitizeGoFinishAfterEventTriger", "f")               
            
            
            
    
    def TestCommandAllowed(self, CMDType, Opcode, ExpectedResult, LogPageID=0):  
    # CMDType:  admin or io
    # ExpectedResult: Deny or Allow
        global ret_code
        
        if not self.IsCommandSupported(CMDType, Opcode, LogPageID):
            self.Print( "Command is not supported, test if controller is working after command!", "w")
            # start the test
            self.StartTestFlowSanitize(CMDType, Opcode, ExpectedResult, LogPageID)
            # print result
            self.Print ("Returned Status: %s"%CMD_Result)
            if self.dev_alive:
                self.Print("PASS", "p")  
            else:
                self.Print("Fail, device is missing", "f")
                self.Print("Exist all the test!", "f")
                self.Print (""    )
                ret_code=1
                self.Print ("ret_code:%s"%ret_code)
                self.Print ("Finish")
                sys.exit(ret_code)                             
            self.Print ("")
        else:    
            # start the test
            self.StartTestFlowSanitize(CMDType, Opcode, ExpectedResult, LogPageID)        
            # print result
            self.Print ("Returned Status: %s"%CMD_Result)
            if re.search("SANITIZE_IN_PROGRESS", CMD_Result) and ExpectedResult=="Deny":
                self.Print("Expected command Deny: PASS", "p")  
            elif not re.search("SANITIZE_IN_PROGRESS", CMD_Result) and ExpectedResult=="Allow":
                self.Print("Expected command Allow: PASS", "p")  
            else:
                self.Print("Expected command %s: Fail"%ExpectedResult, "f")
                ret_code=1    
            self.Print (""    )
    
    def GetErrorLog(self):
        global ErrorLog
        ErrorLog = self.get_log2byte(0x1, 64)
    
    def GetErrorInfoWhileSanitizeInProgress(self):    
        self.Flow.Sanitize.ShowProgress=False   
        self.Flow.Sanitize.SetEventTrigger(self.GetErrorLog)
        self.Flow.Sanitize.SetOptions("-a %s"%self.SANACT)
        # 0< Threshold <65535
        self.Flow.Sanitize.SetEventTriggerThreshold(100)
        self.Flow.Sanitize.Start()
        
    def WaitSanitizeOperationFinish(self, timeout=600, printInfo=False):
    # WaitSanitizeOperationFinish, if finish, then return true, else false(  after timeout )         
        if printInfo:
            self.Print ("")
            self.Print ("Wait sanitize operation finish if there is a sanitize operation is currently in progress(Time out = %s)"%timeout)
                        
        per = self.GetLog.SanitizeStatus.SPROG
        finish=True
        if per != 65535:
            # self.Print("The most recent sanitize operation is currently in progress, waiting the operation finish(Time out = 120s)", "w")
            WaitCnt=0
            while per != 65535:
                #print ("Sanitize Progress: %s"%per)
                per = self.GetLog.SanitizeStatus.SPROG
                WaitCnt = WaitCnt +1
                if WaitCnt ==timeout:
                    #self.Print("Time out!", "f")  
                    finish=False
                    break
                sleep(1)
            #self.Print ("Recent sanitize operation was completed")
   
        if printInfo:
            if finish:
                self.Print("Done", "p")
            else:
                self.Print("Error, Time out!", "f")  
        return finish            

    def TestOverwriteMechanism(self, OIPBP=0, OWPASS=1):
        rtCode=0
        if not self.OverwriteSupport :
            rtCode=255
            self.Print ("Overwrite sanitize not supported, quit this test!")
        else:
            self.Print ("Wait sanitize operation finish if there is a sanitize operation is currently in progress(Time out = 120s)")
            if not self.WaitSanitizeOperationFinish(600):
                self.Print("Time out!, exit all test ", "f")  
                rtCode=1
            else:   
                self.Print("Done", "p")
                self.Print ("")
                self.Print ("Issue overwrite sanitize operation with Overwrite Pattern=0x5D5C5B5A OIPBP=%s, OWPASS=%s, timeout=1 hr"%(OIPBP, OWPASS))
                self.Flow.Sanitize.ShowProgress=True   
                self.Flow.Sanitize.SetEventTrigger(None)
                # CMD = "nvme admin-passthru %s --opcode=0x84 --cdw10=0x3 --cdw11=0x5D5C5B5A 2>&1"%(self.dev, self.SANACT)  
                OPT = "--sanact=3  --ovrpat=0x5D5C5B5A --owpass=%s"%OWPASS
                OPT = OPT if OIPBP==0 else OPT + " --oipbp"
                self.Flow.Sanitize.SetOptions(OPT)
                self.Flow.Sanitize.Mode=FlowSanitizeMode.Normal
                self.Flow.Sanitize.TimeOut=3600
                FlowStatus = self.Flow.Sanitize.Start()       
                CompletedPassesCount = self.Flow.Sanitize.Static_LastOWCPC
                if FlowStatus!=0:
                    self.Print("Fail, FlowStatus: %s"%FlowStatus, "f")

                self.Print ("Done")
                self.Print ("")
                self.Print ("Check if data is 0x5D5C5B5A in first 1G spaces")
                if self.fio_isequal(offset=0, size="1G", pattern=0x5D5C5B5A):
                    self.Print("Pass", "p")
                else:
                    self.Print("Fail, data from SSD as below", "f")
                    mStr = self.shell_cmd("hexdump %s -n 200M | head"%self.dev)
                    self.Print (mStr)
                    rtCode=1           

                self.Print ("")
                self.Print ("Check if Completed Passes Counter in Sanitize Status (SSTAT) is working")
                self.Print ("CompletedPassesCount: %s"%CompletedPassesCount)
                expectedCPC = 0 if OWPASS==0 else (OWPASS-1)
                if CompletedPassesCount == expectedCPC and FlowStatus!=FlowSanitizeStatus.OverWriteCompletedPassesCountCountError:
                    self.Print("Pass", "p")
                else:
                    self.Print("Fail", "f")
                    rtCode=1            
        return rtCode 

    def TestBlockEraseMechanism(self):
        rtCode=0
        if not self.BlockEraseSupport :
            rtCode=255
            self.Print ("Block Erase sanitize not supported, quit this test!")
        else:
            self.Print ("Wait sanitize operation finish if there is a sanitize operation is currently in progress(Time out = 120s)")
            if not self.WaitSanitizeOperationFinish(600):
                self.Print("Time out!, exit all test ", "f")  
                rtCode=1
            else:   
                self.Print("Done", "p")
                self.Print ("")
                
                TestPatten=randint(1, 0xFF)
                self.Print ("Write data to the front, middle and back spaces of the LBA")
                self.Print ("e.g. %s, %s and %s, size 1G, value = %s"%(hex(self.start_SB*self.OneBlockSize), hex(self.middle_SB*self.OneBlockSize), hex(self.last_SB*self.OneBlockSize), hex(TestPatten)))
                self.write_SML_data(TestPatten, "1G")                
                self.Print("Done", "p")
                self.Print ("")                             
                                
                self.Print ("Issue Block Erase sanitize operation, timeout=10 minute")
                self.Flow.Sanitize.ShowProgress=True   
                self.Flow.Sanitize.SetEventTrigger(None)
                # CMD = "nvme admin-passthru %s --opcode=0x84 --cdw10=0x3 --cdw11=0x5D5C5B5A 2>&1"%(self.dev, self.SANACT)  
                OPT = "--sanact=2"
                self.Flow.Sanitize.SetOptions(OPT)
                self.Flow.Sanitize.Mode=FlowSanitizeMode.Normal
                self.Flow.Sanitize.TimeOut=360
                FlowStatus = self.Flow.Sanitize.Start()       
                if FlowStatus!=0:
                    self.Print("Fail, FlowStatus: %s"%FlowStatus, "f")

                self.Print ("Done")
                self.Print ("")
                self.Print ("Check if data is 0x0 in the front, middle and back spaces of the LBA")
                if not self.CheckLogicalBlockDataIsPass(Value = 0, ExpectedResult = "match"):
                    rtCode=1           

        return rtCode 

    def TestCryptoEraseMechanism(self):
        rtCode=0
        if not self.CryptoEraseSupport :
            rtCode=255
            self.Print ("Crypto Erase sanitize not supported, quit this test!")
        else:
            self.Print ("Wait sanitize operation finish if there is a sanitize operation is currently in progress(Time out = 120s)")
            if not self.WaitSanitizeOperationFinish(600):
                self.Print("Time out!, exit all test ", "f")  
                rtCode=1
            else:   
                self.Print("Done", "p")
                self.Print ("")
                
                TestPatten=randint(1, 0xFF)
                self.Print ("Write data to the front, middle and back spaces of the LBA")
                self.Print ("e.g. %s, %s and %s, size 1G, value = %s"%(hex(self.start_SB*self.OneBlockSize), \
                                                                       hex(self.middle_SB*self.OneBlockSize), hex(self.last_SB*self.OneBlockSize), hex(TestPatten)))
                self.write_SML_data(TestPatten, "1G")                
                self.Print("Done", "p")
                                           
                if self.TestModeOn:
                    self.Print ("")
                    self.Print ("Dump front data for inspection ")
                    mStr = self.shell_cmd("hexdump %s -n 200M | head"%self.dev)
                    self.Print (mStr)      
                               
                self.Print ("")  
                self.Print ("Issue Crypto Erase sanitize operation, timeout=10 minute")
                self.Flow.Sanitize.ShowProgress=True   
                self.Flow.Sanitize.SetEventTrigger(None)
                # CMD = "nvme admin-passthru %s --opcode=0x84 --cdw10=0x3 --cdw11=0x5D5C5B5A 2>&1"%(self.dev, self.SANACT)  
                OPT = "--sanact=4"
                self.Flow.Sanitize.SetOptions(OPT)
                self.Flow.Sanitize.Mode=FlowSanitizeMode.Normal
                self.Flow.Sanitize.TimeOut=360
                FlowStatus = self.Flow.Sanitize.Start()       
                if FlowStatus!=0:
                    self.Print("Fail, FlowStatus: %s"%FlowStatus, "f")

                self.Print ("Done", "p")
                self.Print ("")
                self.Print ("Check if data is not %s in the front, middle and back spaces of the LBA"%hex(TestPatten))
                if not self.CheckLogicalBlockDataIsPass(Value = TestPatten, ExpectedResult = "dismatch"):
                    rtCode=1           
                '''
                self.Print ("")
                self.Print ("Check if data is not 0x0 in the front, middle and back spaces of the LBA")
                if not self.CheckLogicalBlockDataIsPass(Value = 0, ExpectedResult = "dismatch"):
                    rtCode=1
                '''    
                self.Print ("")
                self.Print ("Dump front data for inspection ")
                mStr = self.shell_cmd("hexdump %s -n 200M | head"%self.dev)
                self.Print (mStr)                
                  
                    
        return rtCode 
    
    def CheckLogicalBlockDataIsPass(self, Value, ExpectedResult="match"):
        mPass=True
        ExpectMatch = True if ExpectedResult=="match" else False
        if self.fio_isequal(offset=self.start_SB*self.OneBlockSize, size="1G", pattern=Value) == ExpectMatch:
            self.Print("Front: Pass", "p")
        else:
            self.Print("Front: Fail, data from SSD as below", "f")
            CMD = "hexdump %s -n 200M -s %s| head"%(self.dev, self.start_SB*self.OneBlockSize)
            self.Print (CMD)
            mStr = self.shell_cmd(CMD)            
            self.Print (mStr, "w")
            mPass=False

        if self.fio_isequal(offset=self.middle_SB*self.OneBlockSize, size="1G", pattern=Value) == ExpectMatch:
            self.Print("Middle: Pass", "p")
        else:
            self.Print("Middle: Fail, data from SSD as below", "f")
            CMD="hexdump %s -n 200M -s %s| head"%(self.dev, self.middle_SB*self.OneBlockSize)
            self.Print (CMD)
            mStr = self.shell_cmd(CMD)            
            self.Print (mStr, "w")
            mPass=False

        if self.fio_isequal(offset=self.last_SB*self.OneBlockSize, size="1G", pattern=Value) == ExpectMatch:
            self.Print("Back: Pass", "p")
        else:
            self.Print("Back: Fail, data from SSD as below", "f")
            CMD="hexdump %s -n 200M -s %s| head"%(self.dev, self.last_SB*self.OneBlockSize)
            self.Print (CMD)
            mStr = self.shell_cmd(CMD)
            self.Print (mStr, "w")
            mPass=False
        
        return mPass    
                      
        
    # override PreTest()

    def WaitSanitizeOperationFinishWithTimer(self, timeout=600):
    # WaitSanitizeOperationFinish, use real timer to check timeout and show progress        
                        
        per = self.GetLog.SanitizeStatus.SPROG
        if per != 65535:
            # self.Print("The most recent sanitize operation is currently in progress, waiting the operation finish(Time out = 120s)", "w")
            self.timer.start()
            while True:
                #print ("Sanitize Progress: %s"%per)
                per = self.GetLog.SanitizeStatus.SPROG
                self.PrintProgressBar(per, 65535, "SPROG: %s"%per)
                if per==65535:
                    return True

                if int(float(self.timer.time)) >=timeout: 
                    return False                    

        return True       

    def TestFlow12(self, TestSize, Scale):
        self.SetPrintOffset(4)
        value = randint(0x1, 0xFF)              
        self.Print("1. prewrite(fio sequential write, fio_bs=64k, pattern=0x%X) 10%% of full disk as background data"%value)
        self.fio_write(offset=0, size=TestSize, pattern=value, fio_bs="64k", showProgress=True)
        self.Print("") 
        self.Print("2. comparecheck background data to confirm data are successfully written")
        if self.fio_isequal(offset=0, size=TestSize, pattern=value, fio_bs="64k"):
            self.Print("Data compare pass!", "p")
        else:
            self.Print("Data compare fail!, quit", "f")
            return False
        
        self.Print("")        
        self.SANACT=2
        CMD = "nvme admin-passthru %s --opcode=0x84 --cdw10=%s 2>&1"%(self.dev, self.SANACT)  
        self.Print ("3. issue Sanitize block erase cmd: %s"%CMD) 
        self.shell_cmd(CMD)   
        self.Print("") 
        self.Print("4. check if sanitize is in progress(SPROG change), if SPROG has not changed in 60s, fail the test")
        WaitCnt = 0
        per=0
        while True:
            per = self.GetLog.SanitizeStatus.SPROG
            if per!=0 and per!=65535:
                break;
            else:
                WaitCnt = WaitCnt+1
            if WaitCnt>60:
                self.Print("Time out!, SPROG never changed, exit all test ", "f")  
                return False   
            sleep(1)             
        self.Print("Sanitize is in progress now, SPROG= %s"%per)
    

        self.Print("") 

        self.Print("5. issue asyc power off and on when SPROG > %s"%(Scale))         
        while True:
            per = self.GetLog.SanitizeStatus.SPROG
            self.PrintProgressBar(per, 65535, "SPROG: %s"%per)     
            if per>Scale:
                break;    
                               
        self.Print("") 
        self.Print("powering off ..") 
        self.Print("")   
        if not self.spor_reset(sleep_time=0):
            self.Print("6. power on fail, can not find device: %s, quit!"%self.dev, "f")  
            return False
        self.Print("6. power on now")  
        
        self.Print("")        
        self.Print("7. check sanitize command completed, timeout 600s")
        if not self.WaitSanitizeOperationFinishWithTimer(600):
            self.Print("Time out!, exit all test ", "f")  
            return False 
        self.Print("Sanitize command was completed")
        
        self.Print("")        
        self.Print("8. comparecheck background data (pattern 0)")    
        if self.fio_isequal(offset=0, size=TestSize, pattern=0x0, fio_bs="64k"):
            self.Print("Data compare pass!", "p")
        else:
            self.Print("Data compare fail!, quit", "f")
            return False  
        
        self.SetPrintOffset(0)
        return True


    def TestJiraSmi213(self):
        if not self.BlockEraseSupport :
            self.Print("Block Erase not Support, skip")
            return 255
        
        TNOB = self.GetTotalNumberOfBlock()
        TestNLB = int((TNOB*self.prewriteSize)/8)*8
        TestSize=TestNLB*self.OneBlockSize
        self.Print("Total number of blocks: %s"%TNOB)
        self.Print("Test size of blocks: %s(%s%% of total blocks)"%(TestNLB, int(self.prewriteSize*100)))
        self.Print("Test size: %s bytes(Test size of blocks*%s)"%(TestSize, self.OneBlockSize))
        self.Print("Test loop: %s"%self.loops)        
        
        for loop in range(self.loops):
            self.Print("")
                
            if self.sprogScale==0:
                Scale = randint(1, 65534)  
                self.Print("loop: %s, do spor at SPROG: %s"%(loop, Scale), "b")
                if not self.TestFlow12(TestSize, Scale):
                    return 1   
                self.Print("")             
            else:                
                cycle=0
                Scale = self.sprogScale
                while True: 
                    self.Print("loop: %s, cycle: %s, do spor at SPROG: %s"%(loop, cycle, Scale), "b")
                    if not self.TestFlow12(TestSize, Scale):
                        return 1  
                    
                    self.Print("")
                    cycle = cycle+1
                    Scale = Scale + self.sprogScale   
                    if Scale>65534:
                        break                       
        return 0        
    
    def PreTest(self):
        self.Print ("")
        self.Print ("Check if the controller supports the Write Uncorrectable command or not in identify - ONCS")   
        self.WriteUncSupported=self.IdCtrl.ONCS.bit(1)    
        self.WriteUncSupported=True if self.WriteUncSupported=="1" else False
        self.Print ("Write Uncorrectable command supported", "p") if self.WriteUncSupported else self.Print ("Write Uncorrectable command not supported", "f")        
        self.Print ("")               
        
        self.Print ("Check Sanitize Capabilities (SANICAP)")
        self.Print("Crypto Erase sanitize operation is Supported", "p")  if self.CryptoEraseSupport else self.Print("Crypto Erase sanitize operation is not Supported", "f") 
        self.Print("Block Erase sanitize operation is Supported", "p")  if self.BlockEraseSupport else self.Print("Block Erase sanitize operation is not Supported", "f") 
        self.Print("Overwrite sanitize operation is Supported", "p")  if self.OverwriteSupport else self.Print("Overwrite sanitize operation is not Supported", "f") 
        
        if self.SANACT==0:
            self.Print("All sanitize operation is not supported, quit the test!","w")
            self.Print (""    )
            return 255
        
        self.Print ("")
        self.Print ("Wait sanitize operation finish if there is a sanitize operation is currently in progress(Time out = 120s)")
        if self.WaitSanitizeOperationFinish(600):
            self.Print("Done", "p")
        else:
            self.Print("Time out!, exit all test ", "f")  
            return False
        
        if self.TestModeOn:
            return True
        
        self.Print ("Write 10G data, star LBA=0x0, value = 0x7C"    )
        self.fio_write(offset=0, size="10G", pattern="0x7C", showProgress=True)
        self.Print ("Done")
        
        return True        
        
    def VerifyDeallocateAfterSaitize(self):
        self.Print ("Issue Sanitize command with block operation and 'No Deallocate After Sanitize=1'", "b")
        self.SANACT=2
        CMD = "nvme admin-passthru %s --opcode=0x84 --cdw10=%s -d 2>&1"%(self.dev, self.SANACT)  
        self.Print ("Command: %s"%CMD)                     
        mStr, sc=self.shell_cmd_with_sc(CMD)
        self.Print ("Get return code: %s"%mStr)
        self.Print ("Check return code is success or not, expected SUCCESS")
        if sc==0:
            self.Print("PASS", "p")  
        else:
            self.Print("Fail", "f")
            return False 
        
        if not self.WaitSanitizeOperationFinish(timeout=600, printInfo=True): return 1
        self.Print("Done")
        self.Print("")
        SSTAT = self.GetLog.SanitizeStatus.SSTAT
        self.Print("Current SSTAT: 0x%X"%SSTAT)
        self.Print ("Check if bits [2:0] of SSTAT is 100b" )
        self.Print("i.e. The most recent sanitize operation for which No-Deallocate After Sanitize")
        self.Print("was requested has completed successfully with deallocation of all logical blocks")
        if (SSTAT & 0b111) ==4:  
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            return False  
        return True      
        
    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    def SetNODRM(self, valueIn):
        self.Print("Issue set feature command to set No-Deallocate Response Mode (NODRM) to %s"%valueIn)  
        self.set_feature(fid=0x17, value=valueIn)
        value, sc = self.GetFeatureValueWithSC(fid=0x17)
        if sc!=0:
            self.Print("Get feature fail, return code: %s"%(value), "f")
            return False
        else:
            self.Print("Get feature value: %s"%(value))
            if value!=0:
                self.Print("Set feature fail", "f")
                return False
        return True        

    def __init__(self, argv):
        self.SetDynamicArgs(optionName="l", optionNameFull="testLoop", helpMsg="for case 12, test Loop, default=1", argType=int) 
        self.SetDynamicArgs(optionName="z", optionNameFull="prewriteSize", helpMsg="for case 12, test Size, default=0.1 means 10%% prewriteSize,"\
                            " ex, prewrite 20%% capacity of SSD, -z 0.2", argType=str) 
  
        self.SetDynamicArgs(optionName="scale", optionNameFull="sprogScale", helpMsg="for case 12, sprog Scale, default=0 "\
                            "every loop will have several cycles to verify the function with specific spor timer.   \n"\
                            "script will do spor as SPROG> sprogScale and SPROG> sprogScale*2 and so on. \n"\
                            "ex, python SMI_Sanitize_JIRASMI213.py /dev/nvme0n1 -scale 1000, will do spor as SPROG>1000 at first cycle \n"\
                            "and will do spor as SPROG>2000 at second cycle until last cycle to do spor as SPROG>65000, then finish the loop \n"\
                            "it also means it will do int(65536/1000) = 65 cycle test for 1 loop \n"\
                            "if sprogScale not set, spor timer will be random in 1 to 65534 to do spor ", argType=int)     
        
        VersionDefine = ["1.3c", "1.3d", "1.4", "dellx16"]
        VersionDdfault = VersionDefine[0]
        self.SetDynamicArgs(optionName="v", optionNameFull="version", \
                            helpMsg="nvme spec version, %s, default= %s, ex. '-v %s'"%(VersionDefine, VersionDdfault, VersionDdfault), argType=str, default=VersionDdfault)
                     
        
        # initial parent class
        super(SMI_Sanitize, self).__init__(argv)
        
        self.loops = self.GetDynamicArgs(0)  
        self.loops=1 if self.loops==None else self.loops   
        
        self.prewriteSize = self.GetDynamicArgs(1)  
        self.prewriteSize=0.1 if self.prewriteSize==None else float(self.prewriteSize)   
        
        self.sprogScale = self.GetDynamicArgs(2)  
        self.sprogScale=0 if self.sprogScale==None else self.sprogScale  
        
        self.specVer = self.GetDynamicArgs(3)
        if not self.specVer in VersionDefine:   # if input is not in VersionDefine, e.g keyin wrong version
            self.specVer = VersionDdfault        
        
        self.CryptoEraseSupport = True if (self.IdCtrl.SANICAP.bit(0) == "1") else False
        self.BlockEraseSupport = True if (self.IdCtrl.SANICAP.bit(1) == "1") else False
        self.OverwriteSupport = True if (self.IdCtrl.SANICAP.bit(2) == "1") else False
        
        if self.BlockEraseSupport:
            self.SANACT=2
        elif self.CryptoEraseSupport:
            self.SANACT=4
        elif self.OverwriteSupport:
            self.SANACT=3
        else:
            self.SANACT=0
            
        self.OneBlockSize = self.GetBlockSize()
        
    # <sub item scripts>  
    SubCase1TimeOut = 1000
    SubCase1Desc = "Test Command Completion Queue"      
    def SubCase1(self):
        ret_code=0
        self.Print ("When the command is complete, the controller shall post a completion queue entry to the ")
        self.Print ("Admin Completion Queue indicating the status for the command.")
        self.Print ("")
        
        # Sanitize command 
        #CMD="nvme sanitize %s %s 2>&1"%(self.dev_port, "-a %s"%self.SANACT)  
        CMD = "nvme admin-passthru %s --opcode=0x84 --cdw10=%s 2>&1"%(self.dev, self.SANACT)  
        self.Print ("Issue sanitize command: %s"%CMD)
                     
        mStr=self.shell_cmd(CMD)
        self.Print ("Get return code: %s"%mStr)
        self.Print ("Check return code is success or not, expected SUCCESS")
        if re.search("NVMe command result:00000000", mStr):
            self.Print("PASS", "p")  
        else:
            self.Print("Fail", "f")
            ret_code=1 
        
        self.WaitSanitizeOperationFinish(timeout=600, printInfo=True)
        return ret_code
    
    SubCase2TimeOut = 1000
    SubCase2Desc = "Test if only process the Admin commands listed in Figure 287"    
    def SubCase2(self):
        self.Print ("Test While a sanitize operation is in progress")
        self.Print ("Shall only process the Admin commands listed in Figure 287"       )

        ret_code=0
        self.Print ("")
        
        self.Print ("Delete I/O Submission Queue")
        self.TestCommandAllowed("admin", 0x0, "Allow")
        
        self.Print ("Create I/O Submission Queue")
        self.TestCommandAllowed("admin", 0x1, "Allow")          
        
        self.Print ("Get Log Page - Error Information")
        self.TestCommandAllowed("admin", 0x2, "Allow", 0x1)  
        
        self.Print ("Get Log Page - SMART / Health Information")
        self.TestCommandAllowed("admin", 0x2, "Allow", 0x2)  
        
        self.Print ("Get Log Page - Firmware Slot Information")
        self.TestCommandAllowed("admin", 0x2, "Deny", 0x3)  
        
        self.Print ("Get Log Page - Changed Namespace List")
        self.TestCommandAllowed("admin", 0x2, "Allow", 0x4)  
        
        self.Print ("Get Log Page - Commands Supported and Effects")
        self.TestCommandAllowed("admin", 0x2, "Deny", 0x5)  
        
        self.Print ("Get Log Page - Device Self-test")
        self.TestCommandAllowed("admin", 0x2, "Deny", 0x6)  
        
        self.Print ("Get Log Page - Telemetry Host-Initiated")
        self.TestCommandAllowed("admin", 0x2, "Deny", 0x7)  
        
        self.Print ("Get Log Page - Telemetry Controller-Initiated")
        self.TestCommandAllowed("admin", 0x2, "Deny", 0x8)  
        
        self.Print ("Get Log Page - Reservation Notification")
        self.TestCommandAllowed("admin", 0x2, "Allow", 0x80)  
        
        self.Print ("Get Log Page - Sanitize Status")
        self.TestCommandAllowed("admin", 0x2, "Allow", 0x81)  
        
        self.Print ("Delete I/O Completion Queue")
        self.TestCommandAllowed("admin", 0x4, "Allow")   
        
        self.Print ("Create I/O Completion Queue")
        self.TestCommandAllowed("admin", 0x5, "Allow")   
        
        self.Print ("Identify")
        self.TestCommandAllowed("admin", 0x6, "Allow")   
        
        self.Print ("Abort")
        self.TestCommandAllowed("admin", 0x8, "Allow")  
         
        self.Print ("Set Features")
        self.TestCommandAllowed("admin", 0x9, "Allow")   
        
        self.Print ("Get Features")
        self.TestCommandAllowed("admin", 0xA, "Allow")   
        
        self.Print ("Asynchronous Event Request")
        self.TestCommandAllowed("admin", 0xC, "Allow")  
        
        self.Print ("Namespace Management")
        self.TestCommandAllowed("admin", 0xD, "Deny")  
        
        self.Print ("Firmware Commit")
        self.TestCommandAllowed("admin", 0x10, "Deny")  
        
        self.Print ("Firmware Image Download")
        self.TestCommandAllowed("admin", 0x11, "Deny")  
        
        self.Print ("Device Self-test")
        self.TestCommandAllowed("admin", 0x14, "Deny")  
        
        self.Print ("Namespace Attachment")
        self.TestCommandAllowed("admin", 0x15, "Deny")  
        
        self.Print ("Keep Alive")
        self.TestCommandAllowed("admin", 0x18, "Allow")  
        
        self.Print ("Directive Send")
        self.TestCommandAllowed("admin", 0x19, "Deny")  
        
        self.Print ("Directive Receive")
        self.TestCommandAllowed("admin", 0x1A, "Deny")  
        
        self.Print ("Virtualization Management")
        self.TestCommandAllowed("admin", 0x1C, "Deny")  
        
        self.Print ("NVMe-MI Send")
        self.TestCommandAllowed("admin", 0x1D, "Deny")  
        
        self.Print ("NVMe-MI Receive")
        self.TestCommandAllowed("admin", 0xE, "Deny")  
        
        self.Print ("Doorbell Buffer Config")
        self.TestCommandAllowed("admin", 0x7C, "Deny")  
        
        self.Print ("Format NVM")
        self.TestCommandAllowed("admin", 0x80, "Deny")  
        
        self.Print ("Security Send")
        self.TestCommandAllowed("admin", 0x81, "Deny")  
        
        self.Print ("Security Receive")
        self.TestCommandAllowed("admin", 0x82, "Deny")  
        
        self.Print ("Sanitize")
        self.TestCommandAllowed("admin", 0x84, "Deny")            

        
        self.WaitSanitizeOperationFinish(timeout=600, printInfo=True)
        return ret_code
    
    SubCase3TimeOut = 1000
    SubCase3Desc = "Test All I/O Commands shall be aborted"    
    def SubCase3(self):
        self.Print ("Test While a sanitize operation is in progress")
        self.Print ("All I/O Commands shall be aborted with a status of Sanitize In Progress"        )
        self.Print ("")
        ret_code=0
        
        self.Print ("Flush")
        self.TestCommandAllowed("io", 0x0, "Deny")
        
        self.Print ("Write")
        self.TestCommandAllowed("io", 0x1, "Deny")
        
        self.Print ("Read")
        self.TestCommandAllowed("io", 0x2, "Deny")
        
        self.Print ("Write Uncorrectable")
        self.TestCommandAllowed("io", 0x4, "Deny")
        
        self.Print ("Compare")
        self.TestCommandAllowed("io", 0x5, "Deny")
        
        self.Print ("Write Zeroes")
        self.TestCommandAllowed("io", 0x8, "Deny")
        
        self.Print ("Dataset Management")
        self.TestCommandAllowed("io", 0x9, "Deny")
        
        self.Print ("Reservation Register")
        self.TestCommandAllowed("io", 0xD, "Deny")
        
        self.Print ("Reservation Report")
        self.TestCommandAllowed("io", 0xE, "Deny")
        
        self.Print ("Reservation Acquire")
        self.TestCommandAllowed("io", 0x11, "Deny")
        
        self.Print ("Reservation Release")
        self.TestCommandAllowed("io", 0x15, "Deny")

        self.WaitSanitizeOperationFinish(timeout=600, printInfo=True)
        return ret_code
            
    SubCase4TimeOut = 1000
    SubCase4Desc = "Test if controller return zeros in the LBA field for get Error log command"    
    def SubCase4(self):    
        self.Print ("Test While a sanitize operation is in progress and check if controller return zeros in the LBA field for get Error Information log command")
        ret_code=0   
        self.Print ("")
        self.Print ("Write Uncorrectable Supported", "p") if self.WriteUncSupported else self.Print ("Write Uncorrectable Not Supported, skip", "f")
        if not self.WriteUncSupported: return 255
        
        self.Print ("Create Error Information by reading uncorrectable block")
        self.Print ("Set uncorrectable block, start block=0, block count=127")
        self.write_unc(SLB=0, BlockCnt=127)
        
        self.Print ("Generate error log by reading uncorrectable block where is 5th block")
        self.shell_cmd("  buf=$(nvme read %s -s 5 -z 1024 -c 1 2>&1 > /dev/null) "%(self.dev)) 
        
        self.Print ("Check if error log was created with 0x5 in LBA field or not")
        self.GetErrorLog()
        LBA = int(ErrorLog[16])
        self.Print ("LBA Field: %s"%LBA)
        
        if LBA==5:
            self.Print("PASS", "p")         
        else:
            self.Print("Fail: create Error log fail", "f")
            ret_code=1    
        
        if LBA==5:
            self.Print ("")
            self.Print ("Read error log and check if Return zeros in the LBA field or not while sanitize in progress" )
            self.GetErrorInfoWhileSanitizeInProgress()
            LBA = int(ErrorLog[16])
            self.Print ("LBA Field: %s"%LBA)
            
            if LBA==0:
                self.Print("PASS", "p")  
            else:
                self.Print("Fail", "f")
                ret_code=1    
                
        self.WaitSanitizeOperationFinish(timeout=600, printInfo=True)  
        return ret_code

    SubCase5TimeOut = 1000
    SubCase5Desc = "Test hot reset while sanitize operation is in progress"    
    def SubCase5(self):    
        self.Print ("Test Issue hot reset while a sanitize operation is in progress, and check if controller resume the sanitize operation after reset or not")
        ret_code=0   
        
        self.Print ("")
        self.Print ("Wait sanitize operation finish if there is a sanitize operation is currently in progress(Time out = 120s)")
        if not self.WaitSanitizeOperationFinish(600):
            self.Print("Time out!, exit all test ", "f")  
            ret_code=1
        else:   
            self.Print("Done", "p")
            self.Print ("")
            self.Print ("Start to test hot reset while Sanitize Progress(SPROG)>=0x1FFF, Time out=120s"     )
            self.Flow.Sanitize.ShowProgress=True   
            self.Flow.Sanitize.SetEventTrigger(self.link_reset)
            self.Flow.Sanitize.SetOptions("-a %s"%self.SANACT)
            # 0< Threshold <65535
            self.Flow.Sanitize.SetEventTriggerThreshold(0x1FFF)      
            self.Flow.Sanitize.Mode=FlowSanitizeMode.Normal
            self.Flow.Sanitize.TimeOut=120
            Status = self.Flow.Sanitize.Start()       
            
            if  Status==FlowSanitizeStatus.Success:
                self.Print("Pass", "p")
            elif Status==FlowSanitizeStatus.SanitizeGoFinishAfterEventTriger:
                self.Print("Sanitize status: After hot reset, Sprog = 0xFFFF(It may not continues after a Controller Level Reset ) ", "w")                
            else:
                if Status==FlowSanitizeStatus.CommandError:
                    self.Print("Sanitize status: CommandError", "f")
                if Status==FlowSanitizeStatus.ExceptionOccured:
                    self.Print("Sanitize status: ExceptionOccured", "f")
                if Status==FlowSanitizeStatus.TimeOut:
                    self.Print("Sanitize status: TimeOut", "f")
                if Status==FlowSanitizeStatus.SprogCountError:
                    self.Print("Sanitize status: SprogCountError", "f")                                    
                if Status==FlowSanitizeStatus.OverWriteCompletedPassesCountCountError:
                    self.Print("Sanitize status: OverWriteCompletedPassesCountCountError", "f")                      
                
                self.Print("Fail", "f")
                self.Print ("Do POR(power off reset) to reset controller")
                self.por_reset()
                ret_code=1

                
        self.WaitSanitizeOperationFinish(timeout=600, printInfo=True)
        return ret_code    
    
    SubCase6TimeOut = 1000
    SubCase6Desc = "Test Get Log Page - Sanitize Status Log"    
    def SubCase6(self):    

        ret_code=0           
        self.Print ("")
        self.Print ("Wait sanitize operation finish if there is a sanitize operation is currently in progress(Time out = 120s)")
        if not self.WaitSanitizeOperationFinish(600):
            self.Print("Time out!, exit all test ", "f")  
            ret_code=1
        else:   
            self.Print("Done", "p")
            self.Print ("")
            self.Print ("Issue sanitize command"     )
            self.Flow.Sanitize.ShowProgress=True   
            self.Flow.Sanitize.SetEventTrigger(None)
            self.Flow.Sanitize.SetOptions("-a %s"%self.SANACT)
            # 0< Threshold <65535   
            self.Flow.Sanitize.Mode=FlowSanitizeMode.Normal
            self.Flow.Sanitize.TimeOut=120
            FlowStatus = self.Flow.Sanitize.Start()       
            
            self.Print ("")
            self.Print ("Check if SPROG was counting from 0 to 0xFFFF"                )
            if  FlowStatus!=2:
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")
                ret_code=1

            self.Print ("")
            self.Print ("Check if SSTAT is 0x1(The most recent sanitize operation completed successfully)  " )
            if self.GetLog.SanitizeStatus.SSTAT & 0x1 > 0:  
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")
                ret_code=1 

            self.Print ("")
            self.Print ("Check if GlobalDataErased = 1 after sanitize"             )
            if self.GetLog.SanitizeStatus.SSTAT & 0x0100 >0:  
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")
                ret_code=1

            self.Print ("")
            self.Print ("Check if SCDW10 is equal to the Command Dword 10 field of the Sanitize command" )
            self.Print ("Expect value: %s"%self.SANACT            )
            if self.GetLog.SanitizeStatus.SCDW10 ==self.SANACT:  
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")
                ret_code=1
                
        self.WaitSanitizeOperationFinish(timeout=600, printInfo=True)        
        return ret_code    

    # timeout 1.1hr
    SubCase7TimeOut = (4000)
    SubCase7Desc = "Test Logical Block Data - Overwrite sanitize operation, OIPBP=0, OWPASS=1"      
    def SubCase7(self):
        self.Print("")
        ret_code=self.TestOverwriteMechanism(OIPBP=0, OWPASS=1)      
        self.WaitSanitizeOperationFinish(timeout=600, printInfo=True)
        return ret_code
            
    # timeout 1.1hr
    SubCase8TimeOut = (4000)
    SubCase8Desc = "Test Logical Block Data - Overwrite sanitize operation, OIPBP=1, OWPASS=1"      
    def SubCase8(self):
        self.Print("")
        ret_code=self.TestOverwriteMechanism(OIPBP=1, OWPASS=1)      
        self.WaitSanitizeOperationFinish(timeout=600, printInfo=True)
        return ret_code

    # timeout 1.1hr
    SubCase9TimeOut = (4000)
    SubCase9Desc = "Test Logical Block Data - Overwrite sanitize operation, OIPBP=1, OWPASS=2"      
    def SubCase9(self):
        self.Print("")
        ret_code=self.TestOverwriteMechanism(OIPBP=1, OWPASS=2)      
        self.WaitSanitizeOperationFinish(timeout=600, printInfo=True)
        return ret_code
        
    SubCase10TimeOut = (4000)
    SubCase10Desc = "Test Logical Block Data - Block Erase sanitize operation"      
    def SubCase10(self):
        self.Print("")
        ret_code=self.TestBlockEraseMechanism()      
        self.WaitSanitizeOperationFinish(timeout=600, printInfo=True)
        return ret_code

    SubCase11TimeOut = (4000)
    SubCase11Desc = "Test Logical Block Data - Crypto Erase sanitize operation"      
    def SubCase11(self):
        self.Print("")
        ret_code=self.TestCryptoEraseMechanism()     
        self.WaitSanitizeOperationFinish(timeout=600, printInfo=True)
        return ret_code

    SubCase12TimeOut = (4000)
    SubCase12Desc = "Test sanitize with spor(JIRA VCTDEPT-213)"  
    def SubCase12(self):
        self.Print("")
        ret_code=self.TestJiraSmi213()     
        self.WaitSanitizeOperationFinish(timeout=600, printInfo=True)
        return ret_code

    SubCase13TimeOut = 1000
    SubCase13Desc = "Test if CPU go sleep when sanitize is in progress"      
    def SubCase13(self):
        self.Print ("When sanitize is in progress, the controller shall not go sleep.")    
        self.Print ("")
        self.Print ("1. Get sanitize operation time usage as device CPU awake all the time(TimeUsageAwake)", "b")
        CMD = "nvme admin-passthru %s --opcode=0x84 --cdw10=%s 2>&1"%(self.dev, self.SANACT)  
        self.Print ("Issue sanitize command: %s"%CMD)      
        mStr, SC=self.shell_cmd_with_sc(CMD) 
        if SC!=0:
            self.Print ("Command fail, return sataus code: %s"%SC, "f")
            return 1
        else:
            self.Print ("Command success with sataus code = 0", "p")
            self.timer.start()
            self.Print ("Wait for SPROG >=1 ..")
            while True:
                per = self.GetLog.SanitizeStatus.SPROG
                if per>=1:
                    break
            self.Print ("Current SPROG=%s now."%per)
            self.Print ("Issue get log page command every 5 ms for sanitize log(SPROG) to make CPU awake all the time untill sanitize finish")
            per_last=0
            while per != 65535: #print ("Sanitize Progress: %s"%per)
                per = self.GetLog.SanitizeStatus.SPROG
                sleep(0.005) #self.Print ("Recent sanitize operation was completed")
                if per!=per_last:
                    self.PrintProgressBar(per, 65535, "", "SPROG: %s"%per)
                    per_last=per

            TimeUsageAwake = int(float(self.timer.time))
            self.Print ("Sanitize finish")
            self.Print ("Sanitize time usage for CPU awake all the time(TimeUsageAwake): %s seconds"%TimeUsageAwake)      
            if TimeUsageAwake<10:
                    self.Print ("TimeUsageAwake < 10, no need to check this test", "p")
                    return 0
            # ---------------------------------------------------------------------------------------
            self.Print ("")
            self.Print ("2. Get sanitize operation time usage as device CPU may sleep all the time", "b")
            self.Print ("Issue sanitize command: %s"%CMD)      
            mStr, SC=self.shell_cmd_with_sc(CMD) 
            if SC!=0:
                self.Print ("Command fail, return sataus code: %s"%SC, "f")
                return 1
            else:
                self.Print ("Command success with sataus code = 0", "p")
                self.timer.start()
                self.Print ("Wait for SPROG >=1 ..")
                while True:
                    per = self.GetLog.SanitizeStatus.SPROG
                    if per>=1:
                        break
                self.Print ("Current SPROG=%s now."%per)                
                self.Print ("Wait  %s seconds (TimeUsageAwake)"%TimeUsageAwake)
                per = 0                
                while True:
                    sleep(1)
                    self.PrintProgressBar(per, TimeUsageAwake, "", "time: %s"%per)                    
                    if per == TimeUsageAwake: break
                    per=per + 1 
              
                                
                
                
                self.Print ("Issue get log page command and check if SPROG=65535(sanitize finish)")
                per = self.GetLog.SanitizeStatus.SPROG
                self.Print ("Current SPROG: %s"%per)
                
                if per==65535:
                    self.Print ("Sanitize finish, time usage was <= TimeUsageAwake", "p")
                    return 0
                else:
                    self.Print ("Sanitize has not finished")
                    self.Print ("Issue get log page command every 5 ms for sanitize log(SPROG) to make CPU awake all the time untill sanitize finish")
                    self.Print ("If sanitize operation finish in TimeUsageAwake*1.1, then pass, else fail")
                    timeLimit = TimeUsageAwake * 1.1
                    self.Print ("E.g. %s seconds"%timeLimit)
                     
                    per_last = 0
                    while per != 65535: #print ("Sanitize Progress: %s"%per)
                        per = self.GetLog.SanitizeStatus.SPROG
                        sleep(0.005) #self.Print ("Recent sanitize operation was completed")
                        if per!=per_last:
                            self.PrintProgressBar(per, 65535, "", "SPROG: %s"%per)
                            per_last=per  
                            
                        timeUsage1 = int(float(self.timer.time))
                        self.Print ("Sanitize finish")
                        self.Print ("Sanitize time usage %s seconds"%timeUsage1)       
                        self.Print ("Check if time usage <= TimeUsageAwake(%s s)"%TimeUsageAwake) 
                        if timeUsage1<=(TimeUsageAwake*1.1):
                            self.Print ("Pass", "p")
                            return 0
                        else:
                            self.Print ("Fail", "f")
                            return 1

    SubCase14TimeOut = 60
    SubCase14Desc = "NVMe Spec1.3d: test get log command - Log Page Offset"        
    def SubCase14(self):
        ret_code=0
        if self.specVer!="1.3d":
            self.Print( "Current target spec version = %s, please rerun with '-v 1.3d' for NVMe Spec1.3d"%self.specVer,"w")
            return 0

        supportsExtendedEata = True if self.IdCtrl.LPA.bit(2)=="1" else False
        if supportsExtendedEata:
            self.Print( "Controller supports the Log Page Offset in IdCtrl.LPA.bit(2)", "p")
        else:
            self.Print( "Controller don't supports the Log Page Offset in IdCtrl.LPA.bit(2), skip", "w")
            return 0
                
        ret_code = 0 if self.VerifyGetLogWithOffset(LogID=0x81 , ByteOffset=8) else 1
        

        return ret_code 

    SubCase15TimeOut = 800
    SubCase15Desc = "Compare command with block sanitize"        
    def SubCase15(self):
        self.Print ("1.    Get and check Identify Controller Data Structure info", "b")
        self.Print ("Check if the controller supports the Compare command or not in identify - ONCS")   
        CMDSupported=self.IdCtrl.ONCS.bit(0)    
        CMDSupported=True if CMDSupported=="1" else False
        self.Print ("Compare command supported") if CMDSupported else self.Print ("Compare command not supported, skip")
        
        if not CMDSupported: 
            return 0
        
        
        if self.SANACT!=2:
            self.Print ("Block Erase sanitize not supported, skip!")
            return 0
        else:
            self.Print ("Block Erase sanitize supported")
            
        
        self.Print ("")
        self.Print ("Write 0x5A to first 10M data")
        self.fio_write(offset = 0, size = "10M", pattern = 0x5A)
        if self.fio_isequal(offset = 0, size = "10M", pattern = 0x5A):
            self.Print ("Write and verify first 10M data: pass", "p")   
        else:     
            self.Print ("Write and verify first 10M data: fail", "f") 
            return 1
        
        self.Print("")        
        self.Print ("2.    Issue Sanitize command with block operation, ause:0, no deallocate:0", "b")
        self.SANACT=2
        CMD = "nvme admin-passthru %s --opcode=0x84 --cdw10=%s 2>&1"%(self.dev, self.SANACT)  
        self.Print ("Issue block erase sanitize, command: %s"%CMD)                     
        mStr, sc=self.shell_cmd_with_sc(CMD)
        self.Print ("Get return code: %s"%mStr)
        self.Print ("Check return code is success or not, expected SUCCESS")
        if sc==0:
            self.Print("PASS", "p")  
        else:
            self.Print("Fail", "f")
            ret_code=1
            return 1 
        
        #self.Print ("Wait sanitize finish, timeout 600s")
        if not self.WaitSanitizeOperationFinish(timeout=600, printInfo=True): return 1
        
        self.Print("") 
        self.Print ("3.    After sanitize operation completed, issue compare command with data buffer set to 0", "b")
        OneBlockSize = self.GetBlockSize()
        CMD = "dd if=/dev/zero bs=%s count=1 2>&1 | nvme compare %s  -s 0 -z %s -c 0 2>&1"%(OneBlockSize, self.dev, OneBlockSize)
        self.Print ("Issue command to compare first block: %s"%CMD)
        mStr, sc=self.shell_cmd_with_sc(CMD)
        self.Print("Return status: %s"%mStr)
        self.Print("Check if compare command success")
        if sc==0:
            self.Print("Pass", "p") 
        else:
            self.Print("Fail", "f") 
            
        self.Print("")        
        CMD = "hexdump %s -n %s"%(self.dev, OneBlockSize)
        self.Print ("Issue command to read(hexdump) first block: %s"%CMD)
        mStr, sc=self.shell_cmd_with_sc(CMD)   
        self.Print(mStr)  
        return 0
    

    SubCase16TimeOut = 6000
    SubCase16Desc = "NVMe Spec1.4: test 'No Deallocate After Sanitize', NODMMAS, NDI"        
    def SubCase16(self):
        ret_code=0
        if self.specVer!="1.4":
            self.Print( "Current target spec version = %s, please rerun with '-v 1.4' for NVMe Spec1.4"%self.specVer,"w")
            return 0

        SANICAP = self.IdCtrl.SANICAP.int
        self.Print( "SANICAP: %s"%SANICAP )
        NODMMAS = (SANICAP>>30)&0b11 #bit 31:30
        self.Print( "No-Deallocate Modifies Media After Sanitize (NODMMAS): %s"%NODMMAS )
        NDI = (SANICAP>>29)&0b1 #bit 29
        self.Print( "No-Deallocate Inhibited (NDI): %s"%NDI )
        if self.SANACT!=2:
            self.Print ("Block Erase sanitize not supported, skip!")
            return 0
        else:
            self.Print ("Block Erase sanitize supported")        
        
        # TODO
        NODMMAS=2        
        
        
        self.Print("")
        self.Print("1) Verify when NODMMAS=10b, NID=1 and 'No Deallocate After Sanitize=1', sanitize CMD must success")
        self.Print("    And bits [2:0] of Sanitize Status (SSTAT) in Sanitize log must equal to 100b")
        if NODMMAS!=2:
            self.Print("NODMMAS !=10b , skip ")
        elif NDI!=0:
            self.Print("NDI !=0 , skip ")
        else:
            self.Print("")    
            self.SetPrintOffset(4)    
            if not self.VerifyDeallocateAfterSaitize(): return 1
            self.SetPrintOffset(0)        

        self.Print("")
        self.Print("2) Verify when NODMMAS=10b, NID=1, 'No Deallocate After Sanitize=1' and NODRM=1, sanitize CMD must success")
        self.Print("    And bits [2:0] of Sanitize Status (SSTAT) in Sanitize log must equal to 100b")
        self.Print("    Note: If NID set to ‘1’ and the No-Deallocate Response Mode bit is set to ‘1’")
        self.Print("    then the controller deallocates after the sanitize operation even if the No-Deallocate After Sanitize bit is set to ‘1’ in a Sanitize command.")
        if NODMMAS!=2:
            self.Print("NODMMAS !=10b , skip ")
        elif NDI!=1:
            self.Print("NDI !=1 , skip ")
        else:
            self.Print("")    
            self.SetPrintOffset(4)    
            if not self.SetNODRM(1): return 1
            if not self.VerifyDeallocateAfterSaitize(): return 1
            self.SetPrintOffset(0) 
        
        self.Print("")
        self.Print("3) Verify when NODMMAS=10b, NID=1, 'No Deallocate After Sanitize=1' and NODRM=0, sanitize CMD must fail with status = 'Invalid Field'")
        if NODMMAS!=2:
            self.Print("NODMMAS !=10b , skip ")
        elif NDI!=1:
            self.Print("NDI !=1 , skip ")
        else:
            self.Print("")    
            self.SetPrintOffset(4)  
            if not self.SetNODRM(0): return 1                
            self.Print("")       
            self.Print ("Issue Sanitize command with block operation and 'No Deallocate After Sanitize=1'", "b")
            self.SANACT=2
            CMD = "nvme admin-passthru %s --opcode=0x84 --cdw10=%s -d 2>&1"%(self.dev, self.SANACT)  
            self.Print ("Command: %s"%CMD)                     
            mStr, sc=self.shell_cmd_with_sc(CMD)
            self.Print ("Get return code: %s"%mStr)
            self.Print ("Check return code is success or not, expected = 0x2(Invalid Field)")
            if sc==0x2:
                self.Print("PASS", "p")  
            else:
                self.Print("Fail", "f")
                return 1 
            self.SetPrintOffset(0)                 

        self.Print("")
        self.Print("")
        

        return ret_code        
        
    SubCase17TimeOut = 6000
    SubCase17Desc = "DELL: No Deallocate After Sanitize shall not be supported"        
    def SubCase17(self):
        ret_code=0
        if self.specVer!="dellx16":
            self.Print( "Current target spec version = %s, please rerun with '-v dellx16' for Dell"%self.specVer,"w")
            return 0 
                 
        SANICAP = self.IdCtrl.SANICAP.int
        self.Print( "SANICAP: %s"%SANICAP )
        NODMMAS = (SANICAP>>30)&0b11 #bit 31:30
        self.Print( "No-Deallocate Modifies Media After Sanitize (NODMMAS): %s"%NODMMAS )
        NDI = (SANICAP>>29)&0b1 #bit 29
        self.Print( "No-Deallocate Inhibited (NDI): %s"%NDI )
        if self.SANACT!=2:
            self.Print ("Block Erase sanitize not supported, skip!")
            return 0
        else:
            self.Print ("Block Erase sanitize supported")  
        self.Print ("If No Deallocate After Sanitize is not supported, NDI will be set to 1")
        self.Print ("1) Check if No-Deallocate Inhibited (NDI) set to 1 for DELL")
        if NDI!=1:
            self.Print ("Fail!", "f")
            return 0
        else:
            self.Print ("Pass", "p")          
                                   

        self.Print("")
        self.Print("2) Verify when NODMMAS=10b, NID=1, 'No Deallocate After Sanitize=1' and NODRM=1, sanitize CMD must success")
        self.Print("    And bits [2:0] of Sanitize Status (SSTAT) in Sanitize log must equal to 100b")
        self.Print("    Note: If NID set to ‘1’ and the No-Deallocate Response Mode bit is set to ‘1’")
        self.Print("    then the controller deallocates after the sanitize operation even if the No-Deallocate After Sanitize bit is set to ‘1’ in a Sanitize command.")
        if NODMMAS!=2:
            self.Print("NODMMAS !=10b , skip ")
        elif NDI!=1:
            self.Print("NDI !=1 , skip ")
        else:
            self.Print("")    
            self.SetPrintOffset(4)    
            if not self.SetNODRM(1): return 1
            if not self.VerifyDeallocateAfterSaitize(): return 1
            self.SetPrintOffset(0) 
        
        self.Print("")
        self.Print("3) Verify when NODMMAS=10b, NID=1, 'No Deallocate After Sanitize=1' and NODRM=0, sanitize CMD must fail with status = 'Invalid Field'")
        if NODMMAS!=2:
            self.Print("NODMMAS !=10b , skip ")
        elif NDI!=1:
            self.Print("NDI !=1 , skip ")
        else:
            self.Print("")    
            self.SetPrintOffset(4)  
            if not self.SetNODRM(0): return 1                
            self.Print("")       
            self.Print ("Issue Sanitize command with block operation and 'No Deallocate After Sanitize=1'", "b")
            self.SANACT=2
            CMD = "nvme admin-passthru %s --opcode=0x84 --cdw10=%s -d 2>&1"%(self.dev, self.SANACT)  
            self.Print ("Command: %s"%CMD)                     
            mStr, sc=self.shell_cmd_with_sc(CMD)
            self.Print ("Get return code: %s"%mStr)
            self.Print ("Check return code is success or not, expected = 0x2(Invalid Field)")
            if sc==0x2:
                self.Print("PASS", "p")  
            else:
                self.Print("Fail", "f")
                return 1 
            self.SetPrintOffset(0)                 

        self.Print("")
        self.Print("")        

    SubCase18TimeOut = (4000)
    SubCase18Desc = "[Read only mode] Test Logical Block Data - Overwrite sanitize operation, OIPBP=0, OWPASS=1"      
    def SubCase18(self):
        self.Print ("Verify sanitize in Read only mode ")
        if not self.mIKNOWWHATIAMDOING:
            self.Print ("Please run script with option '-iknowwhatiamdoing', it will make DUT into RO mode")
            return 0        
        self.Print ("Issue VU CMD to set DUT in Read only mode ")
        if not self.setReadOnlyMode(): return 1
        self.Print ("Done")
        return self.SubCase7()

            
    # timeout 1.1hr
    SubCase19TimeOut = (4000)
    SubCase19Desc = "[Read only mode] Test Logical Block Data - Overwrite sanitize operation, OIPBP=1, OWPASS=1"      
    def SubCase19(self):
        self.Print ("Verify sanitize in Read only mode ")
        if not self.mIKNOWWHATIAMDOING:
            self.Print ("Please run script with option '-iknowwhatiamdoing', it will make DUT into RO mode")
            return 0        
        self.Print ("Issue VU CMD to set DUT in Read only mode ")
        if not self.setReadOnlyMode(): return 1
        self.Print ("Done")
        return self.SubCase8()

    # timeout 1.1hr
    SubCase20TimeOut = (4000)
    SubCase20Desc = "[Read only mode] Test Logical Block Data - Overwrite sanitize operation, OIPBP=1, OWPASS=2"      
    def SubCase20(self):
        self.Print ("Verify sanitize in Read only mode ")
        if not self.mIKNOWWHATIAMDOING:
            self.Print ("Please run script with option '-iknowwhatiamdoing', it will make DUT into RO mode")
            return 0        
        self.Print ("Issue VU CMD to set DUT in Read only mode ")
        if not self.setReadOnlyMode(): return 1
        self.Print ("Done")
        return self.SubCase9()
        
    SubCase21TimeOut = (4000)
    SubCase21Desc = "[Read only mode] Test Logical Block Data - Block Erase sanitize operation"      
    def SubCase21(self):
        self.Print ("Verify sanitize in Read only mode ")
        if not self.mIKNOWWHATIAMDOING:
            self.Print ("Please run script with option '-iknowwhatiamdoing', it will make DUT into RO mode")
            return 0        
        self.Print ("Issue VU CMD to set DUT in Read only mode ")
        if not self.setReadOnlyMode(): return 1
        self.Print ("Done")
        return self.SubCase10()

    SubCase22TimeOut = (4000)
    SubCase22Desc = "[Read only mode] Test Logical Block Data - Crypto Erase sanitize operation"      
    def SubCase22(self):
        self.Print ("Verify sanitize in Read only mode ")
        if not self.mIKNOWWHATIAMDOING:
            self.Print ("Please run script with option '-iknowwhatiamdoing', it will make DUT into RO mode")
            return 0        
        self.Print ("Issue VU CMD to set DUT in Read only mode ")
        if not self.setReadOnlyMode(): return 1
        self.Print ("Done")
        return self.SubCase11()

    # </sub item scripts> 
               
    '''
    SubCase7TimeOut = 60
    SubCase7Desc = "Test CDW10 - No Deallocate After Sanitize"      
    def SubCase7(self):
        ret_code=0
        
        DSMSupported= True if self.IdCtrl.ONCS.bit(2)="1" else False
        
        if DSMSupported:

            self.Print ("CDW10 - No Deallocate After Sanitize, If set to 1 then the controller shall not deallocate any logical blocks ")
            self.Print ("Start to deallocate the first block at nsid= 1")
            self.shell_cmd("nvme dsm %s -s 0 -b 1 -n 1 -d" % (self.device))                     
            #self.Print ("Check the value read from the first block, expected value: 0x5A")
            if self.Block0IsEqual(0x5A):
                self.Print("Done", "p")
            else:
                self.Print("Can't deallocate block 0, exit", "f")
                ret_code=1  
                return 1            
            self.Print ("")           
            CMD = "nvme admin-passthru %s --opcode=0x84 --cdw10=%s 2>&1"%(self.dev, self.SANACT)  
            self.Print ("Issue sanitize command with 'No Deallocate After Sanitize' = 0")
            self.shell_cmd(CMD)
            
            self.Print ("")
            self.Print ("Wait sanitize operation finish if there is a sanitize operation is currently in progress(Time out = 120s)")
            if self.WaitSanitizeOperationFinish(120):
                self.Print("Done", "p")
                return True
            else:
                self.Print("Time out!, exit all test ", "f")  
                return 1
            
            nvme admin-passthru /dev/nvme0n1 --opcode=0x84 --cdw10=0x3 --cdw11=0xae
        
        return ret_code
    '''
    
if __name__ == "__main__":
    DUT = SMI_Sanitize(sys.argv )     
    DUT.RunScript()
    DUT.Finish()     
    
    
    
