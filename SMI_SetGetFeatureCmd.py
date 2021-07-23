#!/usr/bin/env python
# -*- coding: utf-8 -*-

        #=======================================================================
        # abstract  function
        #     SubCase1() to SubCase64()                            :Override it for sub case 1 to sub case64
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

class item:
    description=0
    fid=1
    capabilities=2
    reset_value=3
    valid_value=4
    supported=5
    
class SMI_SetGetFeatureCMD(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_SetGetFeatureCMD.py"
    Author = "Sam Chan"
    Version = "20210715"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
  

    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    
    def initial(self):
        # [description, id, capabilities, reset_value, valid_value, supported]
        self.Print("")  
        
        description = "Arbitration"
        fid = 1
        supported = True
        if not supported:
            self.TestItems.append([description, fid, 0, 0, 0, supported])
        else:            
            capabilities , SC=self.GetFeatureSupportedCapabilities(fid)
            reset_value , SC=self.GetFeature(fid = fid)
            valid_value=reset_value+(1<<24)
            self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])

        
        description = "Power Management"
        fid = 2
        supported = True if self.IdCtrl.NPSS.int!=0 else False
        if not supported:
            self.TestItems.append([description, fid, 0, 0, 0, supported])
        else:         
            capabilities , SC=self.GetFeatureSupportedCapabilities(fid)
            reset_value , SC=self.GetFeature(fid = fid)
            valid_value=0 if reset_value!=0 else 1
            self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])
        
        description = "LBA Range Type"
        fid = 3
        supported = True
        if not supported:
            self.TestItems.append([description, fid, 0, 0, 0, supported])
        else:         
            capabilities , SC=self.GetFeatureSupportedCapabilities(fid)
            reset_value , SC=self.GetFeature(fid = fid)
            valid_value=0 if reset_value!=0 else 1
            self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])
        
        description = "Temperature Threshold"
        fid = 4
        supported = True
        if not supported:
            self.TestItems.append([description, fid, 0, 0, 0, supported])
        else:         
            capabilities , SC=self.GetFeatureSupportedCapabilities(fid)
            reset_value , SC=self.GetFeature(fid = fid)
            valid_value=reset_value+1
            self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])    
        
        description = "Error Recovery"
        fid = 5
        supported = True
        if not supported:
            self.TestItems.append([description, fid, 0, 0, 0, supported])
        else:         
            capabilities , SC=self.GetFeatureSupportedCapabilities(fid)
            reset_value , SC=self.GetFeature(fid = fid)
            valid_value=reset_value+1
            self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])        
        
        description = "Volatile Write Cache"
        fid = 6
        supported = True if self.IdCtrl.VWC.bit(0) == "1" else False
        if not supported:
            self.TestItems.append([description, fid, 0, 0, 0, supported])
        else:         
            capabilities , SC=self.GetFeatureSupportedCapabilities(fid)
            reset_value , SC=self.GetFeature(fid = fid)
            valid_value=1 if reset_value==0 else 0
            self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])            
        '''    
        description = "Number of Queues"
        fid = 7
        supported = True
        capabilities , SC=self.GetFeatureSupportedCapabilities(fid)
        reset_value , SC=self.GetFeature(fid = fid)
        NCQR=self.int2bytes(reset_value, 2)
        NSQR=self.int2bytes(reset_value, 0)
        valid_value=((NCQR-1)<<16) + (NSQR-1)
        self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])           
        '''    
        
        description = "Interrupt Coalescing"
        fid = 8
        supported = True
        if not supported:
            self.TestItems.append([description, fid, 0, 0, 0, supported])
        else:         
            capabilities , SC=self.GetFeatureSupportedCapabilities(fid)
            reset_value , SC=self.GetFeature(fid = fid)
            valid_value=1 if reset_value==0 else 0
            self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])              
        
        description = "Interrupt Vector Configuration(Testing secend Interrupt Vector where cdw11=0x1)"
        fid = 9
        supported = True
        if not supported:
            self.TestItems.append([description, fid, 0, 0, 0, supported])
        else:         
            capabilities , SC=self.GetFeatureSupportedCapabilities(fid)
            reset_value , SC=self.GetFeature(fid = fid)
            CoalescingDisable=self.int2bytes(reset_value, 4)
            if CoalescingDisable>=1:
                valid_value = reset_value & 0xFFFF
            else:
                valid_value = reset_value | (1<<16)
            self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])        
        
        description = "Write Atomicity Normal"
        fid = 0xA
        supported = True
        if not supported:
            self.TestItems.append([description, fid, 0, 0, 0, supported])
        else:         
            capabilities , SC=self.GetFeatureSupportedCapabilities(fid)
            reset_value , SC=self.GetFeature(fid = fid)
            valid_value=1 if reset_value==0 else 0
            self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])   
            
        description = "Asynchronous Event Configuration"
        fid = 0xB
        supported = True
        if not supported:
            self.TestItems.append([description, fid, 0, 0, 0, supported])
        else:         
            capabilities , SC=self.GetFeatureSupportedCapabilities(fid)
            reset_value , SC=self.GetFeature(fid = fid)
            valid_value=1 if reset_value==0 else 0
            self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])   
            
        description = "Autonomous Power State Transition"
        fid = 0xC
        supported = True if self.IdCtrl.APSTA.bit(0) == "1" else False
        if not supported:
            self.TestItems.append([description, fid, 0, 0, 0, supported])
        else:         
            capabilities , SC=self.GetFeatureSupportedCapabilities(fid)
            reset_value , SC=self.GetFeature(fid = fid)
            valid_value=1 if reset_value==0 else 0
            self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])      
        
        description = "Host Memory Buffer"
        fid = 0xD
        supported = True if self.IdCtrl.HMPRE.int != 0 else False
        if not supported:
            self.TestItems.append([description, fid, 0, 0, 0, supported])
        else:
            self.Print("Host Memory Buffer supported", "b")
            self.HMB_AttributesData = self.GetHMBAttributesDataStructure()
            if len(self.HMB_AttributesData)!=4:              
                self.Print("Readed HMBAttributesDataStructure Error!, %s"%self.HMB_AttributesData, "f")
            else:                
                self.Print("Host Memory Buffer Size (HSIZE): %s"%self.HMB_AttributesData[0])
                self.Print("Host Memory Descriptor List Address Lower (HMDLAL): %s"%hex(self.HMB_AttributesData[1]))
                self.Print("Host Memory Descriptor List Address Upper (HMDLAU): %s"%hex(self.HMB_AttributesData[2]))
                self.Print("Host Memory Descriptor List Entry Count (HMDLEC): %s"%hex(self.HMB_AttributesData[3]))
                                                
            capabilities , SC=self.GetFeatureSupportedCapabilities(fid)
            if SC!=0:
                self.Print("Fail to GetFeatureSupportedCapabilities for %s, rtCode: %s, rtStr: %s"%(description, SC, capabilities), "f")
            reset_value , SC=self.GetFeature(fid = fid)
            if reset_value&0x1 >=1: # current is enabled
                reset_value = 0x1
                valid_value = 0x0                        
            else:
                reset_value = 0x0
                valid_value = 0x1
            self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])    
                           
        description = "Timestamp"
        fid = 0xE
        supported = True if self.IdCtrl.ONCS.bit(6)=="1" else False
        if not supported:
            self.TestItems.append([description, fid, 0, 0, 0, supported])
        else:
            capabilities , SC=self.GetFeatureSupportedCapabilities(fid)
            reset_value , SC=self.GetFeature(fid = fid)
            valid_value=1 if reset_value==0 else 0
            self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])
                
        description = "Host Controlled Thermal Management"
        fid = 0x10
        supported = True if self.IdCtrl.HCTMA.bit(0) == "1" else False
        if not supported:
            self.TestItems.append([description, fid, 0, 0, 0, supported])
        else:         
            capabilities , SC=self.GetFeatureSupportedCapabilities(fid)
            reset_value , SC=self.GetFeature(fid = fid)    
            # Note, MNTMT<= valid_value <=MXTMT
            MXTMT = self.IdCtrl.MXTMT.int
            TMT1=MXTMT-1
            TMT2=MXTMT
            TMT=(TMT1<<16)+(TMT2)    
            if TMT==reset_value:
                TMT1=MXTMT-2
                TMT=(TMT1<<16)+(TMT2)
            valid_value=TMT     
            self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])      
        
        description = "Software Progress Marker"
        fid = 0x80
        capabilities , SC=self.GetFeatureSupportedCapabilities(fid)
        supported = True if SC ==0 else False
        if not supported:
            self.TestItems.append([description, fid, 0, 0, 0, supported])
        else:         
            capabilities , SC=self.GetFeatureSupportedCapabilities(fid)
            reset_value , SC=self.GetFeature(fid = fid)
            valid_value=1 if reset_value==0 else 0
            self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])          
        
        description = "Host Identifier"
        fid = 0x81
        supported = True if self.IdCtrl.ONCS.bit(5) == "1" else False
        if not supported:
            self.TestItems.append([description, fid, 0, 0, 0, supported])
        else:         
            capabilities , SC=self.GetFeatureSupportedCapabilities(fid)
            reset_value , SC=self.GetFeature(fid = fid)
            valid_value=1 if reset_value==0 else 0
            self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])      
        
        description = "Reservation Notification Mask"
        fid = 0x82
        supported = True if self.IdNs.RESCAP.int !=0 else False
        if not supported:
            self.TestItems.append([description, fid, 0, 0, 0, supported])
        else:         
            capabilities , SC=self.GetFeatureSupportedCapabilities(fid)
            reset_value , SC=self.GetFeature(fid = fid)
            valid_value=2 if reset_value==0 else 0
            self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported]) 
        
        description = "Reservation Persistance"
        fid = 0x83
        supported = True if self.IdNs.RESCAP.int !=0 else False
        if not supported:
            self.TestItems.append([description, fid, 0, 0, 0, supported])
        else:         
            capabilities , SC=self.GetFeatureSupportedCapabilities(fid)
            reset_value , SC=self.GetFeature(fid = fid)
            valid_value=1 if reset_value==0 else 0
            self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported]) 

    def SetHMB(self, value):
    # return true/false and current value
        fid = 0xD
        nsSpec = False
        self.SetFeature(fid, value, sv=0,nsid=1) if nsSpec else self.SetFeature(fid, value, sv=0)
        CMD = self.LastCmd
        # read again
        original1  ,SC_w= self.GetFeature(fid, sel=0, nsid=1)
        if original1 != value :
            self.Print("  Fail to set feature value = 0x%X, current get feature value = 0x%X "%(value, original1), "f")                              
            self.Print("issue set feature CMD and print: %s"%CMD)
            self.Print("%s"%self.shell_cmd(CMD))
            return False, original1
        else:
            return True, original1
        
    def DisableHMB(self):
    # return true/false and current value
        return self.SetHMB(0)

    def EnableHMB(self):
    # return true/false and current value
        return self.SetHMB(1)
                    
    def CreateLBARangeDataStructure(self, NumOfEntrys):
        # create multi entry of LBARangeDataStructure
        # return string , ex "\\255\\12\\78\\ .."
        mStr=""
        for entry in range(NumOfEntrys):        
            self.LBARangeDataStructure.Type=0x2
            self.LBARangeDataStructure.Attributes=0x1
            self.LBARangeDataStructure.SLBA=entry*8
            self.LBARangeDataStructure.NLB=7
            self.LBARangeDataStructure.CreatePattern()
            # save created string to mStr
            mStr = mStr + self.LBARangeDataStructure.Pattern
            
        return mStr
            
    def PrintSupportedFeature(self):
        for mItem in self.TestItems:
            print mItem[item.description]
                
    
    def GetFeatureValueWithSC(self, fid, cdw11=0, sel=0, nsid=1, nsSpec=False):
    # get feature with status code
        Value=0 
        mStr="0"        
        if fid==0xE: # Timestamp, datalen=8, data is milliseconds
            buf, SC = self.get_feature_with_sc(fid = fid, cdw11=cdw11, sel = sel, nsid = nsid, nsSpec=nsSpec, dataLen=8) 
            Value= buf
            # if command success
            if SC==0:
                if sel==3:
                    mStr="capabilities value:(.+)"               
                    if re.search(mStr, buf):
                        Value=int(re.search(mStr, buf).group(1),16)
                else: # sel=0, 1, 2
                    patten=re.findall("\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}", buf)            
                    patten1= ''.join(patten)
                    line=patten1.replace(" ", "")
                    # return list
                    # put patten in to list type
                    n=2
                    rawData = [line[i:i+n] for i in range(0, len(line), n)]
                    if len(rawData)==8:
                        Value=int("0x%s"%rawData[5],16) # e.x. 0000: fe 49 02 15 78 01 02 00  , using 01 as value 
        else:
            buf, SC = self.get_feature_with_sc(fid = fid, cdw11=cdw11, sel = sel, nsid = nsid, nsSpec=nsSpec) 
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

        return Value, SC
    
    
    def GetFeatureSupportedCapabilities(self, fid):
        if self.SELSupport:
            return self.GetFeature(fid=fid, sel=3)
        else:
            return -1
    
    def SetFeature(self, fid, value, sv, nsid=0, printInfo=True):
    # return intger, Status Code
    # nsid=0, not ns spec
        # if LBA range, create data structure for set feature command
        mStr=""
        if fid==3:
            # Number of LBA Ranges is zero based, 0 means there is 1 LBA Range
            DS=self.CreateLBARangeDataStructure(value+1)
            mStr, SC = self.set_feature_with_sc(fid = fid, value = value, SV = sv, nsid = nsid, Data=DS)
        elif fid==0xC:
            #DS='\\x0\\x0\\x0\\x0\\x0\\x0\\x0\\x0'
            DS=''.join(["\\x0" for i in range(8*32)]) # set 32 power states to 0x0, i.e. 64bit * 32 power states
            mStr, SC = self.set_feature_with_sc(fid = fid, value = value, SV = sv, nsid = nsid, Data=DS) 
        elif fid == 0xD: #HMB
            HSIZE = self.HMB_AttributesData[0]
            HMDLAL = self.HMB_AttributesData[1]  
            HMDLAU = self.HMB_AttributesData[2]    
            HMDLEC = self.HMB_AttributesData[3]
            if sv!=0:
                CDW10=0xD | 1<<31
            else:
                CDW10=0xD
            CMD = "nvme admin-passthru %s --opcode=0x9 --cdw10=%s "\
            "--cdw11=%s --cdw12=%s --cdw13=%s --cdw14=%s  --cdw15=%s -n %s 2>&1"\
            %(self.dev_port, CDW10, value, hex(HSIZE), hex(HMDLAL), hex(HMDLAU), hex(HMDLEC), nsid)
            mStr, SC = self.shell_cmd_with_sc(CMD)
        elif fid == 0xE: #TimeStamp, set value = 0, and DS = value
            #DS='\\x0\\x0\\x0\\x0\\x0\\x1\\x0\\x0'
            DS='\\x0\\x0\\x0\\x0\\x0\\x%X\\x0\\x0'%value
            mStr, SC = self.set_feature_with_sc(fid = fid, value = 0, SV = sv, nsid = nsid, Data=DS)
        else:
            mStr, SC = self.set_feature_with_sc(fid = fid, value = value, SV = sv, nsid = nsid)
            
        if printInfo:
            if SC==0:
                self.Print("SetFeature cmd success, Return status =: %s"%mStr)
            else:
                self.Print("SetFeature cmd fail, Return status =: %s"%mStr)
            
        return SC #status code
        
    
    def GetFeature(self, fid, sel=0, nsid=1, printInfo=False):
        # if Interrupt Vector Configuration, read with cdw11=1
        # nsSpec=True for test purpuse
        if fid==9:
            Value, SC = self.GetFeatureValueWithSC(fid=fid, sel=sel, cdw11=1, nsid=nsid, nsSpec=True)
        else:
            Value, SC = self.GetFeatureValueWithSC(fid=fid, sel=sel, nsid=nsid, nsSpec=True)
        
        if printInfo:
            if SC==0:
                self.Print("GetFeature cmd success") #self.Print("GetFeature cmd success, Return status =: %s"%Value)
            else:
                self.Print("GetFeature cmd fail, Return status =: %s"%Value)  
        return Value, SC
        
    def DifferentValueFromCurrent(self, fid):
        currentValue  ,SC= self.GetFeature(fid, sel=0)
        resetValue=0
        validValue=0
        for mItem in self.TestItems:
            if mItem[item.fid]==fid:            
                resetValue=mItem[item.reset_value]
                validValue=mItem[item.valid_value]
                break
                
        if currentValue != resetValue:
            return resetValue
        else:
            return validValue
    
    def CheckResult(self, WriteValue, OriginValue, CurrentValue, ExpectMatch):
    # if WriteValue = CurrentValue, and ExpectMatch = true,
    # or OriginValue != CurrentValue, and ExpectMatch = false, then pass
    
        
        self.Print ("Send get feature command, returned feature value: %s "%hex(CurrentValue))
        ecpectedValue = WriteValue if ExpectMatch else OriginValue
        self.Print ("Check get feature value, expected value: %s (%s) "%( ecpectedValue, "changed" if ExpectMatch else "not changed" ))
        if CurrentValue == ecpectedValue:
            self.Print("PASS", "p")  
        else:
            self.Print("Fail", "f")
            self.ret_code=1              
    
    def VerifyNotSupport(self, mItem): 
        
        fid=mItem[item.fid]
        self.Print (""  )
        self.Print ("-(1)-- Test Get Features with Select=0, Current --"    )
        rtCode = int(self.shell_cmd(" nvme get-feature %s -f %s -s 0 >/dev/null 2>&1 ; echo $?"%(self.dev, fid)))
        self.Print ("Send get feature command, returned code: 0x%X "%(rtCode))
        self.Print ("Check if return code!=0")
        if rtCode!=0:
            self.Print("PASS", "p")  
        else:
            self.Print("Fail", "f")
            self.ret_code=1 
            
        self.Print (""  )    
        self.Print ("-(2)-- Test Get Features with Select=1, Default --"  )
        rtCode = int(self.shell_cmd(" nvme get-feature %s -f %s -s 1 >/dev/null 2>&1 ; echo $?"%(self.dev, fid)))
        self.Print ("Send get feature command, returned code: 0x%X "%(rtCode))
        self.Print ("Check if return code!=0")
        if rtCode!=0:
            self.Print("PASS", "p")  
        else:
            self.Print("Fail", "f")
            self.ret_code=1       
            
        self.Print (""  )    
        self.Print ("-(3)--  Test Get Features with Select=2, Saved --"            )
        rtCode = int(self.shell_cmd(" nvme get-feature %s -f %s -s 2 >/dev/null 2>&1  ; echo $?"%(self.dev, fid)))
        self.Print ("Send get feature command, returned code: 0x%X "%(rtCode))
        self.Print ("Check if return code!=0")
        if rtCode!=0:
            self.Print("PASS", "p")  
        else:
            self.Print("Fail", "f")
            self.ret_code=1                        
        
    def SetCurrAndSavedToDiffValue(self, CurrValue, SavedValue, ValidValue, ResetValue, fid, nsSpec):
        if CurrValue==SavedValue:
            if CurrValue!=ValidValue:
                value=ValidValue
            else:
                value=ResetValue                 
            # Send set feature command    
            sc = self.SetFeature(fid, value, sv=0,nsid=1) if nsSpec else self.SetFeature(fid, value, sv=0)                
            GetValue  ,SC= self.GetFeature(fid, sel=0)
            if SavedValue!=GetValue:
                return True
            else:
                return False        
    
    def VerifySaveAble(self, mItem):
        supported=mItem[item.supported]
        saveable=True if mItem[item.capabilities]&0b001 > 0 else False   
        nsSpec=True if mItem[item.capabilities]&0b010 > 0 else False
        changeable=True if mItem[item.capabilities]&0b100 > 0 else False        
        fid=mItem[item.fid]
        # get default value
        DefaultValue  ,SC= self.GetFeature(fid, sel=1)        

        self.Print ("Feature is saveable in capabilities filed") if saveable else self.Print ("Feature is not saveable in capabilities filed")
        
        rdValue , SC=self.GetFeature(fid, sel=2)
        SavedValuebk=rdValue    # backup saved value
        # choice one value that is not equal to saved value (valid_value, DefaultValue, reset_value)
        if rdValue!=mItem[item.valid_value]:
            value=mItem[item.valid_value]
        elif rdValue!=mItem[item.reset_value]:
            value=mItem[item.reset_value]
        else:
            value=DefaultValue        
        self.Print ("Read saved value = %s"%hex(rdValue))
        self.Print ("Read default value = %s"%hex(DefaultValue))
        if not saveable:
            self.Print ("Feature is not saveable, check if saved value is the same as default value.")
            if rdValue==DefaultValue:
                self.Print("PASS", "p")
            else:
                self.Print("Fail", "f")
                self.ret_code=1       
        
        
        self.Print ("Send set feature command with value = %s and SV field =1"%hex(value))
    
        # Send set feature command    
        sc = self.SetFeature(fid, value, sv=1,nsid=1) if nsSpec else self.SetFeature(fid, value, sv=1)
        if saveable:
            self.Print ("Check if set feature command success")
            if sc==0:
                self.Print("PASS", "p")  
            else:
                self.Print("Fail", "f")
                self.ret_code=1 
        else:
            self.Print ("Check if set feature command fail with status code = 0xD(FEATURE_NOT_SAVEABLE)")
            if sc==0xD:
                self.Print("PASS", "p")  
            else:
                self.Print("Fail", "f")
                self.ret_code=1                     
        # Send get feature command    
        GetValue  ,SC= self.GetFeature(fid, sel=2)              
        SavedValue =   GetValue            
        
        # check if (value is set if changeable=true) or  (value is not set if changeable=false) 
        self.CheckResult(WriteValue=value, OriginValue=rdValue, CurrentValue=GetValue, ExpectMatch=saveable)   
        
        if saveable:
            self.Print ("Test Persistent Across Power Cycle and Reset", "b")
            self.SetPrintOffset(4)            
            ValidValue = mItem[item.valid_value]
            ResetValue = mItem[item.reset_value]
            self.Print ("")
            self.Print ("NVMe reset test", "b")
            self.Print ("Set saved and current value different")
            CurrValue  ,SC= self.GetFeature(fid, sel=0)
            if self.SetCurrAndSavedToDiffValue(CurrValue, SavedValue, ValidValue, ResetValue, fid, nsSpec):
                self.Print ("Done")
            else:
                self.Print ("Fail","f")
                self.ret_code=1                
            CurrValue  ,SC= self.GetFeature(fid, sel=0)
            self.Print ("Saved Value: %s"%SavedValue)
            self.Print ("Current Value: %s"%CurrValue)            
            
            self.Print ("-- Issue Nvme Reset")
            self.nvme_reset()
            # Send get feature command    
            GetValue  ,SC= self.GetFeature(fid, sel=2)                
            self.Print ("After reset, read feature saved value: %s "%hex(GetValue))
            self.Print ("Check if get feature saved value is %s or not "%hex(SavedValue))
            if GetValue == value:
                self.Print("PASS", "p")  
            else:
                self.Print("Fail", "f")
                self.ret_code=1 
            GetValue  ,SC= self.GetFeature(fid, sel=0)                
            self.Print ("Read current value: %s "%hex(GetValue))            
            self.Print ("Check if current value is %s or not(the same with saved value) "%hex(SavedValue))
            if GetValue == value:
                self.Print("PASS", "p")  
            else:
                self.Print("Fail", "f")
                self.ret_code=1             
            self.Print ("")
            
            if self.DisablePwr:  
                self.Print ("-- User disable power off and power on test")
            else:
                for mode in ["por", "spor"]:
                    self.Print ("")
                    if mode =="por":
                        self.Print ("Normal power off test", "b")
                    else:
                        self.Print ("Suddenly power off test", "b")
                    self.Print ("Set saved and current value different")
                    CurrValue  ,SC= self.GetFeature(fid, sel=0)
                    if self.SetCurrAndSavedToDiffValue(CurrValue, SavedValue, ValidValue, ResetValue, fid, nsSpec):
                        self.Print ("Done")
                    else:
                        self.Print ("Fail","f")
                        self.ret_code=1                
                    CurrValue  ,SC= self.GetFeature(fid, sel=0)
                    self.Print ("Saved Value: %s"%SavedValue)
                    self.Print ("Current Value: %s"%CurrValue)               
                    
                    if mode =="por":
                        self.Print ("-- Do normal power off and power on ")
                        self.por_reset()
                    else:
                        self.Print ("-- Do suddenly power off and power on ")
                        self.spor_reset()                    
                    sleep(0.5)
                    # Send get feature command    
                    GetValue  ,SC= self.GetFeature(fid, sel=2)                
                    self.Print ("After power on, read feature saved value: %s "%hex(GetValue))
                    self.Print ("Check if get feature saved value is %s or not "%hex(SavedValue))
                    if GetValue == value:
                        self.Print("PASS", "p")  
                    else:
                        self.Print("Fail", "f")
                        self.ret_code=1                         
                    GetValue  ,SC= self.GetFeature(fid, sel=0)                
                    self.Print ("Read current value: %s "%hex(GetValue))            
                    self.Print ("Check if current value is %s or not(the same with saved value) "%hex(SavedValue))
                    if GetValue == value:
                        self.Print("PASS", "p")  
                    else:
                        self.Print("Fail", "f")
                        self.ret_code=1                                                                         
        self.SetPrintOffset(0)
        value = SavedValuebk
        self.Print ("restore to previous 'saved value': %s"%hex(value))
        if int(value)==0:
            value = DefaultValue
            self.Print ("becouse previous 'saved value' =0, set 'saved value' to default value: %s"%hex(value))                        
        # Send set feature command    
        self.SetFeature(fid, value, sv=1,nsid=1) if nsSpec else self.SetFeature(fid, value, sv=1)  
        self.Print ("End of restore values")         
        self.Print (""                          )     
            
    
    def TestNsInMulitNS(self, mItem):
        supported=mItem[item.supported]
        saveable=True if mItem[item.capabilities]&0b001 > 0 else False   
        nsSpec=True if mItem[item.capabilities]&0b010 > 0 else False
        changeable=True if mItem[item.capabilities]&0b100 > 0 else False        
        fid=mItem[item.fid]
        # get default value
        DefaultValue  ,SC= self.GetFeature(fid, sel=1)  
        # if only 1 namespace currently, create 2 namespaces
        if self.Ns==1:
            self.Print ("Create 2 namespaces, size  1G")
            Ns=self.CreateMultiNs(NumOfNS=2)
            
        if Ns!=2:
            self.Print("Fail to create 2 namespaces", "f")
            self.ret_code=1 
        else:                            
            self.Print (""               )
            # nsid = 1 ------------------------------------------------------------
            value = mItem[item.reset_value]
            self.Print ("Reset feature value = %s for nsid=1 and nsid=2"%value)
            self.SetFeature(fid=fid, value=value, sv=0, nsid=1)
            self.SetFeature(fid=fid, value=value, sv=0, nsid=2)
            original1  ,SC= self.GetFeature(fid, sel=0, nsid=1)
            original2  ,SC= self.GetFeature(fid, sel=0, nsid=2)
            #self.Print ("Check if feature value = %s or not in all namespaces"%value                )
            if original1 != value or original2!=value:
                self.Print("Fail, value from ns1= %s ,ns2= %s "%(original1,original2), "f")
                self.ret_code=1                     
            else:
                value = mItem[item.valid_value]
                self.Print ("Set feature with nsid =1, value= %s"%value                    )
                self.SetFeature(fid=fid, value=value, sv=0, nsid=1)
                
                current1  ,SC= self.GetFeature(fid, sel=0, nsid=1)
                current2  ,SC= self.GetFeature(fid, sel=0, nsid=2)
                
                self.Print ("Get feature values from ns1= %s ,ns2= %s "%(current1,current2)                 )
                self.Print ("Check if feature value from ns1 = %s and value from ns2 = %s "   %(value,original2)   )
                
                if current1==value and current2==original2:
                    self.Print("PASS", "p")  
                else:
                    self.Print("Fail", "f")
                    self.ret_code=1 
                
                # nsid = 2 ------------------------------------------------------------
                self.Print ("")
                value = mItem[item.reset_value]
                self.Print ("Reset feature value = %s for nsid=1 and nsid=2"%value)
                self.SetFeature(fid=fid, value=value, sv=0, nsid=1)
                self.SetFeature(fid=fid, value=value, sv=0, nsid=2)                    
                original1  ,SC= self.GetFeature(fid, sel=0, nsid=1)
                original2  ,SC= self.GetFeature(fid, sel=0, nsid=2)  
                   
                value = mItem[item.valid_value]               
                self.Print ("Set feature with nsid =2, value= %s"%value)
                self.SetFeature(fid=fid, value=value, sv=0, nsid=2)
                
                current1  ,SC= self.GetFeature(fid, sel=0, nsid=1)
                current2  ,SC= self.GetFeature(fid, sel=0, nsid=2)
                
                self.Print ("Get feature values from ns1= %s ,ns2= %s "%(current1,current2)                 )
                self.Print ("Check if feature value from ns1 = %s and value from ns2 = %s "   %(original1, value)   )
                
                if current1==original1 and current2==value:
                    self.Print("PASS", "p")  
                else:
                    self.Print("Fail", "f")
                    self.ret_code=1

                # nsid = 3 ------------------------------------------------------------
                self.Print ("")
                value = mItem[item.reset_value]
                self.Print ("Reset feature value = %s for nsid=1 and nsid=2"%value)
                self.SetFeature(fid=fid, value=value, sv=0, nsid=1)
                self.SetFeature(fid=fid, value=value, sv=0, nsid=2)                    
                original1  ,SC= self.GetFeature(fid, sel=0, nsid=1)
                original2  ,SC= self.GetFeature(fid, sel=0, nsid=2)  
                   
                value = mItem[item.valid_value]               
                self.Print ("Set feature with nsid =3, value= %s"%value)
                self.SetFeature(fid=fid, value=value, sv=0, nsid=3)
                
                current1  ,SC= self.GetFeature(fid, sel=0, nsid=1)
                current2  ,SC= self.GetFeature(fid, sel=0, nsid=2)
                
                self.Print ("Get feature values from ns1= %s ,ns2= %s "%(current1,current2)                 )
                self.Print ("Check if feature value from ns1 = %s and value from ns2 = %s "   %(original1,original2)   )
                
                if current1==original1 and current2==original2:
                    self.Print("PASS", "p")  
                else:
                    self.Print("Fail", "f")
                    self.ret_code=1
                
    def TestSetFeatureStatusCode(self, header, mItem, nsid_w, expectStatusCode_w):
    # flow:     1) write to default, 
    #              2) write to another value using nsid_w 
    #              3) verify by reading feature data
    # nsid_w to be write
    # nsid_r to be read
    # expectStatusCode, Completion Queue Entry, incoude Status Code Type (SCT) and Status Code (SC)
        supported=mItem[item.supported]
        saveable=True if mItem[item.capabilities]&0b001 > 0 else False   
        nsSpec=True if mItem[item.capabilities]&0b010 > 0 else False
        changeable=True if mItem[item.capabilities]&0b100 > 0 else False        
        fid=mItem[item.fid]
        # Restore value    
        value = mItem[item.reset_value]        
        self.Print ("")
        step = 1
        self.Print ("%s%s. Restore current value by setting feature value to 0x%X(expected success)"%(header, step, value))
        step = step+1
        self.RestoreCurrentValue(fid, value, nsSpec)     
        RestoredValue = value   
        self.Print ("")

        # write, value_w= write value, SC_w return SC
        value_w = mItem[item.valid_value]
        self.Print ("%s%s. Set feature with nsid =0x%X, value= 0x%X, expected Status Code=0x%X"%(header, step, nsid_w, value_w, expectStatusCode_w))
        step = step+1
        SC_w = self.SetFeature(fid=fid, value=value_w, sv=0, nsid=nsid_w)       
        self.Print ("  Return Status Code: 0x%X"%SC_w)
        self.Print ("  Check if Status Code = 0x%X"   %(expectStatusCode_w))
        if SC_w==expectStatusCode_w:
            self.Print("  PASS", "p")
        else:
            self.Print("  Fail", "f")
            self.ret_code=1
            
        # verify current value
        self.Print ("")
        self.Print ("%s%s. Verify current value, read current value"%(header, step))
        step = step+1
        current1  ,SC= self.GetFeature(fid, sel=0)
        # if read success, then compare value
        if SC==0:
            self.Print ("  Return current value: 0x%X"%current1)   
            if SC_w==0: # if last write success, expect new value
                self.Print ("  Expected current value: 0x%X (write success)"%value_w)
                ExpectedValue = value_w
            else:
                self.Print ("  Expected current value: 0x%X (write fail)"%RestoredValue)
                ExpectedValue = RestoredValue
            
            self.Print ("  Check if current value = Expected value")
            if current1==ExpectedValue:
                self.Print("  PASS", "p")
            else:
                self.Print("  Fail", "f")
                self.ret_code=1     
        else:
            self.Print("  Fail, can't read value!", "f")
            self.ret_code=1     

    def TestGetFeatureStatusCode(self, header, mItem, nsid_r, expectStatusCode_r):
    # flow:     1) write to default, 
    #              2) issue read and check status
    #              3) verify by the data from step 2
    # nsid_r to be read
    # expectStatusCode, Completion Queue Entry, incoude Status Code Type (SCT) and Status Code (SC)
        supported=mItem[item.supported]
        saveable=True if mItem[item.capabilities]&0b001 > 0 else False   
        nsSpec=True if mItem[item.capabilities]&0b010 > 0 else False
        changeable=True if mItem[item.capabilities]&0b100 > 0 else False        
        fid=mItem[item.fid]
        # Restore value    
        value = mItem[item.reset_value]        
        self.Print ("")
        step = 1
        self.Print ("%s%s. Restore current value by setting feature value to 0x%X(expected success)"%(header, step, value))
        step = step+1
        self.RestoreCurrentValue(fid, value, nsSpec)
        RestoredValue = value
        self.Print ("")           
         
        # read
        self.Print ("")
        self.Print ("%s%s. Get feature value with nsid 0x%X, , expected Status Code=0x%X"%(header, step, nsid_r, expectStatusCode_r))
        step = step+1
        current1  ,SC_r= self.GetFeature(fid, sel=0, nsid=nsid_r, printInfo=True)
        self.Print ("  Return Status Code: 0x%X"%SC_r)
        self.Print ("  Check if Status Code = 0x%X"   %(expectStatusCode_r))
        if SC_r==expectStatusCode_r:
            self.Print("  PASS", "p")
        else:
            self.Print("  Fail", "f")
            self.ret_code=1 
            
            
        self.Print ("")
        self.Print ("%s%s. Verify Get feature Cmd returned current value"%(header, step))
        step = step+1            
        # if read success, then compare value
        if SC_r==0:
            self.Print ("  Return current value: 0x%X"%current1)   
            self.Print ("  Expected current value: 0x%X (restored value)"%RestoredValue)
            ExpectedValue = RestoredValue

            
            self.Print ("  Check if current value = Expected value")
            if current1==ExpectedValue:
                self.Print("  PASS", "p")
            else:
                self.Print("  Fail", "f")
                self.ret_code=1     
        else:
            self.Print("  Get feature Cmd is fail, skip this step")
        
                
    
                        
    class nsidType:
        ActiveNS = 0
        InActiveNS = 1
        Broadcast = 2
        Zero = 3
        InValidNS = 4
        UnKnow = 5
    
    def GetSpecStatusCode(self, fid, setGetCmd, nsidTypeIn, isNsSpecific, specVer):
        '''
        setGetCmd: set/get
        nsidTypeIn: class nsidType
        isNsSpecific: True/False
        specVer: 1.3c/1.3d
    
        '''               
        INVALID_NS=0xB
        INVALID_FIELD=0x2
        CMD_SUCCESS=0x0
        FEATURE_NOT_PER_NS=0x0F
        rtSC = CMD_SUCCESS
        # Not NS Specific
        if not isNsSpecific:
            # # Not NS Specific->Set
            if setGetCmd == "set":
                if nsidTypeIn == self.nsidType.Zero:
                    rtSC = CMD_SUCCESS                
                if nsidTypeIn == self.nsidType.ActiveNS:
                    rtSC = FEATURE_NOT_PER_NS
                if nsidTypeIn == self.nsidType.InActiveNS:
                    rtSC = FEATURE_NOT_PER_NS #INVALID_FIELD      
                if nsidTypeIn == self.nsidType.InValidNS:
                    rtSC = INVALID_FIELD
                    '''
                    if specVer =="1.3c":
                        rtSC = INVALID_NS
                    else:
                        rtSC = INVALID_FIELD     
                    '''                           
                if nsidTypeIn == self.nsidType.Broadcast:
                    rtSC = CMD_SUCCESS
            # Not NS Specific->Get        
            elif  setGetCmd == "get":
                if nsidTypeIn == self.nsidType.Zero:
                    rtSC = CMD_SUCCESS                
                if nsidTypeIn == self.nsidType.ActiveNS:
                    rtSC = CMD_SUCCESS
                if nsidTypeIn == self.nsidType.InActiveNS:
                    rtSC = CMD_SUCCESS #INVALID_FIELD      
                if nsidTypeIn == self.nsidType.InValidNS:
                    rtSC = INVALID_FIELD
                    '''
                    if specVer =="1.3c":
                        rtSC = INVALID_NS
                    else:
                        rtSC = INVALID_FIELD  
                    '''                              
                if nsidTypeIn == self.nsidType.Broadcast:
                    rtSC = CMD_SUCCESS                
        # NS Specific
        if isNsSpecific:
            # NS Specific->set
            if setGetCmd == "set":
                if nsidTypeIn == self.nsidType.Zero:
                    rtSC = INVALID_NS                
                if nsidTypeIn == self.nsidType.ActiveNS:
                    rtSC = CMD_SUCCESS
                if nsidTypeIn == self.nsidType.InActiveNS:
                    rtSC = INVALID_FIELD      
                if nsidTypeIn == self.nsidType.InValidNS:
                    rtSC = INVALID_NS                              
                if nsidTypeIn == self.nsidType.Broadcast:
                    rtSC = CMD_SUCCESS
            # NS Specific->get        
            elif  setGetCmd == "get":
                if nsidTypeIn == self.nsidType.Zero:
                    rtSC = INVALID_NS                
                if nsidTypeIn == self.nsidType.ActiveNS:
                    rtSC = CMD_SUCCESS
                if nsidTypeIn == self.nsidType.InActiveNS:
                    rtSC = INVALID_FIELD      
                if nsidTypeIn == self.nsidType.InValidNS:
                    rtSC = INVALID_NS                          
                if nsidTypeIn == self.nsidType.Broadcast:
                    rtSC = INVALID_NS
                    
        # end ..
        # exeption
        # if set feature, FID=3, specVer =="1.3c", specVer !="1.3c", nsid=0xFFFFFFFF return INVALID_FIELD
        if (fid == 3) and (specVer !="1.3c") and (setGetCmd == "set") and (nsidTypeIn == self.nsidType.Broadcast) :      
            rtSC = INVALID_FIELD        
                                 
        return rtSC
    
    def TestFeatureStatusCode(self, header, mItem, nsid, fid, setGetCmd, nsSpec, specVersion):   
        Type = self.nsidType.UnKnow
        TypeStr = "unknow"    
        if nsid==0x0:
            Type = self.nsidType.Zero
            TypeStr = ""
        if nsid==0x1:
            Type = self.nsidType.ActiveNS
            TypeStr = "(ActiveNS)"
        if nsid==0xFFFFFFFE:
            Type = self.nsidType.InValidNS
            TypeStr = "(InValidNS)"
        if nsid==0xFFFFFFFF:
            Type = self.nsidType.Broadcast     
            TypeStr = "(Broadcast)"       
          
            
        # get expected sc code from NVMe spec by fid, set/get, nsidType, nsSpec, specVersion
        SC_w = self.GetSpecStatusCode(fid, setGetCmd, Type, nsSpec, specVersion)
        self.Print ("-(%s)--  test %s feature ID=0x%X with nsid=0x%X%s, feature is %sNS Specific, expected SC = 0x%X"%
                    (header, setGetCmd, fid, nsid, TypeStr, ""if nsSpec else "Not ", SC_w)) 
        header = header +"." 
        if setGetCmd=="set":
            self.TestSetFeatureStatusCode(header=header, mItem=mItem, nsid_w=nsid, expectStatusCode_w = SC_w)
        else:
            self.TestGetFeatureStatusCode(header=header, mItem=mItem, nsid_r=nsid, expectStatusCode_r = SC_w)
    
    def VerifyNSspec(self, mItem):
        supported=mItem[item.supported]
        saveable=True if mItem[item.capabilities]&0b001 > 0 else False   
        nsSpec=True if mItem[item.capabilities]&0b010 > 0 else False
        changeable=True if mItem[item.capabilities]&0b100 > 0 else False        
        fid=mItem[item.fid]
        # get default value
        DefaultValue  ,SC= self.GetFeature(fid, sel=1)
        self.Print ("")     
        if not nsSpec:
            self.Print ("Feature is not namespace specific in capabilities filed")
        else:
            self.Print ("Feature is namespace specific in capabilities filed")      
            
            
            
        headCnt=1    
        self.Print ("-----------------------------------------------------")
              
        self.Print ("")
        header = "%s"%headCnt; headCnt = headCnt +1
        nsid = 0
        setGetCmd = "set"        
        # do TestFeatureStatusCode
        self.TestFeatureStatusCode(header, mItem, nsid, fid, setGetCmd, nsSpec, self.specVersion)
        self.Print ("-----------------------------------------------------") 
        
        self.Print ("")
        header = "%s"%headCnt; headCnt = headCnt +1
        nsid = 0
        setGetCmd = "get"        
        # do TestFeatureStatusCode
        self.TestFeatureStatusCode(header, mItem, nsid, fid, setGetCmd, nsSpec, self.specVersion)
        self.Print ("-----------------------------------------------------") 
        
        self.Print ("")
        header = "%s"%headCnt; headCnt = headCnt +1
        nsid = 1
        setGetCmd = "set"        
        # do TestFeatureStatusCode
        self.TestFeatureStatusCode(header, mItem, nsid, fid, setGetCmd, nsSpec, self.specVersion)
        self.Print ("-----------------------------------------------------") 
        
        self.Print ("")
        header = "%s"%headCnt; headCnt = headCnt +1
        nsid = 1
        setGetCmd = "get"        
        # do TestFeatureStatusCode
        self.TestFeatureStatusCode(header, mItem, nsid, fid, setGetCmd, nsSpec, self.specVersion)
        self.Print ("-----------------------------------------------------")   
        
        self.Print ("")
        header = "%s"%headCnt; headCnt = headCnt +1
        nsid = 0xFFFFFFFE
        setGetCmd = "set"        
        # do TestFeatureStatusCode
        self.TestFeatureStatusCode(header, mItem, nsid, fid, setGetCmd, nsSpec, self.specVersion)
        self.Print ("-----------------------------------------------------")         
              
        self.Print ("")
        header = "%s"%headCnt; headCnt = headCnt +1
        nsid = 0xFFFFFFFE
        setGetCmd = "get"        
        # do TestFeatureStatusCode
        self.TestFeatureStatusCode(header, mItem, nsid, fid, setGetCmd, nsSpec, self.specVersion)
        self.Print ("-----------------------------------------------------")    
        
        self.Print ("")
        header = "%s"%headCnt; headCnt = headCnt +1
        nsid = 0xFFFFFFFF
        setGetCmd = "set"        
        # do TestFeatureStatusCode
        self.TestFeatureStatusCode(header, mItem, nsid, fid, setGetCmd, nsSpec, self.specVersion)
        self.Print ("-----------------------------------------------------")            
        
        self.Print ("")
        header = "%s"%headCnt; headCnt = headCnt +1
        nsid = 0xFFFFFFFF
        setGetCmd = "get"        
        # do TestFeatureStatusCode
        self.TestFeatureStatusCode(header, mItem, nsid, fid, setGetCmd, nsSpec, self.specVersion)
        self.Print ("-----------------------------------------------------") 
                                        
        self.Print ("")            
        if not nsSpec:
            pass
        else:
            self.Print ("Create 2 namespaces to test feature in mulit namespaces")
            if not self.NsSupported:
                self.Print ("Controller don't support mulit namespaces!, skip to test for mulit namespaces", "w")
            elif not changeable:
                self.Print ("Feature is not changeable!, skip to test for mulit namespaces", "w")
            elif self.disableNsTest:
                self.Print ("-- User disable namespace test for this feature")
            else:
                self.TestNsInMulitNS(mItem)
                
        if self.Ns!=1:
            self.Print ("Remove all created namespaces")
            self.ResetNS()    
    
    def VerifyStatusCode(self, fid):
        for mItem in self.TestItems:
            if int(mItem[item.fid])!=int(fid):
                continue
            
            # if fid match
            self.Print ( mItem[item.description]   )
            self.Print ("Feature ID: %s"%mItem[item.fid]   )
            supported=mItem[item.supported]
            
            self.Print ("" )            
            self.Print ("Supported", "p") if supported else self.Print("Not supported", "w")
            if supported:
                saveable=True if mItem[item.capabilities]&0b001 > 0 else False   
                nsSpec=True if mItem[item.capabilities]&0b010 > 0 else False
                changeable=True if mItem[item.capabilities]&0b100 > 0 else False                
                self.Print ("Feature saveable: %s"%("Yes" if saveable else "No"))
                self.Print ("Feature namespace specific: %s"%("Yes" if nsSpec else "No"))
                self.Print ("Feature changeable: %s"%("Yes" if changeable else "No"))
            self.Print ("")
            if not supported:
                pass                            
            else:                                      
                self.Print ("")
                self.Print ("Test Features capabilities bit 1, namespace specific" , "b")
                self.VerifyNSspec(mItem)
                          
    def GetHMBAttributesDataStructure(self, cdw11=0, sel=0, nsid=1, nsSpec=True):
    # get feature with status code
        fid = 13
        Value=0 
        AttributesDataStructure=[]
        buf, SC = self.get_feature_with_sc(fid = fid, cdw11=cdw11, sel = sel, nsid = nsid, nsSpec=nsSpec) 
        mStr="Current value:(\w+)"

        if re.search(mStr, buf):
            Value=int(re.search(mStr, buf).group(1),16)
            # Host Memory Buffer – Attributes Data Structure
            AttributesDataStructure=re.findall("\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}", buf)
            if len(AttributesDataStructure)==0:
                self.Print("Error, cant find AttributesDataStructure, raw data: %s"%buf, "f")
            AttributesDataStructure = AttributesDataStructure[0]   # find first only
            patten1 = AttributesDataStructure
            line=patten1.replace(" ", "")         
            # return list
            # put patten in to list type
            n=2
            AttributesDataStructure= [line[i:i+n] for i in range(0, len(line), n)] 
            AttributesDataStructure = [int(i, 16) for i in AttributesDataStructure]
            if len(AttributesDataStructure)!=16:
                self.Print("Error, AttributesDataStructure size incorrect, raw data: %s"%AttributesDataStructure, "f")   
                
            HSIZE = self.GetBytesFromList(AttributesDataStructure, 3, 0)
            HMDLAL = self.GetBytesFromList(AttributesDataStructure, 7, 4)  
            HMDLAU = self.GetBytesFromList(AttributesDataStructure, 11, 8)
            HMDLEC = self.GetBytesFromList(AttributesDataStructure, 15, 12)
            AttributesDataStructure = [HSIZE, HMDLAL, HMDLAU, HMDLEC]
            
        return AttributesDataStructure    
    
    def VerifyHMB(self):
        # if current is enable, do disable and enable, else reverse flow
        fid = 0xD
        for mItem in self.TestItems:
            if int(mItem[item.fid])!=int(fid):
                continue
            
            # if fid match
            supported=mItem[item.supported]
            
            if supported:                
                reset_value , SC=self.GetFeature(fid = fid)
                self.Print("Start to verify set feature command ------------", "b")
                self.Print("")
                if len(self.HMB_AttributesData)!=4:
                    self.Print("HMBAttributesDataStructure Incorrect!, %s"%self.HMB_AttributesData, "f")
                    return False
                self.Print("Host Memory Buffer Size (HSIZE): %s"%self.HMB_AttributesData[0])
                self.Print("Host Memory Descriptor List Address Lower (HMDLAL): %s"%hex(self.HMB_AttributesData[1]))
                self.Print("Host Memory Descriptor List Address Upper (HMDLAU): %s"%hex(self.HMB_AttributesData[2]))
                self.Print("Host Memory Descriptor List Entry Count (HMDLEC): %s"%hex(self.HMB_AttributesData[3]))
                
                self.Print("")
                self.Print("Issue cmd to get current feature value=%s"%(reset_value), "b")
                # set value with Memory Return (MR) = 1, ie no need to provide Host Memory Descriptor List
                if reset_value==1: # current is enabled
                    self.Print("Current is enabled")                                       
                    self.Print("Start to disable and enable..", "b")
                    self.Print("Try to disable..")
                    success, currentValue = self.DisableHMB()
                    if success:
                        self.Print("Current is disabled, current value = %s"%currentValue)
                        self.Print("Try to enable..")
                        success, currentValue = self.EnableHMB()                
                        if success:
                            self.Print("Current is enabled, current value = %s"%currentValue)
                        else:
                            self.Print("Can not enabled!, current value = %s"%currentValue, "f")  
                            return False                                   
                    else:
                        self.Print("Can not disable!, current value = %s"%currentValue, "f")  
                        return False
                elif reset_value==0:  
                    self.Print("Current is disable")                    
                    self.Print("Start to enable and disable..", "b")
                    self.Print("Try to enable..")
                    success, currentValue = self.EnableHMB()
                    if success:
                        self.Print("Current is enable, current value = %s"%currentValue)
                        self.Print("Try to disable..")
                        success, currentValue = self.DisableHMB()                
                        if success:
                            self.Print("Current is disable, current value = %s"%currentValue)
                        else:
                            self.Print("Can not disable!, current value = %s"%currentValue, "f")        
                            return False                             
                    else:
                        self.Print("Can not enable!, current value = %s"%currentValue, "f")       
                        return False 
                else:
                    self.Print("current value = %s, not = 0x1 or 0x0, invalid value!!"%reset_value, "f")       
                    return False                     
                self.Print("End of verify set feature command ------------", "b")
            self.Print("")             
            return True                
                                
    
    
    def VerifyFID(self, fid):
        
        for mItem in self.TestItems:
            if int(mItem[item.fid])!=int(fid):
                continue
            
            # if fid match
            self.Print ( mItem[item.description]   )
            self.Print ("Feature ID: %s"%mItem[item.fid]   )
            supported=mItem[item.supported]
            
            self.Print ("" )            
            self.Print ("Supported", "p") if supported else self.Print("Not supported", "w")
            if supported:
                saveable=True if mItem[item.capabilities]&0b001 > 0 else False   
                nsSpec=True if mItem[item.capabilities]&0b010 > 0 else False
                changeable=True if mItem[item.capabilities]&0b100 > 0 else False                
                self.Print ("Feature saveable: %s"%("Yes" if saveable else "No"))
                self.Print ("Feature namespace specific: %s"%("Yes" if nsSpec else "No"))
                self.Print ("Feature changeable: %s"%("Yes" if changeable else "No"))
            self.Print ("")            
            
            if not supported:
                self.VerifyNotSupport(mItem)                              
            else:                
                self.Print ("-(1)-- Test Get Features with Select=0, Current --"    , "b")
                self.Print ("        and test Features capabilities bit 2, Feature Identifier is changeable or not")
                self.Print ("        "+ "Feature is changeable, all the fallowing test should change the value" if changeable else "Feature is no changeable, all the fallowing test should not change the value")
                fid=mItem[item.fid]
                rdValue , SC=self.GetFeature(fid, sel=0)
                value=self.DifferentValueFromCurrent(fid)
                self.Print ("Send get feature command, returned feature value: %s "%hex(rdValue))
                self.Print ("Send set feature command with value = %s"%hex(value))
                
                # Send set feature command    
                self.SetFeature(fid, value, sv=0,nsid=1) if nsSpec else self.SetFeature(fid, value, sv=0)
                
                # Send get feature command    
                GetValue  ,SC= self.GetFeature(fid, sel=0)
                
                # check if (value is set if changeable=true) or  (value is not set if changeable=false) 
                self.CheckResult(WriteValue=value, OriginValue=rdValue, CurrentValue=GetValue, ExpectMatch=changeable)    
                self.Print ("")
    
                self.Print ("-(2)--  Test Get Features with Select=1, Default --"  , "b")
                DefaultValue  ,SC= self.GetFeature(fid, sel=1)
                self.Print ("Send get feature command with Select=1, returned feature default value: %s "%hex(DefaultValue))
                self.Print ("")
                
                self.Print ("-(3)--  Test Get Features with Select=2, Saved --" , "b")
                self.VerifySaveAble(mItem)
                                  
                self.Print ("")
                self.Print ("-(4)--  Test Features with capabilities bit 2, Feature Identifier is not changeable", "b")
                if changeable:
                    self.Print( "Feature Identifier is changeable, quit" )
                else:
                    self.Print( "Feature Identifier is not changeable" )
                    self.Print ("Send set feature command with value = %s"%hex(value))                    
                    # Send set feature command    
                    CMD_Result = self.SetFeature(fid, value, sv=0,nsid=1) if nsSpec else self.SetFeature(fid, value, sv=0)
                    self.Print ("Check set feature command status code, expected code: FEATURE_NOT_CHANGEABLE (0x0E)")
                    if CMD_Result==0x0E:  
                        self.Print("PASS", "p")  
                    else:
                        self.Print("Fail", "f")
                        self.ret_code=1                                    

                self.Print ("") 
                self.Print ("-(5)--  Test Get Features with invalid Select field(100b to 111b)" , "b")
                invalidList = [4,5,6,7]
                self.Print ("Send get feature command with SEL=%s, expected CMD fail with INVALID_FIELD(0x2)"%invalidList)
                self.SetPrintOffset(4)
                for sel in invalidList:
                    rdValue , SC=self.GetFeature(fid, sel)
                    self.Print ("Send get feature command with SEL=%s, return status code: 0x%X"%(sel, SC))
                    if SC==0x2:
                        self.Print("PASS", "p")  
                    else:
                        self.Print("Fail", "f")
                        self.ret_code=1                    
                self.SetPrintOffset(0)

                self.Print ("") 
                self.Print ("-(6)--  Restore values", "b")     
                
                value=mItem[item.reset_value]
                self.Print ("restore to previous 'current value': %s"%hex(value))
                self.RestoreCurrentValue(fid, value, nsSpec)                
                                
    def RestoreCurrentValue(self, fid, value, nsSpec):
        # Restore value      
        original1  ,SC_w= self.GetFeature(fid, sel=0, nsid=1)
        if original1==value:
            self.Print("  Current value = 0x%X, no need to restore! "%(original1), "p")
        else:        
            self.SetFeature(fid, value, sv=0,nsid=1) if nsSpec else self.SetFeature(fid, value, sv=0)
            # SC_w = last write status, will use it to 'verify current value'
            original1  ,SC_w= self.GetFeature(fid, sel=0, nsid=1)
            if original1 != value :
                self.Print("  Fail to set feature value = 0x%X, current get feature value = 0x%X "%(value, original1), "f")
                return False
            self.Print("  Success to restore feature value to 0x%X "%(original1), "p")
        return True

    def GetFeatureParameters(self, fid):
        supported = False
        saveable = None
        nsSpec= None
        changeable = None
        for mItem in self.TestItems:
            if int(mItem[item.fid])!=int(fid):
                continue
            
            # if fid match
            self.Print ( mItem[item.description]   )
            self.Print ("Feature ID: %s"%mItem[item.fid]   )
            supported=mItem[item.supported]      
            self.Print ("Supported", "p") if supported else self.Print("Not supported", "w")
            if supported:
                self.Print ("" )      
                saveable=True if mItem[item.capabilities]&0b001 > 0 else False   
                nsSpec=True if mItem[item.capabilities]&0b010 > 0 else False
                changeable=True if mItem[item.capabilities]&0b100 > 0 else False
                currValue=mItem[item.reset_value]             
                self.Print ("Feature saveable: %s"%("Yes" if saveable else "No"))
                self.Print ("Feature namespace specific: %s"%("Yes" if nsSpec else "No"))
                self.Print ("Feature changeable: %s"%("Yes" if changeable else "No"))   
                self.Print ("Feature current value: 0x%X"%currValue)
        return supported,  saveable, nsSpec, changeable, currValue
    
    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def __init__(self, argv):
        # initial new parser if need, -t -d -s -p was used, dont use it again
        self.SetDynamicArgs(optionName="x", optionNameFull="disablepwr", helpMsg="disable poweroff, ex. '-x 1'", argType=int)    
        self.SetDynamicArgs(optionName="n", optionNameFull="disableNsTest", helpMsg="disable namespace test, ex. '-n 1'", argType=int)        
        self.SetDynamicArgs(optionName="v", optionNameFull="version", helpMsg="nvme spec version, 1.3c / 1.3d, default= 1.3d, ex. '-v 1.3c'", argType=str)    
        
        # initial parent class
        super(SMI_SetGetFeatureCMD, self).__init__(argv)
        
        # get new parser if need, where args order is the same with initial order
        self.DisablePwr = self.GetDynamicArgs(0)
        self.DisablePwr = True if self.DisablePwr==1 else False        
        self.disableNsTest = self.GetDynamicArgs(1)
        self.disableNsTest = True if self.disableNsTest==1 else False
        
        VersionDefine = ["1.3c", "1.3d", "1.4"]
        self.specVersion = self.GetDynamicArgs(2)
        self.specVersion = "1.3d" if self.specVersion==None else self.specVersion   # default = 1.3d
        if not self.specVersion in VersionDefine:   # if input is not in VersionDefine, e.g keyin wrong version
            self.specVersion = "1.3c"
                  
        self.ret_code = 0
        self.Ns=1
        self.TestItems=[]
        self.SELSupport = True if self.IdCtrl.ONCS.bit(4)=="1" else False
        self.NsSupported=True if self.IdCtrl.OACS.bit(3)=="1" else False 
        
        self.HMB_AttributesData = []       

    
    # override
    def PreTest(self):
        if self.DisablePwr:
            self.Print ("User disable power off/on test", "f")     
        if self.disableNsTest:
            self.Print ("User disable namespace test", "f")  
        self.Print ("")    
        
        self.Print ("Taget Spec Version: %s"%self.specVersion)
        
        self.Print ("") 
        self.Print ("Issue nvme reset controller")
        self.nvme_reset()
        
        self.Print ("Check if Select field in Get Features - Command Dword 10 supported or not")
        self.Print ("")
        if self.SELSupport:
            self.Print("Supported", "p")    
            # initial self.TestItems
            self.initial()        
            self.Print("Test item 'Keep Alive Timer' has not implemented ", "w")

            return True
        else:
            self.Print("Not Supported", "f")     
            return False   
        
    # <sub item scripts>
    SubCase1TimeOut = 600
    SubCase1Desc = "Arbitration"        
    def SubCase1(self):
        self.ret_code=0
        self.VerifyFID(1)
        return self.ret_code

    SubCase2TimeOut = 600
    SubCase2Desc = "Power Management"        
    def SubCase2(self):
        self.ret_code=0
        self.VerifyFID(2)
        return self.ret_code

    SubCase3TimeOut = 600
    SubCase3Desc = "LBA Range Type"        
    def SubCase3(self):
        self.ret_code=0
        self.VerifyFID(3)
        return self.ret_code

    SubCase4TimeOut = 600
    SubCase4Desc = "Temperature Threshold"        
    def SubCase4(self):
        self.ret_code=0
        self.VerifyFID(4)
        return self.ret_code
    
    SubCase5TimeOut = 600
    SubCase5Desc = "Error Recovery"       
    def SubCase5(self):
        self.ret_code=0
        self.VerifyFID(5)
        return self.ret_code
    
    SubCase6TimeOut = 600
    SubCase6Desc ="Volatile Write Cache"    
    def SubCase6(self):
        self.ret_code=0
        self.VerifyFID(6)
        return self.ret_code
    
    SubCase7TimeOut = 600
    SubCase7Desc = "Number of Queues"       
    def SubCase7(self):
        self.ret_code=0
        self.VerifyFID(7)
        return self.ret_code
    
    SubCase8TimeOut = 600
    SubCase8Desc = "Interrupt Coalescing"      
    def SubCase8(self):
        self.ret_code=0
        self.VerifyFID(8)
        return self.ret_code
    
    SubCase9TimeOut = 600
    SubCase9Desc = "Interrupt Vector Configuration(Testing secend Interrupt Vector where cdw11=0x1)"      
    def SubCase9(self):
        self.ret_code=0
        self.VerifyFID(9)
        return self.ret_code
    
    SubCase10TimeOut = 600
    SubCase10Desc = "Write Atomicity Normal"       
    def SubCase10(self):
        self.ret_code=0
        self.VerifyFID(10)
        return self.ret_code
    
    SubCase11TimeOut = 600
    SubCase11Desc = "Asynchronous Event Configuration"       
    def SubCase11(self):
        self.ret_code=0
        self.VerifyFID(11)
        return self.ret_code
    
    SubCase12TimeOut = 600
    SubCase12Desc = "Autonomous Power State Transition"      
    def SubCase12(self):
        self.ret_code=0
        self.VerifyFID(12)
        return self.ret_code
    
    SubCase13TimeOut = 600
    SubCase13Desc = "Host Memory Buffer"
    def SubCase13(self):
        self.ret_code=0
        if not self.VerifyHMB(): return 1
        self.VerifyFID(13)
        return self.ret_code    
    
    SubCase14TimeOut = 600
    SubCase14Desc = "Host Controlled Thermal Management"
    def SubCase14(self):
        self.ret_code=0
        self.VerifyFID(0x10)
        return self.ret_code  
    
    SubCase15TimeOut = 600
    SubCase15Desc = "Software Progress Marker"
    def SubCase15(self):
        self.ret_code=0
        self.VerifyFID(0x80)
        return self.ret_code  
    
    SubCase16TimeOut = 600
    SubCase16Desc = "Host Identifier"
    def SubCase16(self):
        self.ret_code=0
        self.VerifyFID(0x81)
        return self.ret_code      
    
    SubCase17TimeOut = 600
    SubCase17Desc = "Reservation Notification Mask"
    def SubCase17(self):
        self.ret_code=0
        self.VerifyFID(0x82)
        return self.ret_code      
    
    SubCase18TimeOut = 600
    SubCase18Desc = "Reservation Persistance"
    def SubCase18(self):
        self.ret_code=0
        self.VerifyFID(0x83)
        return self.ret_code     
    
    SubCase19TimeOut = 600
    SubCase19Desc = "Ulink3.0 StatusCode -> Arbitration"        
    def SubCase19(self):
        self.ret_code=0
        self.VerifyStatusCode(1)
        return self.ret_code

    SubCase20TimeOut = 600
    SubCase20Desc = "Ulink3.0 StatusCode -> Power Management"        
    def SubCase20(self):
        self.ret_code=0
        self.VerifyStatusCode(2)
        return self.ret_code

    SubCase21TimeOut = 600
    SubCase21Desc = "Ulink3.0 StatusCode -> LBA Range Type"        
    def SubCase21(self):
        self.ret_code=0
        self.VerifyStatusCode(3)
        return self.ret_code

    SubCase22TimeOut = 600
    SubCase22Desc = "Ulink3.0 StatusCode -> Temperature Threshold"        
    def SubCase22(self):
        self.ret_code=0
        self.VerifyStatusCode(4)
        return self.ret_code
    
    SubCase23TimeOut = 600
    SubCase23Desc = "Ulink3.0 StatusCode -> Error Recovery"       
    def SubCase23(self):
        self.ret_code=0
        self.VerifyStatusCode(5)
        return self.ret_code
    
    SubCase24TimeOut = 600
    SubCase24Desc ="Ulink3.0 StatusCode -> Volatile Write Cache"    
    def SubCase24(self):
        self.ret_code=0
        self.VerifyStatusCode(6)
        return self.ret_code
    
    SubCase25TimeOut = 600
    SubCase25Desc = "Ulink3.0 StatusCode -> Number of Queues"       
    def SubCase25(self):
        self.ret_code=0
        self.VerifyStatusCode(7)
        return self.ret_code
    
    SubCase26TimeOut = 600
    SubCase26Desc = "Ulink3.0 StatusCode -> Interrupt Coalescing"      
    def SubCase26(self):
        self.ret_code=0
        self.VerifyStatusCode(8)
        return self.ret_code
    
    SubCase27TimeOut = 600
    SubCase27Desc = "Ulink3.0 StatusCode -> Interrupt Vector Configuration(Testing secend Interrupt Vector where cdw11=0x1)"      
    def SubCase27(self):
        self.ret_code=0
        self.VerifyStatusCode(9)
        return self.ret_code
    
    SubCase28TimeOut = 600
    SubCase28Desc = "Ulink3.0 StatusCode -> Write Atomicity Normal"       
    def SubCase28(self):
        self.ret_code=0
        self.VerifyStatusCode(10)
        return self.ret_code
    
    SubCase29TimeOut = 600
    SubCase29Desc = "Ulink3.0 StatusCode -> Asynchronous Event Configuration"       
    def SubCase29(self):
        self.ret_code=0
        self.VerifyStatusCode(11)
        return self.ret_code
    
    SubCase30TimeOut = 600
    SubCase30Desc = "Ulink3.0 StatusCode -> Autonomous Power State Transition"      
    def SubCase30(self):
        self.ret_code=0
        self.VerifyStatusCode(12)
        return self.ret_code
    
    SubCase31TimeOut = 600
    SubCase31Desc = "Ulink3.0 StatusCode -> Host Memory Buffer"
    def SubCase31(self):
        self.ret_code=0
        if not self.VerifyHMB(): return 1
        self.VerifyStatusCode(13)
        return self.ret_code    
    
    SubCase32TimeOut = 600
    SubCase32Desc = "Ulink3.0 StatusCode -> Host Controlled Thermal Management"
    def SubCase32(self):
        self.ret_code=0
        self.VerifyStatusCode(0x10)
        return self.ret_code  
    
    SubCase33TimeOut = 600
    SubCase33Desc = "Ulink3.0 StatusCode -> Software Progress Marker"
    def SubCase33(self):
        self.ret_code=0
        self.VerifyStatusCode(0x80)
        return self.ret_code  
    
    SubCase34TimeOut = 600
    SubCase34Desc = "Ulink3.0 StatusCode -> Host Identifier"
    def SubCase34(self):
        self.ret_code=0
        self.VerifyStatusCode(0x81)
        return self.ret_code      
    
    SubCase35TimeOut = 600
    SubCase35Desc = "Ulink3.0 StatusCode -> Reservation Notification Mask"
    def SubCase35(self):
        self.ret_code=0
        self.VerifyStatusCode(0x82)
        return self.ret_code      
    
    SubCase36TimeOut = 600
    SubCase36Desc = "Ulink3.0 StatusCode -> Reservation Persistance"
    def SubCase36(self):
        self.ret_code=0
        self.VerifyStatusCode(0x83)
        return self.ret_code    
    
    SubCase37TimeOut = 600
    SubCase37Desc = "[YMTC CTA-152] Set Features(Asynchronous Event Configuration) for NVMe v1.4"
    def SubCase37(self):
        self.ret_code=0
        self.Print("Current taget version for NVMe: %s"%self.specVersion)
        if self.specVersion!="1.4":
            self.Print("Please run command with -v 1.4 if going to verify this test case!")
            return 0
        
        self.Print("")
        fid = 0xB        
        supported, saveable, nsSpec, changeable, currValue = self.GetFeatureParameters(fid)
        
        if not supported:
            pass                            
        else:                                      
            self.Print ("") 
            self.Print("Issue a Set Features command with value = 5226(0x146A) for FID = 0xB(Asynchronous Event Configuration)")
            value = 0x146A
            self.SetFeature(fid, value, sv=0,nsid=1) if nsSpec else self.SetFeature(fid, value, sv=0)
            self.Print("Issue get feature command")
            current1  ,SC= self.GetFeature(fid, sel=0)
            if SC==0:
                self.Print ("  Return current value: 0x%X"%current1)   
                self.Print ("  Check if current value = 0x%X"%value)
                if current1==value:
                    self.Print("  PASS", "p")
                else:
                    self.Print("  Fail", "f")
                    self.ret_code=1     
            else:
                self.Print("  Fail, can't read value!", "f")
                self.ret_code=1  
                  
            self.Print ("")    
            self.Print ("--  Restore values", "b")    
            value=currValue
            self.Print ("restore to previous 'current value': %s"%hex(value))
            if not self.RestoreCurrentValue(fid, value, nsSpec): 
                self.ret_code = 1

        return self.ret_code        
    
    SubCase38TimeOut = 600
    SubCase38Desc = "[YMTC CTA-169] Set feature bit 14(Endurance Group Event Aggregate Log Change Notices) for NVMe v1.4"
    def SubCase38(self):
        self.ret_code=0
        self.Print("Current taget version for NVMe: %s"%self.specVersion)
        if self.specVersion!="1.4":
            self.Print("Please run command with -v 1.4 if going to verify this test case!")
            return 0
        
        self.Print("")
        fid = 0xB        
        supported, saveable, nsSpec, changeable, resetValue = self.GetFeatureParameters(fid)
        
        if not supported:
            pass                            
        else:                                      
            self.Print ("") 
            EGEALsupported = True if self.IdCtrl.OAES.bit(14) =="1" else False
            
            self.Print("Endurance Group Event Aggregate log: %s"%("supported(oaes bit14=1)" if EGEALsupported else "not supported(oaes bit14=0)"))
            
            value = 1<<14
            self.Print("Issue a Set Features command with value = 0x%X(Endurance Group Event Aggregate Log Change Notices = 1) for FID = 0xB"%value)            
            SC = self.SetFeature(fid, value, sv=0,nsid=1) if nsSpec else self.SetFeature(fid, value, sv=0)
            self.Print("Return status: 0x%X"%SC)
            if EGEALsupported:
                self.Print("Check if status is 0x0(success)")
                if SC==0:
                    self.Print("  PASS", "p")
                else:
                    self.Print("  Fail", "f")
                    self.ret_code=1
            else:
                self.Print("Check if status is 0x2(Invalid Field)")
                if SC==2:
                    self.Print("  PASS", "p")
                else:
                    self.Print("  Fail", "f")
                    self.ret_code=1                        
            
                
                
            self.Print("Issue get feature command")
            current1  ,SC= self.GetFeature(fid, sel=0)
            if SC==0:
                self.Print ("  Return current value: 0x%X"%current1)
                if EGEALsupported:   
                    self.Print("Endurance Group Event Aggregate log supported, expect set feature success")
                    self.Print ("  Check if current value = 0x%X"%value)
                    if current1==value:
                        self.Print("  PASS", "p")
                    else:
                        self.Print("  Fail", "f")
                        self.ret_code=1
                else:   
                    self.Print("Endurance Group Event Aggregate log not supported, expect set feature fail")
                    self.Print ("  Check if current value = 0x%X"%resetValue)
                    if current1==resetValue:
                        self.Print("  PASS", "p")
                    else:
                        self.Print("  Fail", "f")
                        self.ret_code=1                        
                             
            else:
                self.Print("  Fail, can't read value!", "f")
                self.ret_code=1  
                  
            self.Print ("")    
            self.Print ("--  Restore values", "b")    
            value=resetValue
            self.Print ("restore to previous 'current value': %s"%hex(value))
            if not self.RestoreCurrentValue(fid, value, nsSpec): 
                self.ret_code = 1

        return self.ret_code          
    

    SubCase39TimeOut = 600
    SubCase39Desc = "Timestamp"
    def SubCase39(self):
        self.Print ("Note: below test will set/get the 6th byte of Timestamp Data Structure only", "f")        
        self.Print ("")
        self.ret_code=0
        self.VerifyFID(0xE)
        return self.ret_code         
    
    SubCase40TimeOut = 600
    SubCase40Desc = "Ulink3.0 StatusCode -> Timestamp"
    def SubCase40(self):
        self.ret_code=0
        self.Print ("Note: below test will set/get the 6th byte of Timestamp Data Structure only", "f")
        self.Print ("")
        self.VerifyStatusCode(0xE)
        return self.ret_code     
     
    # </sub item scripts>
    
    
    
    
if __name__ == "__main__":
    DUT = SMI_SetGetFeatureCMD(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 
    
    
    
    
    
