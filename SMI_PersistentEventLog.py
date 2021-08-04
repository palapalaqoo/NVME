#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
import re
from time import sleep
import copy
import string
# Import VCT modules
from lib_vct.NVME import NVME
from lib_vct.NVMECom import OrderedAttributeClass
from SMI_FeatureHCTM import SMI_FeatureHCTM
from ftplib import FTP

class FormatClass():
# define parserFuncs
# self, FormatClass class inst
# inst, from outter, pass instant to this class, i.e. pass SMI_PersistentEventLog instant to inst
    def getFormatTime(self, inst, value):
        mStr = "0x%X(%s)"%(value, inst.getFormatTime(value))
        return mStr
    def intToHexStr(self, inst, value):
        return "0x%X"%value 

# class inherit from OrderedAttributeClass that can print ordered attributes
# MyOrderedField: [stop byte, start byte, type, parserFunc=None] where type 0=int, 1=string, 
# 2=not define and need to define type 2 in __init__ to reset after self.PELH_reset()
# ex. rtInst = self.PELH.SetFeature_()         #here will reload __init__ to reset default
# parserFunc: defined in FormatClass, if provided, value = parserFunc(value)
class PELH_(OrderedAttributeClass): 

    # end of define parserFuncs     
    LogIdentifier = OrderedAttributeClass.MyOrderedField((0, 0, 0))
    TNEV = OrderedAttributeClass.MyOrderedField((7, 4, 0))
    TLL = OrderedAttributeClass.MyOrderedField((15, 8, 0))
    LogRevision = OrderedAttributeClass.MyOrderedField((16, 16, 0))
    LogHeaderLength = OrderedAttributeClass.MyOrderedField((19, 18, 0))
    Timestamp = OrderedAttributeClass.MyOrderedField((27, 20, 0, FormatClass().getFormatTime))
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
        EventType = OrderedAttributeClass.MyOrderedField((0, 0, 0))
        EventTypeRevision = OrderedAttributeClass.MyOrderedField((1, 1, 0))
        EHL = OrderedAttributeClass.MyOrderedField((2, 2, 0))
        ControllerIdentifier = OrderedAttributeClass.MyOrderedField((5, 4, 0))
        EventTimestamp = OrderedAttributeClass.MyOrderedField((13, 6, 0,FormatClass().getFormatTime))
        VSIL = OrderedAttributeClass.MyOrderedField((21, 20, 0))
        EL = OrderedAttributeClass.MyOrderedField((23, 22, 0))
        VendorSpecificInformation = OrderedAttributeClass.MyOrderedField((0, 0, 2)) # need to defin in __init__
        EventData = None  
        def __init__(self):
            self.setOrderedAttributesList_init("VendorSpecificInformation", (0, 0, 2))
        
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
        def __init__(self):
            self.setOrderedAttributesList_init("CommandDwords", (0, 0, 2))    
            self.setOrderedAttributesList_init("MemoryBuffer", (0, 0, 2))
            self.setOrderedAttributesList_init("CommandCompletionDword0", (0, 0, 2))
                        
    class TelemetryLogCreated_(OrderedAttributeClass):
        TelemetryInitiatedLog = OrderedAttributeClass.MyOrderedField((511, 0, 0))
        
    class ThermalExcursion_(OrderedAttributeClass):
        OverTemperature = OrderedAttributeClass.MyOrderedField((0, 0, 0))
        Threshold = OrderedAttributeClass.MyOrderedField((1, 1, 0))
