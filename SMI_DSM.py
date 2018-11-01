#!/usr/bin/env python
# -*- coding: utf-8 -*-
from lib_vct import NVME
import sys
from time import sleep
import threading
import re
import time


## paramter #####################################
ret_code=0
sub_ret=0
MoreInfo=0

    
## function #####################################
def Block0IsEqual(value, nsid=1):
    # check if block 0 is equal pattern or not
    return mNVME.fio_isequal(0, 512, value, nsid, 512)

def Block1GIsEqual(value, nsid=1):
    # check if block 0 is equal pattern or not
    return mNVME.fio_isequal(0, "1G", value, nsid, 512)

def Deallocate(nsid=1):
    mNVME.shell_cmd("nvme dsm %s -s 0 -b 1 -n %s -d"%(mNVME.device, nsid))
    
def CheckDealloResult(value):
    result_ret=0
    if DLFEAT_bit2to0==0:
        #  ExpectValue="0x0 or 0xFF"
        if not (value==0x0 or value==0xFF):
            result_ret=1
        
    elif DLFEAT_bit2to0==1:
        #ExpectValue="0x0"
        if not (value==0x0):
            result_ret=1
                
    elif DLFEAT_bit2to0==2:
        #ExpectValue="0xFF"
        if not (value==0xFF):
            result_ret=1
    else:
        #ExpectValue="0x0 or 0xFF"
        if not (value==0x0 or value==0xFF):
            result_ret=1 
            
    if result_ret==0:
        return True
    else:
        return False

## end function #####################################


print ""
print "-- NVME Dataset Management(DSM) command test" 
print "-----------------------------------------------------------------------------------"


print "Ver: 20181023_0900"
mNVME = NVME.NVME(sys.argv )
  
DLFEAT = mNVME.IdNs.DLFEAT
DLFEAT_bit2to0=DLFEAT & 0b00000111

DSMSupported=mNVME.IdCtrl.ONCS.bit(2)
if DSMSupported:
    print "Controller supports the Dataset Management command"
else:
    mNVME.Print( "Controller do not supports the Dataset Management command, quit all the test items"   ,"f")
    sys.exit(ret_code)   



print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Dataset Management – Command Dword 11"
print "Test the controller should accept all the attributes in CDW11"

print ""
print "Attribute – Deallocate (AD) "
mStr = mNVME.shell_cmd("nvme dsm %s -s 0 -b 1 -d"%mNVME.device)
if not re.search("success", mStr):
    mNVME.Print("Fail", "f")
    ret_code = 1
else:
    mNVME.Print("Pass", "p")

print ""
print "Attribute – Integral Dataset for Write (IDW)"
mStr = mNVME.shell_cmd("nvme dsm %s -s 0 -b 1 -w"%(mNVME.device))
if not re.search("success", mStr):
    mNVME.Print("Fail", "f")
    ret_code = 1
else:
    mNVME.Print("Pass", "p")
    
print ""
print "Attribute – Integral Dataset for Read (IDR)"
mStr = mNVME.shell_cmd("nvme dsm %s -s 0 -b 1 -r"%(mNVME.device))
if not re.search("success", mStr):
    mNVME.Print("Fail", "f")
    ret_code = 1
else:
    mNVME.Print("Pass", "p")

print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Keyword: Attribute - Deallocate (AD)"
print "Test the values read from a deallocated is euqal to DLFEAT reported value"
#print "DLFEAT: %s"%DLFEAT
print "The values read from a deallocated logical block that DLFEAT reported is : "
if DLFEAT_bit2to0==0:
    print "    Not reported"
    ExpectValue="0x0 or 0xFF"
elif DLFEAT_bit2to0==1:
    print "    All bytes set to 00h"
    ExpectValue="0x0"
elif DLFEAT_bit2to0==2:
    print "    All bytes set to FFh"
    ExpectValue="0xFF"
else:
    print "    Reserved"
    ExpectValue="0x0 or 0xFF"
    
print "Start to write 1G data from block 0 with pattern is 0x5A"
mNVME.fio_write(0, "1G", 0x5A, 1)
print "Start to deallocate 1G data (2097152 block)"
mNVME.shell_cmd("nvme dsm %s -s 0 -b 2097152 -d"%mNVME.device)
print "Check the value read from the first block, expected value: %s"%ExpectValue
if DLFEAT_bit2to0==0:
    #  ExpectValue="0x0 or 0xFF"
    if Block1GIsEqual(0x0) or Block1GIsEqual(0xFF):
        mNVME.Print("Pass", "p")
    else:
        mNVME.Print("Fail", "f")
        ret_code=1
    
elif DLFEAT_bit2to0==1:
    #ExpectValue="0x0"
    if Block1GIsEqual(0x0):
        mNVME.Print("Pass", "p")
    else:
        mNVME.Print("Fail", "f")
        ret_code=1
            
elif DLFEAT_bit2to0==2:
    #ExpectValue="0xFF"
    if Block1GIsEqual(0xFF):
        mNVME.Print("Pass", "p")
    else:
        mNVME.Print("Fail", "f")    
        ret_code=1
