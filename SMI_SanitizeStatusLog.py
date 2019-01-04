#!/usr/bin/env python

from lib_vct import NVME
import sys
from time import sleep
import re

print "SMI_SanitizeStatusLog.py"
print "Author: Sam Chan"
print "Ver: 20181203"
#  '-r' for reset test,ex 'python SMI_SanitizeStatusLog /dev/nvme0n1 -r'
TestReset=0
if len(sys.argv) == 3 and sys.argv[2]== "-r" :
    TestReset=1

mNVME = NVME.NVME(sys.argv[1] )
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
BlockEraseSupport = True if (mNVME.IdCtrl.SANICAP.bit(1) =="1") else False
if not BlockEraseSupport:
    print "Block Erase sanitize operation not Support! Exit "
    ret_code =255
    print ""
    print "ret_code:%s"%ret_code
    print "Finish"
    sys.exit(ret_code)   

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
sprog_pass=1
test_reset=0
test_retcode=0
ret_code="0"
ResetTest_timer=0
ResetTest_fail=0
print "------------------------------------"
while sprog0 != 0xFFFF:
    sleep(0.1)

    sprog1 = mNVME.GetLog.SanitizeStatus.SPROG
    # check if SPROG count correctlly 
    if sprog0 >  sprog1:          
        sprog_pass=0
    sprog0=sprog1
    print "SPROG = %s" %(sprog0)
    
    # testing sataus code for sanitize command(Sanitize In Progress)
    if test_retcode==0 and sprog1>=0x0FFF: 
        test_retcode=1
        print ""
        print "SPROG>=0x0FFF now, Write 512byte data (value=0x0) to block 0 for testing sataus code" 
        ret_code=mNVME.shell_cmd("  dd if=/dev/zero bs=512 count=1 2>&1 > /dev/null | nvme write %s --start-block=0 --data-size=512 2>&1 " % ( mNVME.dev))
        print "returned status code: %s" %ret_code
        print "check status code (expected result: Sanitize In Progress) " 
        if re.search("SANITIZE_IN_PROGRESS", ret_code):
            print  "\033[32m PASS! \033[0m"  
        else:
            print  "\033[31m FAIL! \033[0m"   
            PassTest=0        
        print ""    
    
    # testing reset for 1 time
    if test_reset==0 and sprog1>=0x1FFF: 
        test_reset=1   
        print "SPROG>=0x1FFF now, issue hot reset to test if controller resume the sanitize operation after reset or not(time out=10s) "    
        #mNVME.subsystem_reset()
        #mNVME.nvme_reset()
        mNVME.hot_reset()
        #mNVME.link_reset()
    
    # time out = 10s for reset test
    if ResetTest_timer==100:
        ResetTest_fail=1
        break
    ResetTest_timer=ResetTest_timer+1

print ""    
print "check reset test"
if ResetTest_fail==0:
    print  "\033[32m PASS! \033[0m"  
else:
    print  "\033[31m FAIL! \033[0m"   
    PassTest=0  

if ResetTest_fail==1:
    print ""    
    print "Because reset test fail, sanitize command can't finish, so do POR(power off reset) to reset controller and quite other test items "     
    mNVME.por_reset()

else:       
    print "Sanitize finished!"
    print ""    
    print "check SPROG"
    if sprog_pass==1:    
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
    


ret_code=0 if PassTest==1 else 1
print ""
print "ret_code:%s"%ret_code
print "Finish"

sys.exit (0 if PassTest==1 else 1)






