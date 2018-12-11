#!/usr/bin/env python
from lib_vct import NVME
import sys
from time import sleep
import threading
import re

print "SMI_FeatureNumberofQueues.py"
print "Author: Sam Chan"
print "Ver: 20181203"
print ""
mNVME = NVME.NVME(sys.argv )
  
## paramter #####################################
ret_code=0
## function #####################################
## end #####################################

print ""
print "-- NVME Feature Number of Queues" 
print "-----------------------------------------------------------------------------------"
print ""
print "Test if NCQR specified is 65,535, the controller should return an error of Invalid Field in Command or not" 
print "set NCQR=0xFFFF, NSQR=0x0"
mStr=mNVME.shell_cmd(" nvme set-feature %s -f 7 -v 0xFFFF0000 2>&1"%(mNVME.dev))
print "returned status code: %s" %mStr
print "Check returned status code"
retCommandSueess=bool(re.search("INVALID_FIELD", mStr))
if (retCommandSueess ==  True) :
    mNVME.Print("PASS", "p")     
else:
    mNVME.Print("Fail", "f")
    ret_code=1

#-----------------------------------------------------------------------------------
print ""
print "Test if NSQR specified is 65,535, the controller should return an error of Invalid Field in Command or not" 
print "set NCQR=0x0, NSQR=0xFFFF"
mStr=mNVME.shell_cmd(" nvme set-feature %s -f 7 -v 0x0000FFFF 2>&1"%(mNVME.dev))
print "returned status code: %s" %mStr
print "Check returned status code"
retCommandSueess=bool(re.search("INVALID_FIELD", mStr))
if (retCommandSueess ==  True) :
    mNVME.Print("PASS", "p")     
else:
    mNVME.Print("Fail", "f")
    ret_code=1    
    
#-----------------------------------------------------------------------------------
print ""
print "Test get feature for NCQA and NSQA" 
mStr=mNVME.shell_cmd(" nvme get-feature %s -f 7 2>&1"%(mNVME.dev))
print mStr
retCommandSueess=bool(re.search("Current value", mStr))
if (retCommandSueess ==  True) :
    mNVME.Print("PASS", "p")     
else:
    mNVME.Print("Fail", "f")
    ret_code=1        
    
print ""
print "ret_code:%s"%ret_code
print "Finish"
sys.exit(ret_code)


