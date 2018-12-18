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
import os.path
import subprocess
from tuned import admin


print "SMI_SetGetFeatureCMD.py"
print "Author: Sam Chan"
print "Ver: 20181203"
print ""
mNVME = NVME.NVME(sys.argv )

## paramter #####################################
ret_code = 0
sub_ret=0
CMD_Result="0"
SANACT=0
ErrorLog=[]
Ns=1
TestItems=[]
SELSupport = True if mNVME.IdCtrl.ONCS.bit(4)=="1" else False
NsSupported=True if mNVME.IdCtrl.OACS.bit(3)=="1" else False
## function #####################################
class item:
    description=0
    fid=1
    capabilities=2
    reset_value=3
    valid_value=4
    supported=5

def initial():
    # [description, id, capabilities, reset_value, valid_value, supported]
    global TestItems
    
    description = "Arbitration"
    fid = 1
    supported = True
    capabilities=GetFeatureSupportedCapabilities(fid)
    reset_value=GetFeature(fid = fid)
    valid_value=reset_value+(1<<24)
    TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])
    
    description = "Power Management"
    fid = 2
    supported = True if mNVME.IdCtrl.NPSS.int!=0 else False
    capabilities=GetFeatureSupportedCapabilities(fid)
    reset_value=GetFeature(fid = fid)
    valid_value=0 if reset_value!=0 else 1
    TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])
    
    description = "LBA Range Type"
    fid = 3
    supported = True
    capabilities=GetFeatureSupportedCapabilities(fid)
    reset_value=GetFeature(fid = fid)
    valid_value=0 if reset_value!=0 else 1
    TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])
    
    description = "Temperature Threshold"
    fid = 4
    supported = True
    capabilities=GetFeatureSupportedCapabilities(fid)
    reset_value=GetFeature(fid = fid)
    valid_value=reset_value+1
    TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])    
    
    description = "Error Recovery"
    fid = 5
    supported = True
    capabilities=GetFeatureSupportedCapabilities(fid)
    reset_value=GetFeature(fid = fid)
    valid_value=reset_value+1
    TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])        
    
    description = "Volatile Write Cache"
    fid = 6
    supported = True if mNVME.IdCtrl.VWC.bit(0) == "1" else False
    capabilities=GetFeatureSupportedCapabilities(fid)
    reset_value=GetFeature(fid = fid)
    valid_value=1 if reset_value==0 else 0
    TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])            
    '''    
    description = "Number of Queues"
    fid = 7
    supported = True
    capabilities=GetFeatureSupportedCapabilities(fid)
    reset_value=GetFeature(fid = fid)
    NCQR=mNVME.int2bytes(reset_value, 2)
    NSQR=mNVME.int2bytes(reset_value, 0)
    valid_value=((NCQR-1)<<16) + (NSQR-1)
    TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])           
    '''    
    
    description = "Interrupt Coalescing"
    fid = 8
    supported = True
    capabilities=GetFeatureSupportedCapabilities(fid)
    reset_value=GetFeature(fid = fid)
    valid_value=1 if reset_value==0 else 0
    TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])              
    
    description = "Interrupt Vector Configuration(Testing secend Interrupt Vector where cdw11=0x1)"
    fid = 9
    supported = True
    capabilities=GetFeatureSupportedCapabilities(fid)
    reset_value=GetFeature(fid = fid)
    CoalescingDisable=mNVME.int2bytes(reset_value, 4)
    if CoalescingDisable>=1:
        valid_value = reset_value & 0xFFFF
    else:
        valid_value = reset_value | (1<<16)
    TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])        
    
    description = "Write Atomicity Normal"
    fid = 0xA
    supported = True
    capabilities=GetFeatureSupportedCapabilities(fid)
    reset_value=GetFeature(fid = fid)
    valid_value=1 if reset_value==0 else 0
    TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])   
        
    description = "Asynchronous Event Configuration"
    fid = 0xB
    supported = True
    capabilities=GetFeatureSupportedCapabilities(fid)
    reset_value=GetFeature(fid = fid)
    valid_value=1 if reset_value==0 else 0
    TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])   
        
    description = "Autonomous Power State Transition"
    fid = 0xC
    supported = True if mNVME.IdCtrl.APSTA.bit(0) == "1" else False
    capabilities=GetFeatureSupportedCapabilities(fid)
    reset_value=GetFeature(fid = fid)
    valid_value=1 if reset_value==0 else 0
    TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])      
    
    description = "Host Memory Buffer"
    fid = 0xD
    supported = True if mNVME.IdCtrl.HMPRE.int != 0 else False
    capabilities=GetFeatureSupportedCapabilities(fid)
    reset_value=GetFeature(fid = fid)    
    if reset_value &0x1 >=1:
        valid_value = reset_value & 0b0010
    else:
        valid_value = reset_value | 0b0001    
    valid_value=1 if reset_value==0 else 0
    TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])  

    description = "Host Controlled Thermal Management"
    fid = 0x10
    supported = True if mNVME.IdCtrl.HCTMA.bit(0) == "1" else False
    capabilities=GetFeatureSupportedCapabilities(fid)
    reset_value=GetFeature(fid = fid)    
    # Note, MNTMT<= valid_value <=MXTMT
    MXTMT = mNVME.IdCtrl.MXTMT.int
    TMT1=MXTMT-1
    TMT2=MXTMT
    TMT=(TMT1<<16)+(TMT2)    
    if TMT==reset_value:
        TMT1=MXTMT-2
        TMT=(TMT1<<16)+(TMT2)
    valid_value=TMT     
    TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])      
    
    description = "Software Progress Marker"
    fid = 0x80
    supported = True
    capabilities=GetFeatureSupportedCapabilities(fid)
    reset_value=GetFeature(fid = fid)
    valid_value=1 if reset_value==0 else 0
    TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])          
    
    description = "Host Identifier"
    fid = 0x81
    supported = True if mNVME.IdCtrl.ONCS.bit(5) == "1" else False
    capabilities=GetFeatureSupportedCapabilities(fid)
    reset_value=GetFeature(fid = fid)
    valid_value=1 if reset_value==0 else 0
    TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])      
    
    description = "Reservation Notification Mask"
    fid = 0x82
    supported = True if mNVME.IdNs.RESCAP.int !=0 else False
    capabilities=GetFeatureSupportedCapabilities(fid)
    reset_value=GetFeature(fid = fid)
    valid_value=2 if reset_value==0 else 0
    TestItems.append([description, fid, capabilities, reset_value, valid_value, supported]) 
    
    description = "Reservation Persistance"
    fid = 0x83
    supported = True if mNVME.IdNs.RESCAP.int !=0 else False
    capabilities=GetFeatureSupportedCapabilities(fid)
    reset_value=GetFeature(fid = fid)
    valid_value=1 if reset_value==0 else 0
    TestItems.append([description, fid, capabilities, reset_value, valid_value, supported]) 
                
