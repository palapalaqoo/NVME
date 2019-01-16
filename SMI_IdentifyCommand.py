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

# Import VCT modules
from lib_vct.NVME import NVME
from lib_vct.NVME import DevWakeUpAllTheTime

class SMI_IdentifyCommand(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_IdentifyCommand.py"
    Author = "Sam Chan"
    Version = "20190114"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    BuildInFile_CNS01_IdentifyControllerDataStructure = "./lib_vct/CSV/CNS01_IdentifyControllerDataStructure.csv"    
    UserInFile_CNS01_IdentifyControllerDataStructure = "./CSV/IdentifyFile.csv"  
    
    TypeInt=0x0
    TypeStr=0x1

    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    
    def GetValueFromUserFile(self, UserFile, idName):
        value=None
        for mItem in UserFile:
            if self.RemoveSpaces(mItem[0].upper()) == self.RemoveSpaces(idName.upper()):
                value=mItem[1]
                break
        return value    
    
    def GetIdentifyController(self):
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x1 2>&1"%self.dev
        # returnd data structure
        rTDS=self.shell_cmd(CMD)
        # format data structure to list 
        DS=self.AdminCMDDataStrucToListOrString(rTDS, 0)         
        
        return DS
    
    def GetCliCommandByBuileInFileName(self, BuileInFileName):
        if BuileInFileName==self.BuildInFile_CNS01_IdentifyControllerDataStructure:
            CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=0x1 2>&1"%self.dev
            
        return CMD     
    
    def PrintAlignString(self,S0, S1, S2, PF="default"):            
        mStr = "{:<8}\t{:<30}\t{:<30}".format(S0, S1, S2)
        if PF=="pass":
            self.Print( mStr , "p")        
        elif PF=="fail":
            self.Print( mStr , "f")      
        else:
            self.Print( mStr )      
    def CheckBuildInWithUserFiles(self, BuileInFileName, UserFileName):
    # BuileInFileName, BuileIn File Name
    # UserFileName,  user file name
        subRt=0
        self.Print("Check if file %s exist or not"%UserFileName)
        UserFile=self.ReadCSVFile(UserFileName)
        if UserFile==None:
            self.Print("Can't find file at %s, skip this test"%SMI_IdentifyCommand.IdentifyFile)
            return 255
        else:  
            self.Print("File %s exist"%UserFileName)  
            self.Print( "" )    
            self.Print( "Check if BuileInFile exist or not")
            BuileInFile = self.ReadCSVFile(BuileInFileName)
            if BuileInFile==None:
                self.Print( "BuileInFile is not exist(%s), quit !"%BuileInFileName,"f")
                return 1
            else:            
                self.Print( "BuileInFile exist")
                self.Print( "Issue identify command to get data structure")
                
                CMD = self.GetCliCommandByBuileInFileName(BuileInFileName)
                # returnd data structure
                rTDS=self.shell_cmd(CMD)
                # format data structure to list 
                DS=self.AdminCMDDataStrucToListOrString(rTDS, 0)            
                if DS==None:
                    self.Print( "Fail to get data structure, quit !","f")
                    return 1
                else:
                    self.Print( "Success to get data structure")
                    self.Print( "Start to check values")
                    self.Print("")
                    self.Print("----------------------------------------------------------------------")   
                    self.PrintAlignString("Name", "Controller", UserFileName)
                    self.Print("----------------------------------------------------------------------")   
                    for mItem in BuileInFile:
                        # if start char=# means it is a comment, and quit it
                        mStr="^#"
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
                            # value from user,  and format it
                            ValueU = self.GetValueFromUserFile(UserFile, Name)
                            ValueU = self.mFormatString(ValueU, mType)
                                
                            # check if value is the same from controller and user file    
                            if ValueU==None:                                
                                self.PrintAlignString(Name, ValueC, "N/A")
                            elif ValueU==ValueC:        
                                self.PrintAlignString(Name, ValueC, ValueU, "pass")                            
                            elif ValueU!=ValueC:      
                                self.PrintAlignString(Name, ValueC, ValueU, "fail")   
                                subRt=1
                    self.Print("----------------------------------------------------------------------")     
                    self.Print("Finish")
                    # end of for mItem in BuileInFile:    
                    return subRt                                          

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
                
    
    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def __init__(self, argv):
        # initial parent class
        super(SMI_IdentifyCommand, self).__init__(argv)
             
        
    # override
    def PreTest(self):   
  
        return True

            
            
    # <sub item scripts>
    SubCase1TimeOut = 60
    SubCase1Desc = "Test Identify Controller Data Structure"        
    SubCase1KeyWord = "Synch"
    def SubCase1(self):
        ret_code=0
        ret_code=self.CheckBuildInWithUserFiles(self.BuildInFile_CNS01_IdentifyControllerDataStructure, self.UserInFile_CNS01_IdentifyControllerDataStructure)
        
        return ret_code

    
    SubCase2TimeOut = 60
    SubCase2Desc = "Test Identify Controller Data Structure" 
    SubCase2KeyWord="The Timestamp field was initialized with a Timestamp value using a Set Features command."
    def SubCase2(self): 
        ret_code=0


        return ret_code
        
    SubCase3TimeOut = 60
    SubCase3Desc = "Test time exceeds 2^48"
    SubCase3KeyWord ="Timestamp field"
    def SubCase3(self): 
        ret_code=0
        self.Print ("If the sum of the Timestamp value set by the host and the elapsed time exceeds 2^48, the value returned should be reduced modulo 2^48 ")
        


        return ret_code






    # </sub item scripts>
    
    
    
    
if __name__ == "__main__":
    DUT = SMI_IdentifyCommand(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 
    
    
    
    
    
