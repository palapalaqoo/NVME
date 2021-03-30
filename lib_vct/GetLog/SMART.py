'''
Created on Aug 10, 2018

@author: root
'''
from lib_vct.NVMECom import NVMECom
class SMART_(object, NVMECom):
    def __init__(self, obj):
        self._mNVME = obj
            
    @property
    def CriticalWarning(self):  
        return self.str2int(self._mNVME.get_log(0x02, 512, 0, 0))
    
    @property
    def CompositeTemperature(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 1, 2))
               
    @property
    def AvailableSpare(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 3, 3))

    @property
    def AvailableSpareThreshold(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 4, 4))

    @property
    def PercentageUsed(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 5, 5))

    @property
    def EnduranceGroupCriticalWarningSummary(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 6, 6))

    @property
    def DataUnitsRead(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 32, 47))

    @property
    def DataUnitsWritten(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 48, 63))

    @property
    def HostReadCommands(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 64, 79))

    @property
    def HostWriteCommands(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 80, 95))

    @property
    def ControllerBusyTime(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 96, 111))

    @property
    def PowerCycles(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 112, 127))

    @property
    def PowerOnHours(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 128, 143))

    @property
    def UnsafeShutdowns(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 144, 159))

    @property
    def MediaandDataIntegrityErrors(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 160, 175))

    @property
    def NumberofErrorInformationLogEntries(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 176, 191))

    @property
    def WarningCompositeTemperatureTime(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 192, 195))

    @property
    def CriticalCompositeTemperatureTime(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 196, 199))

    @property
    def TemperatureSensor1(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 200, 201))

    @property
    def TemperatureSensor2(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 202, 203))

    @property
    def TemperatureSensor3(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 204, 205))

    @property
    def TemperatureSensor4(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 206, 207))

    @property
    def TemperatureSensor5(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 208, 209))

    @property
    def TemperatureSensor6(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 210, 211))

    @property
    def TemperatureSensor7(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 212, 213))

    @property
    def TemperatureSensor8(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 214, 215))

    @property
    def ThermalManagementTemperature1TransitionCount(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 216, 219))

    @property
    def ThermalManagementTemperature2TransitionCount(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 220, 223))

    @property
    def TotalTimeForThermalManagementTemperature1(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 224, 227))

    @property
    def TotalTimeForThermalManagementTemperature2(self):         
        return self.str2int(self._mNVME.get_log(0x02, 512, 228, 231))




















































