#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
import re
# Import VCT modules
from lib_vct.NVME import NVME
from SMI_Dell_HostMetadataDataStructure import SMI_Dell_HostMetadataDataStructure
from SMI_Identify import SMI_IdentifyCommand
from SMI_Sanitize import SMI_Sanitize
from SMI_Format import SMI_Format

class SMI_Dell_vendor_feature(NVME):
    ScriptName = "SMI_Dell_vendor_feature.py"
    Author = "Sam"
    Version = "20210720"         
    
    def SetAndVerifyHCTM(self,TMT1, TMT2):
        self.Print ("Issue command to set TMT1=MXTMT-2( %s), TMT2=MXTMT-1( %s)"%(TMT1, TMT2))
        self.SetTMT1_TMT2(TMT1, TMT2)
        self.Print ("Issue command to get TMT1, TMT2")
        TMT1rt, TMT2rt = self.GetTMT1_TMT1()
        self.Print ("Returned current TMT1, TMT2 value is : %s, %s "%(TMT1rt, TMT2rt)) 
        self.Print ("Check if set feature is success(expect current TMT1, TMT2 =  %s, %s)"%(TMT1, TMT2))
        if TMT1rt==TMT1 and TMT2rt==TMT2:
            self.Print("Pass", "p")
            return True
        else:
            self.Print("Fail", "f")
            return False        
    
    def GetTMT1_TMT1(self):
        buf = self.get_feature(0x10)
        TMT=0
        TMT1=0
        TMT2=0
        # get feature
        mStr="Current value:(.+$)"
        if re.search(mStr, buf):
            TMT=int(re.search(mStr, buf).group(1), 16)
            TMT1=TMT>>16
            TMT2=TMT&0xFFFF    
        return TMT1, TMT2
    
    def GetSavedTMT1_TMT1(self):
        buf = self.get_feature(0x10, sel=2)
        TMT=0
        TMT1=0
        TMT2=0
        # get feature
        mStr="Saved value:(.+)"
        if re.search(mStr, buf):
            TMT=int(re.search(mStr, buf).group(1), 16)
            TMT1=TMT>>16
            TMT2=TMT&0xFFFF    
        return TMT1, TMT2    
    
    def SetTMT1_TMT2(self, TMT1, TMT2):
        
        TMT=(TMT1<<16)+(TMT2)
        # set feature
        return self.set_feature(0x10, TMT)       
              
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
    SubCase4Desc =  "[Hynix SRS] HCTM Persistancy for item 12.9"   
    SubCase4KeyWord = "https://jira.siliconmotion.com.tw:8443/browse/VCTDEPT-891"
    def SubCase4(self):
        ret_code = 0
        if self.IdCtrl.HCTMA.int==1:
            self.Print( "Controller support HCTM", "p")
            self.TMT1bk, self.TMT2bk = self.GetTMT1_TMT1()   
            self.Print ("Current TMT1, TMT2 value is : %s, %s "%(self.TMT1bk, self.TMT2bk), "b")    
            self.MNTMT = self.IdCtrl.MNTMT.int
            self.MXTMT = self.IdCtrl.MXTMT.int
            self.Print ("Minimum Thermal Management Temperature(MNTMT): %s "%self.MNTMT)
            self.Print ("Maximum Thermal Management Temperature(MXTMT): %s "%self.MXTMT)
            
            self.TMT1sv, self.TMT2sv= self.GetSavedTMT1_TMT1()
            self.Print ("Saved TMT1, TMT2 value is : %s, %s "%(self.TMT1bk, self.TMT2bk), "b")                                       
        else:
            self.Print( "Controller do not support HCTM", "w")
            return 1        
        
        
        
        self.Print( "")
        self.Print ("If Controller Reset, maintain TMT1 and TMT2 field. If Powercycle, should not maintain the Value")
         
        # Note, MNTMT<= valid_value <=MXTMT
        TMT1=self.MXTMT-2
        TMT2=self.MXTMT-1   
        self.Print( "")
        self.Print( "(1) NVMe reset test", "b")
        self.SetPrintOffset(4)
        if not self.SetAndVerifyHCTM(TMT1, TMT2): return 1
        
        self.Print( "")
        self.Print( "Issue nvme reset")
        self.nvme_reset()                    
        TMT1rt, TMT2rt = self.GetTMT1_TMT1()
        self.Print ("Read and get current TMT1, TMT2 value is : %s, %s "%(TMT1rt, TMT2rt)) 
        self.Print ("Check if feature is maintained( i.e. expect TMT1, TMT2 =  %s, %s)"%(TMT1, TMT2))
        if TMT1rt==TMT1 and TMT2rt==TMT2:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            ret_code = 1        
               
        self.Print( "")
        self.SetPrintOffset(0)
        self.Print( "(2) POR test", "b")
        self.SetPrintOffset(4)
        if not self.SetAndVerifyHCTM(TMT1, TMT2): return 1
        self.Print( "")
        self.Print( "Do POR")
        if not self.por_reset(): return 1                    
        TMT1rt, TMT2rt = self.GetTMT1_TMT1()
        self.Print ("Current TMT1, TMT2 value is : %s, %s "%(TMT1rt, TMT2rt)) 
        self.Print ("Check if feature does not maintain the Value and equal to saved value(expect current TMT1, TMT2 =  %s, %s)"\
                    %(self.TMT1sv, self.TMT2sv))
        if TMT1rt==self.TMT1sv and TMT2rt==self.TMT2sv:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            ret_code = 1

        self.Print( "")
        self.SetPrintOffset(0)
        self.Print( "(3) SPOR test", "b")
        self.SetPrintOffset(4)
        if not self.SetAndVerifyHCTM(TMT1, TMT2): return 1
               
        self.Print( "")
        self.Print( "Do SPOR")
        if not self.spor_reset(): return 1                    
        TMT1rt, TMT2rt = self.GetTMT1_TMT1()
        self.Print ("Current TMT1, TMT2 value is : %s, %s "%(TMT1rt, TMT2rt)) 
        self.Print ("Check if feature does not maintain the Value and equal to saved value(expect current TMT1, TMT2 =  %s, %s)"\
                    %(self.TMT1sv, self.TMT2sv))
        if TMT1rt==self.TMT1sv and TMT2rt==self.TMT2sv:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            ret_code = 1            

        self.Print( "")
        self.SetPrintOffset(0)
        self.Print ("(4)Reset HCTM to previous value(%s, %s)"%(self.TMT1bk, self.TMT2bk), "b")
        self.SetPrintOffset(4)
        if not self.SetAndVerifyHCTM(self.TMT1bk, self.TMT2bk): return 1
        self.SetPrintOffset(0)

        return ret_code        
        



    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_Dell_vendor_feature(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    