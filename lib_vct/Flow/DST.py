'''
Created on Oct 5, 2018

@author: root
'''
import sys


from time import sleep

class DST_():
    def __init__(self, obj):
        self._mNVME = obj
        self._DstType=1
        self._NSID=1
        # function to be triggered as DST in pregress
        # ex. 'def FormatNSID(nsid)' where _EventTrigger=FormatNSID, _args=nsid
        # ex. mNVME.Flow.DST.SetEventTrigger(FormatNSID, 0xffffffff) where _args=nsid=0xffffffff
        # _EventTrigger: function name
        # _args: function parameters
        self._EventTrigger = None        
        self._args=None
        self.EventTriggeredMessage="Event was triggered while DST execution exceed 40% "
        
        self.ShowProgress=True
         
    def SetEventTrigger(self, EventTrigger=None, args=None):    
        self._EventTrigger = EventTrigger
        self._args=args
        
    def SetDstType(self, DstType=1):  
    # DstType = 1, Short device self-test operation
    # DstType = 2, Extended device self-test operation 
        self._DstType = DstType

    def SetNSID(self, NSID=1):  
    # DstType = 1, Short device self-test operation
    # DstType = 2, Extended device self-test operation 
        self._NSID = NSID              
            
    def Start(self): 
    # start DST and return interger -1 if Exception occured
    # or return device self test status in get log page if command finish
        # if DST not supported
        if self._mNVME.IdCtrl.OACS.bit(4)=="0":
            print "Controller does not support the DST operation, quit DST test!"
            return -1
        print "Starting DST .."  
        event_trigged=0
        error=0
        DST_per_old=0
        # self test command
        self._mNVME.shell_cmd("LOG_BUF=$(nvme admin-passthru %s --opcode=0x14 --namespace-id=%s --data-len=0 --cdw10=%s -r -s 2>&1 > /dev/null)"%(self._mNVME.dev_port, self._NSID, self._DstType))
        
        while True:            
            sleep (0.1)
            # if DST_per value changed, then print DST_per
            DST_per=self._mNVME.GetLog.DeviceSelfTest.CDSTC
            if DST_per_old!=DST_per:
                if self.ShowProgress:
                    print "percentage = %s"%DST_per
            else:
                sleep (0.1)
            DST_per_old=DST_per
            # if percent > 40% and  _EventTrigger!=None, then trigger event
            if DST_per>40 and event_trigged==0 and self._EventTrigger!=None:            
                print "Sending format command while DST execution exceed 40% "     
                # excute event  
                try:  
                    self._EventTrigger(self._args)
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

        
    