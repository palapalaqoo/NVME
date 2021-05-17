#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
import re
from time import sleep
import copy
# Import VCT modules
from lib_vct.NVME import NVME
from lib_vct.NVMECom import OrderedAttributeClass
from SMI_FeatureHCTM import SMI_FeatureHCTM
from ftplib import FTP
    
class SMI_PersistentEventLog(NVME):
    ScriptName = "SMI_PersistentEventLog.py"
    Author = ""
    Version = "20210512"
    
    def getPELHvalue(self, name):
        for i in range(len(self.PELH)):
            if name == self.PELH[i][0]:
                return self.PELH[i][1]
        return None
    
    # class inherit from OrderedAttributeClass that can print ordered attributes
    # MyOrderedField: [stop byte, start byte, type, parserFunc=None] where type 0=int, 1=string, 2=not define and need to be set later
    # parserFunc: if provided, value = parserFunc(value)
    class PELH_(OrderedAttributeClass): 
        # define parserFuncs
        def p_getFormatTime(self, value):
            mStr = "0x%X(%s)"%(value, self.getFormatTime(value))
            return mStr
        # end of define parserFuncs     
        LogIdentifier = OrderedAttributeClass.MyOrderedField((0, 0, 0))
        TNEV = OrderedAttributeClass.MyOrderedField((7, 4, 0))
        TLL = OrderedAttributeClass.MyOrderedField((15, 8, 0))
        LogRevision = OrderedAttributeClass.MyOrderedField((16, 16, 0))
        LogHeaderLength = OrderedAttributeClass.MyOrderedField((19, 18, 0))
        Timestamp = OrderedAttributeClass.MyOrderedField((27, 20, 0, p_getFormatTime))
        POH = OrderedAttributeClass.MyOrderedField((43, 28, 0))
        PowerCycleCount = OrderedAttributeClass.MyOrderedField((51, 44, 0))
        VID = OrderedAttributeClass.MyOrderedField((53, 52, 0))
        SSVID = OrderedAttributeClass.MyOrderedField((55, 54, 0))
        SN = OrderedAttributeClass.MyOrderedField((75, 56, 1))
        MN = OrderedAttributeClass.MyOrderedField((115, 76, 1))
        SUBNQN = OrderedAttributeClass.MyOrderedField((371, 116, 1))
        #SupportedEventsBitmap = OrderedAttributeClass.MyOrderedField(())
        
        class SupportedEventsBitmap_(OrderedAttributeClass):
            VendorSpecificEventSupported = OrderedAttributeClass.MyOrderedField(())
            ThermalExcursionEventSupport = OrderedAttributeClass.MyOrderedField(())
            TelemetryLogCreateEventSupport = OrderedAttributeClass.MyOrderedField(())
            SetFeatureEventSupport = OrderedAttributeClass.MyOrderedField(())
            SanitizeCompletionEventSupport = OrderedAttributeClass.MyOrderedField(())
            SanitizeStartEventSupport = OrderedAttributeClass.MyOrderedField(())
            FormatNVMCompletionEvenSupport = OrderedAttributeClass.MyOrderedField(())
            FormatNVMStartEventSupport = OrderedAttributeClass.MyOrderedField(())
            ChangeNamespaceEventSupport = OrderedAttributeClass.MyOrderedField(())
            NVMSubsystemHardwareError = OrderedAttributeClass.MyOrderedField(())
            PowerOnOrResetEventSupported = OrderedAttributeClass.MyOrderedField(())
            TimestampChangeEventSupported = OrderedAttributeClass.MyOrderedField(())
            FirmwareCommitEventSupported = OrderedAttributeClass.MyOrderedField(())
            SMARTHealthLogSnapshotEventSupported = OrderedAttributeClass.MyOrderedField   
        
        '''PersistentEventN include PersistentEventFormat and 
        EventNotDefine #          
        SMARTHealthLogSnapshot
        FirmwareCommit
        TimestampChange
        Power_onorReset
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
        def __init__(self):
            self.SupportedEventsBitmap = self.SupportedEventsBitmap_()
                        
            self.PersistentEventN=[]             
            self.briefInfo=[]
            #self.PersistentEventFormat = self.PersistentEventFormat_()
            self.EventNotDefine = self.EventNotDefine_()
            self.SMARTHealthLogSnapshot = self.SMARTHealthLogSnapshot_()
            self.FirmwareCommit = self.FirmwareCommit_()
            self.TimestampChange = self.TimestampChange_()
            self.Power_onorReset = self.Power_onorReset_()
            self.NVMSubsystemHardwareError = self.NVMSubsystemHardwareError_()
            self.ChangeNamespace = self.ChangeNamespace_
            self.FormatNVMStart = self.FormatNVMStart_
            self.FormatNVMCompletion = self.FormatNVMCompletion_            
            self.SanitizeStart = self.SanitizeStart_           
            self.SanitizeCompletion = self.SanitizeCompletion_            
            self.SetFeature = self.SetFeature_            
            self.TelemetryLogCreated = self.TelemetryLogCreated_            
            self.ThermalExcursion = self.ThermalExcursion_            

        class PersistentEventFormat_(OrderedAttributeClass):
            def p_getFormatTime(self, value):
                mStr = "0x%X(%s)"%(value, self.getFormatTime(value)) 
                return mStr         
            EventType = OrderedAttributeClass.MyOrderedField((0, 0, 0))
            EventTypeRevision = OrderedAttributeClass.MyOrderedField((1, 1, 0))
            EHL = OrderedAttributeClass.MyOrderedField((2, 2, 0))
            ControllerIdentifier = OrderedAttributeClass.MyOrderedField((5, 4, 0))
            EventTimestamp = OrderedAttributeClass.MyOrderedField((13, 6, 0,p_getFormatTime))
            VSIL = OrderedAttributeClass.MyOrderedField((21, 20, 0))
            EL = OrderedAttributeClass.MyOrderedField((23, 22, 0))
            VendorSpecificInformation = OrderedAttributeClass.MyOrderedField((0, 0, 2))
            EventData = None        
            
        class EventNotDefine_(OrderedAttributeClass):
            NotDefine = OrderedAttributeClass.MyOrderedField((0, 0, 0))        
            
        class SMARTHealthLogSnapshot_(OrderedAttributeClass):
            CriticalWarning = OrderedAttributeClass.MyOrderedField((0, 0, 0))        
            CompositeTemperature = OrderedAttributeClass.MyOrderedField((2, 1, 0))
            AvailableSpare = OrderedAttributeClass.MyOrderedField((3, 3, 0))
            AvailableSpareThreshold = OrderedAttributeClass.MyOrderedField((4, 4, 0))
            PercentageUsed = OrderedAttributeClass.MyOrderedField((5, 5, 0))
            EnduranceGroupCriticalWarningSummary = OrderedAttributeClass.MyOrderedField((6, 6, 0))
            DataUnitsRead = OrderedAttributeClass.MyOrderedField((47, 32, 0))
            DataUnitsWritten = OrderedAttributeClass.MyOrderedField((63, 48, 0))
            HostReadCommands = OrderedAttributeClass.MyOrderedField((79, 64, 0))
            HostWriteCommands = OrderedAttributeClass.MyOrderedField((95, 80, 0))
            ControllerBusyTime = OrderedAttributeClass.MyOrderedField((111, 96, 0))
            PowerCycles = OrderedAttributeClass.MyOrderedField((127, 112, 0))
            PowerOnHours = OrderedAttributeClass.MyOrderedField((143, 128, 0))
            UnsafeShutdowns = OrderedAttributeClass.MyOrderedField((159, 144, 0))
            MediaandDataIntegrityErrors = OrderedAttributeClass.MyOrderedField((175, 160, 0))
            NumberofErrorInformationLogEntries = OrderedAttributeClass.MyOrderedField((191, 176, 0))
            WarningCompositeTemperatureTime = OrderedAttributeClass.MyOrderedField((195, 192, 0))
            CriticalCompositeTemperatureTime = OrderedAttributeClass.MyOrderedField((199, 196, 0))
            TemperatureSensor1 = OrderedAttributeClass.MyOrderedField((201, 200, 0))
            TemperatureSensor2 = OrderedAttributeClass.MyOrderedField((203, 202, 0))
            TemperatureSensor3 = OrderedAttributeClass.MyOrderedField((205, 204, 0))
            TemperatureSensor4 = OrderedAttributeClass.MyOrderedField((207, 206, 0))
            TemperatureSensor5 = OrderedAttributeClass.MyOrderedField((209, 208, 0))
            TemperatureSensor6 = OrderedAttributeClass.MyOrderedField((211, 210, 0))
            TemperatureSensor7 = OrderedAttributeClass.MyOrderedField((213, 212, 0))
            TemperatureSensor8 = OrderedAttributeClass.MyOrderedField((215, 214, 0))
            ThermalManagementTemperature1TransitionCount = OrderedAttributeClass.MyOrderedField((219, 216, 0))
            ThermalManagementTemperature2TransitionCount = OrderedAttributeClass.MyOrderedField((223, 220, 0))
            TotalTimeForThermalManagementTemperature1 = OrderedAttributeClass.MyOrderedField((227, 224, 0))
            TotalTimeForThermalManagementTemperature2 = OrderedAttributeClass.MyOrderedField((231, 228, 0))
    
        class FirmwareCommit_(OrderedAttributeClass):
            OldFirmwareRevision = OrderedAttributeClass.MyOrderedField((7, 0, 0))
            NewFirmwareRevision = OrderedAttributeClass.MyOrderedField((15, 8, 0))
            FirmwareCommitAction = OrderedAttributeClass.MyOrderedField((16, 16, 0))
            FirmwareSlot = OrderedAttributeClass.MyOrderedField((17 ,17, 0))
            StatusCodeTypeforFirmwareCommitCommand = OrderedAttributeClass.MyOrderedField((18, 18, 0))
            StatusReturnedforFirmwareCommitCommand = OrderedAttributeClass.MyOrderedField((19, 19, 0))
            VendorAssignedFirmwareCommitResultCode = OrderedAttributeClass.MyOrderedField((21, 20, 0))  
            
        class TimestampChange_(OrderedAttributeClass):
            PreviousTimestamp = OrderedAttributeClass.MyOrderedField((7, 0, 0))
            MillisecondsSinceReset = OrderedAttributeClass.MyOrderedField((15, 8, 0))         

        class Power_onorReset_(OrderedAttributeClass):
            FirmwareRevision = OrderedAttributeClass.MyOrderedField((7, 0, 1))
            ResetInformationList = [] #OrderedAttributeClass.MyOrderedField((0, 0, 0))                
            def __init__(self):
                self.ControllerResetInformationdescriptor = self.ControllerResetInformationdescriptor_()
                self.setDynamicList(self.ResetInformationList)
                

            class ControllerResetInformationdescriptor_(OrderedAttributeClass):
                ControllerID = OrderedAttributeClass.MyOrderedField((1, 0, 0))
                FirmwareActivation = OrderedAttributeClass.MyOrderedField((2, 2, 0))
                OperationinProgress = OrderedAttributeClass.MyOrderedField((3, 3, 0))
                ControllerPowerCycle = OrderedAttributeClass.MyOrderedField((19, 16, 0))
                Poweronmilliseconds = OrderedAttributeClass.MyOrderedField((27, 20, 0))
                ControllerTimestamp = OrderedAttributeClass.MyOrderedField((35, 28, 0))                

        class NVMSubsystemHardwareError_(OrderedAttributeClass):
            NVMSubsystemHardwareErrorEventCode = OrderedAttributeClass.MyOrderedField((1, 0, 0))
            AdditionalHardwareErrorInformation = OrderedAttributeClass.MyOrderedField((0, 0, 0))

        class ChangeNamespace_(OrderedAttributeClass):
            NamespaceManagementCDW10 = OrderedAttributeClass.MyOrderedField((3, 0, 0))
            NamespaceSize = OrderedAttributeClass.MyOrderedField((15, 8, 0))
            NamespaceCapacity = OrderedAttributeClass.MyOrderedField((31, 24, 0))
            FormattedLBASize = OrderedAttributeClass.MyOrderedField((32, 32, 0))
            End_to_endDataProtectionTypeSettings = OrderedAttributeClass.MyOrderedField((33, 33, 0))
            NamespaceMulti_pathIOandNamespaceSharingCapabilities = OrderedAttributeClass.MyOrderedField((34, 34, 0))
            ANAGroupIdentifier = OrderedAttributeClass.MyOrderedField((39, 36, 0))
            NVMSetIdentifier = OrderedAttributeClass.MyOrderedField((41, 40, 0))
            NamespaceID = OrderedAttributeClass.MyOrderedField((47, 44, 0))

        class FormatNVMStart_(OrderedAttributeClass):
            NamespaceIdentifier = OrderedAttributeClass.MyOrderedField((3, 0, 0))
            FormatNVMAttributes = OrderedAttributeClass.MyOrderedField((4, 4, 0))
            FormatNVMCDW10 = OrderedAttributeClass.MyOrderedField((11, 8, 0))
            
        class FormatNVMCompletion_(OrderedAttributeClass):
            NamespaceIdentifier = OrderedAttributeClass.MyOrderedField((3, 0, 0))
            SmallestFormatProgressIndicator = OrderedAttributeClass.MyOrderedField((4, 4, 0))
            FormatNVMStatus = OrderedAttributeClass.MyOrderedField((5, 5, 0))
            CompletionInformation = OrderedAttributeClass.MyOrderedField((7, 6, 0))
            StatusField = OrderedAttributeClass.MyOrderedField((11, 8, 0))    

        class SanitizeStart_(OrderedAttributeClass):
            SANICAP = OrderedAttributeClass.MyOrderedField((3, 0, 0))
            SanitizeCDW10 = OrderedAttributeClass.MyOrderedField((7, 4, 0))
            SanitizeCDW11 = OrderedAttributeClass.MyOrderedField((11, 8, 0))

        class SanitizeCompletion_(OrderedAttributeClass):
            SanitizeProgress = OrderedAttributeClass.MyOrderedField((1, 0, 0))
            SanitizeStatus = OrderedAttributeClass.MyOrderedField((3, 2, 0))
            CompletionInformation = OrderedAttributeClass.MyOrderedField((5, 4, 0))

        class SetFeature_(OrderedAttributeClass):
            SetFeatureEventLayout = OrderedAttributeClass.MyOrderedField((3, 0, 0))
            CommandDwords = OrderedAttributeClass.MyOrderedField((0, 0, 0))
            MemoryBuffer = OrderedAttributeClass.MyOrderedField((0, 0, 0))            
            CommandCompletionDword0 = OrderedAttributeClass.MyOrderedField((0, 0, 0))
            
        class TelemetryLogCreated_(OrderedAttributeClass):
            TelemetryInitiatedLog = OrderedAttributeClass.MyOrderedField((511, 0, 0))
            
        class ThermalExcursion_(OrderedAttributeClass):
            OverTemperature = OrderedAttributeClass.MyOrderedField((0, 0, 0))
            Threshold = OrderedAttributeClass.MyOrderedField((1, 1, 0))

               
    def SetClassWithRawData(self, classIn, listRawData, offset):
        # classIn, ex, self.PELH
        allList = classIn.getOrderedAttributesList_init() # self.PELH.getOrderedAttributesList_init()
        for mList in allList:
            name = mList[0] # LogIdentifier
            argList = mList[1]
            stopByte = offset + argList[0]
            startByte = offset + argList[1]
            isString=True if argList[2] == 1 else False
            isSkip=True if argList[2] == 2 else False
            parserFunc = None if len(argList)<=3 else argList[3]
            if isSkip:
                setattr(classIn, name, None)
            else:
                value = self.GetBytesFromList(listRawData, stopByte, startByte, isString)
                if parserFunc!=None: # if provided, value = parserFunc(value)
                    value = parserFunc(self, value)
                setattr(classIn, name, value)
            
    
    def ParserPersistentEventLogHeader(self, listRawData):
    # note: listRawData is list type with int element, ex [0x15, 0x26]
        mLen = len(listRawData)
        if mLen!=512:
            self.Print("ParserPersistentEventLogHeader: header size not correct, expect 512byte, current = %s"%len)
            return False

        self.SetClassWithRawData(self.PELH, listRawData, 0)
        # if is string , set isSting=True
        '''
        self.PELH.LogIdentifier = self.GetBytesFromList(listRawData, 0, 0)
        self.PELH.TNEV = self.GetBytesFromList(listRawData, 7, 4)
        self.PELH.TLL = self.GetBytesFromList(listRawData, 15, 8)
        self.PELH.LogRevision = self.GetBytesFromList(listRawData, 16, 16)
        self.PELH.LogHeaderLength = self.GetBytesFromList(listRawData, 19, 18)
        self.PELH.Timestamp = self.GetBytesFromList(listRawData, 27, 20)
        self.PELH.POH = self.GetBytesFromList(listRawData, 43, 28)
        self.PELH.PowerCycleCount = self.GetBytesFromList(listRawData, 51, 44)  
        self.PELH.VID = self.GetBytesFromList(listRawData, 53, 52)
        self.PELH.SSVID = self.GetBytesFromList(listRawData, 55, 54)
        self.PELH.SN = self.GetBytesFromList(listRawData, 75, 56, isString=True)
        self.PELH.MN = self.GetBytesFromList(listRawData, 115, 76, isString=True)
        self.PELH.SUBNQN = self.GetBytesFromList(listRawData, 371, 116, isString=True)
        #self.PELH.SupportedEventsBitmap = self.GetBytesFromList(listRawData, 511, 480)   
        '''

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
        self.PELH.SupportedEventsBitmap.NVMSubsystemHardwareError = True if SEB&(1<<5)>0 else False
        self.PELH.SupportedEventsBitmap.PowerOnOrResetEventSupported = True if SEB&(1<<4)>0 else False
        self.PELH.SupportedEventsBitmap.TimestampChangeEventSupported = True if SEB&(1<<3)>0 else False
        self.PELH.SupportedEventsBitmap.FirmwareCommitEventSupported = True if SEB&(1<<2)>0 else False
        self.PELH.SupportedEventsBitmap.SMARTHealthLogSnapshotEventSupported = True if SEB&(1<<1)>0 else False         

        return True

    def ParserPersistentEventLogEvents(self, listRawData):
        TNEV= self.PELH.TNEV
        #TNEV = 2 # TODO 
        offsetS = 512 # start from offset 512
        self.Print("Size of PersistentEvent log data: %s"%len(listRawData))
        title = self.PrintAlignString("No:", "Start at:", "Stop at:", "Size:", "Type:", "Event Data at:", "Event Data end:", "EventTimestamp")
        self.PELH.briefInfo=[title] # clear and set title for briefInfo
        for i in range(TNEV):
            #return PersistentEventFormat and end offset
            isPass, PersistentEventFormat, offsetE, briefInfo = self.GetPersistentEventN(i, listRawData, offsetS)
            self.PELH.PersistentEventN.append(PersistentEventFormat)
            self.PELH.briefInfo.append(briefInfo)
            
            if offsetS == offsetE:
                self.Print("Error!, current PersistentEvent start at offset: %s, end at offset: %s(EHLplus3plusVSIL=0), stop parsing.."%(offsetS, offsetE), "f")    
                return False  
            elif not isPass:
                return False
            else:
                offsetS = offsetE +1
        lastAddr = offsetE+1 
        self.Print("Check if Total Log Length(%s) in Persistent Event Log Header is equal to the last byte address(%s) of last PersistentEvent"\
                       %(self.PELH.TLL, lastAddr))
        if self.PELH.TLL==lastAddr:
            self.Print("Pass", "p")
        else:            
            self.Print("Fail", "f")            
            return False
        self.Print("")
        self.Print("Check if EventTimestamp is counting up")
        old = 0xFFFFFFFFFFFF
        curr = 0
        Timestamp_old  = ""
        cnt=0
        for Event in self.PELH.PersistentEventN:
            Timestamp = Event.EventTimestamp
            curr , formatedT = self.parserTimestamp(Timestamp)

            if curr>old:                
                curr_n , formatedT_n = self.parserTimestamp(Timestamp_old)
                self.Print("Fail at No: %s , formated Timestamp: %s,  Timestamp: %s"%(cnt-1, formatedT_n, curr_n), "f")
                self.Print("Next at No: %s , formated Timestamp: %s,  Timestamp: %s"%(cnt, formatedT, curr), "f")
                self.Print("")
                if not self.mTestModeOn:
                    return False              
            cnt+=1
            old = curr
            Timestamp_old = Timestamp
        self.Print("Pass", "p")

        return True

    def GetPersistentEventN(self, id, listRawData, offset):
        isPass = True
        # parser Event Format without Vendor Specific Information and Persistent Event Log Event Data, ie, header only
        # class inst
        rtInst = self.PELH.PersistentEventFormat_() # using new class to avoid the same rtInst when call func getOrderedAttributesList_curr()
        self.SetClassWithRawData(rtInst, listRawData, offset)# PersistentEventFormat start from offset of  listRawData
        
        # handle header
        EHL = rtInst.EHL # Event Header Length = EHL+3
        VSIL = rtInst.VSIL # Vendor Specific Information Length
        EHLplus3 = EHL+3
        EHLplus2plusVSIL = EHL+2+VSIL # also = EHL+3 + VSIL -1
        VendSpecInfo = listRawData[offset+EHLplus3: offset+EHLplus2plusVSIL+1]
        rtInst.VendorSpecificInformation = VendSpecInfo
        
        EL = rtInst.EL # Event Length =  Vendor Specific Information Length +  Event Data length
        EHLplusELplus2 = EHL+EL+2 # also = EHL+3 + EL -1
        EHLplus3plusVSIL = EHL+3+VSIL # also = EHL+3 + VSIL -1 +1
        EventData = listRawData[offset+EHLplus3plusVSIL: offset+EHLplusELplus2 +1]
        #EventData = listRawData[0: 512] # TODO
        
        EventType= rtInst.EventType       
        #EventType=0x4 # TODO 
        offsetE = offset+EHLplusELplus2
        # print and save brief information
        timeStamp = rtInst.EventTimestamp
        if re.search("\((.+)\)", timeStamp): # 0x2017968B29BAE(2021-05-14 10:26:46)
            timeStamp = re.search("\((.+)\)", timeStamp).group(1)
        #self.PrintAlignString("No:", "Start at:", "Stop at:", "Size:", "Type:", "Event Data at:", "Event Data end:", "EventTimestamp")       
        briefInfo = self.PrintAlignString(id, offset, offsetE, (EHLplusELplus2+1) ,\
                               EventType, "%s + %s"%(offset, EHLplus3plusVSIL), "%s + %s"%(offset, EHLplusELplus2), timeStamp)
        
        #parser raw data to structure
        rtInst.EventData = self.ParserEventData(EventData, EventType, rtInst, offset)
        if (offset+EHLplusELplus2 +1)>self.PELH.TLL:
            isPass = False
            self.Print("Error!, Expect the last byte of this Event is at: %s"\
                       ", that is less then Total Log Length (TLL): %s "%(offset+EHLplusELplus2 +1, self.PELH.TLL))
        
        return isPass, rtInst, offsetE, briefInfo #return next offset
            
    
    def ParserEventData(self, EventData, EventType, rtInst, offset):
    # rtInst = self.PELH.PersistentEventFormat
        expectSize=None
        if EventType==0x1:
            expectSize = 512 #according to spec, size=512byte
            # class inst
            rtInst = self.PELH.SMARTHealthLogSnapshot_()            
        elif EventType==0x2:
            expectSize = 22
            rtInst = self.PELH.FirmwareCommit_() 
        elif EventType==0x3:
            expectSize = 16
            rtInst = self.PELH.TimestampChange_()
        elif EventType==0x4:
            EL_VSIL_1 = rtInst.EL - rtInst.VSIL - 1
            expectSize = EL_VSIL_1 +1 # Figure 217: Power-on or Reset Event (Event Type 04h)
            rtInst = self.PELH.Power_onorReset_()
        elif EventType==0x5:
            expectSize=len(EventData) # will not check size, so all data as expect
            rtInst = self.PELH.NVMSubsystemHardwareError_()
            # EventData from byte 4  to last byte is AdditionalHardwareErrorInformation
            rtInst.setOrderedAttributesList_init("AdditionalHardwareErrorInformation", (expectSize-1, 4, 0))
        elif EventType==0x6:
            expectSize = 48
            rtInst = self.PELH.ChangeNamespace_()           
        elif EventType==0x7:
            expectSize = 12
            rtInst = self.PELH.FormatNVMStart_()  
        elif EventType==0x8:
            expectSize = 12
            rtInst = self.PELH.FormatNVMCompletion_()                          
        elif EventType==0x9:
            expectSize = 12
            rtInst = self.PELH.SanitizeStart_() 
        elif EventType==0xA:
            expectSize = 8
            rtInst = self.PELH.SanitizeCompletion_()                                             
        elif EventType==0xB:
            expectSize=len(EventData)
            rtInst = self.PELH.SetFeature_()             
        elif EventType==0xC:
            expectSize = 512
            rtInst = self.PELH.TelemetryLogCreated_()   
        elif EventType==0xD:
            expectSize = 2
            rtInst = self.PELH.ThermalExcursion_()                                              
        else:
            self.Print("Error!, EventType undefined: %s"%EventType, "f")   
            rtInst = self.PELH.EventNotDefine
            return rtInst     
        
        if len(EventData)!=expectSize:
            self.Print("Error, start at: %s, EventType=%s, EventData expect size: %s, current size: %s"%(offset, EventType, expectSize, len(EventData)), "f")
            return rtInst        

        self.SetClassWithRawData(rtInst, EventData, 0) # class inst data start from offset 0 of  EventData
        if EventType==0x4:
            descriptorSize = EL_VSIL_1 -8+1
            ControllerResetInformationdescriptorSize = 36 # spec is 36 for every scriptor
            if descriptorSize%ControllerResetInformationdescriptorSize!=0:
                self.Print("Error, EventType==0x4, parsered descriptorSize(EL_VSIL_1 - 8 +1) = %s"\
                           ", not multiple of %s(ControllerResetInformationdescriptorSize)"\
                           (descriptorSize, ControllerResetInformationdescriptorSize))
                return rtInst
                        
            # parser ControllerResetInformationdescriptor_
            loop = descriptorSize/ControllerResetInformationdescriptorSize
            offset = 8 # start for offset = 8
            rtInst.ResetInformationList=[] #clear
            scripterInst = rtInst.ControllerResetInformationdescriptor
            for i in range(loop):                
                self.SetClassWithRawData(scripterInst, EventData, offset) 
                rtInst.ResetInformationList.append(scripterInst)
                offset+=ControllerResetInformationdescriptorSize

        if EventType==0xB:
            # after SetPELHwithRawData, SetFeatureEventLayout value is get, others must calcute by SetFeatureEventLayout
            SetFeatureEventLayout = rtInst.SetFeatureEventLayout
            MemoryBufferCount = SetFeatureEventLayout | 7 # bit 2:0
            LoggedCommandCompletionDword0 = SetFeatureEventLayout | 8 # bit 3
            DwordCount = SetFeatureEventLayout | (0xFFFF<<16) # bit 31:16
                        
            stopByte = DwordCount*4+3 # spec
            startByte = 4            
            rtInst.setOrderedAttributesList_init("CommandDwords", (stopByte, startByte, 0))
            
            stopByte = MemoryBufferCount + DwordCount*4+4 # MemoryBufferCount in spec is 'Data Buffer Count'
            startByte = DwordCount*4+4
            if MemoryBufferCount==0: # if==0, then this field does not exist in the logged event
                rtInst.setOrderedAttributesList_init("MemoryBuffer", (stopByte, startByte, 2)) # set 2 to skip
            else:
                rtInst.setOrderedAttributesList_init("MemoryBuffer", (stopByte, startByte, 0))
                
            stopByte = MemoryBufferCount + DwordCount*4+8
            startByte = MemoryBufferCount + DwordCount*4+5                
            if LoggedCommandCompletionDword0==0: # if==0, then this field is not logged
                rtInst.setOrderedAttributesList_init("CommandCompletionDword0", (stopByte, startByte, 2)) # set 2 to skip
            else:
                rtInst.setOrderedAttributesList_init("CommandCompletionDword0", (stopByte, startByte, 0))
            
            # parser again to get CommandDwords, MemoryBuffer, CommandCompletionDword0
            self.SetClassWithRawData(rtInst, EventData, 0)
            
            
        return rtInst        
        

    def PrintAlignString(self,S0="", S1="", S2="", S3="", S4="", S5="", S6="", S7="", PF="default"):            
        mStr = "{:<4}{:<10}{:<10}{:<8}{:<10}{:<16}{:<16}{:<16}".format(S0, S1, S2, S3, S4, S5, S6, S7 )
        if PF=="pass":
            self.Print( mStr , "p")        
        elif PF=="fail":
            self.Print( mStr , "f")      
        else:
            self.Print( mStr )
        return mStr

    def GetTMT1_TMT1(self):
        buf = self.get_feature(0x10)
        TMT=0
        TMT1=0
        TMT2=0
        # get feature
        mStr="Current value:(.+$)"
        if re.search(mStr, buf):
            TMT=int(re.search(mStr, buf).group(1), 16)
            TMT1=TMT>>16
            TMT2=TMT&0xFFFF    
        return TMT1, TMT2
    
    def SetTMT1_TMT2(self, TMT1, TMT2):       
        TMT=(TMT1<<16)+(TMT2)
        # set feature
        return self.set_feature(0x10, TMT)  
    
    def GetAndParserPEL(self):
        self.Print("1) Issue cmd with ReleaseContext=1 in Log Specific Field(cdw10) to clear current Persistent Event log")
        LSF = self.LSF_ReleaseContext
        result = self.get_log_passthru(LID=0xD, size=512, LSP=LSF, LPO=0)    
        #result = self.get_log_passthru(LID=0x2, size=512, LSP=LSF, LPO=0)        #  TODO 
        if result==None:
            self.Print("Command fail, CMD: %s"%self.LastCmd, "f") 
            mStr = self.shell_cmd(self.LastCmd)
            self.Print(mStr)
            return False

        self.Print("")
        self.Print("2) Issue cmd with EstablishContextAndReadLogData=1 in Log Specific Field to create context and get Persistent Event Log Header(512bytes)")
        LSF = self.LSF_EstablishContextAndReadLogData
        resultStrList = self.get_log_passthru(LID=0xD, size=512, LSP=LSF, LPO=0) 
        #resultStrList = self.get_log_passthru(LID=0x2, size=512, LSP=LSF, LPO=0)        # 0xD TODO
        resultStrList = [int("0x%s"%v, 16) for v in resultStrList]  # conver to int, e.x.  conver string resultStrList["ab", "57"] to resultStrList[0xab, 0x57]
        if resultStrList==None:
            self.Print("Command fail, CMD: %s"%self.LastCmd, "f") 
            mStr = self.shell_cmd(self.LastCmd)
            self.Print(mStr)
            return False
        
        self.Print("")
        self.Print("3) Parser Persistent Event Log Header")
        if not self.ParserPersistentEventLogHeader(resultStrList):
            self.Print("ParserPersistentEventLogHeader fail", "f")
            return False
        self.SetPrintOffset(4, "add")     
        allAttrList= self.PELH.getOrderedAttributesList_curr()
        self.PrintListWithAlign(allAttrList, S0length=60, S1length=60)  
                         
        allAttrList= self.PELH.SupportedEventsBitmap.getOrderedAttributesList_curr()
        self.PrintListWithAlign(allAttrList, S0length=60, S1length=60)    
        self.SetPrintOffset(-4, "add")

        
        self.Print("")
        self.Print("4) Issue cmd with ReadLogData=1 in Log Specific Field to get Persistent Event Log Header and Persistent Event Log Events")
        self.Print("    i.e. cmd with size = 'Total Log Length'(%s), offset = 0"%self.PELH.TLL)        
        self.SetPrintOffset(4, "add")
        LSF = self.LSF_ReadLogData
        TLL = self.PELH.TLL
        #TLL = 1024 #  TODO delete it
        resultStrList = self.get_log_passthru(LID=0xD, size=TLL, LSP=LSF, LPO=0)
        self.Print("CMD: %s"%self.LastCmd)   
        #resultStrList = self.get_log_passthru(LID=0x2, size=1024, LSP=LSF, LPO=0)        #  TODO (LID=0xD, size=TLL, LSP=LSF, LPO=0)   
        resultStrList = [int("0x%s"%v, 16) for v in resultStrList]  # conver to int, e.x.  conver string resultStrList["ab", "57"] to resultStrList[0xab, 0x57]
        if resultStrList==None:
            self.Print("Command fail, CMD: %s"%self.LastCmd, "f") 
            mStr = self.shell_cmd(self.LastCmd)
            self.Print(mStr)
            return False 
        self.Print("Done")
        size = len(resultStrList)
        self.Print("Size of log data: %s"%size)
        self.Print("Check if size of log data = 'Total Log Length'(%s)"%TLL)
        if size==TLL:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            return False    
        self.SetPrintOffset(-4, "add")
     

        self.Print("")
        self.Print("5) Parser Persistent Events")
        self.SetPrintOffset(4, "add")
        if not self.ParserPersistentEventLogEvents(resultStrList):
            return False
        self.SetPrintOffset(-4, "add")
        self.Print("")
        return True    
    
    def PrintPEL(self):        
        self.Print("Show Persistent Event Log Events")          
        self.Print("")
        self.SetPrintOffset(4, "add")
        cnt=0
        for PersistentEventFormat in self.PELH.PersistentEventN:
            allAttrList= PersistentEventFormat.getOrderedAttributesList_curr()
            self.Print("---------------------------------------")
            self.Print("Persistent Event %s"%cnt, "b")
            self.Print("Persistent Event Log Event Header", "b")
            self.PrintListWithAlign(allAttrList, S0length=60, S1length=60) 
            self.Print("Persistent Event Log Event Data", "b")
            allAttrList= PersistentEventFormat.EventData.getOrderedAttributesList_curr()
            self.PrintListWithAlign(allAttrList, S0length=60, S1length=60) 
            cnt+=1
        self.SetPrintOffset(-4, "add")          
    
    def parserTimestamp(self, Timestamp):
        # Timestamp has remove byte 6 ( TimestampOrigin and Synch), ex. '0x017968B29BAE(2021-05-14 10:26:46)'
        # return int(Timestamp) and formated Timestamp, ex. 0x017968B29BAE, '2021-05-14 10:26:46'
        intT = 0
        fT = "None"
        searchStr = "(0x\w+)\((.+)\)"
        if re.search(searchStr, Timestamp): 
            intT = re.search(searchStr, Timestamp).group(1) 
            intT = int(intT, 16)
            intT = intT&0xFFFFFFFFFFFF # remove byte 6 ( TimestampOrigin and Synch)
            fT = re.search(searchStr, Timestamp).group(2)
        return intT, fT

    
    def __init__(self, argv):
        # initial parent class
        super(SMI_PersistentEventLog, self).__init__(argv)
        
        
        # Command Dword 10 – Log Specific Field
        self.LSF_ReadLogData = 0 
        self.LSF_EstablishContextAndReadLogData = 1 
        self.LSF_ReleaseContext = 2 
        
        self.PELH = self.PELH_()

        
        
        
        
        
        

    # define pretest, if not return 0 , skip all subcases
    def PreTest(self):     
        PersistentEventLogSupported = True if self.IdCtrl.LPA.bit(4)=="1" else False
        self.Print("Persistent Event log was supported(IdCtrl.LPA.bit(4)): %s"%("Yes" if PersistentEventLogSupported else "No"))
        #return 0 # TODO
        return 0 if PersistentEventLogSupported else 255
                   

    # <define sub item scripts>
    SubCase1TimeOut = 6000
    SubCase1Desc = "Parser Current Persistent Event log"   
    SubCase1KeyWord = ""
    def SubCase1(self):
        ret_code=0
        
        
        if not self.GetAndParserPEL():
            return 1
        
        self.Print ("")
        #self.Print ("Check Time EventTimestamp")
        
        self.PrintPEL()
   
            
        return ret_code

    SubCase2TimeOut = 6000
    SubCase2Desc = "Test Thermal Excursion Event (Event Type 0Dh)"   
    SubCase2KeyWord = "a temperature that is greater than or equal to TMT1, if any (i.e., light throttling has started)"
    def SubCase2(self):
        ret_code=0
        self.Print ("1) Back up Current PersistentEventLog")
        self.SetPrintOffset(4, "add")
        if not self.GetAndParserPEL():
            return 1
        self.SetPrintOffset(-4, "add")
        PELH_bk = copy.deepcopy(self.PELH) # backup self.PELH

        '''
        self.Print ("2) Back up Current TotalTimeForThermalManagementTemperature1")
        TTTMT1 = self.GetLog.SMART.TotalTimeForThermalManagementTemperature1
        TTTMT2 = self.GetLog.SMART.TotalTimeForThermalManagementTemperature2       
        self.Print ("")
        self.Print ("TTTMT1: %s"%TTTMT1)
        self.Print ("TTTMT2: %s"%TTTMT2)        
        self.Print ("")
        self.Print("3) Run Case 7 (Test HCTM functionality) in SMI_FeatureHCTM ")
        rtcode = self.runSubCase(SMI_FeatureHCTM, 7)    
        self.Print ("")    
        TTTMT1_n = self.GetLog.SMART.TotalTimeForThermalManagementTemperature1
        TTTMT2_n = self.GetLog.SMART.TotalTimeForThermalManagementTemperature2
        self.Print ("")
        self.Print ("-- befor HCTM test --")
        self.Print ("TTTMT1: %s"%TTTMT1)
        self.Print ("TTTMT2: %s"%TTTMT2)
        self.Print ("-- after test --")
        self.Print ("TMT1TC: %s"%TTTMT1_n)
        self.Print ("TMT2TC: %s"%TTTMT2_n)
        self.Print ("") 
        self.Print ("If TTTMT1 changed, Parser PersistentEventLog")
        self.Print ("")       
        if TTTMT1_n==TTTMT1:
            self.Print ("TTTMT1 not changed, skip")
            return 255
        
        self.Print ("")                       
        self.Print("4) Get and parser current PersistentEventLog")    
        if not self.GetAndParserPEL():
            ret_code =1    
            
        '''
        self.PELH.briefInfo.insert(1, "TTTTTTTTTTTT")
        self.PELH.briefInfo.insert(1, "UUUUUUUUUUU")
        self.PELH.briefInfo.insert(1, "VVVVVVVVV")
        self.Print ("")    
        self.Print("5) Print brief PersistentEventLog")        
        self.Print ("")
        self.SetPrintOffset(4, "add")
        
        if len(self.PELH.PersistentEventN)==0:
            self.Print ("Current number of PersistentEvent is 0, skip", "w")
            return 255
        
        #self.Print ("Find new PersistentEvent")
        OldList = PELH_bk.briefInfo[1:-1] # remove 1th line( title )
        for i in range(0, len(OldList)): 
            OldList[i] = re.sub("^\d+", "n/a", OldList[i]) # replace number to 'n/a' because number will be changed
            
        NewList = self.PELH.briefInfo[1:-1] # remove 1th line( title )
        for i in range(0, len(NewList)): 
            NewList[i] = re.sub("^\d+", "n/a", NewList[i]) # replace number to 'n/a' because number will be changed
                    
        pos = self.findStopAddrForFIFOList(NewList , OldList)
        if pos==-1:
            self.Print("Fail, can not find new PersistentEvent, please check below PersistentEvent!", "f")
            self.Print ("-- befor test --")
            self.Print ("briefInfo")
            for line in self.PELH.briefInfo:
                self.Print(line)           
            self.Print ("-- after test --")
            for line in PELH_bk.briefInfo:
                self.Print(line)    
            self.Print ("")
            return 1
        
        self.Print("New PersistentEvent from event 0 to event %s"%pos)
        self.Print("")
        self.Print("Green color: new PersistentEvent, black color, last PersistentEvent")        
        self.Print("------------------------------------------------------")
        cnt = 0
        for line in self.PELH.briefInfo:
            self.Print(line) if (cnt>pos+1 or cnt==0) else self.Print(line, "p") # +1 for title line
            cnt +=1
        self.SetPrintOffset(4, "add")
        
        self.Print("")
        
                          
        return ret_code 

    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_PersistentEventLog(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    