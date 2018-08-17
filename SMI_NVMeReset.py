#!/usr/bin/env python
'''
Created on Aug 15, 2018

@author: root
'''
from lib_vct import NVME
import sys
from time import sleep
import threading

def GetRDY():
    return mNVME.CR.CSTS.Bit(0)

def GetDST_per():
    #ret int , GetDST[1]
    return int(mNVME.get_log(6, 16)[2:4],16)
def GetDST_CDSTO():
    # ret int :Current Device Self-Test Operation
    return int(mNVME.get_log(6, 16)[0:2],16)
def GetDSTS():    
    return int(mNVME.get_log(6, 16)[9],16)
def GetPS():
    return int(mNVME.get_feature(2)[-1:])



    
def F_reset(rsttype):
    if rsttype==0:
        mNVME.nvme_reset()
    elif rsttype==1:
        mNVME.subsystem_reset()
    elif rsttype==2:
        mNVME.hot_reset()        
    elif rsttype==3:
        mNVME.link_reset()        

    

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
    
print dir(mNVME.CR)
RDY = GetRDY()

if RDY==1:
    print "\033[31mCheck CSTS.RDY before reset: FAIL! (CSTS.RDY=%s) , exit test\033[0m" %(RDY)
else:
    print "\033[32mCheck CSTS.RDY before reset: PASS! (CSTS.RDY=%s)\033[0m" %(RDY)
    
    
AQA = mNVME.CR.AQA.ToStr    
ASQ = mNVME.CR.ASQ.ToStr   
ACQ = mNVME.CR.ACQ.ToStr    




print "NVME reset (Controller disable)"

t = threading.Thread(target = mNVME.nvme_reset)
t.start()

print "Wait for CSTS.RDY = 0"
while GetRDY()==1:
    pass

print "\033[32mCSTS.RDY = 0 \033[0m"
print "Wait for CSTS.RDY = 1"
while GetRDY()==0:
    pass

print "\033[32mCSTS.RDY = 1 \033[0m"

print "compare AQA, ASQ, ACQ after reset"
print "before reset: AQA = %s" %(AQA)
print "before reset: ASQ = %s" %(ASQ)
print "before reset: ACQ = %s" %(ACQ)
print "after reset: AQA = %s" %(mNVME.CR.AQA.ToStr)
print "after reset: ASQ = %s" %(mNVME.CR.ASQ.ToStr)
print "after reset: ACQ = %s" %(mNVME.CR.ACQ.ToStr)

if AQA!=mNVME.CR.AQA.ToStr or ASQ!=mNVME.CR.ASQ.ToStr or ACQ!=mNVME.CR.ACQ.ToStr:
    print  "\033[31m FAIL! \033[0m"   
    exit_code=1
else:
    "\033[32mPASS! \033[0m"        
    
    

loop=0
reset_type =2

print "===== reset_type = %s  ========== loop = %s =====" %(reset_type,loop)


print "-- start testing for Pending Admin Commands after reset ------------------------------------------------"
'''
do_cmd=0
# self test command
mNVME.shell_cmd("LOG_BUF=$(nvme admin-passthru %s --opcode=0x14 --namespace-id=0xffffffff --data-len=0 --cdw10=0x1 -r -s 2>&1 > /dev/null)"%(mNVME.dev_port))


while True:
    if GetDST_per()>40 and do_cmd==0:
        F_reset(reset_type)
        print "reset controller while admin command execution exceed 40% "
        do_cmd=1        
 
    #if GetDST_CDSTO() ==0:
    if GetDST_per()==0:
        break
    
    #print GetDST_per()
    
if GetDSTS()==2 or GetDSTS()==7:
    print "\033[32mCheck pending admin commands after reset: PASS! \033[0m"
else:
    print  "\033[31mCheck pending admin commands after reset: FAIL! \033[0m"
    exit_code=1
'''

print "-- start testing for Pending IO Commands after reset(data integrity) ------------------------------------------------"
'''
patten=0x5A
thread_w=5
block_w=1024 
total_byte_w=block_w*thread_w *512

# clear SSD data to 0x0
mNVME.fio_write(0, total_byte_w, 0x0)


# write data using multy thread
mThreads = mNVME.nvme_write_multi_thread(thread_w, 0, block_w, patten)

# check if all process finished 
reset_cnt=0
while True:        
    allfinished=1
    for process in mThreads:
        if process.is_alive():
            allfinished=0

    # if all process finished then, quit while loop, else  send reset command
    if allfinished==1:        
        break
    else:
        F_reset(reset_type)
        reset_cnt=reset_cnt+1
        pass
    
    
print  "send reset command %s times while writing data is in progress"%(reset_cnt)
 
# if have 00 and 5a in flash, then pass the test(f_write pattern=0x5a)
find_00 = mNVME.shell_cmd("hexdump %s -n %s |grep '0000 0000' 2>/dev/null"%(mNVME.dev, total_byte_w))
find_patten = mNVME.shell_cmd("hexdump %s -n %s |grep '5a5a 5a5a' 2>/dev/null"%(mNVME.dev, total_byte_w))


# controller reset can't verify data integrity, so let data integrity test = pass
if (find_00 and find_patten) or reset_type==0:
    print "\033[32mCheck data integrity: PASS! \033[0m"
else:
    print  "\033[31mCheck data integrity: FAIL! \033[0m"
    exit_code=1
    
'''
print "-- start testing for NVM idle state(power state)  ------------------------------------------------------------------------"
       
pst_fail=0       
NPSS=mNVME.IdCtrl.NPSS

for i in range(NPSS+1):
    mNVME.set_feature(2, i)
    PS=GetPS()
    # verify set_feature successfull
    if PS!=i:
        print "\033[31mSet power state error! \033[0m"
        pst_fail=1
        break
    
    F_reset(reset_type)
    
    PS=GetPS()

    # nvme spec: ps=0 after reset
    if PS!=0:
        pst_fail=1
        break        

if pst_fail==0:
    print "\033[32mCheck power state: PASS!\033[0m"
else:
    print "\033[31mCheck power state: FAIL!\033[0m"    
    exit_code=1





    
print "finished" 




    
    


