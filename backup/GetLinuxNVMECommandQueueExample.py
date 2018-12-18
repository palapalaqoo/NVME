#!/usr/bin/env python
# -*- coding: utf-8 -*-
from lib_vct import NVME
from lib_vct import NVMECom
import sys
from time import sleep
import threading
import re
import random
import time
import os.path
import subprocess
from tuned import admin
from lib_vct.Flow.Sanitize import FlowSanitizeMode


print "SMI_Sanitize.py"
print "Author: Sam Chan"
print "Ver: 20181203"
mNVME = NVME.NVME(sys.argv )

## paramter #####################################
ret_code = 0
sub_ret=0
CMD_Result="0"
SANACT=0
ErrorLog=[]
#-- Get Log Page - Commands Supported and Effects Log
mCSAEL=mNVME.get_CSAEL()
## function #####################################

 
    
def asynchronous_event_request_cmd(): 
    global CMD_Result
    CMD_Result = mNVME.shell_cmd("nvme admin-passthru %s --opcode=0xC 2>&1"%(mNVME.dev))

def CMD_Asynchronous():
        # create thread for asynchronous_event_request_cmd        
        t = threading.Thread(target = asynchronous_event_request_cmd)
        t.start()        
        sleep(0.2)
        # raising critical waning
        # set Asynchronous Event Configuration (Feature Identifier 0Bh) bit0-7 to 1
        mNVME.shell_cmd(" nvme set-feature %s -f 0xB -v 0xff"%(mNVME.dev), 0.5)        
        # get log page and set 'Retain Asynchronous Event(RAE) = 0' 
        mNVME.shell_cmd(" buf=$(nvme admin-passthru %s --opcode=0x2 -r --cdw10=0x2 -l 16 2>&1 >/dev/null)"%(mNVME.dev), 0.5)         
        # Set TMPTH to 60 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 0)
        mNVME.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x14D"%(mNVME.dev), 0.5) 
        # Set TMPTH to 10 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 1)
        mNVME.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x11B"%(mNVME.dev), 0.5) 
        # Set TMPTH to 60 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 0)
        mNVME.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x14D"%(mNVME.dev), 0.5) 
        # get log page and set 'Retain Asynchronous Event(RAE) = 0' 
        mNVME.shell_cmd(" buf=$(nvme admin-passthru %s --opcode=0x2 -r --cdw10=0x2 -l 16 2>&1 >/dev/null)"%(mNVME.dev), 0.5)     
        # Set TMPTH to 10 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 1)
        mNVME.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x11B"%(mNVME.dev), 0.5)  
        # Set TMPTH to 60 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 0)
        mNVME.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x14D"%(mNVME.dev), 0.5)    
        # wait thread finish
        t.join()        
        return 0

def CMD_CreateCQ():
    mNVME.shell_cmd("nvme admin-passthru /dev/nvme1 --opcode=0x5 --cdw10=0")

        
def CMD_Abort():
    cmd_success=0
    
    mNVME.nvme_reset()

    # Enable kernel debug
    mNVME.shell_cmd("echo 1 > /sys/kernel/debug/tracing/events/nvme/enable")
    
    # clear trace file
    mNVME.shell_cmd("echo > /sys/kernel/debug/tracing/trace")
    
    # Asynchronous Event Request command    
    t2 =subprocess.Popen("nvme admin-passthru  %s --opcode=0xC"%mNVME.dev, shell=True,  stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)

    # get CID to abort command
    sleep(0.2)    
    CID=-1
    
    
    #t1stdout, t1stderr = t1.communicate(input='')
    #print t1stdout
    #print t1stderr
    filename="/sys/kernel/debug/tracing/trace"
    if(os.path.isfile(filename)): 
        files = open(filename, 'r') 
        mfile=files.read()
        mStr="cmdid=(\d+),"
        if re.search(mStr, mfile):
            CID=int(re.search(mStr, mfile).group(1))
    else:
        print "file missing"
        
    # if get CID success, issue abort command with CID value, and QID=0(admin queue)
    if CID!=-1:
        CDW10=CID<<16
        mNVME.shell_cmd("nvme admin-passthru  %s --opcode=0x8 --cdw10=%s 2>&1 >/dev/null"%(mNVME.dev, CDW10))        
        # stdout, stderr = t2.communicate(input='')
        stdout, stderr = t2.communicate(input='')
        
        if re.search("ABORT_REQ", stderr):
            cmd_success=1     
    else:
        print "CID=-1"
        
    # kill all jobs
    if t2.poll()== None:    
        t2.terminate()

    # Disable kernel debug
    mNVME.shell_cmd("echo 0 > /sys/kernel/debug/tracing/events/nvme/enable")        
                   
    if cmd_success==1:
        mNVME.Print("PASS", "p")  
    else:
        mNVME.Print("Fail", "f")
        ret_code=1        
        

