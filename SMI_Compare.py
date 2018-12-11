#!/usr/bin/env python
from lib_vct import NVME
import sys
from time import sleep
import threading
import re

print "SMI_Compare.py"
print "Author: Sam Chan"
print "Ver: 20181203"
print ""

mNVME = NVME.NVME(sys.argv )


if mNVME.dev_alive:
    print "device alive"
else:    
    print "device missing"
    sys.exit(-1)

  
## paramter #####################################

ret_code=0
MPTRFail=0
DW12Fail=0
DW13Fail=0  
DW14Fail=0
DW15Fail=0


## function #####################################
def CMDisSuccess(mstr):
    cmdsuc0=bool(re.search("NVMe command result:00000000", mstr))
    cmdsuc1=bool(re.search("NVMe Status:COMPARE_FAILED", mstr)) 
    return cmdsuc0 or cmdsuc1

def getDW10_DW11(slba):
    dw10=slba&0xFFFFFFFF
    dw11=slba>>32
    return dw10, dw11


def testDW10_DW11(SLBA, msg0, msg1 , ExpectCommandSuccess):  
    print ""
    print msg0
    print msg1   
    
    cdw10, cdw11=getDW10_DW11(SLBA)
    mStr=mNVME.shell_cmd("dd if=/dev/zero bs=512 count=1 2>&1 |tr \\\\000 \\\\132 |nvme io-passthru %s -o 0x5 -n 1 -l 512 -w --cdw10=%s --cdw11=%s 2>&1 "%(mNVME.dev, cdw10, cdw11))
    retCommandSueess=CMDisSuccess(mStr)
    if (retCommandSueess ==  ExpectCommandSuccess) :
        mNVME.Print("PASS", "p")  
        return True         
    else:
        mNVME.Print("Fail", "f")
        return False   
    
def testDW12(LR, FUA, PRINFO, NLB, ExpectCommandSuccess):      
    #start from block 0
    cdw10, cdw11=getDW10_DW11(0)
    cdw12=(LR<<31) + (FUA<<30)+ (PRINFO<<26) + NLB
    mStr=mNVME.shell_cmd("dd if=/dev/zero bs=512 count=1 2>&1   |tr \\\\000 \\\\132 |nvme io-passthru %s -o 0x5 -n 1 -l 512 -w --cdw10=%s --cdw11=%s --cdw12=%s 2>&1"%(mNVME.dev, cdw10, cdw11, cdw12))
    retCommandSueess=CMDisSuccess(mStr)
    if (retCommandSueess ==  ExpectCommandSuccess) :        
        return True         
    else:
        mNVME.Print("Fail", "f")
        mNVME.Print("LR=%s, FUA=%s, PRINFO=%s, NLB=%s"%(LR, FUA, PRINFO, NLB), "f")
        DW12Fail=1
        return False       

def testDW12NLB(msg0, msg1 ,NLB, ExpectCommandSuccess):      
    print ""
    print msg0
    print msg1   
    cdw12=NLB
    mStr=mNVME.shell_cmd("dd if=/dev/zero bs=512 count=1 2>&1   |tr \\\\000 \\\\132 |nvme io-passthru %s -o 0x5 -n 1 -l 512 -w --cdw10=%s --cdw11=%s --cdw12=%s 2>&1"%(mNVME.dev, 0, 0, cdw12))
    retCommandSueess=CMDisSuccess(mStr)
    if (retCommandSueess ==  ExpectCommandSuccess) :
        mNVME.Print("PASS", "p")  
        return True         
    else:
        mNVME.Print("Fail", "f")
        return False 
    
def testDW13(DSM, ExpectCommandSuccess):      
    mStr=mNVME.shell_cmd("dd if=/dev/zero bs=512 count=1 2>&1   |tr \\\\000 \\\\132 |nvme io-passthru %s -o 0x5 -n 1 -l 512 -w --cdw13=%s 2>&1"%(mNVME.dev, DSM))
    retCommandSueess=CMDisSuccess(mStr)
    if (retCommandSueess ==  ExpectCommandSuccess) :
        return True         
    else:
        mNVME.Print("Fail when DSM=%s"%DSM, "f")
        DW13Fail=1
        return False       

def testDW14(EILBRT, ExpectCommandSuccess):      
    mStr=mNVME.shell_cmd("dd if=/dev/zero bs=512 count=1 2>&1   |tr \\\\000 \\\\132 |nvme io-passthru %s -o 0x5 -n 1 -l 512 -w --cdw14=%s 2>&1"%(mNVME.dev, EILBRT))
    retCommandSueess=CMDisSuccess(mStr)
    if (retCommandSueess ==  ExpectCommandSuccess) :
        return True         
    else:
        mNVME.Print("Fail when EILBRT=%s"%EILBRT, "f")
        DW14Fail=1
        return False    
    
