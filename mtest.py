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
import os.path
def GetPS():
    return int(mNVME.get_feature(2)[-1:])

print "Ver: 20181022_0930"
mNVME = NVME.NVME(sys.argv )


print mNVME.GetLog.SanitizeStatus.SPROG
'''
EDSTT=mNVME.IdCtrl.EDSTT.int
print "123456"

LiveT = mNVME.GetLog.SMART.CompositeTemperature

print mNVME.GetLog.SMART.CompositeTemperature

SECOND=0
print GetPS()

mThreads=mNVME.nvme_write_multi_thread(thread=4, sbk=0, bkperthr=512, value=0x5A)
for process in mThreads:   
    process.join()
'''    
'''    
@deadline(2)
def take_a_long_time():
    while(True):
        sleep (0.5)
        print "1111"    
    
try:
    take_a_long_time()
except TimedOutExc as e:
    print "took too long"

'''




