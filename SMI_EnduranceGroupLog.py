#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
# Import VCT modules
from lib_vct.NVME import NVME

from ctypes import *

# define EnduranceGroupLog structure
class EGLStructure(Structure):
    def __init__(self, NVMEinst):
        # save to mNVME
        self.mNVME = NVMEinst        
        # set default value according to spec.
        self.ElementValue=" " *128 # all string to space(ASCII 20h).
        self.NumberofMetadataElementDescriptors = 1 # always is 1
        self.SetFeature_CDW11_ElementAction = 0 # for set cmd
        self.GetFeature_CDW11_ElementType = 0  # for get cmd
        self.CDW10_SV = 0
    _pack_=1
    _fields_=[
            ('CriticalWarning',c_ubyte * 1),
            ('Reserved_2_1',c_ubyte * 2),
            ('AvailableSpare',c_ubyte * 1),
            ('AvailableSpareThreshold',c_ubyte * 1),
            ('PercentageUsed',c_ubyte * 1),
            ('Reserved_31_6',c_ubyte * 26),
            ('EnduranceEstimate',c_ubyte * 16),
            ('DataUnitsRead',c_ubyte * 16),
            ('DataUnitsWritten',c_ubyte * 16),
            ('MediaUnitsWritten',c_ubyte * 16),
            ('HostReadCommands',c_ubyte * 16),
            ('HostWriteCommands',c_ubyte * 16),
            ('MediaandDataIntegrityErrors',c_ubyte * 16),
            ('NumberofErrorInformationLogEntries',c_ubyte * 16),
            ('Reserved_511_160',c_ubyte * 352)]  
  
    # handle get value, i.e. warpe ByteListToLongInt whe get value in _fields_
    def __getattribute__(self, key):
        # if in _fields_, wrape with ByteListToLongInt
        for  item in EGLStructure._fields_:
            name = item[0]
            if name==key:
                v = super(EGLStructure, self).__getattribute__(key)
                v = self.mNVME.ByteListToLongInt(v) # wrape
                return v
        return super(EGLStructure, self).__getattribute__(key)
    
    def hexdumpEGLStructure(self):
        mStr = string_at(addressof(self),sizeof(self))
        mStr = self.mNVME.hexdump(src=mStr)
        return  mStr

    def IssueGetFeatureCMD(self):
    # return true/false
        rawDataList = self.mNVME.get_log_passthru(LID=0x9, size=512) # e.x.rawDataList = ["ab", "1d"]
        if rawDataList ==None:
            self.mNVME.Print("Get feature cmd fail, CMD: %s"%self.LastCmd,"f")
            return False
        # convert hex to string
        cc =rawDataList[3]
        mStr = self.mNVME.HexListToStr(rawDataList)
        # ctypes.memmove(dst, src, count), copies count bytes from src to dst.
        if sizeof(self) != len(rawDataList):
            self.mNVME.Print("Error!, structure size: %s, getfeature rawData size: %s"%(sizeof(self), len(rawDataList)), "f")
            return False
        memmove(addressof(self),mStr,sizeof(self))        
        return True



