#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
# Import VCT modules
from lib_vct.NVME import NVME
from SMI_Dell_HostMetadataDataStructure import SMI_Dell_HostMetadataDataStructure
from SMI_Identify import SMI_IdentifyCommand
from SMI_Sanitize import SMI_Sanitize
from SMI_Format import SMI_Format

class SMI_Dell_vendor_feature(NVME):
    ScriptName = "SMI_Dell_vendor_feature.py"
    Author = "Sam"
    Version = "20210326"      
              
    def __init__(self, argv):
        # initial parent class
        super(SMI_Dell_vendor_feature, self).__init__(argv)


    # define pretest, if not return 0 , skip all subcases
    def PreTest(self):        
        return 0            

    # <define sub item scripts>
    SubCase1TimeOut = 60000
    SubCase1Desc = "[Hynix SRS] Host Metadata Log"   
    SubCase1KeyWord = "https://jira.siliconmotion.com.tw:8443/browse/VCTDEPT-794"
    def SubCase1(self):
        return self.runSubCase(SMI_Dell_HostMetadataDataStructure, 1)

    SubCase2TimeOut = 60000
    SubCase2Desc = "[Hynix SRS] Identify Dell Vendor Specific"   
    SubCase2KeyWord = "https://jira.siliconmotion.com.tw:8443/browse/VCTDEPT-835"
    def SubCase2(self):
        return self.runSubCase(SMI_IdentifyCommand, 2, appendCMD=["-v", "dellx16"])

    SubCase3TimeOut = 60000
    SubCase3Desc = "[Hynix SRS] Sanitize Command-No Deallocate After Sanitize shall not be supported "   
    SubCase3KeyWord = "https://jira.siliconmotion.com.tw:8443/browse/VCTDEPT-788"
    def SubCase3(self):
        return self.runSubCase(SMI_Sanitize, 17, appendCMD=["-v", "dellx16"])
    
    SubCase4TimeOut = 60000
    SubCase4Desc =  "[Hynix SRS] Sanitize Command-Read only mode"   
    SubCase4KeyWord = "https://jira.siliconmotion.com.tw:8443/browse/VCTDEPT-788"
    def SubCase4(self):
        return self.runSubCase(SMI_Sanitize, 18, appendCMD=["-iknowwhatiamdoing"])            
        
    SubCase5TimeOut = 60000
    SubCase5Desc =  "[Hynix SRS] Format NVM requirement"   
    SubCase5KeyWord = "https://jira.siliconmotion.com.tw:8443/browse/VCTDEPT-743"
    def SubCase5(self):
        return self.runSubCase(SMI_Format, 18, appendCMD=["-iknowwhatiamdoing"])      

    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_Dell_vendor_feature(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    