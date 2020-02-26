#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
# Import VCT modules
from lib_vct.NVME import NVME

class SMI_XT_SRIOV(NVME):
    ScriptName = "SMI_XT_SRIOV.py"
    Author = "Sam"
    Version = "20200226"
    
    
    def GetCurrentMaxHMB(self):
    # return none or interger
        HMB_filename = "/sys/module/nvme/parameters/max_host_mem_size_mb"
        if not self.isfileExist(HMB_filename):
            return None
        else:            
            return int(self.shell_cmd("cat %s"%HMB_filename) )
            
    def TestHMB(self, TargetMHMB):
        self.Print("Try to reload NVMe driver with max_host_mem_size_mb=%s"%TargetMHMB)
        self.ReloadNVMeDriverWithSpecificParameter("max_host_mem_size_mb=%s"%TargetMHMB)
        CurrentMHMB = self.GetCurrentMaxHMB()
        if CurrentMHMB!=TargetMHMB:
            self.Print("Fail to set max_host_mem_size_mb=%s"%TargetMHMB, "f")
            return False
        self.Print("Success!")
    
        self.Print("Check if device is still working after Reload NVMe driver ")
        if not self.ctrl_alive:
            self.Print("Device is missing", "f")
            return False      
        self.Print("Pass!", "p") 
        
        return True       
    
    
    def __init__(self, argv):
        self.SetDynamicArgs(optionName="l", optionNameFull="loops", helpMsg="number of loops for cases", argType=int)
        # initial parent class
        super(SMI_XT_SRIOV, self).__init__(argv)

        self.loops = self.GetDynamicArgs(0)
        # set defalut loop =1   
        self.loops=1 if self.loops==None else self.loops        

    # define pretest  
    def PreTest(self):        
        return True            

    # <define sub item scripts>
    SubCase1TimeOut = 1800
    SubCase1Desc = "Test Host Memory Buffer"   
    SubCase1KeyWord = ""
    def SubCase1(self):      
        ret_code=0
        
        self.Print("Check if crontroller support HMB or not (identify HMPRE >0)")
        if self.IdCtrl.HMPRE.int==0:
            self.Print("crontroller is not support HMB, quit", "w")
            return 255      
        self.Print("Crontroller support HMB feature", "p")  
        
        self.Print("Check if current linux kernel support HMB or not")
        MHMB = self.GetCurrentMaxHMB()
        if MHMB==None:
            self.Print("Kernel is not support HMB, please use linux kernel 4.13+", "w")
            return 255
        self.Print("Kernel support HMB feature", "p")
        self.Print("Current max_host_mem_size_mb: %s"%MHMB)      
           
        for i in range(self.loops):
            self.Print("")
            self.Print("-- Current Loop: %s, Total loop: %s"%(i, self.loops))
            
            TargetMHMB=0
            if not self.TestHMB(TargetMHMB): return 1
            TargetMHMB=MHMB
            if not self.TestHMB(TargetMHMB): return 1       
                 
            

            
                                 
                
                
  
                
        
        return ret_code     
    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_XT_SRIOV(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    