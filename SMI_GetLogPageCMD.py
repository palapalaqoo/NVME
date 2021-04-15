#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
# Import VCT modules
from lib_vct.NVME import NVME

class SMI_GetLogPageCMD(NVME):
    ScriptName = "SMI_GetLogPageCMD.py"
    Author = "Sam"
    Version = "20210413"
    
    def __init__(self, argv):
        # initial parent class
        super(SMI_GetLogPageCMD, self).__init__(argv)

    # define pretest, if not return 0 , skip all subcases
    def PreTest(self):        
        return 0            

    # <define sub item scripts>
    SubCase1TimeOut = 600
    SubCase1Desc = "Verify vaild/invalid LID and Log Specific Field"   
    SubCase1KeyWord = "https://jira.siliconmotion.com.tw:8443/browse/VCTDEPT-862"
    def SubCase1(self):
        ret_code=0

        
        self.Print("Issue get log page with CDW10[11:0] from 0x0 to 0xFFF, and expected controller will work correctly after get log command")
        self.Print("")
        for CDW10 in range(0, 0x1000):
            CMD = "nvme admin-passthru %s --opcode=02 --data-len=512 -r --cdw10=%s 2>&1"\
            %(self.dev, CDW10)
            self.timer.start(returnType = "float")
            mStr, sc = self.shell_cmd_with_sc(CMD)
            TimeUsage = self.timer.time
            LID=CDW10&0xFF
            LSF=(CDW10&0xF00)>>8
            self.Print("LID: %s, Log Specific Field: %s, returned status: %s, TimeUsage: %s second"%(LID, LSF, sc, TimeUsage))
            if not self.dev_alive:
                self.Print("Fail, %s is missing after command"%self.dev)
                ret_code = 1
                break
            
        
        
        return ret_code

    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_GetLogPageCMD(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    