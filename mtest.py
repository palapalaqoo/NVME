#!/usr/bin/env python
from lib_vct import NVME
import sys
from time import sleep
import threading
import re


mNVME = NVME.NVME(sys.argv[1] )

print mNVME.bridge_port
print mNVME.pcie_port


'''
        [virtual] Expansion ROM at df100000 [disabled] [size=64K]
        Capabilities: [40] Power Management version 3
        Capabilities: [50] MSI: Enable- Count=1/16 Maskable+ 64bit+
        Capabilities: [70] Express Endpoint, MSI 01
        Capabilities: [b0] MSI-X: Enable+ Count=22 Masked-
        Capabilities: [100] Advanced Error Reporting
        Capabilities: [158] #19
        Capabilities: [178] Latency Tolerance Reporting
        Capabilities: [180] L1 PM Substates
'''        

buf=mNVME.shell_cmd("lspci -v -s %s" %(mNVME.pcie_port))

print buf
print ""

print mNVME.PMCAP
print mNVME.MSICAP
print mNVME.MSIXCAP
print mNVME.PXCAP
print mNVME.AERCAP

aa= mNVME.read_pcie(mNVME.PXCAP, 0x9)
print aa

aa=aa+ (1<<7)
print aa


print mNVME.IdCtrl.OACS.str
#mNVME.por_reset()

mNVME.shell_cmd("  buf=$( nvme write-uncor %s -s 0 -n 1 -c 127 2>&1 >/dev/null )"%(mNVME.dev))
mNVME.shell_cmd("  buf=$( hexdump %s -n 512 2>&1 >/dev/null )"%(mNVME.dev))

    
    
    
    
    
    



