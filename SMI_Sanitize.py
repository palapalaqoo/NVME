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




print "Ver: 20181106_0930"
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


## end function #####################################

CryptoEraseSupport = True if (mNVME.IdCtrl.SANICAP.bit(0) == "1") else False
BlockEraseSupport = True if (mNVME.IdCtrl.SANICAP.bit(1) == "1") else False
OverwriteSupport = True if (mNVME.IdCtrl.SANICAP.bit(2) == "1") else False





print ""
print "-- NVME Sanitize test" 
print "-----------------------------------------------------------------------------------"

print "Check Sanitize Capabilities (SANICAP)"
mNVME.Print("Crypto Erase sanitize operation is Supported", "p")  if CryptoEraseSupport else mNVME.Print("Crypto Erase sanitize operation is not Supported", "f") 
mNVME.Print("Block Erase sanitize operation is Supported", "p")  if BlockEraseSupport else mNVME.Print("Block Erase sanitize operation is not Supported", "f") 
mNVME.Print("Overwrite sanitize operation is Supported", "p")  if OverwriteSupport else mNVME.Print("Overwrite sanitize operation is not Supported", "f") 





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
print "ret_code:%s"%ret_code
print "Finish"
sys.exit(ret_code)   

