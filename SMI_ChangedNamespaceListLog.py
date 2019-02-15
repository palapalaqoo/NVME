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
    
    def PrintAlignString(self,S0, S1, S2, S3, S4, S5, S6, S7, PF="default"):            
        mStr = "{:<8}{:<8}{:<8}{:<8}{:<8}{:<8}{:<8}{:<8}".format(S0, S1, S2, S3, S4, S5, S6, S7)
        if PF=="pass":
            self.Print( mStr , "p")        
        elif PF=="fail":
            self.Print( mStr , "f")      
        else:
            self.Print( mStr )    
            
            
    def GetAndCheckFirst8NsList(self, v0, v1, v2, v3, v4, v5, v6, v7,CheckMsg=""):
        success=True               
        self.Print ("Issue get log command with id=0x4 to get namespace list in log for Identifier 0 to Identifier 7")        
        # get first 32 byte of log, e.g. Identifier 0 to Identifier 7, string type
        nsList_s = self.get_log_passthru(LID=0x4, size=32, BytesOfElement=4)
        # convert to int
        nsList = [int(element, 16) for element in nsList_s]
        
        if len(nsList)!=8:
            self.Print ("Fail to get log data, exit!", "f")
            success=False
        else:
            self.Print ("Done")
            
            self.Print ("")
            self.PrintAlignString("id0","id1","id2","id3","id4","id5","id6","id7")
            self.Print ("----------------------------------------------------------------")
            self.PrintAlignString(nsList[0],nsList[1],nsList[2],nsList[3],nsList[4],nsList[5],nsList[6],nsList[7])
            self.Print ("")
            self.Print (CheckMsg)
            if nsList[0]==v0 and nsList[1]==v1 and nsList[2]==v2 and nsList[3]==v3 and nsList[4]==v4 and nsList[5]==v5 and nsList[6]==v6 and nsList[7]==v7:
                self.Print ("Pass", "p")
            else:
                self.Print ("Fail", "f")
                success=False
                
        return success
        
              
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
            self.Print ("Number of namespaes: 1 ,skip the test")
        else:
            self.Print ("Number of namespaes: from 1 to %s"%MaxNs)     

            self.Print ("")                
            msg = "Check if Identifier 0 to Identifier 2 = [0x1, 0x2, 0x3] and Identifier 3 to Identifier 7 = 0  in namespace list "
            if not self.GetAndCheckFirst8NsList(1, 2, 3, 0, 0, 0, 0, 0, msg):
                ret_code=1
    
            self.Print ("")                
            msg = "Check if all the values in log was set to 0 "
            if not self.GetAndCheckFirst8NsList(0, 0, 0, 0, 0, 0, 0, 0, msg):
                ret_code=1

            self.Print ("")                
            self.Print ("Issue format command to fomat namespace 2 and namespace 3")
            self.shell_cmd(" nvme format %s -n %s -l %s -s %s -p %s -i %s -m %s 2>&1" % (self.dev_port, 2, 0, 0, 0, 0, 0))
            self.shell_cmd(" nvme format %s -n %s -l %s -s %s -p %s -i %s -m %s 2>&1" % (self.dev_port, 3, 0, 0, 0, 0, 0))
            self.Print ("Done")                
            msg = "Check if Identifier 0 to Identifier 1 = [0x2, 0x3] and Identifier 2 to Identifier 7 = 0"  
            if not self.GetAndCheckFirst8NsList(2, 3, 0, 0, 0, 0, 0, 0, msg):
                ret_code=1            
           
            
        if MaxNs!=1:
            self.Print ("")
            self.Print("Reset all namespaces to namespace 1 and kill other namespaces")
            self.ResetNS()    
            
        
        return ret_code
    # </sub item scripts>
    
    
    
    
if __name__ == "__main__":
    DUT = SMI_ChangedNamespaceListLog(sys.argv ) 
    DUT.RunScript()
    DUT.Finish()
    
    
    
    
    
