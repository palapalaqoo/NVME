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


print "Ver: 20181113_0930"
mNVME = NVME.NVME(sys.argv )

## paramter #####################################
ret_code = 0
sub_ret=0
CMD_Result="0"
SANACT=0
ErrorLog=[]

TestItems=[]
SELSupport = True if mNVME.IdCtrl.ONCS.bit(4)=="1" else False
## function #####################################
class item:
    description=0
    fid=1
    capabilities=2
    reset_value=3
    valid_value=4
    saveable=5
    supported=6

def initial():
    # [description, id, capabilities, reset_value, valid_value, saveable, supported]
    global TestItems
    
    description = "Arbitration"
    fid = 1
    supported = True
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    reset_value=GetFeatureValue(fid = fid)
    valid_value=reset_value+(1<<24)
    TestItems.append([description, fid, capabilities, reset_value, valid_value, saveable, supported])
    
    description = "Power Management"
    fid = 2
    supported = True
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    reset_value=GetFeatureValue(fid = fid)
    valid_value=0 if reset_value!=0 else 1
    TestItems.append([description, fid, capabilities, reset_value, valid_value, saveable, supported])
    
    description = "LBA Range Type"
    fid = 3
    supported = True
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    reset_value=GetFeatureValue(fid = fid)
    valid_value=0 if reset_value!=0 else 1
    TestItems.append([description, fid, capabilities, reset_value, valid_value, saveable, supported])
    
    description = "Temperature Threshold"
    fid = 4
    supported = True
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    reset_value=GetFeatureValue(fid = fid)
    valid_value=reset_value+1
    TestItems.append([description, fid, capabilities, reset_value, valid_value, saveable, supported])    
    
    description = "Error Recovery"
    fid = 5
    supported = True
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    reset_value=GetFeatureValue(fid = fid)
    valid_value=reset_value+1
    TestItems.append([description, fid, capabilities, reset_value, valid_value, saveable, supported])        
    
    description = "Volatile Write Cache"
    fid = 6
    supported = True if mNVME.IdCtrl.VWC.bit(0) == "1" else False
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    reset_value=GetFeatureValue(fid = fid)
    valid_value=1 if reset_value==0 else 0
    TestItems.append([description, fid, capabilities, reset_value, valid_value, saveable, supported])            
    '''    
    description = "Number of Queues"
    fid = 7
    supported = True
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    reset_value=GetFeatureValue(fid = fid)
    NCQR=mNVME.int2bytes(reset_value, 2)
    NSQR=mNVME.int2bytes(reset_value, 0)
    valid_value=((NCQR-1)<<16) + (NSQR-1)
    TestItems.append([description, fid, capabilities, reset_value, valid_value, saveable, supported])           
    '''    
    
    description = "Interrupt Coalescing"
    fid = 8
    supported = True
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    reset_value=GetFeatureValue(fid = fid)
    valid_value=1 if reset_value==0 else 0
    TestItems.append([description, fid, capabilities, reset_value, valid_value, saveable, supported])              
    
    description = "Interrupt Vector Configuration(Testing secend Interrupt Vector where cdw11=0x1)"
    fid = 9
    supported = True
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    reset_value=GetFeatureValue(fid = fid, cdw11=1)
    CoalescingDisable=mNVME.int2bytes(reset_value, 4)
    if CoalescingDisable>=1:
        valid_value = reset_value & 0xFFFF
    else:
        valid_value = reset_value | (1<<16)
    TestItems.append([description, fid, capabilities, reset_value, valid_value, saveable, supported])        
    
    description = "Write Atomicity Normal"
    fid = 0xA
    supported = True
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    reset_value=GetFeatureValue(fid = fid)
    valid_value=1 if reset_value==0 else 0
    TestItems.append([description, fid, capabilities, reset_value, valid_value, saveable, supported])   
        
    description = "Asynchronous Event Configuration"
    fid = 0xB
    supported = True
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    reset_value=GetFeatureValue(fid = fid)
    valid_value=1 if reset_value==0 else 0
    TestItems.append([description, fid, capabilities, reset_value, valid_value, saveable, supported])   
        
    description = "Autonomous Power State Transition"
    fid = 0xC
    supported = True if mNVME.IdCtrl.APSTA.bit(0) == "1" else False
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    reset_value=GetFeatureValue(fid = fid)
    valid_value=1 if reset_value==0 else 0
    TestItems.append([description, fid, capabilities, reset_value, valid_value, saveable, supported])      
    
    description = "Host Memory Buffer"
    fid = 0xD
    supported = True if mNVME.IdCtrl.HMPRE.int != 0 else False
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    reset_value=GetFeatureValue(fid = fid)    
    if reset_value &0x1 >=1:
        valid_value = reset_value & 0b0010
    else:
        valid_value = reset_value | 0b0001    
    valid_value=1 if reset_value==0 else 0
    TestItems.append([description, fid, capabilities, reset_value, valid_value, saveable, supported])  

    description = "Host Controlled Thermal Management"
    fid = 0x10
    supported = True if mNVME.IdCtrl.HCTMA.bit(0) == "1" else False
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    reset_value=GetFeatureValue(fid = fid)    
    # Note, MNTMT<= valid_value <=MXTMT
    MXTMT = mNVME.IdCtrl.MXTMT.int
    TMT1=MXTMT-1
    TMT2=MXTMT
    TMT=(TMT1<<16)+(TMT2)    
    if TMT==reset_value:
        TMT1=MXTMT-2
        TMT=(TMT1<<16)+(TMT2)
    valid_value=TMT     
    TestItems.append([description, fid, capabilities, reset_value, valid_value, saveable, supported])      
    
    description = "Software Progress Marker"
    fid = 0x80
    supported = True
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    reset_value=GetFeatureValue(fid = fid)
    valid_value=1 if reset_value==0 else 0
    TestItems.append([description, fid, capabilities, reset_value, valid_value, saveable, supported])          
    
    description = "Host Identifier"
    fid = 0x81
    supported = True if mNVME.IdCtrl.ONCS.bit(5) == "1" else False
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    reset_value=GetFeatureValue(fid = fid)
    valid_value=1 if reset_value==0 else 0
    TestItems.append([description, fid, capabilities, reset_value, valid_value, saveable, supported])      
    
    description = "Reservation Notification Mask"
    fid = 0x82
    supported = True if mNVME.IdNs.RESCAP.int !=0 else False
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    reset_value=GetFeatureValue(fid = fid)
    valid_value=2 if reset_value==0 else 0
    TestItems.append([description, fid, capabilities, reset_value, valid_value, saveable, supported]) 
    
    description = "Reservation Persistance"
    fid = 0x83
    supported = True if mNVME.IdNs.RESCAP.int !=0 else False
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    reset_value=GetFeatureValue(fid = fid)
    valid_value=1 if reset_value==0 else 0
    TestItems.append([description, fid, capabilities, reset_value, valid_value, saveable, supported]) 
                
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
            

