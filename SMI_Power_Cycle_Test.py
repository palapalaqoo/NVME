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
    Version = "20200917"
    
            
    def GetNewPattern(self):
        while True:
            VALUE =  randint(1, 0xFF)
            if VALUE != self.wPattern:
                break
        return VALUE
    
    def GSD(self):
        Timer =  randint(self.paraUGSDTimerMin, self.paraUGSDTimerMax) # millisecond
        self.wPattern = self.GetNewPattern()
        
        LBAptr = 0          
        self.Print("")
        self.Print(">>>>> GSD <<<<< ", "b")
        self.Print("Starting to write  LBA from 0x0, value = %s, and do POR after %s millisecond"%(self.wPattern, Timer)  )        
        self.timer.start("float") # float will return round(time, 6)
        CurrTime=0
        CurrTime_1=0
        while True:
            if not self.NVMEwrite(self.wPattern, LBAptr, 1, OneBlockSize=self.OneBlockSize): 
                self.Print("Fail, write command failure", "f")
                return False
            
            # round to millisecond
            CurrTime=int(self.timer.time*1000) 
  

            if CurrTime > CurrTime_1+500: # show progress every 0.5 second
                CurrTime_1 = CurrTime_1 + 500
                self.PrintProgressBar(CurrTime, self.paraUGSDTimerMax, length = 20, suffix="Time: %s ms / %s ms, LBAptr: %s"%(CurrTime, self.paraUGSDTimerMax, LBAptr), showPercent=False)    
                
            if CurrTime > Timer: # time up
                self.PrintProgressBar(Timer, self.paraUGSDTimerMax, length = 20, suffix="Time: %s ms / %s ms, LBAptr: %s"%(Timer, self.paraUGSDTimerMax, LBAptr), showPercent=False)
                self.Print("")
                self.Print("Do POR..")
                PowerOffTimer = float(self.paraPwrOffDuration) / 1000 # convert int in minisecond to float in second
                if self.por_reset(showMsg=True, PowerOffDuration=PowerOffTimer):
                    self.Print("Do POR finish")
                    break
                else:
                    self.Print("Do POR fail", "f")
                    return False
                
            LBAptr = LBAptr +1
        # end of while        
        self.Print("") 
        self.Print("Start to verify data from LBA 0x0 to %s, expected data = %s"%(LBAptr, self.wPattern))
        TestSize = self.OneBlockSize*(LBAptr+1) # LBAptr start from 0
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
        PowerOffTimer = float(self.paraPwrOffDuration) / 1000 # convert int in minisecond to float in second
        self.spor_reset(showMsg=True, PowerOffDuration=PowerOffTimer)
        
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
        
        
        Timer =  randint(self.paraUGSDTimerMin, self.paraUGSDTimerMax) # millisecond
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
            
            if not self.NVMEwrite(randPattern, SLBA, Sector, RecordCmdToLogFile=isRecord, showMsg=True, OneBlockSize=self.OneBlockSize): 
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
        
    # for PLI ---------------------------------------------------------------------    
    def getDW10_DW11(self, slba):
        dw10=slba&0xFFFFFFFF
        dw11=slba>>32
        return dw10, dw11    
    
    def IdleForXmin(self):
        self.Print("Idle For %s seconds"%self.paraPLI_Time_Parameter)
        cnt = 0
        while True:
            sleep(1)
            cnt = cnt +1
            self.PrintProgressBar(cnt, self.paraPLI_Time_Parameter, prefix = 'Time:', length = 20)             
            if cnt >=self.paraPLI_Time_Parameter:
                break
        self.Print("Done")  
        return True    
    
    def TimeUpFunc(self):
        self.timeIsUp=True
        
    def RandReadXminMixOfSectorSizes(self):
        self.Print("Random read %s seconds (Mix of sector sizes)"%self.paraPLI_Time_Parameter )
        self.timeIsUp = False
        # thread, if time is up, run TimeUpFunc
        t =self.timeEvent(seconds = self.paraPLI_Time_Parameter, eventFunc = self.TimeUpFunc, printProgressBar = True)
        # set Last LBA for 4k align
        LastLBA = ((self.NCAP-self.MaxNLB)/8)*8
        while True:
            NLB=randint(1, self.MaxNLB)
            SLBA = randint(0, LastLBA)
            # set LBA for 4k align
            SLBA = (SLBA/8)*8
            CMD ="nvme read %s -s 0x%X -z 0x%X -c 0x%X 2>&1"%(self.dev, SLBA, self.OneBlockSize*(NLB+1), NLB)
            self.RecordCmdToLogFile = False
            mStr, SC=self.shell_cmd_with_sc(CMD) 
            self.RecordCmdToLogFile = True 
            # if read fail
            if (SC!=0):
                self.Print("Random read Fail, CMD: %s"%CMD, "f")
                self.Print("Return status: %s"%mStr, "f")
                # stop thread by setting self.timeEventTerminate
                if t.is_alive():
                    self.timeEventTerminate = True
                return False
            
            # if time up
            if self.timeIsUp:
                self.timeIsUp=False
                self.Print("Random read done!")
                return True
            
    def SeqWriteXmin256SectorTransfer(self):
        value =  randint(1, 0xFF)
        #self.MDTSinBlock=self.MDTSinByte/self.GetBlockSize()
        MaxNLB = self.MDTSinBlock
        self.Print("Sequential write %s seconds (256 Sector Transfer), value = 0x%X"%(self.paraPLI_Time_Parameter, value) )
        if MaxNLB<256:
            self.Print("Because MDTS in identify = %s bytes(%s block), so we can't transer 256 sector in 1 command"%(self.MDTSinByte, MaxNLB), "w")
            self.Print("so will transer %s sector in 1 command instead"%MaxNLB, "w")
        else:
            MaxNLB = 256
            
        self.timeIsUp = False
        # thread, if time is up, run TimeUpFunc
        t =self.timeEvent(seconds = self.paraPLI_Time_Parameter, eventFunc = self.TimeUpFunc, printProgressBar = True)
        # set Last LBA 
        LastLBA = self.NCAP - MaxNLB -1
        oct_val=oct(value)[-3:]
        SLBA = 0
        # write total byte
        writeBytes = self.OneBlockSize*MaxNLB
        while True:
            cdw10, cdw11=self.getDW10_DW11(SLBA)
            # count=256, -l 131072 for 256 sector            
            CMD="dd if=/dev/zero bs=%s count=%s 2>&1   |stdbuf -o %s tr \\\\000 \\\\%s 2>/dev/null "\
            "|nvme io-passthru %s -o 0x1 -n 1 -l %s -w --cdw10=%s --cdw11=%s --cdw12=%s 2>&1"\
            %(self.OneBlockSize, MaxNLB, writeBytes, oct_val, self.dev, writeBytes, cdw10, cdw11, MaxNLB-1)            
            # cal start lba for next loop
            SLBA = SLBA + MaxNLB
            if SLBA>LastLBA:
                pass
            SLBA = 0 if SLBA>LastLBA else SLBA
            
            self.RecordCmdToLogFile = False
            mStr, SC=self.shell_cmd_with_sc(CMD)
            self.RecordCmdToLogFile = True  
            # if write fail
            if (SC!=0):
                self.Print("Sequential write Fail, CMD: %s"%CMD, "f")
                self.Print("Return status: %s"%mStr, "f")
                # stop thread by setting self.timeEventTerminate
                if t.is_alive():
                    self.timeEventTerminate = True
                return False
            
            # if time up
            if self.timeIsUp:
                self.timeIsUp=False
                self.Print("Sequential write done!")
                return True            
    
    def ThreadTimeUpDoSpor(self, porTimer, msg):
        # convert to seconds 
        porTimer = float(porTimer) / 1000     
        sleep(porTimer)
        
        PowerOffTimer = float(self.paraPwrOffDuration) / 1000 # convert int in minisecond to float in second
        self.Print(msg)
        self.do_por_reset(mode = "spor", showMsg=True, PowerOffDuration=PowerOffTimer)
        self.timeIsUp=True
        
    def WritePLI(self):    
        BS = self.paraPLI_ReadWrite_sector * self.OneBlockSize
        VALUE =  randint(1, 0xFF)        
        SIZE = self.paraPLI_ReadWrite_size
        OFFSET =  randint(0, self.NCAP - self.paraPLI_ReadWrite_sizeInBLK) # total LBA - paraPLI_ReadWrite_sizeInBLK(ex, 1024k = 2048 lba for sector = 512) 
        OFFSET = OFFSET*self.OneBlockSize
        
        # 1 -------------------------
        self.Print("Write PLI. Step 1: Seq write (QD1)%sB with sector = %s, Start LBA = 0x%X, value = 0x%X"%(SIZE, self.paraPLI_ReadWrite_sector, OFFSET, VALUE))
        self.Print("Issue FIO command")

        CMD = "fio --direct=1 --iodepth=1 --ioengine=libaio --bs=%s --rw=write --numjobs=1 --size=%s --offset=%s "\
        "--filename=%s --name=mdata --do_verify=0 --verify=pattern --verify_pattern=%s 2>&1"%(BS, SIZE, OFFSET, self.dev, VALUE)

        mStr, SC=self.shell_cmd_with_sc(CMD)
        '''
        self.Print("-----------------------------------------------------------")
        self.Print(mStr)
        self.Print("-----------------------------------------------------------")
        '''
        # if fail
        if (SC!=0):
            self.Print("FIO Fail, CMD: %s"%CMD, "f")
            return False  
        else:
            self.Print("Done!", "p")
        
        # 2 -------------------------      
        self.Print("")    
        self.Print("Write PLI. Step 2: Seq read (QD1)%sB, Start LBA = 0x%X expected data = 0x%X "%(SIZE, OFFSET, VALUE))
        if self.fio_isequal(offset=OFFSET, size=SIZE, pattern=VALUE, printMsg=True):
            self.Print("Pass!", "p")
        else:
            self.Print("Fail!", "f")
            return False

        # 3 -------------------------
        self.Print("")
        self.Print("Write PLI. Step 3: Seq write (QD1)%sB, Going to keep writing LBA using FIO with sector = %s, Start LBA = 0x%X, value = 0x%X"%(SIZE, self.paraPLI_ReadWrite_sector, OFFSET, VALUE))
        porTimer =  randint(self.paraUGSDTimerMin, self.paraUGSDTimerMax) 
        
        
        self.Print("and powering disk off after %s ms"%porTimer)  
        self.Print("")
        
        self.timeIsUp=False
        # thread, if time is up, run ThreadTimeUpDoSpor
        msg = "Write PLI. Step 4: Unplanned Power Cycle, start to power disk off.."
        t = threading.Thread(target = self.ThreadTimeUpDoSpor, args=(porTimer, msg,))
        #t.daemon = True # The entire Python program exits when no alive non-daemon threads are left.
        t.start()        
        
        while True:
            #self.RecordCmdToLogFile = False
            mStr, SC=self.shell_cmd_with_sc(CMD)
            #self.RecordCmdToLogFile = True
            # if fail
            if (SC!=0):
                # check if device is missing(expect missing)
                if self.ctrl_alive:
                    self.Print("FIO read Fail", "w")
                    failMaxCnt = 5
                    while True:
                        if failMaxCnt==0: break
                        if not self.ctrl_alive: break
                        failMaxCnt -= 1                     
                                                
                        self.Print("devices is still alive(Linux may not update disk status after power off)", "w")
                        self.Print("issue 'echo 1 > /sys/bus/pci/rescan ' now and check again after 0.1s", "w")
                        self.shell_cmd("echo 1 > /sys/bus/pci/rescan ", 0.1)
                    
                    if not self.ctrl_alive:
                        self.Print("After rescan and wait 0.1s, devices is missing, keep going")
                    else:
                        self.Print("After rescan and wait 0.1s, devices is still alive, fail the test", "f")
                        t.join()
                        return False
                # end of check if device is missing(expect missing)   
                                
                self.Print("FIO write Failure as expected, device is missing(power off), wait for device power on", "p")
                #wait ThreadTimeUpDoSpor finish
                t.join()
                if self.ctrl_alive:
                    self.Print("Success to power disk on")
                else:
                    self.Print("Fail to power disk on, fail the test", "f")
                    return False                        
                break
            
            # if time up
            if self.timeIsUp:
                self.timeIsUp=False
                self.Print("time is up!")
                #wait ThreadTimeUpDoSpor finish
                t.join()                
                break        
        
        
        # 5 -------------------------
        self.Print("")
        self.Print("Write PLI. Step 5: ID Command")
        self.Print("Issue identify command for Identify Controller Data Structure")
        ID_CMD = "nvme id-ctrl %s"%self.dev
        mStr, SC=self.shell_cmd_with_sc(ID_CMD)
        self.Print("Return Status Code: 0x%X"%SC)
        self.Print("Check if Return Status Code=0")
        if (SC==0):
            self.Print("Pass", "p")
        else:
            self.Print("Fail, status: %s"%mStr, "f")
            return False        
                
        # 6 -------------------------
        self.Print("")    
        self.Print("Write PLI. Step 6: Seq read (QD1)%sB, Start LBA = 0x%X expected data = 0x%X "%(SIZE, OFFSET, VALUE))
        if self.fio_isequal(offset=OFFSET, size=SIZE, pattern=VALUE, printMsg=True):
            self.Print("Pass!", "p")
        else:
            self.Print("Fail!", "f")
            return False

    def ReadPLI(self):    
        BS = self.paraPLI_ReadWrite_sector * self.OneBlockSize
        VALUE =  randint(1, 0xFF)        
        SIZE = "8M"
        SizeInBLK = self.KMGT_reverse(SIZE)
        OFFSET =  randint(0, self.NCAP - SizeInBLK) # total LBA - paraPLI_ReadWrite_sizeInBLK(ex, 1024k = 2048 lba for sector = 512) 
        OFFSET = OFFSET*self.OneBlockSize
        
        # 1 -------------------------
        self.Print("Read PLI. Step 1: Seq write (QD1)%sB with sector = %s, Start LBA = 0x%X, value = 0x%X"%(SIZE, self.paraPLI_ReadWrite_sector, OFFSET, VALUE))
        self.Print("Issue FIO command")

        CMD = "fio --direct=1 --iodepth=1 --ioengine=libaio --bs=%s --rw=write --numjobs=1 --size=%s --offset=%s "\
        "--filename=%s --name=mdata --do_verify=0 --verify=pattern --verify_pattern=%s 2>&1"%(BS, SIZE, OFFSET, self.dev, VALUE)

        mStr, SC=self.shell_cmd_with_sc(CMD)
        '''
        self.Print("-----------------------------------------------------------")
        self.Print(mStr)
        self.Print("-----------------------------------------------------------")
        '''
        # if fail
        if (SC!=0):
            self.Print("FIO Fail, CMD: %s"%CMD, "f")
            return False  
        else:
            self.Print("Done!", "p")
        
        # 2 -------------------------      
        self.Print("")    
        self.Print("Read PLI. Step 2: Seq read (QD1)%sB, Start LBA = 0x%X expected data = 0x%X "%(SIZE, OFFSET, VALUE))
        if self.fio_isequal(offset=OFFSET, size=SIZE, pattern=VALUE, printMsg=True):
            self.Print("Pass!", "p")
        else:
            self.Print("Fail!", "f")
            return False

        # 3 -------------------------
        self.Print("")
        self.Print("Read PLI. Step 3: Seq read (QD1)%sB, Going to keep reading LBAs using FIO , Start LBA = 0x%X"%(SIZE, OFFSET))
        porTimer =  randint(self.paraUGSDTimerMin, self.paraUGSDTimerMax) 
        
        
        self.Print("and powering disk off after %s ms"%porTimer)  
        self.Print("")
        
        self.timeIsUp=False
        # thread, if time is up, run ThreadTimeUpDoSpor
        msg = "Read PLI. Step 4: Unplanned Power Cycle, start to power disk off.."
        t = threading.Thread(target = self.ThreadTimeUpDoSpor, args=(porTimer, msg,))
        #t.daemon = True # The entire Python program exits when no alive non-daemon threads are left.
        t.start()        
        
        CMD = "fio --direct=1 --iodepth=1 --ioengine=libaio --bs=%s --rw=read --numjobs=1 --size=%s --offset=%s "\
        "--filename=%s --name=mdata --do_verify=0 2>&1"%(BS, SIZE, OFFSET, self.dev)        
        while True:
            #self.RecordCmdToLogFile = False
            mStr, SC=self.shell_cmd_with_sc(CMD)
            #self.RecordCmdToLogFile = True
            # if fail
            if (SC!=0):
                # check if device is missing(expect missing)
                if self.ctrl_alive:
                    self.Print("FIO read Fail", "w")
                    failMaxCnt = 5
                    while True:
                        if failMaxCnt==0: break
                        if not self.ctrl_alive: break
                        failMaxCnt -= 1                     
                                                
                        self.Print("devices is still alive(Linux may not update disk status after power off)", "w")
                        self.Print("issue 'echo 1 > /sys/bus/pci/rescan ' now and check again after 0.1s", "w")
                        self.shell_cmd("echo 1 > /sys/bus/pci/rescan ", 0.1)
                    
                    if not self.ctrl_alive:
                        self.Print("After rescan and wait 0.1s, devices is missing, keep going")
                    else:
                        self.Print("After rescan and wait 0.1s, devices is still alive, fail the test", "f")
                        t.join()
                        return False
                # end of check if device is missing(expect missing)     
                
                self.Print("FIO read Failure as expected, device is missing(power off), wait for device power on", "p")
                #wait ThreadTimeUpDoSpor finish
                t.join()
                if self.ctrl_alive:
                    self.Print("Success to power disk on")
                else:
                    self.Print("Fail to power disk on, fail the test", "f")
                    return False                        
                break
            
            # if time up
            if self.timeIsUp:
                self.timeIsUp=False
                self.Print("time is up!")
                #wait ThreadTimeUpDoSpor finish
                t.join()                
                break        
        
        
        # 5 -------------------------
        self.Print("")
        self.Print("Read PLI. Step 5: ID Command")
        self.Print("Issue identify command for Identify Controller Data Structure")
        ID_CMD = "nvme id-ctrl %s"%self.dev
        mStr, SC=self.shell_cmd_with_sc(ID_CMD)
        self.Print("Return Status Code: 0x%X"%SC)
        self.Print("Check if Return Status Code=0")
        if (SC==0):
            self.Print("Pass", "p")
        else:
            self.Print("Fail, status: %s"%mStr, "f")
            return False        
                
        # 6 -------------------------
        self.Print("")    
        self.Print("Read PLI. Step 6: Seq read (QD1)%sB, Start LBA = 0x%X expected data = 0x%X "%(SIZE, OFFSET, VALUE))
        if self.fio_isequal(offset=OFFSET, size=SIZE, pattern=VALUE, printMsg=True):
            self.Print("Pass!", "p")
        else:
            self.Print("Fail!", "f")
            return False
    
    def doSmartCheck(self):
        rtCode = True
        self.cntSmartCheck = self.cntSmartCheck +1
        fileName = "smartCheck_%s.txt"%self.cntSmartCheck
        fulllPath = "%s/%s"%(self.SmartCheck.historyLogDir, fileName)
        if not self.SmartCheck.SmartCheckModuleExist:
            self.Print("Can't find smart check module!", "f")
            rtCode = False
        else:
            if self.SmartCheck.isRunOncePass(DisplayOption = self.paraSmartDisplay, HistoryLogFileName = fileName):
                self.Print("Check SMART: Pass(%s)"%fulllPath, "p")
                rtCode = True
            else:
                self.Print("Check SMART: Fail(%s)"%fulllPath, "f")
                self.Print("Please check SMART log file: %s"%fulllPath, "f")
                rtCode = False     
                
            
            
        return rtCode           
        
    def RunPLIflow(self, loop):
        result = True
        if self.paraSKIP_INTEL_PLI_PRECONDITION=="No" and loop==1:
            self.Print("Loop=1 and SKIP_INTEL_PLI_PRECONDITION =No, write 0x0 to entire disk!")
            if not self.fio_precondition(pattern = 0, showProgress= True):
                self.Print("Fail to do precondition!", "f")
                return False
            self.Print("Done")        
        
        self.Print("-----------------------------------------------------", "b")
        if (loop % 3)==0:
            self.Print("Loop: %s,  IdleForXmin"%loop, "p")
            self.SetPrintOffset(4)
            if not self.doSmartCheck(): return False    # check smart log
            result = self.IdleForXmin()
            if not self.doSmartCheck(): return False
            self.SetPrintOffset(0)
        elif  (loop % 3)==1:
            self.Print("Loop: %s,  RandReadXminMixOfSectorSizes"%loop, "p")        
            self.SetPrintOffset(4)      
            if not self.doSmartCheck(): return False
            result = self.RandReadXminMixOfSectorSizes()
            if not self.doSmartCheck(): return False
            self.SetPrintOffset(0)
        else:
            self.Print("Loop: %s,  SeqWriteXmin256SectorTransfer"%loop, "p")  
            self.SetPrintOffset(4)
            if not self.doSmartCheck(): return False
            result = self.SeqWriteXmin256SectorTransfer()
            if not self.doSmartCheck(): return False
            self.SetPrintOffset(0)

        if result ==False:
            return False
        
        # if Loop/3 is even
        if (loop / 3) % 2 ==0: 
            self.Print("Loop: %s,  WritePLI"%loop, "p")  
            self.SetPrintOffset(4)              
            if not self.doSmartCheck(): return False  
            result = self.WritePLI()
            if not self.doSmartCheck(): return False
            self.SetPrintOffset(0)
        # else Loop/3 is not even
        else:
            self.Print("Loop: %s,  ReadPLI"%loop, "p")
            self.SetPrintOffset(4)
            if not self.doSmartCheck(): return False
            result = self.ReadPLI()
            if not self.doSmartCheck(): return False
            self.SetPrintOffset(0)
            
        if result ==False:
            return False


        
        return True                
    # end of for PLI ---------------------------------------------------------------------
        
    
    def __init__(self, argv):
        # initial parameter
        self.SetDynamicArgs(optionName="pcm", optionNameFull="PwrCycleMode", \
                            helpMsg="PwrCycleMode\n0=Ungraceful\n1=Graceful\n2=Intel PLI test"\
                            "\ne.x. for Ungraceful test '--PwrCycleMode 0'", argType=int, default=1,\
                            iniFileName="SMI_Power_Cycle_Test_ini/SMIPowerCycleTest.ini", iniSectionName="None", iniOptionName="PwrCycleMode")        
        
        self.SetDynamicArgs(optionName="tl", optionNameFull="TestLoop", \
                            helpMsg="number of loops, if TestLoop=0 means infinity loop, "
                            "\ne.x. '--TestLoop 1'", argType=int, default=1,\
                            iniFileName="SMI_Power_Cycle_Test_ini/SMIPowerCycleTest.ini", iniSectionName="None", iniOptionName="TestLoop")
        
        self.SetDynamicArgs(optionName="utmin", optionNameFull="UGSDTimerMin", \
                            helpMsg="Power Off Timer minium in minisecond"
                            "\ne.x. '--UGSDTimerMin 1000'", argType=int, default=1000,\
                            iniFileName="SMI_Power_Cycle_Test_ini/SMIPowerCycleTest.ini", iniSectionName="None", iniOptionName="UGSDTimerMin")
        
        self.SetDynamicArgs(optionName="utmax", optionNameFull="UGSDTimerMax", \
                            helpMsg="Power Off Timer maxium in minisecond"
                            "\ne.x. '--UGSDTimerMax 4000'", argType=int, default=4000,\
                            iniFileName="SMI_Power_Cycle_Test_ini/SMIPowerCycleTest.ini", iniSectionName="None", iniOptionName="UGSDTimerMax")
        
        self.SetDynamicArgs(optionName="pod", optionNameFull="PwrOffDuration", \
                            helpMsg="Power Off Duration in minisecond, "
                            "\ne.x. '--PwrOffDuration 5000'", argType=int, default=5000,\
                            iniFileName="SMI_Power_Cycle_Test_ini/SMIPowerCycleTest.ini", iniSectionName="None", iniOptionName="PwrOffDuration")
        
        self.SetDynamicArgs(optionName="eugmt", optionNameFull="ENABLE_UGSD_GSD_MIXED_TEST", \
                            helpMsg="ENABLE_UGSD_GSD_MIXED_TEST, [Yes,No]"\
                            "\nif yes, will mix Ungraceful and Graceful test when PwrCycleMode = 0(Ungraceful) or 1(Graceful)"\
                            "\ne.x. '--ENABLE_UGSD_GSD_MIXED_TEST Yes'", argType=str, default=5000,\
                            iniFileName="SMI_Power_Cycle_Test_ini/Setup.ini", iniSectionName="Setup", iniOptionName="ENABLE_UGSD_GSD_MIXED_TEST")        
        # 6
        self.SetDynamicArgs(optionName="ptp", optionNameFull="PLI_Time_Parameter", \
                            helpMsg="PwrCycleMode-> Intel PLI test:  idle/randRead/seqWrite time in seconds"\
                            "\ne.x. '--PLI_Time_Parameter 300'"\
                            "\ndefault = '300' (5 minutes)", argType=int, default=300)

        self.SetDynamicArgs(optionName="prwse", optionNameFull="PLI_ReadWrite_sector", \
                            helpMsg="PwrCycleMode-> Intel PLI test:  sector size for step 'Read PLI' and 'Write PLI'"\
                            "\ne.x. '--PLI_ReadWrite_sector 256'"\
                            "\ndefault = '256' (256 block for 1 read/write command)", argType=int, default=256)
        # 8
        self.SetDynamicArgs(optionName="prwsi", optionNameFull="PLI_ReadWrite_size", \
                            helpMsg="PwrCycleMode-> Intel PLI test: total size for step 'Read PLI' and 'Write PLI'"\
                            "\ne.x. '--PLI_ReadWrite_size 800M'"\
                            "\ndefault = '800M' (800M will be read/write for step 'Read PLI' and write for step 'Write PLI')", argType=str, default="800M")            
        # 9
        self.SetDynamicArgs(optionName="sipp", optionNameFull="SKIP_INTEL_PLI_PRECONDITION", \
                            helpMsg="SKIP_INTEL_PLI_PRECONDITION [Yes, No], "
                            "\ne.x. '--SKIP_INTEL_PLI_PRECONDITION Yes'", argType=str, default="No",\
                            iniFileName="SMI_Power_Cycle_Test_ini/Setup.ini", iniSectionName="Setup", iniOptionName="SKIP_INTEL_PLI_PRECONDITION")  
        
        self.SetDynamicArgs(optionName="smartdisplay", optionNameFull="SmartDisplay",\
                             helpMsg="Smart log display option[console, newtab, newconsole, gui, no]"\
                             "\n'-smartdisplay console', display smart log in current console"\
                             "\n'-smartdisplay newtab', display smart log in new tab"\
                             "\n'-smartdisplay newconsole', display smart log in new console"\
                             "\n'-smartdisplay gui', display smart log with GUI if tkinter was installed, else display smart log in new console"\
                             "\n'-smartdisplay no', will check smart log but hide log output"\
                             "\ndefault = 'console'"\
                             , argType=str, default="console")
                 
        self.SetDynamicArgs(optionName="epc", optionNameFull="ENABLE_PRECONDITION", \
                            helpMsg="ENABLE_PRECONDITION [Yes, No], "
                            "\ne.x. '--ENABLE_PRECONDITION Yes'", argType=str, default="Yes",\
                            iniFileName="SMI_Power_Cycle_Test_ini/Setup.ini", iniSectionName="Setup", iniOptionName="ENABLE_PRECONDITION")

        self.SetDynamicArgs(optionName="psl", optionNameFull="PRECONDITION_START_LBA", \
                            helpMsg="PRECONDITION_START_LBA, "
                            "\ne.x. '--PRECONDITION_START_LBA 0'", argType=int, default=0,\
                            iniFileName="SMI_Power_Cycle_Test_ini/Setup.ini", iniSectionName="Setup", iniOptionName="PRECONDITION_START_LBA")  
        
        self.SetDynamicArgs(optionName="pel", optionNameFull="PRECONDITION_END_LBA", \
                            helpMsg="PRECONDITION_END_LBA [interger], "
                            "\ne.x. '--PRECONDITION_END_LBA 2000000'", argType=int, default=2000000,\
                            iniFileName="SMI_Power_Cycle_Test_ini/Setup.ini", iniSectionName="Setup", iniOptionName="PRECONDITION_END_LBA")  
               

        
         
        # initial parent class
        super(SMI_Power_Cycle_Test, self).__init__(argv)

        self.paraPwrCycleMode = self.GetDynamicArgs(0) 
        self.paraTestLoop = self.GetDynamicArgs(1) 
        self.paraUGSDTimerMin = self.GetDynamicArgs(2)
        self.paraUGSDTimerMax = self.GetDynamicArgs(3)                 
        self.paraPwrOffDuration = self.GetDynamicArgs(4) # int in minisecond
        self.paraENABLE_UGSD_GSD_MIXED_TEST = self.GetDynamicArgs(5)   
        self.paraPLI_Time_Parameter = self.GetDynamicArgs(6) 
        self.paraPLI_ReadWrite_sector = self.GetDynamicArgs(7)         
        self.paraPLI_ReadWrite_size = self.GetDynamicArgs(8)    
        self.paraSKIP_INTEL_PLI_PRECONDITION = self.GetDynamicArgs(9) 
        self.paraSmartDisplay = self.GetDynamicArgs(10)    
        
        self.paraENABLE_PRECONDITION = self.GetDynamicArgs(11)     
        self.paraPRECONDITION_START_LBA = self.GetDynamicArgs(12)     
        self.paraPRECONDITION_END_LBA = self.GetDynamicArgs(13)     
        
        
        
        

         
        

        self.NCAP=self.IdNs.NCAP.int
        self.wPattern = 0

        self.MaxNLB = self.MaxNLBofCDW12()   
        self.OneBlockSize = self.GetBlockSize()
        self.paraPLI_ReadWrite_sizeInBLK = self.KMGT_reverse(self.paraPLI_ReadWrite_size, self.OneBlockSize)# get number of blocks        
        self.timeIsUp = False
        self.cntSmartCheck = 0

        
        # device infor 
        self.Print("")
        self.Print("-- DUT infomations ----")
        self.Print ("NCAP: 0x%X"%self.NCAP)
        self.Print("DUT sector sizes(1 Block): %s bytes"%(self.OneBlockSize))
        self.Print ("Maximum Data Transfer Size (MDTS): 0x%X bytes"%self.MDTSinByte)
        self.Print("DUT read/write command Maximum Sector(MTDS/DUT sector sizes): %s"%(self.MDTSinBlock))               

    # define pretest, if not return 0 , skip all subcases
    def PreTest(self):   
        # PLI test
        if self.paraPwrCycleMode == 2:
            if self.paraPLI_ReadWrite_sizeInBLK>self.NCAP:
                self.Print("Fail, parameter '-size %s' exceed disk capacity(0x%X > 0x%X), exit"%(self.paraPLI_ReadWrite_size, self.paraPLI_ReadWrite_sizeInBLK, self.NCAP), "f") 
                self.Print("For more infomation, run 'python SMI_Power_Cycle_Test.py'", "f")
                return 1
            
            if self.paraUGSDTimerMin>=self.paraUGSDTimerMax:
                self.Print("Fail, parameter  Power Off Timer incorrect, %s, %s , exit"%(self.paraUGSDTimerMin, self.paraUGSDTimerMax), "f")    
                self.Print("For more infomation, run 'python SMI_Power_Cycle_Test.py'", "f")    
                return 1              
            if self.paraPLI_ReadWrite_sector>self.MDTSinBlock:
                self.Print("Warnning, parameter  Write/Read LPI number of sector(-sector) incorrect(value = %s),"\
                           " can't exceed DUT Maximum Data Transfer Size(%s) "%(self.paraPLI_ReadWrite_sector, self.MDTSinBlock), "w")   
                self.Print("so parameter Write/Read LPI number of sector(-sector) will be modified from %s to %s"%(self.paraPLI_ReadWrite_sector, self.MDTSinBlock), "w")
                self.paraPLI_ReadWrite_sector = self.MDTSinBlock
                self.Print("For more infomation, run 'python SMI_Power_Cycle_Test.py'", "f")        
        return 0            

    # <define sub item scripts>
    SubCase1TimeOut = 0
    SubCase1Desc = "SMI_Power_Cycle_Test"   
    SubCase1KeyWord = ""
    def SubCase1(self):
        ret_code=0




        loop = 0
        while True:
            loop = loop +1
            if (loop > self.paraTestLoop) and (self.paraTestLoop!=0): break
            if loop%20==1 and loop!=1: self.SplitLog() # split log every 20 loops  
            self.PrintLoop = loop
            
            if self.paraENABLE_PRECONDITION=="Yes" and loop==1:
                value = randint(1, 0xFE)
                self.Print("ENABLE_PRECONDITION==Yes and loop==1, do precondition, SLBA=%s, ELBA=%s, value = %s"\
                           %(self.paraPRECONDITION_START_LBA, self.paraPRECONDITION_END_LBA, value), "b")
                self.fio_precondition(pattern=value, fio_direct=1, showProgress=True, \
                                      slba=self.paraPRECONDITION_START_LBA, elba=self.paraPRECONDITION_END_LBA, OneBlockSize=self.OneBlockSize)
                self.Print("Done")   
                self.Print("")          
            
            # (Ungraceful or gracefull) and ENABLE_UGSD_GSD_MIXED_TEST = Yes, do "UGSD GSD Mix"  
            if (self.paraPwrCycleMode==0 or self.paraPwrCycleMode==1) and self.paraENABLE_UGSD_GSD_MIXED_TEST=="Yes": # Ungraceful
                if not self.doSmartCheck(): return False    # check smart log
                if loop%2==1:
                    if not self.UGSD(): 
                        ret_code=1
                        break
                else:
                    if not self.GSD(): 
                        ret_code=1
                        break
            
            # Ungraceful
            elif self.paraPwrCycleMode==0: 
                if not self.doSmartCheck(): return False    # check smart log
                if not self.UGSD(): 
                    ret_code=1
                    break
                
            # Graceful
            elif self.paraPwrCycleMode==1: 
                if not self.doSmartCheck(): return False    # check smart log
                if not self.GSD(): 
                    ret_code=1
                    break
                
            # PLI, note that checking smart log will do in RunPLIflow()
            elif self.paraPwrCycleMode==2: 
                if not self.RunPLIflow(loop): 
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

    
    
    
    