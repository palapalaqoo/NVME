#!/usr/bin/env python
# -*- coding: utf-8 -*-
from lib_vct import NVME
from lib_vct import NVMECom
import sys
from time import sleep
import threading
import re
import random
import time
from unittest.result import TestResult
print "SMI_FeatureHCTM.py"
print "Author: Sam Chan"
print "Ver: 20181203"
print ""



mNVME = NVME.NVME(sys.argv )

## paramter #####################################
ret_code = 0

## function #####################################
def GetPS():
    return int(mNVME.get_feature(2)[-1:])

def GetTMT1_TMT1():
    buf = mNVME.get_feature(0x10)
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

def SetTMT1_TMT2(TMT1, TMT2):
    
    TMT=(TMT1<<16)+(TMT2)
    # set feature
    return mNVME.set_feature(0x10, TMT)   
def CheckisINVALID_FIELD(strin):
    global  ret_code
    mStr = "INVALID_FIELD"
    if re.search(mStr, strin):
        mNVME.Print("Pass", "p")
    else:
        mNVME.Print("Fail", "f")
        ret_code = 1

def ResetHCTM():
    print ""
    print "Set TMT1=MXTMT-1, TMT2=MXTMT to exit the HCTM status if the HCTM is acting "
    mTMT1=MXTMT-1
    mTMT2=MXTMT
    print "Set TMT1= %s, TMT2= %s"%(mNVME.KelvinToC(mTMT1), mNVME.KelvinToC(mTMT2))
    SetTMT1_TMT2(mTMT1, mTMT2)
    sleep(1)
       
def CheckisSuccess(strin):
    global  ret_code
    mStr = "INVALID_FIELD"
    if not re.search(mStr, strin):
        mNVME.Print("Pass", "p")
    else:
        mNVME.Print("Fail", "f")
        ret_code = 1       

def RaisingTempture(TargetTemp, TimeOut):
# TimeOut = time limit in secend
# TargetTemp =temp in Kelvin degree
# Return last tempture read from controller
    TimeCnt=0
    aa=time.time()
    TempNow=0
    while True:                     
        # writing
        mThreads=mNVME.nvme_write_multi_thread(thread=4, sbk=0, bkperthr=512, value=0x5A)
        for process in mThreads:   
            process.join()
        
        TimeCnt= int(time.time()-aa) 
        PS = GetPS()    
        TempNow = mNVME.GetLog.SMART.CompositeTemperature
        mSuffix="Temperature: %s C, Power State: %s"%(mNVME.KelvinToC(TempNow), PS)
        
        # progressbar
        if TimeCnt<TimeOut:
            mNVME.PrintProgressBar(TimeCnt, TimeOut, prefix = 'Time Usage:', suffix = mSuffix, length = 50)
        else:
            mNVME.PrintProgressBar(TimeOut, TimeOut, prefix = 'Time Usage:', suffix = mSuffix, length = 50)
            print "After %s s, time out !,  stop to increase temperature !"%TimeOut
            break
                
        if TempNow>=TargetTemp: 
            print ""
            print "After %s s, temperature is large then target temperature now, stop to increase temperature !"%TimeCnt
            break

    return TempNow

## end function #####################################

HCTMA = mNVME.IdCtrl.HCTMA.int
MNTMT = mNVME.IdCtrl.MNTMT.int
MXTMT = mNVME.IdCtrl.MXTMT.int
TMT1bk, TMT2bk = GetTMT1_TMT1()
print "TMT1: %s = %s °C"%(TMT1bk,mNVME.KelvinToC(TMT1bk))
print "TMT2: %s = %s °C"%(TMT2bk,mNVME.KelvinToC(TMT2bk))

print ""
print "-- NVME Host Controlled Thermal Management(Feature Identifier 10h) test" 
print "-----------------------------------------------------------------------------------"

print ""
print "Check if controll support host controlled thermal management or not"
if HCTMA==1:
    mNVME.Print("Supported", "p")
    print "Minimum Thermal Management Temperature(MNTMT): %s"%mNVME.KelvinToC(MNTMT)
    print "Maximum Thermal Management Temperature(MXTMT): %s"%mNVME.KelvinToC(MXTMT)
    
else:
    mNVME.Print("Not supported", "p")
    print "quit all the test items!"
    ret_code=0 
    print "ret_code:%s"%ret_code
    print "Finish"
    sys.exit(ret_code)  
    
    

print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Test if controller accept TMT1 and TMT2 value is zero or not, expected result: Accept"
mTMT1=0
mTMT2=0
print "Set TMT1= %s, TMT2= %s"%(mTMT1, mTMT2)
mStr =  SetTMT1_TMT2(mTMT1, mTMT2)
CheckisSuccess(mStr)


