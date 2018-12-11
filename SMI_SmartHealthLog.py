#!/usr/bin/env python

# Import python built-ins
import sys
from time import sleep
import threading
import re

# Import VCT modules
from lib_vct.NVME import NVME
from lib_vct.NVMECom import deadline

class SMI_SmartHealthLog(NVME):
    # Script infomation
    ScriptName = "SMI_SmartHealthLog.py"
    Author = "Sam Chan"
    Version = "20181211"
    
    # <Attributes>
    # </Attributes>
    
    def __init__(self, argv):
        # initial parent class
        super(SMI_SmartHealthLog, self).__init__(argv)
        
        # add all sub items to test script list
        self.AddScript(self.Script0)
        self.AddScript(self.Script1)
        
    # <sub item scripts>
    @deadline(3)
    def Script0(self):
        sleep(1)
        print "123456"
        sleep(5)
        print "123"
    
    @deadline(60)
    def Script1(self):
        print "abcde"    
        
    # </sub item scripts>
    
    
    
    
if __name__ == "__main__":
    DUT = SMI_SmartHealthLog(sys.argv ) 
    DUT.RunScript()
    
    
    
    
    
    
