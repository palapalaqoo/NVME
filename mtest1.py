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
# Import VCT modules
from lib_vct.NVME import NVME


class SMI_CommandsSupportedAndEffectsLog(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_CommandsSupportedAndEffectsLog.py"
    Author = "Sam Chan"
    Version = "20190125"
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
    
    def GetValueFromUserFile(self, UserFile, admin_io, opcode):
        # return mItem[3] to mItem[8] if file exist
        # InitLogPage05Lists = [ admin/io, opcode, CommandName, CSE, CCC, NIC, NCC, LBCC, CSUPP ]
        value=[None,None,None,None,None,None]
        if UserFile!=None:
            for mItem in UserFile:
                # if start char=# means it is a comment, and quit it
                mStr = "^#"
                if re.search(mStr, mItem[0]):
                    pass  
                else:               
                    admin_ioC=self.mFormatString(mItem[0], self.TypeStr)
                    opcodeC=self.mFormatString(mItem[1], self.TypeInt)
                    admin_ioU=self.mFormatString(admin_io, self.TypeStr)
                    opcodeU=self.mFormatString(opcode, self.TypeInt)                    
                    
                    
                    admin_ioMatch= True if admin_ioC == admin_ioU else False
                    opcodeMatch= True if opcodeC == opcodeU else False
                    if admin_ioMatch and opcodeMatch:
                        value=mItem[3:9]
                        break
        return value    
    
    def PrintAlignString(self,S0='', S1='', S2='', S3='', S4='', S5='', S6='', S7='', S8='', S3_u='', S4_u='', S5_u='', S6_u='', S7_u='', S8_u='', mode="default"):            
        if mode!="printInfo":
            mStr = "{:<6}{:<7}{:<30}|{:<4}{:<4}{:<4}{:<4}{:<5}{:<6}|{:<4}{:<4}{:<4}{:<4}{:<5}{:<6}".format(S0, S1, S2, S3, S4, S5, S6, S7, S8, S3_u, S4_u, S5_u, S6_u, S7_u, S8_u)
        else:
            mStr = "{:<6}{:<7}{:<30}|{:<27}|{:<20}".format(S0, S1, S2, S3, S3_u)
                    
        if mode=="pass":
            self.Print( mStr , "p")        
        elif mode=="fail":
            self.Print( mStr , "f")      
        else:
            self.Print( mStr )  
            
    def CheckValuesFromControllerWithCsvFile(self):
    # return True/False

        OUT_UserFileFullPath=self.OutPath+self.File_GetLog05
        IN_UserFileFullPath=self.InPath+self.File_GetLog05
        
        subRt=True
        self.Print("Check if file %s exist or not"%IN_UserFileFullPath)
        InUserFile=self.ReadCSVFile(IN_UserFileFullPath)
        if InUserFile==None:
            self.Print("Can't find file at %s"%IN_UserFileFullPath, "w")
        else:  
            self.Print("File %s exist"%IN_UserFileFullPath, "p")         

        self.Print("Check if file %s exist or not"%OUT_UserFileFullPath)
        OutUserFile=self.ReadCSVFile(OUT_UserFileFullPath)
        if OutUserFile==None:
            self.Print("Can't find file at %s"%OUT_UserFileFullPath, "w")
            return False
        else:  
            self.Print("File %s exist"%OUT_UserFileFullPath, "p")  
            self.Print( "" )          

            self.Print( "")
            self.Print( "Start to check values ..")
            self.Print("-----------------------------------------------------------------------------------------------------------")   
            self.PrintAlignString(S3="Contrller", S3_u=IN_UserFileFullPath if InUserFile!=None else (IN_UserFileFullPath+'(missing)'), mode="printInfo")
            self.PrintAlignString("Type", "Opcode", "Desc", "CSE", "CCC","NIC", "NCC", "LBCC", "CSUPP", "CSE", "CCC","NIC", "NCC", "LBCC", "CSUPP")
            self.Print("-----------------------------------------------------------------------------------------------------------")   

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
                    ValueC =[CSE, CCC, NIC, NCC, LBCC, CSUPP ]      

                    # read values from user input csv file
                    CSE_u, CCC_u, NIC_u, NCC_u, LBCC_u, CSUPP_u = self.GetValueFromUserFile(InUserFile, admin_io, opcode)
                    # format that
                    CSE_u = self.mFormatString(CSE_u, self.TypeInt)        
                    CCC_u = self.mFormatString(CCC_u, self.TypeInt)      
                    NIC_u = self.mFormatString(NIC_u, self.TypeInt)      
                    NCC_u = self.mFormatString(NCC_u, self.TypeInt)      
                    LBCC_u = self.mFormatString(LBCC_u, self.TypeInt)      
                    CSUPP_u = self.mFormatString(CSUPP_u, self.TypeInt)                                  
                    ValueU =[CSE_u, CCC_u, NIC_u, NCC_u, LBCC_u, CSUPP_u]      
                    
                    
                    # check if value is the same from controller and user file    
                    if InUserFile==None:                
                        self.PrintAlignString(admin_io, opcode, CommandName, CSE, CCC, NIC, NCC, LBCC, CSUPP, "N/A", "N/A", "N/A", "N/A", "N/A", "N/A")
                    elif ValueU==ValueC:        
                        self.PrintAlignString(admin_io, opcode, CommandName, CSE, CCC, NIC, NCC, LBCC, CSUPP, CSE_u, CCC_u, NIC_u, NCC_u, LBCC_u, CSUPP_u, "pass")                            
                    elif ValueU!=ValueC:      
                        self.PrintAlignString(admin_io, opcode, CommandName, CSE, CCC, NIC, NCC, LBCC, CSUPP, CSE_u, CCC_u, NIC_u, NCC_u, LBCC_u, CSUPP_u, "fail")   
                        subRt=False
                    
        self.Print("----------------------------------------------------------------------")     
        self.Print("")
        # end of for mItem in BuileInFile:    
        return subRt  


                
    def SaveGetLog05ToCSVFile(self):
    # return True/False
        
        OUT_UserFileFullPath=self.OutPath+self.File_GetLog05
        
        self.Print( "Issue get log command with log id = 5") 
        DS=self.get_log2byte(0x5, 4096)
        if DS==None:
            self.Print( "Fail to get data structure, quit !","f")
            return False
        else:
            self.Print( "Success to get data structure")

            self.Print( "Parse and save data structure to csv file(%s)"%OUT_UserFileFullPath )
            self.ParseFunc(DS)
            
            return True       
    
    def ParseFunc(self, DS):
                  
        # write info to csv file
        self.WriteInfo()  
              
        for mItem in self.LogPage05List:
            
            # start to parse
            admin_io = mItem[0]
            opcode = mItem[1]
            CommandName = mItem[2]
            
            StartByte = 0 if admin_io=="admin" else 1024
            StartByte = StartByte + (opcode*4)
            StopByte = StartByte +3

            # Commands Supported and Effects Data Structure
            CSEDS =int( self.convert(DS, StopByte, StartByte, self.TypeInt), 16)
      
            # CSE, bit 16, 17
            CSE =(CSEDS & ((1<< 16) | (1<<17)))>>16
            # CCC, bit 4
            CCC =(CSEDS & (1<< 4) )>>4
            # NIC, bit 3
            NIC =(CSEDS & (1<< 3) )>>3
            # NCC, bit 2
            NCC =(CSEDS & (1<< 2) )>>2
            # LBCC, bit 1
            LBCC =(CSEDS & (1<< 1) )>>1
            # CSUPP, bit 0
            CSUPP =(CSEDS & (1<< 0)) >>0
            
            mlist = [admin_io, opcode, CommandName, CSE, CCC, NIC, NCC, LBCC, CSUPP]
            self.SaveToCSVFile(mlist)
            
    def WriteInfo(self):

        mlist=["# author: Sam Chan"]
        self.SaveToCSVFile(mlist)
        mlist = ["# Note: If row start with #, then comment out the row"]
        self.SaveToCSVFile(mlist)
        mlist = ["# admin/io", "opcode", "CommandName", "CSE", "CCC", "NIC", "NCC", "LBCC", "CSUPP" ]
        self.SaveToCSVFile(mlist)

    def SaveToCSVFile(self, ValueList):
        fileNameFullPath = self.OutPath + self.File_GetLog05
        # if file not exist, then create it
        if not os.path.exists(fileNameFullPath):
            f = open(fileNameFullPath, "w")
            f.close()            
        
        # write
        with open(fileNameFullPath, 'a') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(ValueList)               
    
    def convert(self, lists, stopByte, startByte, mtype, endian="little-endian"):   
        # return is string , eg, '0x1A' or 'SMI2262'
        
        # if error
        if startByte>stopByte and mtype==self.TypeInt:
            return "0"
        if startByte>stopByte and mtype==self.TypeStr:
            return ""
                    
        # sub bytes
        subList=lists[startByte : stopByte+1]
        mStr=""
        if mtype==self.TypeInt:
            if endian=="little-endian":
                # reverse it and combine
                subList=subList[::-1]
            subList_Str="".join(subList)
            # Converting string to int
            mStr = hex(int(subList_Str, 16))
        elif mtype==self.TypeStr: 
            for byte in subList:
                mStr=mStr+chr(int(byte,16))    
        else:
            mStr =  "0"
        return mStr
    
    def RemoveSpaces(self, valueIn):
        # remove space at front and back       
        RE="\s*(\w.*$)"
        if re.search(RE, valueIn):
            valueIn=re.search(RE, valueIn).group(1)
        RE="(^.*\w)\s*"
        if re.search(RE, valueIn):
            valueIn=re.search(RE, valueIn).group(1) 
        return valueIn
    
    def mFormatString(self, valueIn, mType ):
        # if type is int, then format it to hex string,  and remove space at front and back

        # if None
        if valueIn==None:
            return None
        
        # remove space at front and back     
        valueIn=self.RemoveSpaces(valueIn)        
        
        # if type is int, then format it to hex string
        if mType==self.TypeInt:
            # if 0xh or 0xH
            if re.search("0x(\w+)", valueIn) or re.search("0X(\w+)", valueIn):   
                valueIn=hex(int(valueIn, 16))  
            else:                
                valueIn=hex(int(valueIn))  
           
            
        return valueIn

    
    def InitDirs(self):
        # If ./CSV not exist, Create it
        if not os.path.exists("./CSV"):
            os.makedirs("./CSV")
        
        # If ./CSV/In not exist, Create it
        if not os.path.exists(self.InPath):
            os.makedirs(self.InPath)
            
        if not os.path.exists(self.OutPath):
            os.makedirs(self.OutPath)  
        
        # remove all file in /CSV/Out
        if os.path.exists(self.OutPath):
            shutil.rmtree(self.OutPath) 
        # Create dir
        if not os.path.exists(self.OutPath):
            os.makedirs(self.OutPath)    

    
    def InitLogPage05Lists(self):
        # InitLogPage05Lists = [ admin/io, opcode, CommandName, CSE, CCC, NIC, NCC, LBCC, CSUPP ]
        
        # admin command
        self.LogPage05List.append([ "admin", 0x0 , "Delete I/O Submission Queue", None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0x1 , "Create I/O Submission Queue", None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0x2 , "Get Log Page"                           , None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0x4 , "Delete I/O Completion Queue", None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0x5 , "Create I/O Completion Queue", None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0x6 , "Identify"                   , None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0x8 , "Abort"                      , None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0x9 , "Set Features"               , None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0xA , "Get Features"               , None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0xC , "Asynchronous Event Request" , None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0xD , "Namespace Management"       , None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0x10, "Firmware Commit"            , None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0x11, "Firmware Image Download"    , None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0x14, "Device Self-test"                      , None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0x15, "Namespace Attachment"       , None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0x18, "Keep Alive"                 , None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0x19, "Directive Send"             , None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0x1A, "Directive Receive"          , None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0x1C, "Virtualization Management"  , None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0x1D, "NVMe-MI Send"               , None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0xE , "NVMe-MI Receive"            , None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0x7C, "Doorbell Buffer Config"     , None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0x80, "Format NVM"                 , None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0x81, "Security Send"              , None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0x82, "Security Receive"           , None, None, None, None, None, None ])
        self.LogPage05List.append([ "admin", 0x84, "Sanitize"                   , None, None, None, None, None, None ])
        
        # IO command
        self.LogPage05List.append([ "io", 0x0  , "Flush", None, None, None, None, None, None ])
        self.LogPage05List.append([ "io", 0x1  , "Write", None, None, None, None, None, None ])
        self.LogPage05List.append([ "io", 0x2  , "Read", None, None, None, None, None, None ])
        self.LogPage05List.append([ "io", 0x4  , "Write Uncorrectable", None, None, None, None, None, None ])
        self.LogPage05List.append([ "io", 0x5  , "Compare", None, None, None, None, None, None ])
        self.LogPage05List.append([ "io", 0x8  , "Write Zeroes", None, None, None, None, None, None ])
        self.LogPage05List.append([ "io", 0x9  , "Dataset Management", None, None, None, None, None, None ])
        self.LogPage05List.append([ "io", 0xD  , "Reservation Register", None, None, None, None, None, None ])
        self.LogPage05List.append([ "io", 0xE  , "Reservation Report", None, None, None, None, None, None ])
        self.LogPage05List.append([ "io", 0x11 , "Reservation Acquire", None, None, None, None, None, None ])
        self.LogPage05List.append([ "io", 0x15 , "Reservation Release", None, None, None, None, None, None ])        

    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<           
    def __init__(self, argv):
        # initial parent class
        super(SMI_CommandsSupportedAndEffectsLog, self).__init__(argv)
             
        self.InitDirs()
        self.LogPage05List=[]
        self.InitLogPage05Lists()
        
    # override
    def PreTest(self):   

        return True

            
            
    # <sub item scripts>
    SubCase1TimeOut = 600
    SubCase1Desc = "Test Save Get Log page 0x5 To CSVFile(./CSV/Out/GetLog_05.csv)"        
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
            self.Print ("Check values From Controller with csv file")
            if self.CheckValuesFromControllerWithCsvFile():
                self.Print( "Pass !","p")
            else:            
                self.Print( "Fail !","f")
                ret_code=1

        return ret_code

        



    # </sub item scripts>
    
    
    
    
if __name__ == "__main__":
    DUT = SMI_CommandsSupportedAndEffectsLog(sys.argv ) 
    DUT.RunScript()
    DUT.Finish()
    

    
    
    
    
    
