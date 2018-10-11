#!/usr/bin/env python
from lib_vct import NVME
from lib_vct import NVMECom
import sys
from time import sleep
import threading
import re
import random

print "Ver: 20180926_1632"
mNVME = NVME.NVME(sys.argv )
  
## paramter #####################################
ret_code=0
MoreInfo=0

# string from nvme cli to verity the status code
class Result:
    Success="Success formatting namespace"
    INVALID_FORMAT="INVALID_FORMAT"
    INVALID_NS="INVALID_NS"
    
## function #####################################


def Format(nsid, lbaf, ses, pil=0, pi=0, ms=0):
    # namespace-id, 
    # LBA Format, 
    # Secure Erase Settings, 
    # Protection Information Location, 
    # Protection Information,
    # Metadata Settings
    mbuf=mNVME.shell_cmd(" nvme format %s -n %s -l %s -s %s -p %s -i %s -m %s 2>&1"%(mNVME.dev_port, nsid, lbaf, ses, pil, pi, ms))
    return mbuf

def FormatNSID_01():
    print Format(0x1, 0, 0)
def FormatNSID_All():
    print Format(0xFFFFFFFF, 0, 0)
    
def FormatNSID(nsid):
    print Format(nsid, 0, 0)    
    
def GetFPIPercentage():
    
    #return int(mNVME.IdNs.FPI.bit(6,0), 2)

    aa= mNVME.IdNs.FPI.bit(6,0)
    return int(aa, 2)

def CheckResult(Result, ExpectedResult, ShowMsg=True):
# Success:     Success formatting namespace
# Fail:            Invalid Format(0AH)
    showmsg=ShowMsg
    global  ret_code
    CompareStr=ExpectedResult

        
    if re.search(CompareStr, Result):
        if showmsg:
            mNVME.Print("PASS", "p")  
        return True
    else:
        if showmsg:
            mNVME.Print("Fail", "f")
            mNVME.Print("Sataus Value: %s"%Result, "f")
        ret_code=1  
        return False

## end #####################################

print ""
print "-- NVME Format command test" 
print "-----------------------------------------------------------------------------------"

NLBAF=mNVME.IdNs.NLBAF.int
FLBAS=mNVME.IdNs.FLBAS.int
FNA=mNVME.IdCtrl.FNA.int
NN=mNVME.IdCtrl.NN.int
LBAF=mNVME.GetAllLbaf()
SecureEraseSupported=True if  mNVME.IdCtrl.FNA.bit(2)=="1" else False

print "Number of LBA Formats (NLBAF): %s"%NLBAF
print "Formatted LBA Size (FLBAS): %s"%FLBAS
print "Number of Namespaces (NN): %s"%NN

print "%s" %"Cryptographic erase is supported" if SecureEraseSupported else "Cryptographic erase is not supported"

print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Test Format Scope and Secure Erase Scope"
print "send format command with nsid from 0x1 to 0x10 and 0xffffffff, then check command accept/reject"
print "send format command with random nsid for 100 times, then check command accept/reject"
print "----------------"
print "If command with SES=0x0 and .."
print "    if nsid<= NN or nsid=0xffffffff and SecureEraseSupported, expected status code=Success"
print "    if nsid<= NN or nsid=0xffffffff and not SecureEraseSupported, expected status code=Success"
print "    if nsid> NN and SecureEraseSupported, expected status code=INVALID_NS"
print "    if nsid> NN and not SecureEraseSupported, expected status code=INVALID_NS"
print "----------------"
print "If command with SES=0x2 and .."
print "    if nsid<= NN or nsid=0xffffffff and SecureEraseSupported, expected status code=Success"
print "    if nsid<= NN or nsid=0xffffffff and not SecureEraseSupported, expected status code=INVALID_FORMAT"
print "    if nsid> NN and SecureEraseSupported, expected status code=INVALID_NS"
print "    if nsid> NN and not SecureEraseSupported, expected status code=INVALID_NS"

#print Format(1, 0, 2);



print ""    
print "ret_code:%s"%ret_code
print "Finish"
sys.exit(ret_code)    
    
    
    
    
    
    
    
    
    
    






