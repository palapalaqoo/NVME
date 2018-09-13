#!/usr/bin/env python
from lib_vct import NVME
import sys
from time import sleep
import threading
import re

print "Ver: 20180911_1632"
mNVME = NVME.NVME(sys.argv )


if mNVME.dev_alive:
    print "device alive"
else:    
    print "device missing"
    sys.exit(-1)
    
## paramter #####################################

ResetItem=[]
ResetItem.append(["NVME reset", mNVME.nvme_reset])
ResetItem.append(["Hot reset", mNVME.hot_reset])
ResetItem.append(["Link reset", mNVME.link_reset])
ResetItem.append(["Subsystem reset", mNVME.subsystem_reset])
## function #####################################
def GetPS():
    return int(mNVME.get_feature(2)[-1:])


#############################################
    
ret_code=0



SupportTelemetry=mNVME.IdCtrl.LPA.bit(0)

if SupportTelemetry==0:
    mNVME.Print( "Controller do not support telemetry in Log Page Attributes (LPA)", 'f')
    print "exit test" 
    sys.exit(1)
else:
    print "Controller support telemetry in Log Page Attributes (LPA)"






print ""
print "-----------------------------------------------------------------------------------"
print "-- Telemetry Host-Initiated (Log Identifier 07h) test" 
print "Test Data Blocks are 512 bytes in size or not"
#-----------------------------------------------------------------------------------
print "Test if get log page command is not a multiple of 512 bytes for this log, then the controller shall return an error of Invalid Field in Command"
for DataBlock in range(12, 513, 50):
    print "Send Get Log Page command for %s byte datas of Data Blocks "%DataBlock
    
    mStr = mNVME.shell_cmd("nvme get-log %s --log-id=0x7 --log-len=%s 2>&1"%(mNVME.dev, DataBlock))
    mNVME.Print(mStr, 't')

    # if (not a multiple of 512 bytes and get get log fail) or (multiple of 512 bytes and get log success), then pass the test
    if (re.search("NVMe Status:INVALID_FIELD", mStr) and DataBlock!=512) or (not re.search("NVMe Status:INVALID_FIELD", mStr) and DataBlock==512):
        mNVME.Print("PASS", "p")     
    else:
        mNVME.Print("Fail", "f")
        ret_code=1         
#----------------------------------------------------------------------------------- 
print ""
print "check Command Dword 10 -- Log Specific Field for 'Create Telemetry Host-Initiated Data'"

LOG07_0=mNVME.get_log_passthru(7, 512, 0, 0)
LOG07_1=mNVME.get_log_passthru(7, 512, 0, 1)
LOG08_0=mNVME.get_log_passthru(8, 512, 0, 0)
LOG08_1=mNVME.get_log_passthru(8, 512, 0, 1)

if len(LOG07_0) == 512 and len(LOG07_1) == 512 and len(LOG08_0) == 512 and len(LOG08_1) == 512 :
    mNVME.Print("PASS", "p")
else:
    mNVME.Print("Fail", "f")
    ret_code=1 
    
#----------------------------------------------------------------------------------- 

# get 512 byte log data where RAE=0, LSP=0
LOG07=mNVME.get_log_passthru(7, 512, 1, 0)
LOG08=mNVME.get_log_passthru(8, 512, 1, 0)



print ""   
print "Check Log Identifier in log byte0"

LogId=LOG07[0]

print "Log Identifier: %s"%LogId
if LogId=="07":
    mNVME.Print("PASS", "p")
else:
    mNVME.Print("Fail", "f")
    ret_code=1 
    
print ""
print "Check if IEEE OUI Identifier = identify.IEEE or not"
IEEE=int((LOG07[7]+LOG07[6]+LOG07[5]),16)
print "IEEE: %s, identify.IEEE: %s" %(IEEE, mNVME.IdCtrl.IEEE.int)

if IEEE==mNVME.IdCtrl.IEEE.int:
    mNVME.Print("PASS", "p")
else:
    mNVME.Print("Fail", "f")
    ret_code=1 
    
print ""
print "check if (Telemetry Host-Initiated Data Area 1 Last Block <= 2 Last Block<= 3 Last Block) or not"
LastBlock1=int(LOG07[9]+LOG07[8])
LastBlock2=int(LOG07[11]+LOG07[10])
LastBlock3=int(LOG07[13]+LOG07[12])
print "1 Last Block: %s, 2 Last Block: %s, 3 Last Block: %s" %(LastBlock1, LastBlock2, LastBlock3)
if (LastBlock1<=LastBlock2) and (LastBlock2<=LastBlock3):
    mNVME.Print("PASS", "p")
else:
    mNVME.Print("Fail", "f")
    ret_code=1 

print ""
print "check if Telemetry Controller-Initiated Data Available in log ID 07h = Telemetry Controller-Initiated Data Available in log ID 08h  or not"
print "TCIDA in 0x7h: %s, TCIDA in 0x8h: %s" %(LOG07[382], LOG08[382])
if LOG07[382]<=LOG08[382]:
    mNVME.Print("PASS", "p")