else:
    #ExpectValue="0x0 or 0xFF"
    if Block1GIsEqual(0x0) or Block1GIsEqual(0xFF):
        mNVME.Print("Pass", "p")
    else:
        mNVME.Print("Fail", "f")   
        ret_code=1 


# if last test item pass, then test this item
if ret_code==0:    
    print ""
    print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
    print "Keyword: A logical block is allocated when it is written"
    print "After a logical block has been deallocated, test if logical block is allocated again when it is written"

    print "Start to write data( pattern is 0x5A) in to the first block that was deallocated in the last test item"
    mNVME.nvme_write_1_block(0x5A, 0)
    print "Check the value read from the first block, expected value: 0x5A"
    if Block0IsEqual(0x5A):
        mNVME.Print("Pass", "p")
    else:
        mNVME.Print("Fail", "f")
        ret_code=1

    
    

NsSupported=True if mNVME.IdCtrl.OACS.bit(3)=="1" else False
if NsSupported:
    print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
    print "Keyword: Attribute - Deallocate (AD)"
    print "controller supports the Namespace Management and Namespace Attachment commands"
    print "Test the values read from a deallocated is euqal to DLFEAT reported value for multi namespaces "
    
    print ""
    print "Creating namespaces"
    mNS = mNVME.CreateMultiNs()
    if mNS ==1:
        print "only namespace 1 has been created, quit this test"
    else:
        print "namespaces nsid from 1 to %s have been created"%mNS
        
        DLFEAT_bit2to0=DLFEAT & 0b00000111
        #print "DLFEAT: %s"%DLFEAT
        #print "The values read from a deallocated logical block that DLFEAT reported is : "
        if DLFEAT_bit2to0==0:
            #print "    Not reported"
            ExpectValue="0x0 or 0xFF"
        elif DLFEAT_bit2to0==1:
            #print "    All bytes set to 00h"
            ExpectValue="0x0"
        elif DLFEAT_bit2to0==2:
            #print "    All bytes set to FFh"
            ExpectValue="0xFF"
        else:
            #print "    Reserved"
            ExpectValue="0x0 or 0xFF"
            
        print ""
        print "Write data in to the first block(block 0) of SSD with pattern is 0x5A at all namespaces"
        BlockData=[]
        # set BlockData[0]=0 for nvme0n0(not exist)
        BlockData.append(0)
        sub_ret=0
        for i in range(1, mNS+1):
            mNVME.nvme_write_1_block(0x5A, 0, i)
            if Block0IsEqual(0x5A, i):            
                BlockData.append(0x5A)
            else: 
                mNVME.Print("Write data fail at nsid= %s, quit the test"%i, "f")
                sub_ret=1
                ret_code=1
                break
        # if fail to write data for all NS, quit this test
        if sub_ret==0:
                
            print "Done"
            print ""
            print "Deallocate the first block and check the value read from the block of every namespaces"
            print "Expect that the block has been deallocated(read value= %s) where namespaces=Namespace Identifier field in command"%ExpectValue
            print "Blocks in other namespaces  should not be modified"
                   
            for nsid in range(1, mNS+1):      
                
                print "Start to deallocate the first block at nsid= %s"%nsid
                Deallocate(nsid)        
                
                Value=0
                test_ret=0    
                print "Check data"
                for i in range(1, mNS+1):
                    # get block data from nsid=i
                    if Block0IsEqual(0x0, nsid=i):
                        Value=0
                    elif Block0IsEqual(0xFF, nsid=i):
                        Value=0xFF
                    elif Block0IsEqual(0x5A, nsid=i):
                        Value=0x5A
                    
                    if nsid==i:
                        if not CheckDealloResult(Value):
                        # if data from deallocated block is not expected value
                            mNVME.Print("Fail, deallocatin at nsid= %s,expected value= %s read value= %s"%(i, ExpectValue, Value), "f")
                            test_ret=1
                        else:
                        # else save it to list
                            BlockData[i]=Value
                    else:
                    # "Blocks in other namespaces  should not be modified"
                        if BlockData[i]!=Value:
                            mNVME.Print("Fail, block 0 at nsid= %s has been modifyed while deallocation at nsid= %s"%(i, nsid), "f")
                            test_ret = 1
                # end for i
                if test_ret==0:
                    mNVME.Print("Pass", "p")
                else:
                    mNVME.Print("Fail", "f")
                    ret_code=1
            # end for nsid
        # end for if mNS!=1
        mNVME.ResetNS()
        








print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Keyword: Namespace Utilization (NUSE)"
print "Test the current number of logical blocks allocated in the namespace has changed after deallocation"

ThinProvisioningSupported =True if mNVME.IdNs.NSFEAT.bit(0)=="1" else False
print "Thin Provisioning is Supported" if ThinProvisioningSupported else "Thin Provisioning is not Supported"

# write data to make sure the NUSE is large enought
mNVME.fio_write(0, "1M", 0x5A, 1)

