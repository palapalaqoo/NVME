#!/usr/bin/env python
from lib_vct import NVME
from lib_vct import NVMECom
import sys
from time import sleep
import threading
import re
import random
from unittest.result import TestResult
from lib_vct.NVMECom import deadline
from lib_vct.NVMECom import TimedOutExc

print "Ver: 20181127_0930"
mNVME = NVME.NVME(sys.argv )

## paramter #####################################
ret_code=0
MoreInfo=0
NLBAF=mNVME.IdNs.NLBAF.int
FLBAS=mNVME.IdNs.FLBAS.int
FNA=mNVME.IdCtrl.FNA.int
NN=mNVME.IdCtrl.NN.int
LBAF=mNVME.GetAllLbaf()
SecureEraseSupported=True if  mNVME.IdCtrl.FNA.bit(2)=="1" else False
DPC=mNVME.IdNs.DPC.int
Type1Supported=True if mNVME.IdNs.DPC.bit(0)=="1" else False
Type2Supported=True if mNVME.IdNs.DPC.bit(1)=="1" else False
Type3Supported=True if mNVME.IdNs.DPC.bit(2)=="1" else False
LBAF15_LBADS=LBAF[15][mNVME.lbafds.LBADS]
FNAbit_0=mNVME.IdCtrl.FNA.bit(0)
FNAbit_1=mNVME.IdCtrl.FNA.bit(1)
    
NsReady=True
StopNs=1
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
    
def FormatNSID(nsid):
    Format(nsid, 0, 0)    
    
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

def Create8NameSpaces():
    rtc=0
    nn=mNVME.IdCtrl.NN.int
    for i in range(1, nn+1):        
        # delete NS
        #if mNVME.ns_exist(i):
        mNVME.DeleteNs(i)    
    mNVME.shell_cmd("nvme reset %s"%mNVME.dev_port)   
    #hot_reset

    # Create namespaces, and attach it
    for i in range(1, 9):
        sleep(0.2)
        CreatedNSID=mNVME.CreateNs()        
        if CreatedNSID != i:
            print "create namespace error!"    
            rtc=1
            break
        else:
            sleep(0.2)
            mNVME.AttachNs(i)
            sleep(0.2)            
            mNVME.shell_cmd("  nvme reset %s " % (mNVME.dev_port))
            
            #hot_reset
      
    if rtc==0:
        return True
    else:
        return False
def ResetNameSpaces():
    rtc=0
    nn=mNVME.IdCtrl.NN.int
    TNVMCAP=mNVME.IdCtrl.TNVMCAP.int
    TotalBlocks=TNVMCAP/512
    
    for i in range(1, nn+1):        
        # delete NS
        #if mNVME.ns_exist(i):
        mNVME.DeleteNs(i)    
    mNVME.shell_cmd("nvme reset %s"%mNVME.dev_port)   
    #hot_reset

    # Create namespaces=1, and attach it
    i=1    
    sleep(0.2)
    CreatedNSID=mNVME.CreateNs(TotalBlocks)        
    if CreatedNSID != i:
        print "create namespace error!"    
        rtc=1
    else:
        sleep(0.2)
        mNVME.AttachNs(i)
        sleep(0.2)
        mNVME.shell_cmd("  nvme reset %s " % (mNVME.dev_port))
        
            
      
    if rtc==0:
        return True
    else:
        return False
        
def WriteBlock(nsid, value):       
# write  block 
        mNVME.fio_write(0,"64k", value, nsid)
def IsEqualBlock(nsid, value):       
# compare block, return true if equal 
        return mNVME.fio_isequal(0,"64k", value, nsid)        
    
def Test_FFFFFFFF(SES):
    global ret_code
    print "  write 64k data to all namespaces with data=0x5c"
    for nsid in range(1, StopNs+1):
        WriteBlock(nsid, 0x5c)
        if not IsEqualBlock(nsid, 0x5c):
            mNVME.Print(  "  write data Fail at nsid = %s"%nsid ,"w")
            
    print "  Done"
    print "  send format command, nsid=0xFFFFFFFF, check if all namespaces was formatted after command"
    Format(0xFFFFFFFF, 0, SES)
    
    TestResult=0
    for nsid in range(1, StopNs+1):
        if not IsEqualBlock(nsid, 0x0):
            mNVME.Print(  "  Fail at nsid = %s"%nsid ,"w")
            TestResult=1
    if  TestResult==0:
        mNVME.Print("  Pass", "p")
    else:
        mNVME.Print("  Fail", "p")
        ret_code = 1