else:
    mNVME.Print("Fail", "f")
    ret_code=1 

print ""
print "check if Telemetry Controller-Initiated Data Generation Number in log ID 07h = Telemetry Controller-Initiated Data Generation Number in log ID 08h  or not"
print "TCIDGN in 0x7h: %s, TCIDGN in 0x8h: %s" %(LOG07[383], LOG08[383])
if LOG07[383]<=LOG08[383]:
    mNVME.Print("PASS", "p")
else:
    mNVME.Print("Fail", "f")
    ret_code=1 


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
print ""
print "-----------------------------------------------------------------------------------"
print "-- Telemetry Controller-Initiated (Log Identifier 08h) test" 
print "Test Data Blocks are 512 bytes in size or not"
#-----------------------------------------------------------------------------------
print "Test if get log page command is not a multiple of 512 bytes for this log, then the controller shall return an error of Invalid Field in Command"
for DataBlock in range(12, 513, 50):
    print "Send Get Log Page command for %s byte datas of Data Blocks "%DataBlock
    
    mStr = mNVME.shell_cmd("nvme get-log %s --log-id=0x8 --log-len=%s 2>&1"%(mNVME.dev, DataBlock))
    mNVME.Print(mStr, 't')

    # if (not a multiple of 512 bytes and get get log fail) or (multiple of 512 bytes and get log success), then pass the test
    if (re.search("NVMe Status:INVALID_FIELD", mStr) and DataBlock!=512) or (not re.search("NVMe Status:INVALID_FIELD", mStr) and DataBlock==512):
        mNVME.Print("PASS", "p")     
    else:
        mNVME.Print("Fail", "f")
        ret_code=1         
#----------------------------------------------------------------------------------- 
print ""   
print "Check Log Identifier in log byte0"

LogId=LOG08[0]

print "Log Identifier: %s"%LogId
if LogId=="08":
    mNVME.Print("PASS", "p")
else:
    mNVME.Print("Fail", "f")
    ret_code=1 

print ""
print "Check if IEEE OUI Identifier = identify.IEEE or not"
IEEE=int((LOG08[7]+LOG08[6]+LOG08[5]),16)
print "IEEE: %s, identify.IEEE: %s" %(IEEE, mNVME.IdCtrl.IEEE.int)
if IEEE==mNVME.IdCtrl.IEEE.int:
    mNVME.Print("PASS", "p")
else:
    mNVME.Print("Fail", "f")
    ret_code=1 

print ""
print "check if (Telemetry Controller-Initiated Data Area 1 Last Block <= 2 Last Block<= 3 Last Block) or not"
LastBlock1=int(LOG08[9]+LOG08[8])
LastBlock2=int(LOG08[11]+LOG08[10])
LastBlock3=int(LOG08[13]+LOG08[12])
print "1 Last Block: %s, 2 Last Block: %s, 3 Last Block: %s" %(LastBlock1, LastBlock2, LastBlock3)
if (LastBlock1<=LastBlock2) and (LastBlock2<=LastBlock3):
    mNVME.Print("PASS", "p")
else:
    mNVME.Print("Fail", "f")
    ret_code=1 
   
print ""
print "check if Telemetry Controller-Initiated Data Available(TCIDA) value is persistent across power states and reset or not"
TCIDA_old=LOG08[383]
print "TCIDA: %s" %TCIDA_old
print "-- start test TCIDA for power state  --"
NPSS=mNVME.IdCtrl.NPSS.int
print "NPSS: %s"%NPSS
     
NPSS=mNVME.IdCtrl.NPSS.int
    
for i in range(NPSS+1):
    mNVME.set_feature(2, i)
    print "set power state = %s"%i
    PS=GetPS()
    # verify set_feature successfull
    if PS!=i:
        mNVME.Print("Set power state error! ", "f")
        ret_code=1
        break
            
    # reload     
    LOG07=mNVME.get_log_passthru(7, 512, 1, 0)
    LOG08=mNVME.get_log_passthru(8, 512, 1, 0)
        
    print "TCIDA in log 0x7= %s"%LOG07[383]
    print "TCIDA in log 0x8= %s"%LOG08[383]
    if (TCIDA_old==LOG08[383]) and (TCIDA_old==LOG07[383]):
        mNVME.Print("PASS", "p")    
    else:
        mNVME.Print("Fail", "f")
        ret_code=1    
    
print "-- start test TCIDA for reset  --"

for Item in ResetItem:
    print Item[0]

    # trigger reset
    Item[1]()
    
    # reload 
    print "TCIDA in log 0x7= %s"%LOG07[383]
    print "TCIDA in log 0x8= %s"%LOG08[383]
    if (TCIDA_old==LOG08[383]) and (TCIDA_old==LOG07[383]):
        mNVME.Print("PASS", "p")    
    else:
        mNVME.Print("Fail", "f")
        ret_code=1        

print ""
print "Finish"
sys.exit(ret_code)


























