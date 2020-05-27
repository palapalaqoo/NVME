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
from random import randint
# Import VCT modules
from lib_vct.NVME import NVME
from _ctypes import sizeof


class SMI_IdentifyCommand(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_IdentifyCommand.py"
    Author = "Sam Chan"
    Version = "20200527"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    InPath = "./CSV/In/"
    OutPath = "./CSV/Out/"    
    File_BuildIn_Identify_CNS00 = "./lib_vct/CSV/CNS00_IdentifyNamespacedatastructure.csv"    
    File_Identify_CNS00 = "Identify_CNS00.csv" 
    
    File_BuildIn_Identify_CNS01 = "./lib_vct/CSV/CNS01_IdentifyControllerDataStructure.csv"    
    File_Identify_CNS01 = "Identify_CNS01.csv"    

    File_BuildIn_Identify_CNS02 = None    
    File_Identify_CNS02 = "Identify_CNS03.csv"  
        
    File_BuildIn_Identify_CNS03 = None    
    File_Identify_CNS03 = "Identify_CNS03.csv"        
    
    TypeInt=0x0
    TypeStr=0x1

    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    
    def WaitSanitizeOperationFinish(self, timeout=600, printInfo=False):
    # WaitSanitizeOperationFinish, if finish, then return true, else false(  after timeout )         
        if printInfo:
            self.Print ("")
            self.Print ("Wait sanitize operation finish if there is a sanitize operation is currently in progress(Time out = %s)"%timeout)
                        
        per = self.GetLog.SanitizeStatus.SPROG
        finish=True
        if per != 65535:
            # self.Print("The most recent sanitize operation is currently in progress, waiting the operation finish(Time out = 120s)", "w")
            WaitCnt=0
            while per != 65535:
                #print ("Sanitize Progress: %s"%per)
                per = self.GetLog.SanitizeStatus.SPROG
                WaitCnt = WaitCnt +1
                if WaitCnt ==timeout:
                    #self.Print("Time out!", "f")  
                    finish=False
                    break
                sleep(1)
            #self.Print ("Recent sanitize operation was completed")
   
        if printInfo:
            if finish:
                self.Print("Done", "p")
            else:
                self.Print("Error, Time out!", "f")  
        return finish        
    
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
        ParseCfg = self.IdentifyLists[CNS][0]
        UserFileName = self.IdentifyLists[CNS][1]
        CMD = self.IdentifyLists[CNS][2]
        ParseFunc = self.IdentifyLists[CNS][3]        
        
        OUT_UserFileFullPath=self.OutPath+UserFileName
        IN_UserFileFullPath=self.InPath+UserFileName
        
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
                # read name and value from csv file that was created by identify command
                Name=mItem[0]
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


                
    def SaveIdentifyFromControllerToCSVFile(self, CNS):
    # return True/False
    # BuileInFileName, BuileIn File Name
    # UserFileName,  user file name        
        ParseCfg = self.IdentifyLists[CNS][0]
        UserFileName = self.IdentifyLists[CNS][1]
        CMD = self.IdentifyLists[CNS][2]
        ParseFunc = self.IdentifyLists[CNS][3]
        
        OUT_UserFileFullPath=self.OutPath+UserFileName

        if ParseCfg!=None:
            self.Print( "Check if BuileInFile exist or not")
            BuileInFile = self.ReadCSVFile(ParseCfg)
            if BuileInFile==None:
                self.Print( "BuileInFile is not exist(%s), quit !"%ParseCfg,"f")
                return False
            else:            
                self.Print( "BuileInFile exist", "p")
        
        self.Print( "Issue identify command to get data structure")
        # returnd data structure
        rTDS=self.shell_cmd(CMD)
        # format data structure to list 
        DS=self.AdminCMDDataStrucToListOrString(rTDS, 0)            
        if DS==None:
            self.Print( "Fail to get data structure, quit !","f")
            return False
        else:
            self.Print( "Success to get data structure")

            self.Print( "Parse and save data structure to csv file(%s)"%OUT_UserFileFullPath )
            ParseFunc(ParseCfg, OUT_UserFileFullPath, DS)
            
            return True       
        
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
                if Name=="NGUID":
                    pass
                          
                StopByte=int(mItem[1])
                StartByte=int(mItem[2])                
                mType=int(mItem[3])
                # value from controller,  and format it
                ValueC =self.convert(DS, StopByte, StartByte, mType)
                ValueC = self.mFormatString(ValueC, mType)
                    
                # save to csv file
                self.SaveToCSVFile(UserFile, Name, ValueC)

    def SaveToCSVFile(self, fileName, name, value):
        fileNameFullPath = fileName
        # if file not exist, then create it
        if not os.path.exists(fileNameFullPath):
            f = open(fileNameFullPath, "w")
            f.close()            
        
        # write
        with open(fileNameFullPath, 'a') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([name, value])               
    
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
            # mStr = hex(int(subList_Str, 16))
            mStr = "0x"+subList_Str
            
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
                valueIn="0x%x"%int(valueIn, 16)
            else:                
                valueIn="0x%x"%int(valueIn)
           
            
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
        # If ./CSV/Out not exist, Create it       
        if not os.path.exists(self.OutPath):
            os.makedirs(self.OutPath)  
        '''
        # remove all file in /CSV/Out
        if os.path.exists(self.OutPath):
            shutil.rmtree(self.OutPath) 
        # Create dir
        if not os.path.exists(self.OutPath):
            os.makedirs(self.OutPath)    
        '''
        if os.path.exists(self.OutPath+self.File_Identify_CNS00):
            os.remove(self.OutPath+self.File_Identify_CNS00)    
        if os.path.exists(self.OutPath+self.File_Identify_CNS01):
            os.remove(self.OutPath+self.File_Identify_CNS01)               
        if os.path.exists(self.OutPath+self.File_Identify_CNS02):
            os.remove(self.OutPath+self.File_Identify_CNS02)               
        if os.path.exists(self.OutPath+self.File_Identify_CNS03):
            os.remove(self.OutPath+self.File_Identify_CNS03)   
                                    
    def CheckCorrectness(self, CNS): 
    # read /Out/UserFileName and check correctness of value
        UserFileName = self.IdentifyLists[CNS][1]
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
    
    def InitIdentifyLists(self):
        # IdentifyLists = [ File_BuildIn_Identify, File_Identify_CNSxx, command ]
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x0 --namespace-id=0x1 2>&1"%self.dev_port
        self.IdentifyLists.append([ self.File_BuildIn_Identify_CNS00, self.File_Identify_CNS00, CMD, self.ParseFuncCNS_0x0_0x1 ])
        
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x1 2>&1"%self.dev_port
        self.IdentifyLists.append([ self.File_BuildIn_Identify_CNS01, self.File_Identify_CNS01, CMD, self.ParseFuncCNS_0x0_0x1 ])
        
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x3 2>&1"%self.dev_port
        self.IdentifyLists.append([ None, self.File_Identify_CNS02, CMD, self.ParseFuncCNS_0x0_0x1 ])
        
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x3 2>&1"%self.dev_port
        self.IdentifyLists.append([ None, self.File_Identify_CNS03, CMD, self.ParseFuncCNS_0x0_0x1 ])
    def TryToCreateNS(self, ns):
    # try to create namespace and return number of namespaes
        MaxNs=1
        if self.NsSupported:
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
        
    def TryToCreateNSwithoutAttach(self, ns):
        # first ns=1G, secend ns = 2G, 3th = 3G, etc
        NN=self.IdCtrl.NN.int
        SizeInBlock=2097152
        if self.NsSupported:
            #self.Print ("controller supports the Namespace Management and Namespace Attachment commands"            )
            # set max test namespace <=8(default)
            MaxNs=ns
            error=0
            self.Print(  "Delete all the namespcaes" )       
            for i in range(1, NN+1):        
                # delete NS
                self.DeleteNs(i)    
            self.shell_cmd("nvme reset %s"%self.dev_port)           
            # Create namespaces, and attach it
            self.Print(  "Create namespcaes form nsid 1 to nsid %s, size first ns=1G, secend ns = 2G, 3th = 3G, etc"%MaxNs )
            for i in range(1, MaxNs+1):
                sleep(0.2)
                CreatedNSID=self.CreateNs(SizeInBlock * i)        
                if CreatedNSID != i:
                    self.Print ("create namespace error!"    )
                    error=1
                    break        
            # if creat ns error          
            if error==1:
                self.Print(  "create namespcaes Fail, reset to namespaces 1" ,"w")
                self.ResetNS()
                MaxNs=1            
            return MaxNs
                        
    def TestFlow0(self, CNS):
    # return True/False       
    # test with  ParseCfg file
        subRt=True
        self.Print ("Try to Save Identify From Controller To CSVFile")
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
    def TestFlowCNS_0x2_0x10(self, CNS):
        subRt=True
        MaxNs=1
        if CNS==0x2:
            # try to create 4 namespaces and attach it , then get number of namespaces that was created
            MaxNs=self.TryToCreateNS(4)    
        if CNS==0x10:
            # try to create 3 namespaces(will not be attached) and get number of namespaces that was created
            MaxNs=self.TryToCreateNSwithoutAttach(3) 
                                    
        self.Print("")
        
        for nsid in range(MaxNs+1):
        # nsid from 0
            CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=%s --namespace-id=%s 2>&1"%(self.dev_port, CNS, nsid)
            # returnd data structure
            self.Print( "Issue identify command with CNS=%s and CDW1.NSID=%s"%(hex(CNS), nsid) )
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
    
    def TestFlowCNS_0x11(self):
        subRt=True
        if self.NsSupported:        
            # try to create 3 namespaces(will not be attached) and get number of namespaces that was created
            self.Print("try to create 3 namespaces (will not be attached)  ")  
            MaxNs = self.TryToCreateNSwithoutAttach(3)
            self.Print("")
            
            for nsid in range(1, MaxNs+1):
                CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=%s --namespace-id=%s 2>&1"%(self.dev_port, 0x11, nsid)
                # returnd data structure
                self.Print( "Issue identify command with CNS=0x11 and CDW1.NSID=%s for getting NCAP value"%(nsid) )
                rTDS=self.shell_cmd(CMD)
                # format data structure to list 
                DS=self.AdminCMDDataStrucToListOrString(rTDS, 0)            
                if DS==None:
                    self.Print( "Fail to get data structure, quit !","f")
                    subRt = 1
                else:
                    # self.Print( "Success to get data structure") 
                    NCAP=self.convert(lists=DS, stopByte=15, startByte=8, mtype=self.TypeInt)
                    NCAP=int(NCAP, 16)
                    self.Print("NCAP: %s"%hex(NCAP))
                    # check if 1th = 1G(2097152), 2th = 2G (2097152x2 )
                    self.Print("Check if NCAP in namespace %s is %sG( %s ) or not"%(nsid, nsid, hex(nsid*2097152)))
                    if NCAP== nsid*2097152:
                        self.Print("    Pass", "p")
                    else:
                        self.Print("    Fail", "f")
                        subRt=1    
        if MaxNs!=1:
            self.Print("Reset all namespaces to namespace 1 and kill other namespaces")
            self.ResetNS()
        return subRt

    def TestFlowCNS_0x12(self):
        subRt=True
        if self.NsSupported:        
            # try to create 4 namespaces and attach it , then get number of namespaces that was created
            self.Print("try to create 2 namespaces and attach it")  
            MaxNs=self.TryToCreateNS(2)                
            self.Print("")
            
            CNTLID=self.IdCtrl.CNTLID.int
            
            for nsid in range(1, MaxNs+1):
                CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=%s --namespace-id=%s 2>&1"%(self.dev_port, 0x12, nsid)
                # returnd data structure
                self.Print( "Issue identify command with CNS=0x12 and CDW1.NSID=%s for getting Controller List"%(nsid) )
                rTDS=self.shell_cmd(CMD)
                # format data structure to list 
                DS=self.AdminCMDDataStrucToListOrString(rTDS, 0)            
                if DS==None:
                    self.Print( "Fail to get data structure, quit !","f")
                    subRt = 1
                else:
                    # self.Print( "Success to get data structure") 
                    
                    self.Print( "According to Figure 38: Controller List Format")
                    NumOfId=self.convert(lists=DS, stopByte=1, startByte=0, mtype=self.TypeInt)
                    NumOfId=int(NumOfId, 16)
                    self.Print("    Number of Identifiers: %s"%hex(NumOfId))
                    
                    Identifier0=self.convert(lists=DS, stopByte=3, startByte=2, mtype=self.TypeInt)
                    Identifier0=int(Identifier0, 16)
                    self.Print("    Identifier 0: %s"%hex(Identifier0))  
                    
                    self.Print("CNTLID field in Identify Controller data structure: %s"%hex(CNTLID))  
                    self.Print("Check if Identifier 0 in Controller List is equal to CNTLID field in Identify Controller data structure")

                    if CNTLID== Identifier0:
                        self.Print("    Pass", "p")
                    else:
                        self.Print("    Fail", "f")
                        subRt=1    
                    self.Print("")    
            
            for nsid in range(1, MaxNs+1):
                CDW10=0x12|((CNTLID+1)<<16)
                CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=%s --namespace-id=%s 2>&1"%(self.dev_port, CDW10, nsid)
                # returnd data structure
                self.Print( "Issue identify command with CNS=0x12 and CNTID=%s in Command Dword 10"%hex(CNTLID+1))
                self.Print( "And CDW1.NSID=%s for getting Controller List"%(nsid) )
                rTDS=self.shell_cmd(CMD)
                # format data structure to list 
                DS=self.AdminCMDDataStrucToListOrString(rTDS, 0)            
                if DS==None:
                    self.Print( "Fail to get data structure, quit !","f")
                    subRt = 1
                else:
                    # self.Print( "Success to get data structure") 
                    
                    self.Print( "According to Figure 38: Controller List Format")
                    NumOfId=self.convert(lists=DS, stopByte=1, startByte=0, mtype=self.TypeInt)
                    NumOfId=int(NumOfId, 16)
                    self.Print("    Number of Identifiers: %s"%hex(NumOfId))
                    
                    Identifier0=self.convert(lists=DS, stopByte=3, startByte=2, mtype=self.TypeInt)
                    Identifier0=int(Identifier0, 16)
                    self.Print("    Identifier 0: %s"%hex(Identifier0))  
                    self.Print("")

                    self.Print("Check if Number of Identifiers and Identifier 0 in Controller List is equal 0")

                    if int(NumOfId)== 0 and int(Identifier0)==0 :
                        self.Print("    Pass", "p")
                    else:
                        self.Print("    Fail", "f")
                        subRt=1                         
                    self.Print("")    
        if MaxNs!=1:
            self.Print("Reset all namespaces to namespace 1 and kill other namespaces")
            self.ResetNS()
        return subRt


    def TestFlowCNS_0x13(self):
        subRt=True
        CNTLID=self.IdCtrl.CNTLID.int
        if self.NsSupported:        
            if True:
                CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=%s  2>&1"%(self.dev_port, 0x13)
                # returnd data structure
                self.Print( "Issue identify command with CNS=0x13 for getting Controller List" )
                rTDS=self.shell_cmd(CMD)
                # format data structure to list 
                DS=self.AdminCMDDataStrucToListOrString(rTDS, 0)            
                if DS==None:
                    self.Print( "Fail to get data structure, quit !","f")
                    subRt = 1
                else:
                    # self.Print( "Success to get data structure")                     
                    self.Print( "According to Figure 38: Controller List Format")
                    NumOfId=self.convert(lists=DS, stopByte=1, startByte=0, mtype=self.TypeInt)
                    NumOfId=int(NumOfId, 16)
                    self.Print("    Number of Identifiers: %s"%hex(NumOfId))
                    
                    Identifier0=self.convert(lists=DS, stopByte=3, startByte=2, mtype=self.TypeInt)
                    Identifier0=int(Identifier0, 16)
                    self.Print("    Identifier 0: %s"%hex(Identifier0))  
                    
                    self.Print("CNTLID field in Identify Controller data structure: %s"%hex(CNTLID))  
                    self.Print("Check if Identifier 0 in Controller List is equal to CNTLID field in Identify Controller data structure")

                    if CNTLID== Identifier0:
                        self.Print("    Pass", "p")
                    else:
                        self.Print("    Fail", "f")
                        subRt=1    
                    self.Print("")    
            
            if True:
                CDW10=0x13|((CNTLID+1)<<16)
                CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=%s 2>&1"%(self.dev_port, CDW10)
                # returnd data structure
                self.Print( "Issue identify command with CNS=0x13 and CNTID=%s in Command Dword 10"%hex(CNTLID+1))
                rTDS=self.shell_cmd(CMD)
                # format data structure to list 
                DS=self.AdminCMDDataStrucToListOrString(rTDS, 0)            
                if DS==None:
                    self.Print( "Fail to get data structure, quit !","f")
                    subRt = 1
                else:
                    # self.Print( "Success to get data structure")                     
                    self.Print( "According to Figure 38: Controller List Format")
                    NumOfId=self.convert(lists=DS, stopByte=1, startByte=0, mtype=self.TypeInt)
                    NumOfId=int(NumOfId, 16)
                    self.Print("    Number of Identifiers: %s"%hex(NumOfId))
                    
                    Identifier0=self.convert(lists=DS, stopByte=3, startByte=2, mtype=self.TypeInt)
                    Identifier0=int(Identifier0, 16)
                    self.Print("    Identifier 0: %s"%hex(Identifier0))  
                    self.Print("")
                    self.Print("Check if Number of Identifiers and Identifier 0 in Controller List is equal 0")

                    if int(NumOfId)== 0 and int(Identifier0)==0 :
                        self.Print("    Pass", "p")
                    else:
                        self.Print("    Fail", "f")
                        subRt=1                         
                    self.Print("")
        return subRt
         
    def TestFlowCNS_0x3(self):
        subRt=True
        # try to create 4 namespaces and get number of namespaces that was created
        MaxNs=self.TryToCreateNS(4)                    
        self.Print("")
        
        for nsid in range(1, MaxNs+1):
        # nsid from 0
            CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x3 --namespace-id=%s 2>&1"%(self.dev_port, nsid)
            # returnd data structure
            self.Print( "Issue identify command with CNS=0x3 and CDW1.NSID=%s for 4096 byte"%nsid )
            rTDS=self.shell_cmd(CMD)
            # format data structure to list 
            DS=self.AdminCMDDataStrucToListOrString(rTDS, 0)            
            if DS==None:
                self.Print( "Fail to get data structure, quit !","f")
                self.Print( "CMD: %s"%CMD, "f")
                subRt = False
            elif len(DS) != 4096:
                self.Print( "return data structure is not 4096 byte, curresnt byte: %s, quit !"%(sizeof(DS)) ,"f")
                self.Print( "CMD: %s"%CMD, "f")
                subRt = False                
            else:
                # self.Print( "Success to get data structure")  
                # according to Figure 116: Identify - Namespace Identification Descriptor, check the descriptor
                self.Print( "Check Namespace Identification Descriptor")
                self.Print( "")  
                Num = 0       
                Offset = 0    
                LastNIDLis0 = 0  
                NIDT_List = []
                while True:
                    self.Print( "")
                    self.Print( "------------------------------------------------", "b")
                    self.Print( "Parse %s th entry of Descriptor list, start address: 0x%X"%(Num, Offset))
                    # get NIDT, NIDL, NID
                    NIDT_start =  Offset + 0
                    NIDT_size = 1   # 1byte
                    NIDT_stop = NIDT_start + NIDT_size -1
                    
                    NIDL_start =  Offset + 1
                    NIDL_size = 1   # 1byte
                    NIDL_stop = NIDL_start + NIDL_size -1

                    NIDT=int(self.convert(lists=DS, stopByte=NIDT_stop, startByte=NIDT_start, mtype=self.TypeInt), 16)
                    NIDL=int(self.convert(lists=DS, stopByte=NIDL_stop, startByte=NIDL_start, mtype=self.TypeInt), 16)
                    
                    NID_start =  Offset + 4
                    NID_size = NIDL   # 1byte
                    NID_stop = NID_start + NID_size -1
                    NID=int(self.convert(lists=DS, stopByte=NID_stop, startByte=NID_start, mtype=self.TypeInt, endian="big-endian"), 16)

                    if  NIDL==0:
                        LastNIDLis0 = NIDL_stop                        
                        self.Print( "the NIDL of this descriptor is 0 at address 0x%X, it indicates the end of the Namespace Identifier Descriptor list."%LastNIDLis0)
                        self.Print( "stop parse descriptor.")
                        self.Print( "%s th entry of Descriptor list is not availabe descriptor"%(Num))
                        self.Print( "End of the list start address from 0x%X"%Offset)
                        break;

                    NIDT_List.append(NIDT)
                    Offset = NID_stop+1 # for next loop
                
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
                         
                    Num = Num +1    
                # end of parser discriptor   
                
                self.Print("")
                self.Print( "------------------------------------------------", "b")
                self.Print( "From the end of the list address = 0x%X"%(Offset))
                self.Print( "Check if All remaining bytes after the namespace identification descriptor structures should be cleared to 0h"   ) 
                ptr = Offset
                while True:
                    byte=int(self.convert(lists=DS, stopByte=ptr, startByte=ptr, mtype=self.TypeInt), 16)
                    if byte !=0:
                        self.Print("Fail at address 0x%X"%ptr, "f")     
                        subRt = False        
                        break                    
                    if ptr ==4095:  
                        self.Print("Pass", "p")      
                        break;                    
                    ptr = ptr +1
                    
                self.Print("")
                self.Print( "According to 'A controller shall not return multiple descriptors with the same Namespace Identifier Type (NIDT).'")                
                self.Print( "List NIDT for all descriptors")
                self.Print("%s"%NIDT_List)
                self.Print( "Check if the is no multiple descriptors with the same NIDT")
                if len(NIDT_List) == len(set(NIDT_List)):
                    self.Print("Pass", "p")  
                else:
                    self.Print("Fail", "f") 
                    subRt = False   

                self.Print("")
                self.Print( "According to 'A controller shall return at least one descriptor identifying the namespace.'")                
                self.Print( "Number of available descriptor: %s"%Num)
                self.Print( "Check if the Number of available descriptor > = 1")
                if Num >=1:
                    self.Print("Pass", "p")  
                else:
                    self.Print("Fail", "f") 
                    subRt = False                           


            
        if MaxNs!=1:
            self.Print("Reset all namespaces to namespace 1 and kill other namespaces")
            self.ResetNS()
            
        return subRt    

    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<           
    def __init__(self, argv):
        # initial parent class
        super(SMI_IdentifyCommand, self).__init__(argv)
             
        self.InitDirs()
        self.IdentifyLists=[]
        self.InitIdentifyLists()
        
        self.NsSupported=True if self.IdCtrl.OACS.bit(3)=="1" else False        
        
    # override
    def PreTest(self):   

        return True

            
            
    # <sub item scripts>
    SubCase1TimeOut = 60
    SubCase1Desc = "Test CNS=0x00, Identify Namespace data structure"        
    def SubCase1(self):
        ret_code=0
        # check if value from contrller is the same with file 'In/File_Identify_CNS00', and save value from contrller to csv file 'Out/File_Identify_CNS00'    
        if not self.TestFlow0(0x0):
            ret_code=1

        return ret_code

    
    SubCase2TimeOut = 60
    SubCase2Desc = "Test CNS=0x01, Identify Controller Data Structure" 
    def SubCase2(self): 
        ret_code=0
        # check if value from contrller is the same with file 'In/File_Identify_CNS00', and save value from contrller to csv file 'Out/File_Identify_CNS00'    
        if not self.TestFlow0(0x1):
            ret_code=1

        return ret_code
        
    SubCase3TimeOut = 60
    SubCase3Desc = "Test CNS=0x02, A list of 1024 namespace IDs containing active NSIDs"
    def SubCase3(self): 
        ret_code=0
        #self.Print ("If the sum of the Timestamp value set by the host and the elapsed time exceeds 2^48, the value returned should be reduced modulo 2^48 ")
        
        if not self.TestFlowCNS_0x2_0x10(0x2):
            ret_code=1
        
        return ret_code



    SubCase4TimeOut = 60
    SubCase4Desc = "Test CNS=0x03, Namespace Identification Descriptor structures" 
    def SubCase4(self): 
        ret_code= 0
        
        if not self.TestFlowCNS_0x3():
            ret_code=1
        
        return ret_code

    SubCase5TimeOut = 60
    SubCase5Desc = "Test CNS=0x10, A list of 1024 namespace IDs containing allocated NSIDs" 
    def SubCase5(self): 
        ret_code=0
        if self.NsSupported:        
            if not self.TestFlowCNS_0x2_0x10(0x10):
                ret_code=1
        else:
            self.Print("Namespace Management supported: No")
            self.Print("Quit this test case")        
        return ret_code        

    SubCase6TimeOut = 60
    SubCase6Desc = "Test CNS=0x11, Identify Namespace data structure for the namespace specified NSID" 
    def SubCase6(self): 
        ret_code=0
        if self.NsSupported:        
            if not self.TestFlowCNS_0x11():
                ret_code=1
        else:
            self.Print("Namespace Management supported: No")
            self.Print("Quit this test case")        
        return ret_code  

    
    SubCase7TimeOut = 600
    SubCase7Desc = "Test CNS=0x12, Controller List for specified Namespace" 
    def SubCase7(self): 
        ret_code=0
        if self.NsSupported:        
            if not self.TestFlowCNS_0x12():
                ret_code=1
        else:
            self.Print("Namespace Management supported: No")
            self.Print("Quit this test case")        
        return ret_code  

    SubCase8TimeOut = 60
    SubCase8Desc = "Test CNS=0x13, Controller List of NVM subsystem" 
    def SubCase8(self): 
        ret_code=0
        if self.NsSupported:        
            if not self.TestFlowCNS_0x13():
                ret_code=1
        else:
            self.Print("Namespace Management supported: No")
            self.Print("Quit this test case")        
        return ret_code      
 
    SubCase9TimeOut = 3000
    SubCase9Desc = "Test Namespace Utilization (NUSE)" 
    def SubCase9(self): 
        ret_code=0
        
        ThinProvisioningSupported =True if self.IdNs.NSFEAT.bit(0)=="1" else False
        if not ThinProvisioningSupported:    
            self.Print("ThinProvisioning not supported", "p")
        else:
            self.Print("ThinProvisioning supported", "p")
                    
        self.Print("")
        self.Print("1) Check if NUSE is changeable or not")
        self.SetPrintOffset(4)
        self.Print("Try to format device with LBAF0, SES=1")
        CMD = "nvme format %s -n 1 -l 0 -s 1 -i 0"%self.dev
        self.Print("Issue format cmd: %s "%CMD)        
        consoleOut, Status = self.shell_cmd_with_sc(CMD)
        if (Status!=0):
            self.Print("fail to format device, quit!", "f")
            return 1
        else:
            self.Print("Done")
            
        # return LBAF[[0, MS, LBADS, RP], [1, MS, LBADS, RP].. ,[15, MS, LBADS, RP]] , all value is interger
        self.Print("")
        self.Print("Try to get current LBA Data Size (LBADS)")
        LBAF = self.GetAllLbaf()
        LBADS = LBAF[0][2]
        LBADSinByte = pow(2,LBADS)
        self.Print("Current LBADS: %s byte"%LBADSinByte)
        
        
        self.Print("")
        self.Print("fio write 10G data")    
        NUSE = self.IdNs.NUSE.int
        self.Print("Current NUSE: %s (%s)"%(hex(NUSE), NUSE), "p")        
        
        self.Print("")
        testSizeInLBA = 10*1024*1024*1024/LBADSinByte    # 10G/LBADSinByte
        self.Print("Try to write data to first 10G(LBA = 0x%X), pattern = 0xAD"%testSizeInLBA)
        self.fio_write(offset=0 , size= "10G", pattern = 0xAC, showProgress=True)
        sleep(0.5)
        self.Print("Done")        
        
        self.Print("")
        NUSE_c = self.IdNs.NUSE.int
        self.Print("Current NUSE: %s (%s)"%(hex(NUSE_c), NUSE_c), "p")

        # if write can not change NUSE, and not ThinProvisioning, the quit case
        if(NUSE == NUSE_c):
            if not ThinProvisioningSupported:
                self.Print("NUSE was not changed after command", "p")
                self.Print("Because ThinProvisioning not supported, according to Spec.. ")
                self.Print("- A controller may report NUSE equal to NCAP at all times")
                self.Print("- if the product is not targeted for thin provisioning environments.")
                self.Print("")
                self.Print(" Check if NUSE equal to NCAP or not")
                NCAP = self.IdNs.NCAP.int
                if NCAP==NUSE_c:
                    self.Print("Pass!, and skip test case", "p")
                    return 0
                else:
                    self.Print("Fail!, NCAP=0x%X, and skip test case"%NCAP, "f") 
                    return 1                   
                
                
                
            else:
                self.Print("NUSE was not changed after command, fail", "f")
                ret_code = 1    
        else:
            self.Print("NUSE is changeable", "p")
              
        self.Print("")
        DiffNUSE = NUSE_c - NUSE
        self.Print("Difference value of NUSE: %s"%(DiffNUSE))
        self.Print("Check if Difference value of NUSE = %s or not"%testSizeInLBA)
        if(DiffNUSE == testSizeInLBA):
            self.Print("Pass!", "p")
        else:
            self.Print("Fail!", "f")
            ret_code = 1        


        self.Print("")
        self.SetPrintOffset(0)
        self.Print("2) Test format command with LBAF0, SES=0")
        self.SetPrintOffset(4)
        CMD = "nvme format %s -n 1 -l 0 -s 0 -i 0"%self.dev
        self.Print("Issue format cmd: %s "%CMD)
        consoleOut, Status = self.shell_cmd_with_sc(CMD)
        if (Status!=0):
            self.Print("fail to format device, quit!", "f")
            return 1
        else:
            self.Print("Done")
            
        self.Print("")
        self.Print("Check if NUSE is keeping changing after format command for every 0.5s, expect not change and NUSE=0")
        result=True
        for i in range(10):
            NUSE = self.IdNs.NUSE.int
            self.Print("Current NUSE: %s (%s)"%(hex(NUSE), NUSE), "p")  
            if NUSE!=0:
                result=False
            sleep(0.5)
        if result:
            self.Print("Pass!", "p")
        else:
            self.Print("Fail!", "f")
            ret_code = 1
            
        self.Print("")
        self.Print("Wait for NUSE=0")
        while True:
            NUSE = self.IdNs.NUSE.int
            if NUSE==0:
                break
            sleep(0.5)
        self.Print("Done")    
            
        self.Print("")
        self.SetPrintOffset(0)
        self.Print("3) write command")    
        self.SetPrintOffset(4)
        NUSE = self.IdNs.NUSE.int
        self.Print("Current NUSE: %s (%s)"%(hex(NUSE), NUSE), "p")        

        testSizeInLBA = randint(0x0, 0xFF) * 8  # testSizeInLBA 4K align
        ActualSize = testSizeInLBA*LBADSinByte
        self.Print("Try to write %s LBA(%s bytes), start from 0x0, pattern = 0xCE"%(testSizeInLBA, ActualSize))        
        self.fio_write(offset = 0, size = ActualSize, pattern = 0xCE,  fio_bs = "4k")
        if self.fio_isequal(offset = 0, size = ActualSize, pattern = 0xCE, fio_bs = "4k"):
            self.Print("Done")
        else:
            self.Print("Fail to write data, quit!", "f")
            return 1
        
        NUSE_c = self.IdNs.NUSE.int
        self.Print("Current NUSE: %s (%s)"%(hex(NUSE_c), NUSE_c), "p")  
              
        self.Print("")
        DiffNUSE = NUSE_c - NUSE
        self.Print("Difference value of NUSE: %s"%(DiffNUSE))
        self.Print("Check if Difference value of NUSE = %s or not"%testSizeInLBA)
        if(DiffNUSE == testSizeInLBA):
            self.Print("Pass!", "p")
        else:
            self.Print("Fail!", "f")
            ret_code = 1 

        self.Print("")
        self.SetPrintOffset(0)
        self.Print("4) write uncorrectable command")    
        self.SetPrintOffset(4)        
        WriteUncSupported = True if self.IdCtrl.ONCS.bit(1)=="1" else False
        if not WriteUncSupported:    
            self.Print("Write Uncorrectable not supported", "w")
        else:
            self.Print("Write Uncorrectable supported", "p")

            self.Print("Try to format device with LBAF0")
            consoleOut, Status = self.shell_cmd_with_sc("nvme format %s -n 1 -l 0 -s 0 -i 0"%self.dev)
            if (Status!=0):
                self.Print("fail to format device, quit!", "f")
                return 1
            else:
                self.Print("Done")

            NUSE = self.IdNs.NUSE.int
            self.Print("Current NUSE: %s (%s)"%(hex(NUSE), NUSE), "p")  
            testSizeInLBA = randint(0x0, 0xFF) * 8
            self.Print("Issue write uncorrectable command with start LBA = 0, BlockCnt = %s"%(testSizeInLBA))
            self.write_unc(SLB = 0, BlockCnt = testSizeInLBA-1)
            
            NUSE_c = self.IdNs.NUSE.int
            self.Print("Current NUSE: %s (%s)"%(hex(NUSE_c), NUSE_c), "p")
            self.Print("")
            DiffNUSE = NUSE_c - NUSE
            self.Print("Difference value of NUSE: %s"%(DiffNUSE))
            self.Print("Check if Difference value of NUSE = %s or not"%(testSizeInLBA))
            if(DiffNUSE == testSizeInLBA):
                self.Print("Pass!", "p")
            else:
                self.Print("Fail!", "f")
                ret_code = 1


        self.Print("")
        self.SetPrintOffset(0)
        self.Print("5) Deallocate command")    
        self.SetPrintOffset(4)              
        DSMSupported = True if self.IdCtrl.ONCS.bit(2)=="1" else False
        if not DSMSupported:    
            self.Print("DSM(deallocate) not supported(deallocate)", "w")  
        else:
            self.Print("DSM(deallocate) supported", "p")

            self.Print ("Start to write 100M data from block 0 with pattern is 0x5A")
            self.fio_write(0, "100M", 0x5A, 1) 

            NUSE = self.IdNs.NUSE.int
            self.Print("Current NUSE: %s (%s)"%(hex(NUSE), NUSE), "p")  
            testSizeInLBA = randint(0x0, 0xFF) * 8
            self.Print("Issue deallocate command with start LBA = 0, BlockCnt = %s"%(testSizeInLBA))
            CMD = "nvme dsm %s -s 0 -b %s -d"%(self.dev, testSizeInLBA)
            mStr, Status = self.shell_cmd_with_sc(CMD)
            if (Status!=0):
                self.Print("Write deallocate fail!", "f")
                self.Print("Command: %s"%CMD, "f")
                self.Print("Quit!", "f")
                return 1
            else:
                self.Print("Done", "p")
                
            
            NUSE_c = self.IdNs.NUSE.int
            self.Print("Current NUSE: %s (%s)"%(hex(NUSE_c), NUSE_c), "p")
            self.Print("")
            DiffNUSE = NUSE - NUSE_c
            self.Print("Difference value of NUSE: %s"%(DiffNUSE))
            self.Print("Check if Difference value of NUSE = %s or not"%(testSizeInLBA))
            if(DiffNUSE == testSizeInLBA):
                self.Print("Pass!", "p")
            else:
                self.Print("Fail!", "f")
                ret_code = 1


        self.Print("")
        self.SetPrintOffset(0)
        self.Print("6) Write zeros command")    
        self.SetPrintOffset(4)
        WZeroSupported = True if self.IdCtrl.ONCS.bit(3)=="1" else False
        if not WZeroSupported:    
            self.Print("Write zeros not supported(deallocate)", "w")  
        else:
            self.Print("Write zeros supported", "p")

            self.Print ("Start to write 100M data from block 0 with pattern is 0x5A")
            self.fio_write(0, "100M", 0x5A, 1) 

            NUSE = self.IdNs.NUSE.int
            self.Print("Current NUSE: %s (%s)"%(hex(NUSE), NUSE), "p")  
            testSizeInLBA = randint(0x0, 0xFF) * 8
            self.Print("Issue write zero command with start LBA = 0, BlockCnt = %s"%(testSizeInLBA))
            CMD = "nvme write-zeroes %s -s 0 -c %s"%(self.dev, testSizeInLBA)
            mStr, Status = self.shell_cmd_with_sc(CMD)
            if (Status!=0):
                self.Print("Write zeroes fail!", "f")
                self.Print("Command: %s"%CMD, "f")
                self.Print("Quit!", "f")
                return 1
            else:
                self.Print("Done", "p")
                
            
            NUSE_c = self.IdNs.NUSE.int
            self.Print("Current NUSE: %s (%s)"%(hex(NUSE_c), NUSE_c), "p")
            self.Print("")
            DiffNUSE = NUSE - NUSE_c
            self.Print("Difference value of NUSE: %s"%(DiffNUSE))
            self.Print("Check if Difference value of NUSE = %s or not"%(testSizeInLBA))
            if(DiffNUSE == testSizeInLBA):
                self.Print("Pass!", "p")
            else:
                self.Print("Fail!", "f")
                ret_code = 1            

        self.Print("")
        self.SetPrintOffset(0)
        self.Print("7) Sanitize(BlockErase) command")   
        self.SetPrintOffset(4)             
        BlockEraseSupport = True if (self.IdCtrl.SANICAP.bit(1) == "1") else False
        SANACT=2
        if not BlockEraseSupport:    
            self.Print("Sanitize(BlockErase) not supported", "w")  
        else:
            self.Print("Sanitize(BlockErase) supported", "p")

            self.Print ("Start to write 100M data from block 0 with pattern is 0x5A")
            self.fio_write(0, "100M", 0x5A, 1) 

            NUSE = self.IdNs.NUSE.int
            self.Print("Current NUSE: %s (%s)"%(hex(NUSE), NUSE), "p")  
            self.Print("Issue Sanitize BlockErase command")
            CMD = "nvme admin-passthru %s --opcode=0x84 --cdw10=%s 2>&1"%(self.dev, SANACT)  
            mStr, Status = self.shell_cmd_with_sc(CMD)
            if (Status!=0):
                self.Print("Sanitize fail!", "f")
                self.Print("Command: %s"%CMD, "f")
                self.Print("Quit!", "f")
                return 1
            else:
                self.Print("Done", "p")
            
            self.Print("Wait sanitize command finish, timeout: 240s")    
            if not self.WaitSanitizeOperationFinish(timeout=240, printInfo=False):   
                self.Print("Time out, quit", "f")
                return 1

            self.Print("Sanitize operation was finished")   
            NUSE_c = self.IdNs.NUSE.int
            self.Print("Current NUSE: %s (%s)"%(hex(NUSE_c), NUSE_c), "p")
            self.Print("")
            self.Print("Check if NUSE = 0 or not")
            if(NUSE_c == 0):
                self.Print("Pass!", "p")
            else:
                self.Print("Fail!", "f")
                ret_code = 1               
            
            
            
              
        self.SetPrintOffset(0)          
        return ret_code  
    
    # </sub item scripts>    
if __name__ == "__main__":
    DUT = SMI_IdentifyCommand(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 
    
    
    
    
    
