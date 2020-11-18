#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
# Import VCT modules
from lib_vct.NVME import NVME

class SMI_PersistentEventLog(NVME):
    ScriptName = "SMI_PersistentEventLog.py"
    Author = ""
    Version = "20201118"
    
    # PersistentEventLogHeader
    class PELH():
        LogIdentifier = None
        TNEV = None
        TLL = None
        LogRevision = None
        LogHeaderLength = None
        Timestamp = None
        POH = None
        PowerCycleCount = None
        VID = None
        SSVID = None
        SN = None
        MN = None
        SUBNQN = None
        SupportedEventsBitmap = None        
    
    def GetBytes(self, listRawData, stopByteOffet, startByteOffet):
    # return value of specific offset in listRawData
    # ex, listRawData = [1, 2, 3, 4, 5, 6], GetBytes(listRawData, 3, 1), return 2<<0 + 3<<8 + 4<<(8*2)
        value = 0
        x256 = 0
        for i in range(startByteOffet, stopByteOffet+1):
            value = value + (int(listRawData[i])<<(x256 * 8))
            x256 += 1
        return value
    
    def ParserPersistentEventLogHeader(self, listRawData):
    # note: listRawData is list type with string element
        mLen = len(listRawData)
        if mLen!=512:
            self.Print("ParserPersistentEventLogHeader: header size not correct, expect 512byte, current = %s"%len)
            return False
        
        self.PELH.LogIdentifier=self.GetBytes(listRawData, 0, 0)
        self.PELH.TNEV=self.GetBytes(listRawData, 7, 4)
        self.PELH.TLL=self.GetBytes(listRawData, 15, 8)
        self.PELH.LogRevision=self.GetBytes(listRawData, 16, 16)
        self.PELH.LogHeaderLength=self.GetBytes(listRawData, 19, 18)
        self.PELH.Timestamp=self.GetBytes(listRawData, 27, 20)
        self.PELH.POH=self.GetBytes(listRawData, 43, 28)
        self.PELH.PowerCycleCount=self.GetBytes(listRawData, 51, 44)
        self.PELH.VID=self.GetBytes(listRawData, 53, 52)
        self.PELH.SSVID=self.GetBytes(listRawData, 55, 54)
        self.PELH.SN=self.GetBytes(listRawData, 75, 56)
        self.PELH.MN=self.GetBytes(listRawData, 115, 76)
        self.PELH.SUBNQN=self.GetBytes(listRawData, 371, 116)
        self.PELH.SupportedEventsBitmap=self.GetBytes(listRawData, 511, 480)     
        return True

    
    def __init__(self, argv):
        # initial parent class
        super(SMI_PersistentEventLog, self).__init__(argv)
        
        
        # Command Dword 10 – Log Specific Field
        self.LSF_ReadLogData = 0 <<8
        self.LSF_EstablishContextAndReadLogData = 1 <<8
        self.LSF_ReleaseContext = 2 <<8
        
        
        
        
        
        
        

    # define pretest, if not return 0 , skip all subcases
    def PreTest(self):     
        PersistentEventLogSupported = True if self.IdCtrl.LPA.bit(4)=="1" else False
        self.Print("Persistent Event log was supported(IdCtrl.LPA.bit(4)): %s"%("Yes" if PersistentEventLogSupported else "No"))
        return 0
        return 0 if PersistentEventLogSupported else 255
                   

    # <define sub item scripts>
    SubCase1TimeOut = 600
    SubCase1Desc = ""   
    SubCase1KeyWord = "Parser Current Persistent Event log"
    def SubCase1(self):
        ret_code=0
        
        self.Print("Issue cmd with ReleaseContext=1 in Log Specific Field(cdw10) to clear current Persistent Event log")
        LSF = self.LSF_ReleaseContext
        result = self.get_log_passthru(LID=0x1, size=512, LSP=LSF, LPO=0)        # 0xD
        if result==None:
            self.Print("Command fail, CMD: %s"%self.LastCmd, "f") 
            mStr = self.shell_cmd(self.LastCmd)
            self.Print(mStr)
            return 1

        self.Print("Issue cmd with EstablishContextAndReadLogData=1 in Log Specific Field to create context and get log data")
        LSF = self.LSF_EstablishContextAndReadLogData
        resultStrList = self.get_log_passthru(LID=0x1, size=512, LSP=LSF, LPO=0)        # 0xD
        if resultStrList==None:
            self.Print("Command fail, CMD: %s"%self.LastCmd, "f") 
            mStr = self.shell_cmd(self.LastCmd)
            self.Print(mStr)
            return 1

        self.ParserPersistentEventLogHeader(resultStrList)
        
        self.PrintClass(self.PELH)

        
        return ret_code

    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_PersistentEventLog(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    