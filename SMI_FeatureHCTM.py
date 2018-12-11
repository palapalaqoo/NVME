#!/usr/bin/env python

# Import python built-ins
import sys
import time
from time import sleep
import threading
import re

# Import VCT modules
from lib_vct.NVME import NVME
from lib_vct.NVMECom import deadline

class SMI_SmartHealthLog(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_FeatureHCTM.py"
    Author = "Sam Chan"
    Version = "20181211"
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    
    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def GetPS(self):
        return int(self.get_feature(2)[-1:])
    
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
    
    def SetTMT1_TMT2(self, TMT1, TMT2):
        
        TMT=(TMT1<<16)+(TMT2)
        # set feature
        return self.set_feature(0x10, TMT)   
    def CheckisINVALID_FIELD(self, strin):
        global  ret_code
        mStr = "INVALID_FIELD"
        if re.search(mStr, strin):
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            ret_code = 1
    
    def ResetHCTM(self):
        print ""
        print "Set TMT1=MXTMT-1, TMT2=MXTMT to exit the HCTM status if the HCTM is acting "
        mTMT1=self.MXTMT-1
        mTMT2=self.MXTMT
        print "Set TMT1= %s, TMT2= %s"%(self.KelvinToC(mTMT1), self.KelvinToC(mTMT2))
        self.SetTMT1_TMT2(mTMT1, mTMT2)
        sleep(1)
           
    def CheckisSuccess(self, strin):
        global  ret_code
        mStr = "INVALID_FIELD"
        if not re.search(mStr, strin):
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            ret_code = 1       
    
    def RaisingTempture(self, TargetTemp, TimeOut):
    # TimeOut = time limit in secend
    # TargetTemp =temp in Kelvin degree
    # Return last tempture read from controller
        TimeCnt=0
        aa=time.time()
        TempNow=0
        while True:                     
            # writing
            mThreads=self.nvme_write_multi_thread(thread=4, sbk=0, bkperthr=512, value=0x5A)
            for process in mThreads:   
                process.join()
            
            TimeCnt= int(time.time()-aa) 
            PS = self.GetPS()    
            TempNow = self.GetLog.SMART.CompositeTemperature
            mSuffix="Temperature: %s C, Power State: %s"%(self.KelvinToC(TempNow), PS)
            
            # progressbar
            if TimeCnt<TimeOut:
                self.PrintProgressBar(TimeCnt, TimeOut, prefix = 'Time Usage:', suffix = mSuffix, length = 50)
            else:
                self.PrintProgressBar(TimeOut, TimeOut, prefix = 'Time Usage:', suffix = mSuffix, length = 50)
                print "After %s s, time out !,  stop to increase temperature !"%TimeOut
                break
                    
            if TempNow>=TargetTemp: 
                print ""
                print "After %s s, temperature is large then target temperature now, stop to increase temperature !"%TimeCnt
                break
    
        return TempNow
        
        # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def __init__(self, argv):
        # initial parent class
        super(SMI_SmartHealthLog, self).__init__(argv)
        
        # <Parameter>
        self.HCTMA = self.IdCtrl.HCTMA.int
        self.MNTMT = self.IdCtrl.MNTMT.int
        self.MXTMT = self.IdCtrl.MXTMT.int
        self.TMT1bk, self.TMT2bk = self.GetTMT1_TMT1()      
        # </Parameter>
        
        # add all sub items to test script list
        self.AddScript(self.Script0, "Test if controller accept TMT1 and TMT2 value is zero or not")
        self.AddScript(self.Script1)
        
    # <sub item scripts>
    @deadline(60)
    def Script0(self):
  
        
        print "123456"
        return 0
    
    @deadline(60)
    def Script1(self):
        print "abcde"  
        return 1  
        
    # </sub item scripts>
    
    
    
    
if __name__ == "__main__":
    DUT = SMI_SmartHealthLog(sys.argv ) 
    DUT.RunScript()
    
    
    
    
    
    
