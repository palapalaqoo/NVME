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

class SMI_FeatureNumberofQueues(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_FeatureNumberofQueues.py"
    Author = "Sam Chan"
    Version = "20181211"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
  

    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    
    
    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def __init__(self, argv):
        # initial parent class
        super(SMI_FeatureNumberofQueues, self).__init__(argv)
        
        
    # <sub item scripts>
    SubCase1TimeOut = 60
    SubCase1Desc = "Test NCQR"        
    def SubCase1(self):
        ret_code=0
        self.Print ("Test if NCQR specified is 65,535, the controller should return an error of Invalid Field in Command or not" )
        self.Print ("set NCQR=0xFFFF, NSQR=0x0")
        mStr=self.shell_cmd(" nvme set-feature %s -f 7 -v 0xFFFF0000 2>&1"%(self.dev))
        self.Print ("returned status code: %s" %mStr)
        self.Print ("Check returned status code")
        retCommandSueess=bool(re.search("INVALID_FIELD", mStr))
        if (retCommandSueess ==  True) :
            self.Print("PASS", "p")     
        else:
            self.Print("Fail", "f")
            ret_code=1
        return ret_code
    
    SubCase2TimeOut = 60
    SubCase2Desc = "Test NSQR"
    def SubCase2(self): 
        ret_code=0
        self.Print ("Test if NSQR specified is 65,535, the controller should return an error of Invalid Field in Command or not" )
        self.Print ("set NCQR=0x0, NSQR=0xFFFF")
        mStr=self.shell_cmd(" nvme set-feature %s -f 7 -v 0x0000FFFF 2>&1"%(self.dev))
        self.Print ("returned status code: %s" %mStr)
        self.Print ("Check returned status code")
        retCommandSueess=bool(re.search("INVALID_FIELD", mStr))
        if (retCommandSueess ==  True) :
            self.Print("PASS", "p")     
        else:
            self.Print("Fail", "f")
            ret_code=1    
        return ret_code

    SubCase3TimeOut = 60
    SubCase3Desc = "Test get feature for NCQA and NSQA"
    def SubCase3(self): 
        ret_code=0
        mStr=self.shell_cmd(" nvme get-feature %s -f 7 2>&1"%(self.dev))
        print mStr
        retCommandSueess=bool(re.search("Current value", mStr))
        if (retCommandSueess ==  True) :
            self.Print("PASS", "p")     
        else:
            self.Print("Fail", "f")
            ret_code=1        
        return ret_code

        
    # </sub item scripts>
    
    
    
    
if __name__ == "__main__":
    DUT = SMI_FeatureNumberofQueues(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 
    
    
    
    
    
