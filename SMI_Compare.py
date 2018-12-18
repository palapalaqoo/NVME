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

class SMI_Compare(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_Compare.py"
    Author = "Sam Chan"
    Version = "20181211"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
  
    
    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def CMDisSuccess(self, mstr):
        cmdsuc0=bool(re.search("NVMe command result:00000000", mstr))
        cmdsuc1=bool(re.search("NVMe Status:COMPARE_FAILED", mstr)) 
        return cmdsuc0 or cmdsuc1
    
    def getDW10_DW11(self, slba):
        dw10=slba&0xFFFFFFFF
        dw11=slba>>32
        return dw10, dw11
    
    
    def testDW10_DW11(self, SLBA, msg0, msg1 , ExpectCommandSuccess):  
        print ""
        print msg0
        print msg1   
        
        cdw10, cdw11=self.getDW10_DW11(SLBA)
        mStr=self.shell_cmd("dd if=/dev/zero bs=512 count=1 2>&1 |tr \\\\000 \\\\132 |nvme io-passthru %s -o 0x5 -n 1 -l 512 -w --cdw10=%s --cdw11=%s 2>&1 "%(self.dev, cdw10, cdw11))
        retCommandSueess=self.CMDisSuccess(mStr)
        if (retCommandSueess ==  ExpectCommandSuccess) :
            self.Print("PASS", "p")  
            return True         
        else:
            self.Print("Fail", "f")
            return False   
        
    def testDW12(self, LR, FUA, PRINFO, NLB, ExpectCommandSuccess):      
        #start from block 0
        cdw10, cdw11=self.getDW10_DW11(0)
        cdw12=(LR<<31) + (FUA<<30)+ (PRINFO<<26) + NLB
        mStr=self.shell_cmd("dd if=/dev/zero bs=512 count=1 2>&1   |tr \\\\000 \\\\132 |nvme io-passthru %s -o 0x5 -n 1 -l 512 -w --cdw10=%s --cdw11=%s --cdw12=%s 2>&1"%(self.dev, cdw10, cdw11, cdw12))
        retCommandSueess=self.CMDisSuccess(mStr)
        if (retCommandSueess ==  ExpectCommandSuccess) :        
            return True         
        else:
            self.Print("Fail", "f")
            self.Print("LR=%s, FUA=%s, PRINFO=%s, NLB=%s"%(LR, FUA, PRINFO, NLB), "f")
            DW12Fail=1
            return False       
    
    def testDW12NLB(self, msg0, msg1 ,NLB, ExpectCommandSuccess):      
        print ""
        print msg0
        print msg1   
        cdw12=NLB
        mStr=self.shell_cmd("dd if=/dev/zero bs=512 count=1 2>&1   |tr \\\\000 \\\\132 |nvme io-passthru %s -o 0x5 -n 1 -l 512 -w --cdw10=%s --cdw11=%s --cdw12=%s 2>&1"%(self.dev, 0, 0, cdw12))
        retCommandSueess=self.CMDisSuccess(mStr)
        if (retCommandSueess ==  ExpectCommandSuccess) :
            self.Print("PASS", "p")  
            return True         
        else:
            self.Print("Fail", "f")
            return False 
        
    def testDW13(self, DSM, ExpectCommandSuccess):      
        mStr=self.shell_cmd("dd if=/dev/zero bs=512 count=1 2>&1   |tr \\\\000 \\\\132 |nvme io-passthru %s -o 0x5 -n 1 -l 512 -w --cdw13=%s 2>&1"%(self.dev, DSM))
        retCommandSueess=self.CMDisSuccess(mStr)
        if (retCommandSueess ==  ExpectCommandSuccess) :
            return True         
        else:
            self.Print("Fail when DSM=%s"%DSM, "f")
            DW13Fail=1
            return False       
    
    def testDW14(self, EILBRT, ExpectCommandSuccess):      
        mStr=self.shell_cmd("dd if=/dev/zero bs=512 count=1 2>&1   |tr \\\\000 \\\\132 |nvme io-passthru %s -o 0x5 -n 1 -l 512 -w --cdw14=%s 2>&1"%(self.dev, EILBRT))
        retCommandSueess=self.CMDisSuccess(mStr)
        if (retCommandSueess ==  ExpectCommandSuccess) :
            return True         
        else:
            self.Print("Fail when EILBRT=%s"%EILBRT, "f")
            DW14Fail=1
            return False    
        
    def testDW15(self, ELBATM,ELBAT, ExpectCommandSuccess):      
        CDW15=(ELBATM<<16)+ELBAT
        mStr=self.shell_cmd("dd if=/dev/zero bs=512 count=1 2>&1   |tr \\\\000 \\\\132 |nvme io-passthru %s -o 0x5 -n 1 -l 512 -w --cdw15=%s 2>&1"%(self.dev, CDW15))
        retCommandSueess=self.CMDisSuccess(mStr)
        if (retCommandSueess ==  ExpectCommandSuccess) :
            return True         
        else:
            self.Print("Fail when cdw15=%s"%CDW15, "f")
            DW15Fail=1
            return False                
    
    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def __init__(self, argv):
        # initial parent class
        super(SMI_Compare, self).__init__(argv)
        
        # add all sub items to test script list
        #self.AddScript(self.Script0)
        #self.AddScript(self.Script1)
        
    # <sub item scripts>
    SubCase1TimeOut = 3
    SubCase1Desc = "Test Command Dword 10 and Command Dword 11 for Starting LBA (SLBA)"        
    def SubCase1(self):
        ret_code=0
        MC=self.IdNs.MC.int
        print "Metadata Capabilities (MC): %s"%MC
        
        NSZE=self.IdNs.NSZE.int
        print "NSZE: %s"%NSZE
        
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
        print "set  cdw[31:26] from 0x0 to 0x3F and check if compare command success(expected result: command success) "
        
        for i in range(0x40):  
        
            bit26to31=i
            PRINFO=bit26to31 & 0xF
            FUA=(bit26to31 & 0x10) >> 4
            LR=(bit26to31 & 0x20) >> 5
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
        print "set Command Dword 14 from 0x0 to 0xFF and check if compare command success(expected result: command success) "
        
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
        print "set Command Dword 15 from 0x0 to 0xFF and check if compare command success(expected result: command success) "
        
        for i in range(0x100):
            ELBATM= (i<<8) + i
            ELBAT= (i<<8) + i
            ret_code=ret_code if self.testDW15(ELBATM,ELBAT, True) else 1
        
        if ret_code==0:
            self.Print("PASS", "p") 
        else:
            self.Print("Fail", "f")
        
        return ret_code

    SubCase2TimeOut = 60
    SubCase2Desc = ""


        
    # </sub item scripts>
    
    
    
    
if __name__ == "__main__":
    DUT = SMI_Compare(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 
    
    
    
    
    
