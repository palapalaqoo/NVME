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
from lib_vct.Flow.Sanitize import FlowSanitizeMode

class SMI_Sanitize(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_Sanitize.py"
    Author = "Sam Chan"
    Version = "20181211"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    SubCase1TimeOut = 60
    SubCase1Desc = "Test Command Completion Queue"    
    
    SubCase2TimeOut = 180
    SubCase2Desc = "Test if only process the Admin commands listed in Figure 287"

    SubCase3TimeOut = 180
    SubCase3Desc = "Test All I/O Commands shall be aborted"    

    SubCase4TimeOut = 60
    SubCase4Desc = "Test if controller return zeros in the LBA field for get Error log"    


    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

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
            print "Returned Status: %s"%CMD_Result
            if self.dev_alive:
                self.Print("PASS", "p")  
            else:
                self.Print("Fail, device is missing", "f")
                self.Print("Exist all the test!", "f")
                print ""    
                ret_code=1
                print "ret_code:%s"%ret_code
                print "Finish"
                sys.exit(ret_code)                             
            print ""
        else:    
            # start the test
            self.StartTestFlowSanitize(CMDType, Opcode, ExpectedResult, LogPageID)        
            # print result
            print "Returned Status: %s"%CMD_Result
            if re.search("SANITIZE_IN_PROGRESS", CMD_Result) and ExpectedResult=="Deny":
                self.Print("Expected command Deny: PASS", "p")  
            elif not re.search("SANITIZE_IN_PROGRESS", CMD_Result) and ExpectedResult=="Allow":
                self.Print("Expected command Allow: PASS", "p")  
            else:
                self.Print("Expected command %s: Fail"%ExpectedResult, "f")
                ret_code=1    
            print ""    
    
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
        
    # override PreTest()
    def PreTest(self):
        ret_code=0
        print "Check Sanitize Capabilities (SANICAP)"
        self.Print("Crypto Erase sanitize operation is Supported", "p")  if self.CryptoEraseSupport else self.Print("Crypto Erase sanitize operation is not Supported", "f") 
        self.Print("Block Erase sanitize operation is Supported", "p")  if self.BlockEraseSupport else self.Print("Block Erase sanitize operation is not Supported", "f") 
        self.Print("Overwrite sanitize operation is Supported", "p")  if self.OverwriteSupport else self.Print("Overwrite sanitize operation is not Supported", "f") 
        
        if self.SANACT==0:
            self.Print("Any sanitize operation is not supported, quit the test!","w")
            print ""    
            ret_code =255
            return ret_code
        
        print ""
        print "Check if there is any sanitize operation in progress or not"
        per = self.GetLog.SanitizeStatus.SPROG
        if per != 65535:
            self.Print("The most recent sanitize operation is currently in progress, waiting the operation finish(Time out = 120s)", "w")
            WaitCnt=0
            while per != 65535:
                print ("Sanitize Progress: %s"%per)
                per = self.GetLog.SanitizeStatus.SPROG
                WaitCnt = WaitCnt +1
                if WaitCnt ==120:
                    print ""
                    self.Print("Time out!, exit all test ", "f")  
                    ret_code =1
                    return ret_code
                sleep(1)
            print "Recent sanitize operation was completed"
        else:
            print "All sanitize operation was completed"      
        return True if ret_code==0 else False
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
    def SubCase1(self):
        ret_code=0
        print "When the command is complete, the controller shall post a completion queue entry to the "
        print "Admin Completion Queue indicating the status for the command."
        print ""
        
        # Sanitize command 
        CMD="nvme sanitize %s %s 2>&1"%(self.dev_port, "-a %s"%self.SANACT)  
        print "Issue sanitize command: %s"%CMD
                     
        mStr=self.shell_cmd(CMD)
        print "Get return code: %s"%mStr
        print "Check return code is success or not, expected SUCCESS"
        if re.search("SUCCESS", mStr):
            self.Print("PASS", "p")  
        else:
            self.Print("Fail", "f")
            ret_code=1 
        return ret_code
    
    def SubCase2(self):
        print "Test While a sanitize operation is in progress"
        print "Shall only process the Admin commands listed in Figure 287"       

        ret_code=0
        print ""

        print "Delete I/O Submission Queue"
        self.TestCommandAllowed("admin", 0x0, "Allow")
        
        print "Create I/O Submission Queue"
        self.TestCommandAllowed("admin", 0x1, "Allow")          
        
        print "Get Log Page - Error Information"
        self.TestCommandAllowed("admin", 0x2, "Allow", 0x1)  
        
        print "Get Log Page - SMART / Health Information"
        self.TestCommandAllowed("admin", 0x2, "Allow", 0x2)  
        
        print "Get Log Page - Firmware Slot Information"
        self.TestCommandAllowed("admin", 0x2, "Deny", 0x3)  
        
        print "Get Log Page - Changed Namespace List"
        self.TestCommandAllowed("admin", 0x2, "Allow", 0x4)  
        
        print "Get Log Page - Commands Supported and Effects"
        self.TestCommandAllowed("admin", 0x2, "Deny", 0x5)  
        
        print "Get Log Page - Device Self-test"
        self.TestCommandAllowed("admin", 0x2, "Deny", 0x6)  
        
        print "Get Log Page - Telemetry Host-Initiated"
        self.TestCommandAllowed("admin", 0x2, "Deny", 0x7)  
        
        print "Get Log Page - Telemetry Controller-Initiated"
        self.TestCommandAllowed("admin", 0x2, "Deny", 0x8)  
        
        print "Get Log Page - Reservation Notification"
        self.TestCommandAllowed("admin", 0x2, "Allow", 0x80)  
        
        print "Get Log Page - Sanitize Status"
        self.TestCommandAllowed("admin", 0x2, "Allow", 0x81)  
        
        print "Delete I/O Completion Queue"
        self.TestCommandAllowed("admin", 0x4, "Allow")   
        
        print "Create I/O Completion Queue"
        self.TestCommandAllowed("admin", 0x5, "Allow")   
        
        print "Identify"
        self.TestCommandAllowed("admin", 0x6, "Allow")   
        
        print "Abort"
        self.TestCommandAllowed("admin", 0x8, "Allow")  
         
        print "Set Features"
        self.TestCommandAllowed("admin", 0x9, "Allow")   
        
        print "Get Features"
        self.TestCommandAllowed("admin", 0xA, "Allow")   
        
        print "Asynchronous Event Request"
        self.TestCommandAllowed("admin", 0xC, "Allow")  
        
        print "Namespace Management"
        self.TestCommandAllowed("admin", 0xD, "Deny")  
        
        print "Firmware Commit"
        self.TestCommandAllowed("admin", 0x10, "Deny")  
        
        print "Firmware Image Download"
        self.TestCommandAllowed("admin", 0x11, "Deny")  
        
        print "Device Self-test"
        self.TestCommandAllowed("admin", 0x14, "Deny")  
        
        print "Namespace Attachment"
        self.TestCommandAllowed("admin", 0x15, "Deny")  
        
        print "Keep Alive"
        self.TestCommandAllowed("admin", 0x18, "Allow")  
        
        print "Directive Send"
        self.TestCommandAllowed("admin", 0x19, "Deny")  
        
        print "Directive Receive"
        self.TestCommandAllowed("admin", 0x1A, "Deny")  
        
        print "Virtualization Management"
        self.TestCommandAllowed("admin", 0x1C, "Deny")  
        
        print "NVMe-MI Send"
        self.TestCommandAllowed("admin", 0x1D, "Deny")  
        
        print "NVMe-MI Receive"
        self.TestCommandAllowed("admin", 0xE, "Deny")  
        
        print "Doorbell Buffer Config"
        self.TestCommandAllowed("admin", 0x7C, "Deny")  
        
        print "Format NVM"
        self.TestCommandAllowed("admin", 0x80, "Deny")  
        
        print "Security Send"
        self.TestCommandAllowed("admin", 0x81, "Deny")  
        
        print "Security Receive"
        self.TestCommandAllowed("admin", 0x82, "Deny")  
        
        print "Sanitize"
        self.TestCommandAllowed("admin", 0x84, "Deny")            

        return ret_code
    
    def SubCase3(self):
        print "Test While a sanitize operation is in progress"
        print "All I/O Commands shall be aborted with a status of Sanitize In Progress"        
        print ""
        ret_code=0
        
        print "Flush"
        self.TestCommandAllowed("io", 0x0, "Deny")
        
        print "Write"
        self.TestCommandAllowed("io", 0x1, "Deny")
        
        print "Read"
        self.TestCommandAllowed("io", 0x2, "Deny")
        
        print "Write Uncorrectable"
        self.TestCommandAllowed("io", 0x4, "Deny")
        
        print "Compare"
        self.TestCommandAllowed("io", 0x5, "Deny")
        
        print "Write Zeroes"
        self.TestCommandAllowed("io", 0x8, "Deny")
        
        print "Dataset Management"
        self.TestCommandAllowed("io", 0x9, "Deny")
        
        print "Reservation Register"
        self.TestCommandAllowed("io", 0xD, "Deny")
        
        print "Reservation Report"
        self.TestCommandAllowed("io", 0xE, "Deny")
        
        print "Reservation Acquire"
        self.TestCommandAllowed("io", 0x11, "Deny")
        
        print "Reservation Release"
        self.TestCommandAllowed("io", 0x15, "Deny")

        return ret_code
        
    # </sub item scripts>
    
    def SubCase4(self):    
        print "Test While a sanitize operation is in progress and check if controller return zeros in the LBA field for get Error Information log command"
        ret_code=0   
        print ""
        print "Create Error Information by reading uncorrectable block"
        print "Set uncorrectable block, start block=0, block count=127"
        self.write_unc(SLB=0, BlockCnt=127)
        
        print "read uncorrectable block where is 5th block"
        self.shell_cmd("  buf=$(nvme read %s -s 5 -z 1024 -c 1 2>&1 > /dev/null) "%(self.dev)) 
        
        print "Check if error log was created with 0x5 in LBA field or not"
        self.GetErrorLog()
        LBA = int(ErrorLog[16])
        print "LBA Field: %s"%LBA
        
        if LBA==5:
            self.Print("PASS", "p")         
        else:
            self.Print("Fail: create Error log fail", "f")
            ret_code=1    
        
        if LBA==5:
            print ""
            print "Read error log and check if Return zeros in the LBA field or not while sanitize in progress" 
            self.GetErrorInfoWhileSanitizeInProgress()
            LBA = int(ErrorLog[16])
            print "LBA Field: %s"%LBA
            
            if LBA==0:
                self.Print("PASS", "p")  
            else:
                self.Print("Fail", "f")
                ret_code=1      
        return ret_code
    
    
    
if __name__ == "__main__":
    DUT = SMI_Sanitize(sys.argv )     
    DUT.RunScript()
    DUT.Finish()     
    
    
    
