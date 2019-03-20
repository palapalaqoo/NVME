#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
import time
from time import sleep
import re
import os
import csv
import shutil
from random import randint
# Import VCT modules
from lib_vct.NVME import NVME

'''
def my_decorator(func):
    def wrapped_func(*args,**kwargs):
        return func("I've been decorated!",*args,**kwargs)
    return wrapped_func
'''
class Test(NVME):


    def GetFWVer(self):
        FirmwareSlotInformationLog = self.get_log2byte(3, 64)
        AFI=FirmwareSlotInformationLog[0]
        ActiveFirmwareSlot= int(AFI, 16)&0b00000111
        FWVer=""
        for i in range(8):
            FWVer=FWVer+chr(int(FirmwareSlotInformationLog[i+ActiveFirmwareSlot*8], 16))
            
        return FWVer
    
    
    
    def write1block(self, value, block, nsid=1):
        # write 1 block data, ex, nvme_write_1_block(0x32,0)
        # if csts.rdy=0, return false
        # value, value to write        
        # block, block to  write  
        '''
        oct_val=oct(value)[-3:]
        if self.dev_alive and self.status=="normal":
            self.shell_cmd("  buf=$(dd if=/dev/zero bs=512 count=1 2>&1   |tr \\\\000 \\\\%s 2>/dev/null | nvme write %s --start-block=%s --data-size=512 2>&1 > /dev/null) "%(oct_val, self.dev, block))   
        else:
            return False
        '''
        
        oct_val=oct(value)[-3:]
        #if self.dev_alive and self.status=="normal":  
                 
        slba=block
        cdw10=slba&0xFFFFFFFF
        cdw11=slba>>32    
        mStr=self.shell_cmd("dd if=/dev/zero bs=512 count=1 2>&1   |tr \\\\000 \\\\%s 2>/dev/null |nvme io-passthru %s -o 0x1 -n %s -l 512 -w --cdw10=%s --cdw11=%s 2>&1"%(oct_val, self.dev, nsid, cdw10, cdw11))
            #retCommandSueess=bool(re.search("NVMe command result:00000000", mStr))
        return mStr

    def FindPatten(self, offset, size, SearchPatten):
        #return string, if no finding, return ""
        # example:       '00ba000 cdcd cdcd cdcd cdcd cdcd cdcd cdcd cdcd'  
        # SearchPatten = 0xcd, and return 0x00ba000
        find=""
        HexPatten = format(SearchPatten, '02x')
        buf=self.shell_cmd("hexdump %s -n %s -s %s 2>/dev/null"%(self.dev, size, offset,  )) 
        # example:       '00ba000 cdcd cdcd cdcd cdcd cdcd cdcd cdcd cdcd'  
        mStr="[^\n](\w*)%s"%((" "+HexPatten*2)*8)
        if re.search(mStr, buf):       
            find="0x"+re.search(mStr, buf).group(1)   
        return find         


    def CreateLBARangeDataStructure(self, NumOfEntrys):
        # create multi entry of LBARangeDataStructure
        # return string , ex "\\255\\12\\78\\ .."
        mStr=""
        for entry in range(NumOfEntrys):        
            self.LBARangeDataStructure.Type=0x2
            self.LBARangeDataStructure.Attributes=0x1
            self.LBARangeDataStructure.SLBA=entry*8
            self.LBARangeDataStructure.NLB=7
            self.LBARangeDataStructure.CreatePattern()
            # save created string to mStr
            mStr = mStr + self.LBARangeDataStructure.Pattern
            
        return mStr

    def nvme_reset(self):
        self.status="reset"
        #implement in SMI_NVMEReset.py
        CC= self.MemoryRegisterBaseAddress+0x14
        CChex=hex(CC)
        self.shell_cmd("devmem2 %s w 0x00460000"%CChex, 1)

                
        self.shell_cmd("  nvme reset %s "%(self.dev_port), 0.5) 
        #self.hot_reset() 
        self.status="normal"
        return 0    
    def PrintAlignString(self,S0, S1, PF="default"):            
        mStr = "{:<4}{:<30}{:<30}".format("", S0, S1)
        if PF=="pass":
            self.Print( mStr , "p")        
        elif PF=="fail":
            self.Print( mStr , "f")      
        else:
            self.Print( mStr )       
    def thread_ResetRTD3(self):
        self.shell_cmd("echo -n %s > /sys/bus/pci/drivers/nvme/bind"%self.pcie_port)
        self.shell_cmd("echo on > /sys/bus/pci/devices/%s/power/control"%self.pcie_port)  
    def GetRDY(self):
        mStr = self.shell_cmd("devmem2 %s "%self.Reg_CC)        
        if re.search(": (.*)", mStr):
            value = int(re.search(": (.*)", mStr).group(1),16)
        else:
            value = 0
      
        RDY = (value ) & 0b1
        return RDY        
    def __init__(self, argv):
        # initial parent class
        super(Test, self).__init__(argv)
        self.Print("1234567890")
        print self.CR.CSTS.int
        
        '''
        CC= self.MemoryRegisterBaseAddress+0x28
        CChex=hex(CC)
        print CChex
        
        print self.read_pcie(self.PXCAP, 0xC+0x2)
        print self.read_pcie(self.PXCAP, 0xC+0x1)
        print self.read_pcie(self.PXCAP, 0xC+0x0)
        
        print "---------------------"
        print self.read_pcie(self.PXCAP, 0x12+0x0)
        print "---------------------"
        print "---------------------"
        print "---------------------"
        print self.read_pcie(self.PMCAP, 0x2+0x0)
        print self.read_pcie(self.PMCAP, 0x3+0x0)
        print self.read_pcie(self.PMCAP, 0x4+0x0)
        '''
        self.thread_ResetRTD3()
        print "0"
        print ""
        StartT=time.time()
        sleep(1)
        StopT=time.time()
        TimeDiv=StopT-StartT
        self.Print( "Run Time: %s"%TimeDiv, "p")
                    
        self.PrintAlignString("888", "123")

                        
        '''
        self.status="reset"
        self.shell_cmd("  setpci -s %s 3E.b=50 " %(self.bridge_port), 0.5) 
        self.shell_cmd("  setpci -s %s 3E.b=10 " %(self.bridge_port), 0.5) 
        self.shell_cmd("  echo 1 > /sys/bus/pci/devices/%s/remove " %(self.bridge_port), 0.5) 
        self.shell_cmd("  echo 1 > /sys/bus/pci/rescan ", 0.5)
        self.shell_cmd("  rm -f %s* "%(self.dev_port))
        #self.shell_cmd("  echo 1 > /sys/bus/pci/devices/%s/reset " %(self.pcie_port)) 
        self.shell_cmd("  echo 1 > /sys/bus/pci/devices/%s/remove " %(self.bridge_port), 0.5) 
        self.shell_cmd("  echo 1 > /sys/bus/pci/rescan ", 0.5)        
        self.hot_reset()
        self.status="normal"
        '''
        self.Print("")     
        self.Print("Done")
        self.Print("")        
            


'''

mNVME.LBARangeDataStructure.Type=0x2
mNVME.LBARangeDataStructure.Attributes=0x1
mNVME.LBARangeDataStructure.SLBA=0x5432
mNVME.LBARangeDataStructure.NLB=7
mNVME.LBARangeDataStructure.CreatePattern()
print mNVME.LBARangeDataStructure.Pattern


print hex(16)[1:]


start = time.time()
  
print int(time.time())
sleep(1)
print time.time()


for i in range(1,0x12):
    print mNVME.get_feature(fid = i, sel = 0)
    
    
def stopwatch(seconds):
    start = time.time()
    time.clock()    
    elapsed = 0
    while elapsed < seconds:
        elapsed = time.time() - start
        print "loop cycle time: %f, seconds count: %02d" % (time.clock() , elapsed) 
        time.sleep(1)  

stopwatch(20)
    
'''
if __name__ == "__main__":
    DUT = Test(sys.argv ) 



    
    
    
    
    
    
    
    