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
import os

# Import VCT modules
from lib_vct.NVME import NVME
import SMI_AsynchronousEventRequest

class SMI_Telemetry(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_Telemetry.py"
    Author = "Sam Chan"
    Version = "20210525"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>



    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def GetPS(self):
        return int(self.get_feature(2)[-1:])

    def testBlockAreas(self, ID):
        ret=0
        self.Print ("Get log page: %s"%ID)
        self.Print (""    )
        mLOG=self.get_log_passthru(ID, 512, 1, 1)
    
        if not len(mLOG) == 512:
            self.Print("Fail to get log", "f")
            ret=1 
        else:
            self.Print ("check if (Data Area 1 Last Block <= Data Area 2 Last Block<= Data Area 3 Last Block) or not")
            
            LastBlock1=int(mLOG[9]+mLOG[8], 16)
            LastBlock2=int(mLOG[11]+mLOG[10], 16)
            LastBlock3=int(mLOG[13]+mLOG[12], 16)
            '''
            #--- TODO test ----
            LastBlock1=2
            LastBlock2=2
            LastBlock3=1
            '''
            self.Print ("1 Last Block: %s, 2 Last Block: %s, 3 Last Block: %s" %(LastBlock1, LastBlock2, LastBlock3))
            if (LastBlock1<=LastBlock2) and (LastBlock2<=LastBlock3):
                self.Print("PASS", "p")
            else:
                self.Print("Fail", "f")
                ret=1  
            
            #-----------------------------------------------------------------------------------
            self.Print ("")
            self.Print ("check Data Areas")
            
            if LastBlock1==0:
                self.Print ("Data Area 1: No Data")
            else:
                self.Print ("Data Area 1: from block %s to block %s"%("0", LastBlock1))
                
            if LastBlock2==LastBlock1:
                self.Print ("Data Area 2: No Data")
            else:
                self.Print ("Data Area 2: from block %s to block %s"%(LastBlock1+1, LastBlock2))
                
            if LastBlock3==LastBlock2:
                self.Print ("Data Area 3: No Data")
            else:
                self.Print ("Data Area 3: from block %s to block %s"%(LastBlock2+1, LastBlock3)  )
            #-----------------------------------------------------------------------------------
            self.Print ("")
            self.Print ("-------- Read Data Areas 1 --------")
            if LastBlock1==0:
                self.Print ("Data Area 1: No Data"    )
            else:
                self.Print ("Data Area 1: from block %s to block %s"%("0", LastBlock1))
                for i in range(1, LastBlock1+1):
                    LOG=self.get_log_passthru(7, 512, 0, 0, 512*i)
                    self.Print ("Data Area 1, block %s"%i)
                    print LOG

            self.Print ("")
            self.Print ("-------- Read Data Areas 2 --------")
            if LastBlock2==LastBlock1:
                self.Print ("Data Area 2: No Data"    )
            else:
                self.Print ("Data Area 2: from block %s to block %s"%(LastBlock1+1, LastBlock2))
                for i in range(LastBlock1+1, LastBlock2+1):
                    LOG=self.get_log_passthru(7, 512, 0, 0, 512*i)
                    self.Print ("Data Area 2, block %s"%i)
                    print LOG

            self.Print ("")
            self.Print ("-------- Read Data Areas 3 --------")
            if LastBlock3==LastBlock2:
                self.Print ("Data Area 3: No Data"    )
            else:
                self.Print ("Data Area 3: from block %s to block %s"%(LastBlock2+1, LastBlock3)  )
                for i in range(LastBlock2+1, LastBlock3+1):
                    LOG=self.get_log_passthru(7, 512, 0, 0, 512*i)
                    self.Print ("Data Area 3, block %s"%i)
                    print LOG
        return True if ret==0 else False
    
    def getReasonIdentifier(self, ID):
        mLOG=self.get_log_passthru(ID, 512, 1, 0)
        rStr=""
        for byte in range(384, 512):
            rStr=rStr+mLOG[byte]
        return rStr              
    
    def SaveToBinary(self, ID, fileNameAppend=""):
        SavedFileNameList = []
        filePath = "./temp/Telemetry_id%s_block0%s.bin"%(ID, fileNameAppend)        
        # save header             
        mLOG=self.get_log_passthru(ID, 512, 0, 0, ReturnType=2)
        if not os.path.exists(filePath):
            f = open(filePath, "w")
            f.close()           
        self.writeBinaryFileFromList(filePath, mLOG)   
        SavedFileNameList.append(filePath)
        rtHeader = mLOG
        # save data     
        LastBlock1=(mLOG[9]<<8)+mLOG[8]
        LastBlock2=(mLOG[11]<<8)+mLOG[10]
        LastBlock3=(mLOG[13]<<8)+mLOG[12]
        for i in range(1, LastBlock1+1):
            mLOG=self.get_log_passthru(ID, 512, 0, 0, 512*i, ReturnType=2)
            filePath = "./temp/Telemetry_id%s_block%s%s.bin"%(ID, i, fileNameAppend)
            if not os.path.exists(filePath):
                f = open(filePath, "w")
                f.close()           
            self.writeBinaryFileFromList(filePath, mLOG)   
            SavedFileNameList.append(filePath)
    
        for i in range(LastBlock1+1, LastBlock2+1):
            mLOG=self.get_log_passthru(ID, 512, 0, 0, 512*i, ReturnType=2)
            filePath = "./temp/Telemetry_id%s_block%s%s.bin"%(ID, i, fileNameAppend)
            if not os.path.exists(filePath):
                f = open(filePath, "w")
                f.close()           
            self.writeBinaryFileFromList(filePath, mLOG)   
            SavedFileNameList.append(filePath)    
            
        for i in range(LastBlock2+1, LastBlock3+1):
            mLOG=self.get_log_passthru(ID, 512, 0, 0, 512*i, ReturnType=2)
            filePath = "./temp/Telemetry_id%s_block%s%s.bin"%(ID, i, fileNameAppend)
            if not os.path.exists(filePath):
                f = open(filePath, "w")
                f.close()           
            self.writeBinaryFileFromList(filePath, mLOG)   
            SavedFileNameList.append(filePath)
        return SavedFileNameList, rtHeader
    
    def PrintFWlog(self):
        CMD = "nvme fw-log %s"%self.dev_port
        mStr = self.shell_cmd(CMD)
        self.Print(mStr, "d", 4)
    
    def FW_DownloadAndCommit(self, CA):
        self.Print("Current FW log", "b")
        self.PrintFWlog()
        
        self.Print("")
        self.Print("Issue CMD to download FW(%s)"%self.FWimage, "b")
        CMD = "nvme fw-download /dev/nvme0 --fw=%s 2>&1"%self.FWimage
        mStr, sc = self.shell_cmd_with_sc(CMD)
        self.Print(mStr, "d" if sc==0 else "f", 4)
        if sc!=0:
            self.Print(mStr, "f")
            return False

        self.Print("")
        self.Print("Current FW log", "b")
        self.PrintFWlog()        
        
        self.Print("")
        self.Print("Issue fw-commit CMD to commit to slot2 with Commit Action (CA) = %s"%CA, "b")
        CMD = "nvme fw-commit %s --slot=2 --action=%s"%(self.dev_port, CA)
        mStr, sc = self.shell_cmd_with_sc(CMD)# TODO
        self.Print(mStr, "d" if sc==0 else "f", 4)
        if sc!=0:
            self.Print(mStr, "f")
            return False        
                
        self.Print("")
        self.Print("Current FW log", "b")
        self.PrintFWlog()  
        return True
            
    def VerifyTelemetryLogAfterFWcommit(self, CA):
        self.InitFolder("./temp")
        self.Print ("1)-- Save current Telemetry log 0x7 to binary files", "b")
        SavedFileNameList_before, rtHeader = self.SaveToBinary(ID= 7, fileNameAppend = "_beforePOR")
        if len(SavedFileNameList_before)==0:
            self.Print("Fail", "f")
            return False   
        self.Print ("Below files was been created")
        for mList in SavedFileNameList_before:
            self.Print(mList, "d", 4)     
        
        self.Print ("")
        self.Print ("2)-- Commit FW", "b")
        self.SetPrintOffset(4)
        if not self.FW_DownloadAndCommit(CA):
            return False  
        self.SetPrintOffset(0)
        
        self.Print ("")
        self.Print ("3)-- Save current Telemetry log 0x7 to binary files", "b")
        SavedFileNameList_after, rtHeader = self.SaveToBinary(ID= 7, fileNameAppend = "_afterPOR")
        if len(SavedFileNameList_after)==0:
            self.Print("Fail", "f")
            return False    
        self.Print ("Below files was been created")
        self.SetPrintOffset(4)
        for mList in SavedFileNameList_after:
            self.Print(mList)
        self.SetPrintOffset(0)        
        
        self.Print ("")
        if len(SavedFileNameList_after)!=len(SavedFileNameList_before):
            self.Print("Fail, number of created file is not equal! ", "f")
            return False  
        
        self.Print ("")        
        self.Print ("4)-- Compare all log data ..",  "b")
        for before, after in zip(SavedFileNameList_before, SavedFileNameList_after):
            if self.isFileTheSame(before, after)==None:
                self.Print("Pass: %s, %s"%(before, after), "p")        
            else:
                self.Print("Fail: %s, %s"%(before, after), "f")      
                CMD = "hexdump %s"%(before)
                self.Print( "Do shell command to hexdump file: %s"%before) 
                aa= self.shell_cmd(CMD)
                self.SetPrintOffset(4)
                self.Print(aa)
                self.SetPrintOffset(0)  
                CMD = "hexdump %s"%(after)
                self.Print( "Do shell command to hexdump file: %s"%after) 
                aa= self.shell_cmd(CMD)
                self.SetPrintOffset(4)
                self.Print(aa)
                self.SetPrintOffset(0)                  
   
                return False
        return True        
        
            
    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    def __init__(self, argv):
        # initial parent class
        self.SetDynamicArgs(optionName="f", optionNameFull="FWimage", \
                            helpMsg="FW image file in current directory for FFU test, e.x. -f 2265_ISP_Package.bin"\
                            , argType=str, default="FW_Image.bin")        
        
        super(SMI_Telemetry, self).__init__(argv)
        
        self.FWimage = self.GetDynamicArgs(0)
        
        
        self.NSSRSupport=True if self.CR.CAP.NSSRS.int==1 else False
        self.ResetItem=[]
        self.ResetItem.append(["NVME reset", self.nvme_reset])
        self.ResetItem.append(["Hot reset", self.hot_reset])
        self.ResetItem.append(["Link reset", self.link_reset])
        if self.NSSRSupport:
            self.ResetItem.append(["NVM Subsystem Reset", self.subsystem_reset])        
        
        self.SupportTelemetry=True if self.IdCtrl.LPA.bit(3)!="0" else False
        # Create Telemetry Host-Initiated Data bit = 0
        self.LOG07_0=self.get_log_passthru(7, 512, 0, 0)
        # Create Telemetry Host-Initiated Data bit = 1
        self.LOG07_1=self.get_log_passthru(7, 512, 0, 1)
        # Create Telemetry Host-Initiated Data bit = 0
        self.LOG08_0=self.get_log_passthru(8, 512, 0, 0)
        # Create Telemetry Host-Initiated Data bit = 1
        self.LOG08_1=self.get_log_passthru(8, 512, 0, 1)  
        
        self.LOG07=self.LOG07_0
        self.LOG08=self.LOG08_0
          
        self.AsyncNVME = SMI_AsynchronousEventRequest.SMI_AsynchronousEventRequest(sys.argv )
        
    # override PreTest()
    def PreTest(self):
        if DUT.SupportTelemetry:
            self.Print( "Controller support telemetry in Log Page Attributes (LPA)", "p")
        else:
            self.Print( "Controller do not support telemetry in Log Page Attributes (LPA)", "w")
        return DUT.SupportTelemetry

    SubCase1TimeOut = 60
    SubCase1Desc = "Test Data Blocks are 512 bytes in size or not, Log ID=07"           
    # <override sub item scripts>
    def SubCase1(self):
        ret_code = 0
        self.Print ("Test if get log page command is not a multiple of 512 bytes for this log, then the controller shall return an error of Invalid Field in Command")
        
        for DataBlock in range(12, 513, 50):
            self.Print ("Send Get Log Page command for %s byte data of Data Blocks "%DataBlock)
            
            mStr, SC = self.shell_cmd_with_sc("nvme get-log %s --log-id=0x7 --log-len=%s 2>&1"%(self.dev, DataBlock))
            self.Print(mStr)
        
            # if (not a multiple of 512 bytes and get get log fail) or (multiple of 512 bytes and get log success), then pass the test
            if (SC!=0 and DataBlock!=512) or (SC==0 and DataBlock==512):
                self.Print("PASS", "p")     
            else:
                self.Print("Fail", "f")
                ret_code=1       
        return ret_code
    
    
    SubCase2TimeOut = 60
    SubCase2Desc = "Test Command Dword 10 -- Log Specific Field, Log ID=07"    
    def SubCase2(self):
        ret_code = 0
        self.Print ("check Command Dword 10 -- Log Specific Field for 'Create Telemetry Host-Initiated Data'")
        self.Print ("Verify if get log command with Log Specific Field=0 and Log Specific Field=1 are successed")
        if len(self.LOG07_0) == 512 and len(self.LOG07_1) == 512 :
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1 
            
        return ret_code
    
    SubCase3TimeOut = 120
    SubCase3Desc = "Test Log Identifier in log byte0, Log ID=07"        
    def SubCase3(self):
        ret_code = 0        
        
        # get 512 byte log data where RAE=0, LSP=0
        self.LOG07=self.get_log_passthru(7, 512, 1, 0)
        self.LOG08=self.get_log_passthru(8, 512, 1, 0)
        
        
        
        self.Print (""   )
        self.Print ("Check Log Identifier in log byte0")
        
        LogId=self.LOG07[0]
        
        self.Print ("Log Identifier: %s"%LogId)
        if LogId=="07":
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1 
        return ret_code  

    SubCase4TimeOut = 60
    SubCase4Desc = "Test if IEEE OUI Identifier = identify.IEEE, Log ID=07"    
    def SubCase4(self):
        ret_code = 0          
        self.Print ("Check if IEEE OUI Identifier = identify.IEEE or not")
        IEEE=int((self.LOG07[7]+self.LOG07[6]+self.LOG07[5]),16)
        self.Print ("IEEE: %s, identify.IEEE: %s" %(IEEE, self.IdCtrl.IEEE.int))
        
        if IEEE==self.IdCtrl.IEEE.int:
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1       
        return ret_code
    

    SubCase5TimeOut = 60
    SubCase5Desc = "Test if Data Area 1 Last Block <= 2 Last Block<= 3 Last Block, Log ID=07"        
    def SubCase5(self):
        ret_code = 0    
        self.Print ("check if (Telemetry Host-Initiated Data Area 1 Last Block <= 2 Last Block<= 3 Last Block) or not"      )
        LastBlock1=int(self.LOG07[9]+self.LOG07[8], 16)
        LastBlock2=int(self.LOG07[11]+self.LOG07[10], 16)
        LastBlock3=int(self.LOG07[13]+self.LOG07[12], 16)
        self.Print ("1 Last Block: %s, 2 Last Block: %s, 3 Last Block: %s" %(LastBlock1, LastBlock2, LastBlock3))
        if (LastBlock1<=LastBlock2) and (LastBlock2<=LastBlock3):
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1       
        return ret_code

    SubCase6TimeOut = 60
    SubCase6Desc = "Test Telemetry Controller-Initiated Data Available"    
    def SubCase6(self):
        ret_code = 0          
        self.Print ("check if Telemetry Controller-Initiated Data Available in log ID 07h = Telemetry Controller-Initiated Data Available in log ID 08h  or not")
        self.Print ("TCIDA in 0x7h: %s, TCIDA in 0x8h: %s" %(self.LOG07[382], self.LOG08[382])      )
        if self.LOG07[382]==self.LOG08[382]:
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1         
        return ret_code

    SubCase7TimeOut = 60
    SubCase7Desc = "Test Telemetry Controller-Initiated Data Generation Number"
    def SubCase7(self):
        ret_code = 0          
        self.Print ("check if Telemetry Controller-Initiated Data Generation Number in log ID 07h = Telemetry Controller-Initiated Data Generation Number in log ID 08h  or not")
        self.Print ("TCIDGN in 0x7h: %s, TCIDGN in 0x8h: %s" %(self.LOG07[383], self.LOG08[383]))
        if self.LOG07[383]==self.LOG08[383]:
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1       
        return ret_code

    SubCase8TimeOut = 120
    SubCase8Desc = "Test Data Blocks are 512 bytes in size or not, Log ID=08"       
    def SubCase8(self):
        ret_code = 0          
        self.Print ("Test if get log page command is not a multiple of 512 bytes for this log, then the controller shall return an error of Invalid Field in Command")
        for DataBlock in range(12, 513, 50):
            self.Print ("Send Get Log Page command for %s byte datas of Data Blocks "%DataBlock)
            
            mStr, SC = self.shell_cmd_with_sc("nvme get-log %s --log-id=0x8 --log-len=%s 2>&1"%(self.dev, DataBlock))
            self.Print(mStr)
        
            # if (not a multiple of 512 bytes and get get log fail) or (multiple of 512 bytes and get log success), then pass the test
            if (SC!=0 and DataBlock!=512) or (SC==0 and DataBlock==512):
                self.Print("PASS", "p")     
            else:
                self.Print("Fail", "f")
                ret_code=1               
        return ret_code

    SubCase9TimeOut = 60
    SubCase9Desc = "Test Log Identifier in log byte0, Log ID=08"    
    def SubCase9(self):
        ret_code = 0          
        self.Print ("Check Log Identifier in log byte0"      )

        LogId=self.LOG08[0]
        
        self.Print ("Log Identifier: %s"%LogId)
        if LogId=="08":
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1 
        return ret_code

    SubCase10TimeOut = 60
    SubCase10Desc = "Test if IEEE OUI Identifier = identify.IEEE, Log ID=08"   
    def SubCase10(self):
        ret_code = 0          
        self.Print ("Check if IEEE OUI Identifier = identify.IEEE or not")
        IEEE=int((self.LOG08[7]+self.LOG08[6]+self.LOG08[5]),16)
        self.Print ("IEEE: %s, identify.IEEE: %s" %(IEEE, self.IdCtrl.IEEE.int))
        if IEEE==self.IdCtrl.IEEE.int:
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1       
        return ret_code

    SubCase11TimeOut = 60
    SubCase11Desc = "Test if Data Area 1 Last Block <= 2 Last Block<= 3 Last Block, Log ID=08"   
    def SubCase11(self):
        ret_code = 0          
        self.Print ("check if (Telemetry Controller-Initiated Data Area 1 Last Block <= 2 Last Block<= 3 Last Block) or not")
        LastBlock1=int(self.LOG08[9]+self.LOG08[8], 16)
        LastBlock2=int(self.LOG08[11]+self.LOG08[10], 16)
        LastBlock3=int(self.LOG08[13]+self.LOG08[12], 16)
        self.Print ("1 Last Block: %s, 2 Last Block: %s, 3 Last Block: %s" %(LastBlock1, LastBlock2, LastBlock3))
        if (LastBlock1<=LastBlock2) and (LastBlock2<=LastBlock3):
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1       
        return ret_code
    
    SubCase12TimeOut = 60
    SubCase12Desc = "Test TCIDA value is persistent across power states and reset or not"    
    def SubCase12(self):
        ret_code = 0          
        self.Print ("check if Telemetry Controller-Initiated Data Available(TCIDA) value is persistent across power states and reset or not")
        TCIDA_old=self.LOG08[383]
        self.Print ("TCIDA: %s" %TCIDA_old)
        self.Print ("-- start test TCIDA for power state  --")
        NPSS=self.IdCtrl.NPSS.int
        self.Print ("NPSS: %s"%NPSS)
             
        NPSS=self.IdCtrl.NPSS.int
            
        for i in range(NPSS+1):
            self.set_feature(2, i)
            self.Print ("set power state = %s"%i)
            PS=self.GetPS()
            # verify set_feature successfull
            if PS!=i:
                self.Print("Set power state error! ", "f")
                ret_code=1
                break
                    
            # reload     
            self.LOG07=self.get_log_passthru(7, 512, 1, 0)
            self.LOG08=self.get_log_passthru(8, 512, 1, 0)
                
            self.Print ("TCIDA in log 0x7= %s"%self.LOG07[383])
            self.Print ("TCIDA in log 0x8= %s"%self.LOG08[383])
            if (TCIDA_old==self.LOG08[383]) and (TCIDA_old==self.LOG07[383]):
                self.Print("PASS", "p")    
            else:
                self.Print("Fail", "f")
                ret_code=1
                
        self.Print ("-- start test TCIDA for Controller Level Reset --"        )
        for Item in self.ResetItem:
            
            self.Print ( Item[0] )
        
            # trigger reset
            Item[1]()
            
            # reload      
            self.LOG07=self.get_log_passthru(7, 512, 1, 0)
            self.LOG08=self.get_log_passthru(8, 512, 1, 0)
                        
            self.Print ("TCIDA in log 0x7= %s"%self.LOG07[383])
            self.Print ("TCIDA in log 0x8= %s"%self.LOG08[383])
            if (TCIDA_old==self.LOG08[383]) and (TCIDA_old==self.LOG07[383]):
                self.Print("PASS", "p")    
            else:
                self.Print("Fail", "f")
                ret_code=1               
        return ret_code




    
    # </sub item scripts>
    
    SubCase13TimeOut = 600
    SubCase13Desc = "Test Telemetry Data Collection Examples (Informative)"      
    def SubCase13(self):
        ret_code=0
        self.Print ("The host proceeds with a host-initiated data collection ")
        self.Print ("by submitting the Get Log Page command for the Telemetry Host-Initiated log page with the Create Telemetry Host-Initiated Data bit set to '1'.")
        self.Print ("Check if get log page command success")
        
        LOG07=self.get_log_passthru(7, 512, 0, 1)
        if len(LOG07) == 512:
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1  

        self.Print ("")
        self.Print ("Check Block Areas for log 0x7 ")
        if self.testBlockAreas(0x7):
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1         
        
        self.Print ("")
        self.Print ("Get Reason Identifier ")
        self.Print ("Reason Identifier: %s"%self.getReasonIdentifier(0x7)            )
            
                   
        return ret_code

    SubCase14TimeOut = 600
    SubCase14Desc = "Test Async event with Telemetry Controller-Initiated Log(trigger the log was required)"        
    def SubCase14(self):
        ret_code=0    
        self.Print ("Async event test and controller-initiated telemetry test(log page 0x8)" )
        self.Print (""    )
        # save Telemetry Controller-Initiated Data Generation Number
        LOG08=self.get_log_passthru(8, 512, 0, 0)
        LOG08_383_old= LOG08[383]
        
        self.Print ("To receive notification that controller-initiated data is available,")
        self.Print ("the host enables Telemetry Log Notices using the Asynchronous Event Configuration feature.")
        
        self.shell_cmd(" nvme set-feature %s -f 0xB -v 0x3fff"%(self.dev), 0.5)   
        self.Print(  "set Asynchronous Event Configuration = 0xff to enable all the events can be reported to the host: done ", 'p')
        
        # assign a thread for event request cmd
        self.Print ("Assign a thread for event request cmd")
        async_result = self.AsyncNVME.thread_asynchronous_event_request_cmd()
        
        
        # wait thread finish and timeout=2s
        self.Print ("wait for controller signals that controller-initiated telemetry data is available(time out = 60s)")
        self.Print ("please do something to make the controller-initiated telemetry data available in 60s")
        async_result.join(60)
        
                
        # if time out
        if async_result.is_alive():
            self.Print ("async_result.is_alive=true")
            AsyncEventCmdTimeout=1
        else:        
            # get return code from Asynchronous Event Request command        
            try:
                mThreadStr=self.AsyncNVME.que.get(timeout=1)
            except Exception as error:
                self.AsyncNVME.Print("Can't get return code from Asynchronous Event Request command", "f")
                AsyncEventCmdTimeout=1
            self.AsyncNVME.Print("return string from request command : %s" %(mThreadStr), "t")   
            
            mstr="0" 
            try:
                self.Print ("Return status: %s"%mThreadStr)
                mStr="NVMe command result:(.+)" 
                if re.search(mStr, mThreadStr):
                    mstrs=re.search(mStr, mThreadStr).group(1)
                    self.Print ("Completion Queue Entry Dword 0: %s" %(mstrs)    )
                    self.Print ("Check Dword 0")
                    if mstrs=="00080202":
                        self.AsyncNVME.Print("PASS", "p")
                    else:
                        self.AsyncNVME.Print("Fail", "f")
                        AsyncEventCmdFail=1   
                else:
                    AsyncEventCmdTimeout=1          
            except ValueError:
                #when return 'passthru: Interrupted system call'
                self.Print ("return string from request command : %s" %(mThreadStr))
                AsyncEventCmdTimeout=1
            #clear Asynchronous Event Request command
            self.nvme_reset()
        
        # if can't receive async event         
        if AsyncEventCmdTimeout==1:
            self.Print ("")
            self.AsyncNVME.Print("Can't receive the return code of Asynchronous Event Request command", "w")
            self.AsyncNVME.Print("exit async test and controller-initiated telemetry test", "w")
            ret_code=255
        else:
            self.Print ("")
            self.Print ("Check if Telemetry Controller-Initiated Data Available in log 0x7 = 1")
            LOG07=self.get_log_passthru(7, 512, 1, 0)
            if LOG07[382]=="01":
                self.Print("PASS", "p")
            else:
                self.Print("Fail", "f")
                ret_code=1  
                
            self.Print (""      )
            self.Print ("Check if Telemetry Controller-Initiated Data Available in log 0x8 = 1")
            LOG08=self.get_log_passthru(8, 512, 1, 0)
            if LOG08[382]=="01":
                self.Print("PASS", "p")         
            else:
                self.Print("Fail", "f")      
                ret_code=1  
        
            self.Print ("")
            self.Print ("Teset Block Areas for 0x8 ")
            if self.testBlockAreas(0x8):
                self.Print("PASS", "p")
            else:
                self.Print("Fail", "f")
                ret_code=1    

            self.Print ("")
            self.Print ("Get Reason Identifier ")
            self.Print ("Reason Identifier: %s"%self.getReasonIdentifier(0x8)            )
                
            self.Print (""    )
            self.Print ("Check if Telemetry Controller-Initiated Data Available in log 0x8 = 0 after get log command with RAE=0")
            LOG08=self.get_log_passthru(8, 512, 0, 0)
            if LOG08[382]=="00":
                self.Print("PASS", "p")         
            else:
                self.Print("Fail", "f")      
                ret_code=1          
            
            self.Print (""    )
            self.Print ("Check if Telemetry Controller-Initiated Data Generation Number was changed")
            self.Print ("before: %s"%LOG08_383_old)
            self.Print ("after   : %s"%LOG08[383])
            if not LOG08_383_old==LOG08[383]:
                self.Print("PASS", "p")        
            else:
                self.Print("Fail", "f")      
                ret_code=1  

        return ret_code    

    SubCase15TimeOut = 600
    SubCase15Desc = "Check Telemtry Log Across PowerState"        
    def SubCase15(self):
        ret_code=0
        self.InitFolder("./temp")
        self.Print ("Save current Telemetry log 0x8 to binary files")
        SavedFileNameList_before, rtHeader = self.SaveToBinary(ID= 8, fileNameAppend = "_beforePOR")
        if len(SavedFileNameList_before)==0:
            self.Print("Fail", "f")
            return 1     
        self.Print ("Below files was been created")
        self.SetPrintOffset(4)
        for mList in SavedFileNameList_before:
            self.Print(mList)
        self.SetPrintOffset(0)
        # Telemetry Controller-Initiated Data Generation Number
        GNumOld = rtHeader[383]        
        self.Print("Current Telemetry Controller-Initiated Data Generation Number: %s"%GNumOld)
        
        self.Print ("")
        self.Print ("Do POR")
        if not self.por_reset():
            return 1
        
        
        self.Print ("")
        self.Print ("Save current Telemetry log 0x8 to binary files")
        SavedFileNameList_after, rtHeader = self.SaveToBinary(ID= 8, fileNameAppend = "_afterPOR")
        if len(SavedFileNameList_after)==0:
            self.Print("Fail", "f")
            return 1     
        self.Print ("Below files was been created")
        self.SetPrintOffset(4)
        for mList in SavedFileNameList_after:
            self.Print(mList)
        self.SetPrintOffset(0)        
        # Telemetry Controller-Initiated Data Generation Number
        GNumNew = rtHeader[383]        
        self.Print("Current Telemetry Controller-Initiated Data Generation Number: %s"%GNumNew)
        self.Print("")
        self.Print("Check if Telemetry Controller-Initiated Data Generation Number has not changed")
        if GNumNew==GNumOld:
            self.Print("Pass", "p")
        else:
            self.Print("Warnning, Generation Number has changed"\
                       "controller may generate new Controller-Initiated Data when doing POR", "w")
            return 255
                
        self.Print ("")
        if len(SavedFileNameList_after)!=len(SavedFileNameList_before):
            self.Print("Fail, number of created file is not equal! ", "f")
            return 1   
                
        self.Print ("Compare all log data ..")
        for before, after in zip(SavedFileNameList_before, SavedFileNameList_after):
            if self.isFileTheSame(before, after)==None:
                self.Print("Pass: %s, %s"%(before, after), "p")        
            else:
                self.Print("Fail: %s, %s"%(before, after), "f")      
                CMD = "hexdump %s"%(before)
                self.Print( "Do shell command to hexdump file: %s"%before) 
                aa= self.shell_cmd(CMD)
                self.SetPrintOffset(4)
                self.Print(aa)
                self.SetPrintOffset(0)  
                CMD = "hexdump %s"%(after)
                self.Print( "Do shell command to hexdump file: %s"%after) 
                aa= self.shell_cmd(CMD)
                self.SetPrintOffset(4)
                self.Print(aa)
                self.SetPrintOffset(0)                  
   
                ret_code=1 
        return ret_code     


    SubCase16TimeOut = 600
    SubCase16Desc = "Compare Telemetry log after Firmware Commit(CA0~3)"        
    def SubCase16(self):
        ret_code=0
        NumOfFWslot = int(self.IdCtrl.FRMW.bit(3, 1), 2)
        self.Print("Number of firmware slots: %s"%NumOfFWslot)
        self.Print("FWimage: %s"%self.FWimage)
        if not self.isfileExist(self.FWimage):
            self.Print("FWimage( %s ) not exist in current directory, please check or assign FWimage name with -f option"%self.FWimage, "w")
            self.Print("For more informat , run 'python SMI_Telemetry.py'", "w")
            return 255

        for CA in range(0,4):
            self.Print("")
            # print prefix
            self.PrintLoop = CA            
            self.Print("Compare Telemetry log after Firmware Commit with Commit Action (CA) = %s"%CA, "b")
            if not self.VerifyTelemetryLogAfterFWcommit(CA):
                return 1
        
        self.PrintLoop = ""
        self.Print("")
        self.Print("")
        self.Print("")
        self.Print("")
        
        
        
        return ret_code  
        
        
        
        
    
if __name__ == "__main__":
    DUT = SMI_Telemetry(sys.argv ) 
    DUT.RunScript()
    DUT.Finish()
    
    
    
    
    
