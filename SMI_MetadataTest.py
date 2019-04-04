#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
import re
from random import randint
from time import sleep
import threading
# Import VCT modules
from lib_vct.NVME import NVME


class SMI_MetadataTest(NVME):
    ScriptName = "SMI_MetadataTest.py"
    Author = "Sam Chan"
    Version = "20190326"


    
    def initTestItems(self):
        # self.TestItems=[[LBAF_number, RP, LBADS, MS],[LBAF_number, RP, LBADS, MS],..]   

        for x in range(15):
            RP = self.LBAF[x][self.lbafds.RP]
            LBADS = self.LBAF[x][self.lbafds.LBADS] 
            MS = self.LBAF[x][self.lbafds.MS] 
            if MS!=0 and LBADS>=9:                           
                self.TestItems.append([x, RP, LBADS, MS])
        
    def Format(self, nsid, lbaf, ses, pil=0, pi=0, ms=0):
        # namespace-id, 
        # LBA format, 
        # Secure Erase Settings, 
        # Protection Information Location, 
        # Protection Information,
        # Metadata Settings
        mbuf=self.shell_cmd(" nvme format %s -n %s -l %s -s %s -p %s -i %s -m %s 2>&1"%(self.dev_port, nsid, lbaf, ses, pil, pi, ms))
        return mbuf
    
    def Create_MetadataFile_in(self, startValue, size, isConstant=False):
        # if isConstant, the value will not change, or value = value +1 for every byte
        value=startValue
        List_buf = []
        for i in range(size):
            List_buf.append(value)
            if not isConstant:
                if value<0xFF:
                    value=value+1
                else:
                    value=0          
        self.writeBinaryFileFromList(self.MetadataFile_in_WithThreadname, List_buf)        
    
    @property
    def MetadataFile_in_WithThreadname(self):
        return self.MetadataFile_in + "_" + threading.current_thread().name
    
    @property
    def MetadataFile_out_WithThreadname(self):
        return self.MetadataFile_out + "_" + threading.current_thread().name    

    def WriteMetadatas_AsSeparateBuffer(self, sizePerBlock, startBlock, NLB_CDW12, metadataSize, printInfo=True):
        # write metadata with file MetadataFile_in, and data pattern = 0
        # sizePerBlock, 512/4K
        totalMetadataSize=metadataSize * NLB_CDW12
        size = NLB_CDW12*sizePerBlock
        block_cnt = NLB_CDW12-1        
        mStr = self.shell_cmd("dd if=/dev/zero bs=%s count=%s 2>&1  | nvme write %s -s %s -z %s -c %s -y %s -M %s 2>&1"%(sizePerBlock, NLB_CDW12, self.dev, startBlock,size, block_cnt, totalMetadataSize, self.MetadataFile_in_WithThreadname))
        retCommandSueess=bool(re.search("write: Success", mStr))
        if (retCommandSueess ==  True) :
            self.Print("Done") if printInfo else None  
            return True
        else:
            self.Print("Fail, quit all, write cmd= %s"%self.LastCmd, "f")  if printInfo else None
            return False

    def WriteMetadatas_AsContiguousPartOfLB(self, startBlock, NLB_CDW12, sizePerBlock):
        # write data and metadata with file MetadataFile_in
        # sizePerBlock, 512/4K
        size = NLB_CDW12*sizePerBlock
        block_cnt = NLB_CDW12-1        
        mStr = self.shell_cmd("nvme write %s -s %s -z %s -c %s -d %s 2>&1"%( self.dev, startBlock,size, block_cnt, self.MetadataFile_in_WithThreadname))
        retCommandSueess=bool(re.search("write: Success", mStr))
        if (retCommandSueess ==  True) :
            self.Print("Done")    
            return True
        else:
            self.Print("Fail, quit all, write cmd= %s"%self.LastCmd, "f")
            return False
    
    def CreateRandomLogicBlockDataAndMetadataFile(self, NLB_CDW12, sizePerBlock):
        # write to MetadataFile_in
        numOfByte = sizePerBlock*NLB_CDW12
        self.shell_cmd("dd if=/dev/urandom of=%s bs=%s count=1 2>&1 >/dev/null"%(self.MetadataFile_in_WithThreadname, numOfByte))
        
    def CreateRandomMetadataFile(self, NLB_CDW12, metadataSize):
        # write to MetadataFile_in
        numOfByte = metadataSize*NLB_CDW12
        self.shell_cmd("dd if=/dev/urandom of=%s bs=%s count=1 2>&1 >/dev/null"%(self.MetadataFile_in_WithThreadname, numOfByte))
    
    def GetDismatch_LBA_WriteValue_ReadValue(self, F0, F1, Ttype, startBlock, metadataSize):
        Result = self.isFileTheSame(F0, F1)
        if Result==None:
            return None
        elif Ttype=="Separate":
            byteoffset=Result[0]
            LBAoffset=(byteoffset-1)/metadataSize
            LBA=startBlock+LBAoffset
            return [LBA, Result[1], Result[2]]
            
            
        
    
    def CheckBlockMetadatas_AsSeparateBuffer(self, sizePerBlock,startBlock, NLB_CDW12, metadataSize,printInfo=True):
        # read metadata to file MetadataFile_out, and compare with MetadataFile_in
        # startBlock=0, NLB_CDW12=2, metadataSize=8
        totalMetadataSize=metadataSize * NLB_CDW12
        size = NLB_CDW12*sizePerBlock
        block_cnt = NLB_CDW12-1    
        FileOut=self.MetadataFile_out_WithThreadname
        FileIn=self.MetadataFile_in_WithThreadname
                                     
        self.Print("Get metadata from block: %s, number of block: %s, and save to file(%s)"%(startBlock, NLB_CDW12, FileOut)) if printInfo else None

        self.shell_cmd("nvme read %s -s %s -z %s -c %s -y %s -M %s 2>&1 >/dev/null"%(self.dev, startBlock,size, block_cnt, totalMetadataSize, FileOut))
        sleep(0.5)
        if self.isfileExist(FileOut):
            self.Print("Done") if printInfo else None
        else:
            self.Print("Fail to read metadata, quit all", "f") if printInfo else None
            self.rmFile(FileOut)
            return False                
        '''
        self.Print("Check if metadata in first block is 0x0")
        mList = self.readBinaryFileToList(FileOut)
        self.Print("metadata: %s"%mList)            
        '''
        self.Print("Check if metadata from controller(%s) and %s are the same"%(FileOut, FileIn)) if printInfo else None
        # if MetadataFile_out = MetadataFile_in, then pass
        self.CompareResult=self.GetDismatch_LBA_WriteValue_ReadValue(FileOut, FileIn, "Separate", startBlock, metadataSize)
        if self.CompareResult==None:
            self.Print("Pass", "p")  if printInfo else None
        else:
            self.Print("Fail", "f") if printInfo else None
            self.rmFile(FileOut)
            return False                 
        self.rmFile(FileOut)
        return True
    
    # ----------------------------------------------------------------------------------------------              
    def CheckBlockMetadatas_AsContiguousPartOfLB(self, startBlock, NLB_CDW12,sizePerBlock):
        # read metadata to file MetadataFile_out, and compare with MetadataFile_in
        # startBlock=0, NLB_CDW12=2, metadataSize=8
        size = NLB_CDW12*sizePerBlock
        block_cnt = NLB_CDW12-1    
            
        self.rmFile(self.MetadataFile_out_WithThreadname)
                                   
        self.Print("Get metadata from block: %s, number of block: %s, and save to file(%s)"%(startBlock, NLB_CDW12, self.MetadataFile_out_WithThreadname))

        self.shell_cmd("nvme read %s -s %s -z %s -c %s -d %s 2>&1 >/dev/null"%(self.dev, startBlock,size, block_cnt, self.MetadataFile_out_WithThreadname))
        sleep(0.5)
        if self.isfileExist(self.MetadataFile_out_WithThreadname):
            self.Print("Done")
        else:
            self.Print("Fail to read metadata, quit all", "f")
            return False                

        self.Print("Check if data and metadata from controller(%s) and %s are the same"%(self.MetadataFile_out_WithThreadname, self.MetadataFile_in_WithThreadname))            
        # if MetadataFile_out = MetadataFile_in, then pass
        if self.isFileTheSame(self.MetadataFile_out_WithThreadname, self.MetadataFile_in_WithThreadname)==None:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")   
            return False                 

        return True
    # ----------------------------------------------------------------------------------------------  
    def FormatNS(self, LBAF_num, MetadataSetting): 
        self.Print("Format namespace 1 to LBAF %s with Metadata Settings (MSET)= %s"%(LBAF_num, MetadataSetting))                  
        mStr=self.Format(nsid=1, lbaf = LBAF_num, ses=0, pil=0, pi=0, ms=MetadataSetting)
        if re.search("Success formatting namespace", mStr):
            self.Print("Done")
        else:
            self.Print("Fail to format namespace1, quit all, cmd: %s"%self.LastCmd, "f")
            return 1        

        self.Print("")
        FLBAS_bit4 = 1 if (self.IdNs.FLBAS.int&0x10)>0 else 0
        self.Print("Formatted LBA Size (FLBAS) bit 4 : %s"%FLBAS_bit4)           
        if MetadataSetting==0:
            self.Print("Check if Formatted LBA Size (FLBAS) bit 4 was cleared to ‘0’ indicates that all of the metadata for a command is transferred as a separate contiguous buffer of data") 
            if FLBAS_bit4==0:
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")
                return False
        else:
            self.Print("Check if Formatted LBA Size (FLBAS) bit 4 was set to ‘1’ indicates that the metadata is transferred at the end of the data LBA")
            if FLBAS_bit4==1 :
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")
                return False  
        
        return True
    # ----------------------------------------------------------------------------------------------                
    
    def Test_Write_Read_AsSeparateBuffer(self, startBlock, NLB_CDW12, sizePerBlock, metadataSize, printInfo=True):
        # sizePerBlock, 512/4K
        # create metadata file
        self.CreateRandomMetadataFile(NLB_CDW12=NLB_CDW12, metadataSize =metadataSize)
        if not self.WriteMetadatas_AsSeparateBuffer(sizePerBlock=sizePerBlock, startBlock=startBlock , NLB_CDW12=NLB_CDW12 , metadataSize=metadataSize, printInfo=printInfo):
            return False
          
        self.Print("")  if printInfo else None
        # verify 
        self.Print("check if metadata in first %s block and file %s are the same"%(NLB_CDW12, self.MetadataFile_in_WithThreadname)) if printInfo else None 
        if not self.CheckBlockMetadatas_AsSeparateBuffer(sizePerBlock=sizePerBlock,startBlock=startBlock, NLB_CDW12=NLB_CDW12, metadataSize=metadataSize, printInfo=printInfo):
            return False  
           
        self.Print("") if printInfo else None                                       
        return True        
    
    def Test_Write_Read_AsContiguousPartOfLB(self, startBlock, NLB_CDW12, sizePerBlock):
        if not self.WriteMetadatas_AsContiguousPartOfLB(startBlock, NLB_CDW12 , sizePerBlock):
            return False 
            
        self.Print("")
        # verify 
        self.Print("check if metadata in first %s block and file %s are the same"%(NLB_CDW12, self.MetadataFile_in_WithThreadname))    
        if not self.CheckBlockMetadatas_AsContiguousPartOfLB(startBlock, NLB_CDW12,sizePerBlock):
            return False         
        return True   
    
    def Test_Write_Read_AsSeparateBuffer_OneThread(self, startBlock, stopBlock, maximumNLB, sizePerBlock, metadataSize, printInfo=False):
        # loop for the test, if all  block has been test or other thread fail or this thread fail, then return
        
        finished=False
        while True:
            # read blkPtr and allPass           
            
            self.lock.acquire()
            mPtr=self.blkPtr
            NLB=stopBlock-mPtr
            NLB= maximumNLB if NLB>maximumNLB else NLB
            allPass=self.allPass
            if mPtr>=stopBlock or not allPass:
                finished=True
            else:            
                self.blkPtr=self.blkPtr+NLB
            self.lock.release()
            
            if finished:
                return
            
            # if not pass, set self.allPass=false and set failAtStartBlk, failAtStopBlk, then return
            if self.mTestModeOn:
                self.Print(threading.current_thread().name+", Ptr: %s, NLB: %s"%(mPtr, NLB))
            if not self.Test_Write_Read_AsSeparateBuffer(mPtr, NLB, sizePerBlock, metadataSize, printInfo):
                self.allPass=False
                self.failAtStartBlk=mPtr
                self.failAtStopBlk=mPtr+NLB
                self.failAtThread=threading.current_thread().name
                return
    
    def Test_Write_Read_AsSeparateBuffer_MultiThread(self, thread, startBlock, stopBlock, NLB_CDW12, printInfo=False):         
        thread_w=thread
        sizePerBlock=self.GetBlockSize()   
        metadataSize=self.IdNs.LBAFinUse[1]                
        RetThreads = []        
        for i in range(thread_w):   
            t = threading.Thread(target = self.Test_Write_Read_AsSeparateBuffer_OneThread, args=(startBlock, stopBlock, NLB_CDW12, sizePerBlock, metadataSize, printInfo))
            t.start() 
            RetThreads.append(t)     
        return RetThreads    
    
    def PrintProgress(self):      
        totalBlk=self.blkLast-self.blkFirst
        if not self.mTestModeOn:
            self.PrintProgressBar(self.blkPtr, totalBlk, prefix = 'Write area:',suffix="", length = 50)
    
    def __init__(self, argv):
        # initial parent class
        super(SMI_MetadataTest, self).__init__(argv)
        
        self.NLBAF=self.IdNs.NLBAF.int
        self.LBAF=self.GetAllLbaf()
        self.TestItems=[]
        self.initTestItems()

        self.MetadataFile_out = "MetadataFile_out"
        self.MetadataFile_in = "MetadataFile_in"
        
        self.CompareResult=[]
        
        # thread valueable
        self.lock=threading.Lock()
        self.blkPtr=0
        self.allPass=True   # all thread is pass
        self.failAtStartBlk=0    # test fail at start block to stop block
        self.failAtStopBlk=0  
        self.failAtThread="None"  
        self.blkFirst=0
        self.blkLast=0


    # define pretest  
    def PreTest(self):        
        
        self.Print ("Number of LBA formats (self.NLBAF): %s"%self.NLBAF)
        self.Print ("If LBA format support metadata, list the LBAFs")     
        if not self.TestItems:
            self.Print ("All the LBA format does't support metadata, quit all the test case!")
            return False
        else:
            for Item in self.TestItems:
                self.Print("LBAF %s, RP: %s, LBADS: %s, MS: %s"%(Item[0], Item[1], Item[2], Item[3])) 
           
        return True            

    # <define sub item scripts>
    SubCase1TimeOut = 60
    SubCase1Desc = "Metadata test -  Transferred as Separate Buffer"   
    SubCase1KeyWord = ""
    def SubCase1(self):
        ret_code=0
        self.Print("")
        self.Print("Metadata test")
        #self.Print("Mechanism for transferring the metadata is 'as a ontiguous part of the logical block'")
        #MetadataSetting=1
        self.Print("Test mechanism for transferring the metadata is 'separate buffer of data'")
        MetadataSetting= 0

        for Item in self.TestItems:
            self.Print("----------------------------------------")
            self.Print("")
            self.Print("LBAF %s, RP: %s, LBADS: %s, MS: %s"%(Item[0], Item[1], Item[2], Item[3])) 
            LBAF_num = Item[0]
            RP = Item[1]
            LBADS = Item[2]
            MS = Item[3]      
            # LBADS=9, testblock=1, LBADS=12, testblock=8, etc
            sizePerBlock=512*pow(2,(LBADS-9))
            # format namespace
            if not self.FormatNS(LBAF_num, MetadataSetting):
                return 1
            
            # test write and read for minBlock
            testBlock=1
            self.Print("")
            self.Print("Write metadata to controller(file %s), start from LBA0, number of blocks is %s(the minimum data transfer size)"%(self.MetadataFile_in_WithThreadname, testBlock))
            if not self.Test_Write_Read_AsSeparateBuffer(startBlock=0, NLB_CDW12=testBlock, sizePerBlock=sizePerBlock, metadataSize=MS, printInfo=True):
                return 1        
            
            # test write and read for maxBlock
            testBlock=self.MDTSinByte/sizePerBlock
            self.Print("")
            self.Print("Write metadata to controller(file %s), start from LBA0, number of blocks is %s(the maximum data transfer size)"%(self.MetadataFile_in_WithThreadname, hex(testBlock)))
            if not self.Test_Write_Read_AsSeparateBuffer(startBlock=0, NLB_CDW12=testBlock, sizePerBlock=sizePerBlock, metadataSize=MS, printInfo=True):
                return 1 
        
        return ret_code


    # <define sub item scripts>
    SubCase2TimeOut = 60
    SubCase2Desc = "Metadata test -  Transferred as a contiguous part of the logical block that it is associated with"   
    SubCase2KeyWord = ""
    def SubCase2(self):
        ret_code=0
        self.Print("")
        self.Print("Test mechanism for transferring the metadata is 'as a ontiguous part of the logical block'")
        MetadataSetting=1


        for Item in self.TestItems:
            self.Print("----------------------------------------")
            self.Print("")
            self.Print("LBAF %s, RP: %s, LBADS: %s, MS: %s"%(Item[0], Item[1], Item[2], Item[3])) 
            LBAF_num = Item[0]
            RP = Item[1]
            LBADS = Item[2]
            MS = Item[3]            
            # LBADS=9, testblock=1, LBADS=12, testblock=8, etc
            sizePerBlock=512*pow(2,(LBADS-9)) + MS
            # format namespace
            if not self.FormatNS(LBAF_num, MetadataSetting):
                return 1
            
            
            # test write and read for minBlock
            testBlock=1
            self.Print("")            
            self.Print("Write random patten of data with metadata to controller(file %s), start from LBA0, number of blocks is %s"%(self.MetadataFile_in_WithThreadname, testBlock))
            # create metadata file
            self.CreateRandomLogicBlockDataAndMetadataFile(NLB_CDW12=testBlock,sizePerBlock=sizePerBlock)            
            if not self.Test_Write_Read_AsContiguousPartOfLB(startBlock=0 , NLB_CDW12=testBlock ,sizePerBlock=sizePerBlock):
                return 1                                             

            # test write and read for maxBlock
            testBlock=self.MDTSinByte/sizePerBlock
            self.Print("")
            self.Print("Write random patten of data with metadata to controller(file %s), start from LBA0, number of blocks is %s"%(self.MetadataFile_in_WithThreadname, testBlock))
            # create metadata file
            self.CreateRandomLogicBlockDataAndMetadataFile(NLB_CDW12=testBlock,sizePerBlock=sizePerBlock)            
            if not self.Test_Write_Read_AsContiguousPartOfLB(startBlock=0 , NLB_CDW12=testBlock ,sizePerBlock=sizePerBlock):
                return 1   
        
        return ret_code



    SubCase3TimeOut = 60
    SubCase3Desc = "Metadata test -  Transferred as Separate Buffer, test 1G data"   
    SubCase3KeyWord = ""
    def SubCase3(self):
        ret_code=0
        self.Print("")
        self.Print("Metadata test")
        #self.Print("Mechanism for transferring the metadata is 'as a ontiguous part of the logical block'")
        #MetadataSetting=1
        self.Print("Test mechanism for transferring the metadata is 'separate buffer of data'")
        MetadataSetting= 0

        if self.TestItems!=None:
            self.Print("----------------------------------------")
            self.Print("")
            Item=self.TestItems[0]
            self.Print("LBAF %s, RP: %s, LBADS: %s, MS: %s"%(Item[0], Item[1], Item[2], Item[3])) 
            LBAF_num = Item[0]
            RP = Item[1]
            LBADS = Item[2]
            MS = Item[3]      
            # LBADS=9, testblock=1, LBADS=12, testblock=8, etc
            sizePerBlock=512*pow(2,(LBADS-9))
            # format namespace
            if not self.FormatNS(LBAF_num, MetadataSetting):
                return 1
            
            
            
                      
            thread=32
            startBlock=0 
            #stopBlock=1023
            stopBlock=65535
            NLB_CDW12=self.MaxNLBofCDW12() 
            printInfo=False               
            # initial progress bar parameter
            self.blkFirst=startBlock
            self.blkLast=stopBlock
            
            #timer
            self.timer.start()
                        
            # write data using multi thread
            mThreads = self.Test_Write_Read_AsSeparateBuffer_MultiThread(thread, startBlock, stopBlock, NLB_CDW12,  printInfo)
            
            # check if all process finished             
            while True:        
                allfinished=1
                for process in mThreads:
                    if process.is_alive():
                        allfinished=0
                        break
            
                # if all process finished then, quit while loop,
                if allfinished==1:        
                    break
                else:              
                    #print progress bar    
                    self.PrintProgress()           
                    sleep(0.5)                          
            self.timer.stop()
            
            self.Print("")
            #check result
            if self.allPass:
                self.Print("Pass, time usage: %s"%self.timer.time, "p")
            else:
                self.Print("Fail", "f")
                self.Print("Failure block: %s on %s"%(hex(self.failAtStartBlk), self.failAtThread), "f")
        
        return ret_code
    
    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        if not self.mTestModeOn:
            # remove file            
            #self.rmFile(self.MetadataFile_out_WithThreadname)
            #self.rmFile(self.MetadataFile_in_WithThreadname)     
            pass
           
        return True 
    
if __name__ == "__main__":
    DUT = SMI_MetadataTest(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    