#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
from random import randint
from time import sleep
import threading

# Import VCT modules
from lib_vct.NVME import NVME

class SMI_Power_Cycle_Test(NVME):
    ScriptName = "SMI_Power_Cycle_Test.py"
    Author = "Sam"
    Version = "20200716"
    
            
    def GetNewPattern(self):
        while True:
            VALUE =  randint(1, 0xFF)
            if VALUE != self.wPattern:
                break
        return VALUE
    
    def GSD(self):
        Timer =  randint(self.paraPorOffTimer0, self.paraPorOffTimer1) # millisecond
        self.wPattern = self.GetNewPattern()
            
        LBAptr = 0          
        self.Print("")
        self.Print(">>>>> GSD <<<<< ", "b")
        self.Print("Starting to write  LBA from 0x0, value = %s, and do POR after %s millisecond"%(self.wPattern, Timer)  )        
        self.timer.start("float") # float will return round(time, 6)
        CurrTime=0
        CurrTime_1=0
        while True:
            if not self.NVMEwrite(self.wPattern, LBAptr, 1): 
                self.Print("Fail, write command failure", "f")
                return False
            
            # round to millisecond
            CurrTime=int(self.timer.time*1000) 
  

            if CurrTime > CurrTime_1+500: # show progress every 0.5 second
                CurrTime_1 = CurrTime_1 + 500
                self.PrintProgressBar(CurrTime, self.paraPorOffTimer1, length = 20, suffix="Time: %s ms / %s ms, LBAptr: %s"%(CurrTime, self.paraPorOffTimer1, LBAptr), showPercent=False)    
                
            if CurrTime > Timer: # time up
                self.PrintProgressBar(Timer, self.paraPorOffTimer1, length = 20, suffix="Time: %s ms / %s ms, LBAptr: %s"%(Timer, self.paraPorOffTimer1, LBAptr), showPercent=False)
                self.Print("")
                self.Print("Do POR..")
                if self.por_reset(showMsg=True, PowerOffDuration=self.paraPowerOffDuration):
                    self.Print("Do POR finish")
                    break
                else:
                    self.Print("Do POR fail", "f")
                    return False
                
            LBAptr = LBAptr +1
        # end of while        
        self.Print("") 
        self.Print("Start to verify data from LBA 0x0 to %s, expected data = %s"%(LBAptr, self.wPattern))
        TestSize = self.OneBlockSize*LBAptr
        if self.fio_isequal(offset=0, size=TestSize, pattern=self.wPattern, fio_bs=self.OneBlockSize):
            self.Print("Pass", "p")
            return True
        else:
            self.Print("Fail", "f")  
            CMD = "hexdump %s -s %s -n %s"%(self.dev, 0, TestSize)
            self.Print( "Do shell command to hexdump for LBA 0 to LBA %s: %s"%(LBAptr, CMD), "w") 
            aa= self.shell_cmd(CMD)
            self.SetPrintOffset(4)
            self.Print(aa)
            self.SetPrintOffset(0) 
            return False            
    
    def DoSPOR(self):        
        self.spor_reset(showMsg=True, PowerOffDuration=self.paraPowerOffDuration)
        
    def ThreadDoSPOR(self, timer):
        sleep(0.05)
        # call self.DoSPOR() when time is up
        self.threadTimeEvent(seconds=timer, eventFunc = self.DoSPOR, printProgressBar = True)
        
    def UGSD(self):
        wPercent = 0.005
        wPercentInLBA = int(wPercent*self.NCAP)
        wSizeInByte = wPercentInLBA*self.OneBlockSize
        wLBAbottomSLBA = self.NCAP - wPercentInLBA - 1
        wLBAbottomSLBAinByte = wLBAbottomSLBA*self.OneBlockSize
        
        self.wPattern = self.GetNewPattern()
        initPattern = self.wPattern
        
        self.Print("")     
        self.Print(">>>>> UGSD <<<<< ", "b")  
        self.Print("Starting to write initial pattern into the head of the capacity, LBA from 0x0, size = %s LBA(Capacity*%s), value = %s"\
                   %(wPercentInLBA, wPercent, initPattern)  )
        self.fio_write(offset=0 , size=wSizeInByte, pattern=initPattern, fio_bs=self.OneBlockSize, showProgress=True)
        self.Print("Verify initial pattern")
        if self.fio_isequal(offset=0 , size=wSizeInByte, pattern=initPattern, fio_bs=self.OneBlockSize, printMsg=True):
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            return False
        
        
        self.Print("")    
        self.Print("Starting to write initial pattern into the bottom of the capacity, LBA from 0x%X, size = %s LBA(Capacity*%s), value = %s"\
                   %(wLBAbottomSLBA, wPercentInLBA, wPercent, self.wPattern)  )
        self.fio_write(offset=wLBAbottomSLBAinByte , size=wSizeInByte, pattern=self.wPattern, fio_bs=self.OneBlockSize, showProgress=True)
        self.Print("Verify initial pattern")
        if self.fio_isequal(offset=wLBAbottomSLBAinByte , size=wSizeInByte, pattern=initPattern, fio_bs=self.OneBlockSize, printMsg=True):
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")  
            return False   
        
        self.Print("")
        self.Print("IDLE for 5 seconds")
        sleep(5)
        self.Print("Done")
        
        
        Timer =  randint(self.paraPorOffTimer0, self.paraPorOffTimer1) # millisecond
        Timer = float(Timer)/1000 # second
        self.Print("")
        self.Print("Create thread to do SPOR after %s seconds"%Timer)            
        t = threading.Thread(target = self.ThreadDoSPOR, args=( Timer,))
        t.start()
        self.Print("Done")
       
        
        self.wPattern = self.GetNewPattern()
        randPattern = self.wPattern 
        self.Print("")
        self.Print("Going to send random write commands with value = %s."%randPattern)   
        maxSector = self.MaxNLBofCDW12()
        minLBA = wPercentInLBA +1
        maxLBA = wLBAbottomSLBA - maxSector -1
        
        isRecord = True if self.mTestModeOn else False # if TestModeOn, record cmd, else will not record
        flag = False
        while True:
            SLBA = randint(minLBA, maxLBA)
            Sector = randint(1, maxSector)
            
            if not self.NVMEwrite(randPattern, SLBA, Sector, RecordCmdToLogFile=isRecord, showMsg=True): 
                self.Print("Write command fail as expected after do SPOR", "w")
                break
            
            if flag:
                self.Print("Fail, ThreadDoSPOR is finish but write cmd is success, do spor fail, please check spor module!", "f")
                return False
            
            if not t.is_alive():
                flag = True
        # end of while
        
        #self.Print("Wait for SPOR finish")
        t.join()        
        
        self.Print("")
        self.Print("Verify initial pattern(head)")
        if self.fio_isequal(offset=0 , size=wSizeInByte, pattern=initPattern, fio_bs=self.OneBlockSize, printMsg=True):
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")
            return False
        
        self.Print("")        
        self.Print("Verify initial pattern(bottom)")
        if self.fio_isequal(offset=wLBAbottomSLBAinByte , size=wSizeInByte, pattern=initPattern, fio_bs=self.OneBlockSize, printMsg=True):
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")  
            return False
        
        return True                   
        

        
    
    def __init__(self, argv):
        # initial parent class
        self.SetDynamicArgs(optionName="l", optionNameFull="Loops", \
                            helpMsg="number of loops, default = 10", argType=int, default=1)
        self.SetDynamicArgs(optionName="pot0", optionNameFull="PorOffTimer0", \
                            helpMsg="Power Off Timer minium in millisecond, default = 2000", argType=int, default=2000)
        self.SetDynamicArgs(optionName="pot1", optionNameFull="PorOffTimer1", \
                            helpMsg="Power Off Timer maxium in millisecond, default = 4000", argType=int, default=4000)
        self.SetDynamicArgs(optionName="pod", optionNameFull="PowerOffDuration", \
                            helpMsg="Power Off Duration in millisecond, default = 5000", argType=int, default=5000)
 
        super(SMI_Power_Cycle_Test, self).__init__(argv)


        self.paraLoops = self.GetDynamicArgs(0) 
        self.paraPorOffTimer0 = self.GetDynamicArgs(1) 
        self.paraPorOffTimer1 = self.GetDynamicArgs(2) 
                 
        self.paraPowerOffDuration = self.GetDynamicArgs(3) 
        self.paraPowerOffDuration = float(self.paraPowerOffDuration)/1000 # convert to second
         
        

        self.NCAP=self.IdNs.NCAP.int
        self.wPattern = 0
        
        self.OneBlockSize = self.GetBlockSize()
        self.Print("Block size: %s"%self.OneBlockSize, "p")        

    # define pretest, if not return 0 , skip all subcases
    def PreTest(self):        
        return 0            

    # <define sub item scripts>
    SubCase1TimeOut = 0
    SubCase1Desc = "GSD"   
    SubCase1KeyWord = ""
    def SubCase1(self):
        ret_code=0
        
        for loop in range(1, self.paraLoops+1):
            self.PrintLoop = loop
            if not self.GSD(): 
                ret_code=1
                break        
        
            
        return ret_code

    SubCase2TimeOut = 0
    SubCase2Desc = "UGSD"   
    SubCase2KeyWord = ""
    def SubCase2(self):
        ret_code=0
        
        for loop in range(1, self.paraLoops+1):
            self.PrintLoop = loop
            if not self.UGSD(): 
                ret_code=1
                break
        
        return ret_code

    SubCase3TimeOut = 0
    SubCase3Desc = "UGSD"   
    SubCase3KeyWord = ""
    def SubCase3(self):
        ret_code=0
        
        for loop in range(1, self.paraLoops+1):
            self.PrintLoop = loop
            if not self.GSD(): 
                ret_code=1
                break

            if not self.UGSD(): 
                ret_code=1
                break
                    
        return ret_code

    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_Power_Cycle_Test(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    