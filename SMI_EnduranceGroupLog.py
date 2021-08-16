#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
import types
# Import VCT modules
from lib_vct.NVME import NVME

class SMI_EnduranceGroupLog(NVME):
    ScriptName = "SMI_EnduranceGroupLog.py"
    Author = "Sam"
    Version = "20210816"
    
    def getENDGID(self, ns):
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x0 --namespace-id=%s 2>&1"%(self.dev_port, ns)
        rTDS=self.shell_cmd(CMD)
        DS=self.AdminCMDDataStrucToListOrString(rTDS, 2)            
        if DS==None:
            return None
        else:
            return (DS[103]<<8) + DS[102]        

    def getENDGIDMAX(self):
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x1 2>&1"%(self.dev_port)
        rTDS=self.shell_cmd(CMD)
        DS=self.AdminCMDDataStrucToListOrString(rTDS, 2)            
        if DS==None:
            return None
        else:
            return (DS[341]<<8) + DS[340]          

    def getEGL(self, ns):
        self.get_log_passthru(LID=0x9, size=512,ReturnType=2)
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x0 --namespace-id=%s 2>&1"%(self.dev_port, ns)
        rTDS=self.shell_cmd(CMD)
        DS=self.AdminCMDDataStrucToListOrString(rTDS, 2)            
        if DS==None:
            return None
        else:
            return (DS[103]<<8) + DS[102]   

    def PrintAlignString(self,S0="", S1="", S2="", S3="", S4="", S5="", PF="default"):            
        mStr = "{:<16}{:<16}{:<34}{:<16}{:<24}{:<34}".format(S0, S1, S2, S3, S4,S5 )
        if PF=="pass":
            self.Print( mStr , "p")        
        elif PF=="fail":
            self.Print( mStr , "f")      
        else:
            self.Print( mStr )  
    
    def GetFieldValue(self, fieldName):
        return getattr(self.GetLog.EnduranceGroupLog, fieldName) 
    
    def Verify1BillionReadWriteMedia(self, fieldName):
    # fieldName: DataUnitsRead/DataUnitsWritten/MediaUnitsWritten
    # 1G = 1 billion
        rw = "read" if fieldName == "DataUnitsRead" else "write"
        CMD = "fio --direct=1 --iodepth=16 --ioengine=libaio --bs=64k --rw=%s --numjobs=1 --size=100M --filename=%s --name=mtest"\
        %(rw, self.dev)
        value_old = self.GetFieldValue(fieldName)
        isPass=False
        self.Print("Try to %s 100M bytes for 10 times, if %s+1, skip %s command"%(rw, fieldName, rw))
        self.Print("Current value %s"%value_old)
        for cnt in range(10):
            self.shell_cmd(CMD)
            value_curr = self.GetFieldValue(fieldName)
            self.PrintAlignString(cnt+1, "%s 100M"%rw, "%s: %s"%(fieldName, value_curr))
            if value_curr == value_old+1:
                self.Print("%s th, value+1, skip"%(cnt+1), "p")
                isPass = True
                break
        self.Print("")    
        if not isPass:
            self.Print("Fail, After %s 100M bytes x 10 data, %s has not changed "%(rw, fieldName), "f")
            if value_curr==0:
                self.Print("Current value = 0, SPEC: A value of 0h indicates that the controller does not report the number of %s, skip"%fieldName, "w")
                return True
            else:
                return False
        else:
            self.Print("Try to %s 100M bytes for 10 times, if %s+1 at 9th or 10th, pass the test"%(rw, fieldName))
            value_old = self.GetFieldValue(fieldName)
            self.Print("Current value %s"%value_old)
            for cnt in range(10):
                self.shell_cmd(CMD)
                value_curr = self.GetFieldValue(fieldName)
                self.PrintAlignString(cnt+1, "%s 100M"%rw, "%s: %s"%(fieldName, value_curr))
                if value_curr == value_old+1:
                    break 
            self.Print("") 
            if cnt ==9 or cnt==8:
                self.Print("After %s 100M bytes x %s, %s changed(+1)"%(rw, cnt+1, fieldName), "p")  
                self.Print("I.E. This value is reported in billions")  
                return True  
            else:
                self.Print("Fail", "f")
                return False
            
    def VerifyHostReadWriteCMD(self, fieldName, RC="na"):
    # fieldName: HostReadCommands/HostWriteCommands
    # RC = "read" or "compare"  for HostReadCommands, this is the number of Compare commands and Read commands
        if  fieldName == "HostReadCommands" and RC == "read":
            CMD="nvme read %s -s 0 -z 512 -c 0  2>&1  "%self.dev  
        elif  fieldName == "HostReadCommands" and RC == "compare":
            CMD="dd if=/dev/zero bs=512 count=1 2>&1 > /dev/null | nvme compare %s  -s 0 -z 512 -c 0 2>&1 "%self.dev  
        elif  fieldName == "HostWriteCommands" :
            CMD="dd if=/dev/zero bs=4096 count=1 2>&1 | nvme write %s -s 0 -z 4096 2>&1"%self.dev  
        
        else:
            self.Print("Call func VerifyHostReadWriteCMD fail with para", "f")
            return False
                     
        value_old = self.GetFieldValue(fieldName)
        self.Print("Current %s: %s"%(fieldName, value_old))
        self.Print("")  
        self.Print("Issue CMD: %s"%CMD) 
        mstr, sc = self.shell_cmd_with_sc(CMD)
        if sc == 0x85 and RC=="compare": # if is compare cmd and rtcode = 85h, then cmd pass
            pass
        elif sc!=0:
            self.Print("CMD fail with statue: %s"%mstr, "f")
            return False
        else:
            self.Print("CMD Success")
        self.Print("")  
        value_new = self.GetFieldValue(fieldName)
        self.Print("Current %s: %s"%(fieldName, value_new))
        self.Print("Check if %s +1 after CMD"%fieldName)
        if value_new==value_old+1:
            self.Print("Pass", "p")
            return True
        else:
            self.Print("Fail", "f") 
            return False               

    def trigger_error_event(self): 
        nsid = self.GetNSID()
        #print "%s"%nsid
        self.shell_cmd("  buf=$( nvme write-uncor %s -s 0 -n %s -c 127 2>&1 >/dev/null )"%(self.dev, nsid))
        self.shell_cmd("  buf=$( nvme read %s -s 0 -z 512 -c 0 2>&1 >/dev/null )"%(self.dev))

        # clear write-uncor 
        self.shell_cmd("  buf=$(nvme write-zeroes %s -s 0 -c 127 2>&1 > /dev/null) "%(self.dev))    
    
    def __init__(self, argv):
        self.SetDynamicArgs(optionName="PUS100", optionNameFull="PUS100", \
                            helpMsg="PercentageUsedScale for case 16 that will set PercentageUsed to 100"
                            "\ne.x for SKH, formula of PercentageUsed in SMART log is"\
                            "\n(sum of all block erase count/total erase block)/7000"\
                            "\nso run script with '-PUS100 7000'", argType=int, default=7000)          
        # initial parent class
        super(SMI_EnduranceGroupLog, self).__init__(argv)
        
        self.PUS100 = self.GetDynamicArgs(0)
        
        self.EGsupported = True if self.IdCtrl.CTRATT.bit(4)=="1" else False
        self.ENDGID = 0
        self.NsSupported=True if self.IdCtrl.OACS.bit(3)=="1" else False 
        self.CompareSupported=self.IdCtrl.ONCS.bit(0)    
        self.CompareSupported=True if self.CompareSupported=="1" else False
        self.WriteUncSupported=self.IdCtrl.ONCS.bit(1)    
        self.WriteUncSupported=True if self.WriteUncSupported=="1" else False        

    # define pretest, if not return 0 , skip all subcases
    def PreTest(self):      
        self.Print ("Write Uncorrectable command supported", "p") if self.WriteUncSupported else self.Print ("Write Uncorrectable command not supported", "f")
        self.Print ("Compare command supported", "p") if self.CompareSupported else self.Print ("Compare command not supported", "f")  
        self.Print("")        
        self.Print("Check if controller support endurance group in Identify Controller Data Structure -> Controller Attributes (CTRATT) -> bit 4")
        if self.EGsupported:
            self.Print("Supported", "p")
        else:
            self.Print("Not supported, skip all test cases!", "w")
            return 255       
        self.Print("Check if ENDGID in id-ns data structure in nsid=1 is not 0x0") 
        self.ENDGID = self.getENDGID(ns=1)
        if self.ENDGID == None:
            self.Print("Can not get id-ns data structure", "f")
            return 1
        self.Print("ENDGID: 0x%X"%self.ENDGID) 
        if self.ENDGID == 0:
            self.Print("Fail", "f")
            return 1
        else:
            self.Print("Pass", "p")
        
        self.Print("")    
        self.Print("Following test will set EnduranceGroupIdentifier to %s "%self.ENDGID)
        self.GetLog.EnduranceGroupLog.SetEnduranceGroupIdentifierInCDW11(self.ENDGID)
        return 0       

    # <define sub item scripts>
    SubCase1TimeOut = 6000
    SubCase1Desc = "Test get log page command for EnduranceGroupLog"
    SubCase1KeyWord = ""
    def SubCase1(self):
        ret_code=0  
        self.Print ("Issue command to get log data for EnduranceGroupLog and print")
        self.Print("")
        self.PrintAlignString("", "", "CriticalWarning", self.GetLog.EnduranceGroupLog.CriticalWarning)
        self.PrintAlignString("", "", "Reserved_2_1", self.GetLog.EnduranceGroupLog.Reserved_2_1)
        self.PrintAlignString("", "", "AvailableSpare", self.GetLog.EnduranceGroupLog.AvailableSpare)
        self.PrintAlignString("", "", "AvailableSpareThreshold", self.GetLog.EnduranceGroupLog.AvailableSpareThreshold)
        self.PrintAlignString("", "", "PercentageUsed", self.GetLog.EnduranceGroupLog.PercentageUsed)
        self.PrintAlignString("", "", "Reserved_31_6", self.GetLog.EnduranceGroupLog.Reserved_31_6)
        self.PrintAlignString("", "", "EnduranceEstimate", self.GetLog.EnduranceGroupLog.EnduranceEstimate)
        self.PrintAlignString("", "", "DataUnitsRead", self.GetLog.EnduranceGroupLog.DataUnitsRead)
        self.PrintAlignString("", "", "DataUnitsWritten", self.GetLog.EnduranceGroupLog.DataUnitsWritten)
        self.PrintAlignString("", "", "MediaUnitsWritten", self.GetLog.EnduranceGroupLog.MediaUnitsWritten)
        self.PrintAlignString("", "", "HostReadCommands", self.GetLog.EnduranceGroupLog.HostReadCommands)
        self.PrintAlignString("", "", "HostWriteCommands", self.GetLog.EnduranceGroupLog.HostWriteCommands)
        self.PrintAlignString("", "", "MediaandDataIntegrityErrors", self.GetLog.EnduranceGroupLog.MediaandDataIntegrityErrors)
        self.PrintAlignString("", "", "NumberofErrorInformationLogEntries", self.GetLog.EnduranceGroupLog.NumberofErrorInformationLogEntries)
        self.PrintAlignString("", "", "Reserved_511_160", self.GetLog.EnduranceGroupLog.Reserved_511_160)
        
        return ret_code


    SubCase2TimeOut = 4000
    SubCase2Desc = "Test 'Percentage Used' by VU command"      
    def SubCase2(self):
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
            # get value 
            value_curr = self.GetLog.EnduranceGroupLog.CriticalWarning          
            
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
            

   
    SubCase3TimeOut = 4000
    SubCase3Desc = "Test 'EnduranceEstimate"      
    def SubCase3(self):
        ret_code=0      
        if self.NsSupported:
            self.Print("Multi ns supported")
        else:
            self.Print("Multi ns not supported")
        if not self.NsSupported:
            if not self.Verify1BillionReadWriteMedia("EnduranceEstimate"):
                ret_code=1
        return ret_code   


    SubCase4TimeOut = 4000
    SubCase4Desc = "Test 'Data_Units_Read"      
    def SubCase4(self):
        ret_code=0      
        if self.NsSupported:
            self.Print("Multi ns supported")
        else:
            self.Print("Multi ns not supported")
        if not self.NsSupported:
            if not self.Verify1BillionReadWriteMedia("DataUnitsRead"):
                ret_code=1
        return ret_code
   
    SubCase5TimeOut = 4000
    SubCase5Desc = "Test 'Data_Units_Write"      
    def SubCase5(self):
        ret_code=0      
        if self.NsSupported:
            self.Print("Multi ns supported")
        else:
            self.Print("Multi ns not supported")
        if not self.NsSupported:
            if not self.Verify1BillionReadWriteMedia("DataUnitsWritten"):
                ret_code=1
        return ret_code   

    SubCase6TimeOut = 4000
    SubCase6Desc = "Test 'MediaUnitsWritten"      
    def SubCase6(self):
        ret_code=0      
        if self.NsSupported:
            self.Print("Multi ns supported")
        else:
            self.Print("Multi ns not supported") 
        if not self.NsSupported:
            if not self.Verify1BillionReadWriteMedia("MediaUnitsWritten"):
                ret_code=1
        return ret_code      

    SubCase7TimeOut = 4000
    SubCase7Desc = "Test 'HostReadCommands"      
    def SubCase7(self):
        ret_code=0      
        if self.NsSupported:
            self.Print("Multi ns supported")
        else:
            self.Print("Multi ns not supported") 
        if not self.NsSupported:
            self.Print ("Verify HostReadCommands field with read command")
            if not self.VerifyHostReadWriteCMD("HostReadCommands", "read"):
                ret_code=1
            self.Print ("")             
            if self.CompareSupported:
                self.Print ("Compare command supported, verify HostReadCommands field with compare command")
                if not self.VerifyHostReadWriteCMD("HostReadCommands", "compare"):
                    ret_code=1                               
        return ret_code       
    

    SubCase8TimeOut = 4000
    SubCase8Desc = "Test 'HostWriteCommands"      
    def SubCase8(self):
        ret_code=0      
        if self.NsSupported:
            self.Print("Multi ns supported")
        else:
            self.Print("Multi ns not supported") 
        if not self.NsSupported:
            self.Print ("Verify HostWriteCommands field with write command")
            if not self.VerifyHostReadWriteCMD("HostWriteCommands", "na"):
                ret_code=1
                           
        return ret_code   

    SubCase9TimeOut = 6000
    SubCase9Desc = "Test MediaandDataIntegrityErrors"
    def SubCase9(self): 
        ret_code=0
        if self.NsSupported:
            self.Print("Multi ns supported")
        else:
            self.Print("Multi ns not supported") 
        if not self.NsSupported:        
            if not self.WriteUncSupported:
                self.Print("Write unc command not support, skip","w")
                ret_code=255
            else:            
                media_error_old=self.GetLog.EnduranceGroupLog.MediaandDataIntegrityErrors
                self.Print("Current MediaandDataIntegrityErrors: %s"%media_error_old)
                num_err_log_entries0= self.GetLog.SMART.NumberofErrorInformationLogEntries  
                self.Print("Current 'Number of Error Information Log Entries': %s"%num_err_log_entries0)
                self.Print("")
                self.Print("Create error log by issue Write Uncorrectable and read it")
                self.trigger_error_event()
                self.Print("Finish")   
                
                self.Print("")     
                media_error_new=self.GetLog.EnduranceGroupLog.MediaandDataIntegrityErrors
                self.Print("Current MediaandDataIntegrityErrors: %s"%media_error_new)
                num_err_log_entries1= self.GetLog.SMART.NumberofErrorInformationLogEntries
                self.Print("Current 'Number of Error Information Log Entries': %s"%num_err_log_entries1)                                       
        
                self.Print("")   
                self.Print("Check if 'Number of Error Information Log Entries' changed or not, expect: changed(+1)")
                if num_err_log_entries1==(num_err_log_entries0+1):
                    self.Print("Pass", "p")
                else:
                    self.Print("Fail", "f")    
                    ret_code=1   
                    
                self.Print("")   
                self.Print("Check if 'MediaandDataIntegrityErrors' changed or not, expect: changed(+1)")
                if media_error_new==(media_error_old+1):
                    self.Print("Pass", "p")
                else:
                    self.Print("Fail", "f")    
                    ret_code=1                              
        return ret_code


    SubCase10TimeOut = 6000
    SubCase10Desc = "Test NumberofErrorInformationLogEntries"
    def SubCase10(self): 
        ret_code=0
        if self.NsSupported:
            self.Print("Multi ns supported")
        else:
            self.Print("Multi ns not supported") 
        if not self.NsSupported:        
            if not self.WriteUncSupported:
                self.Print("Write unc command not support, skip","w")
                ret_code=255
            else:            
                num_err_log_entries_old= self.GetLog.SMART.NumberofErrorInformationLogEntries  
                self.Print("Current 'Number of Error Information Log Entries': %s"%num_err_log_entries_old)
                self.Print("")
                self.Print("Create error log by issue Write Uncorrectable and read it")
                self.trigger_error_event()
                self.Print("Finish")   
                
                self.Print("")     
                num_err_log_entries_new= self.GetLog.SMART.NumberofErrorInformationLogEntries
                self.Print("Current 'Number of Error Information Log Entries': %s"%num_err_log_entries_new)                                       
        
                self.Print("")   
                self.Print("Check if 'Number of Error Information Log Entries' changed or not, expect: changed(+1)")
                if num_err_log_entries_new==(num_err_log_entries_old+1):
                    self.Print("Pass", "p")
                else:
                    self.Print("Fail", "f")    
                    ret_code=1                         
        return ret_code


    # </define sub item scripts>

    # define PostTest           

    SubCase11TimeOut = 6000
    SubCase11Desc = "Test invalid ENDGID"
    def SubCase11(self): 
        ret_code=0      
        if self.NsSupported:
            self.Print("Multi ns supported")
        else:
            self.Print("Multi ns not supported") 
        if not self.NsSupported:
            self.Print ("")
            ENDGIDMAX = self.getENDGIDMAX()
            self.Print ("ENDGIDMAX: %s"%ENDGIDMAX)
            self.Print ("")
            self.Print ("1) Check if ENDGIDMAX != 0")
            self.SetPrintOffset(4, "add")
            if ENDGIDMAX==0:
                self.Print("Fail", "f")
                return 1
            else:
                self.Print("Pass","p")
            self.SetPrintOffset(-4, "add")
                
                             
            self.Print ("")
            self.Print ("2) Get log page with ENDGID less then or equal to ENDGIDMAX, expect command return success(0x0) or Invalid_Field(0x2)")            
            self.SetPrintOffset(4, "add")
            for id in range(1, ENDGIDMAX+1):
                self.Print ("Get log page - endurance group information with ENDGID = %s"%id)
                self.GetLog.EnduranceGroupLog.SetEnduranceGroupIdentifierInCDW11(id)
                value = self.GetLog.EnduranceGroupLog.CriticalWarning # issue cmd
                mstr, sc = self.shell_cmd_with_sc(self.LastCmd)# issue again and get status
                if sc==0:
                    self.Print( "Get Feature CMD success(0x0)", "p")
                elif sc==0x2:
                    self.Print( "Get Feature CMD fail Invalid_Field(0x2)", "p")
                else:
                    self.Print( "Get Feature CMD fail with status: %s"%mstr, "f")
                    ret_code = 1
                self.Print ("")
            self.SetPrintOffset(-4, "add")
                    
            self.Print ("")
            self.Print ("3) Get log page with ENDGID large then ENDGIDMAX, expect command return Invalid_Field(0x2)")            
            self.SetPrintOffset(4, "add")
            for id in range(ENDGIDMAX+1, ENDGIDMAX+5): # check 4 times               
                self.Print ("Get log page - endurance group information with ENDGID = %s"%id)
                if (id>0xFFFF): # maxium = 0xFFFF
                    self.Print( "Reach maxium value(0xFFFF), break")
                    break 
                self.GetLog.EnduranceGroupLog.SetEnduranceGroupIdentifierInCDW11(id)
                value = self.GetLog.EnduranceGroupLog.CriticalWarning # issue cmd
                mstr, sc = self.shell_cmd_with_sc(self.LastCmd)# issue again and get status
                if sc==0x2:
                    self.Print( "Get Feature CMD fail Invalid_Field(0x2)", "p")
                else:
                    self.Print( "Get Feature CMD return status: %s"%mstr, "f")
                    ret_code = 1
                self.Print ("")
            self.SetPrintOffset(-4, "add")
                    

            
            
            self.Print ("")
            # reset ENDGID
            self.GetLog.EnduranceGroupLog.SetEnduranceGroupIdentifierInCDW11(self.ENDGID)
                           
        return ret_code            
    
    def PostTest(self): 
        return True
            
     


if __name__ == "__main__":
    DUT = SMI_EnduranceGroupLog(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    