def CreateLBARangeDataStructure(NumOfEntrys):
    # create multi entry of LBARangeDataStructure
    # return string , ex "\\255\\12\\78\\ .."
    mStr=""
    for entry in range(NumOfEntrys):        
        mNVME.LBARangeDataStructure.Type=0x2
        mNVME.LBARangeDataStructure.Attributes=0x1
        mNVME.LBARangeDataStructure.SLBA=entry*8
        mNVME.LBARangeDataStructure.NLB=7
        mNVME.LBARangeDataStructure.CreatePattern()
        # save created string to mStr
        mStr = mStr + mNVME.LBARangeDataStructure.Pattern
        
    return mStr
        
def PrintSupportedFeature():
    for mItem in TestItems:
        print mItem[item.description]
            

def GetFeatureValue(fid, cdw11=0, sel=0, nsid=1, nsSpec=False):
    Value=0 
    buf = mNVME.get_feature(fid = fid, cdw11=cdw11, sel = sel, nsid = nsid, nsSpec=nsSpec) 
    mStr="0"
    if sel==0:
        mStr="Current value:(.+)"
    if sel==1:
        mStr="Default value:(.+)"
    if sel==2:
        mStr="Saved value:(.+)"
    if sel==3:
        mStr="capabilities value:(.+)"                
        
    if re.search(mStr, buf):
        Value=int(re.search(mStr, buf).group(1),16)
    else:
        Value= -1
    return Value


def GetFeatureSupportedCapabilities(fid):
    if SELSupport:
        return GetFeature(fid=fid, sel=3)
    else:
        return -1

def SetFeature(fid, value, sv, nsid=0):
    # if LBA range, create data structure for set feature command
    if fid==3:
        # Number of LBA Ranges is zero based, 0 means there is 1 LBA Range
        DS=CreateLBARangeDataStructure(value+1)
        mNVME.set_feature(fid = fid, value = value, SV = sv, nsid = nsid, Data=DS)
    else:
        mNVME.set_feature(fid = fid, value = value, SV = sv, nsid = nsid)

def GetFeature(fid, sel=0, nsid=1):
    # if Interrupt Vector Configuration, read with cdw11=1
    if fid==3:
        return GetFeatureValue(fid=fid, sel=sel, nsid=nsid, nsSpec=True)
    if fid==9:
        return GetFeatureValue(fid=fid, sel=sel, cdw11=1, nsid=nsid, nsSpec=False)
    else:
        return GetFeatureValue(fid=fid, sel=sel, nsid=nsid, nsSpec=False)