def CMD_Flush(): 
    global CMD_Result
    CMD_Result = mNVME.shell_cmd("nvme flush %s  -n 1 2>&1"%(mNVME.dev))

def SendTestCommand(*args): 
    global CMD_Result
    

    
    CMDType=args[0]
    Opcode=args[1]
    LogPageID=args[2]
    
    
        
    
    if CMDType == "admin":
        if Opcode==0x2:
            CMD="nvme admin-passthru %s -opcode=%s --cdw10=%s -r -l 16 2>&1 | sed '2,$d' "%(mNVME.dev, Opcode, LogPageID)
            CMD_Result = mNVME.shell_cmd(CMD)   
        elif Opcode==0xC:          # Asynchronous              
            # create thread for asynchronous_event_request_cmd        
            t = threading.Thread(target = asynchronous_event_request_cmd)
            t.start()        
            sleep(0.5)   
            mNVME.nvme_reset()        
            t.join(10)
        else:  
            CMD="nvme admin-passthru %s -opcode=%s 2>&1"%(mNVME.dev, Opcode)
            CMD_Result = mNVME.shell_cmd(CMD)
    elif CMDType == "io":
        CMD="nvme io-passthru %s -opcode=%s 2>&1"%(mNVME.dev, Opcode)
        CMD_Result = mNVME.shell_cmd(CMD)

def StartTestFlowSanitize(CMDType, Opcode, ExpectedResult, LogPageID=0):  
        mNVME.Flow.Sanitize.ShowProgress=False   
        mNVME.Flow.Sanitize.SetEventTrigger(SendTestCommand, CMDType, Opcode, LogPageID)
        mNVME.Flow.Sanitize.SetOptions("-a %s"%SANACT)
        # 0< Threshold <65535
        mNVME.Flow.Sanitize.Mode=FlowSanitizeMode.KeepSanitizeInProgress
        mNVME.Flow.Sanitize.Start()

def TestCommandAllowed(CMDType, Opcode, ExpectedResult, LogPageID=0):  
# CMDType:  admin or io
# ExpectedResult: Deny or Allow
    global ret_code
    
    if not mNVME.IsCommandSupported(CMDType, Opcode, LogPageID):
        mNVME.Print( "Command is not supported, test if controller is working after command!", "w")
        # start the test
        StartTestFlowSanitize(CMDType, Opcode, ExpectedResult, LogPageID)
        # print result
        print "Returned Status: %s"%CMD_Result
        if mNVME.dev_alive:
            mNVME.Print("PASS", "p")  
        else:
            mNVME.Print("Fail, device is missing", "f")
            mNVME.Print("Exist all the test!", "f")
            print ""    
            ret_code=1
            print "ret_code:%s"%ret_code
            print "Finish"
            sys.exit(ret_code)                             
        print ""
    else:    
        # start the test
        StartTestFlowSanitize(CMDType, Opcode, ExpectedResult, LogPageID)        
        # print result
        print "Returned Status: %s"%CMD_Result
        if re.search("SANITIZE_IN_PROGRESS", CMD_Result) and ExpectedResult=="Deny":
            mNVME.Print("Expected command Deny: PASS", "p")  
        elif not re.search("SANITIZE_IN_PROGRESS", CMD_Result) and ExpectedResult=="Allow":
            mNVME.Print("Expected command Allow: PASS", "p")  
        else:
            mNVME.Print("Expected command %s: Fail"%ExpectedResult, "f")
            ret_code=1    
        print ""    