def testDW15(ELBATM,ELBAT, ExpectCommandSuccess):      
    CDW15=(ELBATM<<16)+ELBAT
    mStr=mNVME.shell_cmd("dd if=/dev/zero bs=512 count=1 2>&1   |tr \\\\000 \\\\132 |nvme io-passthru %s -o 0x5 -n 1 -l 512 -w --cdw15=%s 2>&1"%(mNVME.dev, CDW15))
    retCommandSueess=CMDisSuccess(mStr)
    if (retCommandSueess ==  ExpectCommandSuccess) :
        return True         
    else:
        mNVME.Print("Fail when cdw15=%s"%CDW15, "f")
        DW15Fail=1
        return False            
#############################################






print ""
print "-- NVME compare command test" 
print "-----------------------------------------------------------------------------------"

#===============================================================

#===============================================================
print ""
print "-------- Test Command Dword 10 and Command Dword 11 for Starting LBA (SLBA)"

MC=mNVME.IdNs.MC.int
print "Metadata Capabilities (MC): %s"%MC

NUSE=mNVME.IdNs.NUSE.int
print "NUSE: %s"%NUSE

#--------------------------------------------------
SLBA=0
msg0="compare first block, SLBA=%s"%(SLBA)
msg1="check if compare command success(expected result: command success)"
ret_code=ret_code if testDW10_DW11(SLBA, msg0, msg1, True) else 1
   
#--------------------------------------------------
SLBA=NUSE-1
msg0="compare last block, SLBA=%s"%(SLBA)
msg1="check if compare command success(expected result: command success)"
ret_code=ret_code if testDW10_DW11(SLBA, msg0, msg1, True) else 1
   
#--------------------------------------------------
SLBA=NUSE
msg0="compare block exceed the current number of logical blocks allocated in the namespace, SLBA=%s"%(SLBA)
msg1="check if compare command success(expected result: command fail)"
ret_code=ret_code if testDW10_DW11(SLBA, msg0, msg1, False) else 1
#===============================================================
print ""
print "-------- Test Command Dword 12 for LR, FUA, PRINFO"
print "set  cdw[31:26] from 0x0 to 0x3F and check if compare command success(expected result: command success) "

for i in range(0x40):  

    bit26to31=i
    PRINFO=bit26to31 & 0xF
    FUA=(bit26to31 & 0x10) >> 4
    LR=(bit26to31 & 0x20) >> 5
    NLB=0    
    ret_code=ret_code if testDW12(LR, FUA, PRINFO, NLB, True) else 1
    
if DW12Fail==0:
    mNVME.Print("PASS", "p") 
else:
    mNVME.Print("Fail", "f")   

print ""
print "-------- Test Command Dword 12 for NLB"

NLB=0
msg0="set NLB=%s"%(NLB)
msg1="check if compare command success(expected result: command success)"
ret_code=ret_code if testDW12NLB(msg0, msg1, NLB, True) else 1

NLB=mNVME.MDTSinBlock-1
msg0="set NLB=%s Maximum Data Transfer Size in blocks (MDTS)"%(NLB)
msg1="check if compare command success(expected result: command success)"
ret_code=ret_code if testDW12NLB(msg0, msg1, NLB, True) else 1

NLB=mNVME.MDTSinBlock
msg0="set NLB=%s to exceed the maximum transfer size"%(NLB)
msg1="check if compare command success(expected result: command fail)"
ret_code=ret_code if testDW12NLB(msg0, msg1, NLB, False) else 1


#===============================================================

#===============================================================
print ""
print "-------- Test Command Dword 14"
print "set Command Dword 14 from 0x0 to 0xFF and check if compare command success(expected result: command success) "

for i in range(0x100):
    EILBRT= (i<<24) +(i<<16) +(i<<8) + i
    ret_code=ret_code if testDW14(EILBRT, True) else 1

if DW14Fail==0:
    mNVME.Print("PASS", "p") 
else:
    mNVME.Print("Fail", "f")
#===============================================================
print ""
print "-------- Test Command Dword 15"
print "set Command Dword 15 from 0x0 to 0xFF and check if compare command success(expected result: command success) "

for i in range(0x100):
    ELBATM= (i<<8) + i
    ELBAT= (i<<8) + i
    ret_code=ret_code if testDW15(ELBATM,ELBAT, True) else 1

if DW15Fail==0:
    mNVME.Print("PASS", "p") 
else:
    mNVME.Print("Fail", "f")



print ""
print "ret_code:%s"%ret_code
print "Finish"
sys.exit(ret_code)















