#!/usr/bin/env python
# -*- coding: utf-8 -*-

        #=======================================================================
        # abstract  function
        #     SubCase1() to SubCase32()                            :Override it for sub case 1 to sub case32
        # abstract  variables
        #     SubCase1Desc to SubCase32Desc                 :Override it for sub case 1 description to sub case32 description
        #     SubCase1Keyword to SubCase32Keyword    :Override it for sub case 1 keyword to sub case32 keyword
        #     self.ScriptName, self.Author, self.Version      :self.ScriptName, self.Author, self.Version
        #=======================================================================     
        
# Import python built-ins
import sys
import time
from time import sleep
import threading
import re
from random import randint

# Import VCT modules
from lib_vct.NVME import NVME

class SMI_DSM(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_DSM.py"
    Author = "Sam Chan"
    Version = "20190927"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    

    
    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def Block0IsEqual(self, value, nsid=1):
        # check if block 0 is equal pattern or not
        return self.fio_isequal(0, 512, value, nsid, 512)

    def Block4KIsEqual(self, value, nsid=1):
        # check if block 0-7 is equal pattern or not
        return self.fio_isequal(0, "4K", value, nsid, 512)
    
    def Block1GIsEqual(self, value, nsid=1):
        # check if block 0 is equal pattern or not
        return self.fio_isequal(0, "1G", value, nsid, 512)
    
    def Deallocate(self, nsid=1, size=8):
        self.shell_cmd("nvme dsm %s -s 0 -b %s -n %s -d"%(self.device, size, nsid))
        
    def CheckDealloResult(self, value):
        result_ret=0
        if self.DLFEAT_bit2to0==0:
            #  ExpectValue="0x0 or 0xFF"
            if not (value==0x0 or value==0xFF):
                result_ret=1
            
        elif self.DLFEAT_bit2to0==1:
            #ExpectValue="0x0"
            if not (value==0x0):
                result_ret=1
                    
        elif self.DLFEAT_bit2to0==2:
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
        
    def DoContextAttrText(self, CAS_H, TakeProgress=False):
    # CAS_H CAS high byte, 4 bit
        for cnt in range(0x1FFF+1):
            #parser cnt into Context Attributes
            AL_AF =           cnt&0b0000000111111
            WP_SW_SR =(cnt&0b0000111000000) >> 6
            CAS_L =             (cnt&0b1111000000000) >> 9
            CA=(CAS_H<<28) + (CAS_L<<24) + (WP_SW_SR<<8) + (AL_AF)                        
            mStr = self.shell_cmd("nvme dsm %s -s 0 -b 1 -r -a %s"%(self.device, CA))
            # set progress
            if TakeProgress:
                self.procProgress=cnt
            # if this proc fail
            if not re.search("success", mStr):
                self.Print ("")
                self.Print("Fail at Context Attributes = %s"%hex(CA), "f")
                self.procStatus=False
                break
            # if other proc fail
            if not self.procStatus:
                break
                  
    def GetRangeList(self):
    # trim whole disk(4k)
    # first 255 range, set StartingLBA=i, LengthInLogicalBlocks=1, ContextAttributes=0
    # last range(256), set StartingLBA=i, LengthInLogicalBlocks=NUSE - i, ContextAttributes=0
        NCAP=self.IdNs.NCAP.int
        rtList=[]
        for i in range(256):
            if i!=255:
                StartingLBA=i*8
                LengthInLogicalBlocks=8
                ContextAttributes=0
            else:
                StartingLBA=i*8
                LengthInLogicalBlocks=NCAP-i*8
                ContextAttributes=0
            rtList.append([StartingLBA, LengthInLogicalBlocks, ContextAttributes])
        return rtList
                  
        # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def __init__(self, argv):
        self.SetDynamicArgs(optionName="n", optionNameFull="disableNsTest", helpMsg="disable namespace test, ex. '-n 1'", argType=int)    
        # initial parent class
        super(SMI_DSM, self).__init__(argv)
        
        self.disableNsTest = self.GetDynamicArgs(1)
        self.disableNsTest = True if self.disableNsTest==1 else False        
        
        # <Parameter>
        self.DLFEAT = self.IdNs.DLFEAT
        self.DLFEAT_bit2to0=self.DLFEAT & 0b00000111
        self.DSMSupported=self.IdCtrl.ONCS.bit(2)
        self.NsSupported=True if self.IdCtrl.OACS.bit(3)=="1" else False
        # context attr test
        self.procStatus=True
        self.procProgress=0

        # </Parameter>
        
    # define pretest  
    def PreTest(self): 
        if self.disableNsTest:
            self.Print ("User disable namespace test", "f")         
        
        if not self.DSMSupported:
            self.Print("DSM command not supported, skip all", "w")
            return False
        else:
            self.Print("DSM command supported")
            return True
        
    # <sub item scripts> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    SubCase1TimeOut = 60
    SubCase1Desc = "Test Command Dword 11"    
    def SubCase1(self):  
        self.Print ("Test the controller should accept all the attributes in CDW11")
        if self.DSMSupported:         
            ret_code=0    
            self.Print ("")
            self.Print ("Attribute – Deallocate (AD) ")
            mStr = self.shell_cmd("nvme dsm %s -s 0 -b 1 -d"%self.device)
            if not re.search("success", mStr):
                self.Print("Fail", "f")
                ret_code = 1
            else:
                self.Print("Pass", "p")
            
            self.Print ("")
            self.Print ("Attribute – Integral Dataset for Write (IDW)")
            mStr = self.shell_cmd("nvme dsm %s -s 0 -b 1 -w"%(self.device))
            if not re.search("success", mStr):
                self.Print("Fail", "f")
                ret_code = 1
            else:
                self.Print("Pass", "p")
                
            self.Print ("")
            self.Print ("Attribute – Integral Dataset for Read (IDR)")
            mStr = self.shell_cmd("nvme dsm %s -s 0 -b 1 -r"%(self.device))
            if not re.search("success", mStr):
                self.Print("Fail", "f")
                ret_code = 1
            else:
                self.Print("Pass", "p")
            
            return ret_code
        else:
            self.Print("not supported", "w")
            return 255
    
    SubCase2TimeOut = 60
    SubCase2Desc = "Test Attribute - Deallocate (AD), single name spaces"
    def SubCase2(self):
        ret_code=0    
        if self.DSMSupported:
            self.Print ("Test the values read from a deallocated is euqal to DLFEAT reported value")
            #self.Print ("DLFEAT: %s"%DLFEAT)
            self.Print ("The values read from a deallocated logical block that DLFEAT reported is : ")
            if self.DLFEAT_bit2to0==0:
                self.Print ("    Not reported")
                ExpectValue="0x0 or 0xFF or last data(0x5A)"
            elif self.DLFEAT_bit2to0==1:
                self.Print ("    All bytes set to 00h")
                ExpectValue="0x0"
            elif self.DLFEAT_bit2to0==2:
                self.Print ("    All bytes set to FFh")
                ExpectValue="0xFF"
            else:
                self.Print ("    Reserved")
                ExpectValue="0x0 or 0xFF or last data(0x5A)"
                
            self.Print ("")
            self.Print ("Start to write 1G data from block 0 with pattern is 0x5A")
            self.fio_write(0, "1G", 0x5A, 1)
            self.Print ("Start to deallocate 1G data (2097152 block) from block 0")
            self.shell_cmd("nvme dsm %s -s 0 -b 2097152 -d"%self.device)
            self.Print ("Check the value from the first 1G data with read command, expected value: %s"%ExpectValue)
            if self.DLFEAT_bit2to0==0:
                #  ExpectValue="0x0 or 0xFF or last data"
                if self.Block1GIsEqual(0x0) or self.Block1GIsEqual(0xFF) or self.Block1GIsEqual(0x5A):
                    self.Print("Pass", "p")
                else:
                    self.Print("Fail", "f")
                    ret_code=1
                
            elif self.DLFEAT_bit2to0==1:
                #ExpectValue="0x0"
                if self.Block1GIsEqual(0x0):
                    self.Print("Pass", "p")
                else:
                    self.Print("Fail", "f")
                    ret_code=1
                        
            elif self.DLFEAT_bit2to0==2:
                #ExpectValue="0xFF"
                if self.Block1GIsEqual(0xFF):
                    self.Print("Pass", "p")
                else:
                    self.Print("Fail", "f")    
                    ret_code=1
            else:
                #ExpectValue="0x0 or 0xFF or last data"
                if self.Block1GIsEqual(0x0) or self.Block1GIsEqual(0xFF) or self.Block1GIsEqual(0x5A):
                    self.Print("Pass", "p")
                else:
                    self.Print("Fail", "f")   
                    ret_code=1 
            
            
            # if last test item pass, then test this item
            if ret_code==0:    
                self.Print ("")
                self.Print ("-- %s ---------------------------------------------------------------------------------"%self.SubItemNum())
                self.Print ("Keyword: A logical block is allocated when it is written")
                self.Print ("After a logical block has been deallocated, test if logical block is allocated again when it is written")
            
                self.Print ("Start to write data( pattern is 0x5A) in to the first block that was deallocated in the last test item")
                self.nvme_write_1_block(0x5A, 0)
                self.Print ("Check the value read from the first block, expected value: 0x5A")
                if self.Block0IsEqual(0x5A):
                    self.Print("Pass", "p")
                else:
                    self.Print("Fail", "f")
                    ret_code=1       
                    
            return ret_code
        else:
            self.Print("not supported", "w")
            return 255
        
    SubCase3TimeOut = 120
    SubCase3Desc = "Test Attribute - Deallocate (AD), multi name spaces"    
    def SubCase3(self):
        self.Print ("Test the values read from a deallocated is euqal to DLFEAT reported value for multi namespaces ")
        if self.disableNsTest:
            self.Print ("User disable namespace test, skip", "f") 
            return 255
        ret_code=0
        if self.DSMSupported and self.NsSupported:          
            
            self.Print ("")
            self.Print ("Creating namespaces")
            mNS = self.CreateMultiNs()
            if mNS ==1:
                self.Print ("only namespace 1 has been created, quit this test")
            else:
                self.Print ("namespaces nsid from 1 to %s have been created"%mNS)
                
                DLFEAT_bit2to0=self.DLFEAT & 0b00000111
                #self.Print ("DLFEAT: %s"%DLFEAT)
                #self.Print ("The values read from a deallocated logical block that DLFEAT reported is : ")
                if DLFEAT_bit2to0==0:
                    #self.Print ("    Not reported")
                    ExpectValue="0x0 or 0xFF"
                elif DLFEAT_bit2to0==1:
                    #self.Print ("    All bytes set to 00h")
                    ExpectValue="0x0"
                elif DLFEAT_bit2to0==2:
                    #self.Print ("    All bytes set to FFh")
                    ExpectValue="0xFF"
                else:
                    #self.Print ("    Reserved")
                    ExpectValue="0x0 or 0xFF"
                    
                self.Print ("")
                self.Print ("Write data in to the first 8 blocks(4k) of SSD with pattern is 0x5A at all namespaces")
                BlockData=[]
                # set BlockData[0]=0 for nvme0n0(not exist)
                BlockData.append(0)
                sub_ret=0
                for i in range(1, mNS+1):
                    # write
                    # self.nvme_write_1_block(0x5A, 0, i)
                    self.nvme_write_blocks(value=0x5A, sb=0, nob=8, nsid=i)
                    # verify
                    if self.Block4KIsEqual(0x5A, i):            
                        BlockData.append(0x5A)
                    else: 
                        self.Print("Write data fail at nsid= %s, quit the test"%i, "f")
                        sub_ret=1
                        ret_code=1
                        break
                # if fail to write data for all NS, quit this test
                if sub_ret==0:
                        
                    self.Print ("Done")
                    self.Print ("")
                    self.Print ("Deallocate the first block and check the value read from the block of every namespaces")
                    self.Print ("Expect that the block has been deallocated(read value= %s) where namespaces=Namespace Identifier field in command"%ExpectValue)
                    self.Print ("Blocks in other namespaces  should not be modified")
                           
                    for nsid in range(1, mNS+1):      
                        
                        self.Print ("Start to deallocate the first 8 blocks(4k) at nsid= %s"%nsid)
                        self.Deallocate(nsid, 8)        
                        
                        Value=0
                        test_ret=0    
                        self.Print ("Check data")
                        for i in range(1, mNS+1):
                            # get block data from nsid=i
                            if self.Block4KIsEqual(0x0, nsid=i):
                                Value=0
                            elif self.Block4KIsEqual(0xFF, nsid=i):
                                Value=0xFF
                            elif self.Block4KIsEqual(0x5A, nsid=i):
                                Value=0x5A
                            
                            if nsid==i:
                                if not self.CheckDealloResult(Value):
                                # if data from deallocated block is not expected value
                                    self.Print("Fail, deallocatin at nsid= %s,expected value= %s read value= %s"%(i, ExpectValue, Value), "f")
                                    test_ret=1
                                else:
                                # else save it to list
                                    BlockData[i]=Value
                            else:
                            # "Blocks in other namespaces  should not be modified"
                                if BlockData[i]!=Value:
                                    self.Print("Fail, block 0-7 at nsid= %s has been modifyed while deallocation at nsid= %s"%(i, nsid), "f")
                                    test_ret = 1
                        # end for i
                        if test_ret==0:
                            self.Print("Pass", "p")
                        else:
                            self.Print("Fail", "f")
                            ret_code=1
                    # end for nsid
                # end for if mNS!=1
                self.ResetNS()   
            return ret_code
        else:
            self.Print("not supported", "w")
            return 255

    SubCase4TimeOut = 600
    SubCase4Desc = "Test Attribute - Deallocate whole disk (AD) with a list of ranges"          
    def SubCase4(self):       
        ret_code=0
        if self.DSMSupported:
            
            
            self.Print ("Test the values read from a deallocated is euqal to DLFEAT reported value")
            #self.Print ("DLFEAT: %s"%DLFEAT)
            self.Print ("The values read from a deallocated logical block that DLFEAT reported is : ")
            if self.DLFEAT_bit2to0==0:
                self.Print ("    Not reported")
                ExpectValue="0x0 or 0xFF or last data(0x5A)"
            elif self.DLFEAT_bit2to0==1:
                self.Print ("    All bytes set to 00h")
                ExpectValue="0x0"
            elif self.DLFEAT_bit2to0==2:
                self.Print ("    All bytes set to FFh")
                ExpectValue="0xFF"
            else:
                self.Print ("    Reserved")
                ExpectValue="0x0 or 0xFF or last data(0x5A)"
                
            self.Print("")
            self.start_SB
            self.middle_SB
            self.last_SB
            self.fio_write(0, "1G", 0x5A, 1)
            
            TestPatten=randint(1, 0xFF)
            self.Print ("Write data to the front, middle and back spaces of the LBA and verify if write success")
            self.Print ("e.g. %s, %s and %s, size 1G, value = %s"%(hex(self.start_SB*512), hex(self.middle_SB*512), hex(self.last_SB*512), hex(TestPatten)))
            self.write_SML_data(TestPatten, "1G")    
            if self.isequal_SML_data(TestPatten,"1G", printMsg=True):
                self.Print("Write success", "p")
            else:
                self.Print("Write fail, quit", "f")
                return 1
            
            self.Print ("")            
            RangeList = self.GetRangeList()
            self.Print ("Start to deallocate whole disk with a list of ranges as below")
            self.Print("")
            
            # parse RangeList and print it
            CMD_s=""    # cmd start lba 
            CMD_b=""    # cmd logical blocks
            CMD_a=""    # cmd ContextAttributes
            for i in range(256):
                #[StartingLBA, LengthInLogicalBlocks, ContextAttributes]
                StartingLBA=RangeList[i][0]
                LengthInLogicalBlocks=RangeList[i][1]
                ContextAttributes=RangeList[i][2]
                # add to command syntax
                CMD_s = CMD_s + "%s,"%StartingLBA
                CMD_b = CMD_b + "%s,"%LengthInLogicalBlocks
                CMD_a = CMD_a + "%s,"%ContextAttributes    
                
                # print
                if i <=3 or i>=254:
                    self.Print ("Range %s: Starting LBA = %s, Length in logical blocks = %s, Context Attributes = %s"%(i, StartingLBA, LengthInLogicalBlocks, ContextAttributes))
                if i ==4:
                    self.Print ("  ...")
                    
            self.Print("")
            self.Print("Issue dsm(deallocate) command")
            CMD = "nvme dsm %s -s %s -b %s -a %s -d 2>&1"%(self.device, CMD_s, CMD_b, CMD_a)
            self.Print("CMD: %s"%CMD)
            rtStatus = self.shell_cmd(CMD)
            if bool(re.search("Success", rtStatus)) or bool(re.search("success", rtStatus)):
                self.Print("Command success", "p")
            else:
                self.Print("Command fail, quit", "f")
                self.Print("Command: %s"%CMD)
                return 1
                
            
            
            self.Print ("Check the value from the front, middle and back spaces with read command, expected value: %s"%ExpectValue)
            if self.DLFEAT_bit2to0==0:
                #  ExpectValue="0x0 or 0xFF or last data"
                if self.isequal_SML_data(0x0, "1G", printMsg=True) or self.isequal_SML_data(0xFF, "1G", printMsg=True)\
                or self.isequal_SML_data(TestPatten, "1G", printMsg=True):
                    self.Print("Pass", "p")
                else:
                    self.Print("Fail", "f")
                    ret_code=1
                
            elif self.DLFEAT_bit2to0==1:
                #ExpectValue="0x0"
                if self.isequal_SML_data(0x0, "1G", printMsg=True):
                    self.Print("Pass", "p")
                else:
                    self.Print("Fail", "f")
                    ret_code=1
                        
            elif self.DLFEAT_bit2to0==2:
                #ExpectValue="0xFF"
                if self.isequal_SML_data(0xFF, "1G", printMsg=True):
                    self.Print("Pass", "p")
                else:
                    self.Print("Fail", "f")    
                    ret_code=1
            else:
                #ExpectValue="0x0 or 0xFF or last data"
                if self.isequal_SML_data(0x0, "1G", printMsg=True) or self.isequal_SML_data(0xFF, "1G", printMsg=True)\
                or self.isequal_SML_data(TestPatten, "1G", printMsg=True):
                    self.Print("Pass", "p")
                else:
                    self.Print("Fail", "f")   
                    ret_code=1 
            return ret_code

    SubCase5TimeOut = 60
    SubCase5Desc = "Test Attribute – Integral Dataset for Write (IDW)"            
    def SubCase5(self):
        self.Print ("Test the write performance of IDW" )
        if self.DSMSupported:            
            
            self.Print ("")
            self.Print ("Format nsid = 0 to clear all Attributes")
            self.shell_cmd("nvme format %s -n 1 -l 0 -s 0 -i 0"%self.device)
            
            Block=262144
            #Block=2621440
            Size=self.KMGT(Block*512)
                
            self.Print ("Write  %s blocks(%s), start LBA=0, value=0x5A"%(Block, Size))
            StartT=time.time()
            #self.nvme_write_blocks(0x5A, 0, 1024)
            self.fio_write(0, Block*512, 0x5A, 1)
            StopT=time.time()
            TimeDiv=StopT-StartT
            self.Print( "Run Time: %s"%TimeDiv, "p")
            
            self.Print ("")
            self.Print ("Start to  set  attribute-IDW for %s blocks, start LBA=0"%Block)
            self.shell_cmd("nvme dsm %s -s 0 -b %s -w"%(self.device, Block))
            
            self.Print ("")
            self.Print ("Write  %s blocks(%s), start LBA=0, value=0x5B"%(Block, Size))
            StartT=time.time()
            #self.nvme_write_blocks(0x5A, 0, 1024)
            self.fio_write(0, Block*512, 0x5B, 1)
            StopT=time.time()
            TimeDiv=StopT-StartT
            self.Print( "Run Time: %s"%TimeDiv, "p")
            return 0
        else:
            self.Print("not supported", "w")
            return 255        

    SubCase6TimeOut = 60
    SubCase6Desc = "Test Attribute – Integral Dataset for Read (IDR)"    
    def SubCase6(self):
        self.Print ("Test the read performance of IDR")
        if self.DSMSupported:     
            self.Print ("")
            self.Print ("Format nsid = 0 to clear all Attributes")
            self.shell_cmd("nvme format %s -n 1 -l 0 -s 0 -i 0"%self.device)
            
            Block=262144
            #Block=2621440
            Size=self.KMGT(Block*512)
                
            self.Print ("Read  %s blocks(%s), start LBA=0"%(Block, Size))
            StartT=time.time()
            self.fio_isequal(0, Block*512, 0)
            StopT=time.time()
            TimeDiv=StopT-StartT
            self.Print( "Run Time: %s"%TimeDiv, "p")
            
            self.Print ("")
            self.Print ("Start to  set  attribute-IDR for %s blocks, start LBA=0"%Block)
            self.shell_cmd("nvme dsm %s -s 0 -b %s -r"%(self.device, Block))
            
            self.Print ("")
            self.Print ("Read  %s blocks(%s), start LBA=0"%(Block, Size))
            StartT=time.time()
            self.fio_isequal(0, Block*512, 0)
            StopT=time.time()
            TimeDiv=StopT-StartT
            self.Print( "Run Time: %s"%TimeDiv, "p")
            
            return 0
        else:
            self.Print("not supported", "w")
            return 255   
        
    SubCase7TimeOut = 600
    SubCase7Desc = "Test Context Attributes"
    def SubCase7(self):
        self.Print ("Test Context Attributes for DSM command")
        if self.DSMSupported:    
            ret_code=0        
            self.Print ("")
            self.Print ("Context Attributes total bits=17, Command Access Size: 8, WP: 1, SW: 1, SR: 1, AL: 2, AF: 4")
            self.Print ("Send command with Context Attributes from 0 to 0x1FFFF(17 bits) ")
            self.procStatus=True
            self.procProgress=0
            mThreads = [] 
            # create 16 thread to do task and the CAS high byte = thread number
            for CAS in range(0xF+1):
                # set last thread(CAS = 0xF) to update progress bar            
                if CAS!=0xF:
                    t = threading.Thread(target = self.DoContextAttrText, args=(CAS,False,))
                else:
                    t = threading.Thread(target = self.DoContextAttrText, args=(CAS,True,))
                t.start() 
                mThreads.append(t) 

            # check if all process finished 
            while True:
                allfinished=1
                for process in mThreads:
                    if process.is_alive():
                        allfinished=0
                        break        
                    
                # if all process finished then, quit while loop, else  send reset command
                if allfinished==1:        
                    break
                else:               
                    sleep(1)
                    # print progress whick max is 17 - 4 = 13 bits
                    self.PrintProgressBar(self.procProgress, 0x1FFF, prefix = 'Progress:', length = 50)
                    
            if self.procStatus:
                # print progress with 100 % finish
                self.PrintProgressBar(100, 100, prefix = 'Progress:', length = 50)
                self.Print("Pass","p")
            else:
                self.Print("Fail","f")
                ret_code=1
                                               
            return ret_code
        
            '''
            CA=0
            
                
            for cnt in range(0x1FFFF+1):
                #parser cnt into Context Attributes
                AL_AF =           cnt&0b00000000000111111
                WP_SW_SR =(cnt&0b00000000111000000) >> 6
                CAS =             (cnt&0b11111111000000000) >> 9
                CA=(CAS<<24) + (WP_SW_SR<<8) + (AL_AF)
                
                
                mStr = self.shell_cmd("nvme dsm %s -s 0 -b 1 -r -a %s"%(self.device, CA))
            
                # print progress 
                if cnt%0x1000==0:
                    self.PrintProgressBar(cnt, 0x1FFFF, prefix = 'Progress:', length = 50)
                if not re.search("success", mStr):
                    self.Print ("")
                    self.Print("Fail at Context Attributes = %s"%hex(CA), "f")
                    ret_code = 1
                    sub_ret = 1
                    break
                cnt=cnt+1
            
            if sub_ret==0:
                # print progress with 100 % finish
                self.PrintProgressBar(100, 100, prefix = 'Progress:', length = 50)
                self.Print("Pass","p")
            return ret_code
            '''
            
            
        else:
            self.Print("not supported", "w")
            return 255   

    SubCase8TimeOut = 60
    SubCase8Desc = "Test Namespace Utilization (NUSE)"          
    def SubCase8(self):
        self.Print ("Test the current number of logical blocks allocated in the namespace has changed after deallocation"         )
        ThinProvisioningSupported =True if self.IdNs.NSFEAT.bit(0)=="1" else False
        self.Print ("Thin Provisioning is Supported" if ThinProvisioningSupported else "Thin Provisioning is not Supported")     
        self.Print ("")
        self.Print ("When Thin Provisioning is supported and the DSM command is supported")
        self.Print ("then deallocating LBAs shall be reflected in the Namespace Utilization field(NUSE).")            
        if not ThinProvisioningSupported:
            self.Print ("Thin Provisioning is not Supported, skip", "w" )
            return 255    
            
        if not self.DSMSupported:    
            self.Print("DSM not supported", "w")
            return 255         
        else:   

            # write data to make sure the NUSE is large enought
            self.Print ("Write 1M data to make the NUSE large then 0")
            self.fio_write(0, "1M", 0x5A, 1)            
            self.Print ("")
            self.Print ("Before deallocation ")
            NUSE_B=self.IdNs.NUSE.int
            self.Print( "NUSE: %s"%NUSE_B , "p")
            
            self.Print ("Start to deallocate the first 100 blocks")
            self.shell_cmd("nvme dsm %s -s 0 -b 100 -d"%self.device)
            
            self.Print ("After deallocation ")
            NUSE_A=self.IdNs.NUSE.int
            self.Print( "NUSE: %s"%NUSE_A , "p")


            self.Print ("")
            self.Print ("When Thin Provisioning is supported and the DSM command is supported")
            self.Print ("then deallocating LBAs shall be reflected in the Namespace Utilization field(NUSE).")            
            self.Print ("Check if NUSE has changed or not, expected : Changed")
            if (NUSE_B != NUSE_A):
                self.Print("Pass", "p")
                return 0
            else:
                self.Print("Fail", "f")
                return 1           

    # </sub item scripts> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    
    
    
if __name__ == "__main__":
    DUT = SMI_DSM(sys.argv )
    DUT.RunScript()
    DUT.Finish() 
    
    
    
    
    