def GetErrorLog():
    global ErrorLog
    ErrorLog = mNVME.get_log2byte(0x1, 32)

def GetErrorInfoWhileSanitizeInProgress():    
    mNVME.Flow.Sanitize.ShowProgress=False   
    mNVME.Flow.Sanitize.SetEventTrigger(GetErrorLog)
    mNVME.Flow.Sanitize.SetOptions("-a %s"%SANACT)
    # 0< Threshold <65535
    mNVME.Flow.Sanitize.SetEventTriggerThreshold(100)
    mNVME.Flow.Sanitize.Start()
        
## end function #####################################

CryptoEraseSupport = True if (mNVME.IdCtrl.SANICAP.bit(0) == "1") else False
BlockEraseSupport = True if (mNVME.IdCtrl.SANICAP.bit(1) == "1") else False
OverwriteSupport = True if (mNVME.IdCtrl.SANICAP.bit(2) == "1") else False

if BlockEraseSupport:
    SANACT=2
elif CryptoEraseSupport:
    SANACT=4
elif OverwriteSupport:
    SANACT=3


print ""
print "-- NVME Sanitize test" 
print "-----------------------------------------------------------------------------------"

print "Check Sanitize Capabilities (SANICAP)"
mNVME.Print("Crypto Erase sanitize operation is Supported", "p")  if CryptoEraseSupport else mNVME.Print("Crypto Erase sanitize operation is not Supported", "f") 
mNVME.Print("Block Erase sanitize operation is Supported", "p")  if BlockEraseSupport else mNVME.Print("Block Erase sanitize operation is not Supported", "f") 
mNVME.Print("Overwrite sanitize operation is Supported", "p")  if OverwriteSupport else mNVME.Print("Overwrite sanitize operation is not Supported", "f") 

if SANACT==0:
    mNVME.Print("Any sanitize operation is not supported, quit the test!","w")
    print ""    
    ret_code =255
    print "ret_code:%s"%ret_code
    print "Finish"
    sys.exit(ret_code)   

print ""
print "Check if there is any sanitize operation in progress or not"
per = mNVME.GetLog.SanitizeStatus.SPROG
if per != 65535:
    mNVME.Print("The most recent sanitize operation is currently in progress, waiting the operation finish(Time out = 60s)", "w")
    WaitCnt=0
    while per != 65535:
        print ("Sanitize Progress: %s"%per)
        per = mNVME.GetLog.SanitizeStatus.SPROG
        WaitCnt = WaitCnt +1
        if WaitCnt ==60:
            print ""
            mNVME.Print("Time out!, exit all test ", "f")  
            ret_code =1
            print "ret_code:%s"%ret_code
            print "Finish"
            sys.exit(ret_code) 
        sleep(1)
    print "Recent sanitize operation was completed"
else:
    print "All sanitize operation was completed"
    


print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Keyword: Command Completion"
print "When the command is complete, the controller shall post a completion queue entry to the "
print "Admin Completion Queue indicating the status for the command."
print ""

# Sanitize command 
CMD="nvme sanitize %s %s 2>&1"%(mNVME.dev_port, "-a %s"%SANACT)  
print "Issue sanitize command: %s"%CMD
             
mStr=mNVME.shell_cmd(CMD)
print "Get return code: %s"%mStr
print "Check return code is success or not, expected SUCCESS"
if re.search("SUCCESS", mStr):
    mNVME.Print("PASS", "p")  