'''
vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
'''    
class SMI_PersistentEventLog(NVME):
    ScriptName = "SMI_PersistentEventLog.py"
    Author = ""
    Version = "20210804"
    
    def getPELHvalue(self, name):
        for i in range(len(self.PELH)):
            if name == self.PELH[i][0]:
                return self.PELH[i][1]
        return None

               
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
                if isString: # if is string, remove not printable char, e.g. 0x0
                    printable = set(string.printable)
                    value = filter(lambda x: x in printable, value)
                    value = value.strip() # remove front and tail spaces
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
        title = self.PrintAlignString("No:", "Start at:", "Stop at:", "Size:", "Type:", "Event Data at:", "Event Data end:", "EventTimestamp",  "EventTimestampReadable")
        self.PELH.briefInfo=[title] # clear and set title for briefInfo
        self.PELH.PersistentEventN=[] # clear
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
        ''' Timestamp may set to 0 because host have not set it after por/spor 
        self.Print("Check if EventTimestamp is counting up")
        if self.skipTimestampTest:
            self.Print("Skip EventTimestamp check")
        else:
            old = 0xFFFFFFFFFFFF
            curr = 0
            Timestamp_old  = ""
            cnt=0
            for Event in self.PELH.PersistentEventN:
                Timestamp = Event.EventTimestamp
                curr , os, formatedT = self.parserTimestamp(Timestamp)
    
                if curr>old:                
                    curr_n , os, formatedT_n = self.parserTimestamp(Timestamp_old)
                    self.Print("Fail at No: %s , formated Timestamp: %s,  Timestamp: %s"%(cnt-1, formatedT_n, curr_n), "f")
                    self.Print("Next at No: %s , formated Timestamp: %s,  Timestamp: %s"%(cnt, formatedT, curr), "f")
                    self.Print("")
                    if not self.mTestModeOn:
                        return False              
                cnt+=1
                old = curr
                Timestamp_old = Timestamp
            self.Print("Pass", "p")
        '''

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
        timeStampF = timeStamp
        mSearch =re.search("(\w+)\((.+)\)", timeStamp)
        if mSearch:
            timeStamp = mSearch.group(1)# raw value
            timeStampF= mSearch.group(2)#formated
        #self.PrintAlignString("No:", "Start at:", "Stop at:", "Size:", "Type:", "Event Data at:", "Event Data end:", "EventTimestamp", "EventTimestampReadable")       
        briefInfo = self.PrintAlignString(id, offset, offsetE, (EHLplusELplus2+1) ,\
                               EventType, "%s + %s"%(offset, EHLplus3plusVSIL), "%s + %s"%(offset, EHLplusELplus2), timeStamp, timeStampF)
        
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
            rtInst = self.PELH.SetFeature_()         #here will reload __init to reset default     
            aa = rtInst.getOrderedAttributesList_init()
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
            DwordCount = SetFeatureEventLayout & 7 # bit 2:0
            LoggedCommandCompletionDword0 = 0 if (SetFeatureEventLayout & 8)==0 else 1 # bit 3
            MemoryBufferCount = SetFeatureEventLayout >>16 # bit 31:16
                        
            stopByte = DwordCount*4+3 # spec
            startByte = 4            
            rtInst.setOrderedAttributesList_init("CommandDwords", (stopByte, startByte, 0, FormatClass().intToHexStr))
            if MemoryBufferCount==0: # if==0, then this field does not exist in the logged event
                rtInst.setOrderedAttributesList_init("MemoryBuffer", (stopByte, startByte, 2)) # set 2 to skip
            else:
                startByte =stopByte+1 # next filed, DwordCount*4+4
                # MemoryBufferCount in spec is 'Data Buffer Count'(1 base), MemoryBufferCount + DwordCount*4+4
                stopByte = MemoryBufferCount + startByte -1
                rtInst.setOrderedAttributesList_init("MemoryBuffer", (stopByte, startByte, 0, FormatClass().intToHexStr))         
            if LoggedCommandCompletionDword0==0: # if==0, then this field is not logged
                rtInst.setOrderedAttributesList_init("CommandCompletionDword0", (stopByte, startByte, 2)) # set 2 to skip
            else:
                startByte =stopByte+1 # next filed, MemoryBufferCount + DwordCount*4+5  
                stopByte = startByte+3 # MemoryBufferCount + DwordCount*4+8                                
                rtInst.setOrderedAttributesList_init("CommandCompletionDword0", (stopByte, startByte, 0, FormatClass().intToHexStr))
   
            # parser again to get CommandDwords, MemoryBuffer, CommandCompletionDword0
            self.SetClassWithRawData(rtInst, EventData, 0)
            
            
        return rtInst        
        

    def PrintAlignString(self,S0="", S1="", S2="", S3="", S4="", S5="", S6="", S7="", S8="", S9="", PF="default"):            
        mStr = "{:<4}{:<10}{:<10}{:<8}{:<10}{:<16}{:<16}{:<16}{:<16}{:<16}"\
        .format(S0, S1, S2, S3, S4, S5, S6, S7, S8, S9  )
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
        if TLL>self.PELSinByte:
            self.Print("Error,  Total Log Length(0x%X) > PELSinByte(0x%X)"%(TLL, self.PELSinByte), "f")
            self.SetPrintOffset(-4, "add")
            return False
        resultStrList = self.get_log_passthru(LID=0xD, size=TLL, LSP=LSF, LPO=0)
        self.Print("CMD: %s"%self.LastCmd)   
        #resultStrList = self.get_log_passthru(LID=0x2, size=1024, LSP=LSF, LPO=0)        #  TODO (LID=0xD, size=TLL, LSP=LSF, LPO=0)   
        resultStrList = [int("0x%s"%v, 16) for v in resultStrList]  # conver to int, e.x.  conver string resultStrList["ab", "57"] to resultStrList[0xab, 0x57]
        if resultStrList==None:
            self.Print("Command fail, CMD: %s"%self.LastCmd, "f") 
            mStr = self.shell_cmd(self.LastCmd)
            self.Print(mStr)
            self.SetPrintOffset(-4, "add")
            return False 
        self.Print("Done")
        size = len(resultStrList)
        self.Print("Size of log data: %s"%size)
        self.Print("Check if size of log data = 'Total Log Length'(%s)"%TLL)
        if size==TLL:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            self.SetPrintOffset(-4, "add")
            return False    
        self.SetPrintOffset(-4, "add")
     

        self.Print("")
        self.Print("5) Parser Persistent Events")
        self.SetPrintOffset(4, "add")
        if not self.ParserPersistentEventLogEvents(resultStrList):
            self.SetPrintOffset(-4, "add")
            return False
        self.SetPrintOffset(-4, "add")
        self.Print("")
        return True    
    
    def VerifyHeaderFields(self):
        isPass = True
        self.Print("Persistent Event Log -> Log Identifier : %s"%self.PELH.LogIdentifier)
        self.Print("Check if Log Identifier = 0xD")
        if self.PELH.LogIdentifier==0xD:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "p")
            isPass = False
        
        self.Print("")
        self.Print("Persistent Event Log -> Log Revision : %s"%self.PELH.LogRevision)
        self.Print("Check if Log Identifier = 0x1")
        if self.PELH.LogRevision==0x1:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "p")
            isPass = False
            
        self.Print("")
        TimestampPEL, OS, formatT = self.parserTimestamp(self.PELH.Timestamp)
        self.Print("Persistent Event Log -> Log Timestamp : 0x%X"%TimestampPEL)
        isSuccess, TimestampFeature, Origin, Synch, FormatedTimestamp = self.getTimeStamp()
        if not isSuccess:
            self.Print("Fail to get feature timestamp, CMD: %s "%self.LastCmd, "p"); return 1
        self.Print("Feature -> Timestamp : 0x%X"%TimestampFeature)
        # will not check Origin/Synch because ssd may fall into P4 mode, thus it may set or clear Synch
        self.Print("Check if Timestamp in Persistent Event Log  is approximately equal to Feature Timestamp(tolerance: 1 second )")       
        if (TimestampPEL+1000)>TimestampFeature:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            isPass = False    
            
        self.Print("")
        self.Print("Persistent Event Log -> Power on Hours (POH) : %s"%self.PELH.POH)
        POH_smart = self.GetLog.SMART.PowerOnHours
        self.Print("SMART/Health Log -> Power on Hours (POH) : %s"%POH_smart)
        self.Print("Check if POH in Persistent Event Log  is equal to POH in SMART/Health Log ")
        if self.PELH.POH==POH_smart:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            isPass = False            
            
        self.Print("")
        self.Print("Persistent Event Log -> Power Cycle Count : %s"%self.PELH.PowerCycleCount)
        PC = self.GetLog.SMART.PowerCycles
        self.Print("SMART/Health Log -> Power Cycle : %s"%PC)
        self.Print("Check if Power Cycle in Persistent Event Log  is equal to Power Cycle in SMART/Health Log ")
        if self.PELH.PowerCycleCount==PC:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            isPass = False  

        self.Print("")
        self.Print("Persistent Event Log -> PCI Vendor ID (VID) : %s"%self.PELH.VID)
        VID = self.IdCtrl.VID.int
        self.Print("Identify -> VID : %s"%VID)
        self.Print("Check if VID in Persistent Event Log  is equal to VID in identify data structure ")
        if self.PELH.VID==VID:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            isPass = False 

        self.Print("")
        self.Print("Persistent Event Log -> PCI Subsystem Vendor ID (SSVID) : %s"%self.PELH.SSVID)
        SSVID = self.IdCtrl.SSVID.int
        self.Print("Identify -> SSVID : %s"%SSVID)
        self.Print("Check if SSVID in Persistent Event Log  is equal to SSVID in identify data structure ")
        if self.PELH.SSVID==SSVID:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            isPass = False 

        self.Print("")
        self.Print("Persistent Event Log -> Serial Number (SN): %s"%self.PELH.SN)
        SN = self.IdCtrl.SN.str
        self.Print("Identify -> SN : %s"%SN)
        self.Print("Check if SN in Persistent Event Log  is equal to SN in identify data structure ")
        if self.PELH.SN==SN:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            isPass = False 

        self.Print("")
        self.Print("Persistent Event Log -> Model Number (MN): %s"%self.PELH.MN)
        MN = self.IdCtrl.MN.str
        self.Print("Identify -> MN : %s"%MN)
        self.Print("Check if MN in Persistent Event Log  is equal to MN in identify data structure ")
        if self.PELH.MN==MN:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            isPass = False 
            
        self.Print("")
        self.Print("Persistent Event Log -> NVM Subsystem NVMe Qualified Name (SUBNQN): %s"%self.PELH.SUBNQN)
        SUBNQN = self.IdCtrl.SUBNQN.str
        self.Print("Identify -> SUBNQN : %s"%SUBNQN)
        self.Print("Check if SUBNQN in Persistent Event Log  is equal to SUBNQN in identify data structure ")
        if self.PELH.SUBNQN==SUBNQN:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            isPass = False             
                    
        return isPass
    
    
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
        # Timestamp: string for PEL, format = value(formated time),  ex. '0x2017968B29BAE(2021-05-14 10:26:46)'
        # return int(Timestamp), int(TimestampOrigin and Synch) and string(formated Timestamp)
        # ex. 0x2017968B29BAE, '2021-05-14 10:26:46'
        intT = 0
        intOS = 0
        fT = "None"
        searchStr = "(0x\w+)\((.+)\)"
        if re.search(searchStr, Timestamp): 
            intT = re.search(searchStr, Timestamp).group(1) 
            intT = int(intT, 16)
            intOS = (intT>>48)&0xFF # TimestampOrigin and Synch
            intT = intT&0xFFFFFFFFFFFF # remove byte 6 ( TimestampOrigin and Synch)            
            fT = re.search(searchStr, Timestamp).group(2)
        return intT, intOS, fT

    def CheckNewPELwithTypeAndData(self, Range, Type, fieldInData): 
    # Range: last new PEL address, ex, new PEL at Persistent Event 0 to 4, set Range to 4
    # Type: Event Type
    # fieldInData: filed and expectedValue in Persistent Event Log Event Data, 
    # ex. for 'Threshold' in Event Data for Thermal Excursion Event, set fieldInData = [["Threshold", 0x4]]
    # for 'Threshold' and 'OverTemperature' , set to [["Threshold", 0x4], ["OverTemperature", 1]]
    # return find No in list type
        lastNewPos=Range
        rtList = []
        if self.mTestModeOn: lastNewPos = 20
        for i in range(lastNewPos+1):
            if self.PELH.PersistentEventN[i].EventType==Type: # Type match
                # check if all filed and value in fieldInData are match
                allMatch = True
                for fieldAndValue in fieldInData:
                    field = fieldAndValue[0]
                    expectedValue = fieldAndValue[1]
                    value = getattr(self.PELH.PersistentEventN[i].EventData, field)
                    if not value==expectedValue:
                        allMatch = False
                
                Ctype = "d" #black color, not find
                if allMatch: # print all field if match
                    rtList.append(i)
                    Ctype = "p" #green color, find
                    
                # print info
                self.Print("No: %s, Event Type: 0x%X"%(i, Type), Ctype)
                self.SetPrintOffset(4, "add")
                allAttrList= self.PELH.PersistentEventN[i].EventData.getOrderedAttributesList_curr()
                self.PrintListWithAlign(allAttrList, S0length=40, S1length=40, Ctype=Ctype)
                self.SetPrintOffset(-4, "add")                  

                
                    
        return rtList

    def VerifySpecificFieldWithSpecificEvent(self, TitleStart, EventType, Field, ExpectedValue, ExpectedValueDescription, triggerFunc):
    # return ret_code, ret_id(PersistentEventLog N that match request), , lastNewPos( new event id from 0 to lastNewPos)
    # TitleStart: title id start, and there are 5 step in this function
    # EventType: targeted EventType
    # Field: targeted field(SpecificField) in Persistent Event Log Event Data that will be checked
    # ExpectedValue: ExpectedValue that match the SpecificField, i.e. at matched EventType and Field, if Field value=ExpectedValue , then pass
    # ExpectedValueDescription:
    # triggerFunc: function(SpecificEvent) that will create the new PersistentEventLog
    
        ret_code = 0
        findList = []
        lastNewPos = 0
        self.Print ("%s) Back up Current PersistentEventLog"%TitleStart); TitleStart += 1
        self.SetPrintOffset(4, "add")
        if not self.GetAndParserPEL():
            ret_code = 1 #return 1
        self.SetPrintOffset(-4, "add")
        self.PELH_bk = copy.deepcopy(self.PELH) # backup self.PELH
        
        self.Print ("")
        self.Print ("%s) Try to make new PersistentEventLog"%TitleStart); TitleStart += 1
        self.SetPrintOffset(4, "add")
        self.Print ("Try to run function: %s()"%triggerFunc.__name__)
        triggerFunc()
        self.Print ("Done", "p")
        self.SetPrintOffset(-4, "add")
        
        self.Print ("")
        self.Print ("%s) Get and parser current PersistentEventLog"%TitleStart); TitleStart += 1
        self.SetPrintOffset(4, "add")
        if not self.GetAndParserPEL():
            ret_code = 1 #ret_code =1    
        self.SetPrintOffset(-4, "add")         
         
        self.Print ("")
        self.Print ("%s) Compare PersistentEventLog"%TitleStart); TitleStart += 1
        self.SetPrintOffset(4, "add")       
        if len(self.PELH.PersistentEventN)==0:
            self.Print ("Current number of PersistentEvent is 0, skip", "w")
            return 255, findList, lastNewPos
        
        self.Print ("Find new created PersistentEvent")
        OldList = []
        for Event in self.PELH_bk.PersistentEventN:
            OldList.append(Event.EventTimestamp)
        NewList = []      
        cnt = 0
        for Event in self.PELH.PersistentEventN:          
            NewList.append(Event.EventTimestamp) 
            cnt +=1 
            # sometimes old event will be delete, so check first 40 event is ok, i.e. Maximum number of event must <40 after doing SpecificEvent
            # keyword 'The number of events supported is vendor specific'
            if cnt ==40: break             
        lastNewPos = self.findStopAddrForFIFOList(NewList , OldList) # e.x. 0~4 is new created, lastNewPos will be 4
        if lastNewPos==-1:
            self.Print("Fail, can not find new PersistentEvent, please check below PersistentEvent!", "f")
            self.Print ("-- befor test --")
            for line in self.PELH_bk.briefInfo:
                self.Print(line)           
            self.Print ("-- after test --")
            for line in self.PELH.briefInfo:
                self.Print(line)    
            self.Print ("")        
            return 1, findList, lastNewPos
        
        self.Print("New PersistentEvent from event 0 to event %s"%lastNewPos)
        self.Print("")
        self.Print("Show PersistentEventLog, Green color: new PersistentEvent, black color: last PersistentEvent")        
        self.Print("------------------------------------------------------")
        cnt = 0
        for line in self.PELH.briefInfo:
            self.Print(line) if (cnt>lastNewPos+1 or cnt==0) else self.Print(line, "p") # +1 for title line
            cnt +=1
        self.SetPrintOffset(-4, "add")
        
        self.Print("%s) Check '%s' "%(TitleStart, ExpectedValueDescription)); TitleStart += 1 
        self.SetPrintOffset(4, "add")    
        findList = self.findMatchProperty(lastNewPos, EventType, Field, ExpectedValue, ExpectedValueDescription)
        if len(findList)!=0:
            self.Print("Pass!, %s th was matched"%( findList), "p")
        else:
            self.Print("Fail, can not find", "f")
            ret_code = 1
        self.SetPrintOffset(-4, "add")
                                
        return ret_code, findList, lastNewPos
    def triggerTotalTimeForThermalManagementTemperature1Change(self):
        TTTMT1 = self.GetLog.SMART.TotalTimeForThermalManagementTemperature1   
        self.Print("3) Run Case 7 (Test HCTM functionality) in SMI_FeatureHCTM to change")
        self.Print("SMARTHealthLog -> TotalTimeForThermalManagementTemperature1 and TotalTimeForThermalManagementTemperature2")
        self.SetPrintOffset(8, "add")
        #logPath=self.LogPath + "/HCTM_Case7"  
        #mCMD=["-p", logPath] # set log path to ./Log/HCTM_Case7
        #self.runSubCase(SMI_FeatureHCTM, 7, appendCMD=mCMD) # run
        self.runSubCase(SMI_FeatureHCTM, 7)
        self.SetPrintOffset(-8, "add")
        TTTMT1_n = self.GetLog.SMART.TotalTimeForThermalManagementTemperature1
        self.Print ("-- befor HCTM test --")
        self.Print ("TotalTimeForThermalManagementTemperature1: %s"%TTTMT1)
        self.Print ("-- after test --")
        self.Print ("TotalTimeForThermalManagementTemperature1: %s"%TTTMT1_n)
        return True if TTTMT1_n>TTTMT1 else False
   
                                
    def triggerUnsafeShutdown(self):
        self.spor_reset()
        return True

    def getEventName(self, EventType):
        if EventType==0x1:
            return "SMART / Health Log Snapshot"
        elif EventType==0x2:
            return "Firmware Commit"
        elif EventType==0x3:
            return "Timestamp Change"
        elif EventType==0x4:
            return "Power-on or Reset"
        elif EventType==0x5:
            return "NVM Subsystem Hardware Error"        
        elif EventType==0x6:
            return "Change Namespace"
        elif EventType==0x7:
            return "Format NVM Start"        
        elif EventType==0x8:
            return "Format NVM Completion"
        elif EventType==0x9:
            return "Sanitize Start"
        elif EventType==0xA:
            return "Sanitize Completion"
        elif EventType==0xB:
            return "Set Feature"
        elif EventType==0xC:
            return "Telemetry Log Created"
        elif EventType==0xD:
            return "Thermal Excursion"
        elif EventType==0xE:
            return "Vendor Specific Event"
        elif EventType==0xF:
            return "TCG Defined"  
        else:
            return "Reserved"
                  
    def findMatchProperty(self, lastNewPos, EventType, Field, ExpectedValue, ExpectedValueDescription): 
        self.Print("Check if there is any new PersistentEvent has below property")                 
        self.Print("PersistentEventN->EventType = 0x%X(%s)"%(EventType, self.getEventName(EventType)))
        self.Print("PersistentEventN->EventData->%s = 0x%X(%s)"%(Field, ExpectedValue, ExpectedValueDescription))
        self.Print("")
        self.Print("-----------------------------------------------------------")
        findList = self.CheckNewPELwithTypeAndData(Range=lastNewPos, Type=EventType, fieldInData=[[Field, ExpectedValue]])
        self.Print("-----------------------------------------------------------")
        return  findList
    
    def PELH_reset(self):
        # reset PELH_, i.e. run __init__ in all sub class
        self.PELH = self.PELH_()     

    def intToHexStr(self, value):
        return "0x%X"%value
               
    def __init__(self, argv):
        # initial parent class
        '''
        self.SetDynamicArgs(optionName="skip", optionNameFull="skipTimestampTest", \
                            helpMsg="if set to 1, skip timestamp test when parser PersistentEventLog"
                            "\ne.x. '-skip 1'", argType=int, default=0)     
        '''   
        super(SMI_PersistentEventLog, self).__init__(argv)
        
        #self.skipTimestampTest = False if self.GetDynamicArgs(0)==0 else True
        
        self.PELSinByte = 0
        
        # Command Dword 10 – Log Specific Field
        self.LSF_ReadLogData = 0 
        self.LSF_EstablishContextAndReadLogData = 1 
        self.LSF_ReleaseContext = 2 
        
        self.PELH = PELH_()
        self.PELH_bk = None

        
        
        
        
        
        

    # define pretest, if not return 0 , skip all subcases
    def PreTest(self):     
        PersistentEventLogSupported = True if self.IdCtrl.LPA.bit(4)=="1" else False
        self.Print("Persistent Event log was supported(IdCtrl.LPA.bit(4)): %s"%("Yes" if PersistentEventLogSupported else "No"))
        #return 0 # TODO
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x1 2>&1"%self.dev_port
        mStr = self.shell_cmd(CMD)
        mList = self.AdminCMDDataStrucToListOrString(mStr, 2)        
        PELS = mList[352]+(mList[353]<<8)+(mList[354]<<16)+(mList[355]<<24)
        self.PELSinByte = PELS * 64 *1024
        self.Print("Maximum reportable Persistent Event Log Size (PELS): %s (0x%X bytes)"%(PELS, self.PELSinByte))
        if not PersistentEventLogSupported:
            return 255
        elif self.PELSinByte == 0:
            self.Print("Error!, Persistent Event Log Size (PELS) ==0 when Persistent Event log was supported", "f")
            return 1
        return 0
                   

    # <define sub item scripts>
    SubCase1TimeOut = 6000
    SubCase1Desc = "Parser Current Persistent Event log"   
    SubCase1KeyWord = "https://jira.siliconmotion.com.tw:8443/browse/VCTDEPT-763"
    def SubCase1(self):
        ret_code=0
                
        if not self.GetAndParserPEL():
            return 1
        
        self.Print ("")
        if  not self.VerifyHeaderFields():
            ret_code = 1
        #self.Print ("Check Time EventTimestamp")
        self.Print ("")
        self.PrintPEL()
   
            
        return ret_code

    SubCase2TimeOut = 6000
    SubCase2Desc = "Test Thermal Excursion Event (Event Type 0Dh)"   
    SubCase2KeyWord = "a temperature that is greater than or equal to TMT1, if any (i.e., light throttling has started)"
    def SubCase2(self):
        TitleStart = 1 
        self.Print ("%s) Back up Current TotalTimeForThermalManagementTemperature1"%TitleStart); TitleStart+=1
        TTTMT1 = self.GetLog.SMART.TotalTimeForThermalManagementTemperature1
        TTTMT2 = self.GetLog.SMART.TotalTimeForThermalManagementTemperature2
        self.Print ("")
        self.SetPrintOffset(4, "add")
        self.Print ("TTTMT1: %s"%TTTMT1)
        self.Print ("TTTMT2: %s"%TTTMT2)
        self.SetPrintOffset(-4, "add")
        self.Print("")
        EventType = 0xD
        Field="Threshold"
        ExpectedValue=0x3
        ExpectedValueDescription="temperature is greater than or equal to TMT1"
        triggerFunc = self.triggerTotalTimeForThermalManagementTemperature1Change
        ret_code, findList, lastNewPos =  self.VerifySpecificFieldWithSpecificEvent(TitleStart, EventType, Field\
                                                         , ExpectedValue, ExpectedValueDescription, triggerFunc)
        TitleStart +=5 # there are 5 step in VerifySpecificFieldWithSpecificEvent       
        self.Print("")
        TTTMT1_n = self.GetLog.SMART.TotalTimeForThermalManagementTemperature1
        TTTMT2_n = self.GetLog.SMART.TotalTimeForThermalManagementTemperature2
        self.Print ("")
        self.Print("%s) Print TotalTimeForThermalManagementTemperature1 and TotalTimeForThermalManagementTemperature2 "%TitleStart); TitleStart+=1
        self.SetPrintOffset(4, "add")
        self.Print ("-- befor HCTM test --")
        self.Print ("TTTMT1: %s"%TTTMT1)
        self.Print ("TTTMT2: %s"%TTTMT2)
        self.Print ("-- after test --")
        self.Print ("TMT1TC: %s"%TTTMT1_n)
        self.Print ("TMT2TC: %s"%TTTMT2_n)
        if TTTMT1==TTTMT1_n: # TTTMT1 has not changed
            self.Print("Warnning, TotalTimeForThermalManagementTemperature1 has not changed, skip", "w") 
            return 0
        self.SetPrintOffset(-4, "add")        
        if ret_code!=0: return ret_code # if fail
        # else pass TTTMT1 verification, try to verify TTTMT2

        self.Print("")
        EventType = 0xD
        Field="Threshold"
        ExpectedValue=0x4
        ExpectedValueDescription="temperature is greater than or equal to TMT2"       
        self.Print("%s) Check '%s' "%(TitleStart, ExpectedValueDescription)); TitleStart += 1 
        self.SetPrintOffset(4, "add")
        if TTTMT2==TTTMT2_n:
            self.Print("TotalTimeForThermalManagementTemperature2 has not changed, skip", "w")
        else:                     
            # using findMatchProperty to verify another field after VerifySpecificFieldWithSpecificEvent
            findList = self.findMatchProperty(lastNewPos, EventType, Field, ExpectedValue, ExpectedValueDescription) 
            if len(findList)!=0:
                self.Print("Pass!, No: %s matched"%( findList), "p")
            else:
                self.Print("Fail, can not find", "f")
                ret_code = 1               
        self.SetPrintOffset(-4, "add")
        
        return ret_code

    SubCase3TimeOut = 6000
    SubCase3Desc = "Test NVM Subsystem Hardware Error Event Test (Event Type 05h)"   
    SubCase3KeyWord = ""
    def SubCase3(self):    
        UnsafeShutdowns = self.GetLog.SMART.UnsafeShutdowns  
        self.Print("Current UnsafeShutdowns: %s"%UnsafeShutdowns) 
        self.Print("")
        TitleStart = 1  
        EventType=0x5
        Field="NVMSubsystemHardwareErrorEventCode"
        ExpectedValue=0x8
        ExpectedValueDescription="Unsafe Shutdown"
        triggerFunc = self.triggerUnsafeShutdown
        ret_code, findList, lastNewPos =  self.VerifySpecificFieldWithSpecificEvent(TitleStart, EventType, Field\
                                                         , ExpectedValue, ExpectedValueDescription, triggerFunc)
        if ret_code!=0: return ret_code # if fail
        TitleStart +=5 # there are 5 step in VerifySpecificFieldWithSpecificEvent
        if len(findList)==0:
            self.Print("Fail, findList=%s"%findList, "f") 
            return 1
        no = findList[0] # verify first event in findList
                
        self.Print("")
        self.Print("%s) Check if Current PersistentEventN[%s]->EventData->AdditionalHardwareErrorInformation"%(TitleStart, no)); TitleStart+=1
        self.Print("is the same as the Unsafe Shutdowns field in the SMART / Health Information log at the time of the event")
        self.Print("")
        self.SetPrintOffset(4, "add")
        UnsafeShutdowns = self.GetLog.SMART.UnsafeShutdowns
        AHEI = self.PELH.PersistentEventN[no].EventData.AdditionalHardwareErrorInformation
        self.Print("Current UnsafeShutdowns: %s"%UnsafeShutdowns)    
        self.Print("Current PersistentEventN[%s]->EventData->AdditionalHardwareErrorInformation: %s"%(no, AHEI)) 
        if  UnsafeShutdowns==AHEI:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")  
            ret_code = 1          
        self.SetPrintOffset(-4, "add")
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

    
    
    
    