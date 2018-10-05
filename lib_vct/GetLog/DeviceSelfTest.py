'''
Created on Oct 5, 2018

@author: root
'''
from lib_vct.NVMECom import NVMECom


class SelfTestResultDataStructure_Descriptor(object,NVMECom):  
# Self-test Result Data Structure    
    def __init__(self, WhichNumber):
        # WhichNumber from 1 to 20
        # DataStructureOffset in get log page- device self test log
        self.DataStructureOffset = 4+(WhichNumber-1)*28
    
    def GetDataInInt(self, startbyte, stopbyte):
        # return int
        SRDS = self.get_log_passthru(0x6, 28, 0, 0, self.DataStructureOffset, 1)
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
        return self.str2int(self.get_log(0x6, 20)[0:2])
    @property
    def CDSTC(self):
        # Current Device Self-Test Completion
        # ret int
        return self.str2int(self.get_log(0x6, 20)[2:4])    
    
    TestResultDataStructure_1th=SelfTestResultDataStructure_Descriptor(1)
    TestResultDataStructure_2th=SelfTestResultDataStructure_Descriptor(2)
    TestResultDataStructure_3th=SelfTestResultDataStructure_Descriptor(3)
    TestResultDataStructure_4th=SelfTestResultDataStructure_Descriptor(4)
    TestResultDataStructure_5th=SelfTestResultDataStructure_Descriptor(5)
    TestResultDataStructure_6th=SelfTestResultDataStructure_Descriptor(6)
    TestResultDataStructure_7th=SelfTestResultDataStructure_Descriptor(7)
    TestResultDataStructure_8th=SelfTestResultDataStructure_Descriptor(8)
    TestResultDataStructure_9th=SelfTestResultDataStructure_Descriptor(9)
    TestResultDataStructure_10th=SelfTestResultDataStructure_Descriptor(10)
    TestResultDataStructure_11th=SelfTestResultDataStructure_Descriptor(11)
    TestResultDataStructure_12th=SelfTestResultDataStructure_Descriptor(12)
    TestResultDataStructure_13th=SelfTestResultDataStructure_Descriptor(13)
    TestResultDataStructure_14th=SelfTestResultDataStructure_Descriptor(14)
    TestResultDataStructure_15th=SelfTestResultDataStructure_Descriptor(15)
    TestResultDataStructure_16th=SelfTestResultDataStructure_Descriptor(16)
    TestResultDataStructure_17th=SelfTestResultDataStructure_Descriptor(17)
    TestResultDataStructure_18th=SelfTestResultDataStructure_Descriptor(18)
    TestResultDataStructure_19th=SelfTestResultDataStructure_Descriptor(19)
    TestResultDataStructure_20th=SelfTestResultDataStructure_Descriptor(20)
    

     
    




















    