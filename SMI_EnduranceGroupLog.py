#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
# Import VCT modules
from lib_vct.NVME import NVME

class SMI_EnduranceGroupLog(NVME):
    ScriptName = "SMI_EnduranceGroupLog.py"
    Author = "Sam"
    Version = "20210506"
    
    def getENDGID(self, ns):
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x0 --namespace-id=%s 2>&1"%(self.dev_port, ns)
        rTDS=self.shell_cmd(CMD)
        DS=self.AdminCMDDataStrucToListOrString(rTDS, 2)            
        if DS==None:
            return None
        else:
            return (DS[103]<<8) + DS[102]        
    
    def __init__(self, argv):
        # initial parent class
        super(SMI_EnduranceGroupLog, self).__init__(argv)
        
        
        self.EGsupported = True if self.IdCtrl.CTRATT.bit(4)=="1" else False


    # define pretest, if not return 0 , skip all subcases
    def PreTest(self):      
        self.Print("Check if controller support endurance group in Identify Controller Data Structure -> Controller Attributes (CTRATT) -> bit 4")
        if self.EGsupported:
            self.Print("Supported", "p")
            return 0 
        else:
            self.Print("Not supported, skip all test cases!", "w")
            # TODO
            #return 255 
        self.Print("Check if ENDGID in id-ns data structure in nsid=1 is not 0x0") 
        ENDGID = self.getENDGID(ns=1)
        if ENDGID == None:
            self.Print("Can not get id-ns data structure", "f")
            return 1
        self.Print("ENDGID: 0x%X"%self.ENDGID) 
        if self.ENDGID == 0:
            self.Print("Fail", "f")
            return 1
        else:
            self.Print("Pass", "p")
            
        return 0       
        
          
        return 0            

    # <define sub item scripts>
    SubCase1TimeOut = 60
    SubCase1Desc = ""   
    SubCase1KeyWord = ""
    def SubCase1(self):
        ret_code=0
        return ret_code

    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True
            
        


if __name__ == "__main__":
    DUT = SMI_EnduranceGroupLog(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    