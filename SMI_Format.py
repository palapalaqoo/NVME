#!/usr/bin/env python
from lib_vct import NVME
from lib_vct import NVMECom
import sys
from time import sleep
import threading
import re


print "Ver: 20180926_1632"
mNVME = NVME.NVME(sys.argv )
  
## paramter #####################################
ret_code=0
SubItemCnt=0
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

def Format100():
    print Format(1, 0, 0)
    
def GetFPIPercentage():
    
    #return int(mNVME.IdNs.FPI.bit(6,0), 2)

    aa= mNVME.IdNs.FPI.bit(6,0)
    return int(aa, 2)

def CheckResult(Result, ExpectedResult):
    global  ret_code
    if ExpectedResult==True:
        CompareStr="Success formatting namespace:1"
    else:
        CompareStr="INVALID_FORMAT\(.*10a\)"
        
    if re.search(CompareStr, Result):
        mNVME.Print("PASS", "p")  
        return 0
    else:
        mNVME.Print("Fail", "f")
        mNVME.Print("Sataus Value: %s"%Result, "f")
        ret_code=1  
        return 1


## end #####################################

print ""
print "-- NVME Format command test" 
print "-----------------------------------------------------------------------------------"

NLBAF=mNVME.IdNs.NLBAF.int
FLBAS=mNVME.IdNs.FLBAS.int
FNA=mNVME.IdCtrl.FNA.int

LBAF=mNVME.GetAllLbaf()

print "Number of LBA Formats (NLBAF): %s"%NLBAF
print "Formatted LBA Size (FLBAS): %s"%FLBAS



print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Check if NLBAF <=15 or not"
if (NLBAF <=  15) :
    mNVME.Print("PASS", "p")     
else:
    mNVME.Print("Fail", "f")
    ret_code=1  
    
print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Check if first lbaf is available or not (LBAF0), expected result: Available"
print "i.e. check if LBA Data Size (LBADS) in LBA Format 0 Support (LBAF0) >= 9 or not "


LBAF0_LBADS=LBAF[0][mNVME.lbafds.LBADS]
print "Value for LBAF0->LBADS: %s"%LBAF0_LBADS
if (LBAF0_LBADS >=  9) :
    mNVME.Print("PASS", "p")     
else:
    mNVME.Print("Fail", "f")
    ret_code=1  



print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Check if status code =0x10a while sending format command with an invalid LBA Format number"

print "if last lbaf is not available(lbaf15), then do this test, or quit this item"
# lbaf15->lbads  >=9 or not
LBAF15_LBADS=LBAF[15][mNVME.lbafds.LBADS]

if LBAF15_LBADS < 9:
    print "Value for LBAF15->LBADS: %s (no available)"%LBAF15_LBADS
    print "set lbaf=15 and send command, then check the status code"
    mStr=Format(1, 15, 0);
    print "status code: %s"%mStr
    CheckResult(mStr, False)
else:
    print "last lbaf is available(lbaf15), i.e. from lbaf0 to lbaf15 are all available, quite this test item!"


print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Test Secure Erase Settings (SES) in Command Dword 10"

print ""    
print "Send format command with SES=000b (No secure erase operation requested)"
mStr=Format(1, 0, 0);
print "Check return code, expected returned status code: Success"
CheckResult(mStr, True)

print ""   
print "Send format command with SES=001b (User Data Erase)"
mStr=Format(1, 0, 1);
print "Check return code, expected returned status code: Success"
CheckResult(mStr, True)

print ""   
SecureEraseSupported=True if  mNVME.IdCtrl.FNA.bit(2)=="1" else False
print "Check if cryptographic erase is supported or not in Format NVM Attributes (FNA) bit 2"
if SecureEraseSupported:
    print "Cryptographic erase is supported"
else:
    print "Cryptographic erase is not supported"

print ""       
print "Send format command with SES=010b (Cryptographic Erase:)"
mStr=Format(1, 0, 2);
print "Check return code, expected returned status code: %s"%("Success" if SecureEraseSupported else "Fail")
CheckResult(mStr, SecureEraseSupported)

print ""       
print "Send format command with SES from 011b to 111b (Reserved)"
print "Check return code, expected returned status code: fail"
for i in range(3, 8):
    mStr=Format(1, 0, i);
    if not re.search("Success formatting namespace:1", mStr):
        mNVME.Print("SES=%s, PASS"%i, "p")
    else:
        mNVME.Print("SES=%s, Fail"%i, "f")
        ret_code = 1

print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Test Protection Information Location (PIL) in Command Dword 10"

print ""
print "Send format command with PIL = 0"
print "Check return code, expected returned status code: Success"
mStr=Format(1, 0, 0, 0);
CheckResult(mStr, True)
print ""
print "Send format command with PIL = 1"
print "Check return code, expected returned status code: Success"
mStr=Format(1, 0, 0, 1);
CheckResult(mStr, True)

print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Test Protection Information (PI) in Command Dword 10"


DPC=mNVME.IdNs.DPC.int
print "End-to-end Data Protection Capabilities (DPC): %s"%DPC
Type1Supported=True if mNVME.IdNs.DPC.bit(0)=="1" else False
Type2Supported=True if mNVME.IdNs.DPC.bit(1)=="1" else False
Type3Supported=True if mNVME.IdNs.DPC.bit(2)=="1" else False

print "Type 1: %s"%"Supported" if Type1Supported else "Not supported"
print "Type 2: %s"%"Supported" if Type2Supported else "Not supported"
print "Type 3: %s"%"Supported" if Type3Supported else "Not supported"


print ""
print "Send format command with PI = 000b"
print "Check return code, expected returned status code: Success"
mStr=Format(1, 0, 0, 0, 0);
CheckResult(mStr, True)

print ""
print "Send format command with PI = 001b"
print "Check return code, expected returned status code: %s"%("Success" if Type1Supported else "Fail")
mStr=Format(1, 0, 0, 0, 1);
CheckResult(mStr, Type1Supported)

print ""
print "Send format command with PI = 010b"
print "Check return code, expected returned status code: %s"%("Success" if Type2Supported else "Fail")
mStr=Format(1, 0, 0, 0, 2);
CheckResult(mStr, Type1Supported)

print ""
print "Send format command with PI = 011b"
print "Check return code, expected returned status code: %s"%("Success" if Type3Supported else "Fail")
mStr=Format(1, 0, 0, 0, 3);
CheckResult(mStr, Type1Supported)



print ""       
print "Send format command with PI from 100b to 111b (Reserved)"
print "Check return code, expected returned status code: fail"
for i in range(4, 8):
    mStr=Format(1, 0, 0, 0, i);
    if not re.search("Success formatting namespace:1", mStr):
        mNVME.Print("PI=%s, PASS"%i, "p")
    else:
        mNVME.Print("PI=%s, Fail"%i, "f")
        ret_code = 1


print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Test Metadata Settings (MSET) in Command Dword 10"

print ""
print "Send format command with MSET = 0"
print "Check return code, expected returned status code: Success"
mStr=Format(1, 0, 0, 0, 0, 0);
CheckResult(mStr, True)
print ""
print "Send format command with MSET = 1"
print "Check return code, expected returned status code: Success"
mStr=Format(1, 0, 0, 0, 0, 1);
CheckResult(mStr, True)





print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Check if the comtroller support the Format Progress Indicator or not(Format Progress Indicator (FPI) bit 7 )"
FPI_bit7=mNVME.IdNs.FPI.bit(7)
if FPI_bit7=="1":
    mNVME.Print( "Support", "p")
else:    
    mNVME.Print( "Not support", "w")
 

    
if FPI_bit7=="1":
    print ""
    print "Test the percentage of the format command in Format Progress Indicator is counting down or not"
    print "Sending format command.. "    
    t = threading.Thread(target = Format100)
    t.start()   
    
    status="waiting for start" 
    per=0
    per_old=0
    per_test_fail=0
    while True:
        per=GetFPIPercentage()
        print per
        
        # first loop when per!=0
        if per!=0 and status!="start":
            status="start"
            per_old=per
        # other loops when per!=0
        elif status=="start":   
            if per > per_old:
                per_test_fail=1 
            per_old=per
        
        #sleep(0.1)
        if per==0:
            break
    t.join()    
    print "Check the percentage is counting down or not, expected result: Counting down"             
    if per_test_fail==0:
        mNVME.Print("PASS", "p")
    else:
        mNVME.Print("Fail", "f")
        ret_code = 1

print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "From LBAF0 to LBAF15, send format command and check if command success while LBAFx is valid "
print "and check if command fail while LBAFX is in valid "

for i in range(16):    
    print ""
    # is support if  LBADS >= 9
    IsValid = True if LBAF[i][mNVME.lbafds.LBADS] >=9 else False
    if IsValid:
        print "LBAF%s is valid"%i
    else:
        print "LBAF%s is not valid"%i  
    
    print "send command for LBAF%s"%i
    mStr=Format(1, i, 0);    
    print "Check return code, expected returned status code: %s"%("Success" if IsValid else "Invalid Format")
    CheckResult(mStr, IsValid)   



print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Check Command Specific Status Values"
print ""
print "specifying an invalid LBA Format number, send command with LBAF=16"
print "Check return code, expected returned status code: Invalid Format"
mStr=Format(1, 16, 0);
CheckResult(mStr, False)

    
print ""
print "enabling protection information when there is no sufficient metadata per LBA"
print "Check return code, expected returned status code: Invalid Format"    

if not Type1Supported:
    mStr=Format(1, 0, 0, 0, 1);
    CheckResult(mStr, False)
elif not Type2Supported:
    mStr=Format(1, 0, 0, 0, 2);
    CheckResult(mStr, False)
elif not Type3Supported:
    mStr=Format(1, 0, 0, 0, 3);
    CheckResult(mStr, False)
else:
    mNVME.Print("All Protection Information type is support, quite this test item!", "w")

print ""
print "the specified format is not available in the current configuration"
print "Check return code, expected returned status code: Invalid Format"
if LBAF15_LBADS < 9:
    mStr=Format(1, 15, 0);
    CheckResult(mStr, False)
else:
    mNVME.Print("All lbaf is available, quite this test item!", "w")

    
    

print ""    
print "ret_code:%s"%ret_code
print "Finish"
sys.exit(ret_code)    
    
    
    
    
    
    
    
    
    
    






