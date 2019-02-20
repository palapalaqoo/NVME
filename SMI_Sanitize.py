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

# Import VCT modules
from lib_vct.NVME import NVME
from lib_vct.Flow.Sanitize import FlowSanitizeMode, FlowSanitizeStatus

class SMI_Sanitize(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_Sanitize.py"
    Author = "Sam Chan"
    Version = "20181211"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
  
    

    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def Block0IsEqual(self, value, nsid=1):
        # check if block 0 is equal pattern or not
        return self.fio_isequal(0, 512, value, nsid, 512)
    
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
            self.Flow.Sanitize.Start()
    
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
        ErrorLog = self.get_log2byte(0x1, 32)
    
    def GetErrorInfoWhileSanitizeInProgress(self):    
        self.Flow.Sanitize.ShowProgress=False   
        self.Flow.Sanitize.SetEventTrigger(self.GetErrorLog)
        self.Flow.Sanitize.SetOptions("-a %s"%self.SANACT)
        # 0< Threshold <65535
        self.Flow.Sanitize.SetEventTriggerThreshold(100)
        self.Flow.Sanitize.Start()
        
    def WaitSanitizeOperationFinish(self, timeout=120):
    # WaitSanitizeOperationFinish, if finish, then return true, else false(  after timeout ) 
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
   
        return finish            

    def TestOverwriteMechanism(self, OIPBP=0, OWPASS=1):
        rtCode=0
        if not self.OverwriteSupport :
            self.Print ("Overwrite sanitize not supported, quit this test!")
        else:
            self.Print ("Wait sanitize operation finish if there is a sanitize operation is currently in progress(Time out = 120s)")
            if not self.WaitSanitizeOperationFinish(120):
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
                FlowStatus, CompletedPassesCount = self.Flow.Sanitize.Start()       
                if FlowStatus!=0:
                    self.Print("Fail, FlowStatus: %s"%FlowStatus, "f")

                self.Print ("Done")
                self.Print ("")
                self.Print ("Check if data is 0x5D5C5B5A in first 1G spaces")
                if self.fio_isequal(offset=0, size="1G", pattern=0x5D5C5B5A):
                    self.Print("Pass", "p")
                else:
                    self.Print("Fail, data pattern as below", "f")
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
        
    # override PreTest()
    def PreTest(self):
        self.Print ("Check Sanitize Capabilities (SANICAP)")
        self.Print("Crypto Erase sanitize operation is Supported", "p")  if self.CryptoEraseSupport else self.Print("Crypto Erase sanitize operation is not Supported", "f") 
        self.Print("Block Erase sanitize operation is Supported", "p")  if self.BlockEraseSupport else self.Print("Block Erase sanitize operation is not Supported", "f") 
        self.Print("Overwrite sanitize operation is Supported", "p")  if self.OverwriteSupport else self.Print("Overwrite sanitize operation is not Supported", "f") 
        
        if self.SANACT==0:
            self.Print("All sanitize operation is not supported, quit the test!","w")
            self.Print (""    )
            return False
        
        self.Print ("")
        self.Print ("Wait sanitize operation finish if there is a sanitize operation is currently in progress(Time out = 120s)")
        if self.WaitSanitizeOperationFinish(120):
            self.Print("Done", "p")
            return True
        else:
            self.Print("Time out!, exit all test ", "f")  
            return False
        
    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    def __init__(self, argv):
        # initial parent class
        super(SMI_Sanitize, self).__init__(argv)
        

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
    
              
        
    # <sub item scripts>
    SubCase1TimeOut = 60
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
        
        return ret_code
    
    SubCase2TimeOut = 180
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

        return ret_code
    
    SubCase3TimeOut = 180
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

        return ret_code
            
    SubCase4TimeOut = 60
    SubCase4Desc = "Test if controller return zeros in the LBA field for get Error log command"    
    def SubCase4(self):    
        self.Print ("Test While a sanitize operation is in progress and check if controller return zeros in the LBA field for get Error Information log command")
        ret_code=0   
        self.Print ("")
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
        return ret_code

    SubCase5TimeOut = 60
    SubCase5Desc = "Test hot reset while sanitize operation is in progress"    
    def SubCase5(self):    
        self.Print ("Test Issue hot reset while a sanitize operation is in progress, and check if controller resume the sanitize operation after reset or not")
        ret_code=0   
        
        self.Print ("")
        self.Print ("Wait sanitize operation finish if there is a sanitize operation is currently in progress(Time out = 120s)")
        if not self.WaitSanitizeOperationFinish(120):
            self.Print("Time out!, exit all test ", "f")  
            ret_code=1
        else:   
            self.Print("Done", "p")
            self.Print ("")
            self.Print ("Start to test hot reset while Sanitize Progress(SPROG)>=0x1FFF, Time out=120s"     )
            self.Flow.Sanitize.ShowProgress=True   
            self.Flow.Sanitize.SetEventTrigger(self.nvme_reset)
            self.Flow.Sanitize.SetOptions("-a %s"%self.SANACT)
            # 0< Threshold <65535
            self.Flow.Sanitize.SetEventTriggerThreshold(0x1FFF)      
            self.Flow.Sanitize.Mode=FlowSanitizeMode.Normal
            self.Flow.Sanitize.TimeOut=120
            FlowStatus = self.Flow.Sanitize.Start()       
            
            if  FlowStatus==0:
                self.Print("Pass", "p")
            elif FlowStatus==2:
                self.Print("Fail", "f")
                self.Print ("Do POR(power off reset) to reset controller")
                self.por_reset()
                ret_code=1
            else:
                self.Print("Pass", "p")

        return ret_code    
    
    SubCase6TimeOut = 60
    SubCase6Desc = "Test Get Log Page – Sanitize Status Log"    
    def SubCase6(self):    

        ret_code=0           
        self.Print ("")
        self.Print ("Wait sanitize operation finish if there is a sanitize operation is currently in progress(Time out = 120s)")
        if not self.WaitSanitizeOperationFinish(120):
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
                
        return ret_code    

    # timeout 1.1hr
    SubCase7TimeOut = (4000)
    SubCase7Desc = "Test Overwrite sanitize operation - OIPBP=0, OWPASS=1"      
    def SubCase7(self):
        self.Print("")
        ret_code=self.TestOverwriteMechanism(OIPBP=0, OWPASS=1)      

        return ret_code
            
    # timeout 1.1hr
    SubCase8TimeOut = (4000)
    SubCase8Desc = "Test Overwrite sanitize operation - OIPBP=1, OWPASS=1"      
    def SubCase8(self):
        self.Print("")
        ret_code=self.TestOverwriteMechanism(OIPBP=1, OWPASS=1)      

        return ret_code

    # timeout 1.1hr
    SubCase9TimeOut = (4000)
    SubCase9Desc = "Test Overwrite sanitize operation - OIPBP=1, OWPASS=2"      
    def SubCase9(self):
        self.Print("")
        ret_code=self.TestOverwriteMechanism(OIPBP=1, OWPASS=2)      

        return ret_code
        
    # </sub item scripts>    
    '''
    SubCase7TimeOut = 60
    SubCase7Desc = "Test CDW10 - No Deallocate After Sanitize"      
    def SubCase7(self):
        ret_code=0
        
        DSMSupported= True if self.IdCtrl.ONCS.bit(2)="1" else False
        
        if DSMSupported:

            self.Print ("CDW10 - No Deallocate After Sanitize, If set to ‘1’ then the controller shall not deallocate any logical blocks ")
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
    
    
    
