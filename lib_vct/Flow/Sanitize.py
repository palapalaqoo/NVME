'''
Created on Oct 5, 2018

@author: root
'''
import re
import time

from time import sleep

class FlowSanitizeMode:
    Normal = "Normal"
    KeepSanitizeInProgress = "KeepSanitizeInProgress"

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
        self.TimeOut=60
        self.Mode=FlowSanitizeMode.Normal
        self._Threshold=1000
         
    def SetEventTrigger(self, EventTrigger=None, *args):    
        self._EventTrigger = EventTrigger
        self._args=args
        
    def SetEventTriggerThreshold(self, Threshold=2):    
    # Threshold <65535
        self._Threshold = Threshold
        
    def SetOptions(self, Opt):
    # refer to NVME Cli, nvme-sanitize, ex. '-a 2'
        self._Options=Opt
        
    def WaitRecentSanitizeFinish(self):
    # time out 10s
        per = self._mNVME.GetLog.SanitizeStatus.SPROG
        if per != 65535:
            WaitCnt=0
            while per != 65535:
                #print ("Sanitize Progress: %s"%per)
                per = self._mNVME.GetLog.SanitizeStatus.SPROG
                WaitCnt = WaitCnt +1
                if WaitCnt ==10:
                    return False
                sleep(1)
        else:
            return True

    def _IssueCommand(self):
        # Sanitize command 
        CMD="nvme sanitize %s %s 2>&1"%(self._mNVME.dev_port, self._Options)                
        mStr=self._mNVME.shell_cmd(CMD)
        CMD="echo $?"              
        mStr=self._mNVME.shell_cmd(CMD) 
        sleep(0.1)       
        if not re.search("0", mStr):
            self._mNVME.Print("lib_vct/Flow/Sanitize: Sanitize command error!, command: %s"%CMD, "f")
            self._mNVME.Print("lib_vct/Flow/Sanitize: Command return status: %s"%mStr, "f")
            return False   
        else:
            return True
                
    def Start(self): 
    # start Sanitize and return interger 
    # -1 sanitize command error
    # 1 if Exception occured 
    # 2 timeout
    # 2 SPROG count error
    # or return 0
            
        #print "Starting "  
        #print self.EventTriggeredMessage 
        event_trigged=0
        error=0
        per_old=0
        TimeStart=self._mNVME.Second
        
        # start for self.Mode= FlowSanitizeMode.Normal ===================================================
        if self.Mode==FlowSanitizeMode.Normal:
            # wait for last Sanitize command Finish
            if not self.WaitRecentSanitizeFinish():
                self._mNVME.Print("lib_vct/Flow/Sanitize: Fail!, Recent Sanitize can't finish in 10 s", "f")
                return -1            
            # Sanitize command
            if not self._IssueCommand():
                return -1   
                
            # print Progress with 0% 
            if self.ShowProgress:
                self._mNVME.PrintProgressBar(0, 100, prefix = 'Progress:', length = 50)
            
            # check if SPROG  start to count in 1 s, or quit all
            WaitCnt=0    
            while True:                
                per = self._mNVME.GetLog.SanitizeStatus.SPROG
                if per != 65535:
                    break                
                WaitCnt = WaitCnt +1
                if WaitCnt ==10:
                    return -1
                sleep(0.1)                
                
                
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
                
                # check per
                if per < per_old:
                    return 3
                
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
                        self._mNVME.Print("lib_vct/Flow/Sanitize: " + e, "f")
                        error=1
                        
                    event_trigged=1        
             
                #if fininshed 
                if per == 65535:                
                    break
                
                # if timeout
                TimeElapsed= TimeStart-self._mNVME.Second
                if TimeElapsed > self.TimeOut:
                    print ""
                    self._mNVME.Print("lib_vct/Flow/Sanitize: Fail!, Time out!, TimeElapsed = %s s "%self.TimeOut, "f")
                    error=2                
                    break
    
        # == end for if self.Mode==FlowSanitizeMode.Normal ===================================================
        
        # == start for if self.Mode==FlowSanitizeMode.KeepSanitizeInProgress ========================================
        if self.Mode==FlowSanitizeMode.KeepSanitizeInProgress:
            initper=0
            # If Sanitize command Finish, then issue it again
            per=self._mNVME.GetLog.SanitizeStatus.SPROG
            initper=per
            if per == 65535:                   
                # Sanitize command 
                if not self._IssueCommand():
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
                
                # if percent changed and  _EventTrigger!=None, then trigger event
                if per!=initper and per!=0 and per!=65535 and  self._EventTrigger!=None:                              
                    # excute event  
                    try:
                        if len(self._args)==0:
                            self._EventTrigger()
                            
                            # if sanitize still in progress, then end flow
                            if self._mNVME.GetLog.SanitizeStatus.SPROG != 65535:                
                                break
                                    
                        else:                    
                            self._EventTrigger(*self._args)
                            
                            # if sanitize still in progress, then end flow
                            if self._mNVME.GetLog.SanitizeStatus.SPROG != 65535:                
                                break
                                
                    except Exception as e:
                        print ""
                        self._mNVME.Print("lib_vct/Flow/Sanitize: " + e, "f")
                        error=1

                # if sanitize still in progress, then end flow
                if per==65535:                
                    if not self._IssueCommand():
                        return -1
                
                # if timeout
                TimeElapsed= TimeStart-self._mNVME.Second
                if TimeElapsed > self.TimeOut:
                    print ""
                    self._mNVME.Print("lib_vct/Flow/Sanitize: Fail!, Time out!, TimeElapsed = %s s "%self.TimeOut, "f")
                    error=2               
                    break
        # == end for if self.Mode==FlowSanitizeMode.KeepSanitizeInProgress ========================================    
        return error