else:
    mNVME.Print("Fail", "f")
    ret_code=1 
    
    
    

print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Keyword: When a sanitize operation starts on any controller"
print "Shall abort any command (submitted or in progress) not allowed during a sanitize operation with a status of Sanitize In Progress"
print ""
print "Test While a sanitize operation is in progress"
print "Shall only process the Admin commands listed in Figure 287"
'''
print ""
print "+ Asynchronous Event Request"
mNVME.Flow.Sanitize.ShowProgress=True   
mNVME.Flow.Sanitize.SetEventTrigger(CMD_Asynchronous)
mNVME.Flow.Sanitize.SetOptions("-a %s"%SANACT)
mNVME.Flow.Sanitize.SetEventTriggerThreshold(100)
mNVME.Flow.Sanitize.Start()
if re.search("00020101", CMD_Result):
    mNVME.Print("PASS", "p")  
else:
    mNVME.Print("Fail", "f")
    ret_code=1

print ""
print "+ Asynchronous Event Request"
mNVME.Flow.Sanitize.ShowProgress=True   
mNVME.Flow.Sanitize.SetEventTrigger(CMD_CreateCQ)
mNVME.Flow.Sanitize.SetOptions("-a %s"%SANACT)
mNVME.Flow.Sanitize.SetEventTriggerThreshold(100)
mNVME.Flow.Sanitize.Start()
if re.search("00020101", CMD_Result):
    mNVME.Print("PASS", "p")  
else:
    mNVME.Print("Fail", "f")
    ret_code=1

print ""
print "+ Abort"
CMD_Abort()
'''

print "Admin commands"
print "--------------------------------------------------------"

print "Delete I/O Submission Queue"
TestCommandAllowed("admin", 0x0, "Allow")

print "Create I/O Submission Queue"
TestCommandAllowed("admin", 0x1, "Allow")    


print "Get Log Page - Error Information"
TestCommandAllowed("admin", 0x2, "Allow", 0x1)  

print "Get Log Page - SMART / Health Information"
TestCommandAllowed("admin", 0x2, "Allow", 0x2)  

print "Get Log Page - Firmware Slot Information"
TestCommandAllowed("admin", 0x2, "Deny", 0x3)  

print "Get Log Page - Changed Namespace List"
TestCommandAllowed("admin", 0x2, "Allow", 0x4)  

print "Get Log Page - Commands Supported and Effects"
TestCommandAllowed("admin", 0x2, "Deny", 0x5)  

print "Get Log Page - Device Self-test"
TestCommandAllowed("admin", 0x2, "Deny", 0x6)  

print "Get Log Page - Telemetry Host-Initiated"
TestCommandAllowed("admin", 0x2, "Deny", 0x7)  

print "Get Log Page - Telemetry Controller-Initiated"
TestCommandAllowed("admin", 0x2, "Deny", 0x8)  

print "Get Log Page - Reservation Notification"
TestCommandAllowed("admin", 0x2, "Allow", 0x80)  

print "Get Log Page - Sanitize Status"
TestCommandAllowed("admin", 0x2, "Allow", 0x81)  

print "Delete I/O Completion Queue"
TestCommandAllowed("admin", 0x4, "Allow")   

print "Create I/O Completion Queue"
TestCommandAllowed("admin", 0x5, "Allow")   

print "Identify"
TestCommandAllowed("admin", 0x6, "Allow")   

print "Abort"
TestCommandAllowed("admin", 0x8, "Allow")  
 
print "Set Features"
TestCommandAllowed("admin", 0x9, "Allow")   

print "Get Features"
TestCommandAllowed("admin", 0xA, "Allow")   

print "Asynchronous Event Request"
TestCommandAllowed("admin", 0xC, "Allow")  

print "Namespace Management"
TestCommandAllowed("admin", 0xD, "Deny")  

print "Firmware Commit"
TestCommandAllowed("admin", 0x10, "Deny")  

print "Firmware Image Download"
TestCommandAllowed("admin", 0x11, "Deny")  

