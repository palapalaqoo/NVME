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
import Queue

# Import VCT modules
from lib_vct.NVME import NVME

class SMI_ChangedNamespaceListLog(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_ChangedNamespaceListLog.py"
    Author = "Sam Chan"
    Version = "20190212"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    SubCase1TimeOut = 60
    SubCase1Desc = "Test Status Code - Command specific status values"    
    
    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def convert(self, lists, stopByte, startByte):   
        # return is string , eg, '0x1A'         
                    
        # sub bytes
        subList=lists[startByte : stopByte+1]
        # reverse it and combine
        subList=subList[::-1]
        subList_Str="".join(subList)
        # Converting string to int
        mStr = "0x"+subList_Str            

        return mStr
    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def __init__(self, argv):
        # initial parent class
        super(SMI_ChangedNamespaceListLog, self).__init__(argv)
        self.Log_Supported = True if self.IdCtrl.OAES.bit(8)=="1" else False
        self.NsSupported=True if self.IdCtrl.OACS.bit(3)=="1" else False      
        
      
    # override
    def PreTest(self):   
        if self.Log_Supported:
            self.Print("Changed Namespace List is supported", "p")
            self.Print("")
            return True
        else:
            self.Print("Changed Namespace List is not supported, quit test", "w")     
            self.Print("")       
            return False        
    
    # <sub item scripts>
    def SubCase1(self):
        ret_code=0
        self.Print ("")
        
        self.Print ("Issue get log command with id=0x4 to clear data in log page")
        self.get_log2byte(0x4, 16)
        self.Print ("Done")
        self.Print ("")
                
        MaxNs=1
        if self.NsSupported:
            self.Print ("Namespace Management supported: Yes")
            self.Print (  "try to create 3 namespaces" )
            # function CreateMultiNs() will create namespace less then 8 NS
            MaxNs = self.CreateMultiNs(3)
        else:
            self.Print ("Namespace Management supported: No")
            
        if MaxNs ==1:
            self.Print ("Number of namespaes: 1")
        else:
            self.Print ("Number of namespaes: from 1 to %s"%MaxNs)     

        self.Print ("")                
        self.Print ("Issue get log command with id=0x4 to get namespace list in log")
        # get first 32 byte of log, eg Identifier 0 to Identifier 7
        nsList = self.get_log_passthru(LID=0x4, size=32, BytesOfElement=4)
        
        if len(nsList)!=8:
            self.Print ("Fail to get log data, exit!", "f")
            ret_code=1
        else:
            self.Print ("Done")
            
            self.Print ("")
            

            
            for id in nsList:

                self.Print ("Check if Identifier 0 to Identifier 2 = [0x1, 0x2, 0x3] in namespace list ")
            
            
        
        



        return ret_code
    # </sub item scripts>
    
    
    
    
if __name__ == "__main__":
    DUT = SMI_ChangedNamespaceListLog(sys.argv ) 
    DUT.RunScript()
    DUT.Finish()
    
    
    
    
    
