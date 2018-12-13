#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
import time
from time import sleep
import threading
import re

# Import VCT modules
from lib_vct.NVME import NVME
from lib_vct.NVMECom import deadline

class SMI_NVMeReset(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_NVMeReset.py"
    Author = "Sam Chan"
    Version = "20181211"
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    SubCase1TimeOut = 60
    SubCase1Desc = "Test The Admin Queue registers (AQA, ASQ, or ACQ)"  
    
    SubCase2TimeOut = 60
    SubCase2Desc = "Test if all supported reset is working"    
    
    SubCase3TimeOut = 3600
    SubCase3Desc = "Test if stops processing any outstanding Admin command"

    SubCase4TimeOut = 7200
    SubCase4Desc = "Test if stops processing any outstanding IO command"    

    
    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def GetRDY(self):
        return self.CR.CSTS.bit(0)
    
    def initTestItems(self):
        # self.TestItems=[[description, function],[description, function],..]
        
        self.TestItems.append(["Controller Reset", self.nvme_reset])
        
        if self.NSSRSupport:
            self.TestItems.append(["NVM Subsystem Reset", self.subsystem_reset])
            
        self.TestItems.append(["PCI Express Hot reset", self.hot_reset])    
        
        self.TestItems.append(["Data Link Down status", self.link_reset]) 
        
        self.TestItems.append(["Function Level Reset", self.FunctionLevel_reset])
        
    def StartDstAndGetStatus(self, triggerFunc):
        self.Flow.DST.EventTriggeredMessage="Send format command as DST execution >= 1% "
        self.Flow.DST.ShowProgress=False     
        self.Flow.DST.ShowMessage=False
        # set DST command nsid
        self.Flow.DST.SetNSID(0x1)
        # set DST type = Short device self-test operation
        self.Flow.DST.SetDstType(1)  
        # set Event
        self.Flow.DST.SetEventTrigger(triggerFunc)                   
        # set Threshold = 1 to raise event
        self.Flow.DST.SetEventTriggerThreshold(1)
            
        # start DST flow and get device self test status 
        DSTS=self.Flow.DST.Start() 
        return DSTS       
    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def __init__(self, argv):
        # initial parent class
        super(SMI_NVMeReset, self).__init__(argv)
        
        # <Parameter>
        self.NSSRSupport=True if self.CR.CAP.NSSRS.int==1 else False
        self.TestItems=[]

        # </Parameter>
        
        self.initTestItems()
        
        # add script descriptions
        self.AddInfo(self.ScriptName, self.Author, self.Version)
        
        # add all sub items to test script list

        '''
        self.AddScript(self.SubCase2, self.SubCase2Desc)
        self.AddScript(self.SubCase3, self.SubCase3Desc)
        self.AddScript(self.SubCase4, self.SubCase4Desc)
        self.AddScript(self.SubCase5, self.SubCase5Desc)
        self.AddScript(self.SubCase6, self.SubCase6Desc)
        self.AddScript(self.SubCase7, self.SubCase7Desc)

        '''
        
    # <sub item scripts> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    @deadline(SubCase1TimeOut)
    def SubCase1(self):  
        print "Test The Admin Queue registers (AQA, ASQ, or ACQ) are not reset as part of a controller reset"
        print "" 
        ret_code=0
        RDY = self.GetRDY()
        
        print "Check if CSTS.RDY is set to 1 before reset:"
        if RDY=="1":
            self.Print("Pass", "p")
        else:
            self.Print("Fail, exit sub case!", "f")
            ret_code=1
            return ret_code

                        
        AQA = self.CR.AQA.str    
        ASQ = self.CR.ASQ.str   
        ACQ = self.CR.ACQ.str    
                      
        print "NVME reset (Controller disable)"        
        t = threading.Thread(target = self.nvme_reset)
        t.start()
        
        print "Wait for CSTS.RDY = 0"
        while self.GetRDY()==1:
            pass
        
        self.Print("CSTS.RDY = 0", "p")
        print "Wait for CSTS.RDY = 1"
        while self.GetRDY()==0:
            pass
        
        t.join()
        self.Print("CSTS.RDY = 1", "p")
        
        print "compare AQA, ASQ, ACQ after reset"
        print "before reset: AQA = %s" %(AQA)
        print "before reset: ASQ = %s" %(ASQ)
        print "before reset: ACQ = %s" %(ACQ)
        print "after reset: AQA = %s" %(self.CR.AQA.str)
        print "after reset: ASQ = %s" %(self.CR.ASQ.str)
        print "after reset: ACQ = %s" %(self.CR.ACQ.str)
        
        if AQA!=self.CR.AQA.str or ASQ!=self.CR.ASQ.str or ACQ!=self.CR.ACQ.str:
            self.Print("Fail", "f")
            ret_code=1
        else:
            self.Print("Pass", "p")        
        sleep(0.1)
        
        return ret_code
    
    @deadline(SubCase2TimeOut)
    def SubCase2(self):
        print "Check if all supported reset is working"  
        ret_code=0    

        print ""
        for mItem in self.TestItems:        
            reset_type_name=mItem[0]
            reset_func=mItem[1] 
            print "issue " + reset_type_name
            print "Check if controll is alive after reset"
            reset_func()
            if self.dev_alive:
                self.Print("PASS", "p")
            else:
                self.Print("FAIL, exit", "f")
                ret_code = 1
            print  ""    
                    
        return ret_code

        
    @deadline(SubCase3TimeOut)
    def SubCase3(self):
        print "Test if reset occur, controller stops processing any outstanding Admin command"
        print "Test if device self-test operation(admin command) was aborted due to the reset commands"  
        print "test Loop = 10 "
        print ""
        
        if self.IdCtrl.OACS.bit(4)=="0":
            print "Controller does not support the DST operation, quit this test item!"
            return 0        
        else:
            # max loopcnt = len(TestItems)* loop
            loopcnt=0    
            for loop in range(10):                
                # loop for every kind of reset
                for mItem in self.TestItems:        
                    loopcnt=loopcnt+1
                    # unmark below to assign reset type for all test, 
                    #mItem=self.TestItems[3]
                    reset_type_name=mItem[0]
                    reset_func=mItem[1] 
                    
                    # start DST, if DST progress>1, issue reset in reset_func, after DST finish, get status code
                    DSTS=self.StartDstAndGetStatus(reset_func)
                    # check status code
                    if DSTS!=-1:        
                        # get bit 3:0        
                        DSTSbit3to0 = DSTS & 0b00001111
                        #print "result of the device self-test operation from Get Log Page : %s" %hex(DSTSbit3to0)
                        #print "Check the result of the device self-test operation , expected result:  0x2(Operation was aborted by a Controller Level Reset)"
                        if DSTSbit3to0==2:
                            self.Print("Loop: %s, reset type: %s, PASS"%(loop, reset_type_name), "p")
                        else:
                            self.Print("Loop: %s, reset type: %s, Fail"%(loop, reset_type_name), "f")
                            ret_code = 1                         
                    else:
                        print "Controller does not support the DST operation"     
                             
            return ret_code

    # </sub item scripts> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    
    
    
if __name__ == "__main__":
    DUT = SMI_NVMeReset(sys.argv )
    DUT.PrintInfo()
    DUT.RunScript()
    DUT.PrintColorBriefReport()
    
    
    
    
    
    
