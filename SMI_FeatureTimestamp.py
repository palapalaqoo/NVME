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




print "Ver: 20181105_0930"
mNVME = NVME.NVME(sys.argv )

## paramter #####################################
ret_code = 0
sub_ret=0
## function #####################################

def SetTimeStamp(milliseconds):
    byte0='{:02x}'.format(milliseconds & 0x0000000000FF)
    byte1='{:02x}'.format((milliseconds & 0x00000000FF00) >>8)
    byte2='{:02x}'.format((milliseconds & 0x000000FF0000) >>16)
    byte3='{:02x}'.format((milliseconds & 0x0000FF000000) >>24)
    byte4='{:02x}'.format((milliseconds & 0x00FF00000000) >>32)
    byte5='{:02x}'.format((milliseconds & 0xFF0000000000) >>40)

    mNVME.shell_cmd("echo -n -e '\\x%s\\x%s\\x%s\\x%s\\x%s\\x%s' |nvme admin-passthru %s -o 0x9 -l 8 -w --cdw10=0xE 2>&1"%(byte0, byte1, byte2, byte3, byte4, byte5, mNVME.dev))

def PrintFormatedTime():
    global Timestamp
    mDS.Refresh()
    Timestamp=mDS.Timestamp
    print "Read Timestamp = %s (%s milliseconds)"%(hex(Timestamp), Timestamp)
    #      localtime or gmtime
    mStr=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(Timestamp/1000))
    print "Formatted Timestamp(local time) = %s "%mStr
    return  Timestamp
    

class DataStructure():
    
    def Refresh(self):
        mDS=self._DataStructure()
        if not len(mDS)==8:
            mNVME.Print("Get feature fail", "f")
            print "quit all the test items!"
            ret_code=0 
            print "ret_code:%s"%ret_code
            print "Finish"
            sys.exit(ret_code)          
        else:
            self.DS=mDS
            return 0
        
    @property
    def Timestamp(self):
        return int(self.DS[0], 16) + (int(self.DS[1], 16)<<8) + (int(self.DS[2], 16)<<16) + (int(self.DS[3], 16)<<24) + (int(self.DS[4], 16)<<32) + (int(self.DS[5], 16)<<40)
    
    @property
    def Origin(self):
    # return int, range 0 to 7
        return (int(self.DS[6], 16) & 0b00001110) >>1
    
    @property
    def Synch(self):
    # return int, range 0 to 1
        return int(self.DS[6], 16) & 0b00000001
        
    def _DataStructure(self):
        # get DataStructure of time stamp
        # return 8 bytes
        mbuf=mNVME.shell_cmd("nvme admin-passthru %s --opcode=0xA --data-len=8 -r --cdw10=0xE 2>&1"%mNVME.dev)
        line="0"
        # if command success
        if re.search("NVMe command result:00000000", mbuf):
            patten=re.findall("\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}", mbuf)            
            patten1= ''.join(patten)
            line=patten1.replace(" ", "")
            # return list
            # put patten in to list type
            n=2
            return [line[i:i+n] for i in range(0, len(line), n)]    
        else:
            return [0]    

## end function #####################################
ONCS_bit6 = mNVME.IdCtrl.ONCS.bit(6)
mDS = DataStructure()
mDS.Refresh()
Synch = mDS.Synch

print ""
print "-- NVME Timestamp (Feature Identifier 0Eh) test" 
print "-----------------------------------------------------------------------------------"

print ""
print "Check if controll support Timestamp or not"
if ONCS_bit6=="1":
    mNVME.Print("Supported", "p")
    
else:
    mNVME.Print("Not supported", "p")
    print "quit all the test items!"
    ret_code=0 
    print "ret_code:%s"%ret_code
    print "Finish"
    sys.exit(ret_code)  
