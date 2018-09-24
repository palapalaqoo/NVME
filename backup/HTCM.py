#!/usr/bin/env python
from lib_vct import NVME
import sys
from time import sleep
import threading
import re
from lib_vct import NVMEAsyncEventRequest

mNVME = NVMEAsyncEventRequest.AsyncEvent(sys.argv )

def raiseTemp(arg):
    t = threading.currentThread()
    while getattr(t, "do_run", True):
        mNVME.nvme_write_blocks(0xab, 0, 256)
    print("Stopping as you wish.")

        


def GetDST_per():
    #ret int , GetDST[1]
    return int(mNVME.get_log(6, 12)[2:4],16)

def gettemp():
    return mNVME.shell_cmd("nvme smart-log /dev/nvme0n1 |grep 'temperature' |cut -d ':' -f 2|sed 's/[^0-9]*//g'")

def K2C(value):
    return value-273   

def C2K(value):
    return value+273     

def printTMT():
    print "*********************************"
    print mNVME.shell_cmd("nvme smart-log /dev/nvme0n1 |grep 'Thermal Management T1 Trans Count' ")
    print mNVME.shell_cmd("nvme smart-log /dev/nvme0n1 |grep 'Thermal Management T2 Trans Count' ")
    print mNVME.shell_cmd("nvme smart-log /dev/nvme0n1 |grep 'Thermal Management T1 Total Time' ")
    print mNVME.shell_cmd("nvme smart-log /dev/nvme0n1 |grep 'Thermal Management T2 Total Time' ")
    print "*********************************"
def setTMT(TMT1_K, TMT2_K):
    
    TMT_K=TMT1_K*65536 + TMT2_K
    print "set TMT1: %s, TMT2: %s"%(K2C(TMT1_K), K2C(TMT2_K))
    mNVME.shell_cmd("LOG_BUF=$(nvme set-feature /dev/nvme0n1 -f 0x10 -v %s)"%TMT_K)    


HCTM_old=mNVME.shell_cmd("nvme get-feature /dev/nvme0n1 -f 0x10  |cut -d ':' -f 3")
print "HCTM_old: %s"%HCTM_old
print "reset HCTM"    
#mNVME.shell_cmd("LOG_BUF=$(nvme set-feature /dev/nvme0n1 -f 0x10 -v 0x0158015C)")



    
LiveT=   gettemp()
print LiveT
    
MNTMT_K=mNVME.IdCtrl.MNTMT.int
MXTMT_K=mNVME.IdCtrl.MXTMT.int

MNTMT_C=K2C(MNTMT_K)
MXTMT_C=K2C(MXTMT_K)   
    
TargetTemp=MNTMT_C+4

print "MNTMT_K=%s k(%s C)"%(MNTMT_K,MNTMT_C)
print "MXTMT_K=%s k(%s C)"%(MXTMT_K,MXTMT_C)
print "TargetTemp= %s"%TargetTemp




print ""
print "original TMT"
printTMT()





print ""
print "writing data to increase temperature to make it large then TargetTemp"
print ""

t = threading.Thread(target = raiseTemp, args=("task",))
t.start()        


for i in range(60):    
    #mNVME.nvme_write_blocks(0xab, 0, 256)
    sleep (1)
    LiveT=gettemp()    
    print "get tempture: %s"%LiveT    
    if int(LiveT) >=TargetTemp:
        break
    
print "==================================="
'''
print ""
setTMT(MNTMT_K+1, MXTMT_K)
print "sleep 1.5s"
sleep (1.5)
LiveT=gettemp()    
print "get tempture: %s"%LiveT    
printTMT() 
'''   
print "==================================="

print ""
setTMT(MNTMT_K+1, MNTMT_K+2)
print "sleep 1.5s"
sleep (1.5)
LiveT=gettemp()    
print "get tempture: %s"%LiveT    
printTMT()







print ""
print "stop to raising temp"
t.do_run = False
t.join()
    
    
print "reset HCTM"    
mNVME.shell_cmd("LOG_BUF=$(nvme set-feature /dev/nvme0n1 -f 0x10 -v %s)"%HCTM_old)


    
    
    
    
    
    



