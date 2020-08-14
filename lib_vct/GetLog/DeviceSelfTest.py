'''
Created on Oct 5, 2018

@author: root
'''
from lib_vct.NVMECom import NVMECom


class SelfTestResultDataStructure_Descriptor(object,NVMECom):  
# Self-test Result Data Structure    
    def __init__(self,obj, WhichNumber):
        # WhichNumber from 1 to 20
        # DataStructureOffset in get log page- device self test log
        self.DataStructureOffset = 4+(WhichNumber-1)*28
        self._mNVME = obj    
        # init NVMECom
        NVMECom.__init__(self, obj) 
        self.RecordCmdToLogFile = True         
        self._LogPageOffsetSupport = True if self._mNVME.IdCtrl.LPA.bit(2)=="1" else False
    
    def GetDataInInt(self, startbyte, stopbyte):
        # return int
        SRDS=""
        # if Log Page Offset fields in  get log command is not support, then read all and get substring from DataStructureOffset*2
        if self._LogPageOffsetSupport:
            SRDS = self.get_log_passthru(0x6, 28, 0, 0, self.DataStructureOffset, 1)
        else:
            buf = self.get_log_passthru(0x6, 28+self.DataStructureOffset, 0, 0, 0, 1)
            SRDS = buf[self.DataStructureOffset*2:]
            
        data_in_str = SRDS[startbyte*2 : (stopbyte+1)*2]
        return self.str2int(data_in_str)
    
    @property
    def DeviceSelfTestStatus(self):
    # return int
        return self.GetDataInInt(0, 0)   
    
    @property
    def SegmentNumber(self):
    # return int    
        return self.GetDataInInt(1, 1)

    @property
    def ValidDiagnosticInformation(self):
    # return int    
        return self.GetDataInInt(2, 2)
    
    @property
    def PowerOnHours(self):
    # return int    
        return self.GetDataInInt(4, 11) 
    
    @property
    def NamespaceIdentifier(self):
    # return int    
        return self.GetDataInInt(12, 15) 
        
    @property
    def FailingLBA(self):
    # return int    
        return self.GetDataInInt(16, 23)
    
    @property
    def StatusCodeType(self):
    # return int    
        return self.GetDataInInt(24, 24) 
    
    @property
    def StatusCode(self):
    # return int    
        return self.GetDataInInt(25, 25)
     





class DeviceSelfTest_(object, NVMECom):
    
    @property
    def CDSTO(self):
        # Current Device Self-Test Operation
        # ret int
        return self._mNVME.str2int(self._mNVME.get_log(0x6, 20)[0:2])
    @property
    def CDSTC(self):
        # Current Device Self-Test Completion
        # ret int
        return self._mNVME.str2int(self._mNVME.get_log(0x6, 20)[2:4])    
            
    def __init__(self, obj):
        self._mNVME = obj    
        # init NVMECom
        #NVMECom.__init__(self, obj)
        self.TestResultDataStructure_1th=SelfTestResultDataStructure_Descriptor(obj, 1)
        self.TestResultDataStructure_2th=SelfTestResultDataStructure_Descriptor(obj, 2)
        self.TestResultDataStructure_3th=SelfTestResultDataStructure_Descriptor(obj, 3)
        self.TestResultDataStructure_4th=SelfTestResultDataStructure_Descriptor(obj, 4)
        self.TestResultDataStructure_5th=SelfTestResultDataStructure_Descriptor(obj, 5)
        self.TestResultDataStructure_6th=SelfTestResultDataStructure_Descriptor(obj, 6)
        self.TestResultDataStructure_7th=SelfTestResultDataStructure_Descriptor(obj, 7)
        self.TestResultDataStructure_8th=SelfTestResultDataStructure_Descriptor(obj, 8)
        self.TestResultDataStructure_9th=SelfTestResultDataStructure_Descriptor(obj, 9)
        self.TestResultDataStructure_10th=SelfTestResultDataStructure_Descriptor(obj, 10)
        self.TestResultDataStructure_11th=SelfTestResultDataStructure_Descriptor(obj, 11)
        self.TestResultDataStructure_12th=SelfTestResultDataStructure_Descriptor(obj, 12)
        self.TestResultDataStructure_13th=SelfTestResultDataStructure_Descriptor(obj, 13)
        self.TestResultDataStructure_14th=SelfTestResultDataStructure_Descriptor(obj, 14)
        self.TestResultDataStructure_15th=SelfTestResultDataStructure_Descriptor(obj, 15)
        self.TestResultDataStructure_16th=SelfTestResultDataStructure_Descriptor(obj, 16)
        self.TestResultDataStructure_17th=SelfTestResultDataStructure_Descriptor(obj, 17)
        self.TestResultDataStructure_18th=SelfTestResultDataStructure_Descriptor(obj, 18)
        self.TestResultDataStructure_19th=SelfTestResultDataStructure_Descriptor(obj, 19)
        self.TestResultDataStructure_20th=SelfTestResultDataStructure_Descriptor(obj, 20)
    

     
    




















    