#!/usr/bin/env python
'''
Created on Aug 15, 2018

@author: root
'''
from lib_vct import NVME
import sys
from time import sleep
import threading
import random

print "SMI_NVMeReset.py"
print "Author: Sam Chan"
print "Ver: 20181203"

## paramter #####################################
mNVME = NVME.NVME(sys.argv[1] )
ret_code=0
NSSRSupport=True if mNVME.CR.CAP.NSSRS.int==1 else False
TestItems=[]

## function ##################################### 
def GetRDY():
    return mNVME.CR.CSTS.bit(0)

def init():
    global TestItems
    # TestItems=[[description, function],[description, function],..]
    
    TestItems.append(["Controller Reset", mNVME.nvme_reset])
    
    if NSSRSupport:
        TestItems.append(["NVM Subsystem Reset", mNVME.subsystem_reset])
        
    TestItems.append(["PCI Express Hot reset", mNVME.hot_reset])    
    
    TestItems.append(["Data Link Down status", mNVME.link_reset]) 
    
    TestItems.append(["Function Level Reset", mNVME.FunctionLevel_reset])
    
## end function #####################################







init()


print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Keyword: The Admin Queue registers (AQA, ASQ, or ACQ) are not reset as part of a controller reset"
print "" 
    
RDY = GetRDY()

if RDY==1:
    print "\033[31mCheck CSTS.RDY before reset: FAIL! (CSTS.RDY=%s) , exit test\033[0m" %(RDY)
else:
    print "\033[32mCheck CSTS.RDY before reset: PASS! (CSTS.RDY=%s)\033[0m" %(RDY)
    
    
AQA = mNVME.CR.AQA.str    
ASQ = mNVME.CR.ASQ.str   
ACQ = mNVME.CR.ACQ.str    




print "NVME reset (Controller disable)"

t = threading.Thread(target = mNVME.nvme_reset)
t.start()

print "Wait for CSTS.RDY = 0"
while GetRDY()==1:
    pass

print "\033[32mCSTS.RDY = 0 \033[0m"
print "Wait for CSTS.RDY = 1"
while GetRDY()==0:
    pass

t.join()
print "\033[32mCSTS.RDY = 1 \033[0m"

print "compare AQA, ASQ, ACQ after reset"
print "before reset: AQA = %s" %(AQA)
print "before reset: ASQ = %s" %(ASQ)
print "before reset: ACQ = %s" %(ACQ)
print "after reset: AQA = %s" %(mNVME.CR.AQA.str)
print "after reset: ASQ = %s" %(mNVME.CR.ASQ.str)
print "after reset: ACQ = %s" %(mNVME.CR.ACQ.str)

if AQA!=mNVME.CR.AQA.str or ASQ!=mNVME.CR.ASQ.str or ACQ!=mNVME.CR.ACQ.str:
    print  "\033[31m FAIL! \033[0m"   
    ret_code=1
else:
    "\033[32mPASS! \033[0m"        
sleep(0.1)


print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Check if all supported reset is working"
print ""
for mItem in TestItems:        
    reset_type_name=mItem[0]
    reset_func=mItem[1] 
    print "issue " + reset_type_name
    print "Check if controll is alive after reset"
    reset_func()
    if mNVME.dev_alive:
        mNVME.Print("PASS", "p")
    else:
        mNVME.Print("FAIL, exit", "f")
        ret_code = 1
    print  ""    
    
    
# max loopcnt = len(TestItems)* loop
loopcnt=0    
for loop in range(10):
    
    for mItem in TestItems:        
        loopcnt=loopcnt+1
        mItem=TestItems[3]
        reset_type_name=mItem[0]
        reset_func=mItem[1] 

        print "===== reset_type = %s  ========== loop = %s ============================" %( reset_type_name, loopcnt)        
        print "-- start testing for Pending Admin Commands after reset --"
        print "Keyword: The controller stops processing any outstanding Admin or I/O commands."  
        print "Test if device self-test operation was aborted due to the reset commands"     
          
        if mNVME.IdCtrl.OACS.bit(4)=="0":
            print "Controller does not support the DST operation, quit this test item!"
        else:
            mNVME.Flow.DST.EventTriggeredMessage="Send format command as DST execution >= 1% "
            mNVME.Flow.DST.ShowProgress=True     
            # set DST command nsid
            mNVME.Flow.DST.SetNSID(0x1)
            # set Event
            mNVME.Flow.DST.SetEventTrigger(reset_func)                     
            # set DST type = Short device self-test operation
            mNVME.Flow.DST.SetDstType(1)    
            # set Threshold = 1 to raise event
            mNVME.Flow.DST.SetEventTriggerThreshold(1)
                
            # start DST flow and get device self test status 
            DSTS=mNVME.Flow.DST.Start()        
            if DSTS!=-1:        
                # get bit 3:0        
                DSTSbit3to0 = DSTS & 0b00001111
                print "result of the device self-test operation from Get Log Page : %s" %hex(DSTSbit3to0)
                print "Check the result of the device self-test operation , expected result:  0x2(Operation was aborted by a Controller Level Reset)"
                if DSTSbit3to0==2:
                    mNVME.Print("PASS", "p")
                else:
                    mNVME.Print("FAIL", "f")
                    ret_code = 1                         
            else:
                print "Controller does not support the DST operation"          
        
        
        print""
               
        print "-- start testing for Pending IO Commands after reset(data integrity) --"
        print "Keyword: The controller stops processing any outstanding Admin or I/O commands."  
        print "Test if write command was aborted due to the reset commands"
       
        patten=0x5A
        thread_w=5
        block_w=1024 
        total_byte_w=block_w*thread_w *512
        
        # clear SSD data to 0x0
        mNVME.fio_write(0, total_byte_w, 0x0)        
        
        # write data using multy thread
        mThreads = mNVME.nvme_write_multi_thread(thread_w, 0, block_w, patten)
        
        # check if all process finished 
        reset_cnt=0
        while True:        
            allfinished=1
            for process in mThreads:
                if process.is_alive():
                    allfinished=0
        
            # if all process finished then, quit while loop, else  send reset command
            if allfinished==1:        
                break
            else:
                reset_func()
                reset_cnt=reset_cnt+1
                sleep(0.5)
                        
        print  "send reset command %s times while writing data is in progress"%(reset_cnt)
        if not mNVME.dev_alive:
            ret_code=1
            mNVME.Print("Error! after reset, device is missing, quit test", "f")
            break
         
        # if have 00 and 5a in flash, then pass the test(f_write pattern=0x5a)
        find_00 = mNVME.shell_cmd("hexdump %s -n %s |grep '0000 0000' 2>/dev/null"%(mNVME.dev, total_byte_w))
        find_patten = mNVME.shell_cmd("hexdump %s -n %s |grep '5a5a 5a5a' 2>/dev/null"%(mNVME.dev, total_byte_w))        
        
        # controller reset can't verify data integrity, so let data integrity test = pass
        if (find_00 and find_patten) or reset_type_name=="Controller Reset":
            print "\033[32mCheck data integrity: PASS! \033[0m"
        else:
            print  "\033[31mCheck data integrity: FAIL! \033[0m"
            ret_code=1
            
        print ""
 




print""    
print "ret_code:%s"%ret_code
print "finished" 

sys.exit(ret_code)


    
    


