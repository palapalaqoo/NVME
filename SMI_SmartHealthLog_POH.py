#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
from time import sleep
# Import VCT modules
from lib_vct.NVME import NVME
from lib_vct.NVME import DevWakeUpAllTheTime

class SMI_SmartHealthLog_POH(NVME):
    ScriptName = "SMI_SmartHealthLog_POH.py"
    Author = "Sam chan"
    Version = "20201105"
    
    
    def DoTest(self, ExpectPlusOne = False, OperationalPowerState = False, CheckTimerAccuracy = False):
        ret_code=0
        BusyMode=OperationalPowerState
        POH0=self.GetLog.SMART.PowerOnHours
        self.Print("ExpectPlusOne: %s"%("yes" if ExpectPlusOne else "no"))
        self.Print("OperationalPowerState: %s"%("yes" if OperationalPowerState else "no"))
        self.Print("CheckTimerAccuracy: %s"%("yes" if CheckTimerAccuracy else "no"))
        
        self.Print("")
        self.Print("Get current 'Power On Hours': %s"%POH0)
        
        self.Print("")
        self.timer.start()
        if BusyMode:
            self.Print("Start to issue nvme read command to keep controller in the operational power state")        
            DWUATT=DevWakeUpAllTheTime(nvme = self, RecordCmdToLogFile=False)
            DWUATT.Start()  
        POH=0
        timeout = 3720 #3720
        timeoutOcc=False
        self.Print("Start to keep watching on  'Power On Hours', time out:%s seconds"%timeout)
        timeUsage=0
        # PrintProgressBar
        self.PrintProgressBar(timeUsage, timeout, prefix = 'Time:', length = 50)
        try: 
            while True:
                sleep(1)                  
                POH=self.GetLog.SMART.PowerOnHours
                #  no change
                if POH==POH0:
                    pass
                else:
                    break
                # time out 
                timeUsage = int(round(float(self.timer.time)))
                if timeUsage >=timeout:
                    timeoutOcc=True
                    break
                # progress bar
                if timeUsage%30==0:
                    self.PrintProgressBar(timeUsage, timeout, prefix = 'Time:', length = 50)
                
        except KeyboardInterrupt:
            self.Print("")
            self.Print("Detect ctrl+C, quit")  
            if BusyMode:
                DWUATT.Stop()          
            self.timer.stop()   
            return 255   
        
        self.Print("")           
        # stop timer    
        self.timer.stop()
        # stop write
        if BusyMode:
            DWUATT.Stop()
        
        self.Print("")
        self.Print("Current 'Power On Hours' : %s"%POH)
        self.Print("Time usage: %s second"%timeUsage)  
        self.Print("")
        
        # -------------------------------------------------
        if timeoutOcc:
        # time out            
            self.Print("Time is up")
            if ExpectPlusOne:            
                self.Print("Fail!, 'Power On Hours' never changed, expect +1", "f")
                ret_code = 1
            else:
                self.Print("Pass!, 'Power On Hours' never changed, expect not changed", "p")          
        elif POH==(POH0+1):
        # value==value+1            
            if not ExpectPlusOne:
                self.Print("Fail!, 'Power On Hours' changed, expect not changed", "f")
                ret_code = 1
            else:                
                self.Print("Pass!, 'Power On Hours' +1", "p")
                self.Print("Last value: %s, expect value: %s, current value: %s"%(POH0, POH0+1, POH), "p")            
                self.Print("")
                if CheckTimerAccuracy:
                    toleranceTime = timeout - 3600   
                    MinTime = 3600-toleranceTime                
                    self.Print("Check Timer Accuracy, Tolerance Time: %s seconds(timeout - 3600)"%toleranceTime) 
                    self.Print("Minimum time: %s(3600 - Tolerance Time)"%MinTime)
                    self.Print("Maximum time: %s(time out)"%timeout)               
    
                    self.Print("Check if 'Minimum time' <  Time usage < 'Maximum time'")
                    if(MinTime < timeUsage): # ex. timeUsage= 3500, toleranceTime=40s(minimum time=3560), then fail
                        self.Print("Pass!", "p")
                    else:
                        self.Print("Fail!", "f")
                        ret_code = 1                     
        else:
        # fail, value!=value+1            
            self.Print("Fail!, 'Power On Hours' changed incorrectly", "f")
            self.Print("Last value: %s, current value: %s"%(POH0, POH), "f")
            ret_code = 1            
        # -------------------------------------------------
            
        return ret_code      
    
    
    def __init__(self, argv):
        # initial new parser if need, -t -d -s -p was used, dont use it again
        self.SetDynamicArgs(optionName="k", optionNameFull="Keep_Power_On_Hours", helpMsg="set '-k=1' to expect the 'Power On Hours' to be reatined(no change) in case3", argType=int)   
              
        # initial parent class
        super(SMI_SmartHealthLog_POH, self).__init__(argv)
        
        # get new parser if need, where args order is the same with initial order
        # config_numvfs = int or None
        self.IncreaseExpected = self.GetDynamicArgs(0)
        self.IncreaseExpected = False if self.IncreaseExpected==1 else True


    # define pretest  
    def PreTest(self):        
        return True            

    # <define sub item scripts>

    SubCase1TimeOut = 7200
    SubCase1Desc = "Test Power_On_Hours, ExpectPlusOne: yes, OperationalPowerState: yes, CheckTimerAccuracy: no"
    def SubCase1(self): 
        ret_code = self.DoTest(ExpectPlusOne = True, OperationalPowerState = True, CheckTimerAccuracy = False)          
        return ret_code  
    
    SubCase2TimeOut = 7200
    SubCase2Desc = "Test Power_On_Hours, ExpectPlusOne: yes, OperationalPowerState: yes, CheckTimerAccuracy: yes"
    def SubCase2(self): 
        ret_code = self.DoTest(ExpectPlusOne = True, OperationalPowerState = True, CheckTimerAccuracy = True)          
        return ret_code      
    
    SubCase3TimeOut = 7200
    SubCase3Desc = "Test Power_On_Hours, ExpectPlusOne: user define(default='yes'), OperationalPowerState: no, CheckTimerAccuracy: yes"
    def SubCase3(self): 
        ret_code = self.DoTest(ExpectPlusOne = self.IncreaseExpected, OperationalPowerState = False, CheckTimerAccuracy = True)          
        return ret_code          
    # </define sub item scripts>


    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_SmartHealthLog_POH(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    