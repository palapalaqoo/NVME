#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
from random import randint
from time import sleep
# Import VCT modules
from lib_vct.NVME import NVME

class SMI_Sanitize_JIRASMI213(NVME):
    ScriptName = "SMI_Sanitize_JIRASMI213.py"
    Author = "Sam"
    Version = "20200103"

    def WaitSanitizeOperationFinish(self, timeout=600, printInfo=False):
    # WaitSanitizeOperationFinish, if finish, then return true, else false(  after timeout )         
        if printInfo:
            self.Print ("")
            self.Print ("Wait sanitize operation finish if there is a sanitize operation is currently in progress(Time out = %s)"%timeout)
                        
        per = self.GetLog.SanitizeStatus.SPROG
        finish=True
        if per != 65535:
            # self.Print("The most recent sanitize operation is currently in progress, waiting the operation finish(Time out = 120s)", "w")
            WaitCnt=0
            while per != 65535:
                #print ("Sanitize Progress: %s"%per)
                per = self.GetLog.SanitizeStatus.SPROG
                WaitCnt = WaitCnt +1
                if WaitCnt ==timeout:
                    #self.Print("Time out!", "f")  
                    finish=False
                    break
                sleep(1)
            #self.Print ("Recent sanitize operation was completed")
   
        if printInfo:
            if finish:
                self.Print("Done", "p")
            else:
                self.Print("Error, Time out!", "f")  
        return finish       
        
    def __init__(self, argv):
        # initial parent class
        super(SMI_Sanitize_JIRASMI213, self).__init__(argv)
        self.CryptoEraseSupport = True if (self.IdCtrl.SANICAP.bit(0) == "1") else False
        self.BlockEraseSupport = True if (self.IdCtrl.SANICAP.bit(1) == "1") else False
        self.OverwriteSupport = True if (self.IdCtrl.SANICAP.bit(2) == "1") else False        

    # define pretest  
    def PreTest(self):   
        self.Print ("Check if Block Erase operation is Supported or  not in Sanitize Capabilities (SANICAP)")
        self.Print("Block Erase sanitize operation is Supported", "p")  if self.BlockEraseSupport else self.Print("Block Erase sanitize operation is not Supported, skip all!", "f")         
        if self.BlockEraseSupport:
            return True       
        else:
            return False     

    # <define sub item scripts>
    SubCase1TimeOut = 6000
    SubCase1Desc = "Test flow YMTC JIRA SMI-213"   
    SubCase1KeyWord = ""
    def SubCase1(self):
        ret_code=0

        TNOB = self.GetTotalNumberOfBlock()
        TestNLB = ((TNOB/10)/8)*8
        TestSize=TestNLB*512
        self.Print("Total number of blocks: %s"%TNOB)
        self.Print("Test size of blocks: %s(10%% of total blocks)"%TestNLB)
        self.Print("Test size: %s(Test size of blocks*512)"%TestSize)
        self.Print("")
        self.Print("1. prewrite(sequential write, blocksize=8*512B, pattern=0x57, fua=0) 10% of full disk as background data")
        self.fio_write(offset=0, size=TestSize, pattern=0x57, fio_bs="4k")
        self.Print("2. comparecheck background data to confirm data are successfully written")
        if self.fio_isequal(offset=0, size=TestSize, pattern=0x57, fio_bs="4k"):
            self.Print("Data compare pass!", "p")
        else:
            self.Print("Data compare fail!, quit", "f")
            return 1
        
        self.Print("")        
        self.SANACT=2
        CMD = "nvme admin-passthru %s --opcode=0x84 --cdw10=%s 2>&1"%(self.dev, self.SANACT)  
        self.Print ("3. issue Sanitize block erase cmd: %s"%CMD) 
        self.shell_cmd(CMD)   
        self.Print("4. check sanitize command completed, timeout 600s")
        if not self.WaitSanitizeOperationFinish(600):
            self.Print("Time out!, exit all test ", "f")  
            return 1       

        self.Print("") 
        Stime = randint(1, 5000)
        Stime=float(Stime)/1000
        self.Print("Sleep %.6f seconds"%(Stime) )
        sleep(Stime)
        self.Print("5. issue asyc power off and on") 
        self.spor_reset()
        self.Print("6. power on now")  
        
        self.Print("")        
        self.Print("7. check sanitize command completed, timeout 600s")
        if not self.WaitSanitizeOperationFinish(600):
            self.Print("Time out!, exit all test ", "f")  
            return 1 
        
        self.Print("")        
        self.Print("8. comparecheck background data (pattern 0)")    
        if self.fio_isequal(offset=0, size=TestSize, pattern=0x0, fio_bs="4k"):
            self.Print("Data compare pass!", "p")
        else:
            self.Print("Data compare fail!, quit", "f")
            return 1            
        
        
        
        
        return ret_code

    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_Sanitize_JIRASMI213(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    