def GetFeatureValue(fid, cdw11=0, sel=0):
    Value=0 
    buf = mNVME.get_feature(fid = fid, cdw11=cdw11, sel = sel) 
    mStr="0"
    if sel==0:
        mStr="Current value:(.+)"
    if sel==1:
        mStr="Default value:(.+)"
    if sel==2:
        mStr="Saved value:(.+)"
        
    if re.search(mStr, buf):
        Value=int(re.search(mStr, buf).group(1),16)
    return Value

def GetFeatureSupportedCapabilities(fid):
    if SELSupport:
        Value=0 
        buf = mNVME.get_feature(fid = fid, sel = 3)     
        mStr="capabilities value:(.+)"
        if re.search(mStr, buf):
            Value=int(re.search(mStr, buf).group(1),16)
        return Value
    else:
        return 0


def SetFeature(fid, value, sv):
    # if LBA range, create data structure for set feature command
    if fid==3:
        # Number of LBA Ranges is zero based, 0 means there is 1 LBA Range
        DS=CreateLBARangeDataStructure(value+1)
        mNVME.set_feature(fid, value, sv, Data=DS)
    else:
        mNVME.set_feature(fid, value, sv)

def GetFeature(fid, sel):
    # if Interrupt Vector Configuration, read with cdw11=1
    if fid==9:
        return GetFeatureValue(fid=fid, sel=sel, cdw11=1)
    else:
        return GetFeatureValue(fid=fid, sel=sel)

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


