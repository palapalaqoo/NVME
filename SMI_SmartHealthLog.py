#!/usr/bin/env python
# -*- coding: utf-8 -*-

        #=======================================================================
        # abstract  function
        #     SubCase1() to SubCase32()                            :Override it for sub case 1 to sub case32
        # abstract  variables
        #     SubCase1Desc to SubCase32Desc                 :Override it for sub case 1 description to sub case32 description
        #     SubCase1Keyword to SubCase32Keyword    :Override it for sub case 1 keyword to sub case32 keyword
        #     self.ScriptName, self.Author, self.Version      :self.ScriptName, self.Author, self.Version
        #=======================================================================     
        
# Import python built-ins
import sys
import time
from time import sleep
import threading
import re
import subprocess
# Import VCT modules
from lib_vct.NVME import NVME
from lib_vct.NVME import DevWakeUpAllTheTime
class SMI_SmartHealthLog(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_SmartHealthLog.py"
    Author = "Sam Chan"
    Version = "20210820"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
  

    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    
    def GetTMPTH(self, Sel):
        if Sel=="over":
            buf=self.get_feature(fid=4)
        elif Sel=="under":
            buf=self.get_feature(fid=4, cdw11=0x100000)
        else:
            buf="0"
        
        TMPTH=0    
        mStr="Current value:(.*)"
        if re.search(mStr, buf):
            TMPTH=int(re.search(mStr, buf).group(1),16)    
        
        TMPTH=TMPTH&0xFFFF
        return TMPTH
    
    def SetTMPTH(self, Sel, value):
        if Sel=="over":
            pass
        elif Sel=="under":
            value=value|(1<<20)
        else:
            pass
        self.set_feature(fid=4, value=value)           
    
    def GetCriticalWarningBit1(self):
        CriticalWarning=self.GetLog.SMART.CriticalWarning
        return "1" if CriticalWarning&(1<<1) else "0"

    def GetNSID(self):
        # for SR-IOV nsid may not equal to Y where Y from '/dev/nvmeXnY'
        rtStr = self.shell_cmd("nvme id-ns %s  2>&1"%self.dev)
        mStr = "NVME Identify Namespace (\w*)"
        if re.search(mStr, rtStr):   
            nsid = re.search(mStr, rtStr).group(1)
        else:
            nsid = 0
        return nsid

    def trigger_error_event(self): 
        nsid = self.GetNSID()
        #print "%s"%nsid
        self.shell_cmd("  buf=$( nvme write-uncor %s -s 0 -n %s -c 127 2>&1 >/dev/null )"%(self.dev, nsid))
        self.shell_cmd("  buf=$( nvme read %s -s 0 -z 512 -c 0 2>&1 >/dev/null )"%(self.dev))

        # clear write-uncor 
        self.shell_cmd("  buf=$(nvme write-zeroes %s -s 0 -c 127 2>&1 > /dev/null) "%(self.dev))         

    def testUnsafeShutdowns(self, Mode="POR"):
        # Mode = POR or SPOR
        UnsafeShutdowns0=self.GetLog.SMART.UnsafeShutdowns
        self.Print("")
        self.Print("Get current 'Unsafe Shutdowns': %s"%UnsafeShutdowns0)
        if Mode=="POR":
            self.Print("Do POR")
            if not self.por_reset():
                self.Print("Fail to power off and on device!, please check power module, quit", "f")
                return False
        else:
            self.Print("Do SPOR")
            if not self.spor_reset():
                self.Print("Fail to power off and on device!, please check power module, quit", "f")
                return False
                            
        self.Print("Done")
        sleep(2)
        UnsafeShutdowns1=self.GetLog.SMART.UnsafeShutdowns
        self.Print("Get current 'Unsafe Shutdowns': %s"%UnsafeShutdowns1)    
        
        self.Print("")   
        if Mode=="POR":
            ExpValue = UnsafeShutdowns0
            self.Print("Check if 'Unsafe Shutdowns' changed or not, expect value: %s(not changed for POR))"%ExpValue)            
        else:
            ExpValue = UnsafeShutdowns0+1
            self.Print("Check if 'Unsafe Shutdowns' changed or not, expect: %s(last value+1 for SPOR))"%ExpValue)

        if UnsafeShutdowns1==ExpValue:
            self.Print("Pass", "p")
            return True
        else:
            self.Print("Fail", "f")    
            return False           

    def GetHealthLog(self):
        Value=[]
        Value.append(["CompositeTemperature", self.GetLog.SMART.CompositeTemperature])
        Value.append(["CriticalWarning", self.GetLog.SMART.CriticalWarning])
        Value.append(["AvailableSpare", self.GetLog.SMART.AvailableSpare])
        Value.append(["AvailableSpareThreshold", self.GetLog.SMART.AvailableSpareThreshold])
        Value.append(["PercentageUsed", self.GetLog.SMART.PercentageUsed])
        Value.append(["DataUnitsRead", self.GetLog.SMART.DataUnitsRead])
        Value.append(["DataUnitsWritten", self.GetLog.SMART.DataUnitsWritten])
        Value.append(["HostReadCommands", self.GetLog.SMART.HostReadCommands])
        Value.append(["HostWriteCommands", self.GetLog.SMART.HostWriteCommands])
        Value.append(["ControllerBusyTime", self.GetLog.SMART.ControllerBusyTime])
        Value.append(["PowerCycles", self.GetLog.SMART.PowerCycles])
        Value.append(["PowerOnHours", self.GetLog.SMART.PowerOnHours])
        Value.append(["UnsafeShutdowns", self.GetLog.SMART.UnsafeShutdowns])
        Value.append(["MediaandDataIntegrityErrors", self.GetLog.SMART.MediaandDataIntegrityErrors])
        Value.append(["NumberofErrorInformationLogEntries", self.GetLog.SMART.NumberofErrorInformationLogEntries])
        Value.append(["WarningCompositeTemperatureTime", self.GetLog.SMART.WarningCompositeTemperatureTime])
        Value.append(["CriticalCompositeTemperatureTime", self.GetLog.SMART.CriticalCompositeTemperatureTime])
        Value.append(["ThermalManagementTemperature1TransitionCount", self.GetLog.SMART.ThermalManagementTemperature1TransitionCount])
        Value.append(["ThermalManagementTemperature2TransitionCount", self.GetLog.SMART.ThermalManagementTemperature2TransitionCount])
        Value.append(["TotalTimeForThermalManagementTemperature1", self.GetLog.SMART.TotalTimeForThermalManagementTemperature1])
        Value.append(["TotalTimeForThermalManagementTemperature2", self.GetLog.SMART.TotalTimeForThermalManagementTemperature2])
        return Value

    def VerifyHealthLog(self, OriginalValue, expectAdd1List=[], expectGreatOrEqualList=[]):
        self.Print ("Get current SMART / Health Log ")
        CurrentValue=self.GetHealthLog()
        self.Print ("Check if SMART / Health Log is retained")
        SkipItemList = []
        SkipItemList.append("CompositeTemperature")
        SkipItemList.append("WarningCompositeTemperatureTime")
        SkipItemList.append("CriticalCompositeTemperatureTime")
        SkipItemList.append("ThermalManagementTemperature1TransitionCount")
        SkipItemList.append("ThermalManagementTemperature2TransitionCount")
        SkipItemList.append("TotalTimeForThermalManagementTemperature1")
        SkipItemList.append("TotalTimeForThermalManagementTemperature2")
        
        # print 
        self.Print ("")  
        self.Print ("Note: below fields will not be checked")
        for i in SkipItemList:
            self.Print(i, "b")
        if len(expectAdd1List)!=0:
            self.Print ("")
            self.Print ("Note: expected value of below fields are original values +1 ")
            for i in expectAdd1List:
                self.Print(i, "b")       
        if len(expectGreatOrEqualList)!=0:
            self.Print ("")
            self.Print ("Note: expected value of below fields are greater or equal original values ")
            for i in expectGreatOrEqualList:
                self.Print(i, "b")                                     
        self.Print ("")   
        self.Print ("Note: black text: value remained, red text: value fail, yellow text: value changed")     

        ValueRetained=True
        self.Print ("---------------------------------------------------------------------------------------------------")
        mStr = "{:<60}\t{:<20}\t{:<20}".format("Field", "Original", "Current")
        self.Print(mStr, "b" )        
        for i in range(len(OriginalValue)): 
            itemPass = True               
            original=OriginalValue[i][1] 
            current=CurrentValue[i][1]
            Name =  OriginalValue[i][0]
            # print field name            
            mStr = "{:<60}\t{:<20}\t{:<20}".format(Name, original, current)
            # check value
            intOriginal = int(original)
            intCurrent = int(current)
            
            if Name in SkipItemList:
                pass
            # PowerCycles, UnsafeShutdowns
            elif Name in expectAdd1List: # expect original+1
                if intCurrent!=intOriginal+1:
                    itemPass=False
            elif Name in expectGreatOrEqualList: # expect >= original
                if intCurrent<intOriginal:
                    itemPass=False                
            else:
                if intCurrent!=intOriginal:
                    itemPass=False                
                
            if itemPass:
                # set color
                if intCurrent==intOriginal:
                    color = "b"
                else:
                    color = "w"
                self.Print(mStr, color)
            else:
                self.Print(mStr, "f")
                ValueRetained=False
            
        self.Print ("---------------------------------------------------------------------------------------------------")
        if ValueRetained:                
            self.Print("PASS", "p")
            return True
        else:
            self.Print("FAIL", "f")
            return False        

    def PrintAlignString(self,S0="", S1="", S2="", S3="", S4="", S5="", S6="", PF="default"):            
        mStr = "{:<8}{:<8}{:<28}{:<8}{:<8}{:<28}{:<28}".format(S0, S1, S2, S3, S4, S5, S6)
        if PF=="pass":
            self.Print( mStr , "p")        
        elif PF=="fail":
            self.Print( mStr , "f")      
        else:
            self.Print( mStr )  

    def RaisingTempture(self, TargetTemp, TimeOut):
    # TimeOut = time limit in secend
    # TargetTemp =temp in Kelvin degree
    # Return last tempture read from controller
        TimeCnt=0
        aa=time.time()
        TempNow=0
        # using DevWakeUpAllTheTime
        Inst = DevWakeUpAllTheTime(self, False)
        Inst.Start() # thread start to read all the time
        while True:                     
            sleep(1)            
            TimeCnt= int(time.time()-aa)  
            TempNow = self.GetLog.SMART.CompositeTemperature
            mSuffix="Temperature: %s °C"%(self.KelvinToC(TempNow))
            
            # progressbar
            if TimeCnt<TimeOut:
                self.PrintProgressBar(TimeCnt, TimeOut, prefix = 'Time Usage:', suffix = mSuffix, length = 50)
            else:
                self.PrintProgressBar(TimeOut, TimeOut, prefix = 'Time Usage:', suffix = mSuffix, length = 50)
                self.Print ("After %s s, time out !,  stop to increase temperature !"%TimeOut)
                break
                    
            if TempNow>=TargetTemp: 
                self.Print ("")
                self.Print ("After %s s, CompositeTemperature is large then %s(%s °C)!"%(TimeCnt, TargetTemp, self.KelvinToC(TargetTemp)))
                break
        Inst.Stop()
        return TempNow

    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def __init__(self, argv):
        self.SetDynamicArgs(optionName="v", optionNameFull="version", \
                            helpMsg="nvme spec version, 1.3c / 1.3d, default= 1.3c"
                            "\ne.x. '--version 1.3d'", argType=str, default="1.3c")
        self.SetDynamicArgs(optionName="PUS100", optionNameFull="PUS100", \
                            helpMsg="PercentageUsedScale for case 16 that will set PercentageUsed to 100"
                            "\ne.x for SKH, formula of PercentageUsed in SMART log is"\
                            "\n(sum of all block erase count/total erase block)/7000"\
                            "\nso run script with '-PUS100 7000'", argType=int, default=7000)                
        # initial parent class
        super(SMI_SmartHealthLog, self).__init__(argv)
        
        self.specVer = self.GetDynamicArgs(0)
        self.PUS100 = self.GetDynamicArgs(1)
        
        
        self.Print ("Check if the controller supports the Compare command or not in identify - ONCS")   
        self.CompareSupported=self.IdCtrl.ONCS.bit(0)    
        self.CompareSupported=True if self.CompareSupported=="1" else False
        self.Print ("Compare command supported", "p") if self.CompareSupported else self.Print ("Compare command not supported", "f")
                
        self.Print ("")
        self.Print ("Check if the controller supports the Write Uncorrectable command or not in identify - ONCS")   
        self.WriteUncSupported=self.IdCtrl.ONCS.bit(1)    
        self.WriteUncSupported=True if self.WriteUncSupported=="1" else False
        self.Print ("Write Uncorrectable command supported", "p") if self.WriteUncSupported else self.Print ("Write Uncorrectable command not supported", "f")        
        self.Print ("")
        
        self.MaxBlockCnt= self.MaxNLBofCDW12()
    # <sub item scripts>
    SubCase1TimeOut = 60
    SubCase1Desc = "Test critical warnings"        
    def SubCase1(self):
        ret_code=0
        
        LiveT=self.GetLog.SMART.CompositeTemperature
        WCTEMP=self.IdCtrl.WCTEMP.int
        
        if WCTEMP!=0:
            self.Print("Set TMPTH over to WCTEMP(%s °C)"%self.KelvinToC(WCTEMP))
            self.SetTMPTH("over", WCTEMP)
            self.Print("Set TMPTH under to 0 °C")
            self.SetTMPTH("under", self.CToKelvin(0))
                        
        TMPTH_over=self.GetTMPTH(Sel="over")
        TMPTH_under=self.GetTMPTH(Sel="under")
        self.Print("Now TMPTH over: %s °C"%self.KelvinToC(TMPTH_over)) 
        self.Print("Now TMPTH under: %s °C"%self.KelvinToC(TMPTH_under)) 

        self.Print("")
        self.Print("test the over temperature threshold Feature")   
        self.Print("")
        self.Print("The temperature is %s °C now and TMPTH over is setting to 10 °C, Over Temperature Threshold test"%self.KelvinToC(LiveT))
        self.SetTMPTH("over", 0x11B)
        
        self.Print("Check Critical Warning bit 1, expect value=1")        
        CWarningBit1=self.GetCriticalWarningBit1()         
        if CWarningBit1=="1":
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")   
            ret_code=1
            
        self.Print("")
        self.Print("The temperature is %s °C now and TMPTH over is setting to 60 °C, Over Temperature Threshold test"%self.KelvinToC(LiveT))
        self.SetTMPTH("over", 0x14D)
        
        self.Print("Check Critical Warning bit 1, expect value=0")        
        CWarningBit1=self.GetCriticalWarningBit1()         
        if CWarningBit1=="0":
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")   
            ret_code=1        
            
        self.Print("")             
        self.Print("Reset TMPTH over to %s"%self.KelvinToC(TMPTH_over) )
        self.SetTMPTH("over", TMPTH_over)
        
        #-----------------------------------------------------------------------
        if WCTEMP!=0:
            self.Print("") 
            self.Print("WCTEMP is %s = %s °C(not zero value), so have to test the under temperature threshold Feature"%(WCTEMP, self.KelvinToC(WCTEMP)))
            
            self.Print("")
            self.Print("The temperature is %s °C now and TMPTH under is setting to 10 °C, Under Temperature Threshold test"%self.KelvinToC(LiveT))
            self.SetTMPTH("under", 0x11B)
            
            self.Print("Check Critical Warning bit 1, expect value=0")        
            CWarningBit1=self.GetCriticalWarningBit1()         
            if CWarningBit1=="0":
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")   
                ret_code=1        
            
            self.Print("")
            self.Print("The temperature is %s °C now and TMPTH under is setting to 60 °C, Under Temperature Threshold test"%self.KelvinToC(LiveT))
            self.SetTMPTH("under", 0x14D)
            
            self.Print("Check Critical Warning bit 1, expect value=1")        
            CWarningBit1=self.GetCriticalWarningBit1()         
            if CWarningBit1=="1":
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")   
                ret_code=1        
                
            self.Print("")             
            self.Print("Reset TMPTH under to %s"%self.KelvinToC(TMPTH_under) )
            self.SetTMPTH("under", TMPTH_under)
        
        return ret_code
        
    SubCase2TimeOut = 60
    SubCase2Desc = "Test data_units_read with read command"
    def SubCase2(self): 
        ret_code=0        
        
        self.Print("MaxBlockCnt: %s"%self.MaxBlockCnt)
        if self.MaxBlockCnt>=511:
            cmdBlockCnt = 499
            cmdRange = 2000
        elif self.MaxBlockCnt>=255:
            cmdBlockCnt = 249
            cmdRange = 4000
        else:
            cmdBlockCnt = 124
            cmdRange = 8000        
        
        data_units_read0=self.GetLog.SMART.DataUnitsRead
        self.Print("Issue get log command, data_units_read: %s"%data_units_read0)
                
        self.Print("Issue read command for 1000*512*1000 bytes(%s nvme commands with block count = %s)"%(cmdRange, cmdBlockCnt))
        CMD="nvme read %s -s 0 -z %s -c %s  2>&1 >/dev/null "%(self.dev, (cmdBlockCnt+1)*512, cmdBlockCnt)
        for i in range(cmdRange):            
            mStr, SC = self.shell_cmd_with_sc(CMD)
            if SC!=0:
                self.Print("CMD Fail at %s read command"%i, "f")
                self.Print("CMD : %s"%CMD, "f")
                self.Print("Return code: %s"%SC, "f")
                return 1
                


        data_units_read1=self.GetLog.SMART.DataUnitsRead
        self.Print("Issue get log command, data_units_read: %s"%data_units_read1)
                
        self.Print("Check if data_units_read has been changed(+1000)")
        
        if data_units_read1==(data_units_read0+1000):
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")    
            ret_code=1
            
        return ret_code

        
    SubCase3TimeOut = 60
    SubCase3Desc = "Test data_units_read with compare command"
    def SubCase3(self): 
        ret_code=0        
        
        self.Print("MaxBlockCnt: %s"%self.MaxBlockCnt)
        if self.MaxBlockCnt>=511:
            cmdBlockCnt = 499
            cmdRange = 2000
        elif self.MaxBlockCnt>=255:
            cmdBlockCnt = 249
            cmdRange = 4000
        else: #if self.MaxBlockCnt>=127:
            cmdBlockCnt = 124
            cmdRange = 8000   
                    
        if not self.CompareSupported:
            self.Print("Compare command not support, skip","w")
            ret_code=255
        else:
            data_units_read0=self.GetLog.SMART.DataUnitsRead
            self.Print("Issue get log command, data_units_read: %s"%data_units_read0)
            
            self.Print("Issue compare command for 1000*512*1000 bytes(%s nvme commands with block count = %s)"%(cmdRange, cmdBlockCnt))
            CMD="dd if=/dev/zero bs=512 count=1 2>&1 > /dev/null | nvme compare %s  -s 0 -z %s -c %s 2>&1 > /dev/null"%(self.dev, (cmdBlockCnt+1)*512, cmdBlockCnt)
            for i in range(cmdRange):            
                self.shell_cmd(CMD)    
    
            data_units_read1=self.GetLog.SMART.DataUnitsRead
            self.Print("Issue get log command, data_units_read: %s"%data_units_read1)
                    
            self.Print("Check if data_units_read has been changed(+1000)")
            
            if data_units_read1==(data_units_read0+1000):
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")    
                ret_code=1
            
        return ret_code

    SubCase4TimeOut = 60
    SubCase4Desc = "Test data_units_written with write command"
    def SubCase4(self): 
        ret_code=0        
        
        data_units_written0=self.GetLog.SMART.DataUnitsWritten
        self.Print("Issue get log command, data_units_written: %s"%data_units_written0)
                
        self.Print("Issue write command for 1000*512*1000 bytes")
        CMD="LOG_BUF=$(fio --direct=1 --iodepth=16 --ioengine=libaio --bs=32k --rw=write --numjobs=1 --size=$((1000*512*1000)) --offset=0 --filename=%s --name=mdata --do_verify=0 --verify=pattern --verify_pattern=0x00)"%self.dev
        self.shell_cmd(CMD)
        '''
        mThreads=self.nvme_write_multi_thread(10, 0, 1000, 0)
        for process in mThreads:
            process.join()
        '''

        data_units_written1=self.GetLog.SMART.DataUnitsWritten
        self.Print("Issue get log command, data_units_written: %s"%data_units_written1)
                
        self.Print("Check if data_units_written has been changed(+1000)")
        
        if data_units_written1==(data_units_written0+1000):
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")    
            ret_code=1
            
        return ret_code

    SubCase5TimeOut = 60
    SubCase5Desc = "Test data_units_written with Write Uncorrectable command"
    def SubCase5(self): 
        ret_code=0        
        
        data_units_written0=self.GetLog.SMART.DataUnitsWritten
        self.Print("Issue get log command, data_units_written: %s"%data_units_written0)
                
        self.Print("Issue Write Uncorrectable command for 512*1280bytes( > 512*1000 )")
        for i in range(10):
            #128*512byte
            CMD="LOG_BUF=$(nvme write-uncor %s -s 0 -n 1 -c 127 2>&1 > /dev/null)"%self.dev
            self.shell_cmd(CMD)
            
        data_units_written1=self.GetLog.SMART.DataUnitsWritten
        self.Print("Issue get log command, data_units_written: %s"%data_units_written1)
                
        self.Print("Check if data_units_written has been changed, expect no changed")
        
        if data_units_written1==data_units_written0:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")    
            ret_code=1
            
        self.Print("Clear write uncorrectable by writing zeros")
        self.nvme_write_blocks(0, 0, 128)
            
        return ret_code
        
    SubCase6TimeOut = 60
    SubCase6Desc = "Test host_read_commands and host_write_commands"
    def SubCase6(self): 
        ret_code=0        
        
        host_read_commands0=self.GetLog.SMART.HostReadCommands
        self.Print("Issue get log command, host_read_commands: %s"%host_read_commands0)
                
        self.Print("Issue read command ")
        CMD="nvme read %s -s 0 -z 512 -c 0  2>&1 >/dev/null "%self.dev         
        self.shell_cmd(CMD)
            
        host_read_commands1=self.GetLog.SMART.HostReadCommands
        self.Print("Issue get log command, host_read_commands: %s"%host_read_commands1)
                
        self.Print("Check if host_read_commands has been changed, expect +1")
        
        if host_read_commands1==host_read_commands0+1:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")    
            ret_code=1
        
        if self.CompareSupported:
            self.Print("----------------------------------------")
            host_read_commands0=self.GetLog.SMART.HostReadCommands
            self.Print("Issue get log command, host_read_commands: %s"%host_read_commands0)
                    
            self.Print("Issue compare command ")
            CMD="dd if=/dev/zero bs=512 count=1 2>&1 > /dev/null | nvme compare %s  -s 0 -z 512 -c 0 2>&1 > /dev/null"%self.dev      
            self.shell_cmd(CMD)
                
            host_read_commands1=self.GetLog.SMART.HostReadCommands
            self.Print("Issue get log command, host_read_commands: %s"%host_read_commands1)
                    
            self.Print("Check if host_read_commands has been changed, expect +1")
            
            if host_read_commands1==host_read_commands0+1:
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")    
                ret_code=1

        self.Print("----------------------------------------")
        host_write_commands0=self.GetLog.SMART.HostWriteCommands
        self.Print("Issue get log command, host_write_commands: %s"%host_write_commands0)
                
        self.Print("Issue write command ")
        self.nvme_write_1_block(0, 1)
            
        host_write_commands1=self.GetLog.SMART.HostWriteCommands
        self.Print("Issue get log command, host_write_commands: %s"%host_write_commands1)
                
        self.Print("Check if host_write_commands has been changed, expect +1")
        
        if host_write_commands1==host_write_commands0+1:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")    
            ret_code=1          
                        
        return ret_code

        
    SubCase7TimeOut = 240
    SubCase7Desc = "Test controller busy time"
    def SubCase7(self): 
        ret_code=0
        
        CBT0=self.GetLog.SMART.ControllerBusyTime
        self.Print("")
        self.Print("Get controller busy time: %s"%CBT0)
        self.Print("Issue fio read command for 70 seconds, iodepth=16, bs=64k")
        CMD="LOG_BUF=$(fio --direct=1 --iodepth=16 --ioengine=libaio --bs=64k --rw=read --numjobs=1 --offset=0 --filename=%s --name=mdata --runtime=70 --time_based)"%self.dev
        self.shell_cmd(CMD)
        self.Print("Finish")   
        self.Print("")     
        CBT1=self.GetLog.SMART.ControllerBusyTime
        self.Print("Get controller busy time: %s"%CBT1)
        self.Print("")   
        self.Print("Check if controller busy time has changed or not, expect: changed(+1 or +2)")
        if (CBT1==CBT0+1) or (CBT1==CBT0+2):
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")    
            ret_code=1          
        
        return ret_code
    
    SubCase8TimeOut = 60
    SubCase8Desc = "Test media error and error log"
    def SubCase8(self): 
        ret_code=0
        
        if not self.WriteUncSupported:
            self.Print("Write unc command not support, skip","w")
            ret_code=255
        else:            
            media_error0=self.GetLog.SMART.MediaandDataIntegrityErrors
            num_err_log_entries0= self.GetLog.SMART.NumberofErrorInformationLogEntries
            
            self.Print("")
            self.Print("Get 'Media and Data Integrity Errors': %s"%media_error0)
            self.Print("Get 'Number of Error Information Log Entries': %s"%num_err_log_entries0)
            
            self.Print("Create error log by issue Write Uncorrectable and read it")
            self.trigger_error_event()
            self.Print("Finish")   
            
            self.Print("")     
            media_error1=self.GetLog.SMART.MediaandDataIntegrityErrors
            num_err_log_entries1= self.GetLog.SMART.NumberofErrorInformationLogEntries
            self.Print("Get 'Media and Data Integrity Errors': %s"%media_error1)
            self.Print("Get 'Number of Error Information Log Entries': %s"%num_err_log_entries1)
                    
            self.Print("")   
            self.Print("Check if 'Media and Data Integrity Errors' changed or not, expect: changed(+1)")
            if media_error1==(media_error0+1):
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")    
                ret_code=1                  
    
            self.Print("")   
            self.Print("Check if 'Number of Error Information Log Entries' changed or not, expect: changed(+1)")
            if num_err_log_entries1==(num_err_log_entries0+1):
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")    
                ret_code=1          
        return ret_code       
    
    SubCase9TimeOut = 60
    SubCase9Desc = "Test power_cycle"
    def SubCase9(self): 
        ret_code=0
        PowerCycles0=self.GetLog.SMART.PowerCycles
        self.Print("")
        self.Print("Get current 'Power Cycles': %s"%PowerCycles0)
        self.Print("Do POR")
        if not self.por_reset():
            self.Print("Fail to power off and on device!, please check power module, quit", "f")
        self.Print("Done")
        sleep(2)
        PowerCycles1=self.GetLog.SMART.PowerCycles
        self.Print("Get current 'Power Cycles': %s"%PowerCycles1)    
        
        self.Print("")   
        self.Print("Check if 'Power Cycles' changed or not, expect: changed(+1)")
        if PowerCycles1==(PowerCycles0+1):
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")    
            ret_code=1  

        return ret_code         

    SubCase10TimeOut = 60
    SubCase10Desc = "Test Unsafe_Shutdowns for POR"
    def SubCase10(self): 
        if self.testUnsafeShutdowns(Mode = "POR"):
            return 0
        else:
            return 1

    SubCase11TimeOut = 60
    SubCase11Desc = "Test Unsafe_Shutdowns for SPOR"
    def SubCase11(self): 
        if self.testUnsafeShutdowns(Mode = "SPOR"):
            return 0
        else:
            return 1      

    SubCase12TimeOut = 60
    SubCase12Desc = "Test get SMART / Health log on a per namespace basis"
    def SubCase12(self):  
        ret_code = 0       
        self.Print("")        
        self.Print("Issue get SMART / Health log with nsid=0")
        CMD = "nvme get-log %s --log-id=2 --log-len=512 -n 0 2>&1"%self.dev
        mStr, SC = self.shell_cmd_with_sc(CMD)
        self.Print("Get command status code: 0x%X"%SC)
        self.Print("Check if status code=0, expect command success")
        if SC==0:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            self.Print(mStr, "f")  
            ret_code = 1
     
        self.Print("")        
        self.Print("Issue get SMART / Health log with nsid=0xFFFFFFFF")
        CMD = "nvme get-log %s --log-id=2 --log-len=512 -n 0xFFFFFFFF 2>&1"%self.dev
        mStr, SC = self.shell_cmd_with_sc(CMD)
        self.Print("Get command status code: 0x%X"%SC)
        self.Print("Check if status code=0, expect command success")
        if SC==0:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")  
            self.Print(mStr, "f")  
            ret_code = 1            
            
        self.Print("")      
        LPA_Bit0 = self.IdCtrl.LPA.bit(0)
        isPerNSbasis = True if LPA_Bit0 =="1" else False        
        self.Print("SMART / Health log on a per namespace basis: %s"%("Yes" if isPerNSbasis else "No"), "p")
                    
        self.Print("")        
        self.Print("Issue get SMART / Health log with nsid=1")
        CMD = "nvme get-log %s --log-id=2 --log-len=512 -n 1 2>&1"%self.dev
        mStr, SC = self.shell_cmd_with_sc(CMD)
        self.Print("Get command status code: 0x%X"%SC)
        if isPerNSbasis:
            self.Print("Check if status code=0x0, expect command success")
            if SC==0:
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")    
                self.Print(mStr, "f")  
                ret_code = 1                     
        else:
            self.Print("Check if status code=0x2 (INVALID_FIELD), expect command fail")
            if SC==2:
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")   
                self.Print(mStr, "f")  
                ret_code = 1                                     
     
        self.Print("")        
        self.Print("Issue get SMART / Health log with nsid=0xFFFFFFFE")
        CMD = "nvme get-log %s --log-id=2 --log-len=512 -n 0xFFFFFFFE 2>&1"%self.dev
        mStr, SC = self.shell_cmd_with_sc(CMD)
        self.Print("Get command status code: 0x%X"%SC)
        if isPerNSbasis:
            self.Print("Check if status code=0xB(INVALID_NS), expect command fail")
            if SC==0xB:
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")    
                self.Print(mStr, "f")  
                ret_code = 1                     
        else:
            self.Print("Check if status code=2 (INVALID_FIELD), expect command fail")
            if SC==2:
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")    
                self.Print(mStr, "f")  
                ret_code = 1                
        
        return ret_code
    
    SubCase13TimeOut = 60
    SubCase13Desc = "NVMe Spec1.3d: test get log command - Log Page Offset"        
    def SubCase13(self):
        ret_code=0
        if self.specVer!="1.3d":
            self.Print( "Current target spec version = %s, please rerun with '-v 1.3d' for NVMe Spec1.3d"%self.specVer,"w")
            return 0

        supportsExtendedEata = True if self.IdCtrl.LPA.bit(2)=="1" else False
        if supportsExtendedEata:
            self.Print( "Controller supports the Log Page Offset in IdCtrl.LPA.bit(2)", "p")
        else:
            self.Print( "Controller don't supports the Log Page Offset in IdCtrl.LPA.bit(2), skip", "w")
            return 0
                
        ret_code = 0 if self.VerifyGetLogWithOffset(LogID=0x2 , ByteOffset=64) else 1
        

        return ret_code    

    SubCase14TimeOut = 600
    SubCase14Desc = "Verify data after reset/por/spor"         
    def SubCase14(self):
        self.Print ("NVMe Reset", "b")
        self.SetPrintOffset(4)
        self.Print ("Get current SMART / Health Log ")
        OriginalValue=self.GetHealthLog()
        self.Print ("Done")
        self.Print ("")
        self.Print ("Issue nvme reset")
        self.nvme_reset()
        self.Print ("Done")
        self.Print ("")        
        self.Print ("Verify if SMART / Health Log is retained")
        expectAdd1List = []
        if not self.VerifyHealthLog(OriginalValue, expectAdd1List): return 1
        
        self.Print ("")
        self.SetPrintOffset(0)
        self.Print ("POR", "b")
        self.SetPrintOffset(4)
        self.Print ("Get current SMART / Health Log ")
        OriginalValue=self.GetHealthLog()
        self.Print ("Done")        
        self.Print ("")
        self.Print ("Issue por")
        if self.por_reset():
            self.Print ("Done")
        else:
            self.Print ("can not power on/off device, please check por module!", "f")
            return 1
        self.Print ("")        
        self.Print ("Verify if SMART / Health Log is retained")
        expectAdd1List = ["PowerCycles"]
        expectGreatOrEqualList = ["DataUnitsRead", "HostReadCommands"]
        if not self.VerifyHealthLog(OriginalValue, expectAdd1List, expectGreatOrEqualList): return 1        
        
        self.Print ("")
        self.SetPrintOffset(0)
        self.Print ("SPOR", "b")
        self.SetPrintOffset(4)
        self.Print ("Get current SMART / Health Log ")
        OriginalValue=self.GetHealthLog()
        self.Print ("Done")        
        self.Print ("")
        self.Print ("Issue spor")
        if self.spor_reset():
            self.Print ("Done")
        else:
            self.Print ("can not power on/off device, please check por module!", "f")
            return 1
        self.Print ("")        
        self.Print ("Verify if SMART / Health Log is retained")
        expectAdd1List = ["PowerCycles", "UnsafeShutdowns"]
        expectGreatOrEqualList = ["DataUnitsRead", "HostReadCommands"]
        if not self.VerifyHealthLog(OriginalValue, expectAdd1List, expectGreatOrEqualList): return 1 
        self.SetPrintOffset(0)       
        
    SubCase15TimeOut = (4000)
    SubCase15Desc = "[Read only mode] Test Critical Warning in Read only mode"      
    SubCase15KeyWord = "VCTDEPT-851"
    def SubCase15(self):
        ret_code=0
        self.Print ("Verify Critical Warning in Read only mode ")
        if not self.mIKNOWWHATIAMDOING:
            self.Print ("Please run script with option '-iknowwhatiamdoing', it will make DUT into RO mode")
            return 0        

        EnduranceGroupSupported = True if self.IdCtrl.CTRATT.bit(4)=="1" else False
        if not EnduranceGroupSupported:
            self.Print("EnduranceGroupSupported: No", "w")
        else:
            self.Print("EnduranceGroupSupported: Yes", "p")             
        CriticalWarning=self.GetLog.SMART.CriticalWarning
        self.Print("Currnt CriticalWarning: 0x%X"%CriticalWarning)
        PercentageUsed=self.GetLog.SMART.PercentageUsed
        self.Print("Currnt PercentageUsed: 0x%X"%PercentageUsed)
        self.Print("")
        self.Print ("Issue VU CMD to markBadBlk and verify Critical Warning bit0 and bit3")
        self.Print("bit 0 (available spare capacity has fallen below the threshold)")
        self.Print("bit 3 (the media has been placed in read only mode)")
        self.Print("If any field changed, print all field")
        self.Print("")
        mList = []
        AvailableSpareT = self.GetLog.SMART.AvailableSpareThreshold 
        LBAlist = self.getMarkBadBlkRange() # self.getMarkBadBlkRange() will get list of blocks
        # print title
        self.PrintAlignString("markBadBlk_SLBA")
        self.PrintAlignString("|", "markBadBlk_ELBA")
        self.PrintAlignString("|", "|", "CriticalWarning[bit0,bit1..bit7]")
        self.PrintAlignString("|", "|", "|", "AvailableSpare")
        self.PrintAlignString("|", "|", "|", "|", "AvailableSpareThreshold")
        self.PrintAlignString("|", "|", "|", "|", "|", "EnduranceGroupCriticalWarningSummary")
        # if EnduranceGroupSupported, print title
        if EnduranceGroupSupported: self.PrintAlignString("|", "|", "|", "|", "|", "|","CriticalWarning in EnduranceGroupLog(LID=0x9)")
        if EnduranceGroupSupported: self.PrintAlignString("|", "|", "|", "|", "|", "|","|")         
        self.Print("--------------------------------------------------------------------------------------------------------")
        slbaPtr=0
        elbaPtr=0
        AvailableSpareBK=self.GetLog.SMART.AvailableSpare
        totalNum = len(self.getMarkBadBlkRange())
        listOld = []
        # example, issue cmd, using pointer(slbaPtr/elbaPtr) to get MarkBadBlk value
        for i in range(totalNum):
            lba = LBAlist[i]
            self.markBadBlk(lba)
            # get fields
            CriticalWarningList = self.byte2List(self.GetLog.SMART.CriticalWarning) # convert to bit list
            AvailableSpare=self.GetLog.SMART.AvailableSpare
            EGCWSlist = self.byte2List(self.GetLog.SMART.EnduranceGroupCriticalWarningSummary)
            E_CriticalWarningList = "" if not EnduranceGroupSupported else self.byte2List(self.GetLog.EnduranceGroupLog.CriticalWarning)
            listCurr = [CriticalWarningList, AvailableSpare, AvailableSpareT, EGCWSlist, E_CriticalWarningList]
            haveChanged = True if listCurr!=listOld else False
            listOld = listCurr
            isBelowThreshold = True if CriticalWarningList[0] ==1 else False
            elbaPtr = i
            # ex, PrintMsgEveryXcommand=3, print info after every 3 time of markBadBlk cmd
            # if is last cmd of markBadBlk, or any field changed, print info
            if haveChanged or elbaPtr==totalNum:
                slba = LBAlist[slbaPtr]
                elba = LBAlist[elbaPtr]
                CriticalWarning=self.GetLog.SMART.CriticalWarning
                AvailableSpare=self.GetLog.SMART.AvailableSpare
                CriticalWarningList = self.byte2List(CriticalWarning) # convert to bit list
                EnduranceGroupCriticalWarningSummary=self.GetLog.SMART.EnduranceGroupCriticalWarningSummary
                EGCWSlist = self.byte2List(EnduranceGroupCriticalWarningSummary)                                
                self.PrintAlignString("0x%X"%slba, "0x%X"%elba, CriticalWarningList, AvailableSpare, AvailableSpareT, EGCWSlist, E_CriticalWarningList)
                # save to list, note 3th =CriticalWarningList and 5th =EGCWSlist
                mList.append([slba, elba, CriticalWarningList, AvailableSpare, AvailableSpareT, EGCWSlist, E_CriticalWarningList]) 
                slbaPtr = elbaPtr +1
            # if is last cmd of markBadBlk or spare below threshold(bit0), print info
            if elbaPtr==totalNum or isBelowThreshold:
                break   
            #if AvailableSpare<=85: break         # test
  
        self.Print("--------------------------------------------------------------------------------------------------------") 
        AvailableSpare=self.GetLog.SMART.AvailableSpare
        if (AvailableSpareBK == AvailableSpare):
            self.Print("Warnning! AvailableSpare has no changed!, skip", "w")
            return 255        
        self.Print("Done!")
        self.Print("")
            
        self.Print("1) Check if AvailableSpare is counting down")     
        lastValue=100
        isPass=True
        for item in mList:
            if item[3]>lastValue: 
                isPass=False
                break
            lastValue =  item[3]  
        if isPass:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")   
            ret_code=1            
            
        self.Print("2) Check if Critical Warning bit 0(available spare capacity has fallen below the threshold) was set to 1")    
        self.Print("when AvailableSpare<AvailableSpareThreshold")    
        lastValue=100
        isPass=True
        for item in mList:
            AvailableSpare, AvailableSpareT = item[3:5]
            Bit0 = item[2][0] # element2 is CriticalWarning
            if (AvailableSpare<AvailableSpareT) and Bit0!=1: 
                isPass=False
                break    
            if (AvailableSpare>=AvailableSpareT) and Bit0!=0: 
                isPass=False
                break              
        if isPass:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")   
            ret_code=1      

        self.Print("3) Check Critical Warning bit 0(available spare capacity has fallen below the threshold), expect value=1")      
        Bit0 = mList[len(mList)-1][2][0] # last list element2 is CriticalWarning
        if Bit0==1:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")   
            ret_code=1            
        self.Print("4) Check Critical Warning bit 3(the media has been placed in read only mode), expect value=1")         
        Bit3 = mList[len(mList)-1][2][3] # last list, element2 is CriticalWarning      
        if Bit3==1:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")   
            ret_code=1
 
        self.Print("5) Check Endurance Group Critical Warning Summary")
        if not EnduranceGroupSupported:
            self.Print("EnduranceGroupSupported: No, skip", "w")
        else:
            self.Print("EnduranceGroupSupported: Yes", "p")  
            self.Print("Verify Endurance Group Critical Warning Summary in SMART log, bit [0,2,3] must the same as CriticalWarning")       
            isPass=True
            for item in mList:
                CriticalWarning = item[2]
                EGCWSlist = item[5]
                # compare bit 0,2,3
                if EGCWSlist[0]!=CriticalWarning[0]:isPass=False; break
                if EGCWSlist[2]!=CriticalWarning[2]:isPass=False; break
                if EGCWSlist[3]!=CriticalWarning[3]:isPass=False; break
            if isPass:
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")   
                ret_code=1                
                    
        self.Print("6) Check Critical Warning field in Endurance Group Log, log ID = 0x9")
        if not EnduranceGroupSupported:
            self.Print("EnduranceGroupSupported: No, skip", "w")
        else:
            self.Print("EnduranceGroupSupported: Yes", "p")  
            self.Print("Verify Critical Warning in Endurance Group Log, bit [0,2,3] must the same as CriticalWarning")       
            isPass=True
            for item in mList:
                CriticalWarning = item[2]
                E_CriticalWarning = item[6]
                # compare bit 0,2,3
                if E_CriticalWarning[0]!=CriticalWarning[0]:isPass=False; break
                if E_CriticalWarning[2]!=CriticalWarning[2]:isPass=False; break
                if E_CriticalWarning[3]!=CriticalWarning[3]:isPass=False; break
            if isPass:
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")   
                ret_code=1       
                                
        return ret_code        

    SubCase16TimeOut = (4000)
    SubCase16Desc = "Test 'Percentage Used' by VU command"      
    def SubCase16(self):
        ret_code=0

        
        self.Print("Check if Controller accept UV CMD")
        if not self.setPE(cdw13_PE=0):
            self.Print("Controller do not accept UV CMD: %s"%self.LastCmd, "f")
            self.Print("Warnning!, skip", "w")
            return 255
        else:
            self.Print("Pass", "p")
            
        self.Print("")
        self.Print("PercentageUsedScale: %s"%self.PUS100)
        self.Print("I.E. %s PE( for all blocks ) will set PercentageUsedScale to 100"%self.PUS100)
        PUS=self.PUS100/100
        self.Print("%s PE( for all blocks ) will set PercentageUsedScale to 1"%PUS)
        self.Print("Make PercentageUsedScale to 255 need %s PE ((PercentageUsedScale/100)*255)"%(PUS*255))
        self.Print("")

        self.PrintAlignString("PE", "PercentageUsed")
        self.Print("--------------------------------------------------------------------------------------------------------")
        value_curr = 0
        value_last = 0
        ispass = True
        for PE in range(0x0, PUS*260, PUS):
            self.setPE(cdw13_PE=PE)
            value_curr = self.GetLog.SMART.PercentageUsed
            pf = "pass" if value_curr>=value_last else "fail"
            if pf == "fail":
                ispass = False
            self.PrintAlignString(S0 = "0x%X"%PE, S1 = value_curr)
            value_last = value_curr
            
        self.Print("--------------------------------------------------------------------------------------------------------")
        self.Print("")
                    
        self.Print("Check if PercentageUsed counting up")
        if ispass:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            ret_code = 1
            
        self.Print("")
        self.Print("Reset PE to 0")
        if self.setPE(cdw13_PE=0):            
            self.Print("Done", "p")
        else:
            self.Print("Fail", "f")
            ret_code = 1
            
        return ret_code
            
    SubCase17TimeOut = (4000)
    SubCase17Desc = "Test Critical Warning -> 'NVM subsystem reliability'"
    def SubCase17(self):
        ret_code=0
        self.Print("According to https://jira.siliconmotion.com.tw:8443/browse/VCTDEPT-855")
        self.Print("Before test, SSD must set 'Wear Leveling Count Threshold' to 1")
        self.Print("And 'Retire PE (0 means GRTPE)' to 2")
        self.Print("")
        CriticalWarning = self.GetLog.SMART.CriticalWarning
        reliability = self.byte2List(CriticalWarning)[2] # convert to bit list
        self.Print("Current CriticalWarning: 0x%X, NVM subsystem reliability: %s"%(CriticalWarning, reliability))
        self.Print("")
        if reliability==1:
            self.Print("before test, 'NVM subsystem reliability' = 1, skip", "p")
            return 255
                    
        self.Print("Write whole disk..")
        self.fio_precondition(pattern=0xAB, showProgress=True)
        self.Print("Done", "p")
        self.Print("")
        CriticalWarning = self.GetLog.SMART.CriticalWarning
        reliability = self.byte2List(CriticalWarning)[2] # convert to bit list
        self.Print("Current CriticalWarning: 0x%X, NVM subsystem reliability: %s"%(CriticalWarning, reliability))
                
        self.Print("Check if 'NVM subsystem reliability' = 1 or not")
        if reliability==1:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            ret_code = 1
                   
                   
        
        
        return ret_code                     
    # </sub item scripts>
    
    SubCase18TimeOut = (4000)
    SubCase18Desc = "Test CompositeTemperature"
    def SubCase18(self):
        ret_code = 0
        self.Print("Check if CompositeTemperature changed or not", "b") 
        self.SetPrintOffset(4, "add")
        LiveT = self.GetLog.SMART.CompositeTemperature
        self.Print("Current CompositeTemperature: %s(%s °C)"%(LiveT, self.KelvinToC(LiveT)))        
        self.Print("")        
        self.Print("Expect Current CompositeTemperature > 0 °C, if equal to 0, fail the test")
        if self.KelvinToC(LiveT)>0:            
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")     
            ret_code = 1
             
        self.Print("")
        TargetTemp = LiveT+1
        TimeLimit = 60
        self.Print ("Reading data to raise temperature, when CompositeTemperature >= %s( %s °C)"%(TargetTemp, self.KelvinToC(TargetTemp)))
        self.Print ("Then pass the test, Time limit is %s s "%TimeLimit)
        LiveT_c = self.RaisingTempture(TargetTemp, TimeLimit)
        self.Print("Current CompositeTemperature: %s(%s °C)"%(LiveT_c, self.KelvinToC(LiveT_c))) 
        if LiveT_c!=LiveT:            
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "w")      
            self.Print("")
            self.Print("It may not raise up the tempture due to current tempture is too high")
            self.Print("Let try to cool down with sleep 10s")            
            self.Print("Sleep 10s ..")
            sleep(10)
            self.Print("")
            LiveT_c = self.GetLog.SMART.CompositeTemperature
            self.Print("Current CompositeTemperature: %s(%s °C)"%(LiveT_c, self.KelvinToC(LiveT_c)))  
            self.Print("")
            self.Print("Check if Current CompositeTemperature changed")
            if LiveT_c!=LiveT:            
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")     
                ret_code = 1  
                    
        return ret_code
    
if __name__ == "__main__":
    DUT = SMI_SmartHealthLog(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 
    
    
    
    
    
