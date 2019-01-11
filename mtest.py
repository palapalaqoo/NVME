#!/usr/bin/env python


from lib_vct import NVME
from lib_vct import NVMECom
import sys
from time import sleep
import threading
import re
import random
import time


import signal
import subprocess
from lib_vct.NVMECom import deadline
from lib_vct.NVMECom import TimedOutExc
from gtk.keysyms import seconds
from lib_vct import NVMEAsyncEventRequest
import struct
def GetPS():
    return int(mNVME.get_feature(2)[-1:])


mNVME = NVME.NVME(sys.argv )
'''
def my_decorator(func):
    def wrapped_func(*args,**kwargs):
        return func("I've been decorated!",*args,**kwargs)
    return wrapped_func
'''

# Memory Register Base Address
MRBA=0x0
# MLBAR start from 0x10
for i in range(4):
    MRBA=MRBA+(mNVME.read_pcie(mNVME.PCIHeader, 0x10+i)<<(8*i))
# mask lower 13bits
MRBA = MRBA & 0xFFFFC000
# MUBAR start from 0x14
for i in range(4):
    MRBA=MRBA+(mNVME.read_pcie(mNVME.PCIHeader, 0x14+i)<<(8*i))

print hex(MRBA)





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


