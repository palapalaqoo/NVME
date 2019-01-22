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


class SMI_IdentifyCommand(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_IdentifyCommand.py"
    Author = "Sam Chan"
    Version = "20190114"
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
            return 1
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

            self.Print( "Parse and save to csv file(%s)"%OUT_UserFileFullPath )
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
    
    def convert(self, lists, stopByte, startByte, mtype):   
        # return is string , eg, '0x1A' or 'SMI2262'
        # sub bytes
        subList=lists[startByte : stopByte+1]
        mStr=""
        if mtype==self.TypeInt:
            # reverse it and combine
            lists_R=subList[::-1]
            lists_R_Str="".join(lists_R)
            # Converting string to int
            mStr = hex(int(lists_R_Str, 16))
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
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x0 --namespace-id=0x1 2>&1"%self.dev
        self.IdentifyLists.append([ self.File_BuildIn_Identify_CNS00, self.File_Identify_CNS00, CMD, self.ParseFuncCNS_0x0_0x1 ])
        
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x1 2>&1"%self.dev
        self.IdentifyLists.append([ self.File_BuildIn_Identify_CNS01, self.File_Identify_CNS01, CMD, self.ParseFuncCNS_0x0_0x1 ])
        
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x3 2>&1"%self.dev
        self.IdentifyLists.append([ None, self.File_Identify_CNS02, CMD, self.ParseFuncCNS_0x0_0x1 ])
        
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x3 2>&1"%self.dev
        self.IdentifyLists.append([ None, self.File_Identify_CNS03, CMD, self.ParseFuncCNS_0x0_0x1 ])
    
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
        
            
        
    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    def TestFlowCNS_0x2(self, CNS):
        # check if controller supports the Namespace Management and Namespace Attachment commands or not
        NsSupported=True if self.IdCtrl.OACS.bit(3)=="1" else False
        MaxNs=1
        if NsSupported:
            self.Print ("controller supports the Namespace Management and Namespace Attachment commands")
            print  "try to create namespace" 
            # function CreateMultiNs() will create namespace less then 8 NS
            MaxNs = self.CreateMultiNs(NumOfNS=4)
            if MaxNs ==1:
                self.Print ("only namespace 1 has been created" ,"w")
            else:
                self.Print ("namespaces nsid from 1 to %s have been created"%MaxNs)                         
        
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x2 --namespace-id=0x1 2>&1"%self.dev
        
        self.Print("")
        for nsid in range(MaxNs+1):
        # nsid from 0
            CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x2 --namespace-id=%s 2>&1"%(nsid, self.dev)
            # returnd data structure
            self.Print( "Issue identify command with CNS=0x2 and CDW1.NSID=%s"%nsid )
            rTDS=self.shell_cmd(CMD)
            # format data structure to list 
            DS=self.AdminCMDDataStrucToListOrString(rTDS, 0)            
            if DS==None:
                self.Print( "Fail to get data structure, quit !","f")
                return False
            else:
                # self.Print( "Success to get data structure")  
                
                IDs = []
                # according Figure 37: Namespace List Format, save id to IDs where id lenght is 4 bytes
                for i in range(9):
                    ID=self.convert(lists=DS, stopByte=(i*4+3), startByte=(i*4), mtype=self.TypeInt)
                    IDs.append(ID)
                    
                self.Print( "Get data structure and check if NSIDs is in increasing order start from %s"%nsid )
                mStr=""
                nsidPoint = nsid +1
                Success=True
                for ID in IDs:
                    mStr = mStr + ID + " "
                    if nsidPoint!=ID:
                        Success=False
                                    
                self.Print( "Namespace List: %s"%mStr )
                if Success:
                    self.Print("Pass", "p")
                    self.Print("")
                else:
                    self.Print("Fail", "f")
                    return False
            
        

        
    # return True/False       
    
    def __init__(self, argv):
        # initial parent class
        super(SMI_IdentifyCommand, self).__init__(argv)
             
        self.InitDirs()
        self.IdentifyLists=[]
        self.InitIdentifyLists()
        
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

    
    SubCase2TimeOut = 600
    SubCase2Desc = "Test CNS=0x01, Identify Controller Data Structure" 
    def SubCase2(self): 
        ret_code=0
        # check if value from contrller is the same with file 'In/File_Identify_CNS00', and save value from contrller to csv file 'Out/File_Identify_CNS00'    
        if not self.TestFlow0(0x1):
            ret_code=1

        return ret_code
        
    SubCase3TimeOut = 60
    SubCase3Desc = "Test CNS=0x02, A list of 1024 namespace IDs"
    def SubCase3(self): 
        ret_code=0
        self.Print ("If the sum of the Timestamp value set by the host and the elapsed time exceeds 2^48, the value returned should be reduced modulo 2^48 ")
        
        return ret_code



    SubCase4TimeOut = 60
    SubCase4Desc = "Test CNS=0x03, Namespace Identification Descriptor structures" 
    def SubCase4(self): 
        ret_code=0
        self.Print ("If the sum of the Timestamp value set by the host and the elapsed time exceeds 2^48, the value returned should be reduced modulo 2^48 ")
        
        self
        
        return ret_code


    # </sub item scripts>
    
    
    
    
if __name__ == "__main__":
    DUT = SMI_IdentifyCommand(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 
    
    
    
    
    
