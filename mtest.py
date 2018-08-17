from lib_vct import NVME
import sys
from time import sleep
import threading

def GetRDY():
    return mNVME.CR.CSTS.Bit(0)

def F_reset():
    mNVME.shell_cmd("  nvme sanitize %s -a 0x02 2>&1 > /dev/null"%(mNVME.dev))
    

exit_code=0
mNVME = NVME.NVME_VCT(sys.argv[1] )
if mNVME.dev_alive:
    print "device alive"
else:    
    print "device missing"
    sys.exit(-1)
    
print "SMI_NVMeReset.py"    
print "--------------------------------------------------------------------------------"
print "nvme controller reset test"

mNVME.nvme_write_1_block(0x32,0)
mNVME.nvme_write_1_block(0x33,1)
mNVME.nvme_write_1_block(0x35,2)




