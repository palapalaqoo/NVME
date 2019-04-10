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
from __builtin__ import False


class SMI_MetadataTest(NVME):
    ScriptName = "SMI_MetadataTest.py"
    Author = "Sam Chan"
    Version = "20190410"


    
    def initTestItems(self):
        # self.TestItems=[[LBAF_number, RP, LBADS, MS],[LBAF_number, RP, LBADS, MS],..]   

        for x in range(15):
            RP = self.LBAF[x][self.lbafds.RP]
            LBADS = self.LBAF[x][self.lbafds.LBADS] 
            MS = self.LBAF[x][self.lbafds.MS] 
            if MS!=0 and LBADS>=9:                           
                self.TestItems.append([x, RP, LBADS, MS])
                
    def initNsTestItems(self):
        # self.NsTestItems=[[LBAF_num, RP, LBADS, MS, Type, MetadataSetting, NSID, sizePerBlock],..]   

        # number of NS that will be created and test, each TestItems have 2 transferring mechanism
        # and this test will try to include all the mechanism(NumOfNS must <= NN)
        NumOfNS=len(self.TestItems)*2        
        NN = self.IdCtrl.NN.int
        NumOfNS = NN if NumOfNS>NN else NumOfNS
        
        nsid=1
        #  append  Separate
        for Item in self.TestItems:
            LBAF_num = Item[0]
            RP = Item[1]
            LBADS = Item[2]
            MS = Item[3] 
            Type = "Separate"
            MetadataSetting = 0
            NSID = nsid
            sizePerBlock=512*pow(2,(LBADS-9))
            self.NsTestItems.append([LBAF_num, RP, LBADS, MS, Type, MetadataSetting, NSID, sizePerBlock])
            # nsid ++
            nsid = nsid +1
            if nsid>NumOfNS:
                return
        #  append  Contiguous
        for Item in self.TestItems:
            LBAF_num = Item[0]
            RP = Item[1]
            LBADS = Item[2]
            MS = Item[3] 
            Type = "Contiguous"
            MetadataSetting = 1
            NSID = nsid
            sizePerBlock=512*pow(2,(LBADS-9)) + MS
            self.NsTestItems.append([LBAF_num, RP, LBADS, MS, Type, MetadataSetting, NSID, sizePerBlock])
            # nsid ++
            nsid = nsid +1
            if nsid>NumOfNS:
                return                        
        
        
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

    def WriteMetadatas_AsSeparateBuffer(self, sizePerBlock, startBlock, NLB_CDW12, metadataSize, printInfo=True, nsid=1):
        # write metadata with file MetadataFile_in, and data pattern = 0
        # sizePerBlock, 512/4K
        totalMetadataSize=metadataSize * (NLB_CDW12+1)
        size = (NLB_CDW12+1)*sizePerBlock
        block_cnt = NLB_CDW12        
        mDev=self.dev_port + "n%s"%nsid
        mStr = self.shell_cmd("dd if=/dev/zero bs=%s count=%s 2>&1  | nvme write %s -s %s -z %s -c %s -y %s -M %s 2>&1"%(sizePerBlock, NLB_CDW12, mDev, startBlock,size, block_cnt, totalMetadataSize, self.MetadataFile_in_WithThreadname))
        retCommandSueess=bool(re.search("write: Success", mStr))
        if (retCommandSueess ==  True) :
            self.Print("Done") if printInfo else None  
            return True
        else:
            self.Print("Fail, quit all, write cmd:  %s"%self.LastCmd, "f")  if printInfo else None
            return False

    def WriteMetadatas_AsContiguousPartOfLB(self, startBlock, NLB_CDW12, sizePerBlock, printInfo=False, nsid=1):
        # write data and metadata with file MetadataFile_in
        # sizePerBlock, 512/4K
        size = (NLB_CDW12+1)*sizePerBlock
        block_cnt = NLB_CDW12        
        mDev=self.dev_port + "n%s"%nsid
        mStr = self.shell_cmd("nvme write %s -s %s -z %s -c %s -d %s 2>&1"%( mDev, startBlock,size, block_cnt, self.MetadataFile_in_WithThreadname))
        retCommandSueess=bool(re.search("write: Success", mStr))
        if (retCommandSueess ==  True) :
            self.Print("Done") if printInfo else None  
            return True
        else:
            self.Print("Fail, quit all, write cmd:  %s"%self.LastCmd, "f") if printInfo else None  
            return False
    
    def CreateRandomLogicBlockDataAndMetadataFile(self, NLB_CDW12, sizePerBlock):
        # write to MetadataFile_in
        numOfByte = sizePerBlock*(NLB_CDW12+1)
        self.shell_cmd("dd if=/dev/urandom of=%s bs=%s count=1 2>&1 >/dev/null"%(self.MetadataFile_in_WithThreadname, numOfByte))
        
    def CreateRandomMetadataFile(self, NLB_CDW12, metadataSize):
        # write to MetadataFile_in
        numOfByte = metadataSize*(NLB_CDW12+1)
        self.shell_cmd("dd if=/dev/urandom of=%s bs=%s count=1 2>&1 >/dev/null"%(self.MetadataFile_in_WithThreadname, numOfByte))
    
    def GetDismatch_LBA_WriteValue_ReadValue(self, F0, F1, Ttype, startBlock, cmpareDataSize):
        Result = self.isFileTheSame(F0, F1)
        if Result==None:
            return None
        elif Ttype=="Separate":
            byteoffset=Result[0]
            LBAoffset=(byteoffset-1)/cmpareDataSize
            LBA=startBlock+LBAoffset
            return [LBA, Result[1], Result[2]]
        elif  Ttype=="Contiguous":
            byteoffset=Result[0]
            LBAoffset=(byteoffset-1)/cmpareDataSize
            LBA=startBlock+LBAoffset
            return [LBA, Result[1], Result[2]]            
            
            
        
    
    def CheckBlockMetadatas_AsSeparateBuffer(self, sizePerBlock,startBlock, NLB_CDW12, metadataSize,printInfo=True, nsid=1):
        # read metadata to file MetadataFile_out, and compare with MetadataFile_in
        # startBlock=0, NLB_CDW12=2, metadataSize=8
        totalMetadataSize=metadataSize * (NLB_CDW12+1)
        size = (NLB_CDW12+1)*sizePerBlock
        block_cnt = NLB_CDW12    
        FileOut=self.MetadataFile_out_WithThreadname
        FileIn=self.MetadataFile_in_WithThreadname
        mDev=self.dev_port + "n%s"%nsid
        
        self.rmFile(FileOut)
                                     
        self.Print("Get metadata from block: %s, number of block: %s, and save to file(%s)"%(startBlock, NLB_CDW12, FileOut)) if printInfo else None

        self.shell_cmd("nvme read %s -s %s -z %s -c %s -y %s -M %s 2>&1 >/dev/null"%(mDev, startBlock,size, block_cnt, totalMetadataSize, FileOut))
        
        if self.isfileExist(FileOut):
            self.Print("Done") if printInfo else None
        else:
            self.Print("Fail to read metadata, quit all", "f") if printInfo else None
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
            return False                 
        return True
    
    # ----------------------------------------------------------------------------------------------              
    def CheckBlockMetadatas_AsContiguousPartOfLB(self, startBlock, NLB_CDW12,sizePerBlock, printInfo=False, nsid=1):
        # read metadata to file MetadataFile_out, and compare with MetadataFile_in
        # startBlock=0, NLB_CDW12=2, metadataSize=8
        size = (NLB_CDW12+1)*sizePerBlock
        block_cnt = NLB_CDW12    
        FileOut=self.MetadataFile_out_WithThreadname
        FileIn=self.MetadataFile_in_WithThreadname    
        mDev=self.dev_port + "n%s"%nsid    
            
        self.rmFile(FileOut)
                                   
        self.Print("Get metadata from block: %s, number of block: %s, and save to file(%s)"%(startBlock, NLB_CDW12, FileOut))  if printInfo else None

        self.shell_cmd("nvme read %s -s %s -z %s -c %s -d %s 2>&1 >/dev/null"%(mDev, startBlock,size, block_cnt, FileOut))
        
        if self.isfileExist(FileOut):
            self.Print("Done")  if printInfo else None
        else:
            self.Print("Fail to read metadata, quit all", "f")
            return False                

        self.Print("Check if data and metadata from controller(%s) and %s are the same"%(FileOut, FileIn))  if printInfo else None            
        # if MetadataFile_out = MetadataFile_in, then pass
        self.CompareResult=self.GetDismatch_LBA_WriteValue_ReadValue(FileOut, FileIn, "Contiguous", startBlock, sizePerBlock)
        if self.CompareResult==None:
            self.Print("Pass", "p")  if printInfo else None
        else:
            self.Print("Fail", "f") if printInfo else None
            return False                 
        return True        
        
    # ----------------------------------------------------------------------------------------------  
    def FormatNS(self, LBAF_num, MetadataSetting, nsid=1, printInfo=True): 
        self.Print("Format namespace 1 to LBAF %s with Metadata Settings (MSET)= %s"%(LBAF_num, MetadataSetting)) if printInfo else None                  
        mStr=self.Format(nsid=nsid, lbaf = LBAF_num, ses=0, pil=0, pi=0, ms=MetadataSetting)
        if re.search("Success formatting namespace", mStr):
            self.Print("Done")  if printInfo else None
        else:
            self.Print("Fail to format namespace1, quit all, cmd: %s"%self.LastCmd, "f") if printInfo else None
            return False        

        self.Print("") if printInfo else None
        
        mDev=self.dev_port + "n%s"%nsid
        mStr="nvme id-ns %s |grep 'flbas' |cut -d ':' -f 2 |sed 's/[^0-9a-zA-Z]*//g'" %(mDev)
        FLBAS=int(self.shell_cmd(mStr), 16)
        FLBAS_bit4 = 1 if (FLBAS&0x10)>0 else 0        
        
        self.Print("Formatted LBA Size (FLBAS) bit 4 : %s"%FLBAS_bit4) if printInfo else None           
        if MetadataSetting==0:
            self.Print("Check if Formatted LBA Size (FLBAS) bit 4 was cleared to '0' indicates that all of the metadata for a command is transferred as a separate contiguous buffer of data") if printInfo else None
            if FLBAS_bit4==0:
                self.Print("Pass", "p") if printInfo else None
            else:
                self.Print("Fail", "f") if printInfo else None
                return False
        else:
            self.Print("Check if Formatted LBA Size (FLBAS) bit 4 was set to '1' indicates that the metadata is transferred at the end of the data LBA") if printInfo else None
            if FLBAS_bit4==1 :
                self.Print("Pass", "p") if printInfo else None
            else:
                self.Print("Fail", "f") if printInfo else None
                return False  
        
        return True
    # ----------------------------------------------------------------------------------------------                
    def rmTemporaryfiles(self):
        FileOut=self.MetadataFile_out_WithThreadname
        FileIn=self.MetadataFile_in_WithThreadname
        self.rmFile(FileOut)
        self.rmFile(FileIn)
                    
    def Test_Write_Read_AsSeparateBuffer(self, startBlock, NLB_CDW12, sizePerBlock, metadataSize, printInfo=True, nsid=1):
        # sizePerBlock, 512/4K
        if not self.WriteMetadatas_AsSeparateBuffer(sizePerBlock=sizePerBlock, startBlock=startBlock , NLB_CDW12=NLB_CDW12 , metadataSize=metadataSize, printInfo=printInfo, nsid=nsid):
            return False
          
        self.Print("")  if printInfo else None
        # verify 
        self.Print("check if metadata in first %s block and file %s are the same"%(NLB_CDW12, self.MetadataFile_in_WithThreadname)) if printInfo else None 
        if not self.CheckBlockMetadatas_AsSeparateBuffer(sizePerBlock=sizePerBlock,startBlock=startBlock, NLB_CDW12=NLB_CDW12, metadataSize=metadataSize, printInfo=printInfo, nsid=nsid):
            return False  
           
        self.Print("") if printInfo else None                                       
        return True        
    
    def Test_Write_Read_AsContiguousPartOfLB(self, startBlock, NLB_CDW12, sizePerBlock, printInfo=False, nsid=1):
        if not self.WriteMetadatas_AsContiguousPartOfLB(startBlock, NLB_CDW12 , sizePerBlock, printInfo=False, nsid=nsid):
            return False 
            
        self.Print("") if printInfo else None  
        # verify 
        self.Print("check if metadata in first %s block and file %s are the same"%(NLB_CDW12, self.MetadataFile_in_WithThreadname)) if printInfo else None      
        if not self.CheckBlockMetadatas_AsContiguousPartOfLB(startBlock, NLB_CDW12,sizePerBlock, printInfo=False, nsid=nsid):
            return False         
        return True   
    
    def Test_Write_Read_AsSeparateBuffer_OneThread(self, startBlock, stopBlock, maximumNLB, sizePerBlock, metadataSize, printInfo=False):
        # loop for the test, if all  block has been test or other thread fail or this thread fail, then return
        # create metadata file
        self.rmTemporaryfiles()
        self.CreateRandomMetadataFile(NLB_CDW12=maximumNLB, metadataSize =metadataSize)        
        finished=False
        while True:
            # read blkPtr and allPass           
            
            self.lock.acquire()
            mPtr=self.blkPtr
            NLB=stopBlock-mPtr
            NLB= maximumNLB if NLB>maximumNLB else NLB
            if NLB!=maximumNLB:
                self.rmTemporaryfiles()
                self.CreateRandomMetadataFile(NLB_CDW12=NLB, metadataSize =metadataSize)    
            allPass=self.allPass
            if mPtr>=stopBlock or not allPass:
                finished=True
            else:            
                self.blkPtr=self.blkPtr+NLB+1
            self.lock.release()
            
            if finished:
                self.rmTemporaryfiles()
                return
            
            # if not pass, set self.allPass=false and set failAtStartBlk, failAtStopBlk, then return
            if self.mTestModeOn:
                self.Print(threading.current_thread().name+", Ptr: %s, NLB: %s"%(mPtr, NLB))
            if not self.Test_Write_Read_AsSeparateBuffer(mPtr, NLB, sizePerBlock, metadataSize, printInfo):
                self.allPass=False
                self.failAtStartBlk=mPtr
                self.failAtStopBlk=mPtr+NLB
                self.failAtThread=threading.current_thread().name
                self.rmTemporaryfiles()
                return
        self.rmTemporaryfiles()
        
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
    #-----------------------------------------------------------------------------------------------------------------
    def Test_Write_Read_AsContiguousPartOfLB_OneThread(self, startBlock, stopBlock, maximumNLB, sizePerBlock, metadataSize, printInfo=False):
        # loop for the test, if all  block has been test or other thread fail or this thread fail, then return
        
        # create metadata file for max NLB
        self.rmTemporaryfiles()
        self.CreateRandomLogicBlockDataAndMetadataFile(NLB_CDW12=maximumNLB,sizePerBlock=sizePerBlock)
        
        
        finished=False
        while True:
            # read blkPtr and allPass                       
            self.lock.acquire()
            mPtr=self.blkPtr
            NLB=stopBlock-mPtr
            NLB= maximumNLB if NLB>maximumNLB else NLB
            if NLB!=maximumNLB:
                # create metadata file if last write and nlb!=maximumNLB
                self.rmTemporaryfiles()
                self.CreateRandomLogicBlockDataAndMetadataFile(NLB_CDW12=NLB,sizePerBlock=sizePerBlock)      
                      
            allPass=self.allPass
            if mPtr>=stopBlock or not allPass:
                finished=True
            else:            
                self.blkPtr=self.blkPtr+NLB+1
            self.lock.release()
            
            if finished:
                self.rmTemporaryfiles()
                return
            
            # if not pass, set self.allPass=false and set failAtStartBlk, failAtStopBlk, then return
            if self.mTestModeOn:
                self.Print(threading.current_thread().name+", Ptr: %s, NLB: %s"%(mPtr, NLB))
            if not self.Test_Write_Read_AsContiguousPartOfLB(mPtr, NLB, sizePerBlock, printInfo):
                self.allPass=False
                self.failAtStartBlk=mPtr
                self.failAtStopBlk=mPtr+NLB
                self.failAtThread=threading.current_thread().name
                self.rmTemporaryfiles()
                return 
        self.rmTemporaryfiles()
        
    def Test_Write_Read_AsContiguousPartOfLB_MultiThread(self, thread, startBlock, stopBlock, NLB_CDW12, printInfo=False):         
        thread_w=thread
        sizePerBlock=self.GetBlockSize()   
        metadataSize=self.IdNs.LBAFinUse[1]                
        RetThreads = []        
        for i in range(thread_w):   
            t = threading.Thread(target = self.Test_Write_Read_AsContiguousPartOfLB_OneThread, args=(startBlock, stopBlock, NLB_CDW12, sizePerBlock, metadataSize, printInfo))
            t.start() 
            RetThreads.append(t)     
        return RetThreads    


    def CompareNsMetadatas(self, expectedDataChangedNsid):
        # return 0 = pass, or the error nsid 
        for Item in self.NsTestItems:
            NSID = Item[6]
            fileName=self.MetadataFile_NsBk
            F0=fileName+"_ns%s"%NSID
            fileName=self.MetadataFile_NsCur
            F1=fileName+"_ns%s"%NSID            
            
            Result = self.isFileTheSame(F0, F1)
            TheSame=True if Result==None else False
            # if files are the same and is expected to be changed
            if TheSame and expectedDataChangedNsid==NSID: 
                return NSID
            # if files are not same and is not expected to be changed
            if not TheSame and expectedDataChangedNsid!=NSID: 
                return NSID   
            
        return 0            
        



    def WriteNsMetadatasAndVerify(self, nsid ):
        # get current nsid parameters
        mItem=[]
        for Item in self.NsTestItems:
            if nsid==Item[6] :
                mItem=Item
                
        Item = mItem
        MS = Item[3]   
        Type = Item[4] 
        NSID = Item[6] 
        sizePerBlock = Item[7]     
        startBlock=0
        NLB_CDW12=0
        
        self.rmTemporaryfiles()
        if Type=="Separate":
            self.CreateRandomMetadataFile(NLB_CDW12=NLB_CDW12, metadataSize =MS)
            if not self.Test_Write_Read_AsSeparateBuffer(startBlock=startBlock, NLB_CDW12=NLB_CDW12, sizePerBlock=sizePerBlock, metadataSize=MS, printInfo=False, nsid=NSID):
                self.rmTemporaryfiles()
                return False
                        
        else:  # Contiguous            
            self.CreateRandomLogicBlockDataAndMetadataFile(NLB_CDW12=NLB_CDW12,sizePerBlock=sizePerBlock)            
            if not self.Test_Write_Read_AsContiguousPartOfLB(startBlock=startBlock , NLB_CDW12=NLB_CDW12 ,sizePerBlock=sizePerBlock, printInfo=False, nsid=NSID):
                return False              
            
        return True

    def ReadNsMetadatasToFile_backup(self, sizePerBlock,startBlock, NLB_CDW12, metadataSize,printInfo=True):
        return self.ReadNsMetadatasToFile( sizePerBlock,startBlock, NLB_CDW12, metadataSize, self.MetadataFile_NsBk, printInfo)
        
    def ReadNsMetadatasToFile_current(self, sizePerBlock,startBlock, NLB_CDW12, metadataSize,printInfo=True):
        return self.ReadNsMetadatasToFile( sizePerBlock,startBlock, NLB_CDW12, metadataSize, self.MetadataFile_NsCur, printInfo)
        
    def ReadNsMetadatasToFile(self, sizePerBlock,startBlock, NLB_CDW12, metadataSize, fileName, printInfo=True):
        
        for Item in self.NsTestItems:
            LBAF_num = Item[0]
            RP = Item[1]
            LBADS = Item[2]
            MS = Item[3]   
            Type = Item[4] 
            MetadataSetting = Item[5] 
            NSID = Item[6] 
            sizePerBlock = Item[7]       
            mDev=self.dev_port + "n%s"%NSID
            
            if Type=="Separate":           
                totalMetadataSize=metadataSize * (NLB_CDW12+1)
                size = (NLB_CDW12+1)*sizePerBlock
                block_cnt = NLB_CDW12    
                FileOut=fileName+"_ns%s"%NSID
                self.rmFile(FileOut)
                self.shell_cmd("nvme read %s -s %s -z %s -c %s -y %s -M %s 2>&1 >/dev/null"%(mDev, startBlock,size, block_cnt, totalMetadataSize, FileOut))
            else: # Contiguous
                size = (NLB_CDW12+1)*sizePerBlock
                block_cnt = NLB_CDW12    
                FileOut=fileName+"_ns%s"%NSID
                self.rmFile(FileOut)
                self.shell_cmd("nvme read %s -s %s -z %s -c %s -d %s 2>&1 >/dev/null"%(mDev, startBlock,size, block_cnt, FileOut))
                
            if not self.isfileExist(FileOut):
                return False
            
        return True    
                        

    
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
        
        # create temp folder
        self.TempFolderName = "./temp"
        self.InitFolder(self.TempFolderName)
        self.MetadataFile_out = self.TempFolderName + "/MetadataFile_out"
        self.MetadataFile_in = self.TempFolderName + "/MetadataFile_in"
        self.MetadataFile_NsBk = self.TempFolderName + "/MetadataFile_out_backup"
        self.MetadataFile_NsCur = self.TempFolderName + "/MetadataFile_out_current"
        
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
        
        # multi namespaces
        self.NsSupported=True if self.IdCtrl.OACS.bit(3)=="1" else False
        self.NsTestItems=[]
        self.initNsTestItems()

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
    SubCase1Desc = "Metadata -  Transferred as Separate Buffer"   
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
            NLB_CDW12=0
            self.Print("")
            self.Print("Write metadata to controller(file %s), start from LBA0, NLB in CDW12 is %s(the minimum data transfer size)"%(self.MetadataFile_in_WithThreadname, NLB_CDW12))
            self.rmTemporaryfiles()
            self.CreateRandomMetadataFile(NLB_CDW12=NLB_CDW12, metadataSize =MS)
            if not self.Test_Write_Read_AsSeparateBuffer(startBlock=0, NLB_CDW12=NLB_CDW12, sizePerBlock=sizePerBlock, metadataSize=MS, printInfo=True):
                self.rmTemporaryfiles()
                return 1        
            
            # test write and read for maxBlock
            NLB_CDW12=self.MaxNLBofCDW12()            
            self.Print("")
            self.Print("Write metadata to controller(file %s), start from LBA0, NLB in CDW12 is %s(the maximum data transfer size)"%(self.MetadataFile_in_WithThreadname, NLB_CDW12))
            self.rmTemporaryfiles()
            self.CreateRandomMetadataFile(NLB_CDW12=NLB_CDW12, metadataSize =MS)
            if not self.Test_Write_Read_AsSeparateBuffer(startBlock=0, NLB_CDW12=NLB_CDW12, sizePerBlock=sizePerBlock, metadataSize=MS, printInfo=True):
                self.rmTemporaryfiles()
                return 1 
            
        self.rmTemporaryfiles()
        return ret_code


    # <define sub item scripts>
    SubCase2TimeOut = 60
    SubCase2Desc = "Metadata -  Transferred as a contiguous part of the logical block"   
    SubCase2KeyWord = ""
    def SubCase2(self):
        ret_code=0
        self.Print("")
        self.Print("Test mechanism for transferring the metadata is 'as a contiguous part of the logical block'")
        MetadataSetting=1


        for Item in self.TestItems:
            self.Print("----------------------------------------")
            self.Print("")
            self.Print("LBAF %s, RP: %s, LBADS: %s, MS: %s"%(Item[0], Item[1], Item[2], Item[3])) 
            LBAF_num = Item[0]
            RP = Item[1]
            LBADS = Item[2]
            MS = Item[3]            
            # LBADS=9, ms=8, sizePerBlock=512+8= 520; LBADS=12, ms=8, sizePerBlock=512*8+8= 4104
            sizePerBlock=512*pow(2,(LBADS-9)) + MS
            # format namespace
            if not self.FormatNS(LBAF_num, MetadataSetting):
                return 1
            
            
            # test write and read for minBlock
            NLB_CDW12=0
            self.Print("")            
            self.Print("Write random patten of data with metadata to controller(file %s), start from LBA0, NLB in CDW12 is %s (minimum)"%(self.MetadataFile_in_WithThreadname, NLB_CDW12))
            # create metadata file
            self.rmTemporaryfiles()
            self.CreateRandomLogicBlockDataAndMetadataFile(NLB_CDW12=NLB_CDW12,sizePerBlock=sizePerBlock)            
            if not self.Test_Write_Read_AsContiguousPartOfLB(startBlock=0 , NLB_CDW12=NLB_CDW12 ,sizePerBlock=sizePerBlock):
                self.rmTemporaryfiles()
                return 1                                             

            # test write and read for maxBlock
            NLB_CDW12=self.MaxNLBofCDW12()
            self.Print("")
            self.Print("Write random patten of data with metadata to controller(file %s), start from LBA0, NLB in CDW12 is %s (maximum)"%(self.MetadataFile_in_WithThreadname, NLB_CDW12))
            # create metadata file
            self.rmTemporaryfiles()
            self.CreateRandomLogicBlockDataAndMetadataFile(NLB_CDW12=NLB_CDW12,sizePerBlock=sizePerBlock)            
            if not self.Test_Write_Read_AsContiguousPartOfLB(startBlock=0 , NLB_CDW12=NLB_CDW12 ,sizePerBlock=sizePerBlock):
                self.rmTemporaryfiles()
                return 1   
        
        self.rmTemporaryfiles()
        return ret_code



    SubCase3TimeOut = 60
    SubCase3Desc = "Metadata -  Transferred as Separate Buffer, test 0x100000 block(1048576)"   
    SubCase3KeyWord = ""
    def SubCase3(self):
        ret_code=0
        self.Print("")
        self.Print("Metadata test")
        #self.Print("Mechanism for transferring the metadata is 'as a ontiguous part of the logical block'")
        #MetadataSetting=1
        self.Print("Test mechanism for transferring the metadata is 'separate buffer of data'")
        MetadataSetting= 0
        self.blkPtr=0

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
            
            thread=64
            startBlock=0 
            #stopBlock=1023
            stopBlock=0x100000 #1048576 block
            NLB_CDW12=self.MaxNLBofCDW12() 
            printInfo=False               
            # initial progress bar parameter
            self.blkFirst=startBlock
            self.blkLast=stopBlock
            
            self.Print("Create %s thread to write %s blocks with Maximum transfer block size(NLB) %s"%(thread, stopBlock, NLB_CDW12))
            #timer
            self.timer.start()
                        
            # write data using multi thread
            self.RecordCmdToLogFile=False
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
                    self.PrintProgress()       
                    break
                else:              
                    #print progress bar    
                    self.PrintProgress()           
                    sleep(1)                          
            self.RecordCmdToLogFile=True
            self.timer.stop()            

            self.Print("")
            #check result
            if self.allPass:
                self.Print("Pass, time usage: %s"%self.timer.time, "p")
            else:
                self.Print("Fail", "f")
                self.Print("Failure block: %s on %s"%(hex(self.failAtStartBlk), self.failAtThread), "f")
                ret_code=1
        
        return ret_code


    SubCase4TimeOut = 60
    SubCase4Desc = "Metadata -  Transferred as a contiguous part of the logical block, test 0x100000 block(1048576)"   
    SubCase4KeyWord = ""
    def SubCase4(self):
        ret_code=0
        self.Print("")
        self.Print("Metadata test")
        self.Print("Mechanism for transferring the metadata is 'as a ontiguous part of the logical block'")
        MetadataSetting=1
        self.blkPtr=0

        if self.TestItems!=None:
            self.Print("----------------------------------------")
            self.Print("")
            Item=self.TestItems[0]
            self.Print("LBAF %s, RP: %s, LBADS: %s, MS: %s"%(Item[0], Item[1], Item[2], Item[3])) 
            LBAF_num = Item[0]
            RP = Item[1]
            LBADS = Item[2]
            MS = Item[3]      

            # format namespace
            if not self.FormatNS(LBAF_num, MetadataSetting):
                return 1
            
            thread=64
            startBlock=0 
            #stopBlock=1023
            stopBlock=0x100000 #1048576 block
            NLB_CDW12=self.MaxNLBofCDW12() 
            printInfo=False               
            # initial progress bar parameter
            self.blkFirst=startBlock
            self.blkLast=stopBlock
            

            self.Print("Create %s thread to write %s blocks with Maximum transfer block size(NLB) %s"%(thread, stopBlock, NLB_CDW12))
            
            #timer
            self.timer.start()
            self.RecordCmdToLogFile=False
                        
            # write data using multi thread
            mThreads = self.Test_Write_Read_AsContiguousPartOfLB_MultiThread(thread, startBlock, stopBlock, NLB_CDW12,  printInfo)
            
            # check if all process finished             
            while True:        
                allfinished=1
                for process in mThreads:
                    if process.is_alive():
                        allfinished=0
                        break
            
                # if all process finished then, quit while loop,
                if allfinished==1:        
                    self.PrintProgress()
                    break
                else:              
                    #print progress bar    
                    self.PrintProgress()           
                    sleep(1)      
            self.RecordCmdToLogFile=True                    
            self.timer.stop()

            self.Print("")
            #check result
            if self.allPass:
                self.Print("Pass, time usage: %s"%self.timer.time, "p")
            else:
                self.Print("Fail", "f")
                self.Print("Failure block: %s on %s"%(hex(self.failAtStartBlk), self.failAtThread), "f")
                ret_code=1
        
        return ret_code

    SubCase5TimeOut = 60
    SubCase5Desc = "Metadata -  Test the metadata for multi namespaces"   
    SubCase5KeyWord = ""
    def SubCase5(self):
        ret_code=0
        self.Print("")
        self.Print("Metadata test")
        self.Print("Test the metadata for multi namespaces")
        self.Print("")
        MetadataSetting= 0
        # number of NS that will be created and test, each TestItems have 2 transferring mechanism
        # and this test will try to include all the mechanism
        NumOfNS=len(self.NsTestItems)
        NsReady=True
        
        if not self.NsSupported:
            self.Print ("controller do not supports the Namespace Management, pass this test", "w")
            return 255
        else:
            self.Print ("controller supports the Namespace Management and Namespace Attachment commands")                 
            self.Print  ("try to create namespace from 1 to %s"%NumOfNS) 
            # function CreateMultiNs() will create NumOfNS namespace
            MaxNs = self.CreateMultiNs(NumOfNS)
            if MaxNs ==1:
                self.Print ("only namespace 1 has been created, quit this test")
                NsReady=False
            elif MaxNs!=NumOfNS:
                self.Print ("created namespace fail, current number of ns is %s, quit this test"%MaxNs)
                NsReady=False                
            else:
                self.Print ("namespaces nsid from 1 to %s have been created"%MaxNs)
                NsReady=True      
                            
        if NsReady:
            # self.NsTestItems=[[LBAF_num, RP, LBADS, MS, Type, MetadataSetting, NSID, sizePerBlock],..] 
            self.Print("")
            # formating namespaces
            for Item in self.NsTestItems:
                LBAF_num = Item[0]
                RP = Item[1]
                LBADS = Item[2]
                MS = Item[3]   
                Type = Item[4] 
                MetadataSetting = Item[5] 
                NSID = Item[6] 
                sizePerBlock = Item[7] 
                self.Print("formating NS %s ( LBAF %s, LBADS: %s, MS: %s, transferringType: %s)"%(NSID, LBAF_num, LBADS, MS, Type)) 
   
                # format namespace
                if not self.FormatNS(LBAF_num=LBAF_num, MetadataSetting=MetadataSetting, nsid=NSID, printInfo=False):
                    self.Print("Fail, quit all","f") 
                    return 1
                
            self.Print("Done")
            
            self.Print("")
            # start to test 
            for Item in self.NsTestItems:
                LBAF_num = Item[0]
                RP = Item[1]
                LBADS = Item[2]
                MS = Item[3]   
                Type = Item[4] 
                MetadataSetting = Item[5] 
                NSID = Item[6] 
                sizePerBlock = Item[7] 
                
                NLB_CDW12=0

                self.Print("Backup corrent metadatas in all namespaces")
                if not self.ReadNsMetadatasToFile_backup(sizePerBlock=sizePerBlock, startBlock=0, NLB_CDW12=NLB_CDW12, metadataSize=MS, printInfo=False):
                    self.Print("read fail, quite", "f")
                    return 1
                                
                self.Print("Write metadata to ns %s"%NSID)
                if not self.WriteNsMetadatasAndVerify(NSID):
                    self.Print("Write fail, quite", "f")
                    return 1
                
                self.Print("Read corrent metadatas in all namespaces")
                if not self.ReadNsMetadatasToFile_current(sizePerBlock=sizePerBlock, startBlock=0, NLB_CDW12=NLB_CDW12, metadataSize=MS, printInfo=False):
                    self.Print("read fail, quite", "f")
                    return 1
                
                self.Print("Check if metadata in ns %s has been changed and metadatas in other namespaces  should not be modified"%NSID)                 
                MisMatchNsid=self.CompareNsMetadatas(NSID) 
                if MisMatchNsid==0:
                    self.Print("Pass", "p")
                else:
                    self.Print("Fail at nsid = %s, quit all"%MisMatchNsid, "f")
                    return 1
                
                self.Print("")
                
        return ret_code

        
    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        if not self.mTestModeOn:
            # remove file            
            self.RmFolder(self.TempFolderName)    
            pass

        return True 
    
if __name__ == "__main__":
    DUT = SMI_MetadataTest(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    