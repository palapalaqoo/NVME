'''
Created on Oct 5, 2018

@author: root
'''
import re


from time import sleep

class Sanitize_():
    def __init__(self, obj):
        self._mNVME = obj
        self._Options = "-a 0x02"
        # function to be triggered as Sanitize in pregress
        # ex. 'def FormatNSID(nsid)' where _EventTrigger=FormatNSID, _args=nsid
        # ex. mNVME.Flow.Sanitize.SetEventTrigger(FormatNSID, 0x1, 0xffffffff) where _args=nsid= (0x1 and 0xffffffff)
        # _EventTrigger: function name
        # _args: function parameters, ex, ("123", "456")
        self._EventTrigger = None        
        self._args=None
        self.EventTriggeredMessage="Event was triggered while execution exceed 2% "
        
        self.ShowProgress=True
         
    def SetEventTrigger(self, EventTrigger=None, *args):    
        self._EventTrigger = EventTrigger
        self._args=args
        
    def SetEventTriggerThreshold(self, Threshold=2):    
    # Threshold <65535
        self._Threshold = Threshold
        
    def SetOptions(self, Opt):
    # refer to NVME Cli, nvme-sanitize
        self._Options=Opt
            
    def Start(self): 
    # start Sanitize and return interger -1 if Exception occured
    # or return 0
            
        #print "Starting "  
        #print self.EventTriggeredMessage 
        event_trigged=0
        error=0
        per_old=0
        # Sanitize command
        CMD="nvme sanitize %s %s 2>&1"%(self._mNVME.dev_port, self._Options)
        mStr=self._mNVME.shell_cmd(CMD)
        if not re.search("SUCCESS", mStr):
            self._mNVME.Print("Sanitize command error!, command: %s"%CMD, "f")
            self._mNVME.Print("Command return status: %s"%mStr, "f")
            return -1
            
        # print Progress with 0% 
        if self.ShowProgress:
            self._mNVME.PrintProgressBar(0, 100, prefix = 'Progress:', length = 50)
        while True:            
            sleep (0.1)
            # if per value changed, then print per
            per=self._mNVME.GetLog.SanitizeStatus.SPROG
            if per_old!=per:
                if self.ShowProgress and per!=0:
                    #print "percentage = %s"%per
                    self._mNVME.PrintProgressBar(per, 65535, prefix = 'Progress:', length = 50)
            else:
                sleep (0.1)
            per_old=per
            # if percent > 2% and  _EventTrigger!=None, then trigger event
            if per>=self._Threshold and event_trigged==0 and self._EventTrigger!=None:                              
                # excute event  
                try:
                    if len(self._args)==0:
                        self._EventTrigger()
                    else:                    
                        self._EventTrigger(*self._args)
                except Exception as e:
                    print ""
                    self._mNVME.Print(e, "f")
                    error=1
                    
                event_trigged=1        
         
            #if fininshed 
            if per == 65535:                
                break

        if error==0:           
            return 0
        else:
            return -1

        
    