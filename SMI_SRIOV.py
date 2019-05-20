#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
import re
from time import sleep
import time
import threading
tkinter = None
import os

# Import VCT modules
from lib_vct.NVME import NVME
from lib_vct import mStruct
from random import randint



class SMI_SRIOV(NVME):
    ScriptName = "SMI_SRIOV.py"
    Author = "Sam"
    Version = "20190415"
    
    TypeInt=0x0
    TypeStr=0x1    
    
    # PrimaryControllerCapabilitiesStructure
    class PCCS(mStruct.Struct):
        _format = mStruct.Format.LittleEndian
        CNS=0x14
        CNTLID=mStruct.Type.Byte2   # 2byte
        PORTID=mStruct.Type.Byte2
        CRT=mStruct.Type.Byte1
        RESERVED0=mStruct.Type.Byte1[31-5+1]
        VQFRT=mStruct.Type.Byte4
        VQRFA=mStruct.Type.Byte4
        VQRFAP=mStruct.Type.Byte2
        VQPRT=mStruct.Type.Byte2
        VQFRSM=mStruct.Type.Byte2
        VQGRAN=mStruct.Type.Byte2
        RESERVED1=mStruct.Type.Byte1[63-48+1]
        VIFRT=mStruct.Type.Byte4
        FIRFA=mStruct.Type.Byte4
        VIRFAP=mStruct.Type.Byte2
        VIPRT=mStruct.Type.Byte2
        VIFRSM=mStruct.Type.Byte2
        VIGRAN=mStruct.Type.Byte2
                
                    
    def Get_PrimaryControllerCapabilitiesStructure(self, printInfo=False):
        # expected data length from shell command
        dataLen=self.PCCS.StructSize
        cns=self.PCCS.CNS
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=%s -r --cdw10=%s --namespace-id=%s 2>&1"%(self.dev_port, dataLen, cns, 1)
        # issue command to get binary data structure
        rTDS=self.shell_cmd(CMD)
        # format data structure to class
        if len(rTDS)!=dataLen:
            # if return size !=  dataLen            
            self.Print( "Fail to get data structure, quit !","f")  if printInfo else None
            return None
        else:            
            # format data structure to class PrimaryControllerCapabilitiesStructure 
            rtStruct = self.PCCS(rTDS)
            return rtStruct
        
    # Secondary Controller Entry
    class SCE(mStruct.Struct):
        _format = mStruct.Format.LittleEndian
        SCID=mStruct.Type.Byte2   # 2byte
        PCID=mStruct.Type.Byte2
        SCS=mStruct.Type.Byte1
        RESERVED0=mStruct.Type.Byte1[3]
        VFN=mStruct.Type.Byte2
        NVQ=mStruct.Type.Byte2
        NVI=mStruct.Type.Byte2
        RESERVED1=mStruct.Type.Byte1[31-14+1]
        
    def Get_SecondaryControllerList(self, printInfo=False):
        # 
        NumberofIdentifiers=0
        cns=0x15
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=%s -r --cdw10=%s --namespace-id=%s 2>&1"%(self.dev_port, 16, cns, 1)
        # issue command to get data structure(return string) for get NumberofIdentifiers
        rTDS=self.shell_cmd(CMD)     
        DS=self.AdminCMDDataStrucToListOrString(rTDS, 0)            
        if DS==None:
            self.Print( "Fail to get data structure, quit !","f") if printInfo else None
            return False
        else:
            NumberofIdentifiers=self.convert(lists=DS, stopByte=0, startByte=0, mtype=self.TypeInt)
            
            # issue command again to get binary data structure (return binary) for get all SCEntry  
            CMD = CMD +" -b"     
            rTDS=self.shell_cmd(CMD) 
            # expected size for all SCEntry which equal to 32
            SCEntrySize=self.SCE.StructSize
            for SCEntryID in range(NumberofIdentifiers):
                offset = SCEntrySize*(SCEntryID+1)
                data=rTDS[offset : offset+SCEntrySize]
                # get structure here
                rtStruct = self.SCE(data)
                # save to list , e.g., SecondaryControllerList = [SCEntryID, class SCE], where SCEntryID = 0, 1, 2, ...
                self.SecondaryControllerList.append([SCEntryID, rtStruct])
        
            return True        
    
    def convert(self, lists, stopByte, startByte, mtype, endian="little-endian"):   
        # return is string , eg, '0x1A' or 'SMI2262'        
        # if error
        if startByte>stopByte and mtype==self.TypeInt:
            return "0"
        if startByte>stopByte and mtype==self.TypeStr:
            return ""                    
        # sub bytes
        subList=lists[startByte : stopByte+1]
        mStr=""
        if mtype==self.TypeInt:
            if endian=="little-endian":
                # reverse it and combine
                subList=subList[::-1]
            subList_Str="".join(subList)
            # Converting string to int
            # mStr = hex(int(subList_Str, 16))
            mStr = "0x"+subList_Str            
        elif mtype==self.TypeStr: 
            for byte in subList:
                mStr=mStr+chr(int(byte,16))    
        else:
            mStr =  "0"
        return mStr    
    
    def GetCurrentNumOfVF(self):
        path="/sys/class/block/%s/device/device/sriov_numvfs"%self.dev[5:]
        if self.isfileExist(path):
            return self.shell_cmd("cat %s"%path)
        else:
            return None

    def SetCurrentNumOfVF(self, value):
        path="/sys/class/block/%s/device/device/sriov_numvfs"%self.dev[5:]
        if self.isfileExist(path):
            return True if self.shell_cmd("echo %s > %s 2>&1 >/dev/null ; echo $?"%(value, path))==0 else False
        else:
            return False
        
    def VMC(self, CNTLID, RT, ACT, NR):
        CDW10=(CNTLID<<16) + (RT<<8) + ACT
        CDW11= NR
        CMD = "nvme admin-passthru %s --opcode=0x1C -w --cdw10=%s  --cdw11=%s 2>&1"%(self.dev, CDW10, CDW11, 1)
        rTDS=self.shell_cmd(CMD)
        return rTDS
        
    def Set_PF_ResourceMinimum(self, printInfo=False):        
        if self.VI_ResourceSupported:
            self.Print("Set Primary Controller Resource VI=1 (minimum)") if printInfo else None
            if self.VMC(CNTLID = self.PF_CNTLID, RT = 1, ACT = 1, NR= 1).find("success"):
                return True
            else:
                return False
            
        if self.VQ_ResourceSupported:
            self.Print("Set Primary Controller Resource VQ=2 (minimum)") if printInfo else None
            if self.VMC(CNTLID = self.PF_CNTLID, RT = 0, ACT = 1, NR= 2).find("success"):
                return True
            else:
                return False            

    def Set_VF_ResourceMinimum(self, printInfo=False):  
        for SCEntry in self.SecondaryControllerList:
            SCID= SCEntry.SCID
                
            if self.VI_ResourceSupported:
                self.Print("Set Secondary Controller Resource VI=0 (minimum)") if printInfo else None
                if not self.VMC(CNTLID = SCID, RT = 1, ACT = 1, NR= 0).find("success"):
                    return False
                
            if self.VQ_ResourceSupported:
                self.Print("Set Secondary Controller Resource VQ=0 (minimum)") if printInfo else None
                if not self.VMC(CNTLID = SCID, RT = 0, ACT = 1, NR= 0).find("success"):
                    return False
        return True   

    def Set_VF_ResourceMaxmum(self, printInfo=False):  
        # arrange VQ VI list for all VF
        VF_VQ_List=[]
        VF_VI_List=[]        
        VQResourcesFlexibleTotal  = self.PCCStructure.VQFRT        
        VIResourcesFlexibleTotal  = self.PCCStructure.VIFRT
        totalNumOfVF = len(self.SecondaryControllerList)
        NVQ=int(VQResourcesFlexibleTotal/totalNumOfVF)
        NVQ_mod = VQResourcesFlexibleTotal % totalNumOfVF
        NVI=int(VIResourcesFlexibleTotal/totalNumOfVF)
        NVI_mod = VIResourcesFlexibleTotal % totalNumOfVF        
        for i in range(totalNumOfVF):
            if i<NVQ_mod:
                VF_VQ_List.append(NVQ + 1)
            else:
                VF_VQ_List.append(NVQ)
            if i<NVI_mod:
                VF_VI_List.append(NVI + 1)
            else:
                VF_VI_List.append(NVI)                
        # end
        
        self.Print("Try to set all VF's VQ : %s"%VF_VQ_List) if printInfo else None
        i=0
        for SCEntry in self.SecondaryControllerList:
            SCID= SCEntry.SCID
            NVQ= VF_VQ_List[i]         
            if self.VQ_ResourceSupported:
                self.Print("Set Secondary Controller Resource VQ=%s"%NVQ) if printInfo else None
                if not self.VMC(CNTLID = SCID, RT = 0, ACT = 1, NR= 2).find("success"):
                    return False
            i=i+1   
        
        self.Print("Try to set all VF's VI : %s"%VF_VI_List) if printInfo else None
        i=0
        for SCEntry in self.SecondaryControllerList:
            SCID= SCEntry.SCID
            NVI= VF_VI_List[i]         
            if self.VI_ResourceSupported:
                self.Print("Set Secondary Controller Resource VI=%s "%NVI) if printInfo else None
                if not self.VMC(CNTLID = SCID, RT = 0, ACT = 1, NR= 2).find("success"):
                    return False
            i=i+1         
        return True
        
    def AttachNs(self, nsid, CNTLID):
        return self.shell_cmd("nvme attach-ns %s -n %s -c %s 2>&1 >/dev/null ; echo $?" %(self.dev_port,nsid, CNTLID))
                       
    def CreateMultiNs(self, NumOfNS=8, SizeInBlock=2097152):        
        # Create namespcaes form nsid 1 to nsid 8(default), size 1G(default), and attach to the controller
        # return MaxNs, ex, MaxNs=8, indicate the NS from 1 to 8
        # check if controller supports the Namespace Management and Namespace Attachment commands or not
        NsSupported=True if self.IdCtrl.OACS.bit(3)=="1" else False
        NN=self.IdCtrl.NN.int
        if NsSupported:
            #self.Print ("controller supports the Namespace Management and Namespace Attachment commands"            )
            # set max test namespace <=8(default)
            MaxNs=NumOfNS if NN>NumOfNS else NN
            self.Print(  "create namespcaes form nsid 1 to nsid %s, size 1G, and attach to the controller"%MaxNs )
            error=0            
            for i in range(1, NN+1):        
                # delete NS
                self.DeleteNs(i)    
            self.shell_cmd("nvme reset %s"%self.dev_port)           
            # Create namespaces, and attach it
            for i in range(1, MaxNs+1):

                CreatedNSID=self.CreateNs(SizeInBlock)        
                if CreatedNSID != i:
                    self.Print ("create namespace error!"    )
                    error=1
                    break  
                    
            # if creat ns error          
            if error==1:
                self.Print(  "create namespcaes Fail, reset to namespaces 1" ,"w")
                self.ResetNS()
                MaxNs=1
 
            return MaxNs
        
    def GetControllerList_ThatAreAttachedToTheNamespace(self, nsid):
        rtList=[]
        CMD = "nvme admin-passthru %s --opcode=0x6 --data-len=4096 -r --cdw10=%s --namespace-id=%s 2>&1"%(self.dev_port, 0x12, nsid)
        rTDS=self.shell_cmd(CMD)
        # format data structure to list 
        DS=self.AdminCMDDataStrucToListOrString(rTDS, 0)            
        if DS==None:
            self.Print( "Fail to get data structure, quit !","f")
            return None
        else:
            # self.Print( "Success to get data structure")            
            #self.Print( "According to Figure 38: Controller List Format")
            NumOfId=self.convert(lists=DS, stopByte=1, startByte=0, mtype=self.TypeInt)
            NumOfId=int(NumOfId, 16)
            #self.Print("    Number of Identifiers: %s"%hex(NumOfId))
            
            for i in range(NumOfId):
                Identifier=self.convert(lists=DS, stopByte=3+(2*i), startByte=2+(2*i), mtype=self.TypeInt)
                Identifier=int(Identifier, 16)            
                rtList.append(Identifier)
            return rtList
        
    def InitFormatTestItems(self):
        # self.TestItems=[[LBAF_number, RP, LBADS, MS],[LBAF_number, RP, LBADS, MS],..]   

        for x in range(15):
            RP = self.LBAF[x][self.lbafds.RP]
            LBADS = self.LBAF[x][self.lbafds.LBADS] 
            MS = self.LBAF[x][self.lbafds.MS] 
            #if MS!=0 and LBADS>=9:                           
            self.FormatTestItems.append([x, RP, LBADS, MS])       
    # -------------------------------------------------------------------
    def TestWriteRead(self, SubDUT, writeValue):
    # SubDUT type is NVME
        # write 10M data with writeValue
        SubDUT.fio_write(offset=0, size="10M", pattern=writeValue, nsid=1, devPort=SubDUT.dev_port)
        return True if SubDUT.fio_isequal(offset=0, size="10M", pattern=writeValue, nsid=1) else False            
    
    def TestWriteCompare(self, SubDUT, writeValue):
        # write 10M data with writeValue
        SubDUT.fio_write(offset=0, size="10M", pattern=writeValue, nsid=1, devPort=SubDUT.dev_port)
        # compare command
        oct_val=oct(writeValue)[-3:]
        mStr=SubDUT.shell_cmd("dd if=/dev/zero bs=512 count=1 2>&1   |tr \\\\000 \\\\%s 2>/dev/null |nvme compare %s  -s 0 -z 512 -c 0 2>&1"%(oct_val, SubDUT.dev))
        
        # expected compare command is the same value, i.e. 'compare: Success"
        return True if bool(re.search("compare: Success", mStr))  else False              
    
    def TestWriteFormatRead(self, SubDUT, writeValue):
        # write 10M data with writeValue
        SubDUT.fio_write(offset=0, size="10M", pattern=writeValue, nsid=1, devPort=SubDUT.dev_port)
        # format
        nsid=1; lbaf=0; ses=0; pil=0; pi=0; ms=0
        mStr=SubDUT.shell_cmd(" nvme format %s -n %s -l %s -s %s -p %s -i %s -m %s 2>&1"%(SubDUT.dev_port, nsid, lbaf, ses, pil, pi, ms))
        retCommandSueess=bool(re.search("Success formatting namespace", mStr))  
        if not retCommandSueess:
            self.Print("Fail to format %s, quit all"%SubDUT.dev, "f"); return False
            
        # after format, expected pattern = 0
        return True if SubDUT.fio_isequal(offset=0, size="10M", pattern=0, nsid=1) else False  
   
    def TestWriteSanitizeRead(self, SubDUT, writeValue):  
        # wait if sanitize is in progressing
        if not SubDUT.WaitSanitizeFinish(120): return False
              
        # write 10M data with writeValue
        SubDUT.fio_write(offset=0, size="10M", pattern=writeValue, nsid=1, devPort=SubDUT.dev_port)    
        
        # Issue sanitize command where cdw10=2 for BlockErase        
        CMD = "nvme admin-passthru %s --opcode=0x84 --cdw10=2 2>&1"%(SubDUT.dev)          
        mStr=self.shell_cmd(CMD)
        if not re.search("NVMe command result:00000000", mStr):
            self.Print("Fail for sanitize command, return code: %s"%mStr, "f"); 
            self.Print("Sanitize command: %s"%CMD, "f"); 
            return False

        # wait if sanitize is in progressing
        if not SubDUT.WaitSanitizeFinish(120): return False    
        
        # expected pattern = 0
        return True if SubDUT.fio_isequal(offset=0, size="10M", pattern=0, nsid=1) else False

    
    def TestWriteUncRead(self, SubDUT, writeValue):
        # write 10M data with writeValue
        SubDUT.fio_write(offset=0, size="10M", pattern=writeValue, nsid=1, devPort=SubDUT.dev_port)    
        # write unc
        BlockCnt=127
        CMD = "nvme write-uncor %s -s 0 -n 1 -c %s 2>&1 "%(SubDUT.dev, BlockCnt)
        mStr = SubDUT.shell_cmd(CMD) 
        if not re.search("Write Uncorrectable Success", mStr):
            self.Print("Fail to Write Uncorrectable, return code: %s"%mStr, "f"); 
            self.Print("Write Uncorrectable command: %s"%CMD, "f"); 
            return False 
         
        # check if 'Input/output error' for hexdump command
        CMD = "hexdump %s -n 1M  2>&1 "%(SubDUT.dev)
        mStr = SubDUT.shell_cmd(CMD) 
        if not re.search("Input/output error", mStr):
            self.Print("Read uncorrectable blocks fail, following is the returned result for command: %s"%CMD, "f"); 
            self.Print("--------------------------", "f"); 
            self.Print("%s"%mStr, "f"); 
            self.Print("--------------------------", "f"); 
            return False    

        # write 10M data with writeValue to remove Uncorrectable
        SubDUT.fio_write(offset=0, size="10M", pattern=writeValue, nsid=1, devPort=SubDUT.dev_port)  
                
        return True     
             
    
    def VerifyAllDevices(self, excludeDev=None, printInfo=True):
        # vierify if  '/dev/nvme0n1' to the first block of /dev/nvme0n1, etc.. , for all VF/PV and exclude excludeDev device
        mPass=True
        for Dev in self.AllDevices:     
            if Dev!=excludeDev:    
                # verify
                mStr = self.shell_cmd("hexdump %s -n 512 -C 2>&1"%Dev)
                if bool(re.search("%s"%Dev, mStr)):
                    self.Print("Check %s: Expected string at block 0 is '%s' : Pass"%(Dev, Dev), "p") if printInfo else None
                else:
                    self.Print("Check %s: Expected string at block 0 is '%s' : Fail"%(Dev, Dev), "f") if printInfo else None
                    mPass=False
        return mPass        
    
    def TestSpecificVFandOtherVFshouldNotBeModified(self, SpecificDevice):
        
        #write data to all devices, except SpecificDevice
        self.Print("Write data to all devices, e.g. '/dev/nvme0n1' to the first block of /dev/nvme0n1, etc..")
        for Dev in self.AllDevices:         
            # write '/dev/nvme0n1' to the first block of /dev/nvme0n1 and  '/dev/nvme1n1' to /dev/nvme1n1                
            CMD= "echo %s | nvme write %s --data-size=512 --prinfo=1 2>&1 > /dev/nul"%(Dev, Dev)
            self.shell_cmd(CMD)
            
        # verify    
        self.Print("Check the block 0 of all devices .")
        if not self.VerifyAllDevices(excludeDev=None, printInfo=True): return 1
            
                
        self.Print("")        
        # create SubDUT to use NVME object for specific device, e.x. /dev/nvme0n1,  note that argv is type list
        SubDUT = NVME([SpecificDevice])        
                
        # get test items for current device
        ThreadTestItem=self.GetCurrentDutTestItem(SubDUT)
        # run all test items
        for Item in ThreadTestItem:
            # print test item name
            self.Print(Item[0])
            # run test item with SubDUT and writeValue=any value
            Func = Item[1]
            success = Func(SubDUT=SubDUT, writeValue=randint(1, 0xFF))
            
            if success:
                self.Print("Done", "p"); 
            else:
                self.Print("Fail, quit all", "f"); return 1
            
            # check data in other controllers     
            self.Print("Check if data in other controller has not been modified"); 
            if self.VerifyAllDevices(excludeDev=SpecificDevice, printInfo=False): 
                self.Print("Pass", "p"); 
            else:
                self.Print("Fail", "p"); 
                # print info again
                self.VerifyAllDevices(excludeDev=SpecificDevice, printInfo=True)
                self.Print("Quit all", "p");
                return 1
            self.Print("")
    
    def Push(self, device, TestItemID,scriptName, writeValue, rtPass):
        # write info to mutex variable
        self.lock.acquire()
        # MutexThreadOut [device, TestItemID,scriptName, writeValue, rtPass]
        self.MutexThreadOut.append([device, TestItemID,scriptName, writeValue, rtPass])                
        self.lock.release()        
            
    def ThreadTest(self, device, testTime): 
        # device = /dev/nvmeXn1
        
        # create SubDUT to use NVME object for specific device, e.x. /dev/nvme2n1, note that argv is type list
        SubDUT = NVME([device])    
        
        # get test items for current device
        ThreadTestItem=self.GetCurrentDutTestItem(SubDUT)
        # unmask below to get all command in /log/xxxx.cmdlog
        # SubDUT.RecordCmdToLogFile=True        
        TotalItem=len(ThreadTestItem)
        TestItemID_old=None
        TestItemID=randint(1, 0xFF) % TotalItem
        StartTime = time.time()
        # if using GUI
        if self.UsingGUI:
            # get Lb
            for i in range(len(self.AllDevices)):
                if self.AvaItems[i][0] == device:
                    Lb = self.AvaItems[i][1]
                    break                    
            # update available test item string
            for i in range(TotalItem):
                name = ThreadTestItem[i][0]
                Lb.insert("end", name)                
                
        while True:          
            # if time out
            CurrentTime = time.time()
            if (CurrentTime-StartTime)>testTime: break
            
            # if iMain Thread is not Alive 
            if not self.isMainThreadAlive(): break
                        
            # get test ID that is not the same with current one
            TestItemID=self.GetNextTestItemID(TotalItem, TestItemID_old)
            
            # get writeValue, script name, script func
            writeValue = randint(1, 0xFF)
            scriptName=ThreadTestItem[TestItemID][0]
            func = ThreadTestItem[TestItemID][1]
            # write info to mutex variable, with rtPass=self.Running
            self.Push(device, TestItemID,scriptName, writeValue, self.Running)   
            # run and get return code
            rtPass = func(SubDUT, writeValue)
            # write info to mutex variable, with rtPass
            self.Push(device, TestItemID,scriptName, writeValue, rtPass)               


          
            
            # backup ID
            TestItemID_old = TestItemID
            # if return code is not zero, then quit
            if not rtPass: break                
            
    def MultiThreadTest(self, testTime): 
        # if using GUI, show GUI by threading
        if self.UsingGUI:
            tGUI = threading.Thread(target = self.ThreadCreatUI)
            tGUI.start() 
            # wait window start
            sleep(1)
            
                
        # call ThreadTest(self, device, testTime) for all devices to test their testitems at the same time
        mThreads = [] 
        # clear mutex variable before any thread start
        self.MutexThreadOut=[]
        for Dev in self.AllDevices:
            t = threading.Thread(target = self.ThreadTest, args=(Dev, testTime,))
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
                sleep(0.5)                                                                
                # fetch mutex variable
                self.lock.acquire()
                Out = self.MutexThreadOut  
                # clear
                self.MutexThreadOut=[]
                self.lock.release()
                # if there is info out, parse to console/GUI
                if len(Out):
                    for oneThreadOut in Out:
                        # oneThreadOut [device, TestItemID,scriptName, writeValue, rtPass]  
                        device=oneThreadOut[0]
                        TestItemID=oneThreadOut[1]
                        scriptName=oneThreadOut[2]
                        writeValue=oneThreadOut[3]
                        rtPass=oneThreadOut[4]
                        
                        # show on console
                        if rtPass==self.Running:     # if rtPass is self.Running, skip it
                            result="running"
                        else:                        
                            result= "pass" if rtPass else "fail"                    
                            self.PrintAlignString("Device: %s"%device, "Test function name: %s"%scriptName, "Result: %s"%result, result)
                        
                        # show on GUI if using GUI
                        if self.UsingGUI:
                            # get Lb
                            for i in range(len(self.AllDevices)):
                                if self.CurrItems[i][0] == device:
                                    Lb = self.CurrItems[i][1]
                                    break                    
                            # update Current test item string                         
            
                            if result=="running":     # if result is Running, add item with yellow color
                                Lb.insert("end", scriptName)
                                Lb.itemconfig("end", {'fg': 'blue'})
                                Lb.yview("end")                                  #Set the scrollbar to the end of the listbox
                            elif result=="pass": 
                                Lb.itemconfig("end", {'fg': 'green'})
                            else : 
                                Lb.itemconfig("end", {'fg': 'red'})                            
                                                               
                                            
                        
        # if using GUI, close GUI
        if self.UsingGUI:
            sleep(2)
            self.root.quit()                        

    def PrintAlignString(self,S0, S1, S2, PF="default"):            
        mStr = "{:<25}\t{:<40}\t{:<20}".format(S0, S1, S2)
        if PF=="pass":
            self.Print( mStr , "p")        
        elif PF=="fail":
            self.Print( mStr , "f")      
        else:
            self.Print( mStr ) 
            
    def GetCurrentDutTestItem(self, SubDUT):
        # get current device test item, ex. /dev/nvme0n1 may test all feature
        ThreadTestItem=[]
        # add test items
        ThreadTestItem.append(["Test_Write_Read", self.TestWriteRead])
        ThreadTestItem.append(["Test_Write_Compare", self.TestWriteCompare])                
        # if ibaf0 is supported, i.e.  lbaf0->lbads>9 , then add test item 'TestWriteFormatRead'
        LBAF=SubDUT.GetAllLbaf()
        LBAF0_LBADS=LBAF[0][SubDUT.lbafds.LBADS]
        LBAF0Supported = True if (LBAF0_LBADS >=  9) else False
        ThreadTestItem.append(["Test_Write_Format_Read", self.TestWriteFormatRead]) if LBAF0Supported else None        
        # if BlockErase sanitize is supported, i.e.  sanicap_bit1=1 , then add test item 'TestWriteSanitizeRead'
        BlockEraseSupport = True if (SubDUT.IdCtrl.SANICAP.bit(1) == "1") else False
        ThreadTestItem.append(["Test_Write_Sanitize_Read", self.TestWriteSanitizeRead]) if BlockEraseSupport else None        
        # if WriteUncSupported is supported , then add test item 'WriteUncSupported'
        WriteUncSupported = True if SubDUT.IsCommandSupported(CMDType="io", opcode=0x4) else False
        ThreadTestItem.append(["Test_WriteUnc_Read", self.TestWriteUncRead]) if WriteUncSupported else None
        return ThreadTestItem
        
        
    def GetNextTestItemID(self,TotalItem, TestItemID_old):
        # return random ID that is different from  TestItemID_old
        while True:
            NewID = randint(1, 0xFF) % TotalItem
            if NewID!=TestItemID_old:
                return NewID
        
    # -------------------------------------------------------------------
    
    def GetCurrentNvmeList(self):
        mStr=self.shell_cmd("nvme list")
        return re.findall("/dev/nvme\d+n\d+", mStr)
        
        
        
    def import_with_auto_install(self):
        package = "Tkinter"
        try:
            return __import__(package)
        except ImportError:
            self.Print("Linux has not install tkinter, Try to install tkinter (yum -y install tkinter)", "w")           
            InstallSuccess =  True if self.shell_cmd("yum -y install tkinter 2>&1 >/dev/null ; echo $?")=="0" else False
            
            if InstallSuccess:
                self.Print("Install Success!, restart script..", "p")                           
                os.execl(sys.executable, sys.executable, * sys.argv)
                return None
            else:
                self.Print("Install fail!, using console mode", "f")
                return None
            
    def CheckTkinter(self):    
        #self.shell_cmd("rpm -qa |grep python27-tkinter-2.7.13-5.el7.x86_64.rpm")
        global  tkinter     

        tkinter = self.import_with_auto_install()
        if tkinter==None:
            return False
        return True
                
    def ThreadCreatUI(self):
        numOfDev = len(self.AllDevices)
        ListWidth = 20  # width in characters for current testing item
        ListHight = 20  # hight in characters for current testing item
        ListWidth_ava = 20  # width in characters for list available test item
        ListHight_ava = 10  # hight in characters for list available test item

        InfoHight = 20 # hight in characters        
        self.root=tkinter.Tk()  
        self.root.geometry('{}x{}'.format(1000, 800))
        import tkMessageBox
        
        F_slotView = tkinter.Frame(self.root)
        F_slotView.pack(side="top")
        
        
        for slot in range(numOfDev):
            # ---- per slot            
            # create frame for put all slot elements there
            F_slotView_oneSlot = tkinter.Frame(F_slotView)
            F_slotView_oneSlot.pack(side="left")
            
            # add header
            Dev = self.AllDevices[slot]
            slotHeader = tkinter.Label( F_slotView_oneSlot, text=Dev ,relief="solid", width= ListWidth) # Dev="nvme0n1"
            slotHeader.pack(side="top")      
                  
            # add listview for current testing item
            Lb = tkinter.Listbox(F_slotView_oneSlot, height = ListHight, width= ListWidth)
            Lb.pack(side="top")
            # save to CurrItems for further processing, ex. ["nvme0n1", Lb0], ["nvme1n1", Lb1]
            self.CurrItems.append([Dev, Lb])
            
            # hight in characters for list available test item  
            Lb = tkinter.Listbox(F_slotView_oneSlot, height = ListHight_ava, width= ListWidth_ava)
            Lb.pack(side="top")
            # save to CurrItems for further processing
            self.AvaItems.append([Dev, Lb]) 
            # ---- end per slot
        
        F_Info = tkinter.Frame(self.root)
        F_Info.pack(side="bottom")        
        self.root.mainloop()
        return True       
                
    def __init__(self, argv):
        # initial parent class
        super(SMI_SRIOV, self).__init__(argv)      
        
        # UI define
        self.UsingGUI=self.CheckTkinter()
        #self.UsingGUI=False
        self.CurrItems=[]   # ex. ["nvme0n1", Lb0], ["nvme1n1", Lb1]
        self.AvaItems=[]    # ex. ["nvme0n1", Lb0], ["nvme1n1", Lb1]
        self.root=None
                
        # get TotalVFs of SR-IOV Virtualization Extended Capabilities Register(PCIe Capabilities Registers)
        self.TotalVFs = self.read_pcie(base = self.SR_IOVCAP, offset = 0x0E) + (self.read_pcie(base = self.SR_IOVCAP, offset = 0x0F)<<8)
        
        # get PrimaryControllerCapabilitiesStructure
        self.PCCStructure = self.Get_PrimaryControllerCapabilitiesStructure()
        
        # get SecondaryControllerList
        # [SCEntryID, class SCE], where SCEntryID = 0, 1, 2, ...
        self.SecondaryControllerList=[]
        self.Get_SecondaryControllerList()     
        
        self.PF_CNTLID = self.CNTLID
        
        # 
        self.VirtualizationManagementCommandSupported= True if self.IsOpcodeSupported(CMDType="admin", opcode=0x1C) else False
        self.NsManagementCommandSupported= True if self.IsOpcodeSupported(CMDType="admin", opcode=0x0D) else False
        self.Sysfs_SRIOV_Supported= True if self.GetCurrentNumOfVF()!=None else False
        
        self.VI_ResourceSupported=False
        if self.PCCStructure != None:
            self.VI_ResourceSupported = True if self.PCCStructure.CRT&0b0010 > 0 else False
            
        self.VQ_ResourceSupported=False
        if self.PCCStructure != None:
            self.VQ_ResourceSupported = True if self.PCCStructure.CRT&0b0001 > 0 else False        
        
        # format test    
        self.LBAF=self.GetAllLbaf()
        # [[LBAF_number, RP, LBADS, MS],[LBAF_number, RP, LBADS, MS],..]   
        self.FormatTestItems=[]
        self.InitFormatTestItems()
        
        # device lists, first is PF, others is VF
        self.AllDevices=list(self.dev)
        
        # Mutex for multi thread, [device, TestItemID,scriptName, writeValue, rtPass]
        self.lock=threading.Lock()
        self.MutexThreadOut=[]
        
        # others
        self.Running=None
        
        
    # define pretest  
    def PreTest(self): 
        '''                    
        self.Print("Check if TotalVFs of SR-IOV Virtualization Extended Capabilities Register(PCIe Capabilities Registers) is large then 0(SR-IOV supported)") 
        self.Print("TotalVFs: %s"%self.TotalVFs)
        if self.TotalVFs>0:
            self.Print("PCIe device support SR-IOV", "p")
        else:
            self.Print("PCIe device do not support SR-IOV, quit all", "w"); return False  
            
        self.Print("")
        self.Print("Check if number of Secondary Controller List in identify structure is equal to the value of")
        self.Print("TotalVFs of SR-IOV Virtualization Extended Capabilities Register(PCIe Capabilities Registers)")        
        NumOfSec = len(self.SecondaryControllerList)        
        self.Print("Number of Secondary Controller: %s"%NumOfSec) 
        self.Print("TotalVFs: %s"%self.TotalVFs)
        if NumOfSec==self.TotalVFs:
            self.Print("Pass", "p"); 
        else: 
            self.Print("Fail, quit all", "f"); return False  
        
        self.Print("")
        if self.VirtualizationManagementCommandSupported:
            self.Print("Virtualization Management Command Supported: Yes")
        else:
            self.Print("Virtualization Management Command Supported: No", "w")
            
        if self.NsManagementCommandSupported:
            self.Print("Namespace Management Command Supported: Yes")
        else:
            self.Print("Namespace Management Command Supported: No", "w")             
            
        if self.PCCStructure != None:
            self.Print("Primary Controller Capabilities Structure is avaliable: Yes")
        else:
            self.Print("Primary Controller Capabilities Structure is avaliable: No", "w")         

        if len(self.SecondaryControllerList) != 0:
            self.Print("Secondary Controller List is avaliable: Yes")
        else:
            self.Print("Secondary Controller List is avaliable: No", "w")                   
                    
        if self.Sysfs_SRIOV_Supported:
            self.Print("Linux's sysfs support SRIOV: Yes")
        else:
            self.Print("Linux's sysfs support SRIOV: No", "w")    
        '''            
        return True            
    
    # <define sub item scripts>
    SubCase1TimeOut = 600
    SubCase1Desc = "Enable all VF with all Flexible Resources"   
    SubCase1KeyWord = ""
    def SubCase1(self):
        ret_code=0       
        
        '''
        self.Print("") 
        self.Print("Set all VF offline")
        if not self.SetCurrentNumOfVF(0):
            self.Print("Fail, quit all", "f"); return 1   
        
        # backup os nvme list            
        VFOff_NvmeList=self.GetCurrentNvmeList()
        
        self.Print("Try to set Primary Controller Resources to Minimum")
        self.Set_PF_ResourceMinimum(printInfo=True)
        self.Print("Done")        
   
        
        self.Print("")     
        self.Print("Try to set Secondary Controller Resources to Minimum")
        self.Set_VF_ResourceMinimum(printInfo=True)
        self.Print("Done")  
        
        self.Print("") 
        self.Print("Set all VF online")
        if not self.SetCurrentNumOfVF(len(self.SecondaryControllerList)):
            self.Print("Fail, quit all", "f"); return 1               
        
        self.Print("")     
        NumOfNS=len(self.SecondaryControllerList)+1
        self.Print("Try to create %s namespaces"%NumOfNS)  
        if not self.CreateMultiNs(NumOfNS, 10000)!=   NumOfNS:
            self.Print("Fail, quit all", "f"); return 1    
            
        self.Print("")             
        self.Print("Try to attach namespaces to make each controller having a private namespace and access to a namespace shared by all controllers")  
        self.Print("    Try to attach namespaces 1 - %s to VF 1 - %s"%(NumOfNS-1, NumOfNS-1))
        nsid=1
        for SCEntry in self.SecondaryControllerList:
            SCID= SCEntry.SCID
            if not self.AttachNs(nsid, SCID) ==0:
                self.Print("    Fail at nsid=%s, quit all"%nsid, "f"); return 1    
            nsid=nsid+1      
        self.Print("Done")
        self.Print("    Try to attach namespaces %s to all VF"%(NumOfNS)) 
        nsid=NumOfNS
        for SCEntry in self.SecondaryControllerList:
            SCID= SCEntry.SCID
            if not self.AttachNs(nsid, SCID) ==0:
                self.Print("    Fail at SCID=%s, quit all"%SCID, "f"); return 1            
        self.nvme_reset()                
        self.Print("Done")
                
        self.Print("")     
        self.Print("Check if the Controller List of Identify command with CNS=0x12 indicates that namespaces 1 - %s was attached to VF 1 - %s"%(NumOfNS-1, NumOfNS-1))   
        self.Print("And namespaces %s was attached to all VF  "%(NumOfNS))
        self.Print("------------------------------------------------------")   
        for nsid in range(1 , NumOfNS+1):
            isPass = True
            # if not last one, namespaces attach to 1 SCID only
            if nsid!=NumOfNS:
                CL = self.GetControllerList_ThatAreAttachedToTheNamespace(nsid)
                SCID = self.SecondaryControllerList[nsid-1].SCID
                if CL[0]!=SCID: isPass = False
            else:
            # namespaces was attached to all VF 
                CL = self.GetControllerList_ThatAreAttachedToTheNamespace(nsid)
                CL.sort()                
                SCID = [SCEntry.SCID for SCEntry in self.SecondaryControllerList]
                SCID.sort()
                if CL[0]!=SCID: isPass = False

            if isPass:
                self.Print("namespaces %s : ControllerList: %s : Pass"%(nsid, CL), "p")
            else:
                self.Print("namespaces %s : ControllerList: %s : Fail"%(nsid, CL), "f")
                ret_code = 1
            
        self.Print("------------------------------------------------------")   
        if ret_code!=0: return 1
        

        
        # linux nvme list after enable VF
        VFOn_NvmeList=self.GetCurrentNvmeList()
        VFDevices = list(set(VFOn_NvmeList) - set(VFOff_NvmeList)).sort()
        NumOfVF=len(self.SecondaryControllerList)
        self.Print("Check if linux os create %s NVMe device under folder /dev/"%NumOfVF)
        self.Print("")
        for Dev in VFDevices:
            self.Print(Dev)
        if NumOfVF==len(VFDevices):
            self.Print("Pass","p")
        else:
            self.Print("Fail, quit all", "f"); return 1
        
        # check if all controller is enabled
        self.Print("Check if all SCEntry is enabled in identify structure -> SecondaryControllerList")
        # get identify structure
        self.Get_SecondaryControllerList()    
        for SCEntry in self.SecondaryControllerList:
            SCEntryID = SCEntry[0]
            SCE = SCEntry[1]
            # if Secondary Controller State (SCS)=1, controller is online
            if (SCE.SCS&0b1) ==1:    
                self.Print("SCEntry %s is enabled"%SCEntryID,"p")
            else:
                self.Print("SCEntry %s is disabled, quit all"%SCEntryID,"f"); return 1
        
        # append all devices for testing , where AllDevices[0] is PF, others is VF     
        PFDevices= [self.dev]
        self.AllDevices = PFDevices + ["/dev/nvme1n1"]
                
        # test all test item in one VF and other VF/PF should not be modified 
        self.TestSpecificVFandOtherVFshouldNotBeModified(self.AllDevices[1])
        '''
        
        self.AllDevices = [self.dev] + ["/dev/nvme1n1"]
        self.MultiThreadTest(10)
        

            
        
        
        
        
        
        
        
        
        
                
        self.Print("")     
        self.Print("Try to run SMI_DSM.py for nvme1n1")   
        self.write
        
        print "rtcode=%s"%self.RunSMIScript("SMI_SubProcess/mtest.py", "%s 1,3"%self.dev)
        
        
        '''
        self.Print("")    
        if self.VI_ResourceSupported:
            VIResourcesFlexibleTotal=self.PCCStructure.VIFRT
            
            
            
            
        # minimum number of VQ Resources that may be assigned is two    
            
            
        '''
        


        
        return ret_code

    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_SRIOV(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    