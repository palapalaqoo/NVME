#!/usr/bin/env python
# -*- coding: utf-8 -*-

        #=======================================================================
        # abstract  function
        #     PreTest()                                                           :Override it for pretest, ex. check if controll support features, etc.
        #                                                                                :return true or false
        #     SubCase1() to SubCase32()                            :Override it for sub case 1 to sub case32
        #                                                                                :return 0=pass, 1=fals, 255=skip/notSupport
        # abstract  variables
        #     SubCase1Desc to SubCase32Desc                 :Override it for sub case 1 description to sub case32 description
        #     SubCase1KeyWord to SubCase32KeyWord   :Override it for sub case 1 keyWord to sub case32 keyWord
        #     SubCase1TimeOut to SubCase32TimeOut     :Override it for sub case 1 TimeOut to sub case32 TimeOut        
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

class SMI_FeatureHCTM(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_FeatureHCTM.py"
    Author = "Sam Chan"
    Version = "2021026"
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    SubCase1TimeOut = 60
    SubCase1Desc = "Test if controller accept TMT1 and TMT2 value is zero or not"    
    
    SubCase2TimeOut = 60
    SubCase2Desc = "Test set TMT1 < MNTMT"

    SubCase3TimeOut = 60
    SubCase3Desc = "Test set TMT1 > MXTMT"    

    SubCase4TimeOut = 60
    SubCase4Desc = "Test set TMT1 >= TMT2"    

    SubCase5TimeOut = 60
    SubCase5Desc = "Test set TMT2 < MNTMT"    

    SubCase6TimeOut = 60
    SubCase6Desc = "Test set TMT2 > MXTMT"    

    SubCase7TimeOut = 600
    SubCase7Desc = "Test HCTM functionality"    
    
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
        ret_code=0
        mStr = "INVALID_FIELD"
        if re.search(mStr, strin):
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            ret_code = 1
        return ret_code
    
    def ClearHCTMFunc(self):
        self.Print ("")
        self.Print ("Set TMT1=MXTMT-1, TMT2=MXTMT to exit the HCTM status if the HCTM is acting ")
        mTMT1=self.MXTMT-1
        mTMT2=self.MXTMT
        self.Print ("Set TMT1= %s, TMT2= %s"%(self.KelvinToC(mTMT1), self.KelvinToC(mTMT2)))
        self.SetTMT1_TMT2(mTMT1, mTMT2)
        sleep(1)
        self.Print ("")
        self.Print ("NVMe reset controller")
        self.nvme_reset()    
           
    def CheckisSuccess(self, strin):
        ret_code=0
        mStr = "INVALID_FIELD"
        if not re.search(mStr, strin):
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            ret_code = 1       
        return ret_code
    
    def ResetHCTM(self):
            self.Print ("")     
            self.Print ("== reset HCTM ==")  
            self.Print ("Disable HCTM by setting TMT1 and TMT2 to 0")
            self.SetTMT1_TMT2(0, 0)
            sleep(1)
            self.Print ("Reset TMT to previous  value")
            self.SetTMT1_TMT2(self.TMT1bk, self.TMT2bk)
            cTMT1, cTMT2 = self.GetTMT1_TMT1()
            self.Print ("Current TMT1, TMT2 value is : %s, %s "%(cTMT1, cTMT2))       
            if cTMT1==self.TMT1bk and cTMT2==self.TMT2bk:
                self.Print("Done", "p")
            else:
                self.Print("Fail", "f")
                #return False    

            self.Print ("")
            self.Print ("NVMe reset controller")
            self.nvme_reset()  
            self.Print ("Done")  
            self.Print ("== end of reset HCTM ==")       
    
    def TestValueClearToZero(self, TMT1, TMT2):
        mTMT1=TMT1
        mTMT2=TMT2
        self.Print("")
        self.Print ("Set TMT1= %s, TMT2= %s"%(mTMT1, mTMT2))
        mStr =  self.SetTMT1_TMT2(mTMT1, mTMT2)        
        # if Accept cmd, then verify value, else return 1
        if self.CheckisSuccess(mStr)==1:
            return False
        
        self.Print ("Verify current value by get feature command")
        cTMT1, cTMT2 = self.GetTMT1_TMT1()
        self.Print ("Current TMT1, TMT2 value is : %s, %s "%(cTMT1, cTMT2))
        if cTMT1==TMT1 and cTMT2==TMT2:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            return False     
        return True   
        
    
    
    def RaisingTempture(self, TargetTemp, TimeOut):
    # TimeOut = time limit in secend
    # TargetTemp =temp in Kelvin degree
    # Return last tempture read from controller
        TimeCnt=0
        aa=time.time()
        TempNow=0
        # using DevWakeUpAllTheTime
        Inst = DevWakeUpAllTheTime(self, False)
        Inst.Start() # thread start to read all the time
        while True:                     
            sleep(1)            
            TimeCnt= int(time.time()-aa) 
            PS = self.GetPS()    
            TempNow = self.GetLog.SMART.CompositeTemperature
            mSuffix="Temperature: %s C, Power State: %s"%(self.KelvinToC(TempNow), PS)
            
            # progressbar
            if TimeCnt<TimeOut:
                self.PrintProgressBar(TimeCnt, TimeOut, prefix = 'Time Usage:', suffix = mSuffix, length = 50)
            else:
                self.PrintProgressBar(TimeOut, TimeOut, prefix = 'Time Usage:', suffix = mSuffix, length = 50)
                self.Print ("After %s s, time out !,  stop to increase temperature !"%TimeOut)
                break
                    
            if TempNow>=TargetTemp: 
                self.Print ("")
                self.Print ("After %s s, temperature is large then target temperature now!"%TimeCnt)
                self.Print ("wait 3 more second and stop to increase temperature")              
                sleep(3) 
                break
        Inst.Stop()
        return TempNow

    def PrintAlignString(self,S0="", S1="", S2="", S3="", PF="default"):            
        mStr = "{:<60}\t{:<10}\t{:<10}\t{:<10}".format(S0, S1, S2, S3)
        if PF=="pass":
            self.Print( mStr , "p")        
        elif PF=="fail":
            self.Print( mStr , "f")      
        else:
            self.Print( mStr ) 
        
        # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def __init__(self, argv):
        # initial parent class
        super(SMI_FeatureHCTM, self).__init__(argv)
        
        # <Parameter>
        self.HCTMA = self.IdCtrl.HCTMA.int
        self.MNTMT = self.IdCtrl.MNTMT.int
        self.MXTMT = self.IdCtrl.MXTMT.int
        self.TMT1bk, self.TMT2bk = self.GetTMT1_TMT1()      
        # </Parameter>
        

        
    # override PreTest()
    def PreTest(self):
        if self.HCTMA==1:
            self.Print( "Controller support HCTM", "p")
            self.Print ("Current TMT1, TMT2 value is : %s(%s °C), %s(%s °C) "\
                        %(self.TMT1bk, self.KelvinToC(self.TMT1bk), self.TMT2bk, self.KelvinToC(self.TMT2bk)))  
            self.Print ("Minimum Thermal Management Temperature(MNTMT): %s(%s °C) "%(self.MNTMT, self.KelvinToC(self.MNTMT)) )
            self.Print ("Maximum Thermal Management Temperature(MXTMT): %s(%s °C) "%(self.MXTMT, self.KelvinToC(self.MXTMT)) )                      
            return True
        else:
            self.Print( "Controller do not support HCTM", "w")
            return False
        
    # <override sub item scripts>        
    def SubCase1(self):  
        rtCode = 0
        self.Print ("Test if controller accept TMT1 and TMT2 value is zero or not, expected result: Accept")
        self.Print ("Keyword: A value cleared to zero, specifies that this part of the feature shall be disabled.")
        # all=0
        if self.TMT2bk>self.MXTMT:
            self.Print ("Warnning!, current TMT2>MXTMT", "w")  
            rtCode = 255
        if self.TMT1bk<self.MNTMT and self.TMT1bk!=0:
            self.Print ("Warnning!, current TMT1<MNTMT", "w")
            rtCode = 255
                    
        if self.TestValueClearToZero(TMT1=0, TMT2=0)==False:
            return 1
        # TMT1=0          
        if self.TestValueClearToZero(TMT1=0, TMT2=self.MXTMT)==False:
            return 1          
        # TMT2=0
        if self.TestValueClearToZero(TMT1=self.MNTMT, TMT2=0)==False:
            return 1       
              
        return rtCode

    
    def SubCase2(self):
        self.Print ("Test if set TMT1 < MNTMT, then the command shall fail with a status code of Invalid Field in Command "      )

        mTMT1=self.MNTMT-1
        mTMT2=self.MXTMT
        self.Print ("Set TMT1= %s, TMT2= %s"%(mTMT1, mTMT2))
        mStr =  self.SetTMT1_TMT2(mTMT1, mTMT2)
        return self.CheckisINVALID_FIELD(mStr)            

    def SubCase3(self):
        self.Print ("Test if set TMT1 > MXTMT, then the command shall fail with a status code of Invalid Field in Command "     )
        
        mTMT1=self.MXTMT+1
        mTMT2=self.MXTMT
        self.Print ("Set TMT1= %s, TMT2= %s"%(mTMT1, mTMT2))
        mStr =  self.SetTMT1_TMT2(mTMT1, mTMT2)
        return self.CheckisINVALID_FIELD(mStr)     

        
    def SubCase4(self):
        self.Print ("Test if set TMT1 >= TMT2, then the command shall fail with a status code of Invalid Field in Command "        )
        mTMT1=self.MNTMT
        mTMT2=self.MNTMT
        self.Print ("Set TMT1= %s, TMT2= %s"%(mTMT1, mTMT2))
        mStr =  self.SetTMT1_TMT2(mTMT1, mTMT2)
        code1=self.CheckisINVALID_FIELD(mStr)
        self.Print ("")
        mTMT1=self.MNTMT+1
        mTMT2=self.MNTMT
        self.Print ("Set TMT1= %s, TMT2= %s"%(mTMT1, mTMT2))
        mStr =  self.SetTMT1_TMT2(mTMT1, mTMT2)
        code2=self.CheckisINVALID_FIELD(mStr)
        
        if code1==1 or code2==1:
            return 1
        else:
            return 0
          
        
    def SubCase5(self):
        self.Print ("Test if set TMT2 < MNTMT, then the command shall fail with a status code of Invalid Field in Command "          )
        mTMT1=self.MNTMT
        mTMT2=self.MNTMT-1
        self.Print ("Set TMT1= %s, TMT2= %s"%(mTMT1, mTMT2))
        mStr =  self.SetTMT1_TMT2(mTMT1, mTMT2)
        return self.CheckisINVALID_FIELD(mStr)     
      

    def SubCase6(self):
        self.Print ("Test if set TMT2 > MXTMT, then the command shall fail with a status code of Invalid Field in Command ")
        
        mTMT1=self.MNTMT
        mTMT2=self.MXTMT+1
        self.Print ("Set TMT1= %s, TMT2= %s"%(mTMT1, mTMT2))
        mStr =  self.SetTMT1_TMT2(mTMT1, mTMT2)
        return self.CheckisINVALID_FIELD(mStr)    
       
        
        self.Print ("")
        self.Print ("Reset TMT value")
        self.SetTMT1_TMT2(self.TMT1bk, self.TMT2bk)       
        

    def SubCase7(self):
        self.Print ("Test HCTM functionality")
        ret_code=0    
        self.Print ("")
        self.Print("Warning! If the Composite Temperature is above 35 °C now, it may fail this test  ", "w")
        self.Print("Please cool down the controller and try it later, expected temperature < 35 °C", "w")
        self.Print ("")
        
        LiveT = self.GetLog.SMART.CompositeTemperature
        self.Print ("CompositeTemperature now: %s °C"%self.KelvinToC(LiveT))        
        
        
        self.Print ("1) Reset HCTM function", "b")
        self.SetPrintOffset(4, "add")
        self.ClearHCTMFunc()
        self.Print ("")
        TMT1bk, TMT2bk = self.GetTMT1_TMT1()
        self.Print ("TMT1: %s = %s °C"%(TMT1bk,self.KelvinToC(TMT1bk)))
        self.Print ("TMT2: %s = %s °C"%(TMT2bk,self.KelvinToC(TMT2bk)))
        self.Print ("")
        self.Print ("Check if controller is not performing HCTM function")
        self.Print ("i.e.Thermal Management T1 Total Time and Thermal Management T2 Total Time is not counting")
        TTTMT1 = self.GetLog.SMART.TotalTimeForThermalManagementTemperature1
        TTTMT2 = self.GetLog.SMART.TotalTimeForThermalManagementTemperature2
        
        self.Print ("")
        self.Print ("Total Time For Thermal Management Temperature 1: %s"%TTTMT1)
        self.Print ("Total Time For Thermal Management Temperature 2: %s"%TTTMT2)
        self.Print ("")
        self.Print ("Sleep 2 s")
        sleep(2)
        TTTMT1_n = self.GetLog.SMART.TotalTimeForThermalManagementTemperature1
        TTTMT2_n = self.GetLog.SMART.TotalTimeForThermalManagementTemperature2
        self.Print ("")
        self.Print ("Total Time For Thermal Management Temperature 1: %s"%TTTMT1_n)
        self.Print ("Total Time For Thermal Management Temperature 2: %s"%TTTMT2_n)
        
        if TTTMT1!=TTTMT1_n or TTTMT2!=TTTMT2_n:
            self.Print("Fail, can't reset HCTM function, quit this test item", "f")
            ret_code=1
            return 1
        else:
            self.Print ("Controller is not performing HCTM function now")
            self.Print ("")
            self.SetPrintOffset(-4, "add")
            self.Print ("2) Raise temperature to make it large then TMT2", "b")
            self.SetPrintOffset(4, "add")            
            
            LiveT = self.GetLog.SMART.CompositeTemperature
            self.Print ("")
            self.Print ("Minimum Thermal Management Temperature(MNTMT): %s °C"%self.KelvinToC(self.MNTMT))
            self.Print ("Maximum Thermal Management Temperature(MXTMT): %s °C"%self.KelvinToC(self.MXTMT))
            self.Print ("CompositeTemperature now: %s °C"%self.KelvinToC(LiveT))
            
            
            
            # get value from smart log 
            TMT1TC = self.GetLog.SMART.ThermalManagementTemperature1TransitionCount
            TMT2TC = self.GetLog.SMART.ThermalManagementTemperature2TransitionCount
            TTTMT1 = self.GetLog.SMART.TotalTimeForThermalManagementTemperature1
            TTTMT2 = self.GetLog.SMART.TotalTimeForThermalManagementTemperature2
            
            # TMT min number must large then MNTMT
            if LiveT<self.MNTMT:
                BaseT=self.MNTMT
            else:
                BaseT=LiveT
            
            self.Print ("")
            mTMT1=BaseT+1
            mTMT2=BaseT+2
            self.Print ("Set TMT1= %s °C, TMT2= %s °C"%(self.KelvinToC(mTMT1), self.KelvinToC(mTMT2)))
            self.SetTMT1_TMT2(mTMT1, mTMT2)
            
            TargetTemp = mTMT2 + 1
            TimeLimit = 5
            self.Print ("Reading data to raise temperature and make it large then TMT2(Let's set target temperature = %s °C)"%self.KelvinToC(TargetTemp))
            self.Print ("Time limit is %s s "%TimeLimit)
            LiveT_n = self.RaisingTempture(TargetTemp, TimeLimit)
            
            # get value from smart log 
            TMT1TC_n = self.GetLog.SMART.ThermalManagementTemperature1TransitionCount
            TMT2TC_n = self.GetLog.SMART.ThermalManagementTemperature2TransitionCount
            TTTMT1_n = self.GetLog.SMART.TotalTimeForThermalManagementTemperature1
            TTTMT2_n = self.GetLog.SMART.TotalTimeForThermalManagementTemperature2
            
            self.Print ("")
            self.PrintAlignString("field in SMART", "original value", "current value")
            self.Print ("--------------------------------------------------------------------------------")
            self.PrintAlignString("Composite Temperature", self.KelvinToC(LiveT), self.KelvinToC(LiveT_n))
            self.PrintAlignString("Thermal Management Temperature 1 Transition Count", TMT1TC, TMT1TC_n)
            self.PrintAlignString("Thermal Management Temperature 2 Transition Count", TMT2TC, TMT2TC_n)
            self.PrintAlignString("Total Time For Thermal Management Temperature 1", TTTMT1, TTTMT1_n)
            self.PrintAlignString("Total Time For Thermal Management Temperature 2", TTTMT2, TTTMT2_n)
            self.Print ("--------------------------------------------------------------------------------")
            self.Print ("")
            self.SetPrintOffset(-4, "add")
            self.Print ("3) If Current Temperature is large then TMT1, verify fields in SMART log relating to Temperature 1 ", "b")
            self.SetPrintOffset(4, "add")                
            self.Print ("")
            if LiveT_n>=mTMT1:
                self.Print ("Current Temperature(%s)>=TMT1(%s)"%(self.KelvinToC(LiveT_n), mTMT1))
                self.Print ("Expect HCTM enter light throttle status")
                self.Print ("Check if current 'Thermal Management Temperature 1 Transition Count' > original value")
                if TMT1TC_n>TMT1TC:
                    self.Print("Pass", "p")
                else:
                    self.Print("Fail", "f")
                    ret_code = 1
                self.Print ("Check if current 'Total Time For Thermal Management Temperature 1' >= original value")
                if TTTMT1_n>=TTTMT1:
                    self.Print("Pass", "p")
                else:
                    self.Print("Fail", "f")   
                    ret_code = 1
            else:
                self.Print("Warning! The temperature has never great then TMT1 in %s s"%TimeLimit, "w")
            
            self.Print ("")
            self.SetPrintOffset(-4, "add")
            self.Print ("4) If Current Temperature is large then TMT2, verify fields in SMART log relating to Temperature 2 ", "b")
            self.SetPrintOffset(4, "add")               
            if LiveT_n>=mTMT2:
                self.Print ("Current Temperature(%s)>=TMT2(%s)"%(self.KelvinToC(LiveT_n), mTMT2))
                self.Print ("Expect HCTM enter heavy throttle ststus")
                self.Print ("Check if current 'Thermal Management Temperature 2 Transition Count' > original value")
                if TMT2TC_n>TMT2TC:
                    self.Print("Pass", "p")
                else:
                    self.Print("Fail", "f")
                    ret_code = 1
                self.Print ("Check if current 'Total Time For Thermal Management Temperature 2' >= original value")
                if TTTMT2_n>=TTTMT2:
                    self.Print("Pass", "p")
                else:
                    self.Print("Fail", "f")   
                    ret_code = 1
            else:
                self.Print("Warning! The temperature has never great then TMT2 in %s s"%TimeLimit, "w")    
                
            self.Print ("")
            self.SetPrintOffset(-4, "add")
            self.Print ("5) Check if after the test, Composite Temperature has been changed or not", "b")
            self.SetPrintOffset(4, "add")   
            self.Print ("Current value: %s, original value: %s"%(self.KelvinToC(LiveT_n), self.KelvinToC(LiveT)))
            if LiveT_n!=LiveT:
                self.Print("Pass", "p")
            else:
                self.Print("Warning! never changed", "w")
        return ret_code       

    # override post test to reset values after test is finish
    def PostTest(self):
        self.ResetHCTM()
    


    # </sub item scripts> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    
    
    
if __name__ == "__main__":
    DUT = SMI_FeatureHCTM(sys.argv )
    DUT.RunScript()
    DUT.Finish() 
    
    
    
    
    