def DifferentValueFromCurrent(fid):
    currentValue = GetFeature(fid, sel=0)
    resetValue=0
    validValue=0
    for mItem in TestItems:
        if mItem[item.fid]==fid:            
            resetValue=mItem[item.reset_value]
            validValue=mItem[item.valid_value]
            break
            
    if currentValue != resetValue:
        return resetValue
    else:
        return validValue

def CheckResult(OriginValue, CurrentValue, ExpectMatch):
# if OriginValue = CurrentValue, and ExpectMatch = true,
# or OriginValue != CurrentValue, and ExpectMatch = false, then pass

    global ret_code
    print "Send get feature command, returned feature value: %s "%hex(CurrentValue)
    print "Check get feature value, expected value: %s , %s "%( hex(OriginValue) if ExpectMatch else hex(CurrentValue), "changed" if ExpectMatch else "not changed" )
    if CurrentValue == OriginValue and ExpectMatch == True:
        mNVME.Print("PASS", "p")  
    else:
        mNVME.Print("Fail", "f")
        ret_code=1          
    
## end function #####################################







print ""
print "-- NVME Get/Set Feature command test" 
print "-----------------------------------------------------------------------------------"

print "Nvme reset controller"
mNVME.nvme_reset()

# initial TestItems
initial()

mNVME.Print("Test item 'Timestamp' is in script SMI_FeatureTimestamp ", "w")
mNVME.Print("Test item 'Keep Alive Timer' has not implemented ", "w")
mNVME.Print("Test item 'Number of Queues' has not implemented ", "w")


print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Keyword: Get Features - Command Dword 10"
print "Check if Select field in Get Features - Command Dword 10 supported or not"
print ""
if SELSupport:
    mNVME.Print("Supported", "p")
else:
    mNVME.Print("Not Supported", "f")


