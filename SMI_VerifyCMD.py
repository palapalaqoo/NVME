#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
# Import VCT modules
from lib_vct.NVME import NVME

class SMI_VerifyCMD(NVME):
    ScriptName = "SMI_VerifyCMD.py"
    Author = "Sam"
    Version = "20210313"

    def getDW10_DW11(self, slba):
        dw10=slba&0xFFFFFFFF
        dw11=slba>>32
        return dw10, dw11

    def testDW10_DW11(self, SLBA, ExpectCommandSuccess):          
        cdw10, cdw11=self.getDW10_DW11(SLBA)
        cdw12=0
        cdw14=0
        cdw15=0
        CMD="nvme io-passthru %s -o 0xC -n 1 -r --cdw10=%s --cdw11=%s --cdw12=%s --cdw14=%s --cdw15=%s 2>&1"\
                            %(self.dev, cdw10, cdw11, cdw12, cdw14, cdw15)          
        self.Print("Issue verify CMD with SLBA = 0x%X"%SLBA)   
        self.Print("CMD: %s"%CMD)  
        mStr, sc = self.shell_cmd_with_sc(CMD)
        self.Print("Returned command status: %s"%mStr)
        if ExpectCommandSuccess:
            self.Print("Check if status code=0, expect command success")
            if sc==0:
                self.Print("Pass", "p")
                return True
            else:
                self.Print("Fail", "f")
                return False
        else:
            self.Print("Check if status code!=0, expect command fail")
            if sc!=0:
                self.Print("Pass", "p")
                return True
            else:
                self.Print("Fail", "f")
                return False            

    def testDW(self, LR, FUA, PRINFO, NLB, SLBA, cdw14, cdw15, ExpectCommandSuccess):      
        cdw10, cdw11=self.getDW10_DW11(SLBA)
        cdw12=(LR<<31) + (FUA<<30)+ (PRINFO<<26) + NLB

        CMD="nvme io-passthru %s -o 0xC -n 1 -r --cdw10=%s --cdw11=%s --cdw12=%s --cdw14=%s --cdw15=%s 2>&1"\
                            %(self.dev, cdw10, cdw11, cdw12, cdw14, cdw15)            
        mStr, sc = self.shell_cmd_with_sc(CMD)
        if (ExpectCommandSuccess and sc==0) or (not ExpectCommandSuccess and sc!=0):
            return True
        else :
            self.Print("Fail", "f")
            self.Print("LR=%s, FUA=%s, PRINFO=%s, NLB=0x%X, SLBA=0x%X, CDW14=0x%X, CDW15=0x%X"\
                       %(LR, FUA, PRINFO, NLB, SLBA,cdw14, cdw15), "f")
            self.Print("Command return status: %s"%mStr, "f")            
            return False      
        
        
    
    def __init__(self, argv):
        # initial parent class
        super(SMI_VerifyCMD, self).__init__(argv)
        self.OneBlockSize = self.GetBlockSize()
        self.Print("Current block size: %s"%self.OneBlockSize)

    # define pretest, if not return 0 , skip all subcases
    def PreTest(self):         
        CmdSupported=True if self.IdCtrl.ONCS.bit(7) =="1" else False 
        self.Print("Check bit 7 of ONCS")
        self.Print ("Verify command supported", "p") if CmdSupported else self.Print ("Verify command not supported", "f")
        # TODO
        #return 0
        if CmdSupported:
            return 0
        else:
            return 255

    # <define sub item scripts>
    SubCase1TimeOut = 60
    SubCase1Desc = "Test data_units_read in the SMART/Health Information"   
    SubCase1KeyWord = ""
    def SubCase1(self):
        ret_code=0
        
        data_units_read0=self.GetLog.SMART.DataUnitsRead
        self.Print("Current data_units_read in the SMART/Health Information: %s"%data_units_read0)  
        self.Print("")      
        
        
        
        cdw10=0
        cdw11=0
        cdw12=((1000*512)/self.OneBlockSize) -1
        cdw14=0
        cdw15=0
        CMD="nvme io-passthru %s -o 0xC -n 1 -r --cdw10=%s --cdw11=%s --cdw12=%s --cdw14=%s --cdw15=%s 2>&1"\
                            %(self.dev, cdw10, cdw11, cdw12, cdw14, cdw15)   
        self.Print("Issue CMD to verify first 1000*512 bytes")   
        self.Print("CMD: %s"%CMD)  
        mStr, sc = self.shell_cmd_with_sc(CMD)
        self.Print("Returned command status : %s"%mStr)
        self.Print("Check if status code=0, expect command success")
        if sc==0:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            ret_code = 1        
        
        self.Print("")
        data_units_read1=self.GetLog.SMART.DataUnitsRead
        self.Print("Current data_units_read in the SMART/Health Information: %s"%data_units_read1)  
        self.Print("Check data_units_read, expect data_units_read+1 after verify command")
        if data_units_read1==data_units_read0+1:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            ret_code = 1           
        
        
        return ret_code

    SubCase2TimeOut = 60
    SubCase2Desc = "Test Command Dword 10 and Command Dword 11(SLBA)"   
    SubCase2KeyWord = ""
    def SubCase2(self):
        ret_code=0
        NSZE=self.IdNs.NSZE.int
        self.Print ("NSZE: 0x%X"%NSZE, "b")
        self.Print("")      
        #--------------------------------------------------
        SLBA=0
        self.Print("Verify CMD with vaild SLBA(0x%X)"%SLBA, "b")
        ret_code=ret_code if self.testDW10_DW11(SLBA, True) else 1
        self.Print("")
        #--------------------------------------------------
        SLBA=NSZE-1
        self.Print("Verify CMD with vaild SLBA(0x%X)"%SLBA, "b")
        ret_code=ret_code if self.testDW10_DW11(SLBA, True) else 1
        self.Print("")   
        #--------------------------------------------------
        SLBA=NSZE
        self.Print("Verify CMD with invaild SLBA(0x%X)"%SLBA, "b")
        ret_code=ret_code if self.testDW10_DW11(SLBA, False) else 1
            
        
        return ret_code

    SubCase3TimeOut = 60
    SubCase3Desc = "Test Command Dword 12 for LR, FUA, PRINFO"       
    def SubCase3(self):
        ret_code=0
        
        DPC = self.IdNs.DPC.int
        DataProtectionsupported= True if (DPC>0) else False
        self.Print ("End-to-end Data Protection Capabilities (DPC): 0x%X"%DPC)
        self.Print ("End-to-end Data Protection supported") if DataProtectionsupported else self.Print ("End-to-end Data Protection not supported")         
        
        if (DataProtectionsupported):
            self.Print ("set  cdw[31:26] from 0x0 to 0x3F and check if verify command success(expected result: command success) ")            
            for i in range(0x40):  
            
                bit26to31=i
                PRINFO=bit26to31 & 0xF
                FUA=(bit26to31 & 0x10) >> 4
                LR=(bit26to31 & 0x20) >> 5
                NLB=0    
                SLBA=0
                ret_code=ret_code if self.testDW(LR, FUA, PRINFO, NLB, SLBA, 0, 0, True) else 1
        else:
            self.Print ("set  cdw[31:30] from 0x0 to 0x3 and check if verify command success(expected result: command success) ")
            for i in range(0x4):          
                bit26to31=i
                PRINFO=0
                FUA=(bit26to31 & 0x1)
                LR=(bit26to31 & 0x2) >> 1
                NLB=0    
                SLBA=0
                ret_code=ret_code if self.testDW(LR, FUA, PRINFO, NLB, SLBA, 0, 0, True) else 1     
                            
        if ret_code==0:
            self.Print("PASS", "p") 
        else:
            self.Print("Fail", "f")           

        return ret_code

    SubCase4TimeOut = 600
    SubCase4Desc = "Test Command Dword 12 for NLB"       
    def SubCase4(self):
        ret_code=0
        NSZE=self.IdNs.NSZE.int
        self.Print ("NSZE: 0x%X"%NSZE, "b")
        self.Print("")         
        
        LR=0; FUA=0; PRINFO = 0
        
        SLBA = NSZE-1
        NLB=0
        self.Print("Verify CMD with SLBA=0x%X(NSZE-1) and vaild NLB(0x%X)"%(SLBA, NLB), "b")
        ret_code=ret_code if self.testDW(LR, FUA, PRINFO, NLB, SLBA, 0, 0, True) else 1
        self.Print("")
        
        SLBA = NSZE-1
        NLB=1
        self.Print("Verify CMD with SLBA=0x%X(NSZE-1) and invaild NLB(0x%X)"%(SLBA, NLB), "b")
        ret_code=ret_code if self.testDW(LR, FUA, PRINFO, NLB, SLBA, 0, 0, True) else 1
        self.Print("")
        
        SLBA=0
        validList = range(0, 0xFFFF, 0x100) 
        self.Print("Verify CMD with SLBA=0 and NLB = below lists, and expected command success", "b")
        self.PrintList(validList)
        self.Print("") 
        for NLB in validList:
            ret_code=ret_code if self.testDW(LR, FUA, PRINFO, NLB, SLBA, 0, 0, True) else 1          

        
        return ret_code

    SubCase5TimeOut = 600
    SubCase5Desc = "Test Command Dword 14"       
    def SubCase5(self):
        
        self.Print ("set Command Dword 14(EILBRT) from 0x0 to 0xFF and check if write command success(expected result: command success) ")
        ret_code=0
        LR=0; FUA=0; PRINFO = 0; NLB = 0; SLBA = 0
        for i in range(0x100):
            EILBRT= (i<<24) +(i<<16) +(i<<8) + i
            ret_code=ret_code if self.testDW(LR, FUA, PRINFO, NLB, SLBA, EILBRT, 0, True) else 1
        
        if ret_code==0:
            self.Print("PASS", "p") 
        else:
            self.Print("Fail", "f")
        return ret_code

    # <sub item scripts>
    SubCase6TimeOut = 600
    SubCase6Desc = "Test Command Dword 15"       
    def SubCase6(self):
        self.Print ("set Command Dword 15 from 0x0 to 0xFF and check if write command success(expected result: command success) ")
        ret_code=0
        LR=0; FUA=0; PRINFO=0; NLB=0; SLBA=0; EILBRT=0
        for i in range(0x100):
            LBATM= (i<<8) + i
            LBAT= (i<<8) + i
            CDW15=(LBATM<<16)+LBAT
            ret_code=ret_code if self.testDW(LR, FUA, PRINFO, NLB, SLBA, EILBRT, CDW15, True) else 1
        
        if ret_code==0:
            self.Print("PASS", "p") 
        else:
            self.Print("Fail", "f")
        return ret_code




    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_VerifyCMD(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    