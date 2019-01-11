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

# Import VCT modules
from lib_vct.NVME import NVME
import SMI_AsynchronousEventRequest

class SMI_TelemetryExample(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_TelemetryExample.py"
    Author = "Sam Chan"
    Version = "20181211"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    SubCase1TimeOut = 60
    SubCase1Desc = "Test host-initiated data collection"    
    
    SubCase2TimeOut = 180
    SubCase2Desc = "Test Async event with Telemetry Controller-Initiated Log"


    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
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
            
            LastBlock1=int(mLOG[9]+mLOG[8])
            LastBlock2=int(mLOG[11]+mLOG[10])
            LastBlock3=int(mLOG[13]+mLOG[12])
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
    
    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    aaabbb=123456
    def __init__(self, argv):
        # initial parent class
        super(SMI_TelemetryExample, self).__init__(argv)        
        
        self.AsyncNVME = SMI_AsynchronousEventRequest.SMI_AsynchronousEventRequest(sys.argv )
        self.SupportTelemetry=True if self.IdCtrl.LPA.bit(3)!="0" else False
    # override PreTest()
    def PreTest(self):
        if DUT.SupportTelemetry:
            self.Print( "Controller support telemetry in Log Page Attributes (LPA)", "p")
        else:
            self.Print( "Controller do not support telemetry in Log Page Attributes (LPA)", "w")
        return DUT.SupportTelemetry
        
    # <sub item scripts>
    def SubCase1(self):
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
        self.Print ("Teset Block Areas for 0x7 ")
        if self.testBlockAreas(0x7):
            self.Print("PASS", "p")
        else:
            self.Print("Fail", "f")
            ret_code=1         
        
        self.Print ("")
        self.Print ("Get Reason Identifier ")
        self.Print ("Reason Identifier: %s"%self.getReasonIdentifier(0x7)            )
            
                   
        return ret_code
    
    def SubCase2(self):
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
                    if mstrs=="00030202":
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

















        
    # </sub item scripts>
    
    
    
    
if __name__ == "__main__":
    DUT = SMI_TelemetryExample(sys.argv ) 
    DUT.RunScript()
    DUT.Finish()
    
    
    
    
    