'''    
print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Keyword: The Timestamp field was initialized to ‘0’ by a Controller Level Reset."
print "If there is a Controller Level Reset, then the Timestamp Origin field must be set to 000b "
print "And The Timestamp field was initialized to ‘0’ by a Controller Level Reset."
print "Test If the Timestamp Origin field in Data Structure was set to 000b"
print "Then the Timestamp is set to the time in milliseconds since the last Controller Level Reset."
print ""
print "Send nvme reset command(Controller Level Reset)"
mNVME.nvme_reset()

print ""
print "Get Timestamp"
Timestamp = PrintFormatedTime()

print ""
Origin= mDS.Origin
print "Timestamp Origin = %s"%Origin
print "Check if Timestamp Origin field is set to 000b or not"
if Origin==0:
    mNVME.Print("PASS", "p")
else:
    mNVME.Print("Fail", "f")
    ret_code=1  

'''
    
print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Keyword: Synch"
print "Test the accuracy of Timestamp values"
print ""
#print "Send nvme reset command(Controller Level Reset)"
mNVME.nvme_reset()
print ""
print "Synch = %s"%Synch
if Synch==1:    
    print "Becouse Synch=1, In case of the controller may have stopped counting during vendor specific"
    print "Create a thread of compare operation to avoid controller enter non-operational power states"
    DWUATT=NVME.DevWakeUpAllTheTime(mNVME)
    DWUATT.Start()

last_Timestamp=0 
sub_ret=0
# Timestamp

print ""
print "print Timestamp every 1 second for 5 times"
print ""

for cnt in range(6):    
    Timestamp = PrintFormatedTime()
    if (Timestamp-last_Timestamp<900 or Timestamp-last_Timestamp>1100) and cnt !=0:
        sub_ret=1
    last_Timestamp=Timestamp
    sleep(1)

print ""
print "Check if Timestamp was incresed appropriately (> 0.9 second and < 1.1 second for every loop)"
if sub_ret==0:
    mNVME.Print("PASS", "p")
else:
    mNVME.Print("Fail", "f")
    ret_code=1  



if Synch==1: 
    print ""
    print "Delete thread of compare operation"
    DWUATT.Stop()

print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Keyword: The Timestamp field was initialized with a Timestamp value using a Set Features command."
print "If host set the Timestamp value, then the Timestamp Origin field must be set to 001b "

print "Set Timestamp=0"
SetTimeStamp(0)


print ""
print "Get Timestamp"
Timestamp = PrintFormatedTime()
print ""
print "Check if Timestamp field was initialized with a Timestamp value using a Set Features command or not(e.g. Timestamp<=100 milliseconds)"
if Timestamp<=100:
    mNVME.Print("PASS", "p")
else:
    mNVME.Print("Fail", "f")
    ret_code=1  

Origin= mDS.Origin
print "Timestamp Origin = %s"%Origin
print "Check if Timestamp Origin field is set to 001b or not"
if Origin==1:
    mNVME.Print("PASS", "p")
else:
    mNVME.Print("Fail", "f")
    ret_code=1  





print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Keyword: Timestamp field"
print "If the sum of the Timestamp value set by the host and the elapsed time exceeds 2^48, the value returned should be reduced modulo 2^48 "

if Synch==1:    
    print ""
    print "Becouse Synch=1, In case of the controller may have stopped counting during vendor specific"
    print "Create a thread of compare operation to avoid controller enter non-operational power states"
    DWUATT=NVME.DevWakeUpAllTheTime(mNVME)
    DWUATT.Start()

print ""
print "Set Timestamp=0xFFFFFFFFFFF0"
SetTimeStamp(0xFFFFFFFFFFF0)
PrintFormatedTime()

print ""
print "wait 2 seconds"
sleep(2)

print ""
print "Get Timestamp"
Timestamp = PrintFormatedTime()

print ""
print "Check if Timestamp was be reduced modulo 2^48(e.g. Timestamp <= 2100 milliseconds)"
if Timestamp<=2100:
    mNVME.Print("PASS", "p")
else:
    mNVME.Print("Fail", "f")
    ret_code=1  

if Synch==1: 
    print ""
    print "Delete thread of compare operation"
    DWUATT.Stop()










print ""    
print "ret_code:%s"%ret_code
print "Finish"
sys.exit(ret_code)   