def Test_AllOtherValidValues(SES):
    global ret_code
    print "  write 64k data to all namespaces with data=0x5c"
    for nsid in range(1, StopNs+1):
        WriteBlock(nsid, 0x5c)
        if not IsEqualBlock(nsid, 0x5c):
            mNVME.Print(  "  write data Fail at nsid = %s"%nsid ,"w")
            
    print "  Done"
    print "  send format command, nsid=0x1 to %s, check if particular namespaces was formatted after command"%StopNs
    print "  And other namespaces  should not be modified"
    TestResult=0
    for nsid in range(1, StopNs+1):  
        
        Format(nsid, 0, SES)
        
        # if not first loop, test data in the front of the formating ns  ,should be formatted
        if nsid!=1:
            for i in range(1, nsid):
                if not IsEqualBlock(i, 0x0):
                    mNVME.Print(  "  Fail at format nsid = %s, nsid = %s have unexpected data(modified)"%(nsid, i) ,"f")
                    TestResult=1 
                    
        if not IsEqualBlock(nsid, 0x0):
            mNVME.Print(  "  Fail at format nsid = %s, data is not 0x0"%nsid ,"f")
            TestResult=1
            
        # if not last loop, test data in the back of the formating ns ,should not be formatted
        if nsid!=StopNs:
            for i in range(nsid+1, StopNs+1):
                if not IsEqualBlock(i, 0x5c):
                    mNVME.Print(  "  Fail at format nsid = %s, nsid = %s has been formatted also(modified)"%(nsid, i) ,"f")
                    TestResult=1                    
    if  TestResult==0:
        mNVME.Print("  Pass", "p")
    else:
        mNVME.Print("  Fail", "p")
        ret_code = 1                    

def Test_AllValidValues(SES):
    global ret_code
    print "  write 64k data to all namespaces with data=0x5c"
    for nsid in range(1, StopNs+1):
        WriteBlock(nsid, 0x5c)
        if not IsEqualBlock(nsid, 0x5c):
            mNVME.Print(  "  write data Fail at nsid = %s"%nsid ,"w")
            
    print "  Done"
    print "  send format command, nsid=0x1, check if all namespaces was formatted after command"
    Format(0x1, 0, SES)
    TestResult=0
    for nsid in range(1, StopNs+1):
        if not IsEqualBlock(nsid, 0x0):
            mNVME.Print(  "  Fail at nsid = %s"%nsid ,"w")
            TestResult=1
    if  TestResult==0:
        mNVME.Print("  Pass", "p")
    else:
        mNVME.Print("  Fail", "p")
        ret_code = 1
## end #####################################

@deadline(60)
def info():
    print ""
    print "-- NVME Format command test" 
    print "-----------------------------------------------------------------------------------"
    
    
    
    print "Number of LBA Formats (NLBAF): %s"%NLBAF
    print "Formatted LBA Size (FLBAS): %s"%FLBAS
    print "Number of Namespaces (NN): %s"%NN
    
    print "Cryptographic erase is supported" if SecureEraseSupported else "Cryptographic erase is not supported"

@deadline(60)
def flow0():
    global ret_code
    print ""
    print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
    print "Keyword: The maximum number of LBA formats that may be indicated as supported is 16"
    print "Check if NLBAF <=15 or not"
    if (NLBAF <=  15) :
        mNVME.Print("PASS", "p")     
    else:
        mNVME.Print("Fail", "f")
        ret_code=1  
        
    print ""
    print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
    print "Keyword: LBA formats shall be allocated in order (starting with 0) and packed sequentially"
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
    print "Keyword: specifying an invalid LBA Format number"
    print "Check if status code =0x10a while sending format command with an invalid LBA Format number"
    
    print "if last lbaf is not available(lbaf15), then do this test, or quit this item"
    # lbaf15->lbads  >=9 or not
    
    
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
    print "Keyword: Format NVM - Command Dword 10"
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
    print "Keyword: Format NVM - Command Dword 10"
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
    print "Keyword: Format NVM - Command Dword 10"
    print "Test Protection Information (PI) in Command Dword 10"
    
    
    
    print "End-to-end Data Protection Capabilities (DPC): %s"%DPC

    
    print "Type 1: Supported" if Type1Supported else "Type 1: Not supported"
    print "Type 2: Supported" if Type2Supported else "Type 2: Not supported"
    print "Type 3: Supported" if Type3Supported else "Type 3: Not supported"
    
    
    print ""
    print "Send format command with PI = 000b"
    print "Check return code, expected returned status code: Success"
    mStr=Format(1, 0, 0, 0, 0);
    CheckResult(mStr, Result.Success)
    
    # find LBAF that support Protection Information that if lbafds.MS > 0
    # if find, then send command with PI_SupportedLBAF else LBAF=0
    PI_SupportedLBAF=0
    for i in range(16):
        if LBAF[i][mNVME.lbafds.MS]>0:
            PI_SupportedLBAF=i
            break
    
    print ""
    print "Send format command with PI = 001b"
    print "Check return code, expected returned status code: %s"%("Success" if Type1Supported else "Fail")
    mStr=Format(1, PI_SupportedLBAF, 0, 0, 1);
    CheckResult(mStr, Result.Success) if Type1Supported else CheckResult(mStr, Result.INVALID_FORMAT)
    
    print ""
    print "Send format command with PI = 010b"
    print "Check return code, expected returned status code: %s"%("Success" if Type2Supported else "Fail")
    mStr=Format(1, PI_SupportedLBAF, 0, 0, 2);
    CheckResult(mStr, Result.Success) if Type1Supported else CheckResult(mStr, Result.INVALID_FORMAT)
    
    print ""
    print "Send format command with PI = 011b"
    print "Check return code, expected returned status code: %s"%("Success" if Type3Supported else "Fail")
    mStr=Format(1, PI_SupportedLBAF, 0, 0, 3);
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
    print "Keyword: Format NVM - Command Dword 10"
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
    print "Keyword: Format Progress Indicator (FPI)"
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

