#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
# Import VCT modules
from lib_vct.NVME import NVME

# define AA_SecurityEventLog structure
from ctypes import *
class SecurityEventLog_(Structure):
    def __init__(self, NVMEinst):
        # save to mNVME
        self.mNVME = NVMEinst      
    _pack_=1
    _fields_=[
            ('Failuretoauthenticatefirmware',c_ubyte * 8), # QWORD
            ('AuthorizedaccessofVendorSpecificcommandordiagnosticport',c_ubyte * 8),
            ('UnauthorizedaccessofVendorSpecificcommandordiagnosticport',c_ubyte * 8),
            ('AttempttodownloadSEDfirmwaretoanon_SEDdevice',c_ubyte * 8),
            ('Attempttodownloadnon_SEDfirmwaretoanSEDdevice',c_ubyte * 8),
            ('Attempttodownloadnon_AAfirmwaretoAAdevice',c_ubyte * 8),
            ('FailuretoSecureErase',c_ubyte * 8),
            ('FailuretoSanitize',c_ubyte * 8),
            ('Totalnumberofeventsrecorded',c_ubyte * 8),
            ('TimeStamp',c_ubyte * 8),
            ('Reserved',c_ubyte * 432)]
    
    # handle get value, i.e. issue get commmand and warpe ByteListToLongInt when get value in _fields_
    def __getattribute__(self, key):
        # if in _fields_, wrape with ByteListToLongInt
        for  item in SecurityEventLog_._fields_:
            name = item[0]
            if name==key:
                # start
                if not self.IssueGetFeatureCMD():
                    print "IssueGetFeatureCMD fail"
                    return 0                
                v = super(SecurityEventLog_, self).__getattribute__(key)
                v = self.mNVME.ByteListToLongInt(v) # wrape
                return v
        return super(SecurityEventLog_, self).__getattribute__(key)      
    
    def hexdumpSecurityEventLog_(self):
        mStr = string_at(addressof(self),sizeof(self))
        mStr = self.mNVME.hexdump(src=mStr)
        return  mStr

    def IssueGetFeatureCMD(self):
    # return true/false
        rawDataList = self.mNVME.get_log_passthru(LID=0xC7, size=512) # e.x.rawDataList = ["ab", "1d"]
        if rawDataList ==None:
            self.mNVME.Print("Get feature cmd fail, CMD: %s"%self.mNVME.LastCmd,"f")
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
    
class SMI_HP_SecurityEventLog(NVME):
    ScriptName = "SMI_HP_SecurityEventLog.py"
    Author = ""
    Version = ""
    
    def __init__(self, argv):
        # initial parent class
        super(SMI_HP_SecurityEventLog, self).__init__(argv)
        
        self.SecurityEventLog = SecurityEventLog_(self)

    # define pretest  
    def PreTest(self):        
        return True            

    # <define sub item scripts>
    SubCase1TimeOut = 60
    SubCase1Desc = ""   
    SubCase1KeyWord = ""
    def SubCase1(self):
        ret_code=0
        self.Print("%s"%self.SecurityEventLog.Failuretoauthenticatefirmware)
        self.Print("%s"%self.SecurityEventLog.AuthorizedaccessofVendorSpecificcommandordiagnosticport)
        self.Print("%s"%self.SecurityEventLog.UnauthorizedaccessofVendorSpecificcommandordiagnosticport)
        self.Print("%s"%self.SecurityEventLog.AttempttodownloadSEDfirmwaretoanon_SEDdevice)
        self.Print("%s"%self.SecurityEventLog.Attempttodownloadnon_SEDfirmwaretoanSEDdevice)
        self.Print("%s"%self.SecurityEventLog.Attempttodownloadnon_AAfirmwaretoAAdevice)
        self.Print("%s"%self.SecurityEventLog.FailuretoSecureErase)
        self.Print("%s"%self.SecurityEventLog.FailuretoSanitize)
        self.Print("%s"%self.SecurityEventLog.Totalnumberofeventsrecorded)
        self.Print("%s"%self.SecurityEventLog.TimeStamp)
        
        
        
        return ret_code

    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_HP_SecurityEventLog(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    

    
    