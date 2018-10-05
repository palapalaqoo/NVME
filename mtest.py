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



print mNVME.IdNs.NLBAF.str
print mNVME.IdNs.FLBAS.str
print mNVME.IdNs.FPI.str
print mNVME.IdCtrl.FNA.int
    
SubItemCnt=0    

def SubItemCntPlus1():
    SubItemCnt=SubItemCnt+1
    return SubItemCnt
     
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print mNVME.GetLog.SanitizeStatus.SPROG

print mNVME.GetLog.DeviceSelfTest.TestResultDataStructure_1th.DeviceSelfTestStatus
print mNVME.GetLog.DeviceSelfTest.TestResultDataStructure_1th.PowerOnHours
print mNVME.GetLog.DeviceSelfTest.TestResultDataStructure_2th.DeviceSelfTestStatus
print mNVME.GetLog.DeviceSelfTest.TestResultDataStructure_2th.PowerOnHours
print mNVME.GetLog.DeviceSelfTest.TestResultDataStructure_3th.DeviceSelfTestStatus
print mNVME.GetLog.DeviceSelfTest.TestResultDataStructure_3th.PowerOnHours