if SELSupport:
    print ""
    print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
    print "Keyword: Get Features - Command Dword 10"
    print "Select field supported, test all the attributes in Select field"
    print "" 
    '''   
    print "Supported features:"
    print "------------------------------------------"
    PrintSupportedFeature()
    print "------------------------------------------"
    '''
    
    print ""  

    for mItem in TestItems:
        print "========================================="
        print mItem[item.description]   
        print "Feature ID: %s"%mItem[item.fid]   
        supported=mItem[item.supported]
        saveable=True if mItem[item.capabilities]&0b001 > 0 else False   
        nsSpec=True if mItem[item.capabilities]&0b010 > 0 else False
        changeable=True if mItem[item.capabilities]&0b100 > 0 else False
        if not supported:
            print "Not supported"      
            print ""  
        else:
            print "Supported"              
            print "" 
            print "Feature saveable: %s"%("Yes" if saveable else "No")
            print "Feature namespace specific: %s"%("Yes" if nsSpec else "No")
            print "Feature changeable: %s"%("Yes" if changeable else "No")
            print ""
            
            print "-(1)-- Test Get Features with Select=0, Current --"    
            print "        and test Features capabilities bit 2, Feature Identifier is changeable or not"
            print "        "+ "Feature is changeable, all the fallowing test should change the value" if changeable else "Feature is no changeable, all the fallowing test should not change the value"
            fid=mItem[item.fid]
            rdValue=GetFeature(fid, sel=0)
            value=DifferentValueFromCurrent(fid)
            print "Send get feature command, returned feature value: %s "%hex(rdValue)
            print "Send set feature command with value = %s"%hex(value)
            
            # Send set feature command    
            SetFeature(fid, value, sv=0,nsid=1) if nsSpec else SetFeature(fid, value, sv=0)
            
            # Send get feature command    
            GetValue = GetFeature(fid, sel=0)
            
            # check if (value is set if changeable=true) or  (value is not set if changeable=false) 
            CheckResult(OriginValue=value, CurrentValue=GetValue, ExpectMatch=changeable)    
            print ""

            print "-(2)--  Test Get Features with Select=1, Default --"  
            DefaultValue = GetFeature(fid, sel=1)
            print "Send get feature command with Select=1, returned feature default value: %s "%hex(DefaultValue)
            print ""
            
            print "-(3)--  Test Get Features with Select=2, Saved --"            
                       
            if saveable:
                print "Feature is saveable in capabilities filed"
                
                rdValue=GetFeature(fid, sel=2)
                # choice one value that is not equal to daved value (valid_value, DefaultValue, reset_value)
                if rdValue!=mItem[item.valid_value]:
                    value=mItem[item.valid_value]
                elif rdValue!=mItem[item.reset_value]:
                    value=mItem[item.reset_value]
                else:
                    value=DefaultValue
                
                print "Read saved value = %s"%hex(rdValue)                
                print "Send set feature command with value = %s and SV field =1"%hex(value)
            
                # Send set feature command    
                SetFeature(fid, value, sv=1,nsid=1) if nsSpec else SetFeature(fid, value, sv=1)
                
                # Send get feature command    
                GetValue = GetFeature(fid, sel=2)              
                SavedValue =   GetValue            
                
                # check if (value is set if changeable=true) or  (value is not set if changeable=false) 
                CheckResult(OriginValue=value, CurrentValue=GetValue, ExpectMatch=changeable)   

                
                print "Test Persistent Across Power Cycle and Reset"
                print "Issue Nvme Reset"
                mNVME.nvme_reset()
                # Send get feature command    
                GetValue = GetFeature(fid, sel=2)                
                print "After reset, read feature saved value: %s "%hex(GetValue)
                print "Check if get feature saved value is %s or not "%hex(SavedValue)
                if GetValue == value:
                    mNVME.Print("PASS", "p")  
                else:
                    mNVME.Print("Fail", "f")
                    ret_code=1 
                                    
                print ""                          
                            
            else:
                print "Feature is not saveable in capabilities filed"
                print ""

            print "-(4)--  Test Get Features if capabilities bit 1 = 1, namespace specific"        
            if not nsSpec:
                print "Feature is not namespace specific in capabilities filed"
            else:
                print "Feature is namespace specificin in capabilities filed"
                print "Test if Feature Identifier is namespace specific or not"
                print ""
          
                if not NsSupported:
                    print "Controller don't support mulit namespaces!, quit this test item"
                elif not changeable:
                    print "Feature is not changeable!, quit this test item"
                else:
                    # if only 1 namespace currently, create 2 namespaces
                    if Ns==1:
                        print "Create 2 namespaces, size  1G"
                        Ns=mNVME.CreateMultiNs(NumOfNS=2)
                        
                    if Ns!=2:
                        mNVME.Print("Fail to create 2 namespaces", "f")
                        ret_code=1 
                    else:                            
                        print ""               
                        # nsid = 1 ------------------------------------------------------------
                        value = mItem[item.reset_value]
                        print "Reset feature value = %s for nsid=1 and nsid=2"%value
                        SetFeature(fid=fid, value=value, sv=0, nsid=1)
                        SetFeature(fid=fid, value=value, sv=0, nsid=2)
                        original1 = GetFeature(fid, sel=0, nsid=1)
                        original2 = GetFeature(fid, sel=0, nsid=2)
                        #print "Check if feature value = %s or not in all namespaces"%value                
                        if original1 != value or original2!=value:
                            mNVME.Print("Fail, value from ns1= %s ,ns2= %s "%(original1,original2), "f")
                            ret_code=1                     
                        else:
                            value = mItem[item.valid_value]
                            print "Set feature with nsid =1, value= %s"%value                    
                            SetFeature(fid=fid, value=value, sv=0, nsid=1)
                            
                            current1 = GetFeature(fid, sel=0, nsid=1)
                            current2 = GetFeature(fid, sel=0, nsid=2)
                            
                            print "Get feature values from ns1= %s ,ns2= %s "%(current1,current2)                 
                            print "Check if feature value from ns1 = %s and value from ns2 = %s "   %(value,original2)   
                            
                            if current1==value and current2==original2:
                                mNVME.Print("PASS", "p")  
                            else:
                                mNVME.Print("Fail", "f")
                                ret_code=1 
                            
                            # nsid = 2 ------------------------------------------------------------
                            print ""
                            value = mItem[item.reset_value]
                            print "Reset feature value = %s for nsid=1 and nsid=2"%value
                            SetFeature(fid=fid, value=value, sv=0, nsid=1)
                            SetFeature(fid=fid, value=value, sv=0, nsid=2)                    
                            original1 = GetFeature(fid, sel=0, nsid=1)
                            original2 = GetFeature(fid, sel=0, nsid=2)  
                               
                            value = mItem[item.valid_value]               
                            print "Set feature with nsid =2, value= %s"%value                    
                            SetFeature(fid=fid, value=value, sv=0, nsid=2)
                            
                            current1 = GetFeature(fid, sel=0, nsid=1)
                            current2 = GetFeature(fid, sel=0, nsid=2)
                            
                            print "Get feature values from ns1= %s ,ns2= %s "%(current1,current2)                 
                            print "Check if feature value from ns1 = %s and value from ns2 = %s "   %(value,original2)   
                            
                            if current1==original1 and current2==value:
                                mNVME.Print("PASS", "p")  
                            else:
                                mNVME.Print("Fail", "f")
                                ret_code=1         
                    







if Ns!=1:
    mNVME.ResetNS()



print ""    
print "ret_code:%s"%ret_code
print "Finish"
sys.exit(ret_code)   


