print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Keyword: Get Features – Command Dword 10"
print "Check if Select field in Get Features – Command Dword 10 supported or not"
print ""
if SELSupport:
    mNVME.Print("Supported", "p")
else:
    mNVME.Print("Not Supported", "f")


if SELSupport:
    print ""
    print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
    #print "Keyword: Get Features – Command Dword 10"
    print "Because Select field supported, test all the attributes in Select field"
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
        if not supported:
            print "Not supported"      
            print ""  
        else:
            print "Supported"              
            print "" 
            print "-(1)-- Test Get Features with Select=0, Current --"             
            fid=mItem[item.fid]
            rdValue=mItem[item.reset_value]
            value=mItem[item.valid_value]
            print "Read value = %s"%hex(rdValue)
            print "Send set feature command with value = %s"%hex(value)
            
            # Send set feature command    
            SetFeature(fid, value, sv=0)
            
            # Send get feature command    
            GetValue = GetFeature(fid, sel=0)
            
            print "Send get feature command, returned feature value: %s "%hex(GetValue)
            print "Check if get feature value is %s or not "%hex(value)
            if GetValue == value:
                mNVME.Print("PASS", "p")  
            else:
                mNVME.Print("Fail", "f")
                ret_code=1        
            print ""

            print "-(2)--  Test Get Features with Select=1, Default --"  
            DefaultValue = GetFeature(fid, sel=1)
            print "Send get feature command with Select=1, returned feature default value: %s "%hex(DefaultValue)
            print ""
            
            print "-(3)--  Test Get Features with Select=2, Saved --"  
            saveable = mItem[item.saveable]
            if saveable:
                print "Feature is saveable"
                
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
                SetFeature(fid, value, sv=1)
                
                # Send get feature command    
                GetValue = GetFeature(fid, sel=2)
                
                print "Send get feature command, returned feature saved value: %s "%hex(GetValue)
                print "Check if get feature saved value is %s or not "%hex(value)
                if GetValue == value:
                    mNVME.Print("PASS", "p")  
                else:
                    mNVME.Print("Fail", "f")
                    ret_code=1        
                    
                print "Test Persistent Across Power Cycle and Reset"
                print "Issue Nvme Reset"
                mNVME.nvme_reset()
                # Send get feature command    
                GetValue = GetFeature(fid, sel=2)                
                print "After reset, read feature saved value: %s "%hex(GetValue)
                print "Check if get feature saved value is %s or not "%hex(value)
                if GetValue == value:
                    mNVME.Print("PASS", "p")  
                else:
                    mNVME.Print("Fail", "f")
                    ret_code=1 
                                    
                print ""              
                
                            
            else:
                print "Feature is not saveable"

                
'''        
    print ""   
    print "Test Get Features with Select=1, Default"      
    for mItem in TestItems:
        print mItem[item.description]
        fid=mItem[item.fid]
        rdValue=GetFeatureValue(fid=fid, sel=1)
        print "Read value = %s"%hex(rdValue)

'''





'''
for i in range(1,9):
    #print mNVME.get_feature(fid = i, sel = 3)
    print hex(GetFeatureValue(i))
'''


'''
mNVME.set_feature(2, 2)
print mNVME.get_feature(2)

print ""
print "nvme reset"
mNVME.nvme_reset()

print ""
print mNVME.get_feature(2)
print "--  ---------------------------------------------------------------------------------"


print mNVME.set_feature(2, 2, 1)
print mNVME.get_feature(2)
print ""
print "nvme reset"
mNVME.nvme_reset()

print ""
print mNVME.get_feature(2)
'''











print ""    
print "ret_code:%s"%ret_code
print "Finish"
sys.exit(ret_code)   


