class SMI_EnduranceGroupLog(NVME):
    ScriptName = "SMI_EnduranceGroupLog.py"
    Author = "Sam"
    Version = "20210506"
    
    def getENDGID(self, ns):
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x0 --namespace-id=%s 2>&1"%(self.dev_port, ns)
        rTDS=self.shell_cmd(CMD)
        DS=self.AdminCMDDataStrucToListOrString(rTDS, 2)            
        if DS==None:
            return None
        else:
            return (DS[103]<<8) + DS[102]        

    def getEGL(self, ns):
        self.get_log_passthru(LID=0x9, size=512,ReturnType=2)
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x0 --namespace-id=%s 2>&1"%(self.dev_port, ns)
        rTDS=self.shell_cmd(CMD)
        DS=self.AdminCMDDataStrucToListOrString(rTDS, 2)            
        if DS==None:
            return None
        else:
            return (DS[103]<<8) + DS[102]   

    def PrintAlignString(self,S0="", S1="", S2="", S3="", S4="", S5="", PF="default"):            
        mStr = "{:<16}{:<16}{:<34}{:<16}{:<24}{:<34}".format(S0, S1, S2, S3, S4,S5 )
        if PF=="pass":
            self.Print( mStr , "p")        
        elif PF=="fail":
            self.Print( mStr , "f")      
        else:
            self.Print( mStr )  
    
    def Verify1BillionReadWrite(self, rw):
    # rw: read/write
    # 1G = 1 billion
        CMD = "fio --direct=1 --iodepth=16 --ioengine=libaio --bs=64k --rw=%s --numjobs=1 --size=100M --filename=%s --name=mtest"\
        %(rw, self.dev)
        value_old = self.GetLog.EnduranceGroupLog.DataUnitsRead if rw=="read" else self.GetLog.EnduranceGroupLog.DataUnitsWritten
        isPass=False
        if rw=="read":
            self.Print("Try to read 100M bytes for 10 times, if DataUnitsRead+1, skip read command")
        else:
            self.Print("Try to write 100M bytes for 10 times, if DataUnitsWrite+1, skip write command")
        self.Print("Current value %s"%value_old)
        for cnt in range(10):
            self.shell_cmd(CMD)
            value_curr = self.GetLog.EnduranceGroupLog.DataUnitsRead if rw=="read" else self.GetLog.EnduranceGroupLog.DataUnitsWritten
            if rw=="read":
                self.PrintAlignString(cnt+1, "read 100M", "DataUnitsRead: %s"%value_curr)
            else:
                self.PrintAlignString(cnt+1, "write 100M", "DataUnitsWrite: %s"%value_curr)
            if value_curr == value_old+1:
                self.Print("%s th, value+1, skip"%(cnt+1), "p")
                isPass = True
                break
        self.Print("")    
        if not isPass:
            if rw=="read":
                self.Print("Fail, After read 100M bytes x 10 data, DataUnitsRead has not changed ", "f")
            else:
                self.Print("Fail, After write 100M bytes x 10 data, DataUnitsWrite has not changed ", "f")
            if value_curr==0:
                self.Print("Current value = 0, A value of 0h indicates that the controller does not report the number of Data Units Read/Data Units Written")
                return True
            else:
                return False
        else:
            if rw=="read":
                self.Print("Try to read 100M bytes for 10 times, if DataUnitsRead+1 at 9th or 10th, pass the test")
            else:
                self.Print("Try to write 100M bytes for 10 times, if DataUnitsWrite+1 at 9th or 10th, pass the test")
            value_old = self.GetLog.EnduranceGroupLog.DataUnitsRead if rw=="read" else self.GetLog.EnduranceGroupLog.DataUnitsWritten
            self.Print("Current value %s"%value_old)
            for cnt in range(10):
                self.shell_cmd(CMD)
                value_curr = self.GetLog.EnduranceGroupLog.DataUnitsRead if rw=="read" else self.GetLog.EnduranceGroupLog.DataUnitsWritten
                if rw=="read":
                    self.PrintAlignString(cnt+1, "read 100M", "DataUnitsRead: %s"%value_curr)
                else:
                    self.PrintAlignString(cnt+1, "write 100M", "DataUnitsWrite: %s"%value_curr)
                if value_curr == value_old+1:
                    break 
            self.Print("") 
            if cnt ==9 or cnt==8:
                if rw=="read":
                    self.Print("After read 100M bytes x %s, DataUnitsRead changed"%(cnt+1), "p")  
                else:
                    self.Print("After write 100M bytes x %s, DataUnitsWrite changed"%(cnt+1), "p")  
                self.Print("I.E. This value is reported in billions")  
                return True  
            else:
                self.Print("Fail", "f")
                return False
            
    
    def __init__(self, argv):
        self.SetDynamicArgs(optionName="PUS100", optionNameFull="PUS100", \
                            helpMsg="PercentageUsedScale for case 16 that will set PercentageUsed to 100"
                            "\ne.x for SKH, formula of PercentageUsed in SMART log is"\
                            "\n(sum of all block erase count/total erase block)/7000"\
                            "\nso run script with '-PUS100 7000'", argType=int, default=7000)          
        # initial parent class
        super(SMI_EnduranceGroupLog, self).__init__(argv)
        
        self.PUS100 = self.GetDynamicArgs(0)
        
        self.EGsupported = True if self.IdCtrl.CTRATT.bit(4)=="1" else False
        self.ENDGID = 0
        self.NsSupported=True if self.IdCtrl.OACS.bit(3)=="1" else False

    # define pretest, if not return 0 , skip all subcases
    def PreTest(self):      
        self.Print("Check if controller support endurance group in Identify Controller Data Structure -> Controller Attributes (CTRATT) -> bit 4")
        if self.EGsupported:
            self.Print("Supported", "p")
        else:
            self.Print("Not supported, skip all test cases!", "w")
            return 255 
        self.Print("Check if ENDGID in id-ns data structure in nsid=1 is not 0x0") 
        self.ENDGID = self.getENDGID(ns=1)
        if self.ENDGID == None:
            self.Print("Can not get id-ns data structure", "f")
            return 1
        self.Print("ENDGID: 0x%X"%self.ENDGID) 
        if self.ENDGID == 0:
            self.Print("Fail", "f")
            return 1
        else:
            self.Print("Pass", "p")
        
        self.Print("")    
        self.Print("Following test will set EnduranceGroupIdentifier to %s "%self.ENDGID)
        self.GetLog.EnduranceGroupLog.SetEnduranceGroupIdentifierInCDW11(self.ENDGID)
        return 0       

    # <define sub item scripts>
    SubCase1TimeOut = 6000
    SubCase1Desc = "[Read only mode] Test field: Critical_Warning"   
    SubCase1KeyWord = ""
    def SubCase1(self):
        ret_code=0
        
        mEGL = EGLStructure(self)
        if not mEGL.IssueGetFeatureCMD():
            self.Print("CMD fail!","f")
            return 1     

        print mEGL.CriticalWarning
        print mEGL.Reserved_2_1
        print mEGL.AvailableSpare
        print mEGL.AvailableSpareThreshold
        print mEGL.PercentageUsed
        print mEGL.Reserved_31_6
        print mEGL.EnduranceEstimate
        print mEGL.DataUnitsRead
        print mEGL.DataUnitsWritten
        print mEGL.MediaUnitsWritten
        print mEGL.HostReadCommands
        print mEGL.HostWriteCommands
        print mEGL.MediaandDataIntegrityErrors
        print mEGL.NumberofErrorInformationLogEntries
        print mEGL.Reserved_511_160
        return 0
        
        if not self.mIKNOWWHATIAMDOING:
            self.Print ("Please run script with option '-iknowwhatiamdoing', it will make DUT into RO mode")
            return 0 
       
        mEGL = EGLStructure(self)
        if not mEGL.IssueGetFeatureCMD():
            self.Print("CMD fail!","f")
            return 1     
        CriticalWarning_old = self.ByteListToLongInt(mEGL.CriticalWarning)
        self.Print ("Current CriticalWarning: 0x%X"%CriticalWarning_old)      
        
        self.Print ("")
        self.Print ("Issue VU CMD to set DUT in Read only mode ")
        if not self.setReadOnlyMode(): 
            self.Print ("Set Read only mode fail", "f")
            return 1
        self.Print ("Done")
        
        self.Print ("")
        mEGL = EGLStructure(self)
        if not mEGL.IssueGetFeatureCMD():
            self.Print("CMD fail!","f")
            return 1     
        CriticalWarning_new = self.ByteListToLongInt(mEGL.CriticalWarning)
        self.Print ("Current CriticalWarning: 0x%X"%CriticalWarning_new)
        
        self.Print ("Check if read only mode")     

        
        print self.ByteListToLongInt(mEGL.CriticalWarning)
        print self.ByteListToLongInt(mEGL.Reserved_2_1)
        print self.ByteListToLongInt(mEGL.AvailableSpare)
        print self.ByteListToLongInt(mEGL.AvailableSpareThreshold)
        print self.ByteListToLongInt(mEGL.PercentageUsed)
        print self.ByteListToLongInt(mEGL.Reserved_31_6)
        print self.ByteListToLongInt(mEGL.EnduranceEstimate)
        print self.ByteListToLongInt(mEGL.DataUnitsRead)
        print self.ByteListToLongInt(mEGL.DataUnitsWritten)
        print self.ByteListToLongInt(mEGL.MediaUnitsWritten)
        print self.ByteListToLongInt(mEGL.HostReadCommands)
        print self.ByteListToLongInt(mEGL.HostWriteCommands)
        print self.ByteListToLongInt(mEGL.MediaandDataIntegrityErrors)
        print self.ByteListToLongInt(mEGL.NumberofErrorInformationLogEntries)
        print self.ByteListToLongInt(mEGL.Reserved_511_160)
        return ret_code


    SubCase2TimeOut = 4000
    SubCase2Desc = "Test 'Percentage Used' by VU command"      
    def SubCase2(self):
        ret_code=0

        self.Print("Check if Controller accept UV CMD")
        if not self.setPE(cdw13_PE=0):
            self.Print("Controller do not accept UV CMD: %s"%self.LastCmd, "f")
            self.Print("Warnning!, skip", "w")
            return 255
        else:
            self.Print("Pass", "p")
            
        self.Print("")
        self.Print("PercentageUsedScale: %s"%self.PUS100)
        self.Print("I.E. %s PE( for all blocks ) will set PercentageUsedScale to 100"%self.PUS100)
        PUS=self.PUS100/100
        self.Print("%s PE( for all blocks ) will set PercentageUsedScale to 1"%PUS)
        self.Print("Make PercentageUsedScale to 255 need %s PE ((PercentageUsedScale/100)*255)"%(PUS*255))
        self.Print("")

        self.PrintAlignString("PE", "PercentageUsed")
        self.Print("--------------------------------------------------------------------------------------------------------")
        value_curr = 0
        value_last = 0
        ispass = True   
        for PE in range(0x0, PUS*260, PUS):
            self.setPE(cdw13_PE=PE)
            # get value 
            value_curr = self.GetLog.EnduranceGroupLog.CriticalWarning          
            
            pf = "pass" if value_curr>=value_last else "fail"
            if pf == "fail":
                ispass = False
            self.PrintAlignString(S0 = "0x%X"%PE, S1 = value_curr)
            value_last = value_curr
            
        self.Print("--------------------------------------------------------------------------------------------------------")
        self.Print("")
                    
        self.Print("Check if PercentageUsed counting up")
        if ispass:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            ret_code = 1
            
        self.Print("")
        self.Print("Reset PE to 0")
        if self.setPE(cdw13_PE=0):            
            self.Print("Done", "p")
        else:
            self.Print("Fail", "f")
            ret_code = 1
            
        return ret_code
            


    # </define sub item scripts>

    # define PostTest  

    SubCase3TimeOut = 4000
    SubCase3Desc = "Test 'Data_Units_Read"      
    def SubCase3(self):
        ret_code=0      
        if self.NsSupported:
            self.Print("Multi ns supported")
        else:
            self.Print("Multi ns not supported")
        DUR_old = self.GetLog.EnduranceGroupLog.DataUnitsRead   
        if not self.NsSupported:
            self.Print("Current Data_Units_Read in EnduranceGroupLog: %s"%DUR_old)
            if not self.Verify1BillionReadWrite("read"):
                ret_code=1
        return ret_code
   
    SubCase4TimeOut = 4000
    SubCase4Desc = "Test 'Data_Units_Read"      
    def SubCase4(self):
        ret_code=0      
        if self.NsSupported:
            self.Print("Multi ns supported")
        else:
            self.Print("Multi ns not supported")
        DUR_old = self.GetLog.EnduranceGroupLog.DataUnitsWritten   
        if not self.NsSupported:
            self.Print("Current Data_Units_Read in EnduranceGroupLog: %s"%DUR_old)
            if not self.Verify1BillionReadWrite("write"):
                ret_code=1
        return ret_code   
   
    
    def PostTest(self): 
        return True
            
     


if __name__ == "__main__":
    DUT = SMI_EnduranceGroupLog(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    