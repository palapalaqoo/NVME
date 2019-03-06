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
import re
import os
import csv
import shutil
import threading
# Import VCT modules
from SMI_CommandsSupportedAndEffectsLog import SMI_CommandsSupportedAndEffectsLog


class SMI_StatusCode(SMI_CommandsSupportedAndEffectsLog):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_StatusCode.py"
    Author = "Sam Chan"
    Version = "20190305"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    InPath = "./CSV/In/"
    OutPath = "./CSV/Out/"    
    File_BuildIn_GetLog05 = "./lib_vct/CSV/GetLog05_CommandsSupportedAndEffects.csv"    
    File_GetLog05 = "GetLog_05.csv" 
    
    

    TypeInt=0x0
    TypeStr=0x1

    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def Check_InvalidCommandOpcode_Pass(self):
    # return True/False

        OUT_UserFileFullPath=self.OutPath+self.File_GetLog05
        IN_UserFileFullPath=self.InPath+self.File_GetLog05
        
        subRt=True
        OutUserFile=self.ReadCSVFile(OUT_UserFileFullPath)
        
        if OutUserFile==None:
            self.Print("Can't find file at %s"%OUT_UserFileFullPath, "w")
            return False
        else:  
            self.Print( "")
            self.Print( "Start to check status code ..")
            self.Print("----------------------------------------------------------------------")     
            for mItem in OutUserFile:
                # if start char=# means it is a comment, and quit it
                mStr = "^#"
                if re.search(mStr, mItem[0]):
                    pass   
                else:                 
                    # InitLogPage05Lists = [ admin/io, opcode, CommandName, CSE, CCC, NIC, NCC, LBCC, CSUPP ]
                    
                    # read values from csv file that was created by get log command
                    admin_io=self.mFormatString(mItem[0], self.TypeStr)
                    opcode=self.mFormatString(mItem[1], self.TypeInt)
                    CommandName = self.mFormatString(mItem[2], self.TypeStr)
                    CSE = self.mFormatString(mItem[3], self.TypeInt)        
                    CCC = self.mFormatString(mItem[4], self.TypeInt)      
                    NIC = self.mFormatString(mItem[5], self.TypeInt)      
                    NCC = self.mFormatString(mItem[6], self.TypeInt)      
                    LBCC = self.mFormatString(mItem[7], self.TypeInt)      
                    CSUPP = self.mFormatString(mItem[8], self.TypeInt)      
                    
                    if int(CSUPP,16)==0:
                        self.Print( CommandName )  
                        
                        CMD_Result = self.Get_InvalidCommandOpcode_StatusCode(admin_io, opcode)
                        self.Print( "Return status code: %s" %CMD_Result)
                        if re.search("INVALID_OPCODE", CMD_Result):
                            self.Print("Pass", "p")  
                        else:
                            self.Print("Fail", "f")
                            subRt=False

                        self.Print("")

        self.Print("----------------------------------------------------------------------")     
        self.Print("")
        # end of for mItem in BuileInFile:    
        return subRt  
    
    
    def Get_InvalidCommandOpcode_StatusCode(self, CMDType, Opcode):  
        CMD_Result = ""
        
        if CMDType == "admin":
            CMD="nvme admin-passthru %s -opcode=%s 2>&1"%(self.dev, Opcode)
            CMD_Result = self.shell_cmd(CMD)
        elif CMDType == "io":
            CMD="nvme io-passthru %s -opcode=%s 2>&1"%(self.dev, Opcode)
            CMD_Result = self.shell_cmd(CMD)
        return CMD_Result

    def Check_InvalidLogPage_Pass(self):
    # return True/False        
        subRt=True
        self.Print ("")
        self.Print("----------------------------------------------------------------------")    
        # InitLogPageLists = [ supported/notSupported, LID, LogName ]
        for mItem in self.LogPageList:
            supported = mItem[0]
            LID= mItem[1]
            LogName = mItem[2]
            
            if not supported:
                self.Print(LogName)
                CMD="nvme admin-passthru %s -opcode=0x2 --cdw10=%s -r -l 16 2>&1 | sed '2,$d' "%(self.dev, LID)
                CMD_Result = self.shell_cmd(CMD) 
                self.Print( "Return status code: %s" %CMD_Result)
                if re.search("INVALID_LOG_PAGE", CMD_Result):
                    self.Print("Pass", "p")  
                else:
                    self.Print("Fail", "f")
                    subRt=False
                self.Print ("")
        self.Print("----------------------------------------------------------------------")            
        # end of for mItem   
        return subRt  
            

    def InitLogPageLists(self):
        # InitLogPageLists = [ supported/notSupported, LID, LogName ]
        
        CMDType="admin"
        GetLogOpcode=0x2
        # admin command
        self.LogPageList.append([ True, 0x01 , "Error Information" ])            
        self.LogPageList.append([ True, 0x02 , "SMART / Health Information" ])
        self.LogPageList.append([ True, 0x03 , "Firmware Slot Information" ])        
        
        supported = self.IsCommandSupported(CMDType,GetLogOpcode, 0x4)
        self.LogPageList.append([ supported, 0x04 , "Changed Namespace List" ])
        
        supported = self.IsCommandSupported(CMDType,GetLogOpcode, 0x5)
        self.LogPageList.append([ supported, 0x05 , "Commands Supported and Effects" ])
        
        supported = self.IsCommandSupported(CMDType,GetLogOpcode, 0x6)
        self.LogPageList.append([ supported, 0x06 , "Device Self-test" ])
        
        supported = self.IsCommandSupported(CMDType,GetLogOpcode, 0x7)
        self.LogPageList.append([ supported, 0x07 , "Telemetry Host-Initiated" ])
        
        supported = self.IsCommandSupported(CMDType,GetLogOpcode, 0x8)
        self.LogPageList.append([ supported, 0x08 , "Telemetry Controller-Initiated" ])
        
        supported = self.IsCommandSupported(CMDType,GetLogOpcode, 0x80)
        self.LogPageList.append([ supported, 0x80 , "Reservation Notification" ])
        
        supported = self.IsCommandSupported(CMDType,GetLogOpcode, 0x81)
        self.LogPageList.append([ supported, 0x81 , "Sanitize Status" ])
        
        
        
        
        
    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<           
    def __init__(self, argv):
        # initial parent class
        super(SMI_StatusCode, self).__init__(argv)

        self.LogPageList=[]
        self.InitLogPageLists()        
                     
    # override
    def PreTest(self):   

        return True

            
            
    # <sub item scripts>
    SubCase1TimeOut = 60
    SubCase1Desc = "Test Status Code: Invalid Command Opcode"        
    def SubCase1(self):
        ret_code=0

        self.Print ("Try to Save Get Log page 0x5 From Controller To CSVFile")
        Success = self.SaveGetLog05ToCSVFile()
        if Success:
            self.Print( "Success !","p")
        else:            
            self.Print( "Fail !","f")
            ret_code=1
            
        if Success:
            self.Print ("")
            self.Print ("Issue command if command is not supported by controller (bit CSUPP = 0 in %s"%self.File_GetLog05)
            self.Print ("And check if return code is 'Invalid Command Opcode' or not")
            self.Print ("")
            if self.Check_InvalidCommandOpcode_Pass():
                self.Print( "Case 1 result: Pass !","p")
            else:            
                self.Print( "Case 1 result: Fail !","f")
                ret_code=1

        return ret_code

    SubCase2TimeOut = 60
    SubCase2Desc = "Test Status Code: Invalid Log Page"        
    def SubCase2(self):
        ret_code=0
        
        self.Print ("Issue get log command with log id that is not supported by controller")
        Success = self.Check_InvalidLogPage_Pass()
        self.Print ("")
        if Success:
            self.Print( "Case 2 result: Pass !","p")
        else:            
            self.Print( "Case 2 result: Fail !","f")
            ret_code=1
            
        return ret_code        

    SubCase3TimeOut = 60
    SubCase3Desc = "Test Status Code: Thin Provisioning Not Supported"        
    def SubCase3(self):
        ret_code=0
        
        ThinProvisioningSupported = True if self.IdNs.NSFEAT.bit(0)=="1" else False        
        NsSupported=True if self.IdCtrl.OACS.bit(3)=="1" else False
                    
        if ThinProvisioningSupported:
            self.Print ("Thin Provisioning is Supported, quit this test")
        elif not NsSupported:
            self.Print ("Namespace Management is not Supported, quit this test")
        else:
            self.Print ("Thin Provisioning is not Supported")
            self.Print ("")
            
            self.Print ("Detach namespace 1")
            self.DetachNs(1)
            
            self.Print ("Delete namespace 1")
            self.DeleteNs(1) 
            self.shell_cmd("nvme reset %s"%self.dev_port) 
            
            self.Print ("")
            self.Print ("Issue Namespace Management command for creating namespace 1 with NSZE = 1G, NCAP=100M")
            CMD="nvme create-ns %s -s 2097152 -c 204800 2>&1"%(self.dev_port)
            CMD_Result = self.shell_cmd(CMD)            
            
            self.Print ("")
            self.Print( "Returned status code: %s" %CMD_Result)
            
            self.Print ("")
            self.Print ("Check if Return status code is 'Thin Provisioning Not Supported'")
            if re.search("THIN_PROVISIONING_NOT_SUPPORTED", CMD_Result):
                self.Print("Pass", "p")  
            else:
                self.Print("Fail", "f")
                ret_code=1   
                
            self.Print ("")
            self.Print ("Reset namespaces to ns 1")
            self.ResetNS()
            self.Print ("Done")        
            
        return ret_code        

    SubCase4TimeOut = 60
    SubCase4Desc = "Test Status Code: Controller List Invalid"        
    def SubCase4(self):
        ret_code=0
               
        NsSupported=True if self.IdCtrl.OACS.bit(3)=="1" else False
                    
        self.Print ("")
        if not NsSupported:
            self.Print ("Namespace Management is not Supported, quit this test")
        else:                        
            self.Print ("Controller ID (CNTLID) = %s"%hex(self.CNTLID))
            
            self.Print ("")
            self.Print ("Issue Namespace Attachment command for ns1 with a invalid controller ID, i.e. set controller ID = %s"%(hex(self.CNTLID+1)))          
            CMD="nvme attach-ns %s -n %s -c %s 2>&1 >/dev/null " %(self.dev_port,1, self.CNTLID+1)
            CMD_Result = self.shell_cmd(CMD)
            
            self.Print ("")
            self.Print( "Returned status code: %s" %CMD_Result)
            
            self.Print ("")
            self.Print ("Check if Return status code is 'Controller List Invalid'")
            if re.search("CONTROLLER_LIST_INVALID", CMD_Result):
                self.Print("Pass", "p")  
            else:
                self.Print("Fail", "f")
                ret_code=1   

        return ret_code        

    # </sub item scripts>
    
    
    
    
if __name__ == "__main__":
    DUT = SMI_StatusCode(sys.argv ) 
    DUT.RunScript()
    DUT.Finish()
    

    
    
    
    
    
