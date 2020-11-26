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
    class PELH_(OrderedAttributeClass): 
             
        LogIdentifier = OrderedAttributeClass.MyOrderedField((0, 0, 0))
        TNEV = OrderedAttributeClass.MyOrderedField((7, 4, 0))
        TLL = OrderedAttributeClass.MyOrderedField((15, 8, 0))
        LogRevision = OrderedAttributeClass.MyOrderedField((16, 16, 0))
        LogHeaderLength = OrderedAttributeClass.MyOrderedField((19, 18, 0))
        Timestamp = OrderedAttributeClass.MyOrderedField((27, 20, 0))
        POH = OrderedAttributeClass.MyOrderedField((43, 28, 0))
        PowerCycleCount = OrderedAttributeClass.MyOrderedField((51, 44, 0))
        VID = OrderedAttributeClass.MyOrderedField((53, 52, 1))
        SSVID = OrderedAttributeClass.MyOrderedField((55, 54, 1))
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
            NVMSubsystemHardwareErrorEventSupport = OrderedAttributeClass.MyOrderedField(())
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
            self.PersistentEventFormat = self.PersistentEventFormat_()
            self.EventNotDefine = self.EventNotDefine_()
            self.SMARTHealthLogSnapshot = self.SMARTHealthLogSnapshot_()
            self.FirmwareCommit = self.FirmwareCommit_()
            self.TimestampChange = self.TimestampChange_()
            self.Power_onorReset = self.Power_onorReset_()

        class PersistentEventFormat_(OrderedAttributeClass):
            EventType = OrderedAttributeClass.MyOrderedField((0, 0, 0))
            EventTypeRevision = OrderedAttributeClass.MyOrderedField((1, 1, 0))
            EHL = OrderedAttributeClass.MyOrderedField((2, 2, 0))
            ControllerIdentifier = OrderedAttributeClass.MyOrderedField((5, 4, 0))
            EventTimestamp = OrderedAttributeClass.MyOrderedField((13, 6, 0))
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
            FirmwareRevision = OrderedAttributeClass.MyOrderedField((7, 0, 0))
            
            def __init__(self):
                ResetInformationList = [] #OrderedAttributeClass.MyOrderedField((0, 0, 0))    
                self.ControllerResetInformationdescriptor = self.ControllerResetInformationdescriptor_()

            class ControllerResetInformationdescriptor_(OrderedAttributeClass):
                ControllerID = OrderedAttributeClass.MyOrderedField((1, 0, 0))
                FirmwareActivation = OrderedAttributeClass.MyOrderedField((2, 2, 0))
                OperationinProgress = OrderedAttributeClass.MyOrderedField((3, 3, 0))
                ControllerPowerCycle = OrderedAttributeClass.MyOrderedField((19, 16, 0))
                Poweronmilliseconds = OrderedAttributeClass.MyOrderedField((27, 20, 0))
                ControllerTimestamp = OrderedAttributeClass.MyOrderedField((35, 28, 0))                

    
    # not used
    def SetPELHwithRawData(self, classIn, listRawData, offset):
        # classIn, ex, self.PELH
        allList = classIn.getOrderedAttributesList_init() # self.PELH.getOrderedAttributesList_init()
        for mList in allList:
            name = mList[0] # LogIdentifier
            argList = mList[1]
            stopByte = offset + argList[0]
            startByte = offset + argList[1]
            isString=True if argList[2] == 1 else False
            isSkip=True if argList[2] == 2 else False
            if isSkip:
                setattr(classIn, name, None)
            else:
                setattr(classIn, name, self.GetBytesFromList(listRawData, stopByte, startByte, isString))
            
    
    def ParserPersistentEventLogHeader(self, listRawData):
    # note: listRawData is list type with int element, ex [0x15, 0x26]
        mLen = len(listRawData)
        if mLen!=512:
            self.Print("ParserPersistentEventLogHeader: header size not correct, expect 512byte, current = %s"%len)
            return False

        self.SetPELHwithRawData(self.PELH, listRawData, 0)
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
            else:
                offsetS = offsetE +1
                
        if self.PELH.TLL!=offsetE:
            self.Print("Error!, Total Log Length(%s) in Persistent Event Log Header is not equal to the last byte address(%s) of last PersistentEvent"\
                       %(self.PELH.TLL, offsetE), "f")            
            return False

        return True

    def GetPersistentEventN(self, listRawData, offset):
        # class inst
        rtInst = self.PELH.PersistentEventFormat
        self.SetPELHwithRawData(rtInst, listRawData, offset)# PersistentEventFormat start from offset of  listRawData
        
        EHL = rtInst.EHL # Event Header Length = EHL+3
        VSIL = rtInst.VSIL # Vendor Specific Information Length
        EHLplus3 = EHL+3
        EHLplus2plusVSIL = EHL+2+VSIL # also = EHL+3 + VSIL -1
        VendSpecInfo = listRawData[offset+EHLplus3: offset+EHLplus2plusVSIL+1]
        rtInst.VendorSpecificInformation = VendSpecInfo
        
        EL = rtInst.EL # Event Length =  Vendor Specific Information Length +  Event Data length
        EHLplusELplus2 = EHL+EL+2 # also = EHL+3 + EL -1
        EHLplus3plusVSIL = EHL+3+VSIL # also = EHL+3 + VSIL -1 +1
        EventData = listRawData[offset+EHLplusELplus2: offset+EHLplus3plusVSIL +1]
        EventData = listRawData[0: 512] # TODO
        
        EventType= rtInst.EventType       
        EventType=0x4 # TODO 
        self.Print("Offset: %s, EventType: %s"%(offset, EventType))
        #parset raw data to structure
        rtInst.EventData = self.ParserEventData(EventData, EventType, rtInst)
        
        return rtInst, offset+EHLplus3plusVSIL #return next offset
            
    
    def ParserEventData(self, EventData, EventType, rtInst):
    # rtInst = self.PELH.PersistentEventFormat
        expectSize=0
        if EventType==0x1:
            expectSize = 512 #according to spec, size=512byte
            # class inst
            rtInst = self.PELH.SMARTHealthLogSnapshot            
        elif EventType==0x2:
            expectSize = 22
            rtInst = self.PELH.FirmwareCommit 
        elif EventType==0x3:
            expectSize = 16
            rtInst = self.PELH.TimestampChange
        elif EventType==0x4:
            EL_VSIL_1 = rtInst.EL - rtInst.VSIL - 1
            expectSize = EL_VSIL_1 +1 # Figure 217: Power-on or Reset Event (Event Type 04h)
            rtInst = self.PELH.Power_onorReset   
        else:
            self.Print("Error!, EventType undefined: %s"%EventType, "f")   
            rtInst = self.PELH.EventNotDefine
            return rtInst     
        
        if len(EventData)!=expectSize:
            self.Print("Error, EventType=%s, EventData expect size: %s, current size: %s"%(EventType, expectSize, len(EventData)), "f")
            return rtInst        

        self.SetPELHwithRawData(rtInst, EventData, 0) # class inst data start from offset 0 of  EventData
        if EventType==0x4:
            descriptorSize = EL_VSIL_1 -8+1
            ControllerResetInformationdescriptorSize = 36 # spec is 36 for every scriptor
            if descriptorSize%ControllerResetInformationdescriptorSize!=0:
                self.Print("Error, EventType==0x4, parsered descriptorSize(EL_VSIL_1 - 8 +1) = %s, not multiple of %s(ControllerResetInformationdescriptorSize)"\
                           (descriptorSize, ControllerResetInformationdescriptorSize))
                return rtInst
                        
            # parser ControllerResetInformationdescriptor_
            loop = descriptorSize/ControllerResetInformationdescriptorSize
            offset = 8 # start for offset = 8
            for i in range(loop):
                scripterInst = rtInst.ControllerResetInformationdescriptor
                self.SetPELHwithRawData(scripterInst, EventData, offset) 
                rtInst.ResetInformationList.append(scripterInst)
                offset+=ControllerResetInformationdescriptorSize
        
        return rtInst        
        
    
    def __init__(self, argv):
        # initial parent class
        super(SMI_PersistentEventLog, self).__init__(argv)
        
        
        # Command Dword 10 – Log Specific Field
        self.LSF_ReadLogData = 0 <<8
        self.LSF_EstablishContextAndReadLogData = 1 <<8
        self.LSF_ReleaseContext = 2 <<8
        
        self.PELH = self.PELH_()

        
        
        
        
        
        

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
        allAttrList= self.PELH.getOrderedAttributesList_curr()
        self.PrintListWithAlign(allAttrList, S0length=60, S1length=60)  
                         
        allAttrList= self.PELH.SupportedEventsBitmap.getOrderedAttributesList_curr()
        self.PrintListWithAlign(allAttrList, S0length=60, S1length=60)             

        self.Print("")
        self.Print("Persistent Event Log Events", "b")   
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
            
            






        return ret_code

    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_PersistentEventLog(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    