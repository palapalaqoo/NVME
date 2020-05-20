#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
import re
from time import sleep
from random import randint
import threading

# Import VCT modules
from lib_vct.NVME import NVME

class SMI_PLI(NVME):
    ScriptName = "SMI_PLI.py"
    Author = ""
    Version = ""

    def getDW10_DW11(self, slba):
        dw10=slba&0xFFFFFFFF
        dw11=slba>>32
        return dw10, dw11    
    
    def IdleForXmin(self):
        self.Print("Idle For %s seconds"%self.paraSecond)
        cnt = 0
        while True:
            sleep(1)
            cnt = cnt +1
            self.PrintProgressBar(cnt, self.paraSecond, prefix = 'Time:', length = 20)             
            if cnt >=self.paraSecond:
                break
        self.Print("Done")  
        return True    
    
    def TimeUpFunc(self):
        self.timeIsUp=True
        
    def RandReadXminMixOfSectorSizes(self):
        self.Print("Random read %s seconds (Mix of sector sizes)"%self.paraSecond )
        self.timeIsUp = False
        # thread, if time is up, run TimeUpFunc
        t =self.timeEvent(seconds = self.paraSecond, eventFunc = self.TimeUpFunc, printProgressBar = True)
        # set Last LBA for 4k align
        LastLBA = ((self.NCAP-self.MaxNLB)/8)*8
        while True:
            NLB=randint(1, self.MaxNLB)
            SLBA = randint(0, LastLBA)
            # set LBA for 4k align
            SLBA = (SLBA/8)*8
            CMD ="nvme read %s -s 0x%X -z 0x%X -c 0x%X 2>&1"%(self.dev, SLBA, self.OneBlockSize*(NLB+1), NLB)
            mStr, SC=self.shell_cmd_with_sc(CMD)  
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
        self.Print("Sequential write %s seconds (256 Sector Transfer), value = 0x%X"%(self.paraSecond, value) )
        self.timeIsUp = False
        # thread, if time is up, run TimeUpFunc
        t =self.timeEvent(seconds = self.paraSecond, eventFunc = self.TimeUpFunc, printProgressBar = True)
        # set Last LBA 
        LastLBA = self.NCAP - 256 -1
        oct_val=oct(value)[-3:]
        SLBA = 0
        while True:
            cdw10, cdw11=self.getDW10_DW11(SLBA)
            # count=256, -l 131072 for 256 sector
            CMD="dd if=/dev/zero bs=512 count=256 2>&1   |stdbuf -o 131072 tr \\\\000 \\\\%s 2>/dev/null "\
            "|nvme io-passthru %s -o 0x1 -n 1 -l 131072 -w --cdw10=%s --cdw11=%s --cdw12=255 2>&1"%(oct_val, self.dev, cdw10, cdw11)            
            # cal start lba for next loop
            SLBA = SLBA + 256
            if SLBA>LastLBA:
                pass
            SLBA = 0 if SLBA>LastLBA else SLBA
            
            mStr, SC=self.shell_cmd_with_sc(CMD)  
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
        self.Print(msg)
        self.do_por_reset("spor")
        self.timeIsUp=True
        
    def WritePLI(self):    
        BS = 512 * self.paraLPISector
        VALUE =  randint(1, 0xFF)        
        SIZE = self.paraLPISize
        OFFSET =  randint(0, self.NCAP - self.paraLPISizeInBLK) # total LBA - paraLPISizeInBLK(ex, 1024k = 2048 lba) 
        OFFSET = OFFSET*512
        
        # 1 -------------------------
        self.Print("Write PLI. Step 1: Seq write (QD1)%sB with sector = %s, Start LBA = 0x%X, value = 0x%X"%(SIZE, self.paraLPISector, OFFSET, VALUE))
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
        self.Print("Write PLI. Step 3: Seq write (QD1)%sB, Going to keep writing LBA using FIO with sector = %s, Start LBA = 0x%X, value = 0x%X"%(SIZE, self.paraLPISector, OFFSET, VALUE))
        porTimer =  randint(self.paraPorOffTimer0, self.paraPorOffTimer1) 
        
        
        self.Print("and powering disk off after %s ms"%porTimer)  
        self.Print("")
        
        self.timeIsUp=False
        # thread, if time is up, run ThreadTimeUpDoSpor
        msg = "Write PLI. Step 4: Unplanned Power Cycle, start to power disk off.."
        t = threading.Thread(target = self.ThreadTimeUpDoSpor, args=(porTimer, msg,))
        #t.daemon = True # The entire Python program exits when no alive non-daemon threads are left.
        t.start()        
        
        while True:
            mStr, SC=self.shell_cmd_with_sc(CMD)
            # if fail
            if (SC!=0):
                sleep(1) # sleep 1 s to prevent /dev/nvme0n1 is exist after spor
                if self.dev_alive:
                    self.Print("FIO write Fail, devices is still alive, fail the test", "f")
                    t.join()
                    return False
                else:
                    self.Print("FIO write Failure as expected, device is missing(power off), wait for device power on", "p")
                    #wait ThreadTimeUpDoSpor finish
                    t.join()
                    if self.dev_alive:
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
        BS = 512 * self.paraLPISector
        VALUE =  randint(1, 0xFF)        
        SIZE = "8M"
        SizeInBLK = self.KMGT_reverse(SIZE)
        OFFSET =  randint(0, self.NCAP - SizeInBLK) # total LBA - paraLPISizeInBLK(ex, 1024k = 2048 lba) 
        OFFSET = OFFSET*512
        
        # 1 -------------------------
        self.Print("Read PLI. Step 1: Seq write (QD1)%sB with sector = %s, Start LBA = 0x%X, value = 0x%X"%(SIZE, self.paraLPISector, OFFSET, VALUE))
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
        porTimer =  randint(self.paraPorOffTimer0, self.paraPorOffTimer1) 
        
        
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
            mStr, SC=self.shell_cmd_with_sc(CMD)
            # if fail
            if (SC!=0):
                if self.dev_alive:
                    self.Print("FIO read Fail, devices is still alive, fail the test", "f")
                    t.join()
                    return False
                else:
                    self.Print("FIO read Failure as expected, device is missing(power off), wait for device power on", "p")
                    #wait ThreadTimeUpDoSpor finish
                    t.join()
                    if self.dev_alive:
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
        
    def RunFlow(self):
        result = True
        for loop in range(1, self.loops+1):
            self.Print("-----------------------------------------------------", "b")
            if (loop % 3)==0:
                self.Print("Loop: %s,  IdleForXmin"%loop, "p")
                self.SetPrintOffset(4)
                result = self.IdleForXmin()
                self.SetPrintOffset(0)
            elif  (loop % 3)==1:
                self.Print("Loop: %s,  RandReadXminMixOfSectorSizes"%loop, "p")        
                self.SetPrintOffset(4)      
                result = self.RandReadXminMixOfSectorSizes()
                self.SetPrintOffset(0)
            else:
                self.Print("Loop: %s,  SeqWriteXmin256SectorTransfer"%loop, "p")  
                self.SetPrintOffset(4)
                result = self.SeqWriteXmin256SectorTransfer()
                self.SetPrintOffset(0)

            if result ==False:
                return False
            
            # if Loop/3 is even
            if (loop / 3) % 2 ==0: 
                self.Print("Loop: %s,  WritePLI"%loop, "p")  
                self.SetPrintOffset(4)                
                result = self.WritePLI()
                self.SetPrintOffset(0)
            # else Loop/3 is not even
            else:
                self.Print("Loop: %s,  ReadPLI"%loop, "p")
                self.SetPrintOffset(4)
                result = self.ReadPLI()
                self.SetPrintOffset(0)
                
            if result ==False:
                return False
        
        return True                
    
    
    def __init__(self, argv):
        self.SetDynamicArgs(optionName="l", optionNameFull="loops", helpMsg="number of loops, default = 1", argType=int)
        self.SetDynamicArgs(optionName="s0", optionNameFull="secondParameter0", helpMsg="seconds for idle/randRead/seqWrite, default = '300' (5 minutes)", argType=int)
        self.SetDynamicArgs(optionName="sector", optionNameFull="WriteRead_LPI_sector", helpMsg="Write/Read LPI sector, default = '256'", argType=int)
        self.SetDynamicArgs(optionName="size", optionNameFull="WriteRead_LPI_size", helpMsg="Write/Read LPI size, default = '800M'", argType=str)
        self.SetDynamicArgs(optionName="t0", optionNameFull="PorOffTimer0", helpMsg="Power Off Timer minium in millisecond, default = 2000", argType=int)
        self.SetDynamicArgs(optionName="t1", optionNameFull="PorOffTimer1", helpMsg="Power Off Timer maxium in millisecond, default = 4000", argType=int)
        
        
        # initial parent class
        super(SMI_PLI, self).__init__(argv)
        
        self.loops = self.GetDynamicArgs(0) 
        self.loops=1 if self.loops==None else self.loops  
              
        self.paraSecond = self.GetDynamicArgs(1) 
        self.paraSecond=300 if self.paraSecond==None else self.paraSecond
        
        self.paraLPISector = self.GetDynamicArgs(2) 
        self.paraLPISector=256 if self.paraLPISector==None else self.paraLPISector        
        
        self.paraLPISize = self.GetDynamicArgs(3) 
        self.paraLPISize=256 if self.paraLPISize==None else self.paraLPISize 
        self.paraLPISizeInBLK = self.KMGT_reverse(self.paraLPISize)    
        
        self.paraPorOffTimer0 = self.GetDynamicArgs(4) 
        self.paraPorOffTimer0=2000 if self.paraPorOffTimer0==None else self.paraPorOffTimer0       
        
        self.paraPorOffTimer1 = self.GetDynamicArgs(5) 
        self.paraPorOffTimer1=4000 if self.paraPorOffTimer1==None else self.paraPorOffTimer1                                  
        
        self.NCAP=self.IdNs.NCAP.int  
        self.MaxNLB = self.MaxNLBofCDW12()   
        self.OneBlockSize = self.GetBlockSize()
        
        self.timeIsUp = False
        

    # define pretest, if not return 0 , skip all subcases
    def PreTest(self):       
        self.Print("Total test loop: %s "%self.loops)
        self.Print ("Time for idle/randRead/seqWrite: %s seconds"%self.paraSecond)
        self.Print ("Write/Read LPI sector: %s "%self.paraLPISector)        
        self.Print ("Write/Read LPI size: %s (0x%X LBA)"%(self.paraLPISize, self.paraLPISizeInBLK))          
        self.Print ("Power Off Timer from %s ms to %s ms"%(self.paraPorOffTimer0, self.paraPorOffTimer1))         
        
        # device infor
        self.Print ("NCAP: 0x%X"%self.NCAP)     
        self.Print("Max of sector sizes: %s x %s bytes"%(self.MaxNLB, self.OneBlockSize))
        
        
        if self.paraLPISizeInBLK>self.NCAP:
            self.Print("Fail, input parameter '-size %s' exceed disk capacity(0x%X > 0x%X), exit"%(self.paraLPISize, self.paraLPISizeInBLK, self.NCAP), "f")        
            return 1
        
        if self.paraPorOffTimer0>=self.paraPorOffTimer1:
            self.Print("Fail, input parameter  Power Off Timer incorrect, %s, %s , exit"%(self.paraPorOffTimer0, self.paraPorOffTimer1), "f")        
            return 1                 
        return 0            

    # <define sub item scripts>
    SubCase1TimeOut = 600000
    SubCase1Desc = "Intel PLI test"   
    SubCase1KeyWord = ""
    def SubCase1(self):
        ret_code=0
        try:
            self.RunFlow()
        except KeyboardInterrupt:
            self.Print("")
            self.Print("Detect ctrl+C, quit test case")  
            self.timeEventTerminate = True          
        return ret_code

    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_PLI(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    