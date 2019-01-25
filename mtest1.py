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
    
    def GetValueFromUserFile(self, UserFile, idName):
        value=None
        if UserFile!=None:
            for mItem in UserFile:
                if self.RemoveSpaces(mItem[0].upper()) == self.RemoveSpaces(idName.upper()):
                    value=mItem[1]
                    break
        return value    
    
    def PrintAlignString(self,S0, S1, S2, PF="default"):            
        mStr = "{:<8}\t{:<30}\t{:<30}".format(S0, S1, S2)
        if PF=="pass":
            self.Print( mStr , "p")        
        elif PF=="fail":
            self.Print( mStr , "f")      
        else:
            self.Print( mStr )  
            
    def CheckValuesFromControllerWithCsvFile(self, CNS):
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
            self.Print("----------------------------------------------------------------------")   
            self.PrintAlignString("Name", "Controller", IN_UserFileFullPath if InUserFile!=None else IN_UserFileFullPath+"(missing)")
            self.Print("----------------------------------------------------------------------")   

            for mItem in OutUserFile:
                # if start char=# means it is a comment, and quit it
                mStr = "^#"
                if re.search(mStr, mItem[0]):
                    pass   
                else:                 
                    # InitLogPage05Lists = [ admin/io, opcode, CommandName, CSE, CCC, NIC, NCC, LBCC, CSUPP ]
                    # read name and value from csv file that was created by get log command
                    Name=mItem[3]
                    ValueC=mItem[1]
                    
                    # check value type, 0= int, 1= string
                    mStr="^0x"
                    if re.search(mStr, ValueC):  
                        mType = 0
                    else:
                        mType = 1
                    
                    # value from controller,  and format it
                    ValueC = self.mFormatString(ValueC, mType)
                    # value from user,  and format it
                    ValueU = self.GetValueFromUserFile(InUserFile, Name)
                    ValueU = self.mFormatString(ValueU, mType)                                        
                    
                    # check if value is the same from controller and user file    
                    if ValueU==None:                                
                        self.PrintAlignString(Name, ValueC, "N/A")
                    elif ValueU==ValueC:        
                        self.PrintAlignString(Name, ValueC, ValueU, "pass")                            
                    elif ValueU!=ValueC:      
                        self.PrintAlignString(Name, ValueC, ValueU, "fail")   
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
        
    def ParseFuncCNS_0x0_0x1(self, ParseCfg, UserFile, DataStructIn):
        DS = DataStructIn
        ParseCfgList = self.ReadCSVFile(ParseCfg)
        for mItem in ParseCfgList:
            # if start char=# means it is a comment, and quit it
            mStr = "^#"
            if re.search(mStr, mItem[0]):
                pass   
            else:                 
                Name=mItem[0]                  
                StopByte=int(mItem[1])
                StartByte=int(mItem[2])                
                mType=int(mItem[3])
                # value from controller,  and format it
                ValueC =self.convert(DS, StopByte, StartByte, mType)
                ValueC = self.mFormatString(ValueC, mType)
                    
                # save to csv file
                self.SaveToCSVFile(UserFile, Name, ValueC)

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
    
    def GetIdentifyDataStructure(self, CNS, CNTID):
        if CNS == 0x0:
            pass
        elif CNS == 0x1:
            pass
        elif CNS == 0x2:
            pass
        elif CNS == 0x3:            
            pass
        elif CNS == 0x10: 
            pass           
        elif CNS == 0x11:
            pass
        elif CNS == 0x12:
            pass
        elif CNS == 0x13:            
            pass
        elif CNS == 0x14:              
            pass
        elif CNS == 0x15:              
            pass        
        
    def CreateIDFileFromController(self):
        pass     
    
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
            
    def CheckCorrectness(self, CNS):
    # read /Out/UserFileName and check correctness of value
        UserFileName = self.LogPage05List[CNS][1]
        OUT_UserFileFullPath = self.OutPath + UserFileName    
    
        subRt=0
        UserFile=self.ReadCSVFile(OUT_UserFileFullPath)
        # if can't find file, then pass and return
        if UserFile==None:
            return True
        else:  
            for mItem in UserFile:            
                Name=mItem[0]       
                ValueC=mItem[1]
                # if start char=0x means it is a interger, and quit it
                mStr="0x"
                if re.search(mStr, ValueC):
                    Type=self.TypeInt
                else:     
                    Type=self.TypeStr

                if Name == "VID":
                    self.Print("Check %s"%Name)
                    self.Print("    Is the same value as reported in the ID register")
                    value=self.read_pcie(self.PCIHeader, 0)+(self.read_pcie(self.PCIHeader, 1)<<8)
                    self.Print("    %s : %s  | VID_FromPCIHeader : %s"%(Name,ValueC, hex(value)))
                    if value== int(ValueC, 16):
                        self.Print("    Pass", "p")
                    else:
                        self.Print("    Fail", "f")
                        subRt=1


                if Name == "SSVID":
                    self.Print("Check %s"%Name)
                    self.Print("    Is the same value as reported in the SS register")
                    value=self.read_pcie(self.PCIHeader, 0x2C)+(self.read_pcie(self.PCIHeader, 0x2D)<<8)
                    self.Print("    %s : %s  | SSVID_FromPCIHeader : %s"%(Name,ValueC, hex(value)))
                    if value== int(ValueC, 16):
                        self.Print("    Pass", "p")
                    else:
                        self.Print("    Fail", "f")
                        subRt=1
                        
                if Name == "FR":
                    self.Print("Check %s"%Name)
                    self.Print("    Is the same revision information that may be retrieved with the Get Log Page command")
                    value=self.RemoveSpaces(self.GetFWVer())
                    self.Print("    %s : %s  | Value from Get Log Page : %s"%(Name,ValueC, value))
                    if value== ValueC:
                        self.Print("    Pass", "p")
                    else:
                        self.Print("    Fail", "f")
                        subRt=1

                if Name == "VER":
                    self.Print("Check %s"%Name)
                    self.Print("    Is the same value as reported in the Version register")
                    value=self.CR.VS.TER.int
                    value=value+(self.CR.VS.MNR.int << 8)
                    value=value+(self.CR.VS.MJR.int << 16)                    

                    self.Print("    %s : %s  | VER from Controller Registers : %s"%(Name,ValueC, hex(value)))    
                    if value== int(ValueC, 16):
                        self.Print("    Pass", "p")
                    else:
                        self.Print("    Fail", "f")
                        subRt=1

                                                                  
        return True if subRt==0 else False
    

    def GetFWVer(self):
        FirmwareSlotInformationLog = self.get_log2byte(3, 64)
        AFI=FirmwareSlotInformationLog[0]
        ActiveFirmwareSlot= int(AFI, 16)&0b00000111
        FWVer=""
        for i in range(8):
            FWVer=FWVer+chr(int(FirmwareSlotInformationLog[i+ActiveFirmwareSlot*8], 16))
            
        return FWVer
    
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

    def TryToCreateNS(self, ns):
    # try to create namespace and return number of namespaes
        NsSupported=True if self.IdCtrl.OACS.bit(3)=="1" else False
        MaxNs=1
        if NsSupported:
            self.Print ("Namespace Management supported: Yes")
            self.Print (  "try to create namespace" )
            # function CreateMultiNs() will create namespace less then 8 NS
            MaxNs = self.CreateMultiNs(ns)
        else:
            self.Print ("Namespace Management supported: No")
        if MaxNs ==1:
            self.Print ("Number of namespaes: 1")
        else:
            self.Print ("Number of namespaes: from 1 to %s"%MaxNs)     
        return   MaxNs                 
        
    def TestFlow0(self, CNS):
    # return True/False       
    # test with  ParseCfg file
        subRt=True
        self.Print ("Try to Save Log 05 From Controller To CSVFile")
        Success = self.SaveIdentifyFromControllerToCSVFile(CNS)
        if Success:
            self.Print( "Success !","p")
        else:            
            self.Print( "Fail !","f")
            return False
            
        if Success:
            self.Print ("")
            self.Print ("Check values From Controller with csv file")
            if self.CheckValuesFromControllerWithCsvFile(CNS):
                self.Print( "Pass !","p")
            else:            
                self.Print( "Fail !","f")
                subRt = False
                
            self.Print ("")    
            self.Print ("Check Correctness")
            if self.CheckCorrectness(CNS):
                self.Print( "Pass !","p")
            else:            
                self.Print( "Fail !","f")
                subRt = False
                        
        return subRt
        
            
        

    # return True/False       
    def TestFlowCNS_0x2(self):
        subRt=True
        # try to create 4 namespaces and get number of namespaces that was created
        MaxNs=self.TryToCreateNS(4)                    
        self.Print("")
        
        for nsid in range(MaxNs+1):
        # nsid from 0
            CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x2 --namespace-id=%s 2>&1"%(self.dev, nsid)
            # returnd data structure
            self.Print( "Issue identify command with CNS=0x2 and CDW1.NSID=%s"%nsid )
            rTDS=self.shell_cmd(CMD)
            # format data structure to list 
            DS=self.AdminCMDDataStrucToListOrString(rTDS, 0)            
            if DS==None:
                self.Print( "Fail to get data structure, quit !","f")
                subRt = False
            else:
                # self.Print( "Success to get data structure")  
                
                IDs = []
                # according Figure 37: Namespace List Format, save id to IDs where id lenght is 4 bytes
                for i in range(9):
                    ID=self.convert(lists=DS, stopByte=(i*4+3), startByte=(i*4), mtype=self.TypeInt)
                    ID=int(ID, 16)
                    IDs.append(ID)
                    
                if nsid<MaxNs:
                    self.Print( "Get data structure and check if NSIDs is in increasing order from %s to %s"%(nsid+1, MaxNs) )
                else:
                    self.Print( "Get data structure and check if all NSIDs is 0" )
                mStr=""
                nsidPoint = nsid +1
                Success=True
                for ID in IDs:
                    mStr = mStr + str(ID) + " "
                    if nsidPoint<=MaxNs and nsidPoint!=ID:
                        Success=False
                    if nsidPoint>MaxNs and ID!=0:
                        Success=False            
                        
                    nsidPoint = nsidPoint +1  
                                    
                self.Print( "Namespace List: %s"%mStr )
                if Success:
                    self.Print("Pass", "p")
                    self.Print("")
                else:
                    self.Print("Fail", "f")
                    subRt = False
            
        if MaxNs!=1:
            self.Print("Reset all namespaces to namespace 1 and kill other namespaces")
            self.ResetNS()
            
        return subRt    
         
    def TestFlowCNS_0x3(self):
        subRt=True
        # try to create 4 namespaces and get number of namespaces that was created
        MaxNs=self.TryToCreateNS(4)                    
        self.Print("")
        
        for nsid in range(1, MaxNs+1):
        # nsid from 0
            CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x3 --namespace-id=%s 2>&1"%(self.dev, nsid)
            # returnd data structure
            self.Print( "Issue identify command with CNS=0x3 and CDW1.NSID=%s"%nsid )
            rTDS=self.shell_cmd(CMD)
            # format data structure to list 
            DS=self.AdminCMDDataStrucToListOrString(rTDS, 0)            
            if DS==None:
                self.Print( "Fail to get data structure, quit !","f")
                subRt = False
            else:
                # self.Print( "Success to get data structure")  
                # according to Figure 116: Identify – Namespace Identification Descriptor, check the descriptor
                NIDT=int(self.convert(lists=DS, stopByte=0, startByte=0, mtype=self.TypeInt), 16)
                NIDL=int(self.convert(lists=DS, stopByte=1, startByte=1, mtype=self.TypeInt), 16)
                NID=int(self.convert(lists=DS, stopByte=(NIDL+3), startByte=4, mtype=self.TypeInt, endian="big-endian"), 16)
                self.Print( "Check Namespace Identification Descriptor")
                self.Print( "")
                
                NIDTDefinition="Reserved"
                if NIDT==1:
                    NIDTDefinition="IEEE Extended Unique Identifier"
                if NIDT==2:
                    NIDTDefinition="Namespace Globally Unique Identifier"
                if NIDT==3:
                    NIDTDefinition="Namespace UUID"                
                        
                self.Print( "NIDT: %s ( %s )"%(NIDT, NIDTDefinition))
                self.Print( "NIDL: %s"%NIDL)
                self.Print( "NID: %s"%hex(NID))
                
                
                if NIDT==0x1:
                    EUI64 = self.IdNs.EUI64.int
                    self.Print( "")
                    self.Print( "EUI64 from Identify Namespace structure: %s"%hex(EUI64))
                    self.Print( "Check if NID = EUI64 from Identify Namespace structure")
                    self.Print("Pass", "p") if (NID==EUI64) else self.Print("Fail", "f")
                    subRt = subRt if (NID==EUI64) else False
                                                           
                    self.Print( "Check if the EUI64 field of the Identify Namespace structure is supported")
                    self.Print("Pass", "p") if (EUI64!=0) else self.Print("Fail", "f")
                    subRt = subRt if (EUI64!=0) else False
                                        
                    self.Print( "Check if NIDL= 8")
                    self.Print("Pass", "p") if (NIDL==0x8) else self.Print("Fail", "f")
                    subRt = subRt if (NIDL==0x8) else False       
                    
                if NIDT==0x2:
                    NGUID = self.IdNs.NGUID.int
                    self.Print( "")
                    self.Print( "NGUID from Identify Namespace structure: %s"%hex(NGUID))
                    self.Print( "Check if NID = NGUID from Identify Namespace structure")
                    self.Print("Pass", "p") if (NID==NGUID) else self.Print("Fail", "f")
                    subRt = subRt if (NID==NGUID) else False
                                                           
                    self.Print( "Check if the NGUID field of the Identify Namespace structure is supported")
                    self.Print("Pass", "p") if (NGUID!=0) else self.Print("Fail", "f")
                    subRt = subRt if (NGUID!=0) else False
                                        
                    self.Print( "Check if NIDL= 0x10")
                    self.Print("Pass", "p") if (NIDL==0x10) else self.Print("Fail", "f")
                    subRt = subRt if (NIDL==0x10) else False                                 

                if NIDT==0x3:                                        
                    self.Print( "Check if NIDL= 0x10")
                    self.Print("Pass", "p") if (NIDL==0x10) else self.Print("Fail", "f")
                    subRt = subRt if (NIDL==0x10) else False                           
                                           

            
        if MaxNs!=1:
            self.Print("Reset all namespaces to namespace 1 and kill other namespaces")
            self.ResetNS()
            
        return subRt    

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
    SubCase1TimeOut = 60
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

    
    SubCase2TimeOut = 60
    SubCase2Desc = "Check if value from contrller is the same with file(./CSV/In/GetLog_05.csv)"
    def SubCase2(self): 
        ret_code=0
        # check if value from contrller is the same with file 'In/File_Identify_CNS00', and save value from contrller to csv file 'Out/File_Identify_CNS00'    
        if not self.TestFlow0(0x1):
            ret_code=1

        return ret_code
        



    # </sub item scripts>
    
    
    
    
if __name__ == "__main__":
    DUT = SMI_CommandsSupportedAndEffectsLog(sys.argv ) 
    DUT.RunScript()
    DUT.Finish()
    

    
    
    
    
    
