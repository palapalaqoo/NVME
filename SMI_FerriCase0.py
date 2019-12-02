#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
from random import randint
import threading
from time import sleep
import os
import csv
import random
import re

# Import VCT modules
from lib_vct.NVME import NVME


class SMI_FerriCase0(NVME):
    ScriptName = "SMI_FerriCase0.py"
    Author = ""
    Version = ""
    
    def CreateRandSample(self, seed, area, contant, isSeqWrite):
        # area x  contant = total samples, e.g. create random value form 0 to (area x contant-1)
        # if isSeqWrite, then return list [0, 1, 2, ...] else return random
        while True:
            if isSeqWrite:
                self.RandAreaList = range(area)
                self.RandContantList = range(contant)
            else:
                random.seed(seed)
                self.RandAreaList = random.sample(range(area),area)
                self.RandContantList = random.sample(range(contant),contant)
            self.LenAreaList = len(self.RandAreaList)
            self.LenContantList = len(self.RandContantList)
            # verify if range was create correctly
            if self.LenAreaList == area and self.LenContantList == contant:
                break
            else:
                sleep(0.1)
    
    def ResetRandIndex(self):
        self.RandIndex=0
        
    def GetNextSample(self):     
        # return int start form 0 to (area x contant-1) , or None if finish reading all sample   
        if self.LenAreaList==0 or self.LenContantList==0:
            return None        
        contantInd = self.RandIndex/self.LenAreaList
        areaInd = self.RandIndex%self.LenAreaList
        if self.LenContantList>contantInd: # check if exceed area
            value = self.RandAreaList[areaInd] * self.LenContantList + self.RandContantList[contantInd]
            self.RandIndex = self.RandIndex+1
            #print "%s, %s"%(self.RandAreaList[areaInd], self.RandContantList[contantInd]) #verify here
            
            return value
        else:
            return None
        
        
        
        
    
    def WriteWithSPOR(self, SectorCnt, SizeInBlock, isSeqWrite):   
    # return WriteFail_Index, start from 0
    # return (self.RandIndex -1 ), dataPattern, dataPattern_last
        SLBA = 0 # start lba
        NLB = SectorCnt
        
        #self.Print("Start thread to do SPOR")    
        t = threading.Thread(target = self.ThreadDoSPOR)
        t.start()   
        # wait thread starting
        while self.Running!=True:
            sleep(0.1)
        
        # init data
        dataPattern=randint(1, 0xFF)            
        if isSeqWrite:
            self.Print("Start sequence writing data with value %s for first 1G"%dataPattern)
        else:
            self.Print("Start random writing data with value %s for first 1G"%dataPattern)   
                        
        dataPattern_last=0        
        while True: 
            if self.Running==False:
                WriteFail_LBA= SLBA
                self.Print("SPOR have not occored!")
                break
                
        
            
            # multi GetNextSample with NLB, example, NLB=2, Sample[0-1G]*2 = [0-2G]
            # get next start lba, and make sure that the lba+nlb<SizeInBlock
            SLBA = self.GetNextSample()
            cnt = self.RandIndex # after GetNextSample, self.RandIndex will add 1
            # no next, break
            if SLBA == None:
                # another round
                self.ResetRandIndex()
                dataPattern_last=dataPattern
                while True:
                    dataPattern=randint(1, 0xFF)
                    if dataPattern!=dataPattern_last: break
                if isSeqWrite:
                    self.Print("Start sequence writing data with value %s for first 1G"%dataPattern)
                else:
                    self.Print("Start random writing data with value %s for first 1G"%dataPattern)                    
                continue
                            
            SLBA=SLBA*NLB
            # skip if SLBA + NLB>SizeInBlock
            if SLBA + NLB>SizeInBlock:
                continue
            
            # write    
            if not self.NVMEwrite(value=dataPattern, slba=SLBA, SectorCnt=NLB):
                WriteFail_LBA = SLBA
                self.Print("")
                self.Print("Write fail at start LBA = %s"%WriteFail_LBA)
                break;
            else:
                # sueecess writing, save to img
                offset = SLBA*512
                size = NLB
                value=dataPattern
                data = (((''.join(["%02x"%(value)]))*512)*size).decode("hex")
                with open("%s"%(self.ImageFileFullPath), "r+b") as f:
                    f.seek(offset)  
                    f.write(data)                    
                    f.close()  
                

            self.per = float(cnt)/float(SizeInBlock)            
        # end of while            
        t.join(10)
        self.Print("")        
        return (self.RandIndex -1 ), dataPattern, dataPattern_last
        
        
        
        
        
        
        
        
        
        
        
        
    def NVMEwrite(self, value, slba, SectorCnt):        
        NLB = SectorCnt -1 #field NLB in DW12    

        cdw10=slba&0xFFFFFFFF
        cdw11=slba>>32                
        cdw12=NLB
        oct_val=oct(value)[-3:]
        size = 512*(NLB+1)
        CMD = "dd if=/dev/zero bs=512 count=%s 2>&1   |stdbuf -o %s tr \\\\000 \\\\%s 2>/dev/null |nvme io-passthru %s  "\
                             "-o 0x1 -n 1 -l %s -w --cdw10=%s --cdw11=%s --cdw12=%s >/dev/null 2>&1 ; echo $?"\
                            %(NLB+1, size , oct_val, self.dev, size, cdw10, cdw11, cdw12)
        self.RecordCmdToLogFile=False
        mStr=self.shell_cmd(CMD)
        self.RecordCmdToLogFile=True
        if mStr=="0":
            return True         
        else:
            return False     
    
    def CompareThread(self, SectorCnt, SizeInBlock, WriteFail_Index, dataPattern, dataPattern_last):
        while True:
            NLB = SectorCnt
            
            # multi GetNextSample with NLB, example, NLB=2, Sample[0-1G]*2 = [0-2G]
            self.lock.acquire()
            SLBA = self.GetNextSample()
            self.lock.release() 
            cnt = self.RandIndex # after GetNextSample, self.RandIndex will add 1
            if SLBA==None:
                break
            #if SLBA>=WriteFail_Index+1:# TODO, compare written data only
            #    break            
            
            SLBA=SLBA*NLB
            # skip if SLBA + NLB>SizeInBlock
            if SLBA + NLB>SizeInBlock:
                continue
            
            # index < WriteFail_Index, data =  dataPattern, else data = dataPattern_last       
            expectedValue = dataPattern if self.RandIndex<=WriteFail_Index else dataPattern_last
            # expectedValue = dataPattern if self.RandIndex==WriteFail_Index+1 else 0 # if is WriteFail_LBA
            if not self.diff(SLB=SLBA, NLB=NLB, cmpValue=expectedValue):
                self.FailLBAList.append(SLBA)                
                self.CompareRtCode=False

    def InitDirs(self):
        InPath = "./CSV/In/"
        OutPath = "./CSV/Out/"         
        
        # If ./CSV not exist, Create it
        if not os.path.exists("./CSV"):
            os.makedirs("./CSV")
        
        # If ./CSV/In not exist, Create it
        if not os.path.exists(InPath):
            os.makedirs(InPath)
        # If ./CSV/Out not exist, Create it       
        if not os.path.exists(OutPath):
            os.makedirs(OutPath)
            
        self.shell_cmd("cd CSV/Out; rm -f *.csv")

    def SaveToCSVFile(self, fileName, valueList):
        fileNameFullPath = fileName
        # if file not exist, then create it
        if not os.path.exists(fileNameFullPath):
            f = open(fileNameFullPath, "w")
            f.close()            
        
        # write
        with open(fileNameFullPath, 'a') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(valueList)
    
    def CompareAll(self, Loop, SectorCnt, isSeqWrite):
        block_1 = -1
        totalSize = 2097152*512
        CMD = "cmp -l %s %s -n %s"%(self.dev, self.ImageFileFullPath, totalSize)
        mStr="(\d+) " 

        valueList=[]
        failCnt=0
        Wtype = "seq" if isSeqWrite else "rand"
        fileName="./CSV/Out/loop%s_%s_secCnt%s.csv"%(Loop, Wtype, SectorCnt)         
        for line in self.yield_shell_cmd(CMD):             
            if re.search(mStr, line):
                offset = int(re.search(mStr, line).group(1) )
                block = (offset -1)/512 # value from cmp command start form 1
                if block!=block_1:
                    #self.Print( "compare fail at block: %s"%block)                    
                    # save to csv
                    valueList.append(block)
                    if len(valueList)>=10:
                        self.SaveToCSVFile(fileName, valueList)
                        valueList=[]                 
                    #
                    failCnt=failCnt+1
                    block_1=block
                    
        if len(valueList)!=0:
            self.SaveToCSVFile(fileName, valueList)     
        fCapacity = self.KMGT(failCnt*512)
        self.Print( "Number of compare failure blocks: %s blocks( size: %sbytes )"%(failCnt, fCapacity), "f")
        # if >640k, then fail
        if failCnt>=self.maximumFailureSizeNLB:
            self.CompareRtCode=False
        else:
            self.CompareRtCode=True
        return self.CompareRtCode            
        
            

    
    
    def CompareAll_bk(self, SectorCnt, SizeInBlock, WriteFail_Index, dataPattern, dataPattern_last):
        self.CompareRtCode=True
        self.ResetRandIndex() # RESET INDEX
        mThreads = [] 
        self.FailLBAList=[]
        # start thread to compare data
        for i in range(32):                 
            t = threading.Thread(target = self.CompareThread, args=( SectorCnt, SizeInBlock, WriteFail_Index, dataPattern, dataPattern_last,))
            t.start() 
            mThreads.append(t)             
        # wait thread finished
        percent_old=99    
        while True:
            allfinished=1
            for process in mThreads:
                if process.is_alive():
                    allfinished=0
                    break            
            # if all process finished then, quit while loop, else
            if allfinished==1:        
                break
            else:               
                sleep(1)
                percent = int( float(self.RandIndex )/float(SizeInBlock) * 100) # make range 0 to 100
                if percent_old!= percent:        
                    self.PrintProgressBar(percent, 100, length = 20)
                    percent_old=percent
        
        self.FailLBAList.sort()
        self.Print("Data fail at start LBA = %s"%self.FailLBAList)
                    
        return self.CompareRtCode
    
    
    def CreateRamDisk(self, ImageFolderFullPath, ImageFileFullPath):
        # ImageFolderFullPath = /mnt/SMI_RAM
        # ImageFileFullPath = /mnt/SMI_RAM/img.bin
        # create folder
        if not self.isfileExist(ImageFolderFullPath):
            self.shell_cmd("mkdir -p %s"%ImageFolderFullPath)
        # if not mount     
        if self.shell_cmd("mount |grep '%s'  >/dev/null 2>&1; echo $?"%ImageFolderFullPath) !="0":
            self.shell_cmd("mount -t tmpfs tmpfs %s -o size=1G"%ImageFolderFullPath)
        # init file  to 0x0, size 1G
        self.shell_cmd("dd if=/dev/zero of=%s bs=1M count=1024 >/dev/null 2>&1"%ImageFileFullPath)
    
    def SPOR(self, Loop, SectorCnt, isSeqWrite):
        
        self.per = 0        
        
        SizeInBlock= 2097152#  2097152*512 =1G
        writeType = "Sequence write" if isSeqWrite else "Random write  "
        self.Print("+-- Loop: %s, Sector count: %s, Write type: %s -- "%(Loop, SectorCnt, writeType), "b")
        
        cnt=0
        while True:
            self.Print("Clear first 1G data to 0x0")        
            self.fio_write(offset=0, size="1G", pattern=0)
            self.Print("Verify if first 1G data is 0x0 now")
            if self.fio_isequal(offset=0, size="1G", pattern=0):
                self.Print("Pass", "p")
                break
            else:
                self.Print("Fail", "f")
                cnt=cnt+1
                sleep(1)
                
            if cnt>=10:
                self.Print("Fail to Clear first 1G data more then 10 times, quit test case1", "f")
                return False

        self.Print("Create a super fast ram image for mapping device(at %s)"%(self.ImageFileFullPath))
        self.CreateRamDisk(self.ImageFolderFullPath, self.ImageFileFullPath)
        self.Print("Done")

        # creat rand list
        seed=randint(1, 0xFF) 
        # 65536*32=1G=4096*512
        
        if isSeqWrite:
            self.CreateRandSample(seed=seed, area=1, contant=2097152, isSeqWrite=isSeqWrite)    # one area, start forom 0
        else:
            self.CreateRandSample(seed=seed, area=65536, contant=32, isSeqWrite=isSeqWrite) 
        
        WriteFail_Index, dataPattern, dataPattern_last  = self.WriteWithSPOR(SectorCnt, SizeInBlock, isSeqWrite)
            
        self.Print("Start to compare date")
        #self.Print("%s, %s"%(dataPattern,dataPattern_last), "p")
        # sleep for waiting all the disk ready 
        sleep(2)
        #if self.CompareAll(SectorCnt, SizeInBlock, WriteFail_Index, dataPattern, dataPattern_last):
        if self.CompareAll(Loop, SectorCnt, isSeqWrite):
            self.Print("Check if failure size < %s? Pass"%self.maximumFailureSize, "p")    
            rtCode=True
        else:
            self.Print("Check if failure size < %s? Fail"%self.maximumFailureSize, "f")
            rtCode=False 
 
            
            
        self.Print("")    
        self.Print("Finish")  
        self.Print("") 
        return rtCode         
                    
            
    def ThreadDoSPOR(self):
        # time base, must issue in 60s
        #self.IssueSPORtimeBase = True if SectorCnt<30 else False
        self.IssueSPORtimeBase = True
        TimeOut=20
        if self.IssueSPORtimeBase:            
            doSPOR = randint(1, TimeOut)
            self.Print("Start thread to do SPOR when writing time >= %s second"%doSPOR)       
        else:     
        # random time to run, range 1 to 90 of 1G writting
            doSPOR = randint(1, 90)
            self.Print("Start thread to do SPOR when writing percentage > %s/100"%doSPOR)
        #doSPOR=19    #TODO
        IssuedSPOR=False
        self.timer.start()
        self.Running=True
        while True:
            if IssuedSPOR or not self.Running: # if IssuedSPOR or stop by other thread using self.Running=false
                break
            # get current writing percent
            percent = self.per
            percent = int(percent*100) # make range 0 to 100
            # get current time usage
            cTime = int(float(self.timer.time))
            
            if self.IssueSPORtimeBase:
                # do spor
                if not IssuedSPOR:
                    self.PrintProgressBar(cTime, TimeOut, length = 20, suffix="Time: %s s"%cTime)                    
                    if (doSPOR <= cTime):
                        self.spor_reset()
                        IssuedSPOR = True
                        break
                if cTime>TimeOut+1:
                    break
            else:
                self.PrintProgressBar(percent, 100, length = 20)
                # do spor
                if not IssuedSPOR:
                    if (doSPOR < percent):
                        self.spor_reset()
                        IssuedSPOR = True                
            sleep(0.1)
            
            
        self.Print("")
        self.Print("Stop thread")
        self.Running=False    
        self.timer.stop()
        
        
            
    
    def __init__(self, argv):
        # initial new parser if need, -t -d -s -p -r was used, dont use it again
        self.SetDynamicArgs(optionName="l", optionNameFull="testLoop", helpMsg="test Loop, default=1", argType=int) 
        self.SetDynamicArgs(optionName="m", optionNameFull="maximumFailureSize", \
                            helpMsg="maximum failure size, e.x. '-m 640k' means less then 640k(1280 blocks) data lose is accceptable, default=640k", argType=str) 
        self.SetDynamicArgs(optionName="c", optionNameFull="sectorSize", \
                            helpMsg="sector size(sector count) in LBA for case2, default=1", argType=int) 
        self.SetDynamicArgs(optionName="w", optionNameFull="writeType", \
                            helpMsg="write type, 0=sequence, 1=random, default=0(sequence write)", argType=int)        
                
        # initial parent class
        super(SMI_FerriCase0, self).__init__(argv)
        
        self.loops = self.GetDynamicArgs(0)  
        self.loops=1 if self.loops==None else self.loops
        
        self.maximumFailureSize = self.GetDynamicArgs(1)  
        self.maximumFailureSize="640k" if self.maximumFailureSize==None else self.maximumFailureSize    #640k=1280 NLB
        self.maximumFailureSizeNLB=self.KMGT_reverse(self.maximumFailureSize)
        
        self.sectorSize=self.GetDynamicArgs(2)
        self.sectorSize=1 if self.sectorSize==None else self.sectorSize
        
        self.writeType=self.GetDynamicArgs(3)
        self.writeType=0 if self.writeType==None else self.writeType
        self.writeType="sequence" if self.writeType==0 else "random"
        
        
        self.InitDirs()
        
        # super fast ram for mapping device
        self.ImageFolderFullPath = "/mnt/SMI_RAM"
        self.ImageFileFullPath  =     "/mnt/SMI_RAM/img.bin"
        
        self.lock=threading.Lock()
        
        self.per=0
        self.Running=False # flag for stop thread
        self.IssueSPORtimeBase=False
        self.CompareRtCode=True
        self.FailLBAList=[]

        # for big rand
        self.RandAreaList=[]
        self.RandContantList=[]
        self.LenAreaList=0
        self.LenContantList=0
        self.RandIndex=0
        

    # define pretest  
    def PreTest(self):        
        return True            

    # <define sub item scripts>
    SubCase1TimeOut = 6000000
    SubCase1Desc = "Loop for SPOR testing"   
    SubCase1KeyWord = ""
    def SubCase1(self):   
        ret_code=0
        self.Print("Start to test SPOR")
        self.Print("Total test loop: %s"%self.loops, "f")
        self.Print("%s(%s blocks) data lose is accceptable"%(self.maximumFailureSize, self.maximumFailureSizeNLB), "f")
        self.Print("")

        try: 
            for loop in range(self.loops):
                
                
                for SectorCnt in range(1, 256):
                    isSeqWrite=True  # sequence write
                    if not self.SPOR(Loop=loop, SectorCnt = SectorCnt, isSeqWrite=isSeqWrite): return 1
                    isSeqWrite=False
                    if not self.SPOR(Loop=loop, SectorCnt = SectorCnt, isSeqWrite=isSeqWrite): return 1                  
                    
                    #return 0 #
                    
                for SectorCnt in range(255, 0, -1):
                    isSeqWrite=True
                    if not self.SPOR(Loop=loop, SectorCnt = SectorCnt, isSeqWrite=isSeqWrite): return 1
                    isSeqWrite=False
                    if not self.SPOR(Loop=loop, SectorCnt = SectorCnt, isSeqWrite=isSeqWrite): return 1                
        except KeyboardInterrupt:
            self.Print("")
            self.Print("Detect ctrl+C, quit", "w")  
            # check device is alive or not
            self.Running=False
            if not self.dev_alive:
                self.spor_reset()
            return 255              
        
        
    SubCase2TimeOut = 6000000
    SubCase2Desc = "One time SPOR testing"   
    SubCase2KeyWord = ""
    def SubCase2(self):   
        ret_code=0
        self.Print("Start to test SPOR")
        self.Print("Test type: %s"%self.writeType, "f")
        self.Print("Sector size: %s LBA"%self.sectorSize, "f")
        self.Print("%s(%s blocks) data lose is accceptable"%(self.maximumFailureSize, self.maximumFailureSizeNLB), "f")
        self.Print("")

        try: 
            isSeqWrite=True if self.writeType=="sequence" else False  # sequence write
            if not self.SPOR(Loop=0, SectorCnt = self.sectorSize, isSeqWrite=isSeqWrite): return 1        
        except KeyboardInterrupt:
            self.Print("")
            self.Print("Detect ctrl+C, quit", "w")  
            # check device is alive or not
            self.Running=False
            if not self.dev_alive:
                self.spor_reset()
            return 255              
                
        
        
        
        
        
        
        
        return ret_code

    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        if self.isfileExist(self.ImageFolderFullPath):
            with open("%s"%(self.ImageFileFullPath), "r+b") as f:                 
                f.close()              
            self.shell_cmd("umount %s"%self.ImageFolderFullPath)
            self.shell_cmd("rm -r %s"%self.ImageFolderFullPath)
        return True 


if __name__ == "__main__":
    DUT = SMI_FerriCase0(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    