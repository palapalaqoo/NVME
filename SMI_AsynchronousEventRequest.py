#!/usr/bin/env python
import sys
import re
import threading
from time import sleep
from lib_vct import NVMEAsyncEventRequest

print "Ver: 20180911_1532"
mNVME = NVMEAsyncEventRequest.AsyncEvent(sys.argv )


if mNVME.dev_alive:
    print "device alive"
else:    
    print "device missing"
    sys.exit(-1)
    
ret_code=0

timeup=0

def reset():
    mNVME.nvme_reset()
    mNVME.que.queue.clear()
    mNVME.shell_cmd(" nvme set-feature %s -f 0xB -v 0x3fff"%(mNVME.dev), 0.5)  

# for  Check Asynchronous Event Configuration           
# item[0]: message to print
# item[1]: function to trigger event
# item[0]: expected Completion Queue Entry Dword 0
TestItem=[]
TestItem.append(["Start to test error event(Read uncorrectable blocks)", mNVME.trigger_error_event, "00010400"])
TestItem.append(["Start to test smart/health status event(Over tempture)", mNVME.trigger_SMARTHealthStatus_event, "00020101"])
TestItem.append(["Start to test IO command event(Sanitize)", mNVME.trigger_Sanitize_event, "00810106"])
TestItem.append(["Start to test Notice(FirmwareActivationStarting)", mNVME.trigger_FirmwareActivationStarting, "00030102"])



# item[0]: message to print
# item[1]: function to trigger event
# item[0]: expected Completion Queue Entry Dword 0
TestItemDisableReport=[]
TestItemDisableReport.append(["Start to test smart/health status event(Over tempture)", mNVME.trigger_SMARTHealthStatus_event, "00020101"])
TestItemDisableReport.append(["Start to test IO command event(Sanitize)", mNVME.trigger_Sanitize_event, "00810106"])
TestItemDisableReport.append(["Start to test Notice(FirmwareActivationStarting)", mNVME.trigger_FirmwareActivationStartingNoEvent, "00030102"])

# Asynchronous Event Request Limit, 0's based
AERL=mNVME.IdCtrl.AERL.int

# clear all outstanding Asynchronous Event Request command
reset()

print "==== Asynchronous Event Request command test"  
print ""
    
# Check Status Code - Command specific status values
print "---- Test item 1: Check Status Code - Command specific status values"
print "AERL: %s" %(AERL)
print "Sending Asynchronous Event Request command for %s times.." %(AERL)
result_b=[]
for i  in range(AERL+1):
    
    async_result = mNVME.thread_asynchronous_event_request_cmd()
    result_b.append(async_result)
    
    # if is the last synchronous_event_request_cmd, it must receive the  "Asynchronous Event Request Limit Exceeded"
    if i==AERL:
        
        # wait thread finish and timeout=2s
        async_result.join(2)
        
        # if time out
        if async_result.is_alive():
            mNVME.Print("Error: can't receive the return code of Asynchronous Event Request command", "f")
            ret_code=1
            break
        
        # get return code from Asynchronous Event Request command        
        mThreadStr=mNVME.que.get()       
        
        mNVME.Print("return string from request command : %s" %(mThreadStr), "t")  
        
        # check the commands are aborted or not
        print "This is the last time "
        print "and the return code is: %s" %(mThreadStr) 
        print "Check the return code is Asynchronous Event Request Limit Exceeded or not"
        if re.search("NVMe Status:ASYNC_LIMIT", mThreadStr):
            mNVME.Print("PASS", "p")
        else:
            mNVME.Print("Fail", "f")
            ret_code=1    
    
# clear all outstanding Asynchronous Event Request command
reset()
print ""    
print "---- Test item 2: Check Asynchronous Event Configuration"    

# set Asynchronous Event Configuration feature to allow all the events can be reported to the host 
print "set Asynchronous Event Configuration = 0xff to enable all the events can be reported to the host "
mNVME.shell_cmd(" nvme set-feature %s -f 0xB -v 0x3fff"%(mNVME.dev), 0.5)   

# loop for test items
for Item in TestItem:
    print ""
    print Item[0]
    
    # assign a thread for event request cmd
    async_result = mNVME.thread_asynchronous_event_request_cmd()
    
    # trigger event
    Item[1]()
    
    # wait thread finish and timeout=2s
    async_result.join(2)
        
    # if time out
    if async_result.is_alive():
        mNVME.Print("Error: can't receive the return code of Asynchronous Event Request command", "f")
        ret_code=1
        break
        
    # get return code from Asynchronous Event Request command        
    try:
        mThreadStr=mNVME.que.get(timeout=1)
    except Exception as error:
        mNVME.Print("Can't get return code from Asynchronous Event Request command", "f")
    mNVME.Print("return string from request command : %s" %(mThreadStr), "t")   
    
    mstr="0" 
    try:
        mstr=re.split("NVMe command result:", mThreadStr)[1]
    except ValueError:
        print "return string from request command : %s" %(mThreadStr)

    print "Completion Queue Entry Dword 0: %s" %(mstr)

    print "Check Dword 0"
    if mstr==Item[2]:
        mNVME.Print("PASS", "p")
    else:
        mNVME.Print("Fail", "f")
        ret_code=1  
        
# clear all outstanding Asynchronous Event Request command
reset()            
print ""    
print "---- Test item 3: Check Asynchronous Event Configuration"    

# set Asynchronous Event Configuration feature to allow all the events can be reported to the host 
print "set Asynchronous Event Configuration = 0x0 to disable all the events can be reported to the host "
mNVME.shell_cmd(" nvme set-feature %s -f 0xB -v 0x0"%(mNVME.dev), 0.5)   

# loop for test items
for Item in TestItemDisableReport:
    print ""
    print Item[0]
    
    # assign a thread for event request cmd
    async_result = mNVME.thread_asynchronous_event_request_cmd()
    
    # trigger event
    
    Item[1]()
    
    
    # wait thread finish and timeout=2s
    async_result.join(2)
        
    # if time out, pass the test
    print "Check event was reported to host or not, if an event is not sent to the host then pass the test"
    if async_result.is_alive():
        mNVME.Print("PASS", "p")
    else:
        mNVME.Print("Fail", "f")
        ret_code=1   

# clear all outstanding Asynchronous Event Request command
reset()
# --------------------------------------------------------------------------------------
print ""
print "---- Test item 4: Check if the commands are aborted when the controller is reset"
print "Sending Asynchronous Event Request command"
# assign a thread for event request cmd
async_result = mNVME.thread_asynchronous_event_request_cmd()
  
# nvme reset
print "Trigger nvme reset"
mNVME.nvme_reset()

# wait thread finish and timeout=2s
async_result.join(2)


# if time out
if async_result.is_alive():
    mNVME.Print("Error: can't receive the return code of Asynchronous Event Request command", "f")
    ret_code=1
else:
    # get return code from Asynchronous Event Request command        
    mThreadStr=mNVME.que.get()
    
    mNVME.Print("return string from request command : %s" %(mThreadStr), "t")
    
    mstr = mThreadStr
    print "return code : %s" %(mstr)
    
    print "Check the return code is abort request or not"
    # check the commands are aborted or not
    if re.search("NVMe Status:ABORT_REQ", mThreadStr):
        mNVME.Print("PASS", "p")
    else:
        mNVME.Print("Fail", "f")
        ret_code=1    






sys.exit(ret_code)
    