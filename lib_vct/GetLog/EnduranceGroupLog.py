'''
Created on May 30, 2021

@author: root
'''
from ctypes import *
# define EnduranceGroupLog structure
class EnduranceGroupLog_(Structure):
    def __init__(self, NVMEinst):
        # save to mNVME
        self.mNVME = NVMEinst      
        self.ID=0  # EnduranceGroupIdentifier

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
    
    # handle get value, i.e. issue get commmand wand warpe ByteListToLongInt when get value in _fields_
    def __getattribute__(self, key):
        # if in _fields_, wrape with ByteListToLongInt
        for  item in EnduranceGroupLog_._fields_:
            name = item[0]
            if name==key:
                # start
                if not self.IssueGetFeatureCMD():
                    return 0                
                v = super(EnduranceGroupLog_, self).__getattribute__(key)
                v = self.mNVME.ByteListToLongInt(v) # wrape
                return v
        return super(EnduranceGroupLog_, self).__getattribute__(key)      
    
    def hexdumpEnduranceGroupLog_(self):
        mStr = string_at(addressof(self),sizeof(self))
        mStr = self.mNVME.hexdump(src=mStr)
        return  mStr

    def SetEnduranceGroupIdentifierInCDW11(self, ID):
        self.ID = ID

    def IssueGetFeatureCMD(self):
    # return true/false
        rawDataList = self.mNVME.get_log_passthru(LID=0x9, size=512, LSI=self.ID) # e.x.rawDataList = ["ab", "1d"]
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






        
        
        