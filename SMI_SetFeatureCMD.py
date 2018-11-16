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
    default_value=3
    valid_value=4
    saveable=5

def initial():
    # [description, id, capabilities, default_value, valid_value]
    global TestItems
    
    description = "Arbitration"
    fid = 1
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    default_value=GetFeatureValue(fid = fid)
    valid_value=default_value+(1<<24)
    TestItems.append([description, fid, capabilities, default_value, valid_value, saveable])
    
    description = "Power Management"
    fid = 2
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    default_value=GetFeatureValue(fid = fid)
    valid_value=0 if default_value!=0 else 1
    TestItems.append([description, fid, capabilities, default_value, valid_value, saveable])
    
    description = "LBA Range Type"
    fid = 3
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    default_value=GetFeatureValue(fid = fid)
    valid_value=0 if default_value!=0 else 1
    TestItems.append([description, fid, capabilities, default_value, valid_value, saveable])
    
    description = "Temperature Threshold"
    fid = 4
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    default_value=GetFeatureValue(fid = fid)
    valid_value=default_value+1
    TestItems.append([description, fid, capabilities, default_value, valid_value, saveable])    
    
    description = "Error Recovery"
    fid = 5
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    default_value=GetFeatureValue(fid = fid)
    valid_value=default_value+1
    TestItems.append([description, fid, capabilities, default_value, valid_value, saveable])        
    
    description = "Volatile Write Cache"
    fid = 6
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    default_value=GetFeatureValue(fid = fid)
    valid_value=1 if default_value==0 else 0
    TestItems.append([description, fid, capabilities, default_value, valid_value, saveable])            
    '''    
    description = "Number of Queues"
    fid = 7
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    default_value=GetFeatureValue(fid = fid)
    NCQR=mNVME.int2bytes(default_value, 2)
    NSQR=mNVME.int2bytes(default_value, 0)
    valid_value=((NCQR-1)<<16) + (NSQR-1)
    TestItems.append([description, fid, capabilities, default_value, valid_value, saveable])           
    '''    
    
    description = "Interrupt Coalescing"
    fid = 8
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    default_value=GetFeatureValue(fid = fid)
    valid_value=1 if default_value==0 else 0
    TestItems.append([description, fid, capabilities, default_value, valid_value, saveable])              
    
    description = "Interrupt Vector Configuration(Testing secend Interrupt Vector where cdw11=0x1)"
    fid = 9
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    default_value=GetFeatureValue(fid = fid, cdw11=1)
    CoalescingDisable=mNVME.int2bytes(default_value, 4)
    if CoalescingDisable>=1:
        valid_value = default_value & 0xFFFF
    else:
        valid_value = default_value | (1<<16)
    TestItems.append([description, fid, capabilities, default_value, valid_value, saveable])        
    
    description = "Write Atomicity Normal"
    fid = 0xA
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    default_value=GetFeatureValue(fid = fid)
    valid_value=1 if default_value==0 else 0
    TestItems.append([description, fid, capabilities, default_value, valid_value, saveable])   
        
    description = "Asynchronous Event Configuration"
    fid = 0xB
    capabilities=GetFeatureSupportedCapabilities(fid)
    saveable=True if capabilities&0b001 > 0 else False
    default_value=GetFeatureValue(fid = fid)
    valid_value=1 if default_value==0 else 0
    TestItems.append([description, fid, capabilities, default_value, valid_value, saveable])   
        
    
    
    
    
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
    mStr="Current value:(.+)"
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

## end function #####################################







print ""
print "-- NVME Get/Set Feature command test" 
print "-----------------------------------------------------------------------------------"

print "Nvme reset controller"
mNVME.nvme_reset()

# initial TestItems
initial()

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
    print "Supported features:"
    print "------------------------------------------"
    PrintSupportedFeature()
    print "------------------------------------------"
    
    print ""  
    print "Test Get Features with Select=0, Current"      
    for mItem in TestItems:
        print mItem[item.description]
        fid=mItem[item.fid]
        rdValue=mItem[item.default_value]
        value=mItem[item.valid_value]
        print "Read value = %s"%hex(rdValue)
        print "Send set feature command with value = %s"%hex(value)
        
        # if LBA range, create data structure for set feature command
        if fid==3:
            # Number of LBA Ranges is zero based, 0 means there is 1 LBA Range
            DS=CreateLBARangeDataStructure(value+1)
            mNVME.set_feature(fid, value, SV=0, Data=DS)
        else:
            mNVME.set_feature(fid, value, SV=0)
            
        # if Interrupt Vector Configuration, read with cdw11=1
        if fid==9:
            GetValue=GetFeatureValue(fid=fid, sel=0, cdw11=1)
        else:
            GetValue=GetFeatureValue(fid=fid, sel=0)
        
        print "Send get feature command, returned feature value: %s "%hex(GetValue)
        print "Check if get feature value is %s or not "%hex(value)
        if GetValue == value:
            mNVME.Print("PASS", "p")  
        else:
            mNVME.Print("Fail", "f")
            ret_code=1        
        print ""
            
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


































