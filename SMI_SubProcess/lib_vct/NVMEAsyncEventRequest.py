'''
Created on Aug 24, 2018

@author: root
'''

from lib_vct.NVME import NVME
import threading
import Queue
from multiprocessing.pool import ThreadPool
from time import sleep
class AsyncEvent(NVME):    
    que = Queue.Queue()
        
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
        
        
        