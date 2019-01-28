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
        
    def __init__(self, argv):
        # initial parent class
        super(Test, self).__init__(argv)
        self.Print("1234567890")
        mStr = "{:>7}{:>7}".format("123456","123456")
        self.Print(mStr)
        
        
            


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



    
    
    
    
    
    
    
    