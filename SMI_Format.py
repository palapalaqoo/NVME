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

'''



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
    CheckResult(mStr, Result.INVALID_FORMAT)
else:
    print "last lbaf is available(lbaf15), i.e. from lbaf0 to lbaf15 are all available, quite this test item!"


print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Test Secure Erase Settings (SES) in Command Dword 10"

print ""    
print "Send format command with SES=000b (No secure erase operation requested)"
mStr=Format(1, 0, 0);
print "Check return code, expected returned status code: Success"
CheckResult(mStr, Result.Success)

print ""   
print "Send format command with SES=001b (User Data Erase)"
mStr=Format(1, 0, 1);
print "Check return code, expected returned status code: Success"
CheckResult(mStr, Result.Success)

print ""   


print ""       
print "Send format command with SES=010b (Cryptographic Erase:)"
mStr=Format(1, 0, 2);
print "Check return code, expected returned status code: %s"%("Success" if SecureEraseSupported else "Fail")
CheckResult(mStr, Result.Success) if SecureEraseSupported else CheckResult(mStr, Result.INVALID_FORMAT)



print ""       
print "Send format command with SES from 011b to 111b (Reserved)"
print "Check return code, expected returned status code: fail"
for i in range(3, 8):
    mStr=Format(1, 0, i);
    if not re.search("Success formatting namespace", mStr):
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
CheckResult(mStr, Result.Success)
print ""
print "Send format command with PIL = 1"
print "Check return code, expected returned status code: Success"
mStr=Format(1, 0, 0, 1);
CheckResult(mStr, Result.Success)

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
CheckResult(mStr, Result.Success)

print ""
print "Send format command with PI = 001b"
print "Check return code, expected returned status code: %s"%("Success" if Type1Supported else "Fail")
mStr=Format(1, 0, 0, 0, 1);
CheckResult(mStr, Result.Success) if Type1Supported else CheckResult(mStr, Result.INVALID_FORMAT)

print ""
print "Send format command with PI = 010b"
print "Check return code, expected returned status code: %s"%("Success" if Type2Supported else "Fail")
mStr=Format(1, 0, 0, 0, 2);
CheckResult(mStr, Result.Success) if Type1Supported else CheckResult(mStr, Result.INVALID_FORMAT)

print ""
print "Send format command with PI = 011b"
print "Check return code, expected returned status code: %s"%("Success" if Type3Supported else "Fail")
mStr=Format(1, 0, 0, 0, 3);
CheckResult(mStr, Result.Success) if Type1Supported else CheckResult(mStr, Result.INVALID_FORMAT)



print ""       
print "Send format command with PI from 100b to 111b (Reserved)"
print "Check return code, expected returned status code: fail"
for i in range(4, 8):
    mStr=Format(1, 0, 0, 0, i);
    if not re.search("Success formatting namespace", mStr):
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
CheckResult(mStr, Result.Success)
print ""
print "Send format command with MSET = 1"
print "Check return code, expected returned status code: Success"
mStr=Format(1, 0, 0, 0, 0, 1);
CheckResult(mStr, Result.Success)





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
    t = threading.Thread(target = FormatNSID_01)
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
    CheckResult(mStr, Result.Success) if IsValid else CheckResult(mStr, Result.INVALID_FORMAT)



print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Check Command Specific Status Values"

    
print ""
print "if enabling protection information when there is no sufficient metadata per LBA, then return fail"
print "Check return code, expected returned status code: Invalid Format"    

if not Type1Supported:
    mStr=Format(1, 0, 0, 0, 1);
    CheckResult(mStr, Result.INVALID_FORMAT)
elif not Type2Supported:
    mStr=Format(1, 0, 0, 0, 2);
    CheckResult(mStr, Result.INVALID_FORMAT)
elif not Type3Supported:
    mStr=Format(1, 0, 0, 0, 3);
    CheckResult(mStr, Result.INVALID_FORMAT)
else:
    mNVME.Print("All Protection Information type is support, quite this test item!", "w")

print ""
print "If the specified format is not available in the current configuration, then return fail"
print "Check return code, expected returned status code: Invalid Format"
if LBAF15_LBADS < 9:
    mStr=Format(1, 15, 0);
    CheckResult(mStr, Result.INVALID_FORMAT)
else:
    mNVME.Print("All lbaf is available, quite this test item!", "w")




    
print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Check After the Format NVM command successfully completes"
print "the controller shall not return any user data that was previously contained in an affected namespace"
print "write data at block %s, %s and %s, size=1M"%(mNVME.start_SB, mNVME.middle_SB, mNVME.last_SB)
mNVME.write_SML_data(0xab)
print "send format command"
mStr=Format(1, 0, 0)
print "Check if data at block %s, %s and %s is 0x0 or not"%(mNVME.start_SB, mNVME.middle_SB, mNVME.last_SB)
if mNVME.isequal_SML_data(0x0):
    mNVME.Print("PASS", "p")
else:
    mNVME.Print("FAIL", "f")
    ret_code = 1
  


print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Test if device self-test operation was aborted due to the processing of a Format NVM command"

mNVME.Flow.DST.EventTriggeredMessage="Sending format command while DST execution exceed 40% "
mNVME.Flow.DST.ShowProgress=False

print "Set nsid from 0x1 to %s and 0xffffffff in the format and DST command, then test if DST was aborted or not"%hex(NN)

for i in range(1, NN+1)+[0xFFFFFFFF]:  

    # set DST command nsid
    mNVME.Flow.DST.SetNSID(i)
    # set Event
    mNVME.Flow.DST.SetEventTrigger(FormatNSID, i)

    # mDstType = 1, Short device self-test operation
    # mDstType = 2, 
    for mDstType in [0x1, 0x2]:
        print ""
        print "nsid= %s, %s"%(hex(i), "Short device self-test operation" if mDstType==0x1 else "Extended device self-test operation")
        # set DST type
        mNVME.Flow.DST.SetDstType(mDstType)       
        
        # start DST flow and get device self test status 
        DSTS=mNVME.Flow.DST.Start()
        if DSTS!=-1:        
            # get bit 3:0        
            DSTSbit3to0 = DSTS & 0b00001111
            print "result of the device self-test operation from Get Log Page : %s" %hex(DSTSbit3to0)
            print "Check the result of the device self-test operation , expected result:  0x4"
            if DSTSbit3to0==4:
                mNVME.Print("PASS", "p")
            else:
                mNVME.Print("FAIL", "f")
                ret_code = 1
        else:
            print "Controller does not support the DST operation"
print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Test if device self-test operation was aborted due to the processing of a Format NVM command when"
print "Setting nsid = 0x1 in the DST command"
print "Setting nsid = 0xffffffff in the format command"
# set DST command nsid
mNVME.Flow.DST.SetNSID(0x1)
# set Event
mNVME.Flow.DST.SetEventTrigger(FormatNSID, 0xFFFFFFFF)
# mDstType = 1, Short device self-test operation
# mDstType = 2, 
for mDstType in [0x1, 0x2]:
    print ""
    print "%s"%("Short device self-test operation" if mDstType==0x1 else "Extended device self-test operation")
    # set DST type
    mNVME.Flow.DST.SetDstType(mDstType)             
    # start DST flow and get device self test status 
    DSTS=mNVME.Flow.DST.Start()
    if DSTS!=-1:        
        # get bit 3:0        
        DSTSbit3to0 = DSTS & 0b00001111
        print "result of the device self-test operation from Get Log Page : %s" %hex(DSTSbit3to0)
        if DSTSbit3to0==4:
            mNVME.Print("Operation was aborted due to the processing of a Format NVM command", "p")
        elif DSTSbit3to0==0:
            mNVME.Print("Operation completed without error", "w")
    else:
        print "Controller does not support the DST operation"
print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Test if device self-test operation was aborted due to the processing of a Format NVM command when"
print "Setting nsid = 0xffffffff in the DST command"
print "Setting nsid = 0x1 in the format command"
# set DST command nsid
mNVME.Flow.DST.SetNSID(0xffffffff)
# set Event
mNVME.Flow.DST.SetEventTrigger(FormatNSID, 0x1)
# mDstType = 1, Short device self-test operation
# mDstType = 2, 
for mDstType in [0x1, 0x2]:
    print ""
    print "%s"%("Short device self-test operation" if mDstType==0x1 else "Extended device self-test operation")
    # set DST type
    mNVME.Flow.DST.SetDstType(mDstType)             
    # start DST flow and get device self test status 
    DSTS=mNVME.Flow.DST.Start()
    if DSTS!=-1:        
        # get bit 3:0        
        DSTSbit3to0 = DSTS & 0b00001111
        print "result of the device self-test operation from Get Log Page : %s" %hex(DSTSbit3to0)
        if DSTSbit3to0==4:
            mNVME.Print("Operation was aborted due to the processing of a Format NVM command", "p")
        elif DSTSbit3to0==0:
            mNVME.Print("Operation completed without error", "w")
    else:
        print "Controller does not support the DST operation"
    
'''
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
subret=0
for i in range(1, 17)+[0xffffffff]+random.sample(range(1, 0xffff), 100):
    nsid=i
    
    # send command with ses = Scope(No secure erase operation requested) and Secure Erase Scope(Cryptographic Erase)
    for ses in [0, 2]:
        mStr=Format(nsid, 0, ses)
        if nsid <=NN or nsid==0xffffffff:
            if SecureEraseSupported or ses==0:
                if not CheckResult(mStr, Result.Success, False):
                    print "Fail at nsid = %s, SES = %s, expected returned status code: Success, but got status code: %s"%(nsid, ses, mStr)
                    subret=1        
            else:
                if not CheckResult(mStr, Result.INVALID_FORMAT, False):
                    print "Fail at nsid = %s, SES = %s, expected returned status code: Success, but got status code: %s"%(nsid, ses, mStr)
                    subret=1                   
        else:  
            if not CheckResult(mStr, Result.INVALID_NS, False):
                print "Fail at nsid = %s, SES = %s, expected returned status code: Invalid Namespace or Format, but got status code: %s"%(nsid, ses, mStr)
                subret=1
            
if subret==0:
    mNVME.Print("PASS", "p") 
else:
    mNVME.Print("Fail", "f")


print ""    
print "ret_code:%s"%ret_code
print "Finish"
sys.exit(ret_code)    
    
    
    
    
    
    
    
    
    
    






