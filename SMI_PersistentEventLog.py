#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
# Import VCT modules
from lib_vct.NVME import NVME
from lib_vct.NVMECom import OrderedAttributeClass

    
class SMI_PersistentEventLog(NVME):
    ScriptName = "SMI_PersistentEventLog.py"
    Author = ""
    Version = "20201118"
    
    def getPELHvalue(self, name):
        for i in range(len(self.PELH)):
            if name == self.PELH[i][0]:
                return self.PELH[i][1]
        return None
    
    class PELH_(OrderedAttributeClass):
        
        LogIdentifier = OrderedAttributeClass.MyOrderedField()
        TNEV = OrderedAttributeClass.MyOrderedField()
        TLL = OrderedAttributeClass.MyOrderedField()
        LogRevision = OrderedAttributeClass.MyOrderedField()
        LogHeaderLength = OrderedAttributeClass.MyOrderedField()
        Timestamp = OrderedAttributeClass.MyOrderedField()
        POH = OrderedAttributeClass.MyOrderedField()
        PowerCycleCount = OrderedAttributeClass.MyOrderedField()
        VID = OrderedAttributeClass.MyOrderedField()
         
    
    def ParserPersistentEventLogHeader(self, listRawData):
    # note: listRawData is list type with int element, ex [0x15, 0x26]
        mLen = len(listRawData)
        if mLen!=512:
            self.Print("ParserPersistentEventLogHeader: header size not correct, expect 512byte, current = %s"%len)
            return False
        # if is string , set isSting=True
        self.PELH.append(["LogIdentifier", self.GetBytesFromList(listRawData, 0, 0)])
        self.PELH.append(["TNEV", self.GetBytesFromList(listRawData, 7, 4)])
        self.PELH.append(["TLL", self.GetBytesFromList(listRawData, 15, 8)])
        self.PELH.append(["LogRevision", self.GetBytesFromList(listRawData, 16, 16)])
        self.PELH.append(["LogHeaderLength", self.GetBytesFromList(listRawData, 19, 18)])
        self.PELH.append(["Timestamp", self.GetBytesFromList(listRawData, 27, 20)])
        self.PELH.append(["POH", self.GetBytesFromList(listRawData, 43, 28)])
        self.PELH.append(["PowerCycleCount", self.GetBytesFromList(listRawData, 51, 44)])
        self.PELH.append(["VID", self.GetBytesFromList(listRawData, 53, 52)])
        self.PELH.append(["SSVID", self.GetBytesFromList(listRawData, 55, 54)])
        self.PELH.append(["SN", self.GetBytesFromList(listRawData, 75, 56, isString=True)])
        self.PELH.append(["MN", self.GetBytesFromList(listRawData, 115, 76, isString=True)])
        self.PELH.append(["SUBNQN", self.GetBytesFromList(listRawData, 371, 116, isString=True)])
        self.PELH.append(["SupportedEventsBitmap", self.GetBytesFromList(listRawData, 511, 480)])
        
        self.PELHs.LogIdentifier = self.GetBytesFromList(listRawData, 0, 0)
        self.PELHs.TNEV = self.GetBytesFromList(listRawData, 7, 4)
        self.PELHs.TLL = self.GetBytesFromList(listRawData, 15, 8)
        self.PELHs.LogRevision = self.GetBytesFromList(listRawData, 16, 16)
        self.PELHs.LogHeaderLength = self.GetBytesFromList(listRawData, 19, 18)
        self.PELHs.POH = self.GetBytesFromList(listRawData, 27, 20)
        self.PELHs.PowerCycleCount = self.GetBytesFromList(listRawData, 43, 28)        
        
        # Supported Events Bitmap
        SEB = self.GetBytesFromList(listRawData, 511, 480)
        self.PELH.append(["VendorSpecificEventSupported", True if SEB&(1<<222)>0 else False])
        self.PELH.append(["ThermalExcursionEventSupport", True if SEB&(1<<13)>0 else False])
        self.PELH.append(["TelemetryLogCreateEventSupport", True if SEB&(1<<12)>0 else False])
        self.PELH.append(["SetFeatureEventSupport", True if SEB&(1<<11)>0 else False])
        self.PELH.append(["SanitizeCompletionEventSupport", True if SEB&(1<<10)>0 else False])
        self.PELH.append(["SanitizeStartEventSupport", True if SEB&(1<<9)>0 else False])
        self.PELH.append(["FormatNVMCompletionEvenSupport", True if SEB&(1<<8)>0 else False])
        self.PELH.append(["FormatNVMStartEventSupport", True if SEB&(1<<7)>0 else False])
        self.PELH.append(["ChangeNamespaceEventSupport", True if SEB&(1<<6)>0 else False])
        self.PELH.append(["NVMSubsystemHardwareErrorEventSupport", True if SEB&(1<<5)>0 else False])
        self.PELH.append(["PowerOnOrResetEventSupported", True if SEB&(1<<4)>0 else False])
        self.PELH.append(["TimestampChangeEventSupported", True if SEB&(1<<3)>0 else False])
        self.PELH.append(["FirmwareCommitEventSupported", True if SEB&(1<<2)>0 else False])
        self.PELH.append(["SMARTHealthLogSnapshotEventSupported", True if SEB&(1<<1)>0 else False])            
        return True

    def ParserPersistentEventLogEvents(self, listRawData, TLL):
        
        TNEV=self.GetBytesFromList(listRawData, 7, 4)
        offset = 512 # start from offset 512
        for i in range(TNEV):
            offset = self.GetPersistentEventN(listRawData, offset)


        return True

    def GetPersistentEventN(self, listRawData, offset):
        listTemp = []
        listTemp.append["EventType", self.GetBytesFromList(listRawData, offset+0, offset+0)]
        listTemp.append["EventTypeRevision", self.GetBytesFromList(listRawData, offset+1, offset+1)]
        listTemp.append["EHL", self.GetBytesFromList(listRawData, offset+2, offset+2)]
        listTemp.append["ControllerIdentifier", self.GetBytesFromList(listRawData, offset+5, offset+4)]
        listTemp.append["EventTimestamp", self.GetBytesFromList(listRawData, offset+13, offset+6)]
        listTemp.append["VSIL", self.GetBytesFromList(listRawData, offset+21, offset+20)]
        listTemp.append["EL", self.GetBytesFromList(listRawData, offset+23, offset+22)]
        
        EHL = self.GetBytesFromList(listRawData, offset+2, offset+2)
        VSIL = self.GetBytesFromList(listRawData, offset+21, offset+20)
        EHLplus3 = EHL+3
        EHLplus2plusVSIL = EHL+2+VSIL
        listTemp.append["VendorSpecificInformation", listRawData[offset+EHLplus3, offset+EHLplus2plusVSIL+1]]
        
        EL = self.GetBytesFromList(listRawData, offset+23, offset+22)
        EHLplusELplus2 = EHL+EL+2
        EHLplus3plusVSIL = EHL+3+VSIL
        EventData = listRawData[offset+EHLplusELplus2, offset+EHLplus3plusVSIL +1]
        listTemp.append["EventData", listRawData[offset+EHLplusELplus2, offset+EHLplus3plusVSIL +1]]
        
        EventType= self.GetBytesFromList(listRawData, offset+0, offset+0)
        
        if EventType==0x1:
            self.ParserEventDataType1(EventData)
            self.PersistentEventN
        
        return offset+EHLplus3plusVSIL #return next offset
    
    def ParserEventDataType1(self, EventData):
        # SMART
        listTemp = []
        if len(EventData)!=512:
            self.Print("Error, EventData!=512", "f")
            return listTemp
        
        listTemp.append(["CriticalWarning", self.GetBytesFromList(EventData, 0, 0)])        
        listTemp.append(["CompositeTemperature", self.GetBytesFromList(EventData, 2, 1)])
        listTemp.append(["AvailableSpare", self.GetBytesFromList(EventData, 3, 3)])
        listTemp.append(["AvailableSpareThreshold", self.GetBytesFromList(EventData, 4, 4)])
        listTemp.append(["PercentageUsed", self.GetBytesFromList(EventData, 5, 5)])
        listTemp.append(["EnduranceGroupCriticalWarningSummary", self.GetBytesFromList(EventData, 6, 6)])
        listTemp.append(["DataUnitsRead", self.GetBytesFromList(EventData, 47, 32)])
        listTemp.append(["DataUnitsWritten", self.GetBytesFromList(EventData, 63, 48)])
        listTemp.append(["HostReadCommands", self.GetBytesFromList(EventData, 79, 64)])
        listTemp.append(["HostWriteCommands", self.GetBytesFromList(EventData, 95, 80)])
        listTemp.append(["ControllerBusyTime", self.GetBytesFromList(EventData, 111, 96)])
        listTemp.append(["PowerCycles", self.GetBytesFromList(EventData, 127, 112)])
        listTemp.append(["PowerOnHours", self.GetBytesFromList(EventData, 143, 128)])
        listTemp.append(["UnsafeShutdowns", self.GetBytesFromList(EventData, 159, 144)])
        listTemp.append(["MediaandDataIntegrityErrors", self.GetBytesFromList(EventData, 175, 160)])
        listTemp.append(["NumberofErrorInformationLogEntries", self.GetBytesFromList(EventData, 191, 176)])
        listTemp.append(["WarningCompositeTemperatureTime", self.GetBytesFromList(EventData, 195, 192)])
        listTemp.append(["CriticalCompositeTemperatureTime", self.GetBytesFromList(EventData, 199, 196)])
        listTemp.append(["TemperatureSensor1", self.GetBytesFromList(EventData, 201, 200)])
        listTemp.append(["TemperatureSensor2", self.GetBytesFromList(EventData, 203, 202)])
        listTemp.append(["TemperatureSensor3", self.GetBytesFromList(EventData, 205, 204)])
        listTemp.append(["TemperatureSensor4", self.GetBytesFromList(EventData, 207, 206)])
        listTemp.append(["TemperatureSensor5", self.GetBytesFromList(EventData, 209, 208)])
        listTemp.append(["TemperatureSensor6", self.GetBytesFromList(EventData, 211, 210)])
        listTemp.append(["TemperatureSensor7", self.GetBytesFromList(EventData, 213, 212)])
        listTemp.append(["TemperatureSensor8", self.GetBytesFromList(EventData, 215, 214)])
        listTemp.append(["ThermalManagementTemperature1TransitionCount", self.GetBytesFromList(EventData, 219, 216)])
        listTemp.append(["ThermalManagementTemperature2TransitionCount", self.GetBytesFromList(EventData, 223, 220)])
        listTemp.append(["TotalTimeForThermalManagementTemperature1", self.GetBytesFromList(EventData, 227, 224)])
        listTemp.append(["TotalTimeForThermalManagementTemperature2", self.GetBytesFromList(EventData, 231, 228)])
        
        return listTemp        
        
    
    def __init__(self, argv):
        # initial parent class
        super(SMI_PersistentEventLog, self).__init__(argv)
        
        
        # Command Dword 10 – Log Specific Field
        self.LSF_ReadLogData = 0 <<8
        self.LSF_EstablishContextAndReadLogData = 1 <<8
        self.LSF_ReleaseContext = 2 <<8
        
        self.PELH=[]
        self.PELHs = self.PELH_()
        self.PersistentEventN=[]
        
        
        
        
        

    # define pretest, if not return 0 , skip all subcases
    def PreTest(self):     
        PersistentEventLogSupported = True if self.IdCtrl.LPA.bit(4)=="1" else False
        self.Print("Persistent Event log was supported(IdCtrl.LPA.bit(4)): %s"%("Yes" if PersistentEventLogSupported else "No"))
        return 0 # TODO
        return 0 if PersistentEventLogSupported else 255
                   

    # <define sub item scripts>
    SubCase1TimeOut = 600
    SubCase1Desc = ""   
    SubCase1KeyWord = "Parser Current Persistent Event log"
    def SubCase1(self):
        ret_code=0
        
        self.Print("Issue cmd with ReleaseContext=1 in Log Specific Field(cdw10) to clear current Persistent Event log")
        LSF = self.LSF_ReleaseContext
        result = self.get_log_passthru(LID=0x2, size=512, LSP=LSF, LPO=0)        #  TODO (LID=0xD, size=512, LSP=LSF, LPO=0)    
        if result==None:
            self.Print("Command fail, CMD: %s"%self.LastCmd, "f") 
            mStr = self.shell_cmd(self.LastCmd)
            self.Print(mStr)
            return 1

        self.Print("")
        self.Print("Issue cmd with EstablishContextAndReadLogData=1 in Log Specific Field to create context and get Persistent Event Log Header(512bytes)")
        LSF = self.LSF_EstablishContextAndReadLogData
        resultStrList = self.get_log_passthru(LID=0x2, size=512, LSP=LSF, LPO=0)        # 0xD TODO
        resultStrList = [int("0x%s"%v, 16) for v in resultStrList]  # conver to int, e.x.  conver string resultStrList["ab", "57"] to resultStrList[0xab, 0x57]
        if resultStrList==None:
            self.Print("Command fail, CMD: %s"%self.LastCmd, "f") 
            mStr = self.shell_cmd(self.LastCmd)
            self.Print(mStr)
            return 1

        self.ParserPersistentEventLogHeader(resultStrList)
        
        for mList in self.PELH:            
            self.Print(self.GetAlignString(S0="%s"%mList[0], S1="%s"%mList[1]))

        self.Print("")
        TT= self.PELHs.getOrderedAttributesList()
        self.PrintListWithAlign(TT)

        
        
        self.Print("")
        TLL = self.getPELHvalue("TLL")
        self.Print("Total Log Length (TLL): %s"%TLL)
        self.Print("Issue cmd with ReadLogData=1 in Log Specific Field to get Persistent Event Log Header and Persistent Event Log Events")
        self.Print("i.e. cmd with size = 'Total Log Length', offset = 0")
        
        LSF = self.LSF_ReadLogData
        resultStrList = self.get_log_passthru(LID=0x2, size=1024, LSP=LSF, LPO=0)        #  TODO (LID=0xD, size=TLL, LSP=LSF, LPO=0)   
        resultStrList = [int("0x%s"%v, 16) for v in resultStrList]  # conver to int, e.x.  conver string resultStrList["ab", "57"] to resultStrList[0xab, 0x57]
        if resultStrList==None:
            self.Print("Command fail, CMD: %s"%self.LastCmd, "f") 
            mStr = self.shell_cmd(self.LastCmd)
            self.Print(mStr)
            return 1
        
        self.ParserPersistentEventLogEvents(resultStrList)
                
        return ret_code

    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_PersistentEventLog(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    