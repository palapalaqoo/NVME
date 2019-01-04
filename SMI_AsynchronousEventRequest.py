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
import Queue

# Import VCT modules
from lib_vct.NVME import NVME

class SMI_AsynchronousEventRequest(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_AsynchronousEventRequest.py"
    Author = "Sam Chan"
    Version = "20181211"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    SubCase1TimeOut = 60
    SubCase1Desc = "Test Status Code - Command specific status values"    
    
    SubCase2TimeOut = 120
    SubCase2Desc = "Test Asynchronous Event Configuration-enable all the events"

    SubCase3TimeOut = 120
    SubCase3Desc = "Test Asynchronous Event Configuration-disable all the events"    

    SubCase4TimeOut = 60
    SubCase4Desc = "Check if the commands are aborted when the controller is reset"    

    
    que = Queue.Queue()

    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def asynchronous_event_request_cmd(self): 
        mstr =  self.shell_cmd(" nvme admin-passthru %s --opcode=0xC 2>&1"%(self.dev))   
        self.que.put(mstr)
        
    def thread_asynchronous_event_request_cmd(self):
        # return thread        
        t = threading.Thread(target = self.asynchronous_event_request_cmd)
        t.start()   
       
        return t     

    def trigger_error_event(self): 
        self.shell_cmd("  buf=$( nvme write-uncor %s -s 0 -n 1 -c 127 2>&1 >/dev/null )"%(self.dev))
 
        self.shell_cmd("  buf=$( nvme get-log %s --log-id=1 --log-len=64 2>&1 >/dev/null )"%(self.dev))
        self.shell_cmd("  buf=$( hexdump %s -n 512 2>&1 >/dev/null )"%(self.dev))
        self.shell_cmd("  buf=$( nvme get-log %s --log-id=1 --log-len=64 2>&1 >/dev/null )"%(self.dev))
        self.shell_cmd("  buf=$( hexdump %s -n 512 2>&1 >/dev/null )"%(self.dev))
        # clear write-uncor 
        self.shell_cmd("  buf=$(nvme write-zeroes %s -s 0 -c 127 2>&1 > /dev/null) "%(self.dev)) 
        
    def trigger_SMARTHealthStatus_event(self):              
        # get log page and set 'Retain Asynchronous Event(RAE) = 0' 
        self.shell_cmd(" buf=$(nvme admin-passthru %s --opcode=0x2 -r --cdw10=0x2 -l 16 2>&1 >/dev/null)"%(self.dev), 0.5)         
        # Set TMPTH to 60 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 0)
        self.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x14D"%(self.dev), 0.5) 
        # Set TMPTH to 10 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 1)
        self.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x11B"%(self.dev), 0.5) 
        # Set TMPTH to 60 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 0)
        self.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x14D"%(self.dev), 0.5) 
        # get log page and set 'Retain Asynchronous Event(RAE) = 0' 
        self.shell_cmd(" buf=$(nvme admin-passthru %s --opcode=0x2 -r --cdw10=0x2 -l 16 2>&1 >/dev/null)"%(self.dev), 0.5)     
        # Set TMPTH to 10 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 1)
        self.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x11B"%(self.dev), 0.5)  
        # Set TMPTH to 60 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 0)
        self.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x14D"%(self.dev), 0.5)          
    def trigger_Sanitize_event(self):            
        self.sanitize()
        self.sanitize()
    def trigger_FirmwareActivationStarting(self):         
        self.shell_cmd(" nvme set-feature %s -f 0xB -v 0x07ff"%(self.dev), 0.5)  
        self.shell_cmd(" buf=$(nvme admin-passthru %s --opcode=0x2 -r --cdw10=0x3 -l 16 2>&1 >/dev/null)"%(self.dev), 0.5)       
        self.shell_cmd("buf=$(nvme fw-activate %s --slot=1 --action=3)"%(self.dev), 0.5)  
        self.shell_cmd(" nvme set-feature %s -f 0xB -v 0x07ff"%(self.dev), 0.5)  
        self.shell_cmd(" buf=$(nvme admin-passthru %s --opcode=0x2 -r --cdw10=0x3 -l 16 2>&1 >/dev/null)"%(self.dev), 0.5)       
        self.shell_cmd("buf=$(nvme fw-activate %s --slot=1 --action=3)"%(self.dev), 0.5)  
    def trigger_FirmwareActivationStartingNoEvent(self):         
        self.shell_cmd(" nvme set-feature %s -f 0xB -v 0x0"%(self.dev), 0.5)  
        self.shell_cmd(" buf=$(nvme admin-passthru %s --opcode=0x2 -r --cdw10=0x3 -l 16 2>&1 >/dev/null)"%(self.dev), 0.5)        
        self.shell_cmd("buf=$(nvme fw-activate %s --slot=1 --action=3)"%(self.dev), 0.5)  
        self.shell_cmd(" nvme set-feature %s -f 0xB -v 0x0"%(self.dev), 0.5)  
        self.shell_cmd(" buf=$(nvme admin-passthru %s --opcode=0x2 -r --cdw10=0x3 -l 16 2>&1 >/dev/null)"%(self.dev), 0.5)      
        self.shell_cmd("buf=$(nvme fw-activate %s --slot=1 --action=3)"%(self.dev), 0.5)       
            
    def reset(self):
        self.nvme_reset()
        self.que.queue.clear()
        self.shell_cmd(" nvme set-feature %s -f 0xB -v 0x3fff"%(self.dev), 0.5)  
    
    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def __init__(self, argv):
        # initial parent class
        super(SMI_AsynchronousEventRequest, self).__init__(argv)
        
        
        # for  Check Asynchronous Event Configuration           
        # item[0]: message to print
        # item[1]: function to trigger event
        # item[0]: expected Completion Queue Entry Dword 0
        self.TestItem=[]
        self.TestItem.append(["Start to test error event(Read uncorrectable blocks)", self.trigger_error_event, "00010400"])
        self.TestItem.append(["Start to test smart/health status event(Over tempture)", self.trigger_SMARTHealthStatus_event, "00020101"])
        self.TestItem.append(["Start to test IO command event(Sanitize)", self.trigger_Sanitize_event, "00810106"])
        self.TestItem.append(["Start to test Notice(FirmwareActivationStarting)", self.trigger_FirmwareActivationStarting, "00030102"])

        # item[0]: message to print
        # item[1]: function to trigger event
        # item[0]: expected Completion Queue Entry Dword 0
        self.TestItemDisableReport=[]
        self.TestItemDisableReport.append(["Start to test smart/health status event(Over tempture)", self.trigger_SMARTHealthStatus_event, "00020101"])
        self.TestItemDisableReport.append(["Start to test IO command event(Sanitize)", self.trigger_Sanitize_event, "00810106"])
        self.TestItemDisableReport.append(["Start to test Notice(FirmwareActivationStarting)", self.trigger_FirmwareActivationStartingNoEvent, "00030102"])
        
        # Asynchronous Event Request Limit, 0's based
        self.AERL=self.IdCtrl.AERL.int     
        
        
           
    # <sub item scripts>
    def SubCase1(self):
        ret_code=0
        self.Print ("self.AERL: %s" %(self.AERL))
        self.Print ("Sending Asynchronous Event Request command for %s times.." %(self.AERL))
        self.reset()
        result_b=[]
        for i  in range(self.AERL+1):
            
            async_result = self.thread_asynchronous_event_request_cmd()
            result_b.append(async_result)
            
            # if is the last synchronous_event_request_cmd, it must receive the  "Asynchronous Event Request Limit Exceeded"
            if i==self.AERL:
                
                # wait thread finish and timeout=2s
                async_result.join(2)
                
                # if time out
                if async_result.is_alive():
                    self.Print("Error: can't receive the return code of Asynchronous Event Request command", "f")
                    ret_code=1
                    break
                
                # get return code from Asynchronous Event Request command        
                mThreadStr=self.que.get()       
                
                self.Print("return string from request command : %s" %(mThreadStr), "t")  
                
                # check the commands are aborted or not
                self.Print ("This is the last time ")
                self.Print ("and the return code is: %s" %(mThreadStr) )
                self.Print ("Check the return code is Asynchronous Event Request Limit Exceeded or not")
                if re.search("NVMe Status:ASYNC_LIMIT", mThreadStr):
                    self.Print("PASS", "p")
                else:
                    self.Print("Fail", "f")
                    ret_code=1            
        return ret_code
    def SubCase2(self):
        self.Print ("set Asynchronous Event Configuration = 0xff to enable all the events can be reported to the host ")
        self.reset()
        
        ret_code=0
        # loop for test items
        for Item in self.TestItem:
            self.Print ("")
            print Item[0]
            
            # assign a thread for event request cmd
            async_result = self.thread_asynchronous_event_request_cmd()
            
            # trigger event
            Item[1]()
            
            # wait thread finish and timeout=2s
            async_result.join(2)
                
            # if time out
            if async_result.is_alive():
                self.Print("Error: can't receive the return code of Asynchronous Event Request command", "f")
                ret_code=1
                break
                
            # get return code from Asynchronous Event Request command        
            try:
                mThreadStr=self.que.get(timeout=1)
            except Exception as error:
                self.Print("Can't get return code from Asynchronous Event Request command", "f")
            self.Print("return string from request command : %s" %(mThreadStr), "t")   
            
            mstr="0" 
            try:
                mstr=re.split("NVMe command result:", mThreadStr)[1]
            except ValueError:
                self.Print ("return string from request command : %s" %(mThreadStr))
        
            self.Print ("Completion Queue Entry Dword 0: %s" %(mstr))
        
            self.Print ("Check Dword 0")
            if mstr==Item[2]:
                self.Print("PASS", "p")
            else:
                self.Print("Fail", "f")
                ret_code=1          
        return ret_code
    
    def SubCase3(self):
        self.Print ("set Asynchronous Event Configuration = 0x0 to disable all the events can be reported to the host ")
        self.reset()
        ret_code=0
        self.shell_cmd(" nvme set-feature %s -f 0xB -v 0x0"%(self.dev), 0.5)   
        
        # loop for test items
        for Item in self.TestItemDisableReport:
            self.Print ("")
            print Item[0]
            
            # assign a thread for event request cmd
            async_result = self.thread_asynchronous_event_request_cmd()
            
            # trigger event
            
            Item[1]()
            
            
            # wait thread finish and timeout=2s
            async_result.join(2)
                
            # if time out, pass the test
            self.Print ("Check event was reported to host or not, if an event is not sent to the host then pass the test")
            if async_result.is_alive():
                self.Print("PASS", "p")
            else:
                self.Print("Fail", "f")
                ret_code=1     
        return ret_code
        
    def SubCase4(self):
        self.Print ("Sending Asynchronous Event Request command")
        self.reset()
        ret_code=0
        
        # assign a thread for event request cmd
        async_result = self.thread_asynchronous_event_request_cmd()
          
        # nvme reset
        self.Print ("Trigger nvme reset")
        self.nvme_reset()
        
        # wait thread finish and timeout=2s
        async_result.join(2)
        
        
        # if time out
        if async_result.is_alive():
            self.Print("Error: can't receive the return code of Asynchronous Event Request command", "f")
            ret_code=1
        else:
            # get return code from Asynchronous Event Request command        
            mThreadStr=self.que.get()
            
            self.Print("return string from request command : %s" %(mThreadStr), "t")
            
            mstr = mThreadStr
            self.Print ("return code : %s" %(mstr))
            
            self.Print ("Check the return code is abort request or not")
            # check the commands are aborted or not
            if re.search("NVMe Status:ABORT_REQ", mThreadStr):
                self.Print("PASS", "p")
            else:
                self.Print("Fail", "f")
                ret_code=1            
        return ret_code             
    # </sub item scripts>
    
    
    
    
if __name__ == "__main__":
    DUT = SMI_AsynchronousEventRequest(sys.argv ) 
    DUT.RunScript()
    DUT.Finish()
    
    
    
    
    