@deadline(60)
def flow1():
    global ret_code
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

@deadline(60)
def flow2():
    global ret_code
    print ""
    print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
    print "Keyword: Format NVM - Command Specific Status Values"
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

@deadline(60)
def flow3():
    global ret_code
    DST_Format_ID = [[1, 1], [0xFFFFFFFF, 0xFFFFFFFF],[1, 0xFFFFFFFF], [0xFFFFFFFF, 1]]
    print ""
    print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
    print "Keyword: Get Log Page - Self-test Result Data Structure"
    print "Test if device self-test operation was aborted due to the processing of a Format NVM command"    
    if mNVME.IdCtrl.OACS.bit(4)=="0":
        print "Controller does not support the DST operation, quit this test!"
    else:
        mNVME.Flow.DST.EventTriggeredMessage="Send format command as DST execution >= 1% "
        mNVME.Flow.DST.ShowProgress=True   
            
        for DST_Format in DST_Format_ID:      
            # mDstType = 1, Short device self-test operation
            # mDstType = 2, 
            for mDstType in [0x1, 0x2]:
                IdDST=DST_Format[0]
                IdFormat=DST_Format[1]
                print ""
                print "Setting nsid = %s in the DST command"%hex(IdDST)
                print "Setting nsid = %s in the format command"%hex(IdFormat)
                print "Short device self-test operation" if mDstType==0x1 else "Extended device self-test operation"
                # set DST command nsid
                mNVME.Flow.DST.SetNSID(IdDST)
                # set Event
                mNVME.Flow.DST.SetEventTrigger(FormatNSID, IdFormat)                     
                # set DST type
                mNVME.Flow.DST.SetDstType(mDstType)    
                # set Threshold = 1 to raise event
                mNVME.Flow.DST.SetEventTriggerThreshold(1)
                
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
                        if IdDST==IdFormat:
                            mNVME.Print("FAIL", "f")
                            ret_code = 1
                        else:
                            mNVME.Print("FAIL", "w")
                            mNVME.Print("Warnning! according to NVME Spec 1.3c, page 269, 8.11.1 and 8.11.2", "w")
                            mNVME.Print("shall be aborted by a Format NVM, if the Namespace Identifier field specified in the Format NVM command is the same as- ", "w")
                            mNVME.Print("the Device Self-test command that invoked the device self-test operation ", "w")
                             
                else:
                    print "Controller does not support the DST operation"
              
@deadline(120)
def flow4():
    global ret_code
    global NsReady
    print ""
    print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
    print "Keyword: Format NVM - Format Scope, Format NVM - Secure Erase Scope"
    print "Test Format Scope and Secure Erase Scope"
    
    # geneate vaild namespaces
    # check if controller supports the Namespace Management and Namespace Attachment commands or not
    NsSupported=True if mNVME.IdCtrl.OACS.bit(3)=="1" else False
    if NsSupported:
        print "controller supports the Namespace Management and Namespace Attachment commands"
        
        # set max test namespace <=8
        MaxNs=8 if NN>8 else NN
        print  "create namespcaes form nsid 1 to nsid %s, size 1G, and attach to the controller"%MaxNs
        if not Create8NameSpaces():
            mNVME.Print(  "create namespcaes Fail, exit this test" ,"w")
            NsReady=False
        else:
            StopNs=MaxNs
    
    if NsReady:
        print  ""
        print  "Format NVM - Format Scope"
        if FNAbit_0=="0":
            print  "  FNA bit0=0, test NSID=0xFFFFFFFF, All namespaces attached to the controller"
            Test_FFFFFFFF(0)
            print  "  FNA bit0=0, test NSID=All other valid values, Particular namespace specified"
            Test_AllOtherValidValues(0)
        else:
            print  "  FNA bit0=1, test NSID=All valid values, All namespaces in the NVM subsystem"
            Test_AllValidValues(0)
        
        print ""
        if SecureEraseSupported:      
            print  " Format NVM - Secure Erase Scope"
            if FNAbit_1=="0":
                print  " FNA bit1=0, test NSID=0xFFFFFFFF, All namespaces attached to the controller"
                Test_FFFFFFFF(1)
                print  "  FNA bit1=0, test NSID=All other valid values, Particular namespace specified"
                Test_AllOtherValidValues(1)
            else:
                print  "  FNA bit1=1, test NSID=All valid values, All namespaces in the NVM subsystem"
                Test_AllValidValues(1)    
        else:
            print  "Secure Erase not Supported, will not verify Format NVM - Secure Erase Scope"     
    
    # reset name spaces to 1 ns only
    print  "Reset all namespaces to namespace 1 and kill other namespaces"
    ResetNameSpaces()       