print "Device Self-test"
TestCommandAllowed("admin", 0x14, "Deny")  

print "Namespace Attachment"
TestCommandAllowed("admin", 0x15, "Deny")  

print "Keep Alive"
TestCommandAllowed("admin", 0x18, "Allow")  

print "Directive Send"
TestCommandAllowed("admin", 0x19, "Deny")  

print "Directive Receive"
TestCommandAllowed("admin", 0x1A, "Deny")  

print "Virtualization Management"
TestCommandAllowed("admin", 0x1C, "Deny")  

print "NVMe-MI Send"
TestCommandAllowed("admin", 0x1D, "Deny")  

print "NVMe-MI Receive"
TestCommandAllowed("admin", 0xE, "Deny")  

print "Doorbell Buffer Config"
TestCommandAllowed("admin", 0x7C, "Deny")  

print "Format NVM"
TestCommandAllowed("admin", 0x80, "Deny")  

print "Security Send"
TestCommandAllowed("admin", 0x81, "Deny")  

print "Security Receive"
TestCommandAllowed("admin", 0x82, "Deny")  

print "Sanitize"
TestCommandAllowed("admin", 0x84, "Deny")  


    

    
print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Keyword: When a sanitize operation starts on any controller"
print "Shall abort any command (submitted or in progress) not allowed during a sanitize operation with a status of Sanitize In Progress"
print ""
print "Test While a sanitize operation is in progress"
print "All I/O Commands shall be aborted with a status of Sanitize In Progress"
print ""

print "Flush"
TestCommandAllowed("io", 0x0, "Deny")

print "Write"
TestCommandAllowed("io", 0x1, "Deny")

print "Read"
TestCommandAllowed("io", 0x2, "Deny")

print "Write Uncorrectable"
TestCommandAllowed("io", 0x4, "Deny")

print "Compare"
TestCommandAllowed("io", 0x5, "Deny")

print "Write Zeroes"
TestCommandAllowed("io", 0x8, "Deny")

print "Dataset Management"
TestCommandAllowed("io", 0x9, "Deny")

print "Reservation Register"
TestCommandAllowed("io", 0xD, "Deny")

print "Reservation Report"
TestCommandAllowed("io", 0xE, "Deny")

print "Reservation Acquire"
TestCommandAllowed("io", 0x11, "Deny")

print "Reservation Release"
TestCommandAllowed("io", 0x15, "Deny")


  
print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Keyword: When a sanitize operation starts on any controller"
print "Shall abort any command (submitted or in progress) not allowed during a sanitize operation with a status of Sanitize In Progress"
print ""
print "Test While a sanitize operation is in progress and if controller return zeros in the LBA field for get Error Information log command"

print ""
print "Create Error Information by reading uncorrectable block"
print "Set uncorrectable block, start block=0, block count=127"
mNVME.write_unc(SLB=0, BlockCnt=127)

print "read uncorrectable block where is 5th block"
mNVME.shell_cmd("  buf=$(nvme read %s -s 5 -z 1024 -c 1 2>&1 > /dev/null) "%(mNVME.dev)) 

print "Check if error log was created with 0x5 in LBA field or not"
GetErrorLog()
LBA = int(ErrorLog[16])
print "LBA Field: %s"%LBA

if LBA==5:
    mNVME.Print("PASS", "p")         
else:
    mNVME.Print("Fail", "f")
    ret_code=1    

if LBA==5:
    print ""
    print "Read error log and check if Return zeros in the LBA field or not while sanitize in progress" 
    GetErrorInfoWhileSanitizeInProgress()
    LBA = int(ErrorLog[16])
    print "LBA Field: %s"%LBA
    
    if LBA==0:
        mNVME.Print("PASS", "p")  
    else:
        mNVME.Print("Fail", "f")
        ret_code=1  
        













    



print ""    
print "ret_code:%s"%ret_code
print "Finish"
sys.exit(ret_code)   

