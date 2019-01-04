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
from lib_vct.NVME import DevWakeUpAllTheTime

class SMI_FeatureTimeStamp(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_FeatureTimeStamp.py"
    Author = "Sam Chan"
    Version = "20181211"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
  

    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    
    def SetTimeStamp(self, milliseconds):
        byte0='{:02x}'.format(milliseconds & 0x0000000000FF)
        byte1='{:02x}'.format((milliseconds & 0x00000000FF00) >>8)
        byte2='{:02x}'.format((milliseconds & 0x000000FF0000) >>16)
        byte3='{:02x}'.format((milliseconds & 0x0000FF000000) >>24)
        byte4='{:02x}'.format((milliseconds & 0x00FF00000000) >>32)
        byte5='{:02x}'.format((milliseconds & 0xFF0000000000) >>40)
    
        self.shell_cmd("echo -n -e '\\x%s\\x%s\\x%s\\x%s\\x%s\\x%s' |nvme admin-passthru %s -o 0x9 -l 8 -w --cdw10=0xE 2>&1"%(byte0, byte1, byte2, byte3, byte4, byte5, self.dev))
    
    def PrintFormatedTime(self):
        self.Refresh()
        Timestamp=self.Timestamp
        self.Print ("Timestampstamp = %s (%s milliseconds)"%(hex(self.Timestamp), self.Timestamp))
        #      localtime or gmtime
        mStr=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.Timestamp/1000))
        self.Print ("Formatted Timestamp(local time) = %s "%mStr)
        return  self.Timestamp
        
    def GetDataStructure(self):
        # get DataStructure of time stamp
        # return 8 bytes
        mbuf=self.shell_cmd("nvme admin-passthru %s --opcode=0xA --data-len=8 -r --cdw10=0xE 2>&1"%self.dev)
        line="0"
        # if command success
        if re.search("NVMe command result:00000000", mbuf):
            patten=re.findall("\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}", mbuf)            
            patten1= ''.join(patten)
            line=patten1.replace(" ", "")
            # return list
            # put patten in to list type
            n=2
            return [line[i:i+n] for i in range(0, len(line), n)]    
        else:
            return [0]   
    
    def Refresh(self):
        self.DS=self.GetDataStructure()
        if not len(self.DS)==8:
            self.Print("Get feature fail", "f")

    @property
    def Timestamp(self):
        return int(self.DS[0], 16) + (int(self.DS[1], 16)<<8) + (int(self.DS[2], 16)<<16) + (int(self.DS[3], 16)<<24) + (int(self.DS[4], 16)<<32) + (int(self.DS[5], 16)<<40)

    @property
    def Origin(self):
    # return int, range 0 to 7
        return (int(self.DS[6], 16) & 0b00001110) >>1

    @property
    def Synch(self):
    # return int, range 0 to 1
        return int(self.DS[6], 16) & 0b00000001
               
    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def __init__(self, argv):
        # initial parent class
        super(SMI_FeatureTimeStamp, self).__init__(argv)
        
        self.ONCS_bit6 = self.IdCtrl.ONCS.bit(6)        
        self.DS=""
        self.Refresh()
        
    # override
    def PreTest(self):   
        
        self.Print ("")
        self.Print ("Check if controll support Timestamp or not")
        if self.ONCS_bit6=="1":
            self.Print("Supported", "p")
            return True
        else:
            self.Print("Not supported", "p")
            self.Print ("quit all the test items!")
            return False 
            
            
    # <sub item scripts>
    SubCase1TimeOut = 60
    SubCase1Desc = "Test the accuracy of Timestamp values"        
    SubCase1KeyWord = "Synch"
    def SubCase1(self):
        ret_code=0
        #self.Print ("Send nvme reset command(Controller Level Reset)")
        self.nvme_reset()
        self.Print ("")
        self.Print ("Synch = %s"%self.Synch)
        if self.Synch==1:    
            self.Print ("Becouse Synch=1, In case of the controller may have stopped counting during vendor specific")
            self.Print ("Create a thread of compare operation to avoid controller enter non-operational power states")
            DWUATT=DevWakeUpAllTheTime(self)
            DWUATT.Start()
        
        last_Timestamp=0 
        sub_ret=0
        # Timestamp
        
        self.Print ("")
        self.Print ("print Timestamp every 1 second for 5 times")
        self.Print ("")
        
        for cnt in range(6):    
            Timestamp = self.PrintFormatedTime()
            if (Timestamp-last_Timestamp<900 or Timestamp-last_Timestamp>1100) and cnt !=0:
                sub_ret=1
            last_Timestamp=Timestamp
            sleep(1)
        
        self.Print ("")
        self.Print ("Check if Timestamp was incresed appropriately (> 0.9 second and < 1.1 second for every loop)")
        if sub_ret==0:
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1  
        
        
        
        if self.Synch==1: 
            self.Print ("")
            self.Print ("Delete thread of compare operation")
            DWUATT.Stop()

        return ret_code
    
    
    
    
    
    
    SubCase2TimeOut = 60
    SubCase2Desc = "Timestamp Origin field "
    SubCase2KeyWord="The Timestamp field was initialized with a Timestamp value using a Set Features command."
    def SubCase2(self): 
        ret_code=0
        self.Print ("If host set the Timestamp value, then the Timestamp Origin field must be set to 001b ")
        
        self.Print ("Set Timestamp=0")
        self.SetTimeStamp(0)
        
        
        self.Print ("")
        self.Print ("Get Timestamp")
        Timestamp = self.PrintFormatedTime()
        self.Print ("")
        self.Print ("Check if Timestamp field was initialized with a Timestamp value using a Set Features command or not(e.g. Timestamp<=100 milliseconds)")
        if Timestamp<=100:
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1  
        
        Origin= self.Origin
        self.Print ("Timestamp Origin = %s"%Origin)
        self.Print ("Check if Timestamp Origin field is set to 001b or not")
        if Origin==1:
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1  

        return ret_code
        
    SubCase3TimeOut = 60
    SubCase3Desc = "Test time exceeds 2^48"
    SubCase3KeyWord ="Timestamp field"
    def SubCase3(self): 
        ret_code=0
        self.Print ("If the sum of the Timestamp value set by the host and the elapsed time exceeds 2^48, the value returned should be reduced modulo 2^48 ")
        
        if self.Synch==1:    
            self.Print ("")
            self.Print ("Becouse Synch=1, In case of the controller may have stopped counting during vendor specific")
            self.Print ("Create a thread of compare operation to avoid controller enter non-operational power states")
            DWUATT=DevWakeUpAllTheTime(self)
            DWUATT.Start()
        
        self.Print ("")
        self.Print ("Set Timestamp=0xFFFFFFFFFFF0")
        self.SetTimeStamp(0xFFFFFFFFFFF0)
        self.PrintFormatedTime()
        
        self.Print ("")
        self.Print ("wait 2 seconds")
        sleep(2)
        
        self.Print ("")
        self.Print ("Get Timestamp")
        Timestamp = self.PrintFormatedTime()
        
        self.Print ("")
        self.Print ("Check if Timestamp was be reduced modulo 2^48(e.g. Timestamp <= 2100 milliseconds)")
        if Timestamp<=2100:
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1  
        
        if self.Synch==1: 
            self.Print ("")
            self.Print ("Delete thread of compare operation")
            DWUATT.Stop()        

        return ret_code






    # </sub item scripts>
    
    
    
    
if __name__ == "__main__":
    DUT = SMI_FeatureTimeStamp(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 
    
    
    
    
    