@deadline(60)
def flow5():    
    global ret_code
    print ""
    print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
    print "Keyword: controller shall not return any user data that was previously contained in an affected namespace"
    print "Check data After the Format NVM command successfully completes with SES=0x0 (No secure erase operation requested)"
    print "The controller shall not return any user data that was previously contained in an affected namespace"
    print "write data at block %s, %s and %s, size=1M, patten=%s"%(mNVME.start_SB, mNVME.middle_SB, mNVME.last_SB, "0xab")
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
    print "Keyword: User Data Erase"
    print "Check data After the Format NVM command successfully completes with SES=0x1 (User Data Erase)"
    if not SecureEraseSupported:
        print "Secure Erase is not Supported, quite this test"
    else:
        print "write data at block %s, %s and %s, size=1M, patten=%s"%(mNVME.start_SB, mNVME.middle_SB, mNVME.last_SB, "0xab")
        mNVME.write_SML_data(0xab)
        print "send format command with SES=0x1(User Data Erase)"
        print Format(1, 0, 1)
        print "Check data at block %s, %s and %s, if data is 0x0 or 0xff, then pass the test"%(mNVME.start_SB, mNVME.middle_SB, mNVME.last_SB)
        if mNVME.isequal_SML_data(0x0):
            mNVME.Print("PASS", "p")
        elif mNVME.isequal_SML_data(0xff):
            mNVME.Print("PASS", "p")        
        else:
            mNVME.Print("FAIL", "f")
            ret_code = 1
     
    print ""
    print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
    print "Keyword: Cryptographic Erase"
    print "Check data After the Format NVM command successfully completes with SES=0x2 (Cryptographic Erase )"
    print "This is accomplished by deleting the encryption key."
    print "The data from the controller after Format NVM command is encrypted(garbled)"
    if not SecureEraseSupported:
        print "Secure Erase is not Supported, quite this test"
    else:
        print "write data at block %s, %s and %s, size=1M, patten=%s"%(mNVME.start_SB, mNVME.middle_SB, mNVME.last_SB, "0xab")
        mNVME.write_SML_data(0xab)
        print "send format command with SES=0x2(Cryptographic Erase)"
        print Format(1, 0, 2)
        print "Check data at block %s, %s and %s, if data is 0x0 or 0xff or 0xab, then fail the test"%(mNVME.start_SB, mNVME.middle_SB, mNVME.last_SB)
        if mNVME.isequal_SML_data(0x0):
            mNVME.Print("FAIL", "f")
            ret_code = 1
        elif mNVME.isequal_SML_data(0xff):
            mNVME.Print("FAIL", "f")
            ret_code = 1
        elif mNVME.isequal_SML_data(0xab):
            mNVME.Print("FAIL", "f")
            ret_code = 1
        else:
            mNVME.Print("PASS", "p")        

# ============= Flow start =======================
try:
    flow0()
except TimedOutExc as e:
    mNVME.Print("Timeout 60s", "f")

try:
    flow1()
except TimedOutExc as e:
    mNVME.Print("Timeout 60s", "f")

try:
    flow2()
except TimedOutExc as e:
    mNVME.Print("Timeout 60s", "f") 

try:
    flow3()
except TimedOutExc as e:
    print ""
    mNVME.Print("Timeout 60s, send command to abort DST", "f") 
    mNVME.shell_cmd("LOG_BUF=$(nvme admin-passthru %s --opcode=0x14 --namespace-id=0xffffffff --data-len=0 --cdw10=0xF -r -s 2>&1 > /dev/null)"%(mNVME.dev_port))
    
try:
    flow4()
except TimedOutExc as e: 
    mNVME.Print("Timeout 120s", "f")  
    print  "Reset all namespaces to namespace 1 and kill other namespaces"
    ResetNameSpaces() 
        
try:
    flow5()
except TimedOutExc as e:
    mNVME.Print("Timeout 60s", "f")         
print ""    


print "ret_code:%s"%ret_code
print "Finish"
sys.exit(ret_code)    
    
    
    
    
    
    
    
    
    
    






