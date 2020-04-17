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

# Import VCT modules
from lib_vct.NVME import NVME
from lib_vct.NVMECom import deadline
from __builtin__ import True

class SMI_Compare(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_Compare.py"
    Author = "Sam Chan"
    Version = "20200417"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
  
    
    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def CMDisSuccess(self, SC):
        # if command return cstatus code = 0(success) or 0x85(compare fail)
        cmdsuc=True if (SC==0x85 or SC==0x0) else False
        return cmdsuc
    
    def getDW10_DW11(self, slba):
        dw10=slba&0xFFFFFFFF
        dw11=slba>>32
        return dw10, dw11
    
    
    def testDW10_DW11(self, SLBA, msg0, msg1 , ExpectCommandSuccess):  
        self.Print ("")
        self.Print( msg0 )
        self.Print( msg1  )
        
        cdw10, cdw11=self.getDW10_DW11(SLBA)
        mStr, SC=self.shell_cmd_with_sc("dd if=/dev/zero bs=512 count=1 2>&1 |tr \\\\000 \\\\132 |nvme io-passthru %s -o 0x5 -n 1 -l 512 -w --cdw10=%s --cdw11=%s 2>&1 "%(self.dev, cdw10, cdw11))
        retCommandSueess=self.CMDisSuccess(SC)
        if (retCommandSueess ==  ExpectCommandSuccess) :
            self.Print("PASS", "p")  
            return True         
        else:
            self.Print("Fail", "f")
            self.Print("Command return status: %s"%mStr, "f")
            return False   
        
    def testDW12(self, LR, FUA, PRINFO, NLB, ExpectCommandSuccess):      
        #start from block 0
        cdw10, cdw11=self.getDW10_DW11(0)
        cdw12=(LR<<31) + (FUA<<30)+ (PRINFO<<26) + NLB
        mStr, SC=self.shell_cmd_with_sc("dd if=/dev/zero bs=512 count=1 2>&1   |tr \\\\000 \\\\132 |nvme io-passthru %s -o 0x5 -n 1 -l 512 -w --cdw10=%s --cdw11=%s --cdw12=%s 2>&1"%(self.dev, cdw10, cdw11, cdw12))
        retCommandSueess=self.CMDisSuccess(SC)
        if (retCommandSueess ==  ExpectCommandSuccess) :        
            return True         
        else:
            self.Print("Fail", "f")
            self.Print("LR=%s, FUA=%s, PRINFO=%s, NLB=%s"%(LR, FUA, PRINFO, NLB), "f")
            self.Print("Command return status: %s"%mStr, "f")
            DW12Fail=1
            return False       
    
    def testDW12NLB(self, msg0, msg1 ,NLB, ExpectCommandSuccess):      
        self.Print ("")
        self.Print( msg0 )
        self.Print( msg1  ) 
        cdw12=NLB        
        mStr, SC=self.shell_cmd_with_sc("nvme io-passthru %s -o 0x5 -n 1 -l %s -w --cdw10=%s --cdw11=%s --cdw12=%s -i temp.bin 2>&1"\
                            %(self.dev, 512*(NLB+1), 0, 0, cdw12))
        retCommandSueess=self.CMDisSuccess(SC)
        if (retCommandSueess ==  ExpectCommandSuccess) :
            self.Print("PASS", "p")  
            return True         
        else:
            self.Print("Fail", "f")
            self.Print("Command return status: %s"%mStr, "f")
            return False 
        
    def testDW13(self, DSM, ExpectCommandSuccess):      
        mStr, SC=self.shell_cmd_with_sc("dd if=/dev/zero bs=512 count=1 2>&1   |tr \\\\000 \\\\132 |nvme io-passthru %s -o 0x5 -n 1 -l 512 -w --cdw13=%s 2>&1"%(self.dev, DSM))
        retCommandSueess=self.CMDisSuccess(SC)
        if (retCommandSueess ==  ExpectCommandSuccess) :
            return True         
        else:
            self.Print("Fail when DSM=%s"%DSM, "f")
            self.Print("Command return status: %s"%mStr, "f")
            DW13Fail=1
            return False       
    
    def testDW14(self, EILBRT, ExpectCommandSuccess):      
        mStr, SC=self.shell_cmd_with_sc("dd if=/dev/zero bs=512 count=1 2>&1   |tr \\\\000 \\\\132 |nvme io-passthru %s -o 0x5 -n 1 -l 512 -w --cdw14=%s 2>&1"%(self.dev, EILBRT))
        retCommandSueess=self.CMDisSuccess(SC)
        if (retCommandSueess ==  ExpectCommandSuccess) :
            return True         
        else:
            self.Print("Fail when EILBRT=%s"%EILBRT, "f")
            self.Print("Command return status: %s"%mStr, "f")
            DW14Fail=1
            return False    
        
    def testDW15(self, ELBATM,ELBAT, ExpectCommandSuccess):      
        CDW15=(ELBATM<<16)+ELBAT
        mStr, SC=self.shell_cmd_with_sc("dd if=/dev/zero bs=512 count=1 2>&1   |tr \\\\000 \\\\132 |nvme io-passthru %s -o 0x5 -n 1 -l 512 -w --cdw15=%s 2>&1"%(self.dev, CDW15))
        retCommandSueess=self.CMDisSuccess(SC)
        if (retCommandSueess ==  ExpectCommandSuccess) :
            return True         
        else:
            self.Print("Fail when cdw15=%s"%CDW15, "f")
            self.Print("Command return status: %s"%mStr, "f")
            DW15Fail=1
            return False                
    
    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def __init__(self, argv):
        # initial parent class
        super(SMI_Compare, self).__init__(argv)
        
        # add all sub items to test script list
        #self.AddScript(self.Script0)
        #self.AddScript(self.Script1)
    
    
    
    # override
    def PreTest(self):
        self.Print ("Check if the controller supports the Compare command or not in identify - ONCS")   
        self.CMDSupported=self.IdCtrl.ONCS.bit(0)    
        self.CMDSupported=True if self.CMDSupported=="1" else False
        self.Print ("Compare command supported") if self.CMDSupported else self.Print ("Compare command not supported")
        
        if self.CMDSupported:
            self.Print ("Write 0x5A to first 10M data")
            self.fio_write(offset = 0, size = "10M", pattern = 0x5A)
            if self.fio_isequal(offset = 0, size = "10M", pattern = 0x5A):
                self.Print ("Done", "p")
                
                ncap=self.IdNs.NCAP.int
                self.Print ("NCAP: %s"%ncap)
                self.Print ("Write 0x5A to last block: %s"%(ncap-1))
                self.nvme_write_1_block(value = 0x5A, block = ncap-1)
                
                # create compare file(temp.bin), size = MDTSinBlock +1(ex, MDTSinBlock=512, create 513block) , data = 0x5A
                NLB = self.MDTSinBlock
                CMD = "dd if=/dev/zero bs=512 count=%s 2>&1 |tr \\\\000 \\\\132 > temp.bin"%(NLB+1)
                mStr, SC=self.shell_cmd_with_sc(CMD)
                if SC!=0:
                    self.Print ("Create compare file(temp.bin) fail")
                    return False
            else:
                self.Print ("Verify data fail, quit", "f")
                return False
        
        self.Print ("")
        return True if self.CMDSupported else False
    
    # <sub item scripts>
    SubCase1TimeOut = 60
    SubCase1Desc = "Test Command Dword 10 and Command Dword 11 for Starting LBA (SLBA)"        
    def SubCase1(self):
        ret_code=0
        MC=self.IdNs.MC.int
        self.Print ("Metadata Capabilities (MC): %s"%MC)
        
        NSZE=self.IdNs.NSZE.int
        self.Print ("NSZE: %s"%NSZE)
        
        #--------------------------------------------------
        SLBA=0
        msg0="compare first block, SLBA=%s"%(SLBA)
        msg1="check if compare command success(expected result: command success)"
        ret_code=ret_code if self.testDW10_DW11(SLBA, msg0, msg1, True) else 1
           
        #--------------------------------------------------
        SLBA=NSZE-1
        msg0="compare last block, SLBA=%s"%(SLBA)
        msg1="check if compare command success(expected result: command success)"
        ret_code=ret_code if self.testDW10_DW11(SLBA, msg0, msg1, True) else 1
           
        #--------------------------------------------------
        SLBA=NSZE
        msg0="compare block exceed the current number of logical blocks allocated in the namespace, SLBA=%s"%(SLBA)
        msg1="check if compare command success(expected result: command fail)"
        ret_code=ret_code if self.testDW10_DW11(SLBA, msg0, msg1, False) else 1

        return ret_code
    
    SubCase2TimeOut = 60
    SubCase2Desc = "Test Command Dword 12 for LR, FUA, PRINFO"
    def SubCase2(self):          
        ret_code=0
        
        DPC = self.IdNs.DPC.int
        DataProtectionsupported= True if (DPC>0) else False
        self.Print ("End-to-end Data Protection Capabilities (DPC): 0x%X"%DPC)
        self.Print ("End-to-end Data Protection supported") if DataProtectionsupported else self.Print ("End-to-end Data Protection not supported")         
        
        if (DataProtectionsupported):
            self.Print ("set  cdw[31:26] from 0x0 to 0x3F and check if compare command success(expected result: command success) ")            
            for i in range(0x40):              
                bit26to31=i
                PRINFO=bit26to31 & 0xF
                FUA=(bit26to31 & 0x10) >> 4
                LR=(bit26to31 & 0x20) >> 5
                NLB=0    
                ret_code=ret_code if self.testDW12(LR, FUA, PRINFO, NLB, True) else 1
        else:
            self.Print ("set  cdw[31:30] from 0x0 to 0x3 and check if compare command success(expected result: command success) ")
            for i in range(0x4):          
                bit26to31=i
                PRINFO=0
                FUA=(bit26to31 & 0x1)
                LR=(bit26to31 & 0x2) >> 1
                NLB=0    
                ret_code=ret_code if self.testDW12(LR, FUA, PRINFO, NLB, True) else 1     
            
        if ret_code==0:
            self.Print("PASS", "p") 
        else:
            self.Print("Fail", "f")   
        
        return ret_code

    SubCase3TimeOut = 60
    SubCase3Desc = "Test Command Dword 12 for NLB"
    def SubCase3(self):
          
        ret_code=0
        
        NLB=0
        msg0="set NLB=%s"%(NLB)
        msg1="check if compare command success(expected result: command success)"
        ret_code=ret_code if self.testDW12NLB(msg0, msg1, NLB, True) else 1
        
        NLB=self.MDTSinBlock-1
        msg0="set NLB=%s Maximum Data Transfer Size in blocks (MDTS)"%(NLB)
        msg1="check if compare command success(expected result: command success)"
        ret_code=ret_code if self.testDW12NLB(msg0, msg1, NLB, True) else 1
        
        NLB=self.MDTSinBlock
        msg0="set NLB=%s to exceed the maximum transfer size"%(NLB)
        msg1="check if compare command success(expected result: command fail)"
        ret_code=ret_code if self.testDW12NLB(msg0, msg1, NLB, False) else 1
        
        return ret_code

    SubCase4TimeOut = 60
    SubCase4Desc = "Test Command Dword 14"
    def SubCase4(self):
          
        ret_code=0
        self.Print ("set Command Dword 14 from 0x0 to 0xFF and check if compare command success(expected result: command success) ")
        
        for i in range(0x100):
            EILBRT= (i<<24) +(i<<16) +(i<<8) + i
            ret_code=ret_code if self.testDW14(EILBRT, True) else 1
        
        if ret_code==0:
            self.Print("PASS", "p") 
        else:
            self.Print("Fail", "f")
        return ret_code

    SubCase5TimeOut = 60
    SubCase5Desc = "Test Command Dword 15"
    def SubCase5(self):
          
        ret_code=0
        self.Print ("set Command Dword 15 from 0x0 to 0xFF and check if compare command success(expected result: command success) ")
        
        for i in range(0x100):
            ELBATM= (i<<8) + i
            ELBAT= (i<<8) + i
            ret_code=ret_code if self.testDW15(ELBATM,ELBAT, True) else 1
        
        if ret_code==0:
            self.Print("PASS", "p") 
        else:
            self.Print("Fail", "f")
        
        return ret_code




        
    # </sub item scripts>
    
    
    
    
if __name__ == "__main__":
    DUT = SMI_Compare(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 
    
    
    
    
    
