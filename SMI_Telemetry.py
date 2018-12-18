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

class SMI_Telemetry(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_Telemetry.py"
    Author = "Sam Chan"
    Version = "20181211"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    SubCase1TimeOut = 60
    SubCase1Desc = "Test Data Blocks are 512 bytes in size or not, Log ID=07"    
    
    SubCase2TimeOut = 60
    SubCase2Desc = "Test Command Dword 10 -- Log Specific Field, Log ID=07"

    SubCase3TimeOut = 120
    SubCase3Desc = "Test Log Identifier in log byte0, Log ID=07"    

    SubCase4TimeOut = 60
    SubCase4Desc = "Test if IEEE OUI Identifier = identify.IEEE, Log ID=07"    

    SubCase5TimeOut = 60
    SubCase5Desc = "Test if Data Area 1 Last Block <= 2 Last Block<= 3 Last Block, Log ID=07"    
    
    SubCase6TimeOut = 60
    SubCase6Desc = "Test Telemetry Controller-Initiated Data Available"    
    
    SubCase7TimeOut = 60
    SubCase7Desc = "Test Telemetry Controller-Initiated Data Generation Number"

    SubCase8TimeOut = 120
    SubCase8Desc = "Test Data Blocks are 512 bytes in size or not, Log ID=08"       

    SubCase9TimeOut = 60
    SubCase9Desc = "Test Log Identifier in log byte0, Log ID=08"     

    SubCase10TimeOut = 60
    SubCase10Desc = "Test if IEEE OUI Identifier = identify.IEEE, Log ID=08"     

    SubCase11TimeOut = 60
    SubCase11Desc = "Test if Data Area 1 Last Block <= 2 Last Block<= 3 Last Block, Log ID=08"   
    
    SubCase12TimeOut = 60
    SubCase12Desc = "Test TCIDA value is persistent across power states and reset or not, Log ID=08"


    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def GetPS(self):
        return int(self.get_feature(2)[-1:])
            
    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    aaabbb=123456
    def __init__(self, argv):
        # initial parent class
        super(SMI_Telemetry, self).__init__(argv)
        
        self.ResetItem=[]
        self.ResetItem.append(["NVME reset", self.nvme_reset])
        self.ResetItem.append(["Hot reset", self.hot_reset])
        self.ResetItem.append(["Link reset", self.link_reset])
        self.ResetItem.append(["Subsystem reset", self.subsystem_reset])    
        
        self.SupportTelemetry=True if self.IdCtrl.LPA.bit(3)!="0" else False
        # Create Telemetry Host-Initiated Data bit = 0
        self.LOG07_0=self.get_log_passthru(7, 512, 0, 0)
        # Create Telemetry Host-Initiated Data bit = 1
        self.LOG07_1=self.get_log_passthru(7, 512, 0, 1)
        # Create Telemetry Host-Initiated Data bit = 0
        self.LOG08_0=self.get_log_passthru(8, 512, 0, 0)
        # Create Telemetry Host-Initiated Data bit = 1
        self.LOG08_1=self.get_log_passthru(8, 512, 0, 1)        

    # override PreTest()
    def PreTest(self):
        if DUT.SupportTelemetry:
            self.Print( "Controller support telemetry in Log Page Attributes (LPA)", "p")
        else:
            self.Print( "Controller do not support telemetry in Log Page Attributes (LPA)", "w")
        return DUT.SupportTelemetry
        
    # <override sub item scripts>
    def SubCase1(self):
        ret_code = 0
        print "Test if get log page command is not a multiple of 512 bytes for this log, then the controller shall return an error of Invalid Field in Command"
        
        for DataBlock in range(12, 513, 50):
            print "Send Get Log Page command for %s byte datas of Data Blocks "%DataBlock
            
            mStr = self.shell_cmd("nvme get-log %s --log-id=0x7 --log-len=%s 2>&1"%(self.dev, DataBlock))
            self.Print(mStr, 't')
        
            # if (not a multiple of 512 bytes and get get log fail) or (multiple of 512 bytes and get log success), then pass the test
            if (re.search("NVMe Status:INVALID_FIELD", mStr) and DataBlock!=512) or (not re.search("NVMe Status:INVALID_FIELD", mStr) and DataBlock==512):
                self.Print("PASS", "p")     
            else:
                self.Print("Fail", "f")
                ret_code=1       
        return ret_code
    
    def SubCase2(self):
        ret_code = 0
        print "check Command Dword 10 -- Log Specific Field for 'Create Telemetry Host-Initiated Data'"                
        if len(self.LOG07_0) == 512 and len(self.LOG07_1) == 512 and len(self.LOG08_0) == 512 and len(self.LOG08_1) == 512 :
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1 
            
        return ret_code
    
    def SubCase3(self):
        ret_code = 0        
        
        # get 512 byte log data where RAE=0, LSP=0
        self.LOG07=self.get_log_passthru(7, 512, 1, 0)
        self.LOG08=self.get_log_passthru(8, 512, 1, 0)
        
        
        
        print ""   
        print "Check Log Identifier in log byte0"
        
        LogId=self.LOG07[0]
        
        print "Log Identifier: %s"%LogId
        if LogId=="07":
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1 
        return ret_code  

    def SubCase4(self):
        ret_code = 0          
        print "Check if IEEE OUI Identifier = identify.IEEE or not"
        IEEE=int((self.LOG07[7]+self.LOG07[6]+self.LOG07[5]),16)
        print "IEEE: %s, identify.IEEE: %s" %(IEEE, self.IdCtrl.IEEE.int)
        
        if IEEE==self.IdCtrl.IEEE.int:
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1       
        return ret_code
    
    def SubCase5(self):
        ret_code = 0    
        print "check if (Telemetry Host-Initiated Data Area 1 Last Block <= 2 Last Block<= 3 Last Block) or not"      
        LastBlock1=int(self.LOG07[9]+self.LOG07[8])
        LastBlock2=int(self.LOG07[11]+self.LOG07[10])
        LastBlock3=int(self.LOG07[13]+self.LOG07[12])
        print "1 Last Block: %s, 2 Last Block: %s, 3 Last Block: %s" %(LastBlock1, LastBlock2, LastBlock3)
        if (LastBlock1<=LastBlock2) and (LastBlock2<=LastBlock3):
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1       
        return ret_code

    def SubCase6(self):
        ret_code = 0          
        print "check if Telemetry Controller-Initiated Data Available in log ID 07h = Telemetry Controller-Initiated Data Available in log ID 08h  or not"
        print "TCIDA in 0x7h: %s, TCIDA in 0x8h: %s" %(self.LOG07[382], self.LOG08[382])      
        if self.LOG07[382]<=self.LOG08[382]:
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1         
        return ret_code

    def SubCase7(self):
        ret_code = 0          
        print "check if Telemetry Controller-Initiated Data Generation Number in log ID 07h = Telemetry Controller-Initiated Data Generation Number in log ID 08h  or not"
        print "TCIDGN in 0x7h: %s, TCIDGN in 0x8h: %s" %(self.LOG07[383], self.LOG08[383])
        if self.LOG07[383]<=self.LOG08[383]:
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1       
        return ret_code

    def SubCase8(self):
        ret_code = 0          
        print "Test if get log page command is not a multiple of 512 bytes for this log, then the controller shall return an error of Invalid Field in Command"
        for DataBlock in range(12, 513, 50):
            print "Send Get Log Page command for %s byte datas of Data Blocks "%DataBlock
            
            mStr = self.shell_cmd("nvme get-log %s --log-id=0x8 --log-len=%s 2>&1"%(self.dev, DataBlock))
            self.Print(mStr, 't')
        
            # if (not a multiple of 512 bytes and get get log fail) or (multiple of 512 bytes and get log success), then pass the test
            if (re.search("NVMe Status:INVALID_FIELD", mStr) and DataBlock!=512) or (not re.search("NVMe Status:INVALID_FIELD", mStr) and DataBlock==512):
                self.Print("PASS", "p")     
            else:
                self.Print("Fail", "f")
                ret_code=1               
        return ret_code

    def SubCase9(self):
        ret_code = 0          
        print "Check Log Identifier in log byte0"      

        LogId=self.LOG08[0]
        
        print "Log Identifier: %s"%LogId
        if LogId=="08":
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1 
        return ret_code

    def SubCase10(self):
        ret_code = 0          
        print "Check if IEEE OUI Identifier = identify.IEEE or not"
        IEEE=int((self.LOG08[7]+self.LOG08[6]+self.LOG08[5]),16)
        print "IEEE: %s, identify.IEEE: %s" %(IEEE, self.IdCtrl.IEEE.int)
        if IEEE==self.IdCtrl.IEEE.int:
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1       
        return ret_code

    def SubCase11(self):
        ret_code = 0          
        print "check if (Telemetry Controller-Initiated Data Area 1 Last Block <= 2 Last Block<= 3 Last Block) or not"
        LastBlock1=int(self.LOG08[9]+self.LOG08[8])
        LastBlock2=int(self.LOG08[11]+self.LOG08[10])
        LastBlock3=int(self.LOG08[13]+self.LOG08[12])
        print "1 Last Block: %s, 2 Last Block: %s, 3 Last Block: %s" %(LastBlock1, LastBlock2, LastBlock3)
        if (LastBlock1<=LastBlock2) and (LastBlock2<=LastBlock3):
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1       
        return ret_code
    
    def SubCase12(self):
        ret_code = 0          
        print "check if Telemetry Controller-Initiated Data Available(TCIDA) value is persistent across power states and reset or not"
        TCIDA_old=self.LOG08[383]
        print "TCIDA: %s" %TCIDA_old
        print "-- start test TCIDA for power state  --"
        NPSS=self.IdCtrl.NPSS.int
        print "NPSS: %s"%NPSS
             
        NPSS=self.IdCtrl.NPSS.int
            
        for i in range(NPSS+1):
            self.set_feature(2, i)
            print "set power state = %s"%i
            PS=self.GetPS()
            # verify set_feature successfull
            if PS!=i:
                self.Print("Set power state error! ", "f")
                ret_code=1
                break
                    
            # reload     
            self.LOG07=self.get_log_passthru(7, 512, 1, 0)
            self.LOG08=self.get_log_passthru(8, 512, 1, 0)
                
            print "TCIDA in log 0x7= %s"%self.LOG07[383]
            print "TCIDA in log 0x8= %s"%self.LOG08[383]
            if (TCIDA_old==self.LOG08[383]) and (TCIDA_old==self.LOG07[383]):
                self.Print("PASS", "p")    
            else:
                self.Print("Fail", "f")
                ret_code=1
                
        print "-- start test TCIDA for reset  --"        
        for Item in self.ResetItem:
            print Item[0]
        
            # trigger reset
            Item[1]()
            
            # reload 
            print "TCIDA in log 0x7= %s"%self.LOG07[383]
            print "TCIDA in log 0x8= %s"%self.LOG08[383]
            if (TCIDA_old==self.LOG08[383]) and (TCIDA_old==self.LOG07[383]):
                self.Print("PASS", "p")    
            else:
                self.Print("Fail", "f")
                ret_code=1               
        return ret_code

    
    # </sub item scripts>
    
    
    
    
if __name__ == "__main__":
    DUT = SMI_Telemetry(sys.argv ) 
    DUT.RunScript()
    DUT.Finish()
    
    
    
    
    
