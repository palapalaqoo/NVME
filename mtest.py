#!/usr/bin/env python
from lib_vct import NVME
import sys
from time import sleep
import threading
import re
from lib_vct import NVMEAsyncEventRequest


mNVME = NVMEAsyncEventRequest.AsyncEvent(sys.argv )

def GetDST_per():
    #ret int , GetDST[1]
    return int(mNVME.get_log(6, 12)[2:4],16)

'''
# self test command
mNVME.shell_cmd("LOG_BUF=$(nvme admin-passthru %s --opcode=0x14 --namespace-id=0xffffffff --data-len=0 --cdw10=0x1 -r -s 2>&1 > /dev/null)"%(mNVME.dev_port))

do_cmd=0
while True:
    # if self test percentage > 40%, send reset command
    if GetDST_per()>10 and do_cmd==0:            
        print "reset controller while admin command execution exceed 40% "
        print mNVME.shell_cmd("nvme io-passthru /dev/nvme0n1 -o 0x2 -n 1 -l 16 -r --cdw10=0 --cdw11=0 --cdw12=0xFFFF0000")
        do_cmd=1        
''' 

    

print mNVME.IdNs.NUSE.str
print mNVME.IdNs.NUSE.int













