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


class SMI_SPOR(NVME):
    ScriptName = "SMI_SPOR.py"
    Author = "Sam"
    Version = "20200914"
    
    def CreateRandSample(self, seed, area, contant, isSeqWrite):
        # area x  contant = total samples, e.g. create random value form 0 to (area x contant-1), 
        # if isSeqWrite, then return list [0, 1, 2, ...] else return random
        # use GetNextSample() to get next rand values
        # use ResetRandIndex() to set to the first rand values
        
        # ex, area = 2, contant=5, RandAreaList may = [0,1], RandContantList may =  [3, 1, 4, 0, 2] , 
        # first rand is 1*5 + 2,  e.g. self.RandAreaList[areaInd] * self.LenContantList + self.RandContantList[contantInd]
        # second = 1*5 + 0, 3th =1*5+4 .. until last = 0*5 + 3
        # unmask following syntax to test    
        #seed = 1; area = 2; contant = 5; isSeqWrite = False 
        
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
        
        
        
        
    
    def WriteWithSPOR(self, SectorCnt, SizeInBlock, isSeqWrite, porType):   
    # return WriteFail_Index, start from 0
    # return (self.RandIndex -1 ), dataPattern, dataPattern_last
        SLBA = 0 # start lba
        NLB = SectorCnt
        WriteSLBAList = []
        
        #self.Print("Start thread to do SPOR")    
        t = threading.Thread(target = self.ThreadDoPowerOff, args=(porType,))
        t.start()   
        # wait thread starting
        while self.Running!=True:
            sleep(0.1)
        
        # init data
        dataPattern=randint(1, 0xFF)            
        if isSeqWrite:
            self.Print("Start sequence writing data with value 0x%X for first 1G and sleep %s seconds for every write command(writeDelayTime)"%(dataPattern, self.writeDelayTime))
        else:
            self.Print("Start random writing data with value 0x%X for first 1G and sleep %s seconds for every write command(writeDelayTime)"%(dataPattern, self.writeDelayTime))
                        
        dataPattern_last=0   
        writeSuccessCnt = 0     
        self.ResetRandIndex()
        while True: 
            if self.Running==False:
                WriteFail_LBA= SLBA
                self.Print("%s have not occored!"%(porType))
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
                    self.Print("Start sequence writing data with value 0x%X for first 1G"%dataPattern)
                else:
                    self.Print("Start random writing data with value 0x%X for first 1G"%dataPattern)                    
                continue
                            
            SLBA=SLBA*NLB
            # skip if SLBA + NLB>SizeInBlock
            if SLBA + NLB>SizeInBlock:
                continue
            
            # write    
            if not self.NVMEwrite(value=dataPattern, slba=SLBA, SectorCnt=NLB, RecordCmdToLogFile=self.mTestModeOn, OneBlockSize=self.OneBlockSize):
                WriteFail_LBA = SLBA
                self.Print("Fail at %s th write command with sector = %s"%(writeSuccessCnt+1, NLB), "p")   
                self.Print("Wait for %s finish .."%porType)
                '''
                if self.skipPoweringOffBlock:
                    self.Print("Ferri DF module, expect DUT will flush those data.")
                    self.WriteImg(SLBA, NLB, dataPattern)     
                '''               
                break;
            else:
                # sueecess writing, save to img
                self.WriteImg(SLBA, NLB, dataPattern, self.OneBlockSize)

            writeSuccessCnt = writeSuccessCnt +1
            WriteSLBAList.append(SLBA)
            self.per = float(cnt)/float(SizeInBlock)    
            
            # writeDelayTime
            if self.writeDelayTime!=0:
                sleep(float(self.writeDelayTime))        
        # end of while            
        t.join()
        self.Print("")        
        return (self.RandIndex -1 ), dataPattern, dataPattern_last, WriteSLBAList, WriteFail_LBA

    def WriteImg(self, SLBA, NLB, dataPattern, OneBlockSize):
        # sueecess writing, save to img
        # 4k supported
        offset = SLBA*OneBlockSize
        size = NLB
        value=dataPattern
        data = (((''.join(["%02x"%(value)]))*OneBlockSize)*size).decode("hex")
        with open("%s"%(self.ImageFileFullPath), "r+b") as f:
            f.seek(offset)  
            f.write(data)                    
            f.close()         
    
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
            expectedValueStr = dataPattern if self.RandIndex<=WriteFail_Index else dataPattern_last
            # expectedValueStr = dataPattern if self.RandIndex==WriteFail_Index+1 else 0 # if is WriteFail_LBA
            if not self.diff(SLB=SLBA, NLB=NLB, cmpValue=expectedValueStr):
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

    def SaveToCSVFile(self, fileNameFailBlockList, valueList, titleList=None):
        fileNameFailBlockListFullPath = fileNameFailBlockList
        # if file not exist, then create it
        if not os.path.exists(fileNameFailBlockListFullPath):
            f = open(fileNameFailBlockListFullPath, "w")
            f.close()
            # write titleList if titleList!=None, write in to file
            if titleList!=None:                
                with open(fileNameFailBlockListFullPath, 'a') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(titleList)                
                        
        
        # write
        with open(fileNameFailBlockListFullPath, 'a') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(valueList)
    
    def printColorFailBlockAndGetNOFfailArea(self, failList):
        # get all command number list, ex. whichCMD=409, CMDslba= 1024, CMDelba=1031(write sector= 8)
        # return PassToFailList, FailToPassList,type = [CntFailToPass, LBAptr]
        whichCMDlist = []
        for mList in failList: # mList structure = ([block, expectedValueStr, currentValueStr, whichCMD, CMDslba, CMDelba]) for following syntax
            CMDinfo = [mList[3], mList[4], mList[5]] # grep [whichCMD, CMDslba, CMDelba]
            if CMDinfo not in whichCMDlist:
                whichCMDlist.append(CMDinfo)
                
        # retrive block to blockList
        column1 = [i[0] for i in failList]
        blockList = column1
        
        # check block of every whichCMDlist, range from slba to elba
        AreaInfo = [] # [AreaStart, AreaStop, "pass" or "fail", whichCMD]
        AreaStart = None
        AreaStop = None
        PassToFailList = [] # [CntFailToPass, LBAptr]
        FailToPassList = []
        CntPassToFail = 0 # ▇▁▁
        CntFailToPass = 0 # ▁▁▇
        for CMDinfo in whichCMDlist: #  [whichCMD, CMDslba, CMDelba]
            whichCMD = CMDinfo[0]
            CMDslba = CMDinfo[1]
            CMDelba= CMDinfo[2]
            LBAptr = CMDslba            
            
            isWriteSuccessArea = None
            while True:
                if isWriteSuccessArea == None: # first time run while for every CMDinfo
                    isWriteSuccessArea = True if LBAptr not in blockList else False
                    AreaStart = LBAptr
                    
                    # check last AreaInfo if is not the first CMDinfo
                    cnt = len(AreaInfo)
                    if cnt==0:
                        lastIsSuccess = "pass"                      
                    else:
                        lastAreaInfo = AreaInfo[cnt-1]
                        lastIsSuccess = lastAreaInfo[2]
                        
                    if lastIsSuccess=="pass" and not isWriteSuccessArea: # if last is pass and current is fail
                        PassToFailList.append([CntPassToFail, LBAptr]) # save cnt and Data Break point LBA
                        CntPassToFail = CntPassToFail +1
                        
                    if lastIsSuccess=="fail" and isWriteSuccessArea: # if last is fail and current is pass
                        FailToPassList.append([CntFailToPass, LBAptr]) # save cnt and Data Break point LBA
                        CntFailToPass = CntFailToPass +1                        
                            
                elif isWriteSuccessArea and LBAptr in blockList: 
                # if is WriteSuccessArea and write not success , means end of WriteSuccess area(pass to fail)
                    AreaStop = LBAptr-1
                    AreaInfo.append([AreaStart, AreaStop, "pass", whichCMD])
                    isWriteSuccessArea = False
                    AreaStart = LBAptr
                    PassToFailList.append([CntPassToFail, LBAptr])
                    CntPassToFail = CntPassToFail +1
                    
                elif not isWriteSuccessArea and LBAptr not in blockList: 
                # if is not WriteSuccessArea and write success , means end of WriteSuccess area(fail to pass)
                    AreaStop = LBAptr-1
                    AreaInfo.append([AreaStart, AreaStop, "fail", whichCMD])
                    isWriteSuccessArea = True      
                    AreaStart = LBAptr 
                    FailToPassList.append([CntFailToPass, LBAptr])
                    CntFailToPass = CntFailToPass +1   
                    
                LBAptr = LBAptr+1 
                if LBAptr>CMDelba: break
            # end while
            
            # handle last area        
            AreaStop = LBAptr-1
            AreaInfo.append([AreaStart, AreaStop, "pass" if isWriteSuccessArea else"fail", whichCMD])
        # end for
        
        # draw
        self.Print( "Different colors for each command, and high means block data pass, low means block data fail")
        self.Print("")
        foreColor=None # foreColor will change for every write command
        color0 = "black"
        color1 = "yellow"
        mStr = ""
        # always start with color black, overline, i.e. pass
        mStr = mStr + self.UseStringStyle("  ", mode="overline", fore = foreColor) 
        laststat = "pass"
        
        currwhichCMD = None
        for mAreaInfo in AreaInfo: # [AreaStart, AreaStop, "pass" or "fail", whichCMD]
            strBuf = ""
            
            # set fore color if whichCMD changed
            if currwhichCMD != mAreaInfo[3]:
                foreColor = color0 if foreColor!=color0 else color1 
                currwhichCMD = mAreaInfo[3]
            
            # print charactor
            if mAreaInfo[2] == "pass":
                # if fail to pass, print |
                if laststat=="fail":                     
                    strBuf = strBuf + self.UseStringStyle("▏", mode="overline", fore = foreColor)     
                # print  with overline               
                strBuf = strBuf + self.UseStringStyle("%s-%s "%(mAreaInfo[0], mAreaInfo[1]), mode="overline", fore = foreColor)
            else:
                # if pass to fail, print |
                if laststat=="pass": 
                    strBuf = strBuf + self.UseStringStyle("▏", mode="underline", fore = foreColor)           
                # print  with underline
                strBuf = strBuf + self.UseStringStyle("%s-%s "%(mAreaInfo[0], mAreaInfo[1]), mode="underline", fore = foreColor)    
            laststat = mAreaInfo[2]   
            mStr = mStr + strBuf
              
        self.Print(mStr)
        
        return PassToFailList, FailToPassList
                
            
    def VerifyDismatchBlocks(self, failCnt, fileNameFailDetail, failList, WriteSLBAList, SectorCnt):
        # if >640k, then fail
        rtCode = True         
        if failCnt>self.maximumFailureSizeNLB:
            self.Print("Fail", "f")
            self.Print("Detail infomation of failure blocks at file: %s"%fileNameFailDetail, "f")   
            rtCode=False
    
            # write to file for 'Detail infomation of failure blocks', e.g. summary_fail_block_details.csv
            self.SaveToCSVFile(fileNameFailDetail , ["block", "expected value", "current value", "which cmd", "cmd start LBA", "cmd end LBA"])
            for mList in failList:
                self.SaveToCSVFile(fileNameFailDetail , mList)
                
            # WriteSLBAList to logfile fileNameFailBlockListWriteStartLBA
            self.SaveToCSVFile(fileNameFailDetail , ["write command start LBA"])
            self.SaveToCSVFile(fileNameFailDetail , ["command number", "write slba", "sector"])
            mSLBAcnt=1
            for mSLBA in WriteSLBAList:    
                self.SaveToCSVFile(fileNameFailDetail , [mSLBAcnt ,mSLBA, SectorCnt])    # SaveToCSVFile is list type so using [mSLBA]
                mSLBAcnt = mSLBAcnt +1

        else:
            self.Print("Pass", "p")
            
        return rtCode
    
    def CompareAll(self, fileNameFailBlockList, fileNameFailBlockListSum, fileNameFailDetail, WriteSLBAList, WriteFail_LBA, dataPattern, SectorCnt):
    # use cmp to compare image and ssd
    # if fail, write fail block to log fileNameFailBlockListSum, fileNameFailDetail, and WriteSLBAList to log fileNameFailDetail also
        WriteCMDcnt = len(WriteSLBAList)
    
        block_1 = -1
        totalSize = 2097152*512 # test 1G byte for 512/4K
        CMD = "cmp -l %s %s -n %s"%(self.dev, self.ImageFileFullPath, totalSize)
        # cmp output: ex,    1894400 0 324,     where 1894400=address, 0=value in self.dev(currentValueStr), 324=self.ImageFileFullPath(expectedValueStr)
        mStr="(\d+)\s+(\d+)\s+(\d+)" 
        #mStr="(\d+)"

        failCnt=0
        failList=[]
        for line in self.yield_shell_cmd(CMD):             
            if re.search(mStr, line):
                offset = int(re.search(mStr, line).group(1) )
                block = (offset -1)/self.OneBlockSize # value from cmp command start form 1
                currentValueInt = int(re.search(mStr, line).group(2) ,8 ) # convert OCT to INT
                expectedValueInt = int(re.search(mStr, line).group(3), 8 ) # convert OCT to INT
                currentValueStr = "0x%X"%currentValueInt # convert INT to hex string
                expectedValueStr = "0x%X"%expectedValueInt # convert INT to hex string
                
                if block!=block_1:
                    #self.Print( "compare fail at block: %s"%block)  
                    
                    # if skipPoweringOffBlock, the data may be written to ssd even the write command fail
                    # so we just check if the data in WriteFail_LBA is dataPattern or last value
                    # if is last value, cmp command will not show it becouse it is not writen as expected result.
                    # Check WriteFail_LBA later                       
                    if (block >= WriteFail_LBA and block < WriteFail_LBA+SectorCnt) and self.skipPoweringOffBlock:                        
                        pass
                    else:                            
                        # save to list, ["block", "expected value", "current value"]
                        
                        # find whichCMD
                        whichCMD = None
                        CMDslba = None
                        CMDelba = None
                        for i in range(WriteCMDcnt, 0, -1): # i countdown to 1
                            mSLBA = WriteSLBAList[i-1]
                            if mSLBA <=block and mSLBA +SectorCnt>block: # if block is between (mSLBA) and (mSLBA+SectorCnt)
                                whichCMD = i
                                CMDslba = mSLBA
                                CMDelba = mSLBA +SectorCnt -1
                                break
                            
                        failList.append([block, expectedValueStr, currentValueStr, whichCMD, CMDslba, CMDelba])
                                          
                        #
                        failCnt=failCnt+1
                        block_1=block            
        
        # sort failList by whichCMD, i.e. sort by write command order
        failList.sort(key=lambda a: a[3])
                    
        # if skipPoweringOffBlock, check WriteFail_LBA
        if self.skipPoweringOffBlock:   
            # read 1th byte of fail LBA form image and current SSD
            Image1ByteValue = self.read1ByteFromFile("./mnt/img.bin", WriteFail_LBA*self.OneBlockSize)
            # Device1ByteValue = self.read1ByteFromFile(self.dev, WriteFail_LBA*512) # using fio to verify value later
            # save to list, ["block", "expected value", "current value"]
            block = WriteFail_LBA
            expectedValueStr = "0x%X(write fail, last value) or 0x%X(write success, new value)"%(Image1ByteValue, dataPattern)            
            self.SetPrintOffset(4)
            self.Print( "-- skipPoweringOffBlock --, check current data at the write command failure LBA = %s, size = %s sector"%(WriteFail_LBA, SectorCnt))            
            # using fio to check if data is one of [Image1ByteValue  dataPattern],  if not , fail test
            offset = WriteFail_LBA*self.OneBlockSize
            size = SectorCnt*self.OneBlockSize                
            isDataPattern = self.fio_isequal(offset, size, pattern = dataPattern, fio_bs=self.OneBlockSize)
            isImagePattern = self.fio_isequal(offset, size, pattern = Image1ByteValue, fio_bs=self.OneBlockSize)
            
            if isDataPattern:
                self.Print( "All the data from LBA = %s, size = %s sector, value = %s"%(WriteFail_LBA, SectorCnt, dataPattern)) 
                currentValueStr = "0x%X"%dataPattern
            elif isImagePattern:
                self.Print( "All the data from LBA = %s, size = %s sector, value = %s"%(WriteFail_LBA, SectorCnt, Image1ByteValue)) 
                currentValueStr = "0x%X"%Image1ByteValue
            else:
                self.Print( "The data is not all equal to %s nor %s"%(Image1ByteValue, dataPattern), "w")
                currentValueStr = "uknow"                
                                
            CMD = "hexdump %s -s %s -n %s"%(self.dev, WriteFail_LBA*self.OneBlockSize, SectorCnt*self.OneBlockSize)
            self.Print( "Do shell command to hexdump sectors: %s"%CMD) 
            aa= self.shell_cmd(CMD)
            self.SetPrintOffset(8)
            self.Print(aa)
            self.SetPrintOffset(4)  
                
                
            #  show last fail sectors and will not recorded
            #failList.append([block, expectedValueStr, currentValueStr, whichCMD, CMDslba, CMDelba])                 
                
            self.Print( "-- end of skipPoweringOffBlock --") 
            self.SetPrintOffset(0)        
            self.Print("")               

        # write to FailBlockList file, e.x. 0_loop0_seq_secCnt129.csv
        valueList=[]
        for mList in failList: # mList structure = ([block, expectedValueStr, currentValueStr, whichCMD, CMDslba, CMDelba]) for following syntax
            valueList.append(mList[0])
            if len(valueList)>=10: #  show 10 fail block for every row
                self.SaveToCSVFile(fileNameFailBlockList, valueList)
                valueList=[]             
        if len(valueList)!=0:
            self.SaveToCSVFile(fileNameFailBlockList, valueList)
                    
        # write to summary file( e.g. summary.csv) with value = [fileNameFailBlockList, failCnt]
        fName = fileNameFailBlockList.replace("./CSV/Out/", "") # remove dir name and save to summary.csv
        self.SaveToCSVFile(fileNameFailBlockListSum, [fName, failCnt], titleList=["file name", "number of failure blocks"])
        
        # show failure blocks
        self.Print( "1.) Calculate number of compare failure blocks")
        fCapacity = self.KMGT(failCnt*self.OneBlockSize)
        self.SetPrintOffset(4)
        self.Print( "Number of compare failure blocks: %s blocks( data lost size: %sbytes )"%(self.HighLightRed(failCnt), self.HighLightRed(fCapacity)))
        self.SetPrintOffset(0)
        
        # VerifyDismatchBlocks size 
        self.Print( "")
        self.Print("2.) Check if failure size <= %s "%self.maximumFailureSize)
        self.SetPrintOffset(4)
        if not self.VerifyDismatchBlocks(failCnt, fileNameFailDetail, failList, WriteSLBAList, SectorCnt): self.CompareRtCode = False
        self.SetPrintOffset(0)
             
        # show failure blocks
        self.Print("") 
        self.Print("3.) Show failure blocks") 
        self.SetPrintOffset(4)
        PassToFailList, FailToPassList = self.printColorFailBlockAndGetNOFfailArea(failList)      
           
        self.Print("")                    
        # verify by self.comparison option
        CntPassToFail = len(PassToFailList)
        CntFailToPass = len(FailToPassList)
        self.Print("CntPassToFail: %s, CntFailToPass: %s"%(CntPassToFail, CntFailToPass))
        self.Print("PassToFailList: %s, FailToPassList: %s"%(PassToFailList, FailToPassList))
        self.SetPrintOffset(0)
        
        # comparison
        self.Print("") 
        self.Print("4.) comparison")       
        self.SetPrintOffset(4)  
        self.Print("comparison option: %s"%self.comparison)
        if self.comparison == "normal":
            self.Print("Data lost area: %s"%CntPassToFail)
            self.Print("Check if Data lost area<=2, i.e. CntPassToFail<=2")
            if CntPassToFail<=2:
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")
                self.CompareRtCode=False
                  
        elif self.comparison == "enhanced": 
            self.Print("Check if Data Break point<=1, i.e. CntPassToFail<=1 and CntFailToPass==0")
            if CntPassToFail<=1 and CntFailToPass==0:
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")
                self.CompareRtCode=False
                
        elif self.comparison == "advanced": 
            self.Print("Check if Data Break point=0, i.e. CntPassToFail<=0 and CntFailToPass==0, PLP model")
            if CntPassToFail==0 and CntFailToPass==0:
                self.Print("Pass", "p")
            else:
                self.Print("Fail", "f")
                self.CompareRtCode=False
        
        else:
            self.Print("comparison option not correct(%s), no such option, support [normal, enhanced, advanced] only"%self.comparison)                        
            

        self.SetPrintOffset(0) 
        
            
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
        # ImageFolderFullPath = ./mnt
        # ImageFileFullPath = ./mnt/img.bin
        
        # remove
        self.rmFile(ImageFileFullPath)
        # create folder
        if not self.isfileExist(ImageFolderFullPath):
            self.shell_cmd("mkdir -p %s"%ImageFolderFullPath)
        # if not mount     
        if self.shell_cmd("mount |grep '%s'  >/dev/null 2>&1; echo $?"%ImageFolderFullPath) !="0":
            self.shell_cmd("mount -t tmpfs tmpfs %s -o size=1G"%ImageFolderFullPath)
        # init file  to 0x0, size 1G
        self.shell_cmd("dd if=/dev/zero of=%s bs=1M count=1024 >/dev/null 2>&1"%ImageFileFullPath)
        if self.isfileExist(ImageFileFullPath):
            return True
        else:
            return False
            
    
    def SPOR(self, FileOutCnt, Loop, SectorCnt, isSeqWrite, porType):
        
        self.per = 0        
        
        SizeInBlock= 2097152#  2097152*512 =1G, test 1G byte for 512/4K
        writeType = "Sequence write" if isSeqWrite else "Random write  "
        self.Print("+-- Loop: %s, Sector count: %s, Write type: %s ---------------------------------- "%(Loop, SectorCnt, writeType), "b")
        
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

        self.Print("")
        self.Print("Create a ram image for mapping device(at %s)"%(self.ImageFileFullPath))
        if not self.CreateRamDisk(self.ImageFolderFullPath, self.ImageFileFullPath):
            self.Print("Fail, create file fail", "f")
            return 1
        else:
            self.Print("Done, ram image was created.", "p")
            
        self.Print("")
        # creat rand list
        seed=randint(1, 0xFF) 
        # 65536*32=1G=4096*512
        
        if isSeqWrite:
            if self.OneBlockSize==512:
                self.CreateRandSample(seed=seed, area=1, contant=2097152, isSeqWrite=isSeqWrite) # one area, start from 0, 2097152*512=1G
            else:   #4096
                self.CreateRandSample(seed=seed, area=1, contant=2097152/8, isSeqWrite=isSeqWrite) # one area, start from 0, 2097152/8*4096=1G
        else:
            if self.OneBlockSize==512:
                self.CreateRandSample(seed=seed, area=65536, contant=32, isSeqWrite=isSeqWrite) 
            else:
                self.CreateRandSample(seed=seed, area=65536, contant=32/8, isSeqWrite=isSeqWrite)
        
        WriteFail_Index, dataPattern, dataPattern_last, WriteSLBAList, WriteFail_LBA  = self.WriteWithSPOR(SectorCnt, SizeInBlock, isSeqWrite, porType)
        # sleep for waiting all the disk ready 
        sleep(2)

        Wtype = "seq" if isSeqWrite else "rand"
        # file that store compared failure block number
        fileNameFailBlockList="./CSV/Out/%s_loop%s_%s_secCnt%s.csv"%(FileOutCnt, Loop, Wtype, SectorCnt)     
        # file that store summary of failure block number
        fileNameFailBlockListSum="./CSV/Out/summary.csv"  
        fileNameFailDetail="./CSV/Out/summary_fail_block_details.csv"     
        self.Print("Start to compare date and output to %s"%fileNameFailBlockList) 
        if self.CompareAll(fileNameFailBlockList, fileNameFailBlockListSum, fileNameFailDetail, WriteSLBAList, WriteFail_LBA, dataPattern, SectorCnt): 
            rtCode=True
        else:
            rtCode=False 
 
            
            
        self.Print("")    
        self.Print("Finish")  
        self.Print("") 
        return rtCode         
                    
            
    def ThreadDoPowerOff(self, porType):
        # time base, must issue in 60s
        #self.IssueSPORtimeBase = True if SectorCnt<30 else False
        self.IssueSPORtimeBase = True
        TimeOut=20000 # in millisecond
        if self.IssueSPORtimeBase:            
            doSPORtimer = randint(1000, TimeOut)
            if self.mTestModeOn: doSPORtimer = 3000 # if test mode, set 3 s
            self.Print("Start thread(ThreadDoPowerOff) to do %s when writing time >= %s millisecond"%(self.HighLightRed(porType), doSPORtimer))       
        #doSPORtimer=19   #TODO
        IssuedSPOR=False
        self.timer.start("float")
        self.Running=True
        while True:
            if IssuedSPOR or not self.Running: # if IssuedSPOR or stop by other thread using self.Running=false
                break
            # get current writing percent
            percent = self.per
            percent = int(percent*100) # make range 0 to 100
            # get current time usage
            # round to millisecond        
            cTime = int(self.timer.time*1000)
            
            if self.IssueSPORtimeBase:
                # do spor
                if not IssuedSPOR:    
                    timeDiv = float((doSPORtimer-cTime)/100)# where 100 means 0.1s for sleep(0.1) in this loop
                    if (timeDiv>0.1): # if current time + 0.1s < doSPORtimer, means not time up
                        self.PrintProgressBar(cTime, TimeOut, length = 20, suffix="Time: %ss / %s millisecond"%(cTime, TimeOut), showPercent=False) 
                    else: # time up, power off/on
                        #wait timeDiv second
                        sleep(timeDiv)
                        self.PrintProgressBar(doSPORtimer, TimeOut, length = 20, suffix="Time: %ss / %s millisecond"%(doSPORtimer, TimeOut), showPercent=False)                          
                        if porType=="spor" :
                            self.spor_reset(PowerOffDuration=self.PowerOffDuration) 
                        else: 
                            self.por_reset(PowerOffDuration=self.PowerOffDuration)
                        IssuedSPOR = True
                        break                                             
                
                if cTime>TimeOut+1:
                    break
            else:
                self.PrintProgressBar(percent, 100, length = 20)
                # do spor
                if not IssuedSPOR:
                    if (doSPORtimer < percent):
                        self.spor_reset(PowerOffDuration=self.PowerOffDuration)
                        IssuedSPOR = True                
            sleep(0.1)# where 100 means 0.1s for sleep(0.1) in this loop
            
            
        self.Print("")
        self.Print("Do %s finished"%porType)        
        self.Print("Stop thread(ThreadDoPowerOff)")
        self.Running=False    
        self.timer.stop()
        
        
            
    
    def __init__(self, argv):
        # initial new parser if need, -t -d -s -p -r was used, dont use it again
        self.SetDynamicArgs(optionName="l", optionNameFull="testLoop", helpMsg="test Loop, default=1, e.x. '-l 10'", argType=int, default = 1) 
        self.SetDynamicArgs(optionName="m", optionNameFull="maximumFailureSize", \
                            helpMsg="maximum failure size, e.x. '-m 640k' means less then 640k(1280 blocks) data lose is accceptable, default=640k", argType=str, default="640k") 
        self.SetDynamicArgs(optionName="c", optionNameFull="sectorSize", \
                            helpMsg="sector size(sector count) in LBA for case2, i.e. Number of Logical Blocks will be write to SSD"\
                            "\nex. '-c 1', if SSD format is 512, then write 512 byte for every nvme command"\
                            "\nex. '-c 1', if SSD format is 4K, then write 4096 byte."\
                            "\nex. '-c 0',that will be random sector for every loop, default=1", argType=int, default=1) 
        self.SetDynamicArgs(optionName="w", optionNameFull="writeType", \
                            helpMsg="write type, 0=sequence, 1=random, default=0(sequence write)", argType=int, default=0)        
        self.SetDynamicArgs(optionName="k", optionNameFull="keepImageFile", \
                            helpMsg="keep image file(./mnt/img.bin), e.x. -k 1, default=0(will not keep file)", argType=int, default=0)    
        self.SetDynamicArgs(optionName="spob", optionNameFull="skipPoweringOffBlock", \
                            helpMsg="Skip powering off block, if set to 1, will skip to check the powering off blocks that the spor was occurred"\
                            " \nand do hexdump the powering off blocks for inspection,"\
                            " if set to 0, then expect the data in powering off block \nremain to init-pattern because of the writing command failure."\
                            " e.x. -spob 1, default=0", argType=int, default=0)           
        self.SetDynamicArgs(optionName="cmp", optionNameFull="comparison", \
                            helpMsg="comparison option in [normal, enhanced, advanced], e.x. -cmp normal, default=normal."\
                            "\nnormal: if Data lost area<=2, i.e. CntPassToFail<=2, then pass"\
                            "\nenhanced: if Data Break point<=1, i.e. CntPassToFail<=1 and CntFailToPass==0, then pass"\
                            "\nadvanced: if Data Break point=0, i.e. CntPassToFail<=0 and CntFailToPass==0, PLP model, then pass"\
                            , argType=str, default="normal")  
        self.SetDynamicArgs(optionName="poroffdur", optionNameFull="PowerOffDuration", \
                            helpMsg="Power Off Duration in second, default = 0, e.x. -poroffdur 2.5, Duration=2.5 seconds", argType=float, default=0)        
        self.SetDynamicArgs(optionName="porofftype", optionNameFull="porofftype", \
                            helpMsg="Power Off Type in spor/por/mixed, if type mixed was set, then will do por/spor in sequence, default = spor, e.x. '-porofftype spor'", argType=str, default="spor")           
        self.SetDynamicArgs(optionName="wdt", optionNameFull="writeDelayTime", \
                            helpMsg="Write Delay Time for every write command, default = 0, e.x. '-wdt 2.5', write and delay 2.5 seconds", argType=str, default="0")           
              
                        
        # initial parent class
        super(SMI_SPOR, self).__init__(argv)
        
        self.loops = self.GetDynamicArgs(0)  
        
        self.maximumFailureSize = self.GetDynamicArgs(1)  
        self.maximumFailureSizeNLB=self.KMGT_reverse(self.maximumFailureSize)
        
        self.sectorSize=self.GetDynamicArgs(2)
        
        self.writeType=self.GetDynamicArgs(3)
        self.writeType="sequence" if self.writeType==0 else "random"
        
        self.keepImageFile=self.GetDynamicArgs(4)
        self.keepImageFile=False if self.keepImageFile==0 else True
        
        self.skipPoweringOffBlock=self.GetDynamicArgs(5)
        self.skipPoweringOffBlock=False if self.skipPoweringOffBlock==0 else True
        
        self.comparison=self.GetDynamicArgs(6)
        
        self.PowerOffDuration = self.GetDynamicArgs(7)
        
        self.porofftype= self.GetDynamicArgs(8)
        
        self.writeDelayTime =  self.GetDynamicArgs(9)
        
        self.Print("")
                
        self.InitDirs()
        
        # super fast ram for mapping device
        self.ImageFolderFullPath = "./mnt"
        self.ImageFileFullPath  =     "./mnt/img.bin"
        
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
        
        self.OneBlockSize = self.GetBlockSize()
        

    # define pretest  
    def PreTest(self): 
        self.Print("Block size: %s"%self.OneBlockSize, "p")
        
        return True            

    # <define sub item scripts>
    SubCase1TimeOut = 0
    SubCase1Desc = "SPOR testing"   
    SubCase1KeyWord = ""
    def SubCase1(self):   
        ret_code=0
        self.Print("Start to test SPOR")
        self.Print("Total test loop: %s"%self.loops, "p")
        self.Print("%s(%s blocks) data lose is accceptable"%(self.maximumFailureSize, self.maximumFailureSizeNLB), "p")
        self.Print("Test type: %s"%self.writeType, "p")
        MaxSecCnt = self.MaxNLBofCDW12() +1
        self.Print("Max sector that the controller supported: %s"%MaxSecCnt, "p")            
        
        self.Print("SectorSize: %s"%("random" if self.sectorSize==0 else self.sectorSize), "p")
        self.Print("Por type: %s"%(self.porofftype), "p")
        
        if self.sectorSize>MaxSecCnt:
            self.sectorSize = MaxSecCnt
            self.Print("sectorSize was set to Max sector(%s) because sectorSize is > Max sector"%MaxSecCnt, "w")  

        self.Print("")
        FileOutCnt=0
        isSeqWrite=True if self.writeType=="sequence" else False  # sequence write
        try: 
            for loop in range(self.loops):
                
                SectorCnt = randint(1,MaxSecCnt) if self.sectorSize==0 else self.sectorSize
                if self.porofftype=="mixed":
                    porType="por" if loop%2==0 else "spor"
                else:
                    porType = self.porofftype
                
                if self.SmartCheck.isRunOncePass():
                    self.Print("Check smart log: Pass", "p")
                else:
                    self.Print("Check smart log: Fail", "f")
                    return 1
                
                if not self.SPOR(FileOutCnt, Loop=loop, SectorCnt = SectorCnt, isSeqWrite=isSeqWrite, porType=porType): return 1
                
                if self.SmartCheck.isRunOncePass():
                    self.Print("Check smart log: Pass", "p")
                else:
                    self.Print("Check smart log: Fail", "f")
                    return 1
                          
        except KeyboardInterrupt:
            self.Print("")
            self.Print("Detect ctrl+C, quit", "w")  
            # check device is alive or not
            self.Running=False
            if not self.dev_alive:
                self.spor_reset()
            return 255              

        return ret_code

    SubCase2TimeOut = 0
    SubCase2Desc = "SPOR module test"   
    SubCase2KeyWord = ""
    def SubCase2(self):  
        self.Print("Verify SPOR for power module with smart checking")
        self.Print("Total test loop: %s"%self.loops)
        self.Print("Power Off Duration in second: %s"%self.PowerOffDuration)      
           
        if not self.SmartCheck.isRunOncePass(): return False
            
        for loop in range(self.loops):   
            self.Print("")
            self.Print("loop: %s, start to do spor -----------------------------------------------------------------------"%loop)    
            if not self.spor_reset(showMsg=True, PowerOffDuration=self.PowerOffDuration): 
                self.Print("loop: %s, fail"%loop, "f") 
                return 1
            else:
                self.Print("loop: %s, pass"%loop, "p") 
            
            self.Print("Check smart log")    
            if not self.SmartCheck.isRunOncePass(): return False
            self.Print("")

        return 0
    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        # if need to kill ImageFile
        if not self.keepImageFile:
            if self.isfileExist(self.ImageFolderFullPath):
                with open("%s"%(self.ImageFileFullPath), "r+b") as f:                 
                    f.close()              
                self.shell_cmd("umount %s"%self.ImageFolderFullPath)
                self.shell_cmd("rm -r %s"%self.ImageFolderFullPath)
        return True 


if __name__ == "__main__":
    DUT = SMI_SPOR(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    