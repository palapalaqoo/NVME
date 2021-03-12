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
from random import randint

# Import VCT modules
from lib_vct.NVME import NVME
from lib_vct.NVME import DevWakeUpAllTheTime

class SMI_FeatureTimeStamp(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_FeatureTimeStamp.py"
    Author = "Sam Chan"
    Version = "20200518"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
  

    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    
    def SetTimeStamp(self, milliseconds, SV=0):
        byte0='{:02x}'.format(milliseconds & 0x0000000000FF)
        byte1='{:02x}'.format((milliseconds & 0x00000000FF00) >>8)
        byte2='{:02x}'.format((milliseconds & 0x000000FF0000) >>16)
        byte3='{:02x}'.format((milliseconds & 0x0000FF000000) >>24)
        byte4='{:02x}'.format((milliseconds & 0x00FF00000000) >>32)
        byte5='{:02x}'.format((milliseconds & 0xFF0000000000) >>40)
        
        if SV==0:
            dw10 = 0xE
        else:
            dw10 = 0xE| (0x1<<31)   # for set feature to saveable, set dw10 bit 31=1        
        mStr, sc = self.shell_cmd_with_sc("echo -n -e '\\x%s\\x%s\\x%s\\x%s\\x%s\\x%s' |nvme admin-passthru %s -o 0x9 -l 8 -w --cdw10=0x%X 2>&1"%(byte0, byte1, byte2, byte3, byte4, byte5, self.dev, dw10))
        return mStr, sc
    
    def PrintFormatedTime(self, sel=0):
    # sel : sel in get feature command
        self.Refresh(sel)
        Timestamp=self.Timestamp
        self.Print ("Timestampstamp = %s (%s milliseconds)"%(hex(self.Timestamp), self.Timestamp))
        #      localtime or gmtime
        mStr=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.Timestamp/1000))
        self.Print ("Formatted Timestamp(local time) = %s "%mStr)
        return  self.Timestamp
        
    def GetDataStructure(self, sel=0):
        # Select (SEL): This field specifies which value of the attributes to return in the provided data
        # get DataStructure of time stamp
        # return 8 bytes
        dw10=0xE
        dw10 = dw10 | (sel<<8)
        mbuf=self.shell_cmd("nvme admin-passthru %s --opcode=0xA --data-len=8 -r --cdw10=0x%X 2>&1"%(self.dev, dw10))
        line="0"
        rawData = [0]
        result = 255
        # if command success
        # NVMe command result:00000000
        pattern = "NVMe command result:.*(\w+)"
        if re.search(pattern, mbuf):
            patten=re.findall("\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}", mbuf)            
            patten1= ''.join(patten)
            line=patten1.replace(" ", "")
            # return list
            # put patten in to list type
            n=2
            rawData = [line[i:i+n] for i in range(0, len(line), n)]   
            result = re.search(pattern, mbuf).group(1)
            result = int("0x%s"%result, 16)
        return result, rawData

    
    def Refresh(self, sel=0):
    # sel : sel in get feature command
        result, self.DS=self.GetDataStructure(sel)
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
            return 0
        else:
            self.Print("Not supported", "p")
            self.Print ("quit all the test items!")
            return 255 
            
            
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
            KeepWakeUp=True
        else:
            KeepWakeUp=False
            
        if KeepWakeUp:    
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
        
        
        
        if KeepWakeUp: 
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
            KeepWakeUp=True
        else:
            KeepWakeUp=False
                    
        if KeepWakeUp:    
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
        
        if KeepWakeUp: 
            self.Print ("")
            self.Print ("Delete thread of compare operation")
            DWUATT.Stop()        

        return ret_code

    
    SubCase4TimeOut = 60
    SubCase4Desc = "Test feature saveable value"
    SubCase4KeyWord ="If the Timestamp feature supports a saveable value\n"\
    "then the timestamp value restored after a subsequent power on or reset event is the value that was saved"
    def SubCase4(self):
        self.Print ("")
        ret_code = 0
        
        self.Print("Check if feature is saveable or not", "b")
        SELSupport = True if self.IdCtrl.ONCS.bit(4)=="1" else False
        if SELSupport:
            self.Print("Get feature with sel option is supported")
        else:
            self.Print("Get feature with sel option is not supported, skip test case.")
            return 0

        self.Print("Issue get feature with sel = 3 for feature capabilities")
        capabilities , SC=self.GetFeatureValueWithSC(fid=0xE, sel=3)
        if SC!=0:
            self.Print("Command fail(get feature with sel = 3)", "f")
            self.Print("CMD: %s"%self.LastCmd, "f")
            return 1
        else:
            self.Print("Capabilities: 0x%X"%capabilities)
            
        saveable=True if capabilities&0b001 > 0 else False 
        if saveable:#saveable
            self.Print("feature is saveable")
        else:
            self.Print("feature is not saveable, skip test case")
            return 0
        
        self.Print ("")
        self.Print ("Setting Current Timestamp=0", "b")
        self.SetTimeStamp(0)  
        self.Print ("Get Current Timestamp")
        Timestamp = self.PrintFormatedTime()         
        self.Print ("Check if Current Timestamp was set to 0x0(e.g. Timestamp <= 100 milliseconds)")
        if Timestamp<=100:
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            return 1        
        
        self.Print ("")
        saveValue = randint(1, 0xFF) 
        saveValue = saveValue << 16 # shift 0x10000
        self.Print ("Setting saved Timestamp=0x%X(%d milliseconds) with save=1 in cdw10"%(saveValue, saveValue), "b")
        self.SetTimeStamp(saveValue, SV=1) 
        self.Print("Done")
        
        self.Print ("")
        self.Print ("Do nvme reset", "b") 
        self.nvme_reset()        
        self.Print ("nvme reset finish")
                                 
        self.Print ("")
        self.Print ("Get and verify Current Timestamp", "b")
        self.Print ("Read Current Timestamp")
        Timestamp = self.PrintFormatedTime()
        self.Print ("Check if Current Timestamp was the same as saved value (e.g. Timestamp <= (0x%X + 0x7D0) milliseconds, where 0x7D0 is 2S tolerance)"%saveValue)
        if Timestamp<= saveValue+2000:
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1
            
        self.Print ("")
        self.Print ("Get and verify saved Timestamp", "b")
        self.Print ("Read saved Timestamp")
        Timestamp = self.PrintFormatedTime(sel=0x2)
        self.Print ("Check if Timestamp was the same as saved value (e.g. Timestamp =  0x%X)"%saveValue)
        if Timestamp==saveValue:
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1  
            
        return ret_code
    
    # </sub item scripts>
             
   
if __name__ == "__main__":
    DUT = SMI_FeatureTimeStamp(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 
    
    
    
    
    
