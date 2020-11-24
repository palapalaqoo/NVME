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
    
    # class inherit from OrderedAttributeClass that can print ordered attributes
    class PELH(OrderedAttributeClass):        
        LogIdentifier = OrderedAttributeClass.MyOrderedField()
        TNEV = OrderedAttributeClass.MyOrderedField()
        TLL = OrderedAttributeClass.MyOrderedField()
        LogRevision = OrderedAttributeClass.MyOrderedField()
        LogHeaderLength = OrderedAttributeClass.MyOrderedField()
        Timestamp = OrderedAttributeClass.MyOrderedField()
        POH = OrderedAttributeClass.MyOrderedField()
        PowerCycleCount = OrderedAttributeClass.MyOrderedField()
        VID = OrderedAttributeClass.MyOrderedField()
        SSVID = OrderedAttributeClass.MyOrderedField()
        SN = OrderedAttributeClass.MyOrderedField()
        MN = OrderedAttributeClass.MyOrderedField()
        SUBNQN = OrderedAttributeClass.MyOrderedField()
        #SupportedEventsBitmap = OrderedAttributeClass.MyOrderedField()
        
        class SupportedEventsBitmap(OrderedAttributeClass):
            VendorSpecificEventSupported = OrderedAttributeClass.MyOrderedField()
            ThermalExcursionEventSupport = OrderedAttributeClass.MyOrderedField()
            TelemetryLogCreateEventSupport = OrderedAttributeClass.MyOrderedField()
            SetFeatureEventSupport = OrderedAttributeClass.MyOrderedField()
            SanitizeCompletionEventSupport = OrderedAttributeClass.MyOrderedField()
            SanitizeStartEventSupport = OrderedAttributeClass.MyOrderedField()
            FormatNVMCompletionEvenSupport = OrderedAttributeClass.MyOrderedField()
            FormatNVMStartEventSupport = OrderedAttributeClass.MyOrderedField()
            ChangeNamespaceEventSupport = OrderedAttributeClass.MyOrderedField()
            NVMSubsystemHardwareErrorEventSupport = OrderedAttributeClass.MyOrderedField()
            PowerOnOrResetEventSupported = OrderedAttributeClass.MyOrderedField()
            TimestampChangeEventSupported = OrderedAttributeClass.MyOrderedField()
            FirmwareCommitEventSupported = OrderedAttributeClass.MyOrderedField()
            SMARTHealthLogSnapshotEventSupported = OrderedAttributeClass.MyOrderedField   
        
        '''PersistentEventN include PersistentEventFormat and 
        SMARTHealthLogSnapshot
        FirmwareCommit
        TimestampChange
        Power-onorReset
        NVMSubsystemHardwareError
        ChangeNamespace
        FormatNVMStart
        FormatNVMCompletion
        SanitizeStart
        SanitizeCompletion
        SetFeature
        TelemetryLogCreated
        ThermalExcursion      
        '''  
        PersistentEventN=[] 
        
        class PersistentEventFormat(OrderedAttributeClass):
            EventType = OrderedAttributeClass.MyOrderedField()
            EventTypeRevision = OrderedAttributeClass.MyOrderedField()
            EHL = OrderedAttributeClass.MyOrderedField()
            ControllerIdentifier = OrderedAttributeClass.MyOrderedField()
            EventTimestamp = OrderedAttributeClass.MyOrderedField()
            VSIL = OrderedAttributeClass.MyOrderedField()
            EL = OrderedAttributeClass.MyOrderedField()
            VendorSpecificInformation = OrderedAttributeClass.MyOrderedField()
            EventData = None        
            
        class SMARTHealthLogSnapshot(OrderedAttributeClass):
            CriticalWarning = OrderedAttributeClass.MyOrderedField()
            CompositeTemperature = OrderedAttributeClass.MyOrderedField()
            AvailableSpare = OrderedAttributeClass.MyOrderedField()
            AvailableSpareThreshold = OrderedAttributeClass.MyOrderedField()
            PercentageUsed = OrderedAttributeClass.MyOrderedField()
            EnduranceGroupCriticalWarningSummary = OrderedAttributeClass.MyOrderedField()
            DataUnitsRead = OrderedAttributeClass.MyOrderedField()
            DataUnitsWritten = OrderedAttributeClass.MyOrderedField()
            HostReadCommands = OrderedAttributeClass.MyOrderedField()
            HostWriteCommands = OrderedAttributeClass.MyOrderedField()
            ControllerBusyTime = OrderedAttributeClass.MyOrderedField()
            PowerCycles = OrderedAttributeClass.MyOrderedField()
            PowerOnHours = OrderedAttributeClass.MyOrderedField()
            UnsafeShutdowns = OrderedAttributeClass.MyOrderedField()
            MediaandDataIntegrityErrors = OrderedAttributeClass.MyOrderedField()
            NumberofErrorInformationLogEntries = OrderedAttributeClass.MyOrderedField()
            WarningCompositeTemperatureTime = OrderedAttributeClass.MyOrderedField()
            CriticalCompositeTemperatureTime = OrderedAttributeClass.MyOrderedField()
            TemperatureSensor1 = OrderedAttributeClass.MyOrderedField()
            TemperatureSensor2 = OrderedAttributeClass.MyOrderedField()
            TemperatureSensor3 = OrderedAttributeClass.MyOrderedField()
            TemperatureSensor4 = OrderedAttributeClass.MyOrderedField()
            TemperatureSensor5 = OrderedAttributeClass.MyOrderedField()
            TemperatureSensor6 = OrderedAttributeClass.MyOrderedField()
            TemperatureSensor7 = OrderedAttributeClass.MyOrderedField()
            TemperatureSensor8 = OrderedAttributeClass.MyOrderedField()
            ThermalManagementTemperature1TransitionCount = OrderedAttributeClass.MyOrderedField()
            ThermalManagementTemperature2TransitionCount = OrderedAttributeClass.MyOrderedField()
            TotalTimeForThermalManagementTemperature1 = OrderedAttributeClass.MyOrderedField()
            TotalTimeForThermalManagementTemperature2 = OrderedAttributeClass.MyOrderedField()
    
        class FirmwareCommit(OrderedAttributeClass):
            OldFirmwareRevision = OrderedAttributeClass.MyOrderedField()
            NewFirmwareRevision = OrderedAttributeClass.MyOrderedField()
            FirmwareCommitAction = OrderedAttributeClass.MyOrderedField()
            FirmwareSlot = OrderedAttributeClass.MyOrderedField()
            StatusCodeTypeforFirmwareCommitCommand = OrderedAttributeClass.MyOrderedField()
            StatusReturnedforFirmwareCommitCommand = OrderedAttributeClass.MyOrderedField()
            VendorAssignedFirmwareCommitResultCode = OrderedAttributeClass.MyOrderedField()    
    
    
    def ParserPersistentEventLogHeader(self, listRawData):
    # note: listRawData is list type with int element, ex [0x15, 0x26]
        mLen = len(listRawData)
        if mLen!=512:
            self.Print("ParserPersistentEventLogHeader: header size not correct, expect 512byte, current = %s"%len)
            return False
        # if is string , set isSting=True
        self.PELH.LogIdentifier = self.GetBytesFromList(listRawData, 0, 0)
        self.PELH.TNEV = self.GetBytesFromList(listRawData, 7, 4)
        self.PELH.TLL = self.GetBytesFromList(listRawData, 15, 8)
        self.PELH.LogRevision = self.GetBytesFromList(listRawData, 16, 16)
        self.PELH.LogHeaderLength = self.GetBytesFromList(listRawData, 19, 18)
        self.PELH.POH = self.GetBytesFromList(listRawData, 27, 20)
        self.PELH.PowerCycleCount = self.GetBytesFromList(listRawData, 43, 28)  
        self.PELH.VID = self.GetBytesFromList(listRawData, 53, 52)
        self.PELH.SSVID = self.GetBytesFromList(listRawData, 55, 54)
        self.PELH.SN = self.GetBytesFromList(listRawData, 75, 56, isString=True)
        self.PELH.MN = self.GetBytesFromList(listRawData, 115, 76, isString=True)
        self.PELH.SUBNQN = self.GetBytesFromList(listRawData, 371, 116, isString=True)
        #self.PELH.SupportedEventsBitmap = self.GetBytesFromList(listRawData, 511, 480)   
        
        # Supported Events Bitmap
        SEB = self.GetBytesFromList(listRawData, 511, 480)
        self.PELH.SupportedEventsBitmap.VendorSpecificEventSupported = True if SEB&(1<<222)>0 else False
        self.PELH.SupportedEventsBitmap.ThermalExcursionEventSupport = True if SEB&(1<<13)>0 else False
        self.PELH.SupportedEventsBitmap.TelemetryLogCreateEventSupport = True if SEB&(1<<12)>0 else False
        self.PELH.SupportedEventsBitmap.SetFeatureEventSupport = True if SEB&(1<<11)>0 else False
        self.PELH.SupportedEventsBitmap.SanitizeCompletionEventSupport = True if SEB&(1<<10)>0 else False
        self.PELH.SupportedEventsBitmap.SanitizeStartEventSupport = True if SEB&(1<<9)>0 else False
        self.PELH.SupportedEventsBitmap.FormatNVMCompletionEvenSupport = True if SEB&(1<<8)>0 else False
        self.PELH.SupportedEventsBitmap.FormatNVMStartEventSupport = True if SEB&(1<<7)>0 else False
        self.PELH.SupportedEventsBitmap.ChangeNamespaceEventSupport = True if SEB&(1<<6)>0 else False
        self.PELH.SupportedEventsBitmap.NVMSubsystemHardwareErrorEventSupport = True if SEB&(1<<5)>0 else False
        self.PELH.SupportedEventsBitmap.PowerOnOrResetEventSupported = True if SEB&(1<<4)>0 else False
        self.PELH.SupportedEventsBitmap.TimestampChangeEventSupported = True if SEB&(1<<3)>0 else False
        self.PELH.SupportedEventsBitmap.FirmwareCommitEventSupported = True if SEB&(1<<2)>0 else False
        self.PELH.SupportedEventsBitmap.SMARTHealthLogSnapshotEventSupported = True if SEB&(1<<1)>0 else False         

        return True

    def ParserPersistentEventLogEvents(self, listRawData):
        TNEV= self.PELH.TNEV
        TNEV = 2 # TODO 
        offsetS = 512 # start from offset 512
        for i in range(TNEV):
            #return PersistentEventFormat and end offset
            PersistentEventFormat, offsetE = self.GetPersistentEventN(listRawData, offsetS)
            self.PELH.PersistentEventN.append(PersistentEventFormat)
            if offsetS == offsetE:
                self.Print("Error!, current PersistentEvent start at offset: %s, end at offset: %s(EHLplus3plusVSIL=0), stop parsing.."%(offsetS, offsetE), "f")    
                return False        
                
        if self.PELH.TLL!=offsetE:
            self.Print("Error!, Total Log Length(%s) in Persistent Event Log Header is not equal to the last byte address(%s) of last PersistentEvent"\
                       %(self.PELH.TLL, offsetE), "f")            
            return False

        return True

    def GetPersistentEventN(self, listRawData, offset):
        # PersistentEventFormatInst template
        rtInst = self.PELH.PersistentEventFormat
        rtInst.EventType = self.GetBytesFromList(listRawData, offset+0, offset+0)
        rtInst.EventTypeRevision = self.GetBytesFromList(listRawData, offset+1, offset+1)
        rtInst.EHL = self.GetBytesFromList(listRawData, offset+2, offset+2)
        rtInst.ControllerIdentifier = self.GetBytesFromList(listRawData, offset+5, offset+4)
        rtInst.EventTimestamp = self.GetBytesFromList(listRawData, offset+13, offset+6)
        rtInst.VSIL = self.GetBytesFromList(listRawData, offset+21, offset+20)
        rtInst.EL = self.GetBytesFromList(listRawData, offset+23, offset+22)
        
        
        EHL = rtInst.EHL
        VSIL = rtInst.VSIL
        EHLplus3 = EHL+3
        EHLplus2plusVSIL = EHL+2+VSIL
        VendSpecInfo = listRawData[offset+EHLplus3: offset+EHLplus2plusVSIL+1]
        rtInst.VendorSpecificInformation = VendSpecInfo
        
        EL = rtInst.EL
        EHLplusELplus2 = EHL+EL+2
        EHLplus3plusVSIL = EHL+3+VSIL
        EventData = listRawData[offset+EHLplusELplus2: offset+EHLplus3plusVSIL +1]
        EventData = listRawData[0: 512] # TODO
        
        EventType= rtInst.EventType        
        #parset raw data to structure
        if EventType==0x0:
            rtInst.EventData = self.ParserEventDataType1(EventData)
        else:
            self.Print("Error!, EventType undefined: %s"%EventType, "f")
        
        return rtInst, offset+EHLplus3plusVSIL #return next offset
    
    def ParserEventDataType1(self, EventData):
        # SMART
        if len(EventData)!=512:
            self.Print("Error, EventData!=512", "f")
            return None
        
        rtInst = self.PELH.SMARTHealthLogSnapshot
        
        rtInst.CriticalWarning = self.GetBytesFromList(EventData, 0, 0)        
        rtInst.CompositeTemperature = self.GetBytesFromList(EventData, 2, 1)
        rtInst.AvailableSpare = self.GetBytesFromList(EventData, 3, 3)
        rtInst.AvailableSpareThreshold = self.GetBytesFromList(EventData, 4, 4)
        rtInst.PercentageUsed = self.GetBytesFromList(EventData, 5, 5)
        rtInst.EnduranceGroupCriticalWarningSummary = self.GetBytesFromList(EventData, 6, 6)
        rtInst.DataUnitsRead = self.GetBytesFromList(EventData, 47, 32)
        rtInst.DataUnitsWritten = self.GetBytesFromList(EventData, 63, 48)
        rtInst.HostReadCommands = self.GetBytesFromList(EventData, 79, 64)
        rtInst.HostWriteCommands = self.GetBytesFromList(EventData, 95, 80)
        rtInst.ControllerBusyTime = self.GetBytesFromList(EventData, 111, 96)
        rtInst.PowerCycles = self.GetBytesFromList(EventData, 127, 112)
        rtInst.PowerOnHours = self.GetBytesFromList(EventData, 143, 128)
        rtInst.UnsafeShutdowns = self.GetBytesFromList(EventData, 159, 144)
        rtInst.MediaandDataIntegrityErrors = self.GetBytesFromList(EventData, 175, 160)
        rtInst.NumberofErrorInformationLogEntries = self.GetBytesFromList(EventData, 191, 176)
        rtInst.WarningCompositeTemperatureTime = self.GetBytesFromList(EventData, 195, 192)
        rtInst.CriticalCompositeTemperatureTime = self.GetBytesFromList(EventData, 199, 196)
        rtInst.TemperatureSensor1 = self.GetBytesFromList(EventData, 201, 200)
        rtInst.TemperatureSensor2 = self.GetBytesFromList(EventData, 203, 202)
        rtInst.TemperatureSensor3 = self.GetBytesFromList(EventData, 205, 204)
        rtInst.TemperatureSensor4 = self.GetBytesFromList(EventData, 207, 206)
        rtInst.TemperatureSensor5 = self.GetBytesFromList(EventData, 209, 208)
        rtInst.TemperatureSensor6 = self.GetBytesFromList(EventData, 211, 210)
        rtInst.TemperatureSensor7 = self.GetBytesFromList(EventData, 213, 212)
        rtInst.TemperatureSensor8 = self.GetBytesFromList(EventData, 215, 214)
        rtInst.ThermalManagementTemperature1TransitionCount = self.GetBytesFromList(EventData, 219, 216)
        rtInst.ThermalManagementTemperature2TransitionCount = self.GetBytesFromList(EventData, 223, 220)
        rtInst.TotalTimeForThermalManagementTemperature1 = self.GetBytesFromList(EventData, 227, 224)
        rtInst.TotalTimeForThermalManagementTemperature2 = self.GetBytesFromList(EventData, 231, 228)
        
        return rtInst        
        
    
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
        return 0 # TODO
        return 0 if PersistentEventLogSupported else 255
                   

    # <define sub item scripts>
    SubCase1TimeOut = 600
    SubCase1Desc = ""   
    SubCase1KeyWord = "Parser Current Persistent Event log"
    def SubCase1(self):
        ret_code=0
        
        self.Print("1) Issue cmd with ReleaseContext=1 in Log Specific Field(cdw10) to clear current Persistent Event log")
        LSF = self.LSF_ReleaseContext
        result = self.get_log_passthru(LID=0x2, size=512, LSP=LSF, LPO=0)        #  TODO (LID=0xD, size=512, LSP=LSF, LPO=0)    
        if result==None:
            self.Print("Command fail, CMD: %s"%self.LastCmd, "f") 
            mStr = self.shell_cmd(self.LastCmd)
            self.Print(mStr)
            return 1

        self.Print("")
        self.Print("2) Issue cmd with EstablishContextAndReadLogData=1 in Log Specific Field to create context and get Persistent Event Log Header(512bytes)")
        LSF = self.LSF_EstablishContextAndReadLogData
        resultStrList = self.get_log_passthru(LID=0x2, size=512, LSP=LSF, LPO=0)        # 0xD TODO
        resultStrList = [int("0x%s"%v, 16) for v in resultStrList]  # conver to int, e.x.  conver string resultStrList["ab", "57"] to resultStrList[0xab, 0x57]
        if resultStrList==None:
            self.Print("Command fail, CMD: %s"%self.LastCmd, "f") 
            mStr = self.shell_cmd(self.LastCmd)
            self.Print(mStr)
            return 1
        
        self.Print("")
        self.Print("3) Parser Persistent Event Log Header")
        if not self.ParserPersistentEventLogHeader(resultStrList):
            self.Print("ParserPersistentEventLogHeader fail", "f")
            return 1
        
        self.Print("")
        self.Print("4) Issue cmd with ReadLogData=1 in Log Specific Field to get Persistent Event Log Header and Persistent Event Log Events")
        self.Print("    i.e. cmd with size = 'Total Log Length', offset = 0")        
        
        LSF = self.LSF_ReadLogData
        TLL = 1024 #  TODO delete it
        resultStrList = self.get_log_passthru(LID=0x2, size=1024, LSP=LSF, LPO=0)        #  TODO (LID=0xD, size=TLL, LSP=LSF, LPO=0)   
        resultStrList = [int("0x%s"%v, 16) for v in resultStrList]  # conver to int, e.x.  conver string resultStrList["ab", "57"] to resultStrList[0xab, 0x57]
        if resultStrList==None:
            self.Print("Command fail, CMD: %s"%self.LastCmd, "f") 
            mStr = self.shell_cmd(self.LastCmd)
            self.Print(mStr)
            return 1        
                
        
     

        self.Print("")
        self.Print("5) Parser Persistent Events")
        
        if not self.ParserPersistentEventLogEvents(resultStrList):
            ret_code = 1
            
        
        self.Print("")
        self.Print("6) Show Log")
        self.Print("Persistent Event Log Header", "b")          
        allAttrList= self.PELH.getOrderedAttributesList()
        self.PrintListWithAlign(allAttrList, S0length=60, S1length=60)  
                         
        allAttrList= self.PELH.SupportedEventsBitmap.getOrderedAttributesList()
        self.PrintListWithAlign(allAttrList, S0length=60, S1length=60)             

        self.Print("")
        self.Print("Persistent Event Log Events", "b")   
        cnt=0
        for PersistentEventFormat in self.PELH.PersistentEventN:
            allAttrList= PersistentEventFormat.getOrderedAttributesList()
            self.Print("---------------------------------------")
            self.Print("Persistent Event %s"%cnt, "b")
            self.Print("Persistent Event Log Event Header", "b")
            self.PrintListWithAlign(allAttrList, S0length=60, S1length=60) 
            self.Print("Persistent Event Log Event Data", "b")
            allAttrList= PersistentEventFormat.EventData.getOrderedAttributesList()
            self.PrintListWithAlign(allAttrList, S0length=60, S1length=60) 
            cnt+=1
            
            






        return ret_code

    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_PersistentEventLog(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    