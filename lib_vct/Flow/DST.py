'''
Created on Oct 5, 2018

@author: root
'''
import sys


from time import sleep

class DST_():
    def __init__(self, obj):
        self._mNVME = obj
        self._EventTrigger = None
        self._DstType=1
         
    def SetEventTrigger(self, EventTrigger=None):    
        self._EventTrigger = EventTrigger
        
    def SetDstType(self, DstType=1):  
    # DstType = 1, Short device self-test operation
    # DstType = 2, Extended device self-test operation 
        self._DstType = DstType
              
            
    def Start(self): 
    # start DST and return interger -1 if Exception occured
    # or return device self test status in get log page if command finish
        print "Starting DST .."  
        event_trigged=0
        error=0
        # self test command
        self._mNVME.shell_cmd("LOG_BUF=$(nvme admin-passthru %s --opcode=0x14 --namespace-id=0xffffffff --data-len=0 --cdw10=%s -r -s 2>&1 > /dev/null)"%(self._mNVME.dev_port, self._DstType))
        
        while True:
            # if self test percentage > 40%, send reset command
            sleep (0.1)
            DST_per=self._mNVME.GetLog.DeviceSelfTest.CDSTC
            print "percentage = %s"%DST_per
            # if percent > 40% and  _EventTrigger!=None, then trigger event
            if DST_per>40 and event_trigged==0 and self._EventTrigger!=None:            
                print "Sending format command while DST execution exceed 40% "     
                # excute event  
                try:  
                    self._EventTrigger()
                except Exception as e:
                    self._mNVME.Print(e, "f")
                    error=1
                    
                event_trigged=1        
         
            #if if self test fininshed (Current Device Self-Test Operation==0)
            if self._mNVME.GetLog.DeviceSelfTest.CDSTO==0:
                break
            
            
        
        print "DST finished" 
        if error==0:
            return self._mNVME.GetLog.DeviceSelfTest.TestResultDataStructure_1th.DeviceSelfTestStatus
        else:
            return -1

        
    