#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
import re
from random import randint
from time import sleep
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
            if MS!=0:                           
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
        self.writeBinaryFileFromList(self.MetadataFile_in, List_buf)        

    def WriteMetadatas_AsSeparateBuffer(self, startBlock, numOfBlock, metadataSize):
        # write metadata with file MetadataFile_in
        totalMetadataSize=metadataSize * numOfBlock
        size = numOfBlock*512
        block_cnt = numOfBlock-1        
        mStr = self.shell_cmd("dd if=/dev/zero bs=512 count=%s 2>&1   |tr \\\\000 \\\\132 2>/dev/null | nvme write %s -s %s -z %s -c %s -y %s -M %s 2>&1"%(numOfBlock, self.dev, startBlock,size, block_cnt, totalMetadataSize, self.MetadataFile_in))
        retCommandSueess=bool(re.search("write: Success", mStr))
        if (retCommandSueess ==  True) :
            self.Print("Done")    
            return True
        else:
            self.Print("Fail, quit all, write cmd= %s"%self.LastCmd, "f")
            return False

    def WriteMetadatas_AsContiguousPartOfLB(self, startBlock, numOfBlock, metadataSize):
        # write data and metadata with file MetadataFile_in
        size = numOfBlock*(512+metadataSize)
        block_cnt = numOfBlock-1        
        mStr = self.shell_cmd("nvme write %s -s %s -z %s -c %s -d %s 2>&1"%( self.dev, startBlock,size, block_cnt, self.MetadataFile_in))
        retCommandSueess=bool(re.search("write: Success", mStr))
        if (retCommandSueess ==  True) :
            self.Print("Done")    
            return True
        else:
            self.Print("Fail, quit all, write cmd= %s"%self.LastCmd, "f")
            return False
    
    def CreateRandomLogicBlockDataAndMetadataFile(self, numOfBlock, metadataSize):
        # write to MetadataFile_in
        numOfByte = (512 + metadataSize)*numOfBlock
        self.shell_cmd("dd if=/dev/urandom of=%s bs=%s count=1 2>&1 >/dev/null"%(self.MetadataFile_in, numOfByte))
        
    def CreateRandomMetadataFile(self, numOfBlock, metadataSize):
        # write to MetadataFile_in
        numOfByte = metadataSize*numOfBlock
        self.shell_cmd("dd if=/dev/urandom of=%s bs=%s count=1 2>&1 >/dev/null"%(self.MetadataFile_in, numOfByte))

    def CheckBlockMetadatas_AsSeparateBuffer(self, startBlock, numOfBlock, metadataSize):
        # read metadata to file MetadataFile_out, and compare with MetadataFile_in
        # startBlock=0, numOfBlock=2, metadataSize=8
        totalMetadataSize=metadataSize * numOfBlock
        size = numOfBlock*512
        block_cnt = numOfBlock-1    
            
        self.rmFile(self.MetadataFile_out)
                                   
        self.Print("Get metadata from block: %s, number of block: %s, and save to file(%s)"%(startBlock, numOfBlock, self.MetadataFile_out))

        self.shell_cmd("nvme read %s -s %s -z %s -c %s -y %s -M %s 2>&1 >/dev/null"%(self.dev, startBlock,size, block_cnt, totalMetadataSize, self.MetadataFile_out))
        sleep(0.5)
        if self.isfileExist(self.MetadataFile_out):
            self.Print("Done")
        else:
            self.Print("Fail to read metadata, quit all", "f")
            return False                
        '''
        self.Print("Check if metadata in first block is 0x0")
        mList = self.readBinaryFileToList(self.MetadataFile_out)
        self.Print("metadata: %s"%mList)            
        '''
        self.Print("Check if metadata from controller(%s) and %s are the same"%(self.MetadataFile_out, self.MetadataFile_in))            
        # if MetadataFile_out = MetadataFile_in, then pass
        if self.isFileTheSame(self.MetadataFile_out, self.MetadataFile_in):
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")   
            return False                 

        return True
    
            
    def CheckBlockMetadatas_AsContiguousPartOfLB(self, startBlock, numOfBlock, metadataSize):
        # read metadata to file MetadataFile_out, and compare with MetadataFile_in
        # startBlock=0, numOfBlock=2, metadataSize=8
        size = numOfBlock*(512+metadataSize)
        block_cnt = numOfBlock-1    
            
        self.rmFile(self.MetadataFile_out)
                                   
        self.Print("Get metadata from block: %s, number of block: %s, and save to file(%s)"%(startBlock, numOfBlock, self.MetadataFile_out))

        self.shell_cmd("nvme read %s -s %s -z %s -c %s -d %s 2>&1 >/dev/null"%(self.dev, startBlock,size, block_cnt, self.MetadataFile_out))
        sleep(0.5)
        if self.isfileExist(self.MetadataFile_out):
            self.Print("Done")
        else:
            self.Print("Fail to read metadata, quit all", "f")
            return False                

        self.Print("Check if data and metadata from controller(%s) and %s are the same"%(self.MetadataFile_out, self.MetadataFile_in))            
        # if MetadataFile_out = MetadataFile_in, then pass
        if self.isFileTheSame(self.MetadataFile_out, self.MetadataFile_in):
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")   
            return False                 

        return True
    
    def __init__(self, argv):
        # initial parent class
        super(SMI_MetadataTest, self).__init__(argv)
        
        self.NLBAF=self.IdNs.NLBAF.int
        self.LBAF=self.GetAllLbaf()
        self.TestItems=[]
        self.initTestItems()

        self.MetadataFile_out = "MetadataFile_out"
        self.MetadataFile_in = "MetadataFile_in"


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
 
            self.Print("Format namespace 1 to LBAF %s with Metadata Settings (MSET)= %s"%(LBAF_num, MetadataSetting))                  
            mStr=self.Format(nsid=1, lbaf = LBAF_num, ses=0, pil=0, pi=0, ms=MetadataSetting)
            if re.search("Success formatting namespace", mStr):
                self.Print("Done")
            else:
                self.Print("Fail to format namespace1, quit all, cmd: %s"%self.LastCmd, "f")
                return 1
            
            # ----------------------------------------------------------------------------------------------
            self.Print("")
            self.Print("Check if Formatted LBA Size (FLBAS) bit 4 was cleared to ‘0’ indicates that all of the metadata for a command is transferred as a separate contiguous buffer of data")
            FLBAS_bit4 = 1 if (self.IdNs.FLBAS.int&0x10)>0 else 0
            self.Print("Formatted LBA Size (FLBAS) bit 4 : %s"%FLBAS_bit4)    
            if FLBAS_bit4==0:
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")
                ret_code=1
                
                
            testBlock=8
            '''
            self.Print("check if metadata in first %s block is 0"%testBlock)            
            # create MetadataFile_in with value=0 and size = MS , for compare MetadataFile_out
            self.Create_MetadataFile_in(startValue = 0, size=MS*testBlock, isConstant=True)
            # verify 
            if not self.CheckBlockMetadatas_AsSeparateBuffer(startBlock=0, numOfBlock=testBlock, metadataSize=MS):
                return 1 
            '''
            # ----------------------------------------------------------------------------------------------
            testBlock=8
            self.Print("")
            self.Print("Write metadata to controller(file %s), start from LBA0, number of blocks is %s"%(self.MetadataFile_in, testBlock))
            # create metadata file
            self.CreateRandomMetadataFile(numOfBlock=testBlock, metadataSize =MS)
            if not self.WriteMetadatas_AsSeparateBuffer(startBlock=0 , numOfBlock=testBlock , metadataSize=MS):
                return 1 
            
            self.Print("")
            # verify 
            self.Print("check if metadata in first %s block and file %s are the same"%(testBlock, self.MetadataFile_in))    
            if not self.CheckBlockMetadatas_AsSeparateBuffer(startBlock=0, numOfBlock=testBlock, metadataSize=MS):
                return 1 
            # ----------------------------------------------------------------------------------------------            
            self.Print("")                                               
        
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

            self.Print("Format namespace 1 to LBAF %s with Metadata Settings (MSET)= %s"%(LBAF_num, MetadataSetting))                
            mStr=self.Format(nsid=1, lbaf = LBAF_num, ses=0, pil=0, pi=0, ms=MetadataSetting)
            if re.search("Success formatting namespace", mStr):
                self.Print("Done")
            else:
                self.Print("Fail to format namespace1, quit all, cmd: %s"%self.LastCmd, "f")
                return 1

            # ----------------------------------------------------------------------------------------------
            # ----------------------------------------------------------------------------------------------
            self.Print("")
            self.Print("Check if Formatted LBA Size (FLBAS) bit 4 was set to ‘1’ indicates that the metadata is transferred at the end of the data LBA")
            FLBAS_bit4 = 1 if (self.IdNs.FLBAS.int&0x10)>0 else 0
            self.Print("Formatted LBA Size (FLBAS) bit 4 : %s"%FLBAS_bit4)    
            if FLBAS_bit4==1 :
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")
                ret_code=1
            
            testBlock=8
            self.Print("")
            self.Print("Write random patten of data with metadata to controller(file %s), start from LBA0, number of blocks is %s"%(self.MetadataFile_in, testBlock))
            # create metadata file
            self.CreateRandomLogicBlockDataAndMetadataFile(numOfBlock=testBlock, metadataSize =MS)
            if not self.WriteMetadatas_AsContiguousPartOfLB(startBlock=0 , numOfBlock=testBlock , metadataSize=MS):
                return 1 
            
            self.Print("")
            # verify 
            self.Print("check if metadata in first %s block and file %s are the same"%(testBlock, self.MetadataFile_in))    
            if not self.CheckBlockMetadatas_AsContiguousPartOfLB(startBlock=0, numOfBlock=testBlock, metadataSize=MS):
                return 1 
            # ----------------------------------------------------------------------------------------------            
            self.Print("")                                                
        
        
        return ret_code

    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        if not self.mTestModeOn:
            # remove file            
            self.rmFile(self.MetadataFile_out)
            self.rmFile(self.MetadataFile_in)     
           
        return True 


if __name__ == "__main__":
    DUT = SMI_MetadataTest(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    