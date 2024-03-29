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
    
class FlowSanitizeStatus:
    CommandError = -1
    Success = 0
    ExceptionOccured = 1
    TimeOut = 2
    SprogCountError = 3
    OverWriteCompletedPassesCountCountError = 4    
    SanitizeGoFinishAfterEventTriger = 5

class Sanitize_():
    # OverWriteCompletedPassesCount
    Static_LastOWCPC=0
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
        self._SANACT=2
        self.GetEventTriggerStartSPROG=0xFFFF # self._EventTrigger start at
        self.GetEventTriggerStopSPROG=0xFFFF # self._EventTrigger stop at
         
    def SetEventTrigger(self, EventTrigger=None, *args):    
        self._EventTrigger = EventTrigger
        self._args=args
        
    def SetEventTriggerThreshold(self, Threshold=2):    
    # Threshold <65535
        self._Threshold = Threshold
        
    def SetOptions(self, Opt):
    # refer to NVME Cli, nvme-sanitize, ex. '-a 2'
        self._Options=Opt
        
        # parse Sanitize Action (SANACT)
        mStr="-a (\w*)"
        if re.search(mStr, Opt):
            self._SANACT=int(re.search(mStr, Opt).group(1), 16)    
        mStr="--sanact=(\w*)"
        if re.search(mStr, Opt):
            self._SANACT=int(re.search(mStr, Opt).group(1), 16)           
        
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
    # 3 SPROG count error
    # 4 completed passes count error(Overwrite)
    # or return 0
            
        #self._mNVME.Print ("Starting "  )
        #print self.EventTriggeredMessage 
        event_trigged=0
        rtCode=FlowSanitizeStatus.Success
        rtOWCPC=0   # rtOverWriteCompletedPassesCount
        OWLCP_old=0
        per_old=0
        TimeStart=self._mNVME.Second
        TimeElapsed=0
        
        # start for self.Mode= FlowSanitizeMode.Normal ===================================================
        if self.Mode==FlowSanitizeMode.Normal:
            # wait for last Sanitize command Finish
            if not self.WaitRecentSanitizeFinish():
                self._mNVME.Print("lib_vct/Flow/Sanitize: Fail!, Recent Sanitize can't finish in 10 s", "f")
                return FlowSanitizeStatus.CommandError         
            # Sanitize command
            if not self._IssueCommand():
                return FlowSanitizeStatus.CommandError
                
            # print Progress with 0% 
            if self.ShowProgress:
                mSuffix = 'Time: %s s'%(self.TimeOut-TimeElapsed) + ", Completed passes: %s"%rtOWCPC
                self._mNVME.PrintProgressBar(0, 100, prefix = 'Progress:',suffix=mSuffix, length = 50)
            
            # check if SPROG  start to count in 1 s, or quit all
            WaitCnt=0    
            while True:                
                per = self._mNVME.GetLog.SanitizeStatus.SPROG
                if per != 65535:
                    break                
                WaitCnt = WaitCnt +1
                if WaitCnt ==10:                    
                    # if is Crypto Erase, SPROG may not count properly, becouse changing the media encryption keys is very fast
                    if self._SANACT==4:
                        break
                    else:
                        rtCode = FlowSanitizeStatus.SprogCountError
                        self._mNVME.Print ("lib_vct/Flow/Sanitize: Error!, after sending sanitize command and wait for 1 second, SPROG still equal to 0xFFFF !", "f")
                        self._mNVME.Print ("lib_vct/Flow/Sanitize: i.e. controller has not starting sanitize operation in 1s after received command!", "f")
                        return rtCode
                sleep(0.1)                
                
                
            while True:            
                sleep (0.1)
                # if per value changed, then print per
                per=self._mNVME.GetLog.SanitizeStatus.SPROG
                if per_old!=per:
                    if self.ShowProgress and per!=0:
                        #self._mNVME.Print ("percentage = %s"%per)
                        mSuffix = 'Time: %s s'%(self.TimeOut-TimeElapsed) + ", Completed passes: %s"%rtOWCPC
                        self._mNVME.PrintProgressBar(per, 65535, prefix = 'Progress:',suffix=mSuffix, length = 50)
                else:
                    sleep (0.1)
                
                # check per
                if per < per_old:
                    rtCode= FlowSanitizeStatus.SprogCountError
                
                # OverWriteCompletedPassesCount
                OWCPC=(self._mNVME.GetLog.SanitizeStatus.SSTAT&0b11111000)>>3
                # counter error ?
                if rtOWCPC > OWCPC and OWCPC!=0:
                    rtCode= FlowSanitizeStatus.OverWriteCompletedPassesCountCountError
                # if finish sanitize and OWCPC!=0
                if per == 65535 and OWCPC!=0:
                    rtCode= FlowSanitizeStatus.OverWriteCompletedPassesCountCountError
                # save counter to rtOWCPC
                if rtOWCPC < OWCPC:     
                    rtOWCPC = OWCPC

                
                # if percent > 2% and  _EventTrigger!=None, then trigger event -------------------------------------------------------
                if per>=self._Threshold and event_trigged==0 and self._EventTrigger!=None:                              
                    # excute event  
                    try:
                        self.GetEventTriggerStartSPROG=per # start _EventTrigger at SPROG
                        if len(self._args)==0:
                            self._EventTrigger()
                        else:                    
                            self._EventTrigger(*self._args)
                        self.GetEventTriggerStopSPROG=self._mNVME.GetLog.SanitizeStatus.SPROG # stop _EventTrigger at SPROG
                            

                            
                    except Exception as e:
                        self._mNVME.Print ("")
                        self._mNVME.Print("lib_vct/Flow/Sanitize: " + e, "f")
                        rtCode=FlowSanitizeStatus.ExceptionOccured
                        break
                        
                    event_trigged=1        
                    
                    # if Sanitize counter direct go to FFFF after reset/EventTrigger, Sanitize may not finish the operation,  according to the below message    
                    # Once a sanitize operation is started, it cannot be aborted and continues after a Controller Level Reset including across power cycles.
                    # check this once only                       
                    per=self._mNVME.GetLog.SanitizeStatus.SPROG
                    if per == 65535:    
                        rtCode=FlowSanitizeStatus.SanitizeGoFinishAfterEventTriger            
                        break 
                # end of trigger event -------------------------------------------------------
                
                #if fininshed 
                if per == 65535:                
                    break
                
                # if timeout
                TimeElapsed= self._mNVME.Second-TimeStart
                if TimeElapsed > self.TimeOut:
                    self._mNVME.Print ("")
                    self._mNVME.Print("lib_vct/Flow/Sanitize: Fail!, Time out!, TimeElapsed = %s s "%self.TimeOut, "f")
                    rtCode=FlowSanitizeStatus.TimeOut              
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
                self._mNVME.PrintProgressBar(0, 100, prefix = 'Progress:',suffix='Time: %s s'%(self.TimeOut-TimeElapsed), length = 50)
                
            TryAgain = False
            while True:            
                sleep (0.1)
                # if per value changed, then print per
                per=self._mNVME.GetLog.SanitizeStatus.SPROG
                if per_old!=per:
                    if self.ShowProgress and per!=0:
                        #self._mNVME.Print ("percentage = %s"%per)
                        self._mNVME.PrintProgressBar(per, 65535, prefix = 'Progress:',suffix='Time: %s s'%(self.TimeOut-TimeElapsed), length = 50)
                else:
                    sleep (0.1)
                per_old=per
                
                # if percent changed and  _EventTrigger!=None, then trigger event -------------------------------------------------------
                if per!=initper and per!=0 and per!=65535 and  self._EventTrigger!=None:                              
                    # excute event  
                    try:
                        if len(self._args)==0:
                            self._EventTrigger()
                        else:                    
                            self._EventTrigger(*self._args)                                                       
                    except Exception as e:
                        self._mNVME.Print ("")
                        self._mNVME.Print("lib_vct/Flow/Sanitize: " + e, "f")
                        rtCode=FlowSanitizeStatus.ExceptionOccured    
                    # if sanitize still in progress, then end flow
                    if self._mNVME.GetLog.SanitizeStatus.SPROG != 65535:                
                        break
                    else:
                        # if Sanitize counter direct go to FFFF, Sanitize may not finish the operation, do _EventTrigger again
                        if TryAgain==False:
                            TryAgain=True     
                        # after do _EventTrigger again, still direct go to FFFF, the according to the below message    
                        # Once a sanitize operation is started, it cannot be aborted and continues after a Controller Level Reset including across power cycles.                       
                        else:
                            rtCode=FlowSanitizeStatus.SanitizeGoFinishAfterEventTriger
                            break;                        
                # end of trigger event -------------------------------------------------------

                # if sanitize not in progress, then issue cmd
                if per==65535:                
                    if not self._IssueCommand():
                        rtCode=FlowSanitizeStatus.CommandError
                        return rtCode
                
                # if timeout
                TimeElapsed= self._mNVME.Second-TimeStart
                if TimeElapsed > self.TimeOut:
                    self._mNVME.Print ("")
                    self._mNVME.Print("lib_vct/Flow/Sanitize: Fail!, Time out!, TimeElapsed = %s s "%self.TimeOut, "f")
                    rtCode=FlowSanitizeStatus.TimeOut            
                    break
        # == end for if self.Mode==FlowSanitizeMode.KeepSanitizeInProgress ========================================  
        # save rtOWCPC to static valuable
        Sanitize_.Static_LastOWCPC=rtOWCPC
        
        self._mNVME.Print ("")
          
        return rtCode
