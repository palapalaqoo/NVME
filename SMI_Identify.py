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
    Version = "20210820"
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
    TypeIntwithOffset=0x2
    TypeReserved=0x3
    

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
                if len(mItem)<2: continue
                if self.RemoveSpaces(mItem[0].upper()) == self.RemoveSpaces(idName.upper()):
                    value=mItem[1]
                    break
        return value    
    
    def PrintAlignString(self,S0, S1, S2, S3, PF="default"):            
        mStr = "{:<32}\t{:<30}\t{:<30}\t{:<30}".format(S0, S1, S2, S3)
        if PF=="pass":
            self.Print( mStr , "p")        
        elif PF=="fail":
            self.Print( mStr , "f")      
        else:
            self.Print( mStr )  
            
    def CheckValuesFromControllerWithCsvFile(self, CNS):
    # return True/False
        ParseCfg = self.IdentifyLists[CNS][0] # field that will be parsered
        UserFileName = self.IdentifyLists[CNS][1]
        CMD = self.IdentifyLists[CNS][2]
        ParseFunc = self.IdentifyLists[CNS][3]        
        
        OUT_UserFileFullPath=self.OutPath+UserFileName
        IN_UserFileFullPath=self.InPath+UserFileName
        
        if self.binFileIn!="":
            self.Print("Convert %s to %s"%(self.binFileIn, IN_UserFileFullPath), "b")
            self.SetPrintOffset(4, "add")
            DS = self.ReadFile(self.binFileIn)            
            DS=self.hexdump(DS) # after here, the format of DS is the same as nvme id-ctrl /dev/nvme0n1 for bin file               
            if self.SaveIdentifyFromListToCSVFile(DS, ParseCfg, IN_UserFileFullPath, ParseFunc):
                self.SetPrintOffset(-4, "add")
            else:
                self.Print("Fail, please check file: %s"%self.binFileIn, "f")
                self.SetPrintOffset(-4, "add")
                return False
            
        self.Print("")
        subRt=True
        self.Print("Check if file %s exist or not(for comparing identify data if applicable, else show current identify data only)"%IN_UserFileFullPath)
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
            self.Print("------------------------------------------------------------------------------------------------------------")   
            self.PrintAlignString("Name", "Controller", "Expected value", "[Bytes][Bits]", "default")
            self.PrintAlignString("", "%s"%OUT_UserFileFullPath, IN_UserFileFullPath if InUserFile!=None else IN_UserFileFullPath+"(missing)", "", "")
            self.Print("------------------------------------------------------------------------------------------------------------")   


            cnt = 0
            for mItem in OutUserFile:
                cnt +=1
                # read name and value from csv file that was created by identify command
                Name=mItem[0]
                ValueC=mItem[1]
                ByteAndBit=mItem[2] # [stop byte: start byte][stop bit: start bit]
                
                if Name=="VenderSpecRawData": continue # will show it later
                
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
                    self.PrintAlignString(Name, ValueC, "N/A", ByteAndBit, "default")
                elif ValueU==ValueC:        
                    self.PrintAlignString(Name, ValueC, ValueU, ByteAndBit, "pass")                            
                elif ValueU!=ValueC:      
                    self.PrintAlignString(Name, ValueC, ValueU, ByteAndBit, "fail")   
                    subRt=False
            if CNS==0x0:
                #self.PrintAlignString("VenderSpecRawData", "N/A", "N/A", "[4096:384][:]", "default")
                
                for info in self.CNS00_VenderSpecRawDataList:
                    # info = [line, ByteAndBit]
                    line = info[0]
                    ByteAndBit = info[1]
                    line = "VenderSpec: 0x%s"%line
                    mStr = "{:<90}\t{:<30}".format(line, ByteAndBit)
                    self.Print( mStr , "b")                      
        self.Print("----------------------------------------------------------------------")
        self.Print("Total num of item: %s"%cnt)
        self.Print("")
        # end of for mItem in BuileInFile:    
        return subRt  

    def SaveIdentifyFromControllerToCSVFile(self, CNS):
    # return True/False
    # BuileInFileName, BuileIn File Name
    # UserFileName,  user file name        
        ParseCfg = self.IdentifyLists[CNS][0] # field that will be parsered
        UserFileName = self.IdentifyLists[CNS][1]
        CMD = self.IdentifyLists[CNS][2]
        ParseFunc = self.IdentifyLists[CNS][3]
        
        OUT_UserFileFullPath=self.OutPath+UserFileName

        self.Print( "Issue identify command to get data structure")
        # returnd data structure
        rTDS, sc=self.shell_cmd_with_sc(CMD)
        if sc!=0:
            self.Print("Command fail, status: %s"%rTDS)
            return False
        else:
            self.Print("Command success")
        # format data structure to list 
        if not self.SaveIdentifyFromListToCSVFile( rTDS, ParseCfg, OUT_UserFileFullPath, ParseFunc):
            return False
        else:
            if CNS==0x0:
                self.SaveVenderSpecRawData(CMD, OUT_UserFileFullPath)
            return True 
                
    def SaveIdentifyFromListToCSVFile(self, DataStructureListIn, ParseCfg, OUT_UserFileFullPath, ParseFunc):
    # return True/False
    # BuileInFileName, BuileIn File Name
    # UserFileName,  user file name        
        
        if ParseCfg!=None:
            self.Print( "TestCase will using fields in  %s to parser data structure"%SMI_IdentifyCommand.File_BuildIn_Identify_CNS01)
            BuileInFile = self.ReadCSVFile(ParseCfg)
            if BuileInFile==None:
                self.Print( "BuileInFile is not exist(%s), quit !"%ParseCfg,"f")
                return False
            else: 
                pass           
                # self.Print( "BuileInFile exist", "p")

        # format data structure to list 
        DS=self.AdminCMDDataStrucToListOrString(DataStructureListIn, 0)            
        if DS==None:
            self.Print( "Fail to get data structure in AdminCMDDataStrucToListOrString(), quit !","f")
            return False
        else:           
            self.Print( "Start to parser and save data structure to csv file(%s)"%OUT_UserFileFullPath )
            ParseFunc(ParseCfg, OUT_UserFileFullPath, DS)
            self.Print( "Done")
        return True
    
    def SaveVenderSpecRawData(self, CMD, OUT_UserFileFullPath):
            if True:
                self.Print( "Start to parser VenderSpecRawData and save to csv file(%s)"%OUT_UserFileFullPath )
                mStr = "^(0\w\w\w):"
                self.CNS00_VenderSpecRawDataList = []
                for line in self.yield_shell_cmd(CMD):
                    # remove from 0000 to 0180, e.g. offset 384
                    # 0000: 87 19 87 19 37 46 45 30 30 37 30 43 30 36 37 31 "....7FE0070C0671"
                    if re.search(mStr, line):
                        Num=int(re.search(mStr, line).group(1), 16)
                        if Num <384:
                            continue # don't record
                        stopByte = Num + 15 #stopByte offset
                        startByte = Num                        
                        ByteAndBit = "[%s:%s][:]"%(stopByte, startByte)
                        self.CNS00_VenderSpecRawDataList.append([line, ByteAndBit] )  #record
                        # save to csv file
                        self.SaveToCSVFile(OUT_UserFileFullPath, "VenderSpecRawData", line, ByteAndBit)
                self.Print("Done")
            return True       
        
    def ParseFuncCNS_0x0_0x1(self, ParseCfg, UserFile, DataStructIn):
        DS = DataStructIn
        ParseCfgList = self.ReadCSVFile(ParseCfg)
        for mItem in ParseCfgList:
            if len(mItem)<3: # if no data
                continue
            # if start char=# means it is a comment, and quit it
            mStr = "^#"
            if re.search(mStr, mItem[0]):
                pass   
            else:  
                # name,stop byte,start byte,type, stop bit, start bit
                Name=mItem[0]        
                #if Name=="NGUID":
                #    pass
                          
                StopByte=int(mItem[1])
                StartByte=int(mItem[2])                
                mType=int(mItem[3])
                StopBit=None
                StartBit=None
                if len(mItem)>=5: # if stop bit, start bit provided in csv file
                    StopBit=int(mItem[4]) 
                    StartBit=int(mItem[5])
               
                # value from controller,  and format it
                ValueC =self.convert(DS, StopByte, StartByte, mType, StopBit, StartBit)
                ValueC = self.mFormatString(ValueC, mType)
                
                # [stop byte: start byte][stop bit: start bit]
                ByteAndBit = "[%s:%s][%s:%s]"%(StopByte, StartByte, "" if StopBit==None else StopBit, "" if StartBit==None else StartBit)
                    
                # save to csv file
                self.SaveToCSVFile(UserFile, Name, ValueC, ByteAndBit)

    def SaveToCSVFile(self, fileName, name, value, ByteAndBit):
        fileNameFullPath = fileName
        # if file not exist, then create it
        if not os.path.exists(fileNameFullPath):
            f = open(fileNameFullPath, "w")
            f.close()            
        
        # write
        with open(fileNameFullPath, 'a') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([name, value, ByteAndBit])               
    
    def convert(self, lists, stopByte, startByte, mtype, StopBit=None, StartBit=None, endian="little-endian"):   
        # return is string , eg, '0x1A' or 'SMI2262'
        # mtype=0, get string int,  ex, '0x1A' , get value from [StopBit, StartBit]
        #    e.x, lists=[0x5A, 0x2D, 0x8B], stopByte=2, startByte=1, return "0x5A2D"
        #
        # mtype=1, get string, ex,  'SMI2262'
        #
        # mtype=2, get string int, ex, '0x1A' , get value from [StopBit, StartBit] and offset=startByte where discard stopByte
        #     e.x, lists=[0x5A, 0x2D, 0x8B], startByte=1, StopBit=7, StartBit=4, return "0xD"
        # mtype=3, return string with raw data, ex. "00000000", for reserved field
        # if error
        if startByte>stopByte and mtype==self.TypeInt:
            return "0"
        if startByte>stopByte and mtype==self.TypeStr:
            return ""
        if (StopBit==None or StartBit==None) and mtype==self.TypeIntwithOffset:
            return "0"        
        
                    
        # sub bytes
        if mtype==self.TypeIntwithOffset:
            # ex, startByte=2, StartBit=10, equal to startByte=3, StartBit=2, 
            stopByte = startByte# set to startByte
            bitLen = StopBit-StartBit
            offset = StartBit/8
            startByte = startByte+offset
            StartBit=StartBit%8 # adjust StartBit
            offset = StopBit/8
            stopByte = stopByte+offset
            StopBit=StartBit + bitLen # adjust StopBit
            subList=lists[startByte : stopByte+1]
        else:
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
        elif mtype==self.TypeIntwithOffset:
            if endian=="little-endian":
                # reverse it and combine
                subList=subList[::-1]
            subList_Str="".join(subList)
            # Converting string to int
            mStr = int(subList_Str, 16)
            # format to bit string, e.x. str: 0b1001001101111 for 0x126F
            strLen = (stopByte - startByte +1)*8 + 2 # byte*8 +2 where 2 is for string '0b'
            mStr=format(mStr, '#0%sb'%strLen) # '#010b' means 10 bit include '0b'
            #mStr=bin(mStr) #e.x. str: 0b1001001101111 for 0x126F
            # get bits
            size=strLen # will equal to len(mStr)
            mStr=mStr[size-StopBit-1:size-StartBit] # get bit
            mStr= int(mStr, 2) 
            mStr="0x%X"%mStr
        elif mtype==self.TypeReserved:
        # return string with raw data, ex. "00000000"
            for byte in subList:
                mStr=mStr+byte            
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
        if mType==self.TypeReserved:
            IsZero = True
            cnt = 0
            while True:
                subStr = valueIn[-16:] # slice into 8bytes
                # if 0xh or 0xH
                if re.search("0x(\w+)", subStr) or re.search("0X(\w+)", subStr):   
                    value=int(subStr, 16)
                else:                
                    value=int(subStr)
                if value!=0:
                    IsZero = False
                    break      
                cnt+=1          
                valueIn = valueIn[:-17] # shift to right(remove 8bytes)
                if len(valueIn)==0: break
                                                 
            if IsZero:
                valueIn = "0x0"
            else:
                valueIn = "-1(not all value is zero, raw data: %s, offset: %s bytes"%(subStr, cnt*8)
            
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
                        
                if Name == "TNVMCAP":
                    self.Print("Check %s"%Name)
                    NsSupported=True if self.IdCtrl.OACS.bit(3)=="1" else False     
                    self.Print("    Namespace Management Supported") if NsSupported else self.Print("    Namespace Management not Supported")
                    if not NsSupported:
                        self.Print("    Skip due to Namespace Management is not Supported")
                    else:
                        self.Print("    TNVMCAP must > 0 because Namespace Management is Supported")
                        self.Print("    TNVMCAP: %s"%ValueC)
                        if int(ValueC, 16)>0:
                            self.Print("    Pass", "p")
                        else:
                            self.Print("    Fail", "f")
                            subRt=1
                                                                  
        return True if subRt==0 else False
    
    def CheckSanicap(self):
        SANICAP = self.IdCtrl.SANICAP.int
        
        self.CryptoEraseSupport = True if (self.IdCtrl.SANICAP.bit(0) == "1") else False
        self.BlockEraseSupport = True if (self.IdCtrl.SANICAP.bit(1) == "1") else False
        self.OverwriteSupport = True if (self.IdCtrl.SANICAP.bit(2) == "1") else False
                
        if self.BlockEraseSupport:
            self.SANACT=2
        elif self.CryptoEraseSupport:
            self.SANACT=4
        elif self.OverwriteSupport:
            self.SANACT=3
        else:
            self.SANACT=0
                            
        self.Print ("Current SANICAP: 0x%X"%SANICAP)
        self.Print("Crypto Erase sanitize operation is Supported", "p")  if self.CryptoEraseSupport else self.Print("Crypto Erase sanitize operation is not Supported", "f") 
        self.Print("Block Erase sanitize operation is Supported", "p")  if self.BlockEraseSupport else self.Print("Block Erase sanitize operation is not Supported", "f") 
        self.Print("Overwrite sanitize operation is Supported", "p")  if self.OverwriteSupport else self.Print("Overwrite sanitize operation is not Supported", "f") 
        self.Print ("")  
                
        if self.SANACT==0:
            self.Print("All sanitize operation is not supported!")
            
            self.Print ("")           
            CMD = "nvme admin-passthru %s --opcode=0x84 --cdw10=%s 2>&1"%(self.dev, 2)  
            self.Print ("Issue sanitize command(BlockErase): %s"%CMD)
            mStr, sc = self.shell_cmd_with_sc(CMD)
            self.Print ("Return status: %s"%mStr)
            self.Print("Check and expect command fail")
            if sc==0:
                self.Print ("Fail, return code=0", "f")
                return False
            else:
                self.Print("Pass, return code !=0", "p")
                
            self.Print ("")           
            CMD = "nvme admin-passthru %s --opcode=0x84 --cdw10=%s 2>&1"%(self.dev, 4)  
            self.Print ("Issue sanitize command(CryptoErase): %s"%CMD)
            mStr, sc = self.shell_cmd_with_sc(CMD)
            self.Print ("Return status: %s"%mStr)
            self.Print("Check and expect command fail")
            if sc==0:
                self.Print ("Fail, return code=0", "f")
                return False
            else:
                self.Print("Pass, return code !=0", "p")            
            
            self.Print ("")           
            CMD = "nvme admin-passthru %s --opcode=0x84 --cdw10=%s 2>&1"%(self.dev, 3)  
            self.Print ("Issue sanitize command(Overwrite): %s"%CMD)
            mStr, sc = self.shell_cmd_with_sc(CMD)
            self.Print ("Return status: %s"%mStr)
            self.Print("Check and expect command fail")
            if sc==0:
                self.Print ("Fail, return code=0", "f")
                return False
            else:
                self.Print("Pass, return code !=0", "p")  
                
            self.Print ("")
            self.Print ("keyword: If the Sanitize command is not supported, then this field shall be cleared to 0h")
            self.Print ("Check if SANICAP = 0 ")
            if SANICAP == 0:
                self.Print("Pass" , "p")
            else:
                self.Print ("Fail, SANICAP!=0", "f")
                return False
        # end of self.SANACT==0, and verify sanitize support in tool SMI_Sanitize
        return True
    
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
        
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x2 2>&1"%self.dev_port
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
        self.Print ("Try to Save Identify From Controller To CSVFile", "b")
        self.SetPrintOffset(4, "add")
        Success = self.SaveIdentifyFromControllerToCSVFile(CNS)
        if Success:
            self.Print( "Success !","p")
        else:            
            self.Print( "Fail !","f")
            return False
        self.SetPrintOffset(-4, "add")
            
        if Success:
            self.Print ("")
            self.Print ("Check values From Controller with csv file", "b")
            self.SetPrintOffset(4, "add")
            if self.CheckValuesFromControllerWithCsvFile(CNS):
                self.Print( "Pass !","p")
            else:            
                self.Print( "Fail !","f")
                subRt = False
            self.SetPrintOffset(-4, "add")    
            
            self.Print ("")    
            self.Print ("Check Correctness", "b")
            self.SetPrintOffset(4, "add")
            if self.CheckCorrectness(CNS):
                self.Print( "Pass !","p")
            else:            
                self.Print( "Fail !","f")
                subRt = False
            self.SetPrintOffset(-4, "add")    
            self.Print ("")    
            self.Print ("Check SANICAP", "b")   
            self.SetPrintOffset(4, "add")  
            if not self.CheckSanicap():
                subRt = False
            self.SetPrintOffset(-4, "add")            
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
                    
                    self.Print( "Parse returned data(According to 'Controller List Format' in NVMe spec)")
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
                    self.Print( "CMD: %s"%CMD,"f")
                    self.Print( "Returned status: %s"%rTDS,"f")
                    subRt = 1
                else:
                    # self.Print( "Success to get data structure") 
                    
                    self.Print( "Parse returned data(According to 'Controller List Format' in NVMe spec)")
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
                    self.Print( "CMD: %s"%CMD,"f")
                    self.Print( "Returned status: %s"%rTDS,"f")                    
                    subRt = 1
                else:
                    # self.Print( "Success to get data structure")                     
                    self.Print( "Parse returned data(According to 'Controller List Format' in NVMe spec)")
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
                    self.Print( "Parse returned data(According to 'Controller List Format' in NVMe spec)")
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
                        #EUI64 = self.IdNs.EUI64.int
                        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x0 --namespace-id=%s 2>&1"%(self.dev_port, nsid)
                        mStr = self.shell_cmd(CMD)
                        rtList = self.AdminCMDDataStrucToListOrString(strIn = mStr)
                        EUI64 = int(self.convert(lists=rtList, stopByte=127, startByte=120, mtype=self.TypeInt, endian="big-endian"), 16)
                        
                        self.Print( "")
                        self.Print( "EUI64 from Identify Namespace structure: %s"%hex(EUI64))
                        self.Print( "Check if NID = EUI64 from Identify Namespace structure")
                        self.Print("Pass", "p") if (NID==EUI64) else self.Print("Fail", "f")
                        subRt = subRt if (NID==EUI64) else False
                                                               
                        self.Print( "Check if the EUI64 field of the Identify Namespace structure is supported(pass if EUI64!=0)")
                        self.Print("Pass", "p") if (EUI64!=0) else self.Print("Fail", "f")
                        subRt = subRt if (EUI64!=0) else False
                                            
                        self.Print( "Check if NIDL= 8")
                        self.Print("Pass", "p") if (NIDL==0x8) else self.Print("Fail", "f")
                        subRt = subRt if (NIDL==0x8) else False       
                        
                    if NIDT==0x2:
                        #NGUID = self.IdNs.NGUID.int
                        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x0 --namespace-id=%s 2>&1"%(self.dev_port, nsid)
                        mStr = self.shell_cmd(CMD)
                        rtList = self.AdminCMDDataStrucToListOrString(strIn = mStr)
                        NGUID = int(self.convert(lists=rtList, stopByte=119, startByte=104, mtype=self.TypeInt, endian="big-endian"), 16)                        
                        
                        self.Print( "")
                        self.Print( "NGUID from Identify Namespace structure: %s"%hex(NGUID))
                        self.Print( "Check if NID = NGUID from Identify Namespace structure")
                        self.Print("Pass", "p") if (NID==NGUID) else self.Print("Fail", "f")
                        subRt = subRt if (NID==NGUID) else False
                                                               
                        self.Print( "Check if the NGUID field of the Identify Namespace structure is supported(pass if NGUID!=0)")
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
        VersionDefine = ["1.3c", "1.4", "dellx16", "hp", "lenovo", "srs"]
        VersionDdfault = VersionDefine[0]
        self.SetDynamicArgs(optionName="v", optionNameFull="version", \
                            helpMsg="nvme spec version, %s, default= %s, ex. '-v %s'"%(VersionDefine, VersionDdfault, VersionDdfault), argType=str, default=VersionDdfault)
        self.SetDynamicArgs(optionName="b", optionNameFull="binFileIn", \
                            helpMsg="Bin file for identify, will convert to csv and replace ./CSV/In/Identify_CNS00.csv for case1"\
                            "\nor ./CSV/In/Identify_CNS01.csv for case2, ex. '-b PC300_v081_IdentifyController.bin'", argType=str, default="")

        
        # initial parent class
        super(SMI_IdentifyCommand, self).__init__(argv)

        self.specVersion = self.GetDynamicArgs(0)
        if not self.specVersion in VersionDefine:   # if input is not in VersionDefine, e.g keyin wrong version
            self.specVersion = VersionDdfault
            
        self.binFileIn = self.GetDynamicArgs(1)

        if self.specVersion=="1.4":
            SMI_IdentifyCommand.File_BuildIn_Identify_CNS01 = "./lib_vct/CSV/CNS01_IdentifyControllerDataStructure_V1_4.csv"
            SMI_IdentifyCommand.File_BuildIn_Identify_CNS00 = "./lib_vct/CSV/CNS00_IdentifyNamespacedatastructure_V1_4.csv"
        if self.specVersion=="dellx16":
            # https://jira.siliconmotion.com.tw:8443/browse/VCTDEPT-835
            SMI_IdentifyCommand.File_BuildIn_Identify_CNS01 = "./lib_vct/CSV/CNS01_IdentifyControllerDataStructure_V1_4_SRS.csv"
        if self.specVersion=="hp":
            # https://jira.siliconmotion.com.tw:8443/browse/VCTDEPT-836
            SMI_IdentifyCommand.File_BuildIn_Identify_CNS01 = "./lib_vct/CSV/CNS01_IdentifyControllerDataStructure_V1_4_SRS.csv" 
        if self.specVersion=="lenovo":
            # https://jira.siliconmotion.com.tw:8443/browse/VCTDEPT-836
            SMI_IdentifyCommand.File_BuildIn_Identify_CNS01 = "./lib_vct/CSV/CNS01_IdentifyControllerDataStructure_V1_4_SRS.csv"                       
            
             
        self.InitDirs()
        self.IdentifyLists=[]
        self.InitIdentifyLists()
        
        self.NsSupported=True if self.IdCtrl.OACS.bit(3)=="1" else False  
        self.CNS00_VenderSpecRawDataList = [] # [line, ByteAndBit]
        
    # override
    def PreTest(self):   
        if self.binFileIn!="":
            if self.isfileExist(self.binFileIn):
                self.Print("%s exist"%self.binFileIn)
            else:
                self.Print("%s not exist"%self.binFileIn, "f")
                self.binFileIn=""
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
    
    SubCase10TimeOut = 3000
    SubCase10Desc = "Test status code" 
    def SubCase10(self): 
        ret_code = 0
        self.Print("1, If a controller does not support the specified CNS value, then the controller shall abort the command with a status of Invalid Field in Command", "b")
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0xFF 2>&1 > /dev/null"%self.dev_port
        self.Print("Issue CMD with CNS=0xFF: %s"%CMD)
        mStr, sc = self.shell_cmd_with_sc(CMD)
        self.Print("Return status: %s"%mStr)
        self.Print("Check if status is Invalid Field(0x2)")
        if sc==2:
            self.Print("Pass", "p") 
        else:
            self.Print("Fail", "f")
            ret_code = 1
            
        self.Print("")
        NsSupported=True if self.IdCtrl.OACS.bit(3)=="1" else False     
        self.Print("2. Identify Namespace data structure (CNS 00h) with nsid=0xFFFFFFFF", "b")
        self.Print("Namespace Management Supported") if NsSupported else self.Print("Namespace Management not Supported")
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x0 --namespace-id=0xFFFFFFFF 2>&1 > /dev/null"%self.dev_port
        if NsSupported:
            self.Print("Controller must success the command")            
            self.Print("Issue CMD: %s"%CMD)         
            mStr, sc = self.shell_cmd_with_sc(CMD)
            self.Print("Return status: %s"%mStr)
            self.Print("Check if status is success(0x0)")
            if sc==0:
                self.Print("Pass", "p") 
            else:
                self.Print("Fail", "f")
                ret_code = 1
        else:
            self.Print("Controller shall fail the command with a status code of Invalid Namespace or Format")
            self.Print("Issue CMD: %s"%CMD)         
            mStr, sc = self.shell_cmd_with_sc(CMD)
            self.Print("Return status: %s"%mStr)
            self.Print("Check if status is Invalid Namespace or Format(0xB)")
            if sc==0xB:
                self.Print("Pass", "p") 
            else:
                self.Print("Fail", "f")
                ret_code = 1  
                
        self.Print("")    
        self.Print("3. Active Namespace ID list (CNS 02h) with nsid=0xFFFFFFFE/0xFFFFFFFF", "b")
        self.Print("Controller should abort the command with status code Invalid Namespace or Format if the NSID field is set to FFFFFFFEh or FFFFFFFFh")
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x2 --namespace-id=0xFFFFFFFE 2>&1 > /dev/null"%self.dev_port
        self.Print("Issue CMD with nsid=0xFFFFFFFE: %s"%CMD)
        mStr, sc = self.shell_cmd_with_sc(CMD)
        self.Print("Return status: %s"%mStr)
        self.Print("Check if status is Invalid Namespace or Format(0xB)")
        if sc==0xB:
            self.Print("Pass", "p") 
        else:
            self.Print("Fail", "f")
            ret_code = 1    
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x2 --namespace-id=0xFFFFFFFF 2>&1 > /dev/null"%self.dev_port
        self.Print("Issue CMD with nsid=0xFFFFFFFF: %s"%CMD)
        mStr, sc = self.shell_cmd_with_sc(CMD)
        self.Print("Return status: %s"%mStr)
        self.Print("Check if status is Invalid Namespace or Format(0xB)")
        if sc==0xB:
            self.Print("Pass", "p") 
        else:
            self.Print("Fail", "f")
            ret_code = 1                          
                
        self.Print("")    
        self.Print("4. Namespace Identification Descriptor list (CNS 03h) with nsid=0xFFFFFFFF", "b")
        self.Print("Controller should abort the command with status code Invalid Namespace or Format If the NSID field does not specify an active NSID(ex. nsid=0xFFFFFFFF)")
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x3 --namespace-id=0xFFFFFFFF 2>&1 > /dev/null"%self.dev_port
        self.Print("Issue CMD with nsid=0xFFFFFFFF: %s"%CMD)
        mStr, sc = self.shell_cmd_with_sc(CMD)
        self.Print("Return status: %s"%mStr)
        self.Print("Check if status is Invalid Namespace or Format(0xB)")
        if sc==0xB:
            self.Print("Pass", "p") 
        else:
            self.Print("Fail", "f")
            ret_code = 1                 
                
        self.Print("")    
        self.Print("5. Allocated Namespace ID list (CNS 10h) with nsid=0xFFFFFFFE/0xFFFFFFFF", "b")
        self.Print("Controller should abort the command with status code Invalid Namespace or Format if the NSID field is set to FFFFFFFEh or FFFFFFFFh")
        if self.NsSupported:
            self.Print ("Namespace Management supported: Yes")
        else:
            self.Print ("Namespace Management supported: No") 
            self.Print ("Skip")            
        if self.NsSupported:
            CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x10 --namespace-id=0xFFFFFFFE 2>&1 > /dev/null"%self.dev_port
            self.Print("Issue CMD with nsid=0xFFFFFFFE: %s"%CMD)
            mStr, sc = self.shell_cmd_with_sc(CMD)
            self.Print("Return status: %s"%mStr)
            self.Print("Check if status is Invalid Namespace or Format(0xB)")
            if sc==0xB:
                self.Print("Pass", "p") 
            else:
                self.Print("Fail", "f")
                ret_code = 1    
            CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x10 --namespace-id=0xFFFFFFFF 2>&1 > /dev/null"%self.dev_port
            self.Print("Issue CMD with nsid=0xFFFFFFFF: %s"%CMD)
            mStr, sc = self.shell_cmd_with_sc(CMD)
            self.Print("Return status: %s"%mStr)
            self.Print("Check if status is Invalid Namespace or Format(0xB)")
            if sc==0xB:
                self.Print("Pass", "p") 
            else:
                self.Print("Fail", "f")
                ret_code = 1     

        self.Print("")    
        self.Print("6. Identify Namespace data structure for an Allocated Namespace ID (CNS 11h) with nsid=0xFFFFFFFF", "b")
        self.Print("Controller should abort the command with status code Invalid Namespace or Format if the NSID field is set to FFFFFFFFh")
        if self.NsSupported:
            self.Print ("Namespace Management supported: Yes")
        else:
            self.Print ("Namespace Management supported: No") 
            self.Print ("Skip")            
        if self.NsSupported:
            CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x11 --namespace-id=0xFFFFFFFF 2>&1 > /dev/null"%self.dev_port
            self.Print("Issue CMD with nsid=0xFFFFFFFF: %s"%CMD)
            mStr, sc = self.shell_cmd_with_sc(CMD)
            self.Print("Return status: %s"%mStr)
            self.Print("Check if status is Invalid Namespace or Format(0xB)")
            if sc==0xB:
                self.Print("Pass", "p") 
            else:
                self.Print("Fail", "f")
                ret_code = 1                    

        self.Print("")    
        self.Print("7. Namespace Attached Controller list (CNS 12h) with nsid=0xFFFFFFFF", "b")
        self.Print("If the NSID field is set to FFFFFFFFh, then the controller should fail the command with a status code of Invalid Field in Command")
        if self.NsSupported:
            self.Print ("Namespace Management supported: Yes")
        else:
            self.Print ("Namespace Management supported: No") 
            self.Print ("Skip")            
        if self.NsSupported:
            CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x12 --namespace-id=0xFFFFFFFF 2>&1 > /dev/null"%self.dev_port
            self.Print("Issue CMD with nsid=0xFFFFFFFF: %s"%CMD)
            mStr, sc = self.shell_cmd_with_sc(CMD)
            self.Print("Return status: %s"%mStr)
            self.Print("Check if status is Invalid Field(0x2)")
            if sc==2:
                self.Print("Pass", "p") 
            else:
                self.Print("Fail", "f")
                ret_code = 1            
            
        return ret_code

    SubCase11TimeOut = 3000
    SubCase11Desc = "Verify invalid CNS" 
    SubCase11KeyWord = "https://jira.siliconmotion.com.tw:8443/browse/VCTDEPT-840"
    def SubCase11(self): 
        ret_code = 0
        self.Print("Current taget version for NVMe: %s"%self.specVersion)
        mandatoryCNSlist = [0x0, 0x1, 0x2, 0x3]
        if self.specVersion=="1.3c":
            optionalCNSlist = [0x10, 0x11, 0x12, 0x13, 0x14, 0x15]
        else: # 1.4 if not 1.3c
            optionalCNSlist = [0x4, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17]    
        
        invalidCNSlist = range(0, 0x100) # 0x14 to 0xFF
        invalidCNSlist = [item for item in invalidCNSlist if item not in mandatoryCNSlist] # remove mandatoryCNSlist
        invalidCNSlist = [item for item in invalidCNSlist if item not in optionalCNSlist] # remove optionalCNSlist
        
        self.Print("Issue identify command with invalidCNSlist, expected status is Invalid Field(0x2)")
        #self.Print("invalidCNSlist: %s"%map(lambda x: "0x%X"%x, invalidCNSlist)) 
        mStr = ""
        self.Print("invalidCNSlist:")
        self.SetPrintOffset(4)
        tens = 0
        for mCNS in invalidCNSlist:  
            if mCNS==0xEF:
                pass
            curr_tens =mCNS/16
            if tens!=curr_tens:
                self.Print(mStr)
                tens=curr_tens
                mStr = ""
            mStr += "0x%X "%mCNS
        if mStr!=0:
            self.Print(mStr)    
        self.SetPrintOffset(0) 
       
        for mCNS in invalidCNSlist:
            CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=%s 2>&1"%(self.dev_port, mCNS)
            mstr, sc = self.shell_cmd_with_sc(CMD)
            if sc == 0x2:
                self.Print("CNS: 0x%X, status code: %s, Pass"%(mCNS, sc), "p") 
            else:
                self.Print("CNS: 0x%X, status code: %s, Fail"%(mCNS, sc), "f")
                ret_code = 1 
        return ret_code
                
    # </sub item scripts>    
if __name__ == "__main__":
    DUT = SMI_IdentifyCommand(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 
    
    
    
    
    
