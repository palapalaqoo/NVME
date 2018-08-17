#!/usr/bin/env python

from lib_vct import NVME
import sys
from time import sleep

#  '-r' for reset test,ex 'python SMI_SanitizeStatusLog /dev/nvme0n1 -r'
TestReset=0
if len(sys.argv) == 3 and sys.argv[2]== "-r" :
    TestReset=1

mNVME = NVME.NVME_VCT(sys.argv[1] )
if mNVME.dev_alive:
    print "device alive"
else:    
    print "device missing"
    sys.exit(-1)
    

def SanitizeInProgress():
    # if sanitize in progress(SSTAT bit 1 = 1), retrun ture 
    return True if (mNVME.GetLog.SanitizeStatus.SSTAT & 0x2 >0) else False

def GlobalDataErased():
    # return Global Data Erased(SSTAT bit 8 )
    return 1 if (mNVME.GetLog.SanitizeStatus.SSTAT & 0x0100 >0) else 0

def SanitizeCompleted():
    # if sanitize in progress(SSTAT bit 0 = 1), retrun ture 
    return True if (mNVME.GetLog.SanitizeStatus.SSTAT & 0x1 >0) else False

# Block Erase sanitize operation Support 
BlockEraseSupport = True if (mNVME.IdCtrl.SANICAP & 0x2 > 0) else False
if not BlockEraseSupport:
    print "Block Erase sanitize operation not Support! Exit "
    sys.exit(-1)

PassTest=1

# wait for sanitize finish if recent sanitize operation has not completed
if SanitizeInProgress():
    print "The most recent sanitize operation is in progress! wait for sanitize finish!"  
while SanitizeInProgress():
    pass

# send sanitize command   
mNVME.shell_cmd("  nvme sanitize %s -a 0x02 2>&1 > /dev/null"%(mNVME.dev))

# wait for sanitize command start(SSTAT bit 2 = 1)
while not SanitizeInProgress():
    pass
    
print "controller start to sanitize"    
# wait for sanitize command complate
sprog0=mNVME.GetLog.SanitizeStatus.SPROG 
sprog1=sprog0
reset=0
while sprog0 != 0xFFFF:
    sleep(0.1)
    
    reset=reset +1
    if reset==3 and TestReset==1:    
        print "reset"    
        #mNVME.subsystem_reset()
        #mNVME.nvme_reset()
        mNVME.hot_reset()
        #mNVME.link_reset()

        
    
    sprog1 = mNVME.GetLog.SanitizeStatus.SPROG
    # check if SPROG count correctlly 
    if sprog0 >  sprog1:          
        PassTest=0
    sprog0=sprog1
    print "SPROG = %s" %(sprog0)
    
print "check SPROG"
if PassTest==1:    
    print  "\033[32m PASS! \033[0m"  
else:
    print  "\033[31m FAIL! \033[0m"   
    PassTest=0

print "check SSTAT"
# if SSTAT[0:4] = 2'b 001
if not SanitizeInProgress() and SanitizeCompleted():    
    print  "\033[32m PASS! \033[0m"  
else:
    print  "\033[31m FAIL! \033[0m"   
    PassTest=0
    
print "check SCDW10"
if mNVME.GetLog.SanitizeStatus.SCDW10=="02000000":
    print  "\033[32m PASS! \033[0m"  
else:
    print  "\033[31m FAIL! \033[0m"   
    PassTest=0    
    
print "check if GlobalDataErased = 1 after sanitize"
if GlobalDataErased()==1:
    print  "\033[32m PASS! \033[0m"  
else:
    print  "\033[31m FAIL! \033[0m"   
    PassTest=0 

print "check if GlobalDataErased = 0 after write data to ssd"
mNVME.write()
if GlobalDataErased()==0:
    print  "\033[32m PASS! \033[0m"  
else:
    print  "\033[31m FAIL! \033[0m"   
    PassTest=0 






sys.exit (0 if PassTest==1 else 1)






