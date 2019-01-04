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

class SMI_Read(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_Read.py"
    Author = "Sam Chan"
    Version = "20181211"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    SubCase1TimeOut = 60
    SubCase1Desc = "Test Metadata Pointer (MPTR)"    
    
    SubCase2TimeOut = 60
    SubCase2Desc = "Test Command Dword 10 and 11, Starting LBA(SLBA)"

    SubCase3TimeOut = 60
    SubCase3Desc = "Test Command Dword 12 for LR, FUA, PRINFO"    

    SubCase4TimeOut = 60
    SubCase4Desc = "Test Command Dword 12 for NLB"    

    SubCase5TimeOut = 120
    SubCase5Desc = "Test Command Dword 13"   
    
    SubCase6TimeOut = 120
    SubCase6Desc = "Test Command Dword 14"   
    
    SubCase7TimeOut = 120
    SubCase7Desc = "Test Command Dword 15"            

    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def getDW10_DW11(self,slba):
        dw10=slba&0xFFFFFFFF
        dw11=slba>>32
        return dw10, dw11
    
    def testMPTR(self,MetadataLen):
    #MetadataLen = Metadata Length
    
        mStr=self.shell_cmd("nvme read %s -s 0 -z 512 -y %s 2>&1"%(self.dev,MetadataLen))
        retCommandSueess=bool(re.search("read: Success", mStr))
        if (retCommandSueess ==  True) :
            return True         
        else:
            self.Print("Fail at MetadataLen= %s"%MetadataLen, "f")
            return False       
    
    
    def testDW10_DW11(self, SLBA, msg0, msg1 , ExpectCommandSuccess):  
        self.Print ("")
        print msg0
        print msg1   
        
        cdw10, cdw11=self.getDW10_DW11(SLBA)
        mStr=self.shell_cmd("nvme io-passthru %s -o 0x2 -n 1 -l 16 -r --cdw10=%s --cdw11=%s 2>&1"%(self.dev, cdw10, cdw11))
        retCommandSueess=bool(re.search("NVMe command result:00000000", mStr))
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
        mStr=self.shell_cmd("nvme io-passthru %s -o 0x2 -n 1 -l 16 -r --cdw10=%s --cdw11=%s --cdw12=%s 2>&1"%(self.dev, cdw10, cdw11, cdw12))
        retCommandSueess=bool(re.search("NVMe command result:00000000", mStr))
        if (retCommandSueess ==  ExpectCommandSuccess) :        
            return True         
        else:
            self.Print("Fail", "f")
            self.Print("LR=%s, FUA=%s, PRINFO=%s, NLB=%s"%(LR, FUA, PRINFO, NLB), "f")
            return False       
    
    def testDW12NLB(self, msg0, msg1 ,NLB, ExpectCommandSuccess):      
        self.Print ("")
        print msg0
        print msg1   
    
        mStr=self.shell_cmd("nvme read %s -s 0 -z 512 -c %s 2>&1"%(self.dev, NLB))
        retCommandSueess=bool(re.search("read: Success", mStr))
        if (retCommandSueess ==  ExpectCommandSuccess) :
            self.Print("PASS", "p")  
            return True         
        else:
            self.Print("Fail", "f")
            return False 
        
    def testDW13(self, DSM, ExpectCommandSuccess):      
        mStr=self.shell_cmd("nvme io-passthru %s -o 0x2 -n 1 -l 16 -r --cdw13=%s 2>&1"%(self.dev, DSM))
        retCommandSueess=bool(re.search("NVMe command result:00000000", mStr))
        if (retCommandSueess ==  ExpectCommandSuccess) :
            return True         
        else:
            self.Print("Fail when DSM=%s"%DSM, "f")
            return False       
    
    def testDW14(self, EILBRT, ExpectCommandSuccess):      
        mStr=self.shell_cmd("nvme io-passthru %s -o 0x2 -n 1 -l 16 -r --cdw14=%s 2>&1"%(self.dev, EILBRT))
        retCommandSueess=bool(re.search("NVMe command result:00000000", mStr))
        if (retCommandSueess ==  ExpectCommandSuccess) :
            return True         
        else:
            self.Print("Fail when EILBRT=%s"%EILBRT, "f")
            return False    
        
    def testDW15(self, ELBATM,ELBAT, ExpectCommandSuccess):      
        CDW15=(ELBATM<<16)+ELBAT
        mStr=self.shell_cmd("nvme io-passthru %s -o 0x2 -n 1 -l 16 -r --cdw15=%s 2>&1"%(self.dev, CDW15))
        retCommandSueess=bool(re.search("NVMe command result:00000000", mStr))
        if (retCommandSueess ==  ExpectCommandSuccess) :
            return True         
        else:
            self.Print("Fail when cdw15=%s"%CDW15, "f")
            return False              
    
    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def __init__(self, argv):
        # initial parent class
        super(SMI_Read, self).__init__(argv)
        
        
        
    # <sub item scripts>
    def SubCase1(self):
        self.Print ("-------- Test Metadata Pointer (MPTR)")
        ret_code=0
        for i in range(16):  
        
            ML=i
            #msg0="set Metadata Length=%s for read command"%(ML)
            #msg1="check if read command success(expected result: command success)"    
            if self.testMPTR(ML) == False:
                ret_code=1
            
        if ret_code==0:
            self.Print("PASS", "p") 
        else:
            self.Print("Fail", "f")   
        
        return ret_code           
    
    def SubCase2(self):
        self.Print ("-------- Test Command Dword 10 and Command Dword 11 for Starting LBA (SLBA)")
        ret_code=0   

        MC=self.IdNs.MC.int
        self.Print ("Metadata Capabilities (MC): %s"%MC)
        
        NSZE=self.IdNs.NSZE.int
        self.Print ("NSZE: %s"%NSZE       )

        #--------------------------------------------------
        SLBA=0
        msg0="read first block, SLBA=%s"%(SLBA)
        msg1="check if read command success(expected result: command success)"
        ret_code=ret_code if self.testDW10_DW11(SLBA, msg0, msg1, True) else 1
           
        #--------------------------------------------------
        SLBA=NSZE-1
        msg0="read last block, SLBA=%s"%(SLBA)
        msg1="check if read command success(expected result: command success)"
        ret_code=ret_code if self.testDW10_DW11(SLBA, msg0, msg1, True) else 1
           
        #--------------------------------------------------
        SLBA=NSZE
        msg0="read block exceed the current number of logical blocks allocated in the namespace, SLBA=%s"%(SLBA)
        msg1="check if read command success(expected result: command fail)"
        ret_code=ret_code if self.testDW10_DW11(SLBA, msg0, msg1, False) else 1        
        
        return ret_code    

    def SubCase3(self):
        ret_code=0
        self.Print ("set  cdw[31:26] from 0x0 to 0x3F and check if read command success(expected result: command success) ")

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

    def SubCase4(self):
        ret_code=0
        self.Print ("Test Command Dword 12 for NLB")

        NLB=0
        msg0="set NLB=%s"%(NLB)
        msg1="check if read command success(expected result: command success)"
        ret_code=ret_code if self.testDW12NLB(msg0, msg1, NLB, True) else 1
        
        NLB=self.MDTSinBlock-1
        msg0="set NLB=%s Maximum Data Transfer Size in blocks (MDTS)"%(NLB)
        msg1="check if read command success(expected result: command success)"
        ret_code=ret_code if self.testDW12NLB(msg0, msg1, NLB, True) else 1
        
        NLB=self.MDTSinBlock
        msg0="set NLB=%s to exceed the maximum transfer size"%(NLB)
        msg1="check if read command success(expected result: command fail)"
        ret_code=ret_code if self.testDW12NLB(msg0, msg1, NLB, False) else 1       
        
        
        return ret_code

    def SubCase5(self):
        ret_code=0
        self.Print ("set Command Dword 13 from 0x0 to 0xFF and check if read command success(expected result: command success) ")

        for i in range(0x100):
            DSM=i
            ret_code=ret_code if self.testDW13(DSM, True) else 1
        
        if ret_code==0:
            self.Print("PASS", "p") 
        else:
            self.Print("Fail", "f")        
        
        return ret_code

    def SubCase6(self):
        ret_code=0
        self.Print ("set Command Dword 14 from 0x0 to 0xFF and check if read command success(expected result: command success) ")
                
        for i in range(0x100):
            EILBRT= (i<<24) +(i<<16) +(i<<8) + i
            ret_code=ret_code if self.testDW14(EILBRT, True) else 1
        
        if ret_code==0:
            self.Print("PASS", "p") 
        else:
            self.Print("Fail", "f")
        return ret_code

    def SubCase7(self):
        ret_code=0
        self.Print ("set Command Dword 15 from 0x0 to 0xFF and check if read command success(expected result: command success) ")
        
        
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
    DUT = SMI_Read(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 
    
    
    
    
    
