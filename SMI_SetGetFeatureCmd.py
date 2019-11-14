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
from lib_vct.NVMECom import deadline

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
    Version = "20191030"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
  

    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    
    def initial(self):
        # [description, id, capabilities, reset_value, valid_value, supported]
        
        description = "Arbitration"
        fid = 1
        supported = True
        capabilities=self.GetFeatureSupportedCapabilities(fid)
        reset_value=self.GetFeature(fid = fid)
        valid_value=reset_value+(1<<24)
        self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])
        
        description = "Power Management"
        fid = 2
        supported = True if self.IdCtrl.NPSS.int!=0 else False
        capabilities=self.GetFeatureSupportedCapabilities(fid)
        reset_value=self.GetFeature(fid = fid)
        valid_value=0 if reset_value!=0 else 1
        self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])
        
        description = "LBA Range Type"
        fid = 3
        supported = True
        capabilities=self.GetFeatureSupportedCapabilities(fid)
        reset_value=self.GetFeature(fid = fid)
        valid_value=0 if reset_value!=0 else 1
        self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])
        
        description = "Temperature Threshold"
        fid = 4
        supported = True
        capabilities=self.GetFeatureSupportedCapabilities(fid)
        reset_value=self.GetFeature(fid = fid)
        valid_value=reset_value+1
        self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])    
        
        description = "Error Recovery"
        fid = 5
        supported = True
        capabilities=self.GetFeatureSupportedCapabilities(fid)
        reset_value=self.GetFeature(fid = fid)
        valid_value=reset_value+1
        self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])        
        
        description = "Volatile Write Cache"
        fid = 6
        supported = True if self.IdCtrl.VWC.bit(0) == "1" else False
        capabilities=self.GetFeatureSupportedCapabilities(fid)
        reset_value=self.GetFeature(fid = fid)
        valid_value=1 if reset_value==0 else 0
        self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])            
        '''    
        description = "Number of Queues"
        fid = 7
        supported = True
        capabilities=self.GetFeatureSupportedCapabilities(fid)
        reset_value=self.GetFeature(fid = fid)
        NCQR=self.int2bytes(reset_value, 2)
        NSQR=self.int2bytes(reset_value, 0)
        valid_value=((NCQR-1)<<16) + (NSQR-1)
        self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])           
        '''    
        
        description = "Interrupt Coalescing"
        fid = 8
        supported = True
        capabilities=self.GetFeatureSupportedCapabilities(fid)
        reset_value=self.GetFeature(fid = fid)
        valid_value=1 if reset_value==0 else 0
        self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])              
        
        description = "Interrupt Vector Configuration(Testing secend Interrupt Vector where cdw11=0x1)"
        fid = 9
        supported = True
        capabilities=self.GetFeatureSupportedCapabilities(fid)
        reset_value=self.GetFeature(fid = fid)
        CoalescingDisable=self.int2bytes(reset_value, 4)
        if CoalescingDisable>=1:
            valid_value = reset_value & 0xFFFF
        else:
            valid_value = reset_value | (1<<16)
        self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])        
        
        description = "Write Atomicity Normal"
        fid = 0xA
        supported = True
        capabilities=self.GetFeatureSupportedCapabilities(fid)
        reset_value=self.GetFeature(fid = fid)
        valid_value=1 if reset_value==0 else 0
        self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])   
            
        description = "Asynchronous Event Configuration"
        fid = 0xB
        supported = True
        capabilities=self.GetFeatureSupportedCapabilities(fid)
        reset_value=self.GetFeature(fid = fid)
        valid_value=1 if reset_value==0 else 0
        self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])   
            
        description = "Autonomous Power State Transition"
        fid = 0xC
        supported = True if self.IdCtrl.APSTA.bit(0) == "1" else False
        capabilities=self.GetFeatureSupportedCapabilities(fid)
        reset_value=self.GetFeature(fid = fid)
        valid_value=1 if reset_value==0 else 0
        self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])      
        
        description = "Host Memory Buffer"
        fid = 0xD
        supported = True if self.IdCtrl.HMPRE.int != 0 else False
        capabilities=self.GetFeatureSupportedCapabilities(fid)
        reset_value=self.GetFeature(fid = fid)    
        if reset_value &0x1 >=1:
            valid_value = reset_value & 0b0010
        else:
            valid_value = reset_value | 0b0001    
        valid_value=1 if reset_value==0 else 0
        self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])  
    
        description = "Host Controlled Thermal Management"
        fid = 0x10
        supported = True if self.IdCtrl.HCTMA.bit(0) == "1" else False
        capabilities=self.GetFeatureSupportedCapabilities(fid)
        reset_value=self.GetFeature(fid = fid)    
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
        supported = True
        capabilities=self.GetFeatureSupportedCapabilities(fid)
        reset_value=self.GetFeature(fid = fid)
        valid_value=1 if reset_value==0 else 0
        self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])          
        
        description = "Host Identifier"
        fid = 0x81
        supported = True if self.IdCtrl.ONCS.bit(5) == "1" else False
        capabilities=self.GetFeatureSupportedCapabilities(fid)
        reset_value=self.GetFeature(fid = fid)
        valid_value=1 if reset_value==0 else 0
        self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported])      
        
        description = "Reservation Notification Mask"
        fid = 0x82
        supported = True if self.IdNs.RESCAP.int !=0 else False
        capabilities=self.GetFeatureSupportedCapabilities(fid)
        reset_value=self.GetFeature(fid = fid)
        valid_value=2 if reset_value==0 else 0
        self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported]) 
        
        description = "Reservation Persistance"
        fid = 0x83
        supported = True if self.IdNs.RESCAP.int !=0 else False
        capabilities=self.GetFeatureSupportedCapabilities(fid)
        reset_value=self.GetFeature(fid = fid)
        valid_value=1 if reset_value==0 else 0
        self.TestItems.append([description, fid, capabilities, reset_value, valid_value, supported]) 
                    
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
                
    
    def GetFeatureValue(self, fid, cdw11=0, sel=0, nsid=1, nsSpec=False):
        Value=0 
        buf = self.get_feature(fid = fid, cdw11=cdw11, sel = sel, nsid = nsid, nsSpec=nsSpec) 
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
    
    
    def GetFeatureSupportedCapabilities(self, fid):
        if self.SELSupport:
            return self.GetFeature(fid=fid, sel=3)
        else:
            return -1
    
    def SetFeature(self, fid, value, sv, nsid=0):
        # if LBA range, create data structure for set feature command
        if fid==3:
            # Number of LBA Ranges is zero based, 0 means there is 1 LBA Range
            DS=self.CreateLBARangeDataStructure(value+1)
            return self.set_feature(fid = fid, value = value, SV = sv, nsid = nsid, Data=DS)
        elif fid==0xC:
            DS='\\x0\\x0\\x0\\x0\\x0\\x0\\x0\\x0'
            return self.set_feature(fid = fid, value = value, SV = sv, nsid = nsid, Data=DS)            
        else:
            return self.set_feature(fid = fid, value = value, SV = sv, nsid = nsid)
    
    def GetFeature(self, fid, sel=0, nsid=1):
        # if Interrupt Vector Configuration, read with cdw11=1
        if fid==3:
            return self.GetFeatureValue(fid=fid, sel=sel, nsid=nsid, nsSpec=True)
        if fid==9:
            return self.GetFeatureValue(fid=fid, sel=sel, cdw11=1, nsid=nsid, nsSpec=False)
        else:
            return self.GetFeatureValue(fid=fid, sel=sel, nsid=nsid, nsSpec=False)
    def DifferentValueFromCurrent(self, fid):
        currentValue = self.GetFeature(fid, sel=0)
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
    
    def CheckResult(self, OriginValue, CurrentValue, ExpectMatch):
    # if OriginValue = CurrentValue, and ExpectMatch = true,
    # or OriginValue != CurrentValue, and ExpectMatch = false, then pass
    
        
        self.Print ("Send get feature command, returned feature value: %s "%hex(CurrentValue))
        self.Print ("Check get feature value, expected value: %s (%s) "%( hex(OriginValue) if ExpectMatch else hex(CurrentValue), "changed" if ExpectMatch else "not changed" ))
        if CurrentValue == OriginValue and ExpectMatch == True:
            self.Print("PASS", "p")  
        elif CurrentValue != OriginValue and ExpectMatch == False:
            self.Print("PASS", "p") 
        else:
            self.Print("Fail", "f")
            self.ret_code=1              
    
    def VerifyNotSupport(self, mItem): 
        
        fid=mItem[item.fid]
        self.Print ("Not supported", "w")
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
        
             
    
    def VerifySaveAble(self, mItem):
        supported=mItem[item.supported]
        saveable=True if mItem[item.capabilities]&0b001 > 0 else False   
        nsSpec=True if mItem[item.capabilities]&0b010 > 0 else False
        changeable=True if mItem[item.capabilities]&0b100 > 0 else False        
        fid=mItem[item.fid]
        # get default value
        DefaultValue = self.GetFeature(fid, sel=1)        

        self.Print ("Feature is saveable in capabilities filed") if saveable else self.Print ("Feature is not saveable in capabilities filed")
        
        rdValue=self.GetFeature(fid, sel=2)
        SavedValuebk=rdValue    # backup saved value
        # choice one value that is not equal to saved value (valid_value, DefaultValue, reset_value)
        if rdValue!=mItem[item.valid_value]:
            value=mItem[item.valid_value]
        elif rdValue!=mItem[item.reset_value]:
            value=mItem[item.reset_value]
        else:
            value=DefaultValue
        
        self.Print ("Read saved value = %s"%hex(rdValue)                )
        self.Print ("Send set feature command with value = %s and SV field =1"%hex(value))
    
        # Send set feature command    
        self.SetFeature(fid, value, sv=1,nsid=1) if nsSpec else self.SetFeature(fid, value, sv=1)
        
        # Send get feature command    
        GetValue = self.GetFeature(fid, sel=2)              
        SavedValue =   GetValue            
        
        # check if (value is set if changeable=true) or  (value is not set if changeable=false) 
        self.CheckResult(OriginValue=value, CurrentValue=GetValue, ExpectMatch=saveable)   
        
        if saveable:
            self.Print ("Test Persistent Across Power Cycle and Reset")
            self.Print ("-- Issue Nvme Reset")
            self.nvme_reset()
            # Send get feature command    
            GetValue = self.GetFeature(fid, sel=2)                
            self.Print ("After reset, read feature saved value: %s "%hex(GetValue))
            self.Print ("Check if get feature saved value is %s or not "%hex(SavedValue))
            if GetValue == value:
                self.Print("PASS", "p")  
            else:
                self.Print("Fail", "f")
                self.ret_code=1 
            
            if self.DisablePwr:  
                self.Print ("-- User disable power off and power on test")
            else:
                self.Print ("-- Do power off and power on ")
                self.por_reset()
                sleep(0.5)
                # Send get feature command    
                GetValue = self.GetFeature(fid, sel=2)                
                self.Print ("After power on, read feature saved value: %s "%hex(GetValue))
                self.Print ("Check if get feature saved value is %s or not "%hex(SavedValue))
                if GetValue == value:
                    self.Print("PASS", "p")  
                else:
                    self.Print("Fail", "f")
                    self.ret_code=1                         
                                                                    
       
            value = SavedValuebk
            self.Print ("restore to previous 'saved value': %s"%hex(value))
            if int(value)==0:
                value = DefaultValue
                self.Print ("becouse previous 'saved value' =0, set 'saved value' to default value: %s"%hex(value))                        
            # Send set feature command    
            self.SetFeature(fid, value, sv=1,nsid=1) if nsSpec else self.SetFeature(fid, value, sv=1)  
            self.Print ("End of restore values")         
            self.Print (""                          )     
    
    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def __init__(self, argv):
        # initial new parser if need, -t -d -s -p was used, dont use it again
        self.SetDynamicArgs(optionName="x", optionNameFull="disablepwr", helpMsg="disable poweroff, ex. '-x 1'", argType=int)    
        self.SetDynamicArgs(optionName="n", optionNameFull="disableNsTest", helpMsg="disable namespace test, ex. '-n 1'", argType=int)        
        
        # initial parent class
        super(SMI_SetGetFeatureCMD, self).__init__(argv)
        
        # get new parser if need, where args order is the same with initial order
        self.DisablePwr = self.GetDynamicArgs(0)
        self.DisablePwr = True if self.DisablePwr==1 else False        
        self.disableNsTest = self.GetDynamicArgs(1)
        self.disableNsTest = True if self.disableNsTest==1 else False
          
        self.ret_code = 0
        self.Ns=1
        self.TestItems=[]
        self.SELSupport = True if self.IdCtrl.ONCS.bit(4)=="1" else False
        self.NsSupported=True if self.IdCtrl.OACS.bit(3)=="1" else False        

    
    # override
    def PreTest(self):
        if self.DisablePwr:
            self.Print ("User disable power off/on test", "f")     
        if self.disableNsTest:
            self.Print ("User disable namespace test", "f")  
        self.Print ("")    
        self.Print ("Issue nvme reset controller")
        self.nvme_reset()
        
        self.Print ("Check if Select field in Get Features - Command Dword 10 supported or not")
        self.Print ("")
        if self.SELSupport:
            self.Print("Supported", "p")    
            # initial self.TestItems
            self.initial()        
            self.Print("Test item 'Timestamp' is in script SMI_FeatureTimestamp ", "w")
            self.Print("Test item 'Keep Alive Timer' has not implemented ", "w")
            self.Print("Test item 'Number of Queues' has not implemented ", "w")
            return True
        else:
            self.Print("Not Supported", "f")     
            return False   
        
    # <sub item scripts>
    SubCase1TimeOut = 600
    SubCase1Desc = "Test all the attributes in Select field"        
    def SubCase1(self):
        self.ret_code=0
        
        for mItem in self.TestItems:
            self.Print ("==========================================================================")
            self.Print ( mItem[item.description]   )
            self.Print ("Feature ID: %s"%mItem[item.fid]   )
            supported=mItem[item.supported]
            saveable=True if mItem[item.capabilities]&0b001 > 0 else False   
            nsSpec=True if mItem[item.capabilities]&0b010 > 0 else False
            changeable=True if mItem[item.capabilities]&0b100 > 0 else False
            
            self.Print ("" )            
            self.Print ("Supported", "p") if supported else self.Print("Not supported", "w")
            self.Print ("Feature saveable: %s"%("Yes" if saveable else "No"))
            self.Print ("Feature namespace specific: %s"%("Yes" if nsSpec else "No"))
            self.Print ("Feature changeable: %s"%("Yes" if changeable else "No"))
            self.Print ("")            
            
            if not supported:
                self.VerifyNotSupport(mItem)
                              
            else:

                
                self.Print ("-(1)-- Test Get Features with Select=0, Current --"    )
                self.Print ("        and test Features capabilities bit 2, Feature Identifier is changeable or not")
                self.Print ("        "+ "Feature is changeable, all the fallowing test should change the value" if changeable else "Feature is no changeable, all the fallowing test should not change the value")
                fid=mItem[item.fid]
                rdValue=self.GetFeature(fid, sel=0)
                value=self.DifferentValueFromCurrent(fid)
                self.Print ("Send get feature command, returned feature value: %s "%hex(rdValue))
                self.Print ("Send set feature command with value = %s"%hex(value))
                
                # Send set feature command    
                self.SetFeature(fid, value, sv=0,nsid=1) if nsSpec else self.SetFeature(fid, value, sv=0)
                
                # Send get feature command    
                GetValue = self.GetFeature(fid, sel=0)
                
                # check if (value is set if changeable=true) or  (value is not set if changeable=false) 
                self.CheckResult(OriginValue=value, CurrentValue=GetValue, ExpectMatch=changeable)    
                self.Print ("")
    
                self.Print ("-(2)--  Test Get Features with Select=1, Default --"  )
                DefaultValue = self.GetFeature(fid, sel=1)
                self.Print ("Send get feature command with Select=1, returned feature default value: %s "%hex(DefaultValue))
                self.Print ("")
                
                self.Print ("-(3)--  Test Get Features with Select=2, Saved --"            )
                self.VerifySaveAble(mItem)
    
                self.Print ("-(4)--  Test Get Features if capabilities bit 1 = 1, namespace specific"        )
                if not nsSpec:
                    self.Print ("Feature is not namespace specific in capabilities filed")
                else:
                    self.Print ("Feature is namespace specificin in capabilities filed")
                    self.Print ("Test if Feature Identifier is namespace specific or not")
                    self.Print ("")
              
                    if not self.NsSupported:
                        self.Print ("Controller don't support mulit namespaces!, quit this test item")
                    elif not changeable:
                        self.Print ("Feature is not changeable!, quit this test item")
                    elif self.disableNsTest:
                        self.Print ("-- User disable namespace test for this feature")
                    else:
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
                            original1 = self.GetFeature(fid, sel=0, nsid=1)
                            original2 = self.GetFeature(fid, sel=0, nsid=2)
                            #self.Print ("Check if feature value = %s or not in all namespaces"%value                )
                            if original1 != value or original2!=value:
                                self.Print("Fail, value from ns1= %s ,ns2= %s "%(original1,original2), "f")
                                self.ret_code=1                     
                            else:
                                value = mItem[item.valid_value]
                                self.Print ("Set feature with nsid =1, value= %s"%value                    )
                                self.SetFeature(fid=fid, value=value, sv=0, nsid=1)
                                
                                current1 = self.GetFeature(fid, sel=0, nsid=1)
                                current2 = self.GetFeature(fid, sel=0, nsid=2)
                                
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
                                original1 = self.GetFeature(fid, sel=0, nsid=1)
                                original2 = self.GetFeature(fid, sel=0, nsid=2)  
                                   
                                value = mItem[item.valid_value]               
                                self.Print ("Set feature with nsid =2, value= %s"%value                    )
                                self.SetFeature(fid=fid, value=value, sv=0, nsid=2)
                                
                                current1 = self.GetFeature(fid, sel=0, nsid=1)
                                current2 = self.GetFeature(fid, sel=0, nsid=2)
                                
                                self.Print ("Get feature values from ns1= %s ,ns2= %s "%(current1,current2)                 )
                                self.Print ("Check if feature value from ns1 = %s and value from ns2 = %s "   %(value,original2)   )
                                
                                if current1==original1 and current2==value:
                                    self.Print("PASS", "p")  
                                else:
                                    self.Print("Fail", "f")
                                    self.ret_code=1         
                self.Print ("")        
                self.Print ("-(5)--  Test Set Features if capabilities bit 2 = 0, Feature Identifier is not changeable"        )
                if changeable:
                    self.Print( "Feature Identifier is changeable, quit" )
                else:
                    self.Print( "Feature Identifier is not changeable" )
                    self.Print ("Send set feature command with value = %s"%hex(value))                    
                    # Send set feature command    
                    CMD_Result = self.SetFeature(fid, value, sv=0,nsid=1) if nsSpec else self.SetFeature(fid, value, sv=0)
                    self.Print ("Check set feature command status code, expected code: FEATURE_NOT_CHANGEABLE")
                    if re.search("FEATURE_NOT_CHANGEABLE", CMD_Result):  
                        self.Print("PASS", "p")  
                    else:
                        self.Print("Fail", "f")
                        self.ret_code=1                                    
                
                self.Print ("") 
                self.Print ("-(6)--  Restore values")     
                
                value=mItem[item.reset_value]
                self.Print ("restore to previous 'current value': %s"%hex(value))
                # Send set feature command    
                self.SetFeature(fid, value, sv=0,nsid=1) if nsSpec else self.SetFeature(fid, value, sv=0)
                                


        if self.Ns!=1:
            self.ResetNS()
            
        return self.ret_code

    # </sub item scripts>
    
    
    
    
if __name__ == "__main__":
    DUT = SMI_SetGetFeatureCMD(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 
    
    
    
    
    
