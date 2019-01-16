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
        self._Threshold=2
        # function to be triggered as DST in pregress
        # ex. 'def FormatNSID(nsid)' where _EventTrigger=FormatNSID, _args=nsid
        # ex. mNVME.Flow.DST.SetEventTrigger(FormatNSID, 0xffffffff) where _args=nsid=0xffffffff
        # _EventTrigger: function name
        # _args: function parameters
        self._EventTrigger = None        
        self._args=None
        self.EventTriggeredMessage="Event was triggered while DST execution exceed 2% "
        
        self.ShowProgress=True
        self.ShowMessage=True
         
    def SetEventTrigger(self, EventTrigger=None, args=None):    
        self._EventTrigger = EventTrigger
        self._args=args
        
    def SetEventTriggerThreshold(self, Threshold=2):    
        self._Threshold = Threshold
                
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
            self._mNVME.Print ("Controller does not support the DST operation, quit DST test!")
            return -1
        # if DST is running before this test, then send abort DST command with cd10=0xf
        if self._mNVME.GetLog.DeviceSelfTest.CDSTO!=0:
            self._mNVME.shell_cmd("LOG_BUF=$(nvme admin-passthru %s --opcode=0x14 --namespace-id=%s --data-len=0 --cdw10=0xF -r -s 2>&1 > /dev/null)"%(self._mNVME.dev_port, self._NSID))
            
        if self.ShowMessage:    
            self._mNVME.Print ("Starting DST .."  )
            print self.EventTriggeredMessage 
        event_trigged=0
        error=0
        DST_per_old=0
        # self test command
        self._mNVME.shell_cmd("LOG_BUF=$(nvme admin-passthru %s --opcode=0x14 --namespace-id=%s --data-len=0 --cdw10=%s -r -s 2>&1 > /dev/null)"%(self._mNVME.dev_port, self._NSID, self._DstType))
        # print Progress with 0% 
        if self.ShowProgress:
            self._mNVME.PrintProgressBar(0, 100, prefix = 'Progress:', length = 50)
        while True:            
            sleep (0.1)
            # if DST_per value changed, then print DST_per
            DST_per=self._mNVME.GetLog.DeviceSelfTest.CDSTC
            if DST_per_old!=DST_per:
                if self.ShowProgress and DST_per!=0:
                    #self._mNVME.Print ("percentage = %s"%DST_per)
                    self._mNVME.PrintProgressBar(DST_per, 100, prefix = 'Progress:', length = 50)
            else:
                sleep (0.1)
            DST_per_old=DST_per
            # if percent > 2% and  _EventTrigger!=None, then trigger event
            if DST_per>=self._Threshold and event_trigged==0 and self._EventTrigger!=None:                              
                # excute event  
                try:  
                    if self._args==None:
                        self._EventTrigger()
                    else:
                        self._EventTrigger(self._args)
                except Exception as e:
                    self._mNVME.Print(e, "f")
                    error=1
                    
                event_trigged=1        
         
            #if if self test fininshed (Current Device Self-Test Operation==0) and ShowProgress
            if self._mNVME.GetLog.DeviceSelfTest.CDSTO==0:
                # if DST Operation completed without error, then set progress bar to 100%
                DSTS=self._mNVME.GetLog.DeviceSelfTest.TestResultDataStructure_1th.DeviceSelfTestStatus
                DSTSbit3to0 = DSTS & 0b00001111
                if DSTSbit3to0==0 and self.ShowProgress:
                    self._mNVME.PrintProgressBar(100, 100, prefix = 'Progress:', length = 50)
                else:                
                    self._mNVME.Print ("")
                break

        if self.ShowMessage:
            self._mNVME.Print ("DST finished" )
        if error==0:           
            return self._mNVME.GetLog.DeviceSelfTest.TestResultDataStructure_1th.DeviceSelfTestStatus
        else:
            return -1

        
    