#!/usr/bin/env python
from lib_vct import NVME
import sys
from time import sleep
import threading
import re
from lib_vct import NVMEAsyncEventRequest

print "Ver: 20180911_1632"
mNVME = NVME.NVME(sys.argv )
AsyncNVME = NVMEAsyncEventRequest.AsyncEvent(sys.argv )


if mNVME.dev_alive:
    print "device alive"
else:    
    print "device missing"
    sys.exit(-1)
    
## paramter #####################################
ret_code=0
AsyncEventCmdFail=0
## function #####################################
def testBlockAreas(ID):
    ret=0
    print "Get log page: %s"%ID
    print ""    
    mLOG=mNVME.get_log_passthru(ID, 512, 1, 1)

    if not len(mLOG) == 512:
        mNVME.Print("Fail to get log", "f")
        ret=1 
    else:
        
        print "check if (Data Area 1 Last Block <= Data Area 2 Last Block<= Data Area 3 Last Block) or not"
        
        LastBlock1=int(mLOG[9]+mLOG[8])
        LastBlock2=int(mLOG[11]+mLOG[10])
        LastBlock3=int(mLOG[13]+mLOG[12])
        '''
        #--- TODO test ----
        LastBlock1=2
        LastBlock2=2
        LastBlock3=1
        '''
        
        print "1 Last Block: %s, 2 Last Block: %s, 3 Last Block: %s" %(LastBlock1, LastBlock2, LastBlock3)
        if (LastBlock1<=LastBlock2) and (LastBlock2<=LastBlock3):
            mNVME.Print("PASS", "p")
        else:
            mNVME.Print("Fail", "f")
            ret=1  
        
        #-----------------------------------------------------------------------------------
        print ""
        print "check Data Areas"
        
        if LastBlock1==0:
            print "Data Area 1: No Data"
        else:
            print "Data Area 1: from block %s to block %s"%("0", LastBlock1)
            
        if LastBlock2==LastBlock1:
            print "Data Area 2: No Data"
        else:
            print "Data Area 2: from block %s to block %s"%(LastBlock1+1, LastBlock2)
            
        if LastBlock3==LastBlock2:
            print "Data Area 3: No Data"
        else:
            print "Data Area 3: from block %s to block %s"%(LastBlock2+1, LastBlock3)  
        #-----------------------------------------------------------------------------------
        print ""
        print "-------- Read Data Areas 1 --------"
        if LastBlock1==0:
            print "Data Area 1: No Data"    
        else:
            print "Data Area 1: from block %s to block %s"%("0", LastBlock1)
            for i in range(1, LastBlock1+1):
                LOG=mNVME.get_log_passthru(7, 512, 0, 0, 512*i)
                print "Data Area 1, block %s"%i
                print LOG
        
            
        print ""
        print "-------- Read Data Areas 2 --------"
        if LastBlock2==LastBlock1:
            print "Data Area 2: No Data"    
        else:
            print "Data Area 2: from block %s to block %s"%(LastBlock1+1, LastBlock2)
            for i in range(LastBlock1+1, LastBlock2+1):
                LOG=mNVME.get_log_passthru(7, 512, 0, 0, 512*i)
                print "Data Area 2, block %s"%i
                print LOG
         
                    
        print ""
        print "-------- Read Data Areas 3 --------"
        if LastBlock3==LastBlock2:
            print "Data Area 3: No Data"    
        else:
            print "Data Area 3: from block %s to block %s"%(LastBlock2+1, LastBlock3)  
            for i in range(LastBlock2+1, LastBlock3+1):
                LOG=mNVME.get_log_passthru(7, 512, 0, 0, 512*i)
                print "Data Area 3, block %s"%i
                print LOG
    return True if ret==0 else False

def getReasonIdentifier(ID):
    mLOG=mNVME.get_log_passthru(ID, 512, 1, 0)
    rStr=""
    for byte in range(384, 512):
        rStr=rStr+mLOG[byte]
    return rStr
#############################################
    





print ""
print "-----------------------------------------------------------------------------------"
print "-- Telemetry (Optional) test" 

#-----------------------------------------------------------------------------------
print "The host identifies controller support for Telemetry log pages in the Identify Controller data structure."
SupportTelemetry=mNVME.IdCtrl.LPA.bit(0)

if SupportTelemetry==0:
    mNVME.Print( "Controller do not support telemetry in Log Page Attributes (LPA)", 'f')
    print "exit test" 
    sys.exit(1)
else:
    mNVME.Print( "Check if Controller support telemetry in Log Page Attributes (LPA) or not", 'p')
    

#-----------------------------------------------------------------------------------

print ""    
print "====================== Host-initiated telemetry test(log page 0x7) ====================== "
print ""  
print "The host proceeds with a host-initiated data collection "
print "by submitting the Get Log Page command for the Telemetry Host-Initiated log page with the Create Telemetry Host-Initiated Data bitset to '1'."
print "Check if get log page command success"
LOG07=mNVME.get_log_passthru(7, 512, 0, 1)
if len(LOG07) == 512:
    mNVME.Print("PASS", "p")
else:
    mNVME.Print("Fail", "f")
    ret_code=1 

print ""
print "Teset Block Areas for 0x7 "
if testBlockAreas(0x7):
    mNVME.Print("PASS", "p")
else:
    mNVME.Print("Fail", "f")
    ret_code=1         

print ""
print "Get Reason Identifier "
print "Reason Identifier: %s"%getReasonIdentifier(0x7)

#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------

#----------------------------------------------------------------------------------- 
print ""     
print "====================== Async event test and controller-initiated telemetry test(log page 0x8) ====================== "
print ""    
# save Telemetry Controller-Initiated Data Generation Number
LOG08=mNVME.get_log_passthru(8, 512, 0, 0)
LOG08_383_old= LOG08[383]

print "To receive notification that controller-initiated data is available,"
print "the host enables Telemetry Log Notices using the Asynchronous Event Configuration feature."

mNVME.shell_cmd(" nvme set-feature %s -f 0xB -v 0x3fff"%(mNVME.dev), 0.5)   
mNVME.Print(  "set Asynchronous Event Configuration = 0xff to enable all the events can be reported to the host: done ", 'p')

# assign a thread for event request cmd
print "Assign a thread for event request cmd"
async_result = AsyncNVME.thread_asynchronous_event_request_cmd()


# wait thread finish and timeout=2s
print "wait for controller signals that controller-initiated telemetry data is available(time out = 60s)"
async_result.join(60)

        
# if time out
if async_result.is_alive():
    print "async_result.is_alive=true"
    AsyncEventCmdFail=1
else:        
    # get return code from Asynchronous Event Request command        
    try:
        mThreadStr=AsyncNVME.que.get(timeout=1)
    except Exception as error:
        AsyncNVME.Print("Can't get return code from Asynchronous Event Request command", "f")
        AsyncEventCmdFail=1
    AsyncNVME.Print("return string from request command : %s" %(mThreadStr), "t")   
    
    mstr="0" 
    try:
        mstr=re.split("NVMe command result:", mThreadStr)[1]
        print "Completion Queue Entry Dword 0: %s" %(mstr)    
        print "Check Dword 0"
        if mstr=="00030202":
            AsyncNVME.Print("PASS", "p")
        else:
            AsyncNVME.Print("Fail", "f")
            AsyncEventCmdFail=1         
        
    except ValueError:
        #when return 'passthru: Interrupted system call'
        print "return string from request command : %s" %(mThreadStr)
        AsyncEventCmdFail=1
    #clear Asynchronous Event Request command
    mNVME.nvme_reset()
        
if AsyncEventCmdFail==1:
    print ""
    AsyncNVME.Print("Can't receive the return code of Asynchronous Event Request command", "w")
    AsyncNVME.Print("exit async test and controller-initiated telemetry test", "w")   
    ret_code=1     
else:
    print ""
    print "Check if Telemetry Controller-Initiated Data Available in log 0x7 = 1"
    LOG07=mNVME.get_log_passthru(7, 512, 1, 0)
    if LOG07[382]=="01":
        mNVME.Print("PASS", "p")
    else:
        mNVME.Print("Fail", "f")
        ret_code=1  
        
    print ""      
    print "Check if Telemetry Controller-Initiated Data Available in log 0x8 = 1"
    LOG08=mNVME.get_log_passthru(8, 512, 1, 0)
    if LOG08[382]=="01":
        mNVME.Print("PASS", "p")         
    else:
        mNVME.Print("Fail", "f")      
        ret_code=1  

    print ""
    print "Teset Block Areas for 0x8 "
    if testBlockAreas(0x8):
        mNVME.Print("PASS", "p")
    else:
        mNVME.Print("Fail", "f")
        ret_code=1    
        
    print ""    
    print "Check if Telemetry Controller-Initiated Data Available in log 0x8 = 0 after get log command with RAE=0"
    LOG08=mNVME.get_log_passthru(8, 512, 0, 0)
    if LOG08[382]=="00":
        mNVME.Print("PASS", "p")         
    else:
        mNVME.Print("Fail", "f")      
        ret_code=1          
    
    print ""    
    print "Check if Telemetry Controller-Initiated Data Generation Number changed"
    print "before: %s"%LOG08_383_old
    print "after   : %s"%LOG08[383]
    if not LOG08_383_old==LOG08[383]:
        mNVME.Print("PASS", "p")        
    else:
        mNVME.Print("Fail", "f")      
        ret_code=1  
         
    print ""
    print "Get Reason Identifier "
    print "Reason Identifier: %s"%getReasonIdentifier(0x8)        
        


print ""
print "ret_code:%s"%ret_code
print "Finish"
sys.exit(ret_code)



