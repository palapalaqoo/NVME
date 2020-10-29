#!/usr/bin/env python
# -*- coding: utf-8 -*-

        #=======================================================================
        # abstract  function
        #     SubCase1() to SubCase32()                            :Override it for sub case 1 to sub case32
        # abstract  variables
        #     SubCase1Desc to SubCase32Desc                 :Override it for sub case 1 description to sub case32 description
        #     SubCase1Keyword to SubCase32Keyword    :Override it for sub case 1 keyword to sub case32 keyword
        #     self.ScriptName, self.Author, self.Version      :self.ScriptName, self.Author, self.Version
        #=======================================================================     
        
# Import python built-ins
import sys
import time
from time import sleep
import threading
import re
from random import randint

# Import VCT modules
from lib_vct.NVME import NVME
from lib_vct.NVMECom import deadline

class SMI_Format(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_Format.py"
    Author = "Sam Chan"
    Version = "20201029"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    Status_InvalidFormat = "INVALID_FORMAT"
    Status_InvalidField = "INVALID_FIELD"
    Status_InvalidNS = "INVALID_NS"
    Status_Success = "Success formatting namespace"
    
    Expected_Success = 0
    Expected_Fail = 1
    Expected_InvalidFormat = 2
    
    CryptographicErasePass_0 = "SMI2260"
    CryptographicErasePass_1 = "SMI2262"
    CryptographicErasePass_2 = "SMI2263"
    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def GetHealthLog(self):
        Value=[]
        Value.append(["CompositeTemperature", self.GetLog.SMART.CompositeTemperature])
        Value.append(["CriticalWarning", self.GetLog.SMART.CriticalWarning])
        Value.append(["AvailableSpare", self.GetLog.SMART.AvailableSpare])
        Value.append(["AvailableSpareThreshold", self.GetLog.SMART.AvailableSpareThreshold])
        Value.append(["PercentageUsed", self.GetLog.SMART.PercentageUsed])
        Value.append(["DataUnitsRead", self.GetLog.SMART.DataUnitsRead])
        Value.append(["DataUnitsWritten", self.GetLog.SMART.DataUnitsWritten])
        Value.append(["HostReadCommands", self.GetLog.SMART.HostReadCommands])
        Value.append(["HostWriteCommands", self.GetLog.SMART.HostWriteCommands])
        Value.append(["ControllerBusyTime", self.GetLog.SMART.ControllerBusyTime])
        Value.append(["PowerCycles", self.GetLog.SMART.PowerCycles])
        Value.append(["PowerOnHours", self.GetLog.SMART.PowerOnHours])
        Value.append(["UnsafeShutdowns", self.GetLog.SMART.UnsafeShutdowns])
        Value.append(["MediaandDataIntegrityErrors", self.GetLog.SMART.MediaandDataIntegrityErrors])
        Value.append(["NumberofErrorInformationLogEntries", self.GetLog.SMART.NumberofErrorInformationLogEntries])
        Value.append(["WarningCompositeTemperatureTime", self.GetLog.SMART.WarningCompositeTemperatureTime])
        Value.append(["CriticalCompositeTemperatureTime", self.GetLog.SMART.CriticalCompositeTemperatureTime])
        Value.append(["ThermalManagementTemperature1TransitionCount", self.GetLog.SMART.ThermalManagementTemperature1TransitionCount])
        Value.append(["ThermalManagementTemperature2TransitionCount", self.GetLog.SMART.ThermalManagementTemperature2TransitionCount])
        Value.append(["TotalTimeForThermalManagementTemperature1", self.GetLog.SMART.TotalTimeForThermalManagementTemperature1])
        Value.append(["TotalTimeForThermalManagementTemperature2", self.GetLog.SMART.TotalTimeForThermalManagementTemperature2])
        return Value
    
    def Format(self, nsid, lbaf, ses, pil=0, pi=0, ms=0):
        # namespace-id, 
        # LBA format, 
        # Secure Erase Settings, 
        # Protection Information Location, 
        # Protection Information,
        # Metadata Settings
        mbuf=self.shell_cmd(" nvme format %s -n %s -l %s -s %s -p %s -i %s -m %s 2>&1"%(self.dev_port, nsid, lbaf, ses, pil, pi, ms))
        return mbuf
    
    def FormatNSID_01(self):
        self.Print( self.Format(0x1, 0, 0) )
        
    def ThreadFIOwriteForCase17(self):
        CMD = "fio --direct=1 --iodepth=16 --ioengine=libaio --bs=64k --rw=write --numjobs=1"\
        " --filename=%s --name=mdata --runtime=60"%self.dev
        self.Print("Thread msg-> issue fio cmd: %s"%CMD)
        self.shell_cmd(CMD)

    def ThreadFormatCmdForCase17(self):
        CMD = "nvme format %s -n 1 -l 0"%self.dev_port
        self.Print("Thread msg-> issue format cmd: %s"%CMD)
        self.threadFlag=True
        self.shell_cmd(CMD)
        self.threadFlag=False
                
    def FormatNSID(self, nsid):
        self.Format(nsid, 0, 0)    
        
    def GetFPIPercentage(self):
        
        #return int(self.IdNs.FPI.bit(6,0), 2)
    
        aa= self.IdNs.FPI.bit(6,0)
        return int(aa, 2)
    
    def CheckResult(self, ResultStr, ExpectedResult, ShowMsg=True):
    # Success:     Success Formatting namespace
    # Fail:            Invalid Format(0AH) or others
    # ExpectedResult: 0= success, 1= fail
    
        Pass=0
        Fail=1
        Result=Fail
        # ---------------------------------------------
        if ExpectedResult==self.Expected_Success:
            CompareStr=self.Status_Success
            if re.search(CompareStr, ResultStr):            
                Result=Pass
                        
        elif ExpectedResult==self.Expected_Fail:
            CompareStr=self.Status_Success
            if not re.search(CompareStr, ResultStr):            
                Result=Pass

        elif ExpectedResult==self.Expected_InvalidFormat:
            CompareStr=self.Status_InvalidFormat
            if re.search(CompareStr, ResultStr):            
                Result=Pass
        # ---------------------------------------------    
        if Result==Pass:
            if ShowMsg:
                self.Print("PASS", "p")  
            return True
        else:
            if ShowMsg:
                self.Print("Fail", "f")
                self.Print("Sataus Value: %s"%ResultStr, "f")  
            return False              
    
    def ResetNameSpaces(self):
        rtc=0
        nn=self.IdCtrl.NN.int
        TNVMCAP=self.IdCtrl.TNVMCAP.int
        TotalBlocks=TNVMCAP/512
        
        for i in range(1, nn+1):        
            # delete NS
            #if self.ns_exist(i):
            self.DeleteNs(i)    
        self.shell_cmd("nvme reset %s"%self.dev_port)   
        #hot_reset
    
        # Create namespaces=1, and attach it
        i=1    
        sleep(0.2)
        CreatedNSID=self.CreateNs(TotalBlocks)        
        if CreatedNSID != i:
            self.Print ("create namespace error!"    )
            rtc=1
        else:
            sleep(0.2)
            self.AttachNs(i)
            sleep(0.2)
            self.shell_cmd("  nvme reset %s " % (self.dev_port))
            
                
          
        if rtc==0:
            return True
        else:
            return False
            
    def WriteBlock(self, nsid, value):       
    # write  block 
            self.fio_write(0,"64k", value, nsid)
    def IsEqualBlock(self, nsid, value):       
    # compare block, return true if equal 
            return self.fio_isequal(0,"64k", value, nsid)        
        
    def Test_FFFFFFFF(self, SES):
        ret_code=0
        self.Print ("  write 64k data to all namespaces with data=0x5c")
        for nsid in range(1, self.StopNs+1):
            self.WriteBlock(nsid, 0x5c)
            if not self.IsEqualBlock(nsid, 0x5c):
                self.Print(  "  write data Fail at nsid = %s"%nsid ,"w")
                
        self.Print ("  Done")
        self.Print ("  send format command, nsid=0xFFFFFFFF, check if all namespaces was formatted after command")
        self.Format(0xFFFFFFFF, 0, SES)
        
        TestResult=0
        for nsid in range(1, self.StopNs+1):
            if not self.IsEqualBlock(nsid, 0x0):
                self.Print(  "  Fail at nsid = %s"%nsid ,"w")
                TestResult=1
        if  TestResult==0:
            self.Print("  Pass", "p")
        else:
            self.Print("  Fail", "p")
            ret_code = 1
        return ret_code
    def Test_AllOtherValidValues(self, SES):
        ret_code=0
        self.Print ("  write 64k data to all namespaces with data=0x5c")
        for nsid in range(1, self.StopNs+1):
            self.WriteBlock(nsid, 0x5c)
            if not self.IsEqualBlock(nsid, 0x5c):
                self.Print(  "  write data Fail at nsid = %s"%nsid ,"w")
                
        self.Print ("  Done")
        self.Print ("  send format command, nsid=0x1 to %s, check if particular namespaces was formatted after command"%self.StopNs)
        self.Print ("  And other namespaces  should not be modified")
        TestResult=0
        for nsid in range(1, self.StopNs+1):  
            
            self.Format(nsid, 0, SES)
            
            # if not first loop, test data in the front of the formating ns  ,should be formatted
            if nsid!=1:
                for i in range(1, nsid):
                    if not self.IsEqualBlock(i, 0x0):
                        self.Print(  "  Fail at format nsid = %s, nsid = %s have unexpected data(modified)"%(nsid, i) ,"f")
                        TestResult=1 
                        
            if not self.IsEqualBlock(nsid, 0x0):
                self.Print(  "  Fail at format nsid = %s, data is not 0x0"%nsid ,"f")
                TestResult=1
                
            # if not last loop, test data in the back of the formating ns ,should not be formatted
            if nsid!=self.StopNs:
                for i in range(nsid+1, self.StopNs+1):
                    if not self.IsEqualBlock(i, 0x5c):
                        self.Print(  "  Fail at format nsid = %s, nsid = %s has been formatted also(modified)"%(nsid, i) ,"f")
                        TestResult=1                    
        if  TestResult==0:
            self.Print("  Pass", "p")
        else:
            self.Print("  Fail", "p")
            ret_code = 1                    
        return ret_code

    def Test_AllValidValues(self, SES):
        ret_code=0
        self.Print ("  write 64k data to all namespaces with data=0x5c")
        for nsid in range(1, self.StopNs+1):
            self.WriteBlock(nsid, 0x5c)
            if not self.IsEqualBlock(nsid, 0x5c):
                self.Print(  "  write data Fail at nsid = %s"%nsid ,"w")
                
        self.Print ("  Done")
        self.Print ("  send format command, nsid=0x1, check if all namespaces was formatted after command")
        self.Format(0x1, 0, SES)
        TestResult=0
        for nsid in range(1, self.StopNs+1):
            if not self.IsEqualBlock(nsid, 0x0):
                self.Print(  "  Fail at nsid = %s"%nsid ,"w")
                TestResult=1
        if  TestResult==0:
            self.Print("  Pass", "p")
        else:
            self.Print("  Fail", "p")
            ret_code = 1    
        return ret_code


    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def __init__(self, argv):
        # initial parent class
        super(SMI_Format, self).__init__(argv)
        
        self.NLBAF=self.IdNs.NLBAF.int
        self.FLBAS=self.IdNs.FLBAS.int
        self.FNA=self.IdCtrl.FNA.int
        self.NN=self.IdCtrl.NN.int
        self.LBAF=self.GetAllLbaf()
        self.SecureEraseSupported=True if  self.IdCtrl.FNA.bit(2)=="1" else False
        self.DPC=self.IdNs.DPC.int
        self.Type1Supported=True if self.IdNs.DPC.bit(0)=="1" else False
        self.Type2Supported=True if self.IdNs.DPC.bit(1)=="1" else False
        self.Type3Supported=True if self.IdNs.DPC.bit(2)=="1" else False
        self.LBAF15_LBADS=self.LBAF[15][self.lbafds.LBADS]
        self.FNAbit_0=self.IdCtrl.FNA.bit(0)
        self.FNAbit_1=self.IdCtrl.FNA.bit(1)
        
        
        self.NsReady=True
        self.StopNs=1     
        
        self.threadFlag=False             
        
    # =======================================================================================    
    # override pretest  
    def PreTest(self):        
        self.Print ("")
        self.Print ("-- NVME format command test" )
        self.Print ("-----------------------------------------------------------------------------------"            )
        self.Print ("Number of LBA formats (self.NLBAF): %s"%self.NLBAF)
        self.Print ("formatted LBA Size (self.FLBAS): %s"%self.FLBAS)
        self.Print ("Number of Namespaces (NN): %s"%self.NN    )
        self.Print ("Cryptographic erase is supported" if self.SecureEraseSupported else "Cryptographic erase is not supported" )
        self.Print ("-----------------------------------------------------------------------------------"       )
        self.Print ("")
        return True
                                        
    # <sub item scripts>
    SubCase1TimeOut = 600
    SubCase1Desc = "Check if NLBAF <=15 or not"   
    SubCase1KeyWord = "The maximum number of LBA formats that may be indicated as supported is 16"
    def SubCase1(self):
        ret_code=0
        if (self.NLBAF <=  15) :
            self.Print("PASS", "p")     
        else:
            self.Print("Fail", "f")
            ret_code=1  
        return ret_code
    
    SubCase2TimeOut = 600
    SubCase2Desc = "Check LBAF0"
    SubCase2KeyWord = "LBA formats shall be allocated in order (starting with 0) and packed sequentially"
    def SubCase2(self): 
        ret_code=0
        self.Print ("Check if first lbaf is available or not (self.LBAF0), expected result: Available")
        self.Print ("i.e. check if LBA Data Size (LBADS) in LBA format 0 Support (self.LBAF0) >= 9 or not ")
        
        
        self.LBAF0_LBADS=self.LBAF[0][self.lbafds.LBADS]
        self.Print ("Value for self.LBAF0->LBADS: %s"%self.LBAF0_LBADS)
        if (self.LBAF0_LBADS >=  9) :
            self.Print("PASS", "p")     
        else:
            self.Print("Fail", "f")
            ret_code=1  
        
        return ret_code

    SubCase3TimeOut = 6000
    SubCase3Desc = "Test sending format command with an invalid LBA format number"
    SubCase3KeyWord = "Specifying an invalid LBA format number"
    def SubCase3(self): 
        ret_code=0
        
        self.Print ("if last lbaf is not available(lbaf15), then do this test, or quit this item")
        # lbaf15->lbads  >=9 or not
        
        
        if self.LBAF15_LBADS < 9:
            self.Print ("Value for self.LBAF15->LBADS: %s (no available)"%self.LBAF15_LBADS)
            self.Print ("set lbaf=15 and send command, then check the status code")
            mStr=self.Format(1, 15, 0);
            self.Print ("status code: %s"%mStr)
            if not self.CheckResult(mStr, self.Expected_Fail):
                ret_code=1
        else:
            self.Print ("last lbaf is available(lbaf15), i.e. from lbaf0 to lbaf15 are all available, quite this test item!")
            
        return ret_code

    SubCase4TimeOut = 600
    SubCase4Desc = "Test Secure Erase Settings (SES) in Command Dword 10"
    SubCase4KeyWord = "format NVM - Command Dword 10"
    def SubCase4(self): 
        ret_code=0
        
        self.Print (""    )
        self.Print ("Send format command with SES=000b (No secure erase operation requested)")
        mStr=self.Format(1, 0, 0);
        self.Print ("Check return code, expected returned status code: Success")
        ret_code = ret_code if self.CheckResult(mStr, self.Expected_Success) else 1
        
        self.Print (""   )
        self.Print ("Send format command with SES=001b (User Data Erase)")
        mStr=self.Format(1, 0, 1);
        self.Print ("Check return code, expected returned status code: Success")
        ret_code = ret_code if self.CheckResult(mStr, self.Expected_Success) else 1
        
        self.Print (""   )
        
        
        self.Print (""       )
        self.Print ("Send format command with SES=010b (Cryptographic Erase:)")
        mStr=self.Format(1, 0, 2);
        self.Print ("Check return code, expected returned status code: %s"%("Success" if self.SecureEraseSupported else "Fail"))
        if self.SecureEraseSupported:
            ret_code = ret_code if self.CheckResult(mStr, self.Expected_Success) else 1
        else:
            ret_code = ret_code if self.CheckResult(mStr, self.Expected_Fail) else 1        
        
        
        self.Print (""       )
        self.Print ("Send format command with SES from 011b to 111b (Reserved)")
        self.Print ("Check return code, expected returned status code: fail")
        for i in range(3, 8):
            mStr=self.Format(1, 0, i);
            if not re.search("Success formatting namespace", mStr):
                self.Print("SES=%s, PASS"%i, "p")
            else:
                self.Print("SES=%s, Fail"%i, "f")
                ret_code = 1
        
        return ret_code

    SubCase5TimeOut = 600
    SubCase5Desc = "Test Protection Information Location (PIL)"
    SubCase5KeyWord = "format NVM - Command Dword 10"
    def SubCase5(self): 
        ret_code=0
        self.Print ("")
        self.Print ("Send format command with PIL = 0, PI = 0")
        self.Print ("Check return code, expected returned status code: Success")
        mStr=self.Format(1, 0, 0, 0);
        ret_code = ret_code if self.CheckResult(mStr, self.Expected_Success) else 1
        self.Print ("")
        self.Print ("Send format command with PIL = 1, PI = 0")
        self.Print ("Check return code, expected returned status code: Success")
        mStr=self.Format(1, 0, 0, 1);
        ret_code = ret_code if self.CheckResult(mStr, self.Expected_Success) else 1
        self.Print ("")
        self.Print ("Send format command with PIL = 0, PI = 0")
        self.Print ("Check return code, expected returned status code: Success")
        mStr=self.Format(1, 0, 0, 0);
        ret_code = ret_code if self.CheckResult(mStr, self.Expected_Success) else 1        
        return ret_code

    SubCase6TimeOut = 600
    SubCase6Desc = "Test Protection Information (PI)"
    SubCase6KeyWord = "format NVM - Command Dword 10"
    def SubCase6(self): 
        ret_code=0
    
        self.Print ("End-to-end Data Protection Capabilities (self.DPC): %s"%self.DPC)
    
        
        self.Print ("Type 1: Supported" if self.Type1Supported else "Type 1: Not supported")
        self.Print ("Type 2: Supported" if self.Type2Supported else "Type 2: Not supported")
        self.Print ("Type 3: Supported" if self.Type3Supported else "Type 3: Not supported")
        
        
        self.Print ("")
        self.Print ("Send format command with PIL = 0, PI = 000b")
        self.Print ("Check return code, expected returned status code: Success")
        mStr=self.Format(1, 0, 0, 0, 0);
        ret_code = ret_code if self.CheckResult(mStr, self.Expected_Success) else 1
        
        # find self.LBAF that support Protection Information that if lbafds.MS > 0
        # if find, then send command with PI_Supportedself.LBAF else self.LBAF=0
        PI_SupportedLBAF=0
        for i in range(16):
            if self.LBAF[i][self.lbafds.MS]>0:
                PI_SupportedLBAF=i
                break
        
        self.Print ("")
        self.Print ("Send format command with PIL = 0, PI = 001b")
        self.Print ("Check return code, expected returned status code: %s"%("Success" if self.Type1Supported else "Fail"))
        mStr=self.Format(1, PI_SupportedLBAF, 0, 0, 1);
        if self.Type1Supported:
            ret_code = ret_code if self.CheckResult(mStr, self.Expected_Success) else 1
        else:
            ret_code = ret_code if self.CheckResult(mStr, self.Expected_Fail) else 1
        
        self.Print ("")
        self.Print ("Send format command with PIL = 0, PI = 010b")
        self.Print ("Check return code, expected returned status code: %s"%("Success" if self.Type2Supported else "Fail"))
        mStr=self.Format(1, PI_SupportedLBAF, 0, 0, 2);
        if self.Type1Supported:
            ret_code = ret_code if self.CheckResult(mStr, self.Expected_Success) else 1
        else:
            ret_code = ret_code if self.CheckResult(mStr, self.Expected_Fail) else 1
            
                    
        self.Print ("")
        self.Print ("Send format command with PIL = 0, PI = 011b")
        self.Print ("Check return code, expected returned status code: %s"%("Success" if self.Type3Supported else "Fail"))
        mStr=self.Format(1, PI_SupportedLBAF, 0, 0, 3);
        if self.Type1Supported:
            ret_code = ret_code if self.CheckResult(mStr, self.Expected_Success) else 1
        else:
            ret_code = ret_code if self.CheckResult(mStr, self.Expected_Fail) else 1        
        
        
        self.Print (""       )
        self.Print ("Send format command with PIL = 0, PI from 100b to 111b (Reserved)")
        self.Print ("Check return code, expected returned status code: fail")
        for i in range(4, 8):
            mStr=self.Format(1, 0, 0, 0, i);
            if not re.search("Success formatting namespace", mStr):
                self.Print("PI=%s, PASS"%i, "p")
            else:
                self.Print("PI=%s, Fail"%i, "f")
                ret_code = 1
        return ret_code

    SubCase7TimeOut = 600
    SubCase7Desc = "Test Metadata Settings (MSET) "
    SubCase7KeyWord = "format NVM - Command Dword 10"
    def SubCase7(self): 
        ret_code=0
        
        LBAFid = None
        # initial test item for metadata
        TestItems=[]      
        for x in range(15):
            RP = self.LBAF[x][self.lbafds.RP]
            LBADS = self.LBAF[x][self.lbafds.LBADS] 
            MS = self.LBAF[x][self.lbafds.MS] 
            if MS!=0 and LBADS>=9:                           
                TestItems.append([x, RP, LBADS, MS])      
                  
        self.Print ("Number of LBA formats (self.NLBAF): %s"%self.NLBAF)
        self.Print ("If LBA format support metadata, list the LBAFs")         
        if not TestItems:
            self.Print ("All the LBA format does't support metadata, quit this test case!")
            return 0     
        else:
            for Item in TestItems:
                self.Print("LBAF %s, RP: %s, LBADS: %s, MS: %s"%(Item[0], Item[1], Item[2], Item[3]))  
                if LBAFid==None:    # use first lbaf that is support metadata
                        LBAFid = Item[0]
        
        self.Print ("")
        self.Print ("Send format command with MSET = 0, LBAF: %s"%LBAFid)
        self.Print ("Check return code, expected returned status code: Success")
        mStr=self.Format(1, 0, 0, 0, 0, 0);
        ret_code = ret_code if self.CheckResult(mStr, self.Expected_Success) else 1
        self.Print ("")
        self.Print ("Send format command with MSET = 1, LBAF: %s"%LBAFid)
        self.Print ("Check return code, expected returned status code: Success")
        mStr=self.Format(1, 0, 0, 0, 0, 1);
        ret_code = ret_code if self.CheckResult(mStr, self.Expected_Success) else 1
        return ret_code

    SubCase8TimeOut = 600
    SubCase8Desc = "Test format Progress Indicator (FPI)"
    SubCase8KeyWord = "format Progress Indicator (FPI)"
    def SubCase8(self): 
        ret_code=0
        self.Print ("Check if the controller support the format Progress Indicator or not(format Progress Indicator (FPI) bit 7 )")
        FPI_bit7=self.IdNs.FPI.bit(7)
        if FPI_bit7=="1":
            self.Print( "Support", "p")
        else:    
            self.Print( "Not support", "w")
         
        
            
        if FPI_bit7=="1":
            self.Print ("")
            self.Print ("Test the percentage of the format command in format Progress Indicator is counting down or not")
            self.Print ("Sending format command.. "    )
            t = threading.Thread(target = self.FormatNSID_01)
            t.start()   
            
            status="waiting for start" 
            per=0
            per_old=0
            per_test_fail=0
            while True:
                per=self.GetFPIPercentage()
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
            self.Print ("Check the percentage is counting down or not, expected result: Counting down"             )
            if per_test_fail==0:
                self.Print("PASS", "p")
            else:
                self.Print("Fail", "f")
                ret_code = 1
        return ret_code

    SubCase9TimeOut = 600
    SubCase9Desc = "Test format command for all LBAF"
    SubCase9KeyWord = ""
    def SubCase9(self): 
        ret_code=0
        self.Print ("From self.LBAF0 to self.LBAF15, send format command and check if command success while self.LBAFx is valid ")
        self.Print ("and check if command fail while self.LBAFX is in valid ")
        
        for i in range(16):    
            self.Print ("")
            # is support if  LBADS >= 9
            IsValid = True if self.LBAF[i][self.lbafds.LBADS] >=9 else False
            if IsValid:
                self.Print ("self.LBAF%s is valid"%i)
            else:
                self.Print ("self.LBAF%s is not valid"%i  )
            
            self.Print ("send command for self.LBAF%s"%i)
            mStr=self.Format(1, i, 0);    
            self.Print ("Check return code, expected returned status code: %s"%("Success" if IsValid else "Invalid format"))
            if IsValid:
                ret_code = ret_code if self.CheckResult(mStr, self.Expected_Success) else 1
            else:
                ret_code = ret_code if self.CheckResult(mStr, self.Expected_Fail) else 1
                
        return ret_code

    SubCase10TimeOut = 600
    SubCase10Desc = "Check Command Specific Status Values"
    SubCase10KeyWord = "format NVM - Command Specific Status Values"
    def SubCase10(self): 
        ret_code=0
        '''
        self.Print ("if enabling protection information when there is no sufficient metadata per LBA, then return fail")
        self.Print ("Check return code, expected returned status code: Invalid format"    )
        
        if not self.Type1Supported:
            mStr=self.Format(1, 0, 0, 0, 1);
            ret_code = ret_code if self.CheckResult(mStr, self.Expected_InvalidFormat) else 1
        elif not self.Type2Supported:
            mStr=self.Format(1, 0, 0, 0, 2);
            ret_code = ret_code if self.CheckResult(mStr, self.Expected_InvalidFormat) else 1
        elif not self.Type3Supported:
            mStr=self.Format(1, 0, 0, 0, 3);
            ret_code = ret_code if self.CheckResult(mStr, self.Expected_InvalidFormat) else 1
        else:
            self.Print("All Protection Information type is support, quite this test item!", "w")
        '''
        self.Print ("")
        self.Print ("If the specified format is not available in the current configuration, then return fail")
        self.Print ("Check return code, expected returned status code: Invalid format")
        if self.LBAF15_LBADS < 9:
            mStr=self.Format(1, 15, 0);
            ret_code = ret_code if self.CheckResult(mStr, self.Expected_InvalidFormat) else 1
        else:
            self.Print("All lbaf is available, quite this test item!", "w")
        return ret_code

    SubCase11TimeOut = 600
    SubCase11Desc = "Test if DST operation was aborted due to format NVM command"
    SubCase11KeyWord = "Get Log Page - Self-test Result Data Structure"
    def SubCase11(self): 
        ret_code=0
        DST_Format_ID = [[1, 1], [0xFFFFFFFF, 0xFFFFFFFF],[1, 0xFFFFFFFF], [0xFFFFFFFF, 1]]
        self.Print ("Test if device self-test operation was aborted due to the processing of a format NVM command"    )
        if self.IdCtrl.OACS.bit(4)=="0":
            self.Print ("Controller does not support the DST operation, quit this test!")
        else:
            self.Flow.DST.EventTriggeredMessage="Send format command as DST percentage  >= 1% "
            self.Flow.DST.ShowProgress=True   
                
            for DST_Format in DST_Format_ID:      
                # mDstType = 1, Short device self-test operation
                # mDstType = 2, extended device self-test operation
                for mDstType in [0x1, 0x2]:
                    IdDST=DST_Format[0]
                    IdFormat=DST_Format[1]
                    self.Print ("")
                    self.Print ("Setting nsid = %s in the DST command"%hex(IdDST))
                    self.Print ("Setting nsid = %s in the format command"%hex(IdFormat))
                    self.Print ("Short device self-test operation" if mDstType==0x1 else "Extended device self-test operation")
                    # set DST command nsid
                    self.Flow.DST.SetNSID(IdDST)
                    # set Event
                    self.Flow.DST.SetEventTrigger(self.FormatNSID, IdFormat)                     
                    # set DST type
                    self.Flow.DST.SetDstType(mDstType)    
                    # set Threshold = 1 to raise event
                    self.Flow.DST.SetEventTriggerThreshold(1)
                    
                    # start DST flow and get device self test status 
                    DSTS=self.Flow.DST.Start()
                    if DSTS!=-1:        
                        # get bit 3:0        
                        DSTSbit3to0 = DSTS & 0b00001111
                        self.Print ("result of the device self-test operation from Get Log Page : %s" %hex(DSTSbit3to0))
                        self.Print ("Check the result of the device self-test operation , expected result:  0x4")
                        if DSTSbit3to0==4:
                            self.Print("PASS", "p")
                        else:
                            if IdDST==IdFormat:
                                self.Print("FAIL", "f")
                                ret_code = 1
                            else:
                                self.Print("FAIL", "w")
                                self.Print("Warnning! according to NVME Spec 1.3c, page 269, 8.11.1 and 8.11.2", "w")
                                self.Print("shall be aborted by a format NVM, if the Namespace Identifier field specified in the format NVM command is the same as- ", "w")
                                self.Print("the Device Self-test command that invoked the device self-test operation ", "w")
                                 
                    else:
                        self.Print ("Controller does not support the DST operation")
        return ret_code

    SubCase12TimeOut = 600
    SubCase12Desc = "Test format Scope and Secure Erase Scope"
    SubCase12KeyWord = "format NVM - format Scope, format NVM - Secure Erase Scope"
    def SubCase12(self): 
        ret_code=0
    
        # geneate vaild namespaces
        # check if controller supports the Namespace Management and Namespace Attachment commands or not
        NsSupported=True if self.IdCtrl.OACS.bit(3)=="1" else False
        if NsSupported:
            self.Print ("controller supports the Namespace Management and Namespace Attachment commands")
            print  "try to create namespace" 
            # function CreateMultiNs() will create namespace less then 8 NS
            MaxNs = self.CreateMultiNs()
            if MaxNs ==1:
                self.Print ("only namespace 1 has been created, quit this test")
                self.NsReady=False
            else:
                self.Print ("namespaces nsid from 1 to %s have been created"%MaxNs)
                self.StopNs=MaxNs                            
        
        if self.NsReady:
            print  ""
            print  "format NVM - format Scope"
            if self.FNAbit_0=="0":
                print  "  self.FNA bit0=0, test NSID=0xFFFFFFFF, All namespaces attached to the controller"
                ret_code=ret_code if self.Test_FFFFFFFF(0)==0 else 1
                print  "  self.FNA bit0=0, test NSID=All other valid values, Particular namespace specified"
                ret_code=ret_code if self.Test_AllOtherValidValues(0)==0 else 1
            else:
                print  "  self.FNA bit0=1, test NSID=All valid values, All namespaces in the NVM subsystem"
                ret_code=ret_code if self.Test_AllValidValues(0)==0 else 1
            
            self.Print ("")
            if self.SecureEraseSupported:      
                print  " format NVM - Secure Erase Scope"
                if self.FNAbit_1=="0":
                    print  " self.FNA bit1=0, test NSID=0xFFFFFFFF, All namespaces attached to the controller"
                    ret_code=ret_code if self.Test_FFFFFFFF(1)==0 else 1
                    print  "  self.FNA bit1=0, test NSID=All other valid values, Particular namespace specified"
                    ret_code=ret_code if self.Test_AllOtherValidValues(1)==0 else 1
                else:
                    print  "  self.FNA bit1=1, test NSID=All valid values, All namespaces in the NVM subsystem"
                    ret_code=ret_code if self.Test_AllValidValues(1)==0 else 1
            else:
                print  "Secure Erase not Supported, will not verify format NVM - Secure Erase Scope"     
        
        # reset name spaces to 1 ns only
        print  "Reset all namespaces to namespace 1 and kill other namespaces"
        self.ResetNameSpaces()       
        return ret_code

    SubCase13TimeOut = 600
    SubCase13Desc = "Check data After the format NVM command with SES=0x0"
    SubCase13KeyWord = "controller shall not return any user data that was previously contained in an affected namespace"
    def SubCase13(self): 
        ret_code=0
        self.Print ("Check data After the format NVM command successfully completes with SES=0x0 (No secure erase operation requested)")
        self.Print ("The controller shall not return any user data that was previously contained in an affected namespace")
        self.Print ("write data at block %s, %s and %s, size=1M, patten=%s"%(self.start_SB, self.middle_SB, self.last_SB, "0xab"))
        self.write_SML_data(0xab)
        self.Print ("send format command")
        mStr=self.Format(1, 0, 0)
        self.Print ("Check if data at block %s, %s and %s is 0x0 or not"%(self.start_SB, self.middle_SB, self.last_SB))
        if self.isequal_SML_data(0x0):
            self.Print("PASS", "p")
        else:
            self.Print("FAIL", "f")
            ret_code = 1
        return ret_code

    SubCase14TimeOut = 600
    SubCase14Desc = "Check data After the format NVM command with SES=0x1"
    SubCase14KeyWord = "User Data Erase"
    def SubCase14(self): 
        ret_code=0
        self.Print ("Check data After the format NVM command successfully completes with SES=0x1 (User Data Erase)")
        if not self.SecureEraseSupported:
            self.Print ("Secure Erase is not Supported, quite this test")
        else:
            self.Print ("write data at block %s, %s and %s, size=1M, patten=%s"%(self.start_SB, self.middle_SB, self.last_SB, "0xab"))
            self.write_SML_data(0xab)
            self.Print ("send format command with SES=0x1(User Data Erase)")
            self.Print( self.Format(1, 0, 1) )
            self.Print ("Check data at block %s, %s and %s, if data is 0x0 or 0xff, then pass the test"%(self.start_SB, self.middle_SB, self.last_SB))
            if self.isequal_SML_data(0x0):
                self.Print("PASS", "p")
            elif self.isequal_SML_data(0xff):
                self.Print("PASS", "p")        
            else:
                self.Print("FAIL", "f")
                ret_code = 1
        return ret_code

    SubCase15TimeOut = 600
    SubCase15Desc = "Check data After the format NVM command with SES=0x2"
    SubCase15KeyWord = "Cryptographic Erase"
    def SubCase15(self): 
        ret_code=0
        self.Print ("Check data After the format NVM command successfully completes with SES=0x2 (Cryptographic Erase )")
        self.Print ("This is accomplished by deleting the encryption key.")
        if not self.SecureEraseSupported:
            self.Print ("Secure Erase is not Supported, quite this test")
        else:
            self.Print ("write data at block %s, %s and %s, size=1M, patten=%s"%(self.start_SB, self.middle_SB, self.last_SB, "0xab"))
            self.write_SML_data(0xab)
            self.Print ("send format command with SES=0x2(Cryptographic Erase)")
            self.Print( self.Format(1, 0, 2) )
            self.Print ("Check data at block %s, %s and %s, size=1M, if data is 0xab, then fail the test"%(self.start_SB, self.middle_SB, self.last_SB))
            if self.isequal_SML_data(0xab):
                self.Print("FAIL, data is 0xab", "f")
                ret_code = 1
            else:
                self.Print("PASS", "p")  
        '''        
        if self.IsControllerName(self.CryptographicErasePass_0):     
            self.Print ("Controller is %s, so let this test pass"%self.CryptographicErasePass_0)
            ret_code=0
        if self.IsControllerName(self.CryptographicErasePass_1):     
            self.Print ("Controller is %s, so let this test pass"%self.CryptographicErasePass_1)
            ret_code=0
        if self.IsControllerName(self.CryptographicErasePass_2):     
            self.Print ("Controller is %s, so let this test pass"%self.CryptographicErasePass_2)
            ret_code=0   
        '''                     
            
        return ret_code

    SubCase16TimeOut = 600
    SubCase16Desc = "Check if SMART / Health Log is retained after format command"
    SubCase16KeyWord = "SMART / Health Information Log"
    def SubCase16(self): 
        ret_code=0
        self.Print ("Check if SMART / Health Log is retained after the format NVM command successfully completes")
        self.Print ("")
        
        StartTime = time.time()      
        self.Print ("Store SMART / Health Log ")
        OriginalValue=self.GetHealthLog()
        
        self.Print ("")
        self.Print ("Send format command with SES=000b (No secure erase operation requested)")
        mStr=self.Format(1, 0, 0);
        self.Print ("Check return code, expected returned status code: Success")
        CmdSuccess = self.CheckResult(mStr, self.Expected_Success)
        
        if not CmdSuccess:
            self.Print ("Becouse format command fail, quit this test item!")
        else:
            self.Print ("")
            self.Print ("Get current SMART / Health Log ")
            CurrentValue=self.GetHealthLog()
            
            CurrentTime = time.time()   
            timeUsage = int(CurrentTime-StartTime) +1
            
            self.Print ("")
            self.Print ("Time used for format command: %d s "%timeUsage)            
            self.Print ("")
            self.Print ("Check if SMART / Health Log is retained after the format command")
            self.Print ("Note: tempture and HCTM infomations maybe changed")
            self.Print (""        )
            ValueRetained=True
            self.Print ("============================================")
            for i in range(len(OriginalValue)):                
                original=OriginalValue[i][1] 
                current=CurrentValue[i][1]
                Name =  OriginalValue[i][0]
                # print field name
                
                self.Print(Name )
                mStr = "{:<25}".format("Original: %s"%original) + "Current: %s"%current
                # all the following have torlerance for time base values
                if Name == "CompositeTemperature" \
                    or Name == "WarningCompositeTemperatureTime" \
                    or Name == "CriticalCompositeTemperatureTime" \
                    or Name == "ThermalManagementTemperature1TransitionCount" \
                    or Name == "ThermalManagementTemperature2TransitionCount" \
                    or Name == "TotalTimeForThermalManagementTemperature1" \
                    or Name == "TotalTimeForThermalManagementTemperature2":
                    torlerance=timeUsage
                else:
                    torlerance=0

                # check value
                intOriginal = int(original)
                intCurrent = int(current)
                if (intOriginal <= intCurrent + torlerance) and (intOriginal >= intCurrent - torlerance) :                
                    self.Print(mStr, "p")
                else:
                    self.Print(mStr, "f")
                    ValueRetained=False
                self.Print ("---------------------")
                
            self.Print ("============================================")
            if ValueRetained:                
                self.Print("PASS", "p")
            else:
                self.Print("FAIL", "f")
                ret_code=1 
        return ret_code

    SubCase17TimeOut = 3600
    SubCase17Desc = "Spec1.4, Verify status code of Format in Progress"
    SubCase17KeyWord = "I/O commands for a namespace that has a Format NVM command in progress may be aborted and if aborted"\
    "\n the controller should return a status code of Format in Progress."
    def SubCase17(self): 
        ret_code = 0
        self.Print ("")
        loopTotal = 10
        self.Print ("Test loop total = %s"%loopTotal)
        CMDwrite = "dd if=/dev/zero bs=4096 count=1 2>&1 |nvme write %s --data-size=4096  2>&1"%self.dev
        self.Print ("Write command: %s"%CMDwrite)

        loop =0
        
        while True:
            loop +=1
            if loop>10:
                break

            self.Print ("")            
            self.Print ("Loop: %s"%loop, "b" )
            '''
            self.Print ("Do precondition") 
            CMDprecon = "fio --direct=1 --iodepth=16 --ioengine=libaio --bs=64k --rw=write --numjobs=1 "\
            "--filename=%s --name=mdata --runtime=5"%self.dev
            self.shell_cmd(CMDprecon)
            self.Print ("Done") 
            '''
            
            waitTimeInMs = randint(1, 0xFF) 
            waitTimeInS = float(waitTimeInMs)/1000
            self.Print ("Create thread to issue format command and wait %s ms(%s S), then send write command"%(waitTimeInMs, waitTimeInS))
            self.threadFlag=False # true while thread sending command, else false
            t = threading.Thread(target = self.ThreadFormatCmdForCase17)
            t.start()   

            while True:            
                if self.threadFlag:
                    sleep(waitTimeInS)
                    mStr, sc = self.shell_cmd_with_sc(CMDwrite)
                    self.Print("After sending write command, return status: %s"%mStr)
                    if sc==0:
                        self.Print("I/O commands was not aborted, Status code = 0")
                    elif sc==0x84:                        
                        self.Print("I/O commands was aborted, Status code == 0x84(Format in Progress)", "p")
                    else:
                        self.Print("I/O commands was aborted, Status code != 0x84, fail the test and quit", "f")
                        ret_code = 1
                        
                    self.Print("Wait for thread finish(timout 10s)")
                    t.join(timeout=10)
                    sleep(1)
                    
                    if ret_code!=0:
                        return 1
                    
                    self.Print("Loop ending")
                    break
                    

    # </sub item scripts>
    
    # override PostTest  
    def PostTest(self):  
        Now_FLBAS=self.IdNs.FLBAS.int
        if Now_FLBAS!=self.FLBAS:
            self.Print ("")
            self.Print (" == Post Test =====================================")
            self.Print ("FLBAS = %s, format to previous format(%s)"%(Now_FLBAS, self.FLBAS))
            lbaf=self.FLBAS&0xF
            mStr=self.Format(1, lbaf, 0);
            self.Print ("Check format command success or not, expected returned status code: Success")
            return self.CheckResult(mStr, self.Expected_Success)         
            
        return True    
    
    
if __name__ == "__main__":
    DUT = SMI_Format(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 
    
    
    
    
    