print ""
print "Before deallocation "
NUSE_B=mNVME.IdNs.NUSE.int
mNVME.Print( "NUSE: %s"%NUSE_B , "p")

print "Start to deallocate the first 100 blocks"
mNVME.shell_cmd("nvme dsm %s -s 0 -b 100 -d"%mNVME.device)

print "After deallocation "
NUSE_A=mNVME.IdNs.NUSE.int
mNVME.Print( "NUSE: %s"%NUSE_A , "p")

if ThinProvisioningSupported:
    print ""
    print "When Thin Provisioning is supported and the DSM command is supported"
    print "then deallocating LBAs shall be reflected in the Namespace Utilization field(NUSE)."

    print "Check if NUSE has changed or not, expected : Changed"
    if (NUSE_B != NUSE_A):
        mNVME.Print("Pass", "p")
    else:
        mNVME.Print("Fail", "f")
        ret_code=1


print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Keyword: Attribute – Integral Dataset for Write (IDW)"
print "Test the write performance of IDW"
print ""
print "Format nsid = 0 to clear all Attributes"
mNVME.shell_cmd("nvme format %s -n 1 -l 0 -s 0 -i 0"%mNVME.device)

Block=262144
#Block=2621440
Size=mNVME.KMGT(Block*512)
    
print "Write  %s blocks(%s), start LBA=0, value=0x5A"%(Block, Size)
StartT=time.time()
#mNVME.nvme_write_blocks(0x5A, 0, 1024)
mNVME.fio_write(0, Block*512, 0x5A, 1)
StopT=time.time()
TimeDiv=StopT-StartT
mNVME.Print( "Run Time: %s"%TimeDiv, "p")

print ""
print "Start to  set  attribute-IDW for %s blocks, start LBA=0"%Block
mNVME.shell_cmd("nvme dsm %s -s 0 -b %s -w"%(mNVME.device, Block))

print ""
print "Write  %s blocks(%s), start LBA=0, value=0x5B"%(Block, Size)
StartT=time.time()
#mNVME.nvme_write_blocks(0x5A, 0, 1024)
mNVME.fio_write(0, Block*512, 0x5B, 1)
StopT=time.time()
TimeDiv=StopT-StartT
mNVME.Print( "Run Time: %s"%TimeDiv, "p")

print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Keyword: Attribute – Integral Dataset for Read (IDR)"
print "Test the read performance of IDR"
print ""
print "Format nsid = 0 to clear all Attributes"
mNVME.shell_cmd("nvme format %s -n 1 -l 0 -s 0 -i 0"%mNVME.device)

Block=262144
#Block=2621440
Size=mNVME.KMGT(Block*512)
    
print "Read  %s blocks(%s), start LBA=0"%(Block, Size)
StartT=time.time()
mNVME.fio_isequal(0, Block*512, 0)
StopT=time.time()
TimeDiv=StopT-StartT
mNVME.Print( "Run Time: %s"%TimeDiv, "p")

print ""
print "Start to  set  attribute-IDR for %s blocks, start LBA=0"%Block
mNVME.shell_cmd("nvme dsm %s -s 0 -b %s -r"%(mNVME.device, Block))

print ""
print "Read  %s blocks(%s), start LBA=0"%(Block, Size)
StartT=time.time()
mNVME.fio_isequal(0, Block*512, 0)
StopT=time.time()
TimeDiv=StopT-StartT
mNVME.Print( "Run Time: %s"%TimeDiv, "p")



print ""
print "-- %s ---------------------------------------------------------------------------------"%mNVME.SubItemNum()
print "Keyword: Context Attributes"
print "Test Context Attributes for DSM command"
print ""
print "Context Attributes total bits=17, Command Access Size: 8, WP: 1, SW: 1, SR: 1, AL: 2, AF: 4"
print "Send command with Context Attributes from 0 to 0x1FFFF(17 bits) "
sub_ret=0

CA=0

    
for cnt in range(0x1FFFF+1):
    #parser cnt into Context Attributes
    AL_AF =           cnt&0b00000000000111111
    WP_SW_SR =(cnt&0b00000000111000000) >> 6
    CAS =             (cnt&0b11111111000000000) >> 9
    CA=(CAS<<24) + (WP_SW_SR<<8) + (AL_AF)
    
    
    mStr = mNVME.shell_cmd("nvme dsm %s -s 0 -b 1 -r -a %s"%(mNVME.device, CA))

    # print progress 
    if cnt%0x1000==0:
        mNVME.PrintProgressBar(cnt, 0x1FFFF, prefix = 'Progress:', length = 50)
    if not re.search("success", mStr):
        print ""
        mNVME.Print("Fail at Context Attributes = %s"%hex(CA), "f")
        ret_code = 1
        sub_ret = 1
        break
    cnt=cnt+1


if sub_ret==0:
    # print progress with 100 % finish
    mNVME.PrintProgressBar(100, 100, prefix = 'Progress:', length = 50)
    mNVME.Print("Pass","p")





print ""    
print "ret_code:%s"%ret_code
print "Finish"
sys.exit(ret_code)   








