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
    Version = "20200528"

    def WaitSanitizeOperationFinish(self, timeout=600):
    # WaitSanitizeOperationFinish, if finish, then return true, else false(  after timeout )         
                        
        per = self.GetLog.SanitizeStatus.SPROG
        if per != 65535:
            # self.Print("The most recent sanitize operation is currently in progress, waiting the operation finish(Time out = 120s)", "w")
            self.timer.start()
            while True:
                #print ("Sanitize Progress: %s"%per)
                per = self.GetLog.SanitizeStatus.SPROG
                self.PrintProgressBar(per, 65535, "SPROG: %s"%per)
                if per==65535:
                    return True

                if int(float(self.timer.time)) >=timeout: 
                    return False                    

        return True       
        
    def TestFlow(self, TestSize, Scale):
        self.SetPrintOffset(4)
        value = randint(0x1, 0xFF)              
        self.Print("1. prewrite(fio sequential write, fio_bs=64k, pattern=0x%X) 10%% of full disk as background data"%value)
        self.fio_write(offset=0, size=TestSize, pattern=value, fio_bs="64k", showProgress=True)
        self.Print("") 
        self.Print("2. comparecheck background data to confirm data are successfully written")
        if self.fio_isequal(offset=0, size=TestSize, pattern=value, fio_bs="64k"):
            self.Print("Data compare pass!", "p")
        else:
            self.Print("Data compare fail!, quit", "f")
            return False
        
        self.Print("")        
        self.SANACT=2
        CMD = "nvme admin-passthru %s --opcode=0x84 --cdw10=%s 2>&1"%(self.dev, self.SANACT)  
        self.Print ("3. issue Sanitize block erase cmd: %s"%CMD) 
        self.shell_cmd(CMD)   
        self.Print("") 
        self.Print("4. check if sanitize is in progress(SPROG change), if SPROG has not changed in 60s, fail the test")
        WaitCnt = 0
        per=0
        while True:
            per = self.GetLog.SanitizeStatus.SPROG
            if per!=0 and per!=65536:
                break;
            else:
                WaitCnt = WaitCnt+1
            if WaitCnt>60:
                self.Print("Time out!, SPROG never changed, exit all test ", "f")  
                return False   
            sleep(1)             
        self.Print("Sanitize is in progress now, SPROG= %s"%per)
    

        self.Print("") 

        self.Print("5. issue asyc power off and on when SPROG > %s"%(Scale))         
        while True:
            per = self.GetLog.SanitizeStatus.SPROG
            self.PrintProgressBar(per, 65535, "SPROG: %s"%per)     
            if per>Scale:
                break;    
                               
        self.Print("") 
        self.Print("powering off ..") 
        self.Print("")   
        if not self.spor_reset(sleep_time=0):
            self.Print("6. power on fail, can not find device: %s, quit!"%self.dev, "f")  
            return False
        self.Print("6. power on now")  
        
        self.Print("")        
        self.Print("7. check sanitize command completed, timeout 600s")
        if not self.WaitSanitizeOperationFinish(600):
            self.Print("Time out!, exit all test ", "f")  
            return False 
        self.Print("Sanitize command was completed")
        
        self.Print("")        
        self.Print("8. comparecheck background data (pattern 0)")    
        if self.fio_isequal(offset=0, size=TestSize, pattern=0x0, fio_bs="4k"):
            self.Print("Data compare pass!", "p")
        else:
            self.Print("Data compare fail!, quit", "f")
            return False  
        
        self.SetPrintOffset(0)
        return True
                 
        
    def __init__(self, argv):
        self.SetDynamicArgs(optionName="l", optionNameFull="testLoop", helpMsg="test Loop, default=1", argType=int) 
        self.SetDynamicArgs(optionName="z", optionNameFull="prewriteSize", helpMsg="test Size, default=0.1 means 10%% prewriteSize,"\
                            " ex, prewrite 20%% capacity of SSD, -z 0.2", argType=str) 
  
        self.SetDynamicArgs(optionName="scale", optionNameFull="sprogScale", helpMsg="sprog Scale, default=0 "\
                            "every loop will have several cycles to verify the function with specific spor timer.   \n"\
                            "script will do spor as SPROG> sprogScale and SPROG> sprogScale*2 and so on. \n"\
                            "ex, python SMI_Sanitize_JIRASMI213.py /dev/nvme0n1 -scale 1000, will do spor as SPROG>1000 at first cycle \n"\
                            "and will do spor as SPROG>2000 at second cycle until last cycle to do spor as SPROG>65000, then finish the loop \n"\
                            "it also means it will do int(65536/1000) = 65 cycle test for 1 loop \n"\
                            "if sprogScale not set, spor timer will be random in 1 to 65534 to do spor ", argType=int) 
 
        
        # initial parent class
        super(SMI_Sanitize_JIRASMI213, self).__init__(argv)
        
        self.loops = self.GetDynamicArgs(0)  
        self.loops=1 if self.loops==None else self.loops   
        
        self.prewriteSize = self.GetDynamicArgs(1)  
        self.prewriteSize=0.1 if self.prewriteSize==None else float(self.prewriteSize)   
        
        self.sprogScale = self.GetDynamicArgs(2)  
        self.sprogScale=0 if self.sprogScale==None else self.sprogScale               
        
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

        TNOB = self.GetTotalNumberOfBlock()
        TestNLB = int((TNOB*self.prewriteSize)/8)*8
        TestSize=TestNLB*512
        self.Print("Total number of blocks: %s"%TNOB)
        self.Print("Test size of blocks: %s(%s%% of total blocks)"%(TestNLB, int(self.prewriteSize*100)))
        self.Print("Test size: %s bytes(Test size of blocks*512)"%TestSize)
        self.Print("Test loop: %s"%self.loops)
        
        
        for loop in range(self.loops):
            self.Print("")

                
            if self.sprogScale==0:
                Scale = randint(1, 65534)  
                self.Print("loop: %s, do spor at SPROG: %s"%(loop, Scale), "b")
                if not self.TestFlow(TestSize, Scale):
                    return 1   
                self.Print("")             
            else:                
                cycle=0
                Scale = self.sprogScale
                while True: 
                    self.Print("loop: %s, cycle: %s, do spor at SPROG: %s"%(loop, cycle, Scale), "b")
                    if not self.TestFlow(TestSize, Scale):
                        return 1  
                    
                    self.Print("")
                    cycle = cycle+1
                    Scale = Scale + self.sprogScale   
                    if Scale>65534:
                        break               
            

         
        
        return 0

    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_Sanitize_JIRASMI213(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    