print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Test if set TMT1 < MNTMT, then the command shall fail with a status code of Invalid Field in Command "
mTMT1=MNTMT-1
mTMT2=MXTMT
print "Set TMT1= %s, TMT2= %s"%(mTMT1, mTMT2)
mStr =  SetTMT1_TMT2(mTMT1, mTMT2)
CheckisINVALID_FIELD(mStr)

print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Test if set TMT1 > MXTMT, then the command shall fail with a status code of Invalid Field in Command "
mTMT1=MXTMT+1
mTMT2=MXTMT
print "Set TMT1= %s, TMT2= %s"%(mTMT1, mTMT2)
mStr =  SetTMT1_TMT2(mTMT1, mTMT2)
CheckisINVALID_FIELD(mStr)

print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Test if set TMT1 >= TMT2, then the command shall fail with a status code of Invalid Field in Command "
mTMT1=MNTMT
mTMT2=MNTMT
print "Set TMT1= %s, TMT2= %s"%(mTMT1, mTMT2)
mStr =  SetTMT1_TMT2(mTMT1, mTMT2)
CheckisINVALID_FIELD(mStr)
print ""
mTMT1=MNTMT+1
mTMT2=MNTMT
print "Set TMT1= %s, TMT2= %s"%(mTMT1, mTMT2)
mStr =  SetTMT1_TMT2(mTMT1, mTMT2)
CheckisINVALID_FIELD(mStr)

print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Test if set TMT2 < MNTMT, then the command shall fail with a status code of Invalid Field in Command "
mTMT1=MNTMT
mTMT2=MNTMT-1
print "Set TMT1= %s, TMT2= %s"%(mTMT1, mTMT2)
mStr =  SetTMT1_TMT2(mTMT1, mTMT2)
CheckisINVALID_FIELD(mStr)

print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Test if set TMT2 > MXTMT, then the command shall fail with a status code of Invalid Field in Command "
mTMT1=MNTMT
mTMT2=MXTMT+1
print "Set TMT1= %s, TMT2= %s"%(mTMT1, mTMT2)
mStr =  SetTMT1_TMT2(mTMT1, mTMT2)
CheckisINVALID_FIELD(mStr)

print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Test if set TMT2 <= TMT1, then the command shall fail with a status code of Invalid Field in Command "
mTMT1=MNTMT
mTMT2=MNTMT
print "Set TMT1= %s, TMT2= %s"%(mTMT1, mTMT2)
mStr =  SetTMT1_TMT2(mTMT1, mTMT2)
CheckisINVALID_FIELD(mStr)
print ""
mTMT1=MNTMT+1
mTMT2=MNTMT
print "Set TMT1= %s, TMT2= %s"%(mTMT1, mTMT2)
mStr =  SetTMT1_TMT2(mTMT1, mTMT2)
CheckisINVALID_FIELD(mStr)

print ""
print "Reset TMT value"
SetTMT1_TMT2(TMT1bk, TMT2bk)
print ""

print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Test HCTM functionality"
print ""
mNVME.Print("Warning! If the Composite Temperature is above 35 °C now, it may fail this test  ", "w")
mNVME.Print("Please cool down the controller and try it later, expected temperature < 35 °C", "w")
print ""
print "NVMe reset controller to reset HCTM function"
mNVME.nvme_reset()
print ""
TMT1bk, TMT2bk = GetTMT1_TMT1()
print "TMT1: %s = %s °C"%(TMT1bk,mNVME.KelvinToC(TMT1bk))
print "TMT2: %s = %s °C"%(TMT2bk,mNVME.KelvinToC(TMT2bk))
print ""
print "Check if controller is not performing HCTM function"
print "i.e.Thermal Management T1 Total Time and Thermal Management T2 Total Time is not counting"
TTTMT1 = mNVME.GetLog.SMART.TotalTimeForThermalManagementTemperature1
TTTMT2 = mNVME.GetLog.SMART.TotalTimeForThermalManagementTemperature2

print ""
print "TTTMT1: %s"%TTTMT1
print "TTTMT2: %s"%TTTMT2
print ""
print "Sleep 2 s"
sleep(2)
TTTMT1_n = mNVME.GetLog.SMART.TotalTimeForThermalManagementTemperature1
TTTMT2_n = mNVME.GetLog.SMART.TotalTimeForThermalManagementTemperature2
print ""
print "TTTMT1: %s"%TTTMT1_n
print "TTTMT2: %s"%TTTMT2_n

if TTTMT1!=TTTMT1_n or TTTMT2!=TTTMT2_n:
    mNVME.Print("Fail, can't reset HCTM function, quit this test item", "f")
    ret_code=1
else:
    print "Controller is not performing HCTM function now"
    LiveT = mNVME.GetLog.SMART.CompositeTemperature
    
    print "Minimum Thermal Management Temperature(MNTMT): %s °C"%mNVME.KelvinToC(MNTMT)
    print "Maximum Thermal Management Temperature(MXTMT): %s °C"%mNVME.KelvinToC(MXTMT)
    print "CompositeTemperature now: %s °C"%mNVME.KelvinToC(LiveT)
    
    
    
    # get value from smart log 
    TMT1TC = mNVME.GetLog.SMART.ThermalManagementTemperature1TransitionCount
    TMT2TC = mNVME.GetLog.SMART.ThermalManagementTemperature2TransitionCount
    TTTMT1 = mNVME.GetLog.SMART.TotalTimeForThermalManagementTemperature1
    TTTMT2 = mNVME.GetLog.SMART.TotalTimeForThermalManagementTemperature2
    
    
    # TMT min number must large then MNTMT
    if LiveT<MNTMT:
        BaseT=MNTMT
    else:
        BaseT=LiveT
    
    print ""
    mTMT1=BaseT+1
    mTMT2=BaseT+2
    print "Set TMT1= %s °C, TMT2= %s °C"%(mNVME.KelvinToC(mTMT1), mNVME.KelvinToC(mTMT2))
    SetTMT1_TMT2(mTMT1, mTMT2)
    
    TargetTemp = mTMT2 + 1
    TimeLimit = 180
    print "Writing data to increase temperature to make it large then TMT2(Let's set target temperature = %s °C)"%mNVME.KelvinToC(TargetTemp)
    print "Time limit is %s s "%TimeLimit
    LiveT_n = RaisingTempture(TargetTemp, TimeLimit)
    
    # get value from smart log 
    TMT1TC_n = mNVME.GetLog.SMART.ThermalManagementTemperature1TransitionCount
    TMT2TC_n = mNVME.GetLog.SMART.ThermalManagementTemperature2TransitionCount
    TTTMT1_n = mNVME.GetLog.SMART.TotalTimeForThermalManagementTemperature1
    TTTMT2_n = mNVME.GetLog.SMART.TotalTimeForThermalManagementTemperature2
    
    print ""
    print "-- befor test --"
    print "Composite Temperature: %s °C"%mNVME.KelvinToC(LiveT)
    print "TMT1TC: %s"%TMT1TC
    print "TMT2TC: %s"%TMT2TC
    print "TTTMT1: %s"%TTTMT1
    print "TTTMT2: %s"%TTTMT2
    print "-- after test --"
    print "Composite Temperature: %s °C"%mNVME.KelvinToC(LiveT_n)
    print "TMT1TC: %s"%TMT1TC_n
    print "TMT2TC: %s"%TMT2TC_n
    print "TTTMT1: %s"%TTTMT1_n
    print "TTTMT2: %s"%TTTMT2_n
    
    print ""
    if LiveT_n>=mTMT1:
        print "HCTM enter light throttle status, Composite Temperature > TMT1"
        print "Check if after the test, TMT1TC += 1"
        if TMT1TC_n==TMT1TC+1:
            mNVME.Print("Pass", "p")
        else:
            mNVME.Print("Fail", "f")
            ret_code = 1
        print "Check if after the test, TTTMT1 changed"
        if TTTMT1_n!=TTTMT1:
            mNVME.Print("Pass", "p")
        else:
            mNVME.Print("Fail", "f")   
            ret_code = 1
    else:
        mNVME.Print("Warning! The temperature has never great then TMT1 in %s s"%TimeLimit, "w")
    
    print ""
    if LiveT_n>=mTMT2:
        print "HCTM enter heavy throttle ststus, Composite Temperature > TMT2"
        print "Check if after the test, TMT2TC += 1"
        if TMT2TC_n==TMT2TC+1:
            mNVME.Print("Pass", "p")
        else:
            mNVME.Print("Fail", "f")
            ret_code = 1
        print "Check if after the test, TTTMT2 changed"
        if TTTMT2_n!=TTTMT2:
            mNVME.Print("Pass", "p")
        else:
            mNVME.Print("Fail", "f")   
            ret_code = 1
    else:
        mNVME.Print("Warning! The temperature has never great then TMT2 in %s s"%TimeLimit, "w")    
        
    print ""   
    print "Check if after the test, Composite Temperature has been changed or not"
    if LiveT_n!=LiveT:
        mNVME.Print("Pass", "p")
    else:
        mNVME.Print("Warning! never changed", "w")   
    




print ""
print "Reset TMT value"
SetTMT1_TMT2(TMT1bk, TMT2bk)
print ""


print ""
print "NVMe reset controller"
mNVME.nvme_reset()

print ""    
print "ret_code:%s"%ret_code
print "Finish"
sys.exit(ret_code)   



