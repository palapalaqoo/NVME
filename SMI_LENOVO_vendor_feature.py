#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
# Import VCT modules
from lib_vct.NVME import NVME
from SMI_Identify import SMI_IdentifyCommand

class SMI_Lenovo_vendor_feature(NVME):
    ScriptName = "SMI_Lenovo_vendor_feature.py"
    Author = "Sam"
    Version = "20210419"
    
    def __init__(self, argv):
        # initial parent class
        super(SMI_Lenovo_vendor_feature, self).__init__(argv)

    # define pretest, if not return 0 , skip all subcases
    def PreTest(self):        
        return 0            

    # <define sub item scripts>
    SubCase1TimeOut = 60
    SubCase1Desc = "[Hynix SRS] Identify Lenovo Security Feature Supported"   
    SubCase1KeyWord = "https://jira.siliconmotion.com.tw:8443/browse/VCTDEPT-906"
    def SubCase1(self):
        return self.runSubCase(SMI_IdentifyCommand, 2, appendCMD=["-v", "lenovo"])

    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_Lenovo_vendor_feature(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    