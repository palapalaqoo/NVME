#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
import re
from time import sleep
import time
import threading
import os
import xml.etree.ElementTree as ET
import datetime

# Import VCT modules
from lib_vct.NVME import NVME
from lib_vct import mStruct
from random import randint





class SMI_SRIOV(NVME):
    ScriptName = "SMI_SRIOV.py"
    Author = "Sam"
    Version = "20200325"
    
    TypeInt=0x0
    TypeStr=0x1    

    File_Config = "./CSV/In/config.csv"    
    
        
    def ParseConfigFile(self):
        if not self.isfileExist(self.File_Config):
            return False
        else:            
            ParseCfgList = self.ReadCSVFile(self.File_Config)
            for mItem in ParseCfgList:
                # if start char=# means it is a comment, and quit it
                mStr = "^#"
                if re.search(mStr, mItem[0]):
                    pass   
                else:                 
                    Name=mItem[0]        
                    if Name=="numvfs":
                        self.config_numvfs=int(mItem[1] )
            return True
            
    
    
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
    
    class VMinfoClass():            
        # VM
        vmName=None
        vmHostNVMEname=None
        vmXmlFilePCIE=None
        vmPciePort=None   
        vmIpAddr=None
        vmXmlFileRawDisk=None
                    
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
    

    # set vf, if success, set AllDevices where AllDevices[0] is PF, others is VF 
    def SetCurrentNumOfVF(self, value):
        value=int(value)
        #path="/sys/class/block/%s/device/device/sriov_numvfs"%self.dev[5:]
        path="/sys/bus/pci/devices/%s/sriov_numvfs"%self.pcie_port
        if self.isfileExist(path):
            if self.shell_cmd("echo %s > %s 2>&1  ; echo $?"%(value, path))!="0" :
                self.Print("command fail", "f"); return False
            else:
                if value!=0: 
                    # wait for os to create drive        
                    sleep(2)
                    # backup dmesg
                    dmesgFileNameLast = "dmesgAfterSRIOV_Last.txt"
                    dmesgFileNameCurr = "dmesgAfterSRIOV_Curr.txt"            
                    self.DmesgBackup(dmesgFileNameLast, dmesgFileNameCurr)
                    # get VF list
                    self.VFDevices = self.GetVFListCreatedByPF()
                    # save to AllDevices
                    self.AllDevices = [self.dev] + self.VFDevices
                    self.Print("Check if linux os create %s NVMe device under folder /dev/"%value)
                    self.Print("Created VF drive:")
                    for Dev in self.VFDevices:
                        self.Print("        %s"%Dev)
                    if value==len(self.VFDevices):
                        self.Print("Pass","p")
                    else:
                        self.Print("Fail", "f"); return False
        else:
            self.Print("Can't find file: %s"%path, "f"); return False
        
        return True 
        
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
    def TestWriteRead(self, SubDUT, writeValue=0):
    # SubDUT type is NVME
        # write 10M data with writeValue
        SubDUT.fio_write(offset=0, size="10M", pattern=writeValue, nsid=1, devPort=SubDUT.dev_port)
        if SubDUT.fio_isequal(offset=0, size="10M", pattern=writeValue, nsid=1):
            return True
        else:
            self.Print("Device: %s TestWriteRead fail: expected pattern is %s"%(SubDUT, writeValue), "f")
            return False
           
    
    def TestWriteCompare(self, SubDUT, writeValue=0):
        # write 10M data with writeValue
        SubDUT.fio_write(offset=0, size="10M", pattern=writeValue, nsid=1, devPort=SubDUT.dev_port)
        # compare command
        oct_val=oct(writeValue)[-3:]
        mStr=SubDUT.shell_cmd("dd if=/dev/zero bs=512 count=1 2>&1   |tr \\\\000 \\\\%s 2>/dev/null |nvme compare %s  -s 0 -z 512 -c 0 2>&1"%(oct_val, SubDUT.dev))
        
        # expected compare command is the same value, i.e. 'compare: Success"    
        if bool(re.search("compare: Success", mStr)):
            return True
        else:
            self.Print("Device: %s TestWriteCompare fail: expected pattern is %s"%(SubDUT, writeValue), "f")
            return False      
    
    def TestWriteFormatRead(self, SubDUT, writeValue=0):
        # write 10M data with writeValue
        SubDUT.fio_write(offset=0, size="10M", pattern=writeValue, nsid=1, devPort=SubDUT.dev_port)
        # format
        nsid=1; lbaf=0; ses=0; pil=0; pi=0; ms=0
        mStr=SubDUT.shell_cmd(" nvme format %s -n %s -l %s -s %s -p %s -i %s -m %s 2>&1"%(SubDUT.dev_port, nsid, lbaf, ses, pil, pi, ms))
        retCommandSueess=bool(re.search("Success formatting namespace", mStr))  
        if not retCommandSueess:
            self.Print("Fail to format %s, quit all"%SubDUT.dev, "f"); return False            
        # after format, expected pattern = 0  
        if SubDUT.fio_isequal(offset=0, size="10M", pattern=0, nsid=1):
            return True
        else:
            self.Print("Device: %s TestWriteFormatRead fail: expected pattern is %s"%(SubDUT, 0), "f")
            return False         
   
    def TestWriteSanitizeRead(self, SubDUT, writeValue=0):  
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
        if not SubDUT.WaitSanitizeFinish(240): return False            
        # expected pattern = 0
        if SubDUT.fio_isequal(offset=0, size="10M", pattern=0, nsid=1):
            return True
        else:
            self.Print("Device: %s TestWriteSanitizeRead fail: expected pattern is %s"%(SubDUT, 0), "f")
            return False    
    
    def TestWriteUncRead(self, SubDUT, writeValue=0):
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

    def nvme_reset(self, SubDUT, writeValue=0):
        rtcode = self.shell_cmd("  nvme reset %s; echo $? "%(SubDUT.dev_port), 0.5)
        sleep(1) 
        return True if rtcode=="0" else False
    
    def hot_reset(self, SubDUT, writeValue=0):
        self.shell_cmd("  echo 1 > /sys/bus/pci/devices/%s/remove " %(SubDUT.pcie_port), 0.1) 
        self.shell_cmd("  echo 1 > /sys/bus/pci/rescan ", 0.1)
        sleep(1)     
        return True        
    
    def FunctionLevel_reset(self, SubDUT, writeValue=0):       
        SubDUT.write_pcie(SubDUT.PXCAP, 0x9, SubDUT.IFLRV)
        sleep(1)
        self.shell_cmd("  echo 1 > /sys/bus/pci/devices/%s/reset " %(SubDUT.pcie_port), 2) 
        if SubDUT.dev_alive:            
            return True        
        else:
            return False     
    
    def DeleteCreateAttach_NS(self, SubDUT, writeValue=0):        
        return SubDUT.ResetNS()                
                      
    
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
    '''
    def TestSpecificVFandOtherVFshouldNotBeModified(self, SpecificDevice):
        
        #write data to all devices, except SpecificDevice
        self.Print("Write data to all devices, e.g. '/dev/nvme0n1' to the first block of /dev/nvme0n1, etc..")
        for Dev in self.AllDevices:         
            # write '/dev/nvme0n1' to the first block of /dev/nvme0n1 and  '/dev/nvme1n1' to /dev/nvme1n1                
            CMD= "echo %s | nvme write %s --data-size=512 --prinfo=1 2>&1 > /dev/nul"%(Dev, Dev)
            self.shell_cmd(CMD)
            
        # verify    
        self.Print("Check the block 0 of all devices .")
        if not self.VerifyAllDevices(excludeDev=None, printInfo=True): return False            
                
        self.Print("")        
        # create SubDUT to use NVME object for specific device, e.x. /dev/nvme0n1,  note that argv is type list
        SubDUT = NVME([SpecificDevice])        

        if self.TestModeOn:
            SubDUT.RecordCmdToLogFile=True     
                            
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
                self.Print("Fail, quit all", "f"); return False
            
            # check data in other controllers     
            self.Print("Check if data in other controller has not been modified"); 
            if self.VerifyAllDevices(excludeDev=SpecificDevice, printInfo=False): 
                self.Print("Pass", "p"); 
            else:
                self.Print("Fail", "p"); 
                # print info again
                self.VerifyAllDevices(excludeDev=SpecificDevice, printInfo=True)
                self.Print("Quit all", "p");
                return False
            self.Print("")
        return True
    '''
    def Push(self, device, TestItemID,scriptName, writeValue, rtPass):
        # write info to mutex variable
        self.lock.acquire()
        # MutexThreadOut [device, TestItemID,scriptName, writeValue, rtPass]
        self.MutexThreadOut.append([device, TestItemID,scriptName, writeValue, rtPass])                
        self.lock.release()        
            
    def ThreadTest(self, device, DevType, testTime): 
        # device = /dev/nvmeXn1
        # DevType ="PF" of "VF"
        
        # create SubDUT to use NVME object for specific device, e.x. /dev/nvme2n1, note that argv is type list
        SubDUT = NVME([device])    
        
        # get test items for current device
        ThreadTestItem=self.GetCurrentDutTestItem(SubDUT, DevType)
        # unmask below to get all command in /log/xxxx.cmdlog
        if self.TestModeOn:
            SubDUT.RecordCmdToLogFile=True        
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
            # if any thread fail
            if not self.IsPass: break
                        
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
            # if return code is not zero,set IsPass=false and quit
            if not rtPass: 
                self.IsPass=False
                break                
            
    def MultiThreadTest(self, testTime): 
        rtResult=True
        # if using GUI, create GUI by threading
        if self.UsingGUI:
            tGUI = threading.Thread(target = self.ThreadCreatUI)
            tGUI.start() 
            # wait window start
            sleep(1)
            
                
        # call ThreadTest(self, device, testTime) for all devices to test their testitems at the same time
        mThreads = [] 
        # clear mutex variable and IsPass=true before any thread start 
        self.MutexThreadOut=[]
        self.IsPass=True
        isPF=True
        for Dev in self.AllDevices:
            # first is PF, others are VF
            if isPF:
                DevType = "PF"
                isPF=False
            else:
                DevType = "VF"
            
            t = threading.Thread(target = self.ThreadTest, args=(Dev, DevType, testTime,))
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
                                rtResult=False                           
                        
        # if using GUI, close GUI
        if self.UsingGUI:
            sleep(2)
            self.root.quit()   
            
        return rtResult                     

    def PrintAlignString(self,S0, S1, S2, PF="default"):            
        mStr = "{:<25}\t{:<40}\t{:<20}".format(S0, S1, S2)
        if PF=="pass":
            self.Print( mStr , "p")        
        elif PF=="fail":
            self.Print( mStr , "f")      
        else:
            self.Print( mStr ) 
            
    def GetCurrentDutTestItem(self, SubDUT, DevType):
        # DevType ="PF" of "VF"
        # get current device test item, ex. /dev/nvme0n1 may test all feature
        ThreadTestItem=[]
        # add test items
        ThreadTestItem.append(["Write_Read", self.TestWriteRead])
        #ThreadTestItem.append(["Write_Compare", self.TestWriteCompare])                
        # if ibaf0 is supported, i.e.  lbaf0->lbads>9 , then add test item 'TestWriteFormatRead'
        #LBAF=SubDUT.GetAllLbaf()
        #LBAF0_LBADS=LBAF[0][SubDUT.lbafds.LBADS]
        #LBAF0Supported = True if (LBAF0_LBADS >=  9) else False
        #ThreadTestItem.append(["Write_Format_Read", self.TestWriteFormatRead]) if LBAF0Supported else None        
        # if BlockErase sanitize is supported, i.e.  sanicap_bit1=1 , then add test item 'TestWriteSanitizeRead'
        #BlockEraseSupport = True if (SubDUT.IdCtrl.SANICAP.bit(1) == "1") else False
        #ThreadTestItem.append(["Write_Sanitize_Read", self.TestWriteSanitizeRead]) if BlockEraseSupport else None        
        # if WriteUncSupported is supported , then add test item 'WriteUncSupported'
        #WriteUncSupported = True if SubDUT.IsCommandSupported(CMDType="io", opcode=0x4) else False
        #ThreadTestItem.append(["WriteUnc_Read", self.TestWriteUncRead]) if WriteUncSupported else None
        # nvme_reset
        #ThreadTestItem.append(["Controller_Reset", self.nvme_reset])
        # hot_reset
        #ThreadTestItem.append(["Hot_Reset", self.hot_reset])   
        # DeleteCreateAttach_NS
        #NsSupported=True if SubDUT.IdCtrl.OACS.bit(3)=="1" else False
        #ThreadTestItem.append(["DeleteCreateAttach_NS", self.DeleteCreateAttach_NS]) if NsSupported else None   
        
        # if is VF     
        #if DevType=="VF":
        #    ThreadTestItem.append(["FunctionLevel_reset", self.FunctionLevel_reset]) 
              
            
                   
        
        return ThreadTestItem


            
    def GetNextTestItemID(self,TotalItem, TestItemID_old):
        # return random ID that is different from  TestItemID_old
        # if TotalItem=1 return 0 to assign the only 1 item to be tested
        if TotalItem==1:
            return 0
        while True:
            NewID = randint(1, 0xFF) % TotalItem
            if NewID!=TestItemID_old:
                return NewID
        
    # -------------------------------------------------------------------
    
    def GetCurrentNvmeList(self):
        mStr=self.shell_cmd("nvme list")
        return re.findall("/dev/nvme\d+n\d+", mStr)
        
        

            

                
    def ThreadCreatUI(self):
        numOfDev = len(self.AllDevices)
        ListWidth = 20  # width in characters for current testing item
        ListHight = 20  # hight in characters for current testing item
        ListWidth_ava = 20  # width in characters for list available test item
        ListHight_ava = 10  # hight in characters for list available test item

        InfoHight = 20 # hight in characters        
        self.root=self.tkinter.Tk()  
        self.root.geometry('{}x{}'.format(1000, 800))
        import tkMessageBox
        
        F_slotView = self.tkinter.Frame(self.root)
        F_slotView.pack(side="top")
        
        
        for slot in range(numOfDev):
            # ---- per slot            
            # (highlightbackground="brown", highlightcolor="brown", highlightthickness=2, bd=0) for brown border color
            # create frame for put all slot elements there
            F_slotView_oneSlot = self.tkinter.Frame(F_slotView, relief="flat",  highlightbackground="brown", highlightcolor="brown", highlightthickness=2, bd=0)
            F_slotView_oneSlot.pack(side="left")
            
            # add header
            Dev = self.AllDevices[slot]
            slotHeader = self.tkinter.Label( F_slotView_oneSlot, text=Dev , width= ListWidth,relief="flat", highlightbackground="brown", highlightcolor="brown", highlightthickness=2, bd=0) # Dev="nvme0n1"
            slotHeader.pack(side="top")      
                  
            # add listview for current testing item
            Lb = self.tkinter.Listbox(F_slotView_oneSlot, height = ListHight, width= ListWidth, relief="flat")
            Lb.pack(side="top")
            # save to CurrItems for further processing, ex. ["nvme0n1", Lb0], ["nvme1n1", Lb1]
            self.CurrItems.append([Dev, Lb])
            
            # add header

            slotHeader = self.tkinter.Label( F_slotView_oneSlot, text="Available test items" , width= ListWidth,relief="flat", highlightbackground="brown", highlightcolor="brown", highlightthickness=2, bd=0) # Dev="nvme0n1"
            slotHeader.pack(side="top")  
                        
            # hight in characters for list available test item  
            Lb = self.tkinter.Listbox(F_slotView_oneSlot, height = ListHight_ava, width= ListWidth_ava,relief="flat")
            Lb.pack(side="top")
            # save to CurrItems for further processing
            self.AvaItems.append([Dev, Lb]) 
            
            # create frame space
            F_slotView_space = self.tkinter.Frame(F_slotView,  width=10)
            F_slotView_space.pack(side="left")            
            # ---- end per slot
        
        F_Info = self.tkinter.Frame(self.root)
        F_Info.pack(side="bottom")        
        self.root.mainloop()
        return True       
                
                
    def GetVMList(self):
    # return [id, name, state]
        rtList=[]
        mStr=self.shell_cmd("virsh list --all| sed 1,2d")   # remove first line for re.search   
        # ' -     VM0                            shut off'         
        comp = "\S+\s+VM\d+\s+.+"
        OneVM = re.findall(comp, mStr)
        if OneVM!=None:
            comp = "(\S)+\s+(VM\d)+\s+(.+)"
            for mVM in OneVM:
                # id may equal '-', means not active
                Id =re.search(comp, mVM).group(1)
                if Id=="-":
                    Id=0
                else:
                    Id =int(Id)
                    
                Name =re.search(comp, mVM).group(2)
                State =re.search(comp, mVM).group(3)
                rtList.append([Id, Name, State])
            return rtList
        else:
            return None
                
    def AttachDeviceToVM(self, VMname, XMLfile):
        fullPath="./SRIOV_Resources/%s"%XMLfile
        self.shell_cmd("virsh attach-device %s %s"%(VMname, fullPath))
        
    def DetachDeviceToVM(self, VMname, XMLfile):
        fullPath="./SRIOV_Resources/%s"%XMLfile
        self.shell_cmd("virsh detach-device %s %s"%(VMname, fullPath))    
    
    def GetCurrentXMLforAttachDetachPCIE(self):
        VM_xml_list=[]
        mFile = self.shell_cmd("ls ./SRIOV_Resources |grep 'AttachDetachPCIE_'")
        findall = re.findall("(AttachDetachPCIE_\w*_.*.xml)", mFile)
        pattern = "AttachDetachPCIE_(\w*)_(.*).xml"       
        for mStr in findall:       
            if re.search(pattern, mStr):
                VMname = re.search(pattern, mStr).group(1) 
                pcie_port = re.search(pattern, mStr).group(2) 
                fileName=mStr
                VM_xml_list.append([ "none", fileName, pcie_port, VMname])    
        return VM_xml_list
    
    def CreateXMLforAttachDetachPCIE(self):
        #Create XML("AttachDetachPCIE.xml") file for attach/detach pci, command as below(VF0 is the name of VM)
        # virsh attach-device VF0 AttachDetachPCIE.xml 
        # virsh detach-device VF0 AttachDetachPCIE.xml  
        
        VM_xml_list=[]
        
        # remove old
        self.shell_cmd("cd SRIOV_Resources; rm -f AttachDetachPCIE_*")
        
        # for all VF devices
        i=0
        for device in self.VFDevices:
                              
            SubDUT = NVME([device]) 
            VMname="VM%s"%i            
            fileName = "AttachDetachPCIE_%s_%s.xml"%(VMname, SubDUT.pcie_port)
            i=i+1
            # get nvme pci port                 
            sBus, sSlot, sFunc = self.GetPortBusSlotFunc(SubDUT)        
    
            sBus = int(sBus)
            sSlot = int(sSlot)
            sFunc= int(sFunc)
            domain='0x0000'
            fullPath="./SRIOV_Resources/%s"%fileName
            if self.isfileExist(fullPath):
                self.rmFile(fullPath)
                
            # create the file structure
            hostdev = ET.Element('hostdev')
            source = ET.SubElement(hostdev, 'source')
            source_address = ET.SubElement(source, 'address')
            rom = ET.SubElement(hostdev, 'rom')
            address = ET.SubElement(hostdev, 'address')
            
            hostdev.set('mode','subsystem')
            hostdev.set('type','pci')
            hostdev.set('managed','yes')
            
            # host pcie port, ex. 0000:01:00.0 
            source_address.set('domain',domain)
            source_address.set('bus',"0x%X"%sBus)
            source_address.set('slot',"0x%X"%sSlot)
            source_address.set('function',"0x%X"%sFunc)
            
            # rom bar
            rom.set('bar','on')
            
            # VM pcie port, find a unused port in VM before fill this value
            address.set('type','pci')         
            
            # create a new XML file with the results
            mydata = ET.tostring(hostdev)
            myfile = open(fullPath, "w")
            myfile.write(mydata) 
            
            # save to VM_xml_list, example [ '/dev/nvme1n1' , 'AttachDetachPCIE_0000:01:00.1', '0000:01:00.1' ]
            VM_xml_list.append([ device, fileName, SubDUT.pcie_port, VMname])   
        return VM_xml_list    

    def FormatPFtoExt4(self):
        # Format PF where PF = AllDevices[0]
        self.shell_cmd("sudo mkfs -t ext4 %s 2>&1 >/dev/null"%self.AllDevices[0])
        
    def MountPF(self):
        # Mount PF to folder , where PF = AllDevices[0]
        # mkdir for further mount PF
        if not self.isfileExist("SRIOV_Resources/MntPF"):
            self.shell_cmd("sudo mkdir SRIOV_Resources/MntPF")
        # mount PF
        self.shell_cmd("sudo mount %s SRIOV_Resources/MntPF 2>&1 >/dev/null"%self.AllDevices[0])        

    def CreateRawDiskImg(self, numOfDisk, DiskSize="5G"):
    # Create raw disk on it
    # e.g. in SRIOV_Resources/MntPF,  create vmdisk0.img, vmdisk1.img ..., and so on.
        # create raw disk
        for i in range(numOfDisk):
            self.shell_cmd("cd SRIOV_Resources/MntPF; qemu-img create -f raw -o preallocation=full vmdisk%s.img %s"%(i, DiskSize))
        # check result for create raw disk
        return self.isNumOfRawDiskImgExist(numOfDisk)
            


    def isNumOfRawDiskImgExist(self, numOfDisk):
    # check if raw disk inage is exist
        for i in range(numOfDisk):            
            if not self.isfileExist("SRIOV_Resources/MntPF/vmdisk%s.img"%i):
                return False        
        return True 
        

    def CreateXMLforAttachDetachRawDisk(self):
        #Create XML("AttachDetachRawDisk_0.xml") file for attach/detach PF raw image drive, command as below(VF0 is the name of VM)
        # virsh attach-device VF0 AttachDetachRawDisk_0.xml 
        # virsh detach-device VF0 AttachDetachRawDisk_0.xml       
        VM_xml_list=[]   
        numOfDisk = len(self.VMinfo)
        if not self.isNumOfRawDiskImgExist(numOfDisk):
            self.Print("Error, number of vmdisk in 'SRIOV_Resources/MntPF' is not match number of VM, expect %s files"%numOfDisk)
            return 1
        
        # for numOfDisk
        for i in range(numOfDisk):
                              
            # data pattern generation
            mDIR = os.path.dirname(os.path.realpath(__file__))
            mydata = "<disk type='block' device='disk'> \
                            <driver name='qemu' type='raw' cache='none' io='native'/> \
                            <source dev='%s/SRIOV_Resources/MntPF/vmdisk%s.img'/> \
                            <target dev='vda' bus='virtio'/> \
                            </disk>"%(mDIR, i)
            
            # create a new XML file with the results
            fileName = "AttachDetachRawDisk_%s.xml"%i
            fullPath="./SRIOV_Resources/%s"%fileName
            myfile = open(fullPath, "w")
            myfile.write(mydata) 
            # save to VM_xml_list, example [ 'AttachDetachRawDisk_0' ]
            VM_xml_list.append(fileName)   
        return VM_xml_list                 
    
    def CreateVM(self, VMname, CPU=1, RAM=1024):
        mDIR = os.path.dirname(os.path.realpath(__file__))
        TempFullPath=mDIR + "/SRIOV_Resources/Template.qcow2"        
        VMfullPath=mDIR + "/SRIOV_Resources/%s.qcow2"%VMname

        if not self.isfileExist(TempFullPath):
            self.Print("Template file not found: %s, quit"%TempFullPath)
            return False
        
        # if VM exist, delete it
        VirshList = self.GetVMList()
        if VirshList!= None:
            for List in VirshList:     
                ListVMname=List[1]     
                if ListVMname==VMname:
                    self.Print("Previous %s exist, try to remove it and rebulid"%ListVMname)
                    ListState = List[2]
                    # if is running, do shut down first
                    if ListState=="running":
                        self.shell_cmd("virsh destroy  --domain %s"%ListVMname)
                    self.shell_cmd("virsh undefine --domain %s"%ListVMname)
        
        
        # if file exist, remove it
        if self.isfileExist(VMfullPath):
            self.rmFile(VMfullPath)
            
        # create Snapshot image
        self.shell_cmd("qemu-img create -f qcow2 -o backing_file=%s %s"%(TempFullPath, VMfullPath))
        
        # create VM, --vcpus %s = number of cpu
        CMD="virt-install -n %s --vcpus=1,maxvcpus=1,sockets=1,cores=2,threads=4 --cpuset=%s -r %s --cpu host-model-only --os-type=linux --disk %s,device=disk,bus=ide -w  bridge=virbr0,model=virtio \
        --vnc  --import   --os-variant rhel7 --noautoconsole"%(VMname, CPU, RAM, VMfullPath) 
        self.shell_cmd(CMD)

        # verify
        if self.shell_cmd("virsh list --all |grep %s 2>&1 >/dev/null; echo $?"%VMname)=="0":
            return True
        else:
            return False
        
    def PowerOnVM(self, VMname):
        self.shell_cmd("virsh start %s"%VMname)
        
    def PowerOffVM(self, VMname):
        self.shell_cmd("virsh shutdown  %s"%VMname)       
    
    def VM_shell_cmd(self, IP, CMD):
        if self.paramiko==None:
            self.Print("paramiko not installed!", "f")
        else:
            #self.lock.acquire()
            s = self.paramiko.SSHClient()
            s.set_missing_host_key_policy(self.paramiko.AutoAddPolicy())
            s.connect(hostname=IP, port=22, username="root", password="Smi888")
            stdin, stdout, stderr = s.exec_command(CMD)
            #self.lock.release()
            return stdout.read()
            
    
    def GetPortBusSlotFunc(self, SubDUT):
        mPort = SubDUT.pcie_port # 0000:01:00.0
        Bus = re.search(":(\d+):(\d+).(\d+)", mPort).group(1)
        Slot = re.search(":(\d+):(\d+).(\d+)", mPort).group(2)
        Func = re.search(":(\d+):(\d+).(\d+)", mPort).group(3)
        return Bus, Slot, Func
        
    def GetVM_IPaddr(self, VMname, timeout):
        # ex. ? (192.168.122.222) at 52:54:00:5c:1c:2b [ether] on virbr0
        StartTime=time.time()
        while True:            
            rtArp = self.shell_cmd("arp -na | grep $(virsh domiflist %s | tail -n +3 | awk '{print$5}' | sed '/^$/d') "%VMname)
            if re.search("\((.*)\)", rtArp):
                IP = re.search("\((.*)\)", rtArp).group(1)    
            else:
                IP =None    
            
            # got ip    
            if IP!=None: break                            
            # timeout          
            CurrentTime = time.time()
            if (CurrentTime-StartTime)>timeout: break
            sleep(1)
            
        return IP
    
    def GetFIO_Speed(self, FIOresult, rw="w"):
        # FIOresult, where command  --output-format=terse 
        # rw = read/write
        findall = re.findall("([^;]*);", FIOresult)
        if len(findall)>0:
            read_BW_in_KBs = findall[6]
            write_BW_in_KBs = findall[47]
            if rw=="w":
                return int(write_BW_in_KBs)
            if rw=="r":
                return int(read_BW_in_KBs)
            return None
        else:
            return None    
        
    def DoHost_FIOtest(self, device, outputFilename):
        # issue command
        FIO_CMD = self.FIO_CMD(device)
        mStr = self.shell_cmd(FIO_CMD)
        
        # save to file, FilePath=./Log/FIO_devnvme0n1.txt
        FilePath = "./Log/%s"%outputFilename
        with open(FilePath, "w") as text_file:
            text_file.write(mStr)
        
        # check if get fio bw    
        speedInKbyte = self.GetFIO_Speed(mStr)
        if speedInKbyte==None:
            return False  
        else:       
            return True        
        
    def DoVM_FIOtest(self, info, targetDevice = "/dev/nvme0n1", rw="w"):
        # targetDevice = "/dev/nvme0n1" for SRIOV in all VMs
        # targetDevice = "/dev/vda" for raw disk in all VMs
        # rw: read = "r", write = "w"
        '''
        ReadWrite="write" if rw=="w" else "read" 
        FIO_CMD = self.FIO_CMD(targetDevice, rw)
        self.Print(FIO_CMD)   
        IP=info.vmIpAddr
        VMname= info.vmName
        
        # remove old fio out file
        self.VM_shell_cmd(IP, "rm -f fioOut")        
        # issue FIO test and run in background
        FIO_CMD = FIO_CMD + " >> fioOut &"
        mStr = self.VM_shell_cmd(IP, FIO_CMD)
        # grab output file and parse to bandwidth with timeout 3600
        for cnt in range(60):
            sleep(1)
            mStr = int(self.VM_shell_cmd(IP, "cat fioOut 2>&1 >/dev/null ; echo $?"))
            if mStr==0: # fio finish, file exist
                mStr = self.VM_shell_cmd(IP, "cat fioOut")               
                speedInKbyte = self.GetFIO_Speed(mStr)
                if speedInKbyte==None:
                    self.Print("FIO fail", "f")
                    return False  
                else:   
                    self.Print("FIO %s %s: bw=%.1f MiB/s,  bandwidth (KB/s):%s"%("write", VMname, speedInKbyte/float(1024), speedInKbyte), "f") 
                    return True
        return False  
        '''
    

        # targetDevice = "/dev/nvme0n1" for SRIOV in all VMs
        # targetDevice = "/dev/vda" for raw disk in all VMs
        # rw: read = "r", write = "w"
        ReadWrite="write" if rw=="w" else "read" 
        FIO_CMD = self.FIO_CMD(targetDevice, rw)
        self.Print(FIO_CMD)   
        IP=info.vmIpAddr
        VMname= info.vmName
        mStr = self.VM_shell_cmd(IP, FIO_CMD)
        speedInKbyte = self.GetFIO_Speed(mStr, rw)
        if speedInKbyte==None:
            self.Print("FIO fail", "f")
            return False  
        else:   
            self.Print("FIO %s %s: bw=%.1f MiB/s,  bandwidth (KB/s):%s"%(ReadWrite, VMname, speedInKbyte/float(1024), speedInKbyte), "f") 
            self.FIOresultList.append([VMname, speedInKbyte])
            return True
  

    def DoHostStandaloneAllDeviceFIOtest(self):
    # HostFIOsimuOutList, simultaneously test result file        
        HostFIOoutList=[]
        for device in self.AllDevices:
            self.Print("Do FIO for  %s"%device)
            FileName = "HostFIO_%s.txt"%device.replace("/","")
            HostFIOoutList.append(FileName)
            if not self.DoHost_FIOtest(device, FileName):
                return 1
            else:                
                mStr =self.ReadFile(FileName)
                speedInKbyte = self.GetFIO_Speed(mStr)
                if speedInKbyte==None:
                    self.Print("FIO fail", "f")
                    return 1
                else:
                    self.Print("Result: FIO write %s: bw=%.1f MiB/s,  bandwidth (KB/s):%s"%(device, speedInKbyte/float(1024), speedInKbyte), "f")    
        return HostFIOoutList
    
    def DoHostSimultaneouslyFIOtest(self,deviceList):
    # deviceList, device will be compared
    # HostFIOsimuOutList, simultaneously test result file
        mThreads = [] 
        HostFIOsimuOutList=[]
        for device in deviceList:
            FileName = "HostFIOsimu_%s.txt"%device.replace("/","")
            HostFIOsimuOutList.append(FileName)
            t = threading.Thread(target = self.DoHost_FIOtest, args=(device,FileName,))
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
        return HostFIOsimuOutList
          
    def DoSpeedCompare(self,deviceList, HostFIOoutList, HostFIOsimuOutList):
    # deviceList, device will be compared
    # HostFIOoutList, standalone test result file
    # HostFIOsimuOutList, simultaneously test result file
        self.Print("------------------------------------------------------")   
        self.PrintAlignString("Device", "standalone", "simultaneously")
        cnt=0
        sumSpeedSimu=0
        sumSpeedStand=0
        for device in deviceList:
            mStr =self.ReadFile(HostFIOoutList[cnt])
            speedInKbyteStand = self.GetFIO_Speed(mStr)
            mStr =self.ReadFile(HostFIOsimuOutList[cnt])
            speedInKbyteSimu = self.GetFIO_Speed(mStr) 
                
            speedStand = speedInKbyteStand/float(1024)
            sumSpeedStand = sumSpeedStand+speedStand
            speedSimu = speedInKbyteSimu/float(1024)
            sumSpeedSimu = sumSpeedSimu + speedSimu
            self.PrintAlignString(device, "%.1f MB/s"%speedStand, "%.1f MB/s"%speedSimu, "pass")
            cnt=cnt+1
            
        self.Print("") 
        self.Print("------------------------------------------------------") 
        SpeedStandAverage=sumSpeedStand/len(deviceList)
        speedText = self.UseStringStyle("%.1f MB/s"%SpeedStandAverage, fore="green")
        self.Print("Average speed for %s, %s .. :  %s"%(deviceList[0], deviceList[1], speedText)) 
        speedText = self.UseStringStyle("%.1f MB/s"%sumSpeedSimu, fore="green")
        self.Print("Simultaneously test sum of bw for %s, %s .. :  %s"%(deviceList[0], deviceList[1], speedText)) 
        self.Print("") 
        percent = 0.9
        self.Print("Check if sum of bw for Simultaneously test is > Average speed * %s (tolerance)"%percent) 
        if sumSpeedSimu>=SpeedStandAverage*percent:
            self.Print("Pass", "p") 
            return True
        else:
            self.Print("Fail", "f")  
            return False
                
        
    def ReadFile(self, Filename):    
        with open("./Log/%s"%Filename, 'r') as content_file:
            content = content_file.read()      
        return content  
        
    def FIO_CMD(self, device, rw="w"):
        # output format terse,normal
        '''
        ReadWrite="write" if rw=="w" else "read"       
        
        return "fio --direct=1 --iodepth=1 --ioengine=libaio --bs=64k --rw=%s --numjobs=1 " \
            "--offset=0 --filename=%s --name=mdata --do_verify=0  " \
            "--output-format=terse,normal --runtime=10"%(ReadWrite, device)        
        '''
        ReadWrite="write" if rw=="w" else "read" 
        return "fio --direct=0 --iodepth=128 --ioengine=libaio --bs=128k --rw=%s --numjobs=1 --size=10G " \
            "--offset=0 --filename=%s --name=mdata --do_verify=0 --runtime=5 --time_based  " \
            "--output-format=terse,normal "%(ReadWrite, device)     
        
    def DO_Script_Test(self, testScriptName, option=""):
        # ex. testScriptName = 'SMI_SmartHealthLog.py'
        for device in self.AllDevices:            
            self.Print("") 
            self.Print("python %s %s"%(testScriptName, device) )
            self.Print("")
            # ex. Log/sublog/devnvme0n1/SMI_SmartHealthLog/
            logPath=self.LogPath + "sublog/%s/%s"%(device.replace("/",""), testScriptName.replace(".py",""))
            # run script
            rtCode, FailCaseNum = self.RunSMIScript(scriptName= testScriptName, DevAndArgs= "%s %s"%(device, option), LogPath = logPath)
            sleep(0.5)
            if rtCode!=0:
                self.Print("")
                self.Print("Fail, detail consol output log at: %s"%logPath , "f") 
                self.Print("Below is the fail cases that console output from %s"%testScriptName)
                self.Print("")
                self.Print("-------------------------------------------------------------------------", "f")    
                for caseNum in FailCaseNum:
                    self.PrintSMIScriptConsoleOutput(LogPath = logPath, SubCase=caseNum)    
                self.Print("-------------------------------------------------------------------------", "f")       
                self.Print("")
                return False
        return True      
        
    def GetVFListCreatedByPF(self):
    # e.x. mList=[/dev/nvme1n1 , /dev/nvme2n1 ]
        mList=[]
        
        PFPort = self.GetPciePort(self.dev)
        # if created VF is nvme1n1 nvme2n1 ...
        if PFPort.find("nvme-subsys")==-1: 
            PF_PciePort=self.pcie_port
            # 0000:02:00.0, bus=0000, dev=02, func=00.0
            # get device bus and device number, remove function number
            PF_BusDeviceNum = PF_PciePort[:-5]
            # get nvme list all devices
            NvmeList=self.GetCurrentNvmeList()
            for device in NvmeList:
                Port = self.GetPciePort(device)                            
                BusDeviceNum = Port[:-5]
                # if not PF device and (bus and device num) is the same, than it is VF from PF
                if PF_BusDeviceNum==BusDeviceNum and device!=self.dev:
                    mList.append(device)           
        # if created VF is nvme0n1 nvme0n2 ...
        else:     
            # get nvme list all devices
            NvmeList=self.GetCurrentNvmeList()
            for device in NvmeList:
                Port = self.GetPciePort(device)  
                # if Port = nvme-subsys0 and not PF
                if Port == PFPort and device!=self.dev:
                    mList.append(device) 
        return mList
    
    def DoVM_FIOtest_Simultaneously(self, targetDevice, rw, numDUT=None, sleepTime=5, TrimAllBeforeTest=False):
    # targetDevice: "SRIOV" or "RawDisk"
    # rw : r or w
    # numDUT, ex. if there are 4 VMs and you need to test 3 VMs only, then set numDUT=3
        if targetDevice=="SRIOV":
            dev="/dev/nvme0n1"
        elif targetDevice=="RawDisk":
            dev="/dev/vda"
        else:
            self.Print("Fail: func DoVM_FIOtest_Simultaneously, expect  targetDevice error!(%s)"%targetDevice)
            return False
        
        ReadWrite="write" if rw=="w" else "read"        
        self.Print("")
        self.Print("Using SSH to issue nvme commands to guest VMs")
        self.Print("Virtual machine FIO %s test, all VMs do FIO simultaneously(%s)"%(ReadWrite, targetDevice))
        mThreads = [] 
        #self.DoVM_FIOtest(self.VMinfo[0])        
            
        # set nVM, ex. if there are 4 VMs and you need to test 3 VMs only, then set numDUT=3
        nDUT=1000
        if numDUT!=None:
            if numDUT<=len(self.VMinfo):
                nDUT=numDUT

        if TrimAllBeforeTest:
            self.Print("Trim whole disk for all VF .. ") 
            for info in self.VMinfo:
            #for dev in self.AllDevices:
                IP=info.vmIpAddr
                FIO_CMD = "nvme dsm %s -s 0 -b %s -d 2>&1" % (dev, self.NUSE)              
                self.VM_shell_cmd(IP, FIO_CMD)  
            self.Print("Done")
  
        for info in self.VMinfo:            
            t = threading.Thread(target = self.DoVM_FIOtest, args=(info, dev, rw,))
            t.start() 
            mThreads.append(t) 
            nDUT = nDUT -1
            #sleep(1)# TODO0
            if nDUT==0:
                break
    
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
        sleep(sleepTime)    

    def DoTestSpeed(self, readWrite="write"):
        rtCode = True
        
        self.Print("Trim whole disk for all VF/PF .. ") 
        for dev in self.AllDevices:
            SubDUT = NVME([dev]) 
            SubDUT.TrimWholeDisk()   
            
            
            
            '''
            cmd = "blkdiscard %s"%dev
            self.Print(cmd)
            rtCode = self.shell_cmd(cmd)
            '''
        #rtCode = self.shell_cmd("fstrim -a -v")
        
        #self.Print(rtCode) 
        self.Print("Done")
        self.Print("")       
        
        
        
        
        
        # create SubDUT to use NVME object for specific device, e.x. /dev/nvme0n1,  note that argv is type list
        PF = self.AllDevices[0]
        SubDUT = NVME([PF])         
        NUSE=SubDUT.IdNs.NUSE.int        
        
        self.Print("NUSE: 0x%X"%NUSE) 
        totalByte = NUSE*512  
        
        mPattern = randint(1, 0xFF)
        if readWrite=="write":
            CMDtemp = "fio --direct=1 --iodepth=16 --ioengine=libaio --bs=64K --rw=%s --numjobs=1 "\
         "--offset=0 --name=mtest --do_verify=0 --verify=pattern --size=0x%X "\
        "--verify_pattern=%s"%(readWrite, totalByte, mPattern)
        else:
            CMDtemp = "fio --direct=1 --iodepth=16 --ioengine=libaio --bs=64K --rw=read --numjobs=1 "\
             "--offset=0 --name=mtest --do_verify=0 --size=0x%X " \
            %(totalByte)        
        
        # start to test PF
        CMD1 = CMDtemp + " --filename=%s"%(PF)
        self.Print("")        
        self.Print("Do FIO test for %s entire disk of %s, command as folowing"%(readWrite, PF))      
        self.Print(CMD1)
        
        CMD=[CMD1]
        FIOcmdWithPyPlot = self.FIOcmdWithPyPlot_(self)        
        averageBwList = FIOcmdWithPyPlot.RunFIOcmdWithConsoleOutAndPyplot(CMDlist = CMD, maxPlot=180, printInfo=False)
        self.Print("Finished")
        Did=0
        self.Print("%s: FIO bw= %sMiB/s"%(PF, averageBwList[Did]), "p")
        pfBW=averageBwList[Did]
        self.Print("PF bw= %sMiB/s"%(pfBW))
        sleep(5)      
        
        # start to test all VF at the same time
        self.Print("")
        self.Print("Trim all SSD.. ") 
        for dev in self.AllDevices:
            cmd = "blkdiscard %s"%dev
            self.Print(cmd)
            rtCode = self.shell_cmd(cmd)      
        
        self.Print("Do FIO test for %s entire disk of all VFs at the same time(Simultaneously), FIO commands as below"%readWrite)
        CMD=[]
        for dev in self.VFDevices:      
            CMD1 = CMDtemp + " --filename=%s"%(dev)  
            self.Print(CMD1) 
            CMD.append(CMD1)
            
        FIOcmdWithPyPlot = self.FIOcmdWithPyPlot_(self)        
        averageBwList = FIOcmdWithPyPlot.RunFIOcmdWithConsoleOutAndPyplot(CMDlist = CMD, maxPlot=180, printInfo=False)
        self.Print("Finished")
        sleep(5)
        Did=0
        for dev in self.VFDevices: 
            self.Print("%s: FIO bw= %sMiB/s"%(dev, averageBwList[Did]), "p")
            Did=Did+1
            
        self.Print("")        
        totalBW=sum(averageBwList)
        self.Print("Total bw for all FIO VF testing(VF0 + VF1 + VF2 ..): %s"%totalBW)
        self.Print("PF bw= %sMiB/s"%(pfBW))
        self.Print("Check if (total bw of VF) >= (0.8*PF bw)")
        if((pfBW*0.8)> totalBW):
            self.Print("Fail","f")
            rtCode=False
        else:
            self.Print("Pass","p")
                      
        self.Print("")        
        maxBW=max(averageBwList) 
        minBW=min(averageBwList) 
        self.Print("Min bw of VF=%s, Max bw of VF=%s"%(minBW, maxBW))
        self.Print("Check QOS(Quality of Service) for VFs")
        self.Print("Check if the VF is shared the throughput equally") 
        self.Print("e.g. (Min bw of VF)/(Max bw of VF) >=0.7) ")
        if(float(minBW/maxBW)<0.7 ):
            self.Print("Fail","f")
            rtCode=False
        else:
            self.Print("Pass","p")    
            rtCode=True    
        
        return rtCode
                
    def TestOSsleep(self, mode, wakeuptimer):
    # mode = S3, S4
        # enter sleep
        mTime=datetime.datetime.now()
        if mode=="S3":
            self.Print("Test S3 mode(Suspend To Ram) for SR-IOV device")
            # if user input wakeuptimer arg
            Timer = 10 if wakeuptimer==None else wakeuptimer
            self.Print("Set system enter S3 mode for % seconds, current time: %s"%(Timer, mTime))
            self.DoSystemEnterS3mode(Timer)
        elif mode=="S4":
            self.Print("Test S4 mode(Suspend To Disk) for SR-IOV device")
            Timer = 40 if wakeuptimer==None else wakeuptimer
            self.Print("Set system enter S4 mode for % seconds, current time: %s"%(Timer, mTime))
            self.DoSystemEnterS4mode(Timer)
        self.Print("")
        
        # wakeup from here
        mTime=datetime.datetime.now()
        self.Print("system exit sleep, current time: %s"%mTime)
        
        self.Print("Check if VFs is missing after wakeup")
        Missing = False
        for Dev in self.VFDevices:
            if self.isfileExist(Dev):
                self.Print("        Pass: %s, exist"%Dev, "p")  
            else:
                self.Print("        Fail: %s, missing"%Dev, "f")    
                Missing = True
        
        if Missing:                     
            self.Print("")
            self.Print("VFs is missing after wakeup, Reset SR-IOV and check if create VFs success")
            self.Print("Set all VF offline")
            if not self.SetCurrentNumOfVF(0):
                self.Print("Fail, quit all", "f"); return False
            self.Print("Do remove and rescan device")
            self.shell_cmd("  echo 1 > /sys/bus/pci/devices/%s/remove " %(self.pcie_port), 0.1) 
            self.shell_cmd("  echo 1 > /sys/bus/pci/rescan ", 0.1)  
            self.Print("Set all VF online (TotalVFs = %s)"%self.TotalVFs)            
            if not self.SetCurrentNumOfVF(self.TotalVFs):
                self.Print("Create VF Fail", "f"); return False         
                    
        return True             

    def ClearRebootTest(self, printInfo = False):
        fPath ="/etc/rc.d/rc.local"   
        
        # parse argv, script name is enought
        scriptName=sys.argv[0]
        
        # load file
        with open(fPath, 'r') as mfile:
            # read a list of lines into data
            data = mfile.read()
        if data==None:
            self.Print( "Can't find file: %s"%fPath, "f")
            sys.exit(1)                
        # find the line with 'sudo python  scriptName'  to the end, and replace to ""
        mStr="(\nsudo python %s .*\n)"%scriptName    
        if re.search(mStr, data):
            parameters = re.search(mStr, data).group(1)    
            data = data.replace(parameters, "")     
            # and write everything back
            with open(fPath, 'w') as mfile:
                mfile.writelines( data )

    def CreateCronShellScript(self, filePath, CMD):
        # create AutoRunAfterReboot.sh(filePath)
        # content
        # This function will create AutoRunAfterReboot.sh with following example strings
        '''
            #!/bin/sh
            # set display valuable
            export DISPLAY=:10.0
            # run command
            /bin/gnome-terminal --maximize -- bash -c 'cd /home/root/sam/eclipse/NVME; python SMI_SRIOV.py /dev/nvme0n1 14 -t -n 2 -c 0 -r 14; exec bash'
        '''
        data = "#!/bin/sh" + "\n"
        # set display valuable
        data = data + "# set display valuable" + "\n"
        DISPLAY = self.shell_cmd("echo $DISPLAY")
        data = data + "export DISPLAY=%s"%DISPLAY + "\n"
        data = data + "# run command" + "\n"
        TerminalLocation = self.shell_cmd("which gnome-terminal")
        data = data + "%s --maximize -- bash -c '%s; exec bash'\n"%(TerminalLocation, CMD) + "\n"
        data = data + "exit 0" + "\n"
        # write
        with open(filePath, 'w') as mfile:
            mfile.writelines( data ) 
        # change mod for excutable    
        self.shell_cmd("chmod +x %s"%filePath)    
               
    def SetRebootTest(self, currentLoop, resumeFromCaseNo, printInfo = False):
        # currentLoop: pass loop number for next reboot
        # resumeFromCaseNo: pass Case number for next reboot, after reboot , from case1 to resumeFromCaseNo-1 will not excute
        # remove
        mDir = os.path.dirname(os.path.realpath(__file__))
        fPath = mDir
        fPath = fPath + "/AutoRunAfterReboot.sh" # content  
        self.rmFile(fPath)      
        # create
        # parse argv
        itemAll=""
        for item in sys.argv:
            itemAll = "%s %s"%(itemAll, item)
        itemAll = itemAll.lstrip()

        # remove '-c \d' for current loop
        if re.search("(-c \d+)", itemAll):
            parameters = re.search("(-c \d+)", itemAll).group(1)      
            itemAll = itemAll.replace(parameters, "")
            
        # add '-c \d' for current loop    
        itemAll = "%s -c %s"%(itemAll, currentLoop)

        # add '-r \d' for resumeFromCaseNo if not find
        if not re.search("(-r \d+)", itemAll):  
            itemAll = "%s -r %s"%(itemAll, resumeFromCaseNo)
        
        '''
            if isCentos
                CMD='cd /home/root/sam/eclipse/NVME; python SMI_SRIOV.py /dev/nvme0n1 14 -t -n 2 -c 0 -r 14'
            if isUbuntu, using sudo to run python  for file AutoRunAfterReboot.sh
                CMD='cd /home/root/sam/eclipse/NVME; echo '%s' | sudo -S python SMI_SRIOV.py /dev/nvme0n1 14 -t -n 2 -c 0 -r 14 -acc sam -pw Smi888'            
            if isUbuntu, SMI_SRIOV.py must run with -acc and -pw to specify current user accout and pw for root privileges,  e.x. '-acc sam -pw Smi888'
        '''
        # if find 2.7, then using python2.7 to run command , else using default version     
        pythonVer = "2.7" if int(self.shell_cmd("which python2.7 >/dev/null 2>&1 ; echo $?"))==0 else ""
        if self.isCentOS:
            CMD="cd %s; python%s %s"%(mDir, pythonVer, itemAll)
        else:
            CMD="cd %s; echo '%s' | sudo -S python%s %s"%(mDir, self.UserPw, pythonVer, itemAll)         
        
        self.Print(CMD) if printInfo else None
                        
        self.CreateCronShellScript(fPath, CMD)
        
        # setting crontab, copy current environment to /etc/crontab as below content for centos
        '''
        SHELL=/usr/bin/bash
        PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin
        @reboot root sleep 20 && /home/root/sam/eclipse/NVME/AutoRunAfterReboot.sh
        '''
        # for Ubuntu
        '''
        @reboot 'useracc' sleep 20 && /home/root/sam/eclipse/NVME/AutoRunAfterReboot.sh
        '''
        
        mStr = self.shell_cmd("which bash")        
        data = "SHELL=%s"%mStr + "\n"   
        mStr = self.shell_cmd("echo $PATH")        
        data = data + "PATH=%s"%mStr + "\n" 
        if self.isCentOS:
            data = data + "@reboot root sleep 20 && %s"%fPath + "\n"
        else:
            data = data + "@reboot %s sleep 20 && %s"%(self.UserAcc, fPath) + "\n" 
        
        # and write everything back
        with open("/etc/crontab", 'w') as mfile:
            mfile.writelines( data )        
        
        
        
        '''
        fPath ="/etc/rc.d/rc.local"            
        self.Print("Setting %s for reboot test"%fPath)   
                 
        # clear old
        self.ClearRebootTest()
        
        # parse argv
        itemAll=""
        for item in sys.argv:
            itemAll = "%s %s"%(itemAll, item)
        itemAll = itemAll.lstrip()
        
        # remove '-c \d' for current loop
        if re.search("-c \d+", itemAll):
            parameters = re.search("-c \d+", itemAll).group(1)      
            itemAll = itemAll.replace(parameters, "")
            
        # add '-c \d' for current loop    
        itemAll = "%s -c %s"%(itemAll, currentLoop)
        
        mStr="sudo python %s"%itemAll
        self.Print("Add '%s' to %s"%(mStr, fPath)) if printInfo else None
            
        # load file
        with open(fPath, 'r') as mfile:
            # read a list of lines into data
            data = mfile.read()
        if data==None:
            self.Print( "Can't find file: %s"%fPath, "f")
            sys.exit(1)                
        # now add the line             
        if re.search(mStr, data):
            pass
        else:
            data = data +"\n%s\n"%mStr
        
        # and write everything back
        with open(fPath, 'w') as mfile:
            mfile.writelines( data )
        
        # change mod for excutable    
        self.shell_cmd("chmod +x %s"%fPath)    
        '''
        return True

    def Case10TestFunc(self, targetDevice, rw, OutCSVfullPath, testLoop, sleepTimeForEveryLoop, TrimAllBeforeTest=False):
    # targetDevice: SRIOV or RawDisk
    # rw: r/w
    # OutCSVfullPath: csv file name
    # testLoop: number of loops to be tested for testing 1 VF to all VF at the same time 
    # sleepTimeForEveryLoop: sleep seconds after every loop
    # TrimAllBeforeTest: trim disk before test, true/false
        if True:
            self.rmFile(OutCSVfullPath)
            # print header, ex. "Number of VF", "VM0 KB/s", "VM1 KB/s", "VM2 KB/s"
            totalVF = len(self.VMinfo)
            mData=[]
            mData.append("Number of VF")
            mData.extend("VM%s KB/s"%i for i in range(totalVF))
            self.WriteCSVFile(OutCSVfullPath, mData) 
            
            # for 1 VF to all VF
            for i in range(totalVF):
                nvf = i+1
                sleep(1)       
                # test testLoop times, ex. 10 times         
                for loop in range(testLoop):
                    self.FIOresultList=[]   # clear
                    self.Print("test for %sVF, loop: %s"%(nvf, loop)) 
                    self.DoVM_FIOtest_Simultaneously(targetDevice = targetDevice , rw=rw, numDUT=nvf, sleepTime=sleepTimeForEveryLoop, TrimAllBeforeTest=TrimAllBeforeTest)
                    # save to csv
                    SortedByName=[0 for s in range(nvf)]
                    for result in self.FIOresultList: #VMname, speedInKbyte
                        VMname=result[0]    # 'VM0'
                        speedInKbyte=result[1]
                        ID=VMname.replace("VM", "")
                        ID = int(ID)
                        SortedByName[ID]=speedInKbyte
                    # mData = current value of "Number of VF", "VM0 KB/s", "VM1 KB/s", "VM2 KB/s"
                    mData = []
                    mData.append(nvf)
                    mData.extend(SortedByName)
                    self.WriteCSVFile(OutCSVfullPath, mData)
                    # end of save to csv
                    self.Print("")         

    def DmesgBackup(self, dmesgFileNameLast, dmesgFileNameCurr):
        self.Print("Backup current dmesg to %s"%dmesgFileNameCurr)  
        # move to last
        if self.isfileExist(dmesgFileNameCurr):
            self.shell_cmd("mv %s %s"%(dmesgFileNameCurr, dmesgFileNameLast)) 
        # print timestamp
        timeStamp = self.PrefixString()
        self.shell_cmd("echo '%s' > %s"%(timeStamp, dmesgFileNameCurr))
        # print dmesg
        self.shell_cmd("dmesg >> %s"%(dmesgFileNameCurr))         
    
    def __init__(self, argv): 
        # initial new parser if need, -t -d -s -p was used, dont use it again
        self.SetDynamicArgs(optionName="n", optionNameFull="numofvf", helpMsg="number of VF that will be enable and test", argType=int) 
        self.SetDynamicArgs(optionName="l", optionNameFull="loops", helpMsg="number of loops for case11, case12 and case14", argType=int)
        self.SetDynamicArgs(optionName="w", optionNameFull="wakeuptimer", helpMsg="wakeup timer in seconds for case11, case12 and case14", argType=int)
        self.SetDynamicArgs(optionName="c", optionNameFull="CurrentLoopForResumeFromReboot", helpMsg="curren loop for resume from reboot, please do not set it", argType=int)
        self.SetDynamicArgs(optionName="acc", optionNameFull="CurrentUbuntuUserAccount", helpMsg="Current Ubuntu user account", argType=str)
        self.SetDynamicArgs(optionName="pw", optionNameFull="CurrentUbuntuUserPassword", helpMsg="Current Ubuntu user password", argType=str)
        self.SetDynamicArgs(optionName="v", optionNameFull="timerAfterReboot", helpMsg="waiting timer After Reboot, then run script for case14", argType=int) 
        
                
        # initial parent class
        super(SMI_SRIOV, self).__init__(argv)      
        
        # get new parser if need, where args order is the same with initial order
        # config_numvfs = int or None
        self.config_numvfs = self.GetDynamicArgs(0)  
        self.loops = self.GetDynamicArgs(1)  
        self.wakeuptimer = self.GetDynamicArgs(2)  # if no wakeuptimer arg in, wakeuptimer = None
        self.CurrentLoopForResumeFromReboot = int(self.GetDynamicArgs(3)  ) if self.GetDynamicArgs(3)!=None else None
        self.UserAcc = "" if self.GetDynamicArgs(4)==None else self.GetDynamicArgs(4)
        self.UserPw = "" if self.GetDynamicArgs(5)==None else self.GetDynamicArgs(5)
        self.timerAfterReboot = self.GetDynamicArgs(6)
        
        if self.timerAfterReboot!= None:
            self.Print("timerAfterReboot: %s, sleep for %s seconds"%(self.timerAfterReboot, self.timerAfterReboot))
            sleep(self.timerAfterReboot)    
            
        dmesgFileNameLast = "dmesgBeforeSRIOV_Last.txt"
        dmesgFileNameCurr = "dmesgBeforeSRIOV_Curr.txt"            
        self.DmesgBackup(dmesgFileNameLast, dmesgFileNameCurr)

        # set defalut loop =1   
        self.loops=1 if self.loops==None else self.loops
        
        # ResumeFromReboot, true/false
        self.ResumeFromReboot=True  if self.ResumeSubCase!=None else False
        # first run
        if not self.ResumeFromReboot==None and self.loops==0:
            self.Print("Error, loop must >=1","f")
            return 255
        
        #check OS is isCentOS or Ubuntu
        self.isCentOS = True if self.shell_cmd("cat /etc/os-release |grep 'CentOS' 2>&1 >/dev/null; echo $?")=="0" else False
        self.isUbuntu = True if self.shell_cmd("cat /etc/os-release |grep 'Ubuntu' 2>&1 >/dev/null; echo $?")=="0" else False
        
        # import module if installed, else yum install module 
        self.tkinter = self.ImportModuleWithAutoYumInstall("Tkinter", "sudo yum -y install tkinter python-tools")
        self.paramiko = self.ImportModuleWithAutoYumInstall("paramiko", None)        
        self.PyVersion=2 if sys.version_info[0] < 3 else 3
        self.matplotlib = self.ImportModuleWithAutoYumInstall("matplotlib", "sudo yum install -y python%s-matplotlib python-matplotlib"%self.PyVersion)
        
        # if tkinter imported, using GUI
        self.UsingGUI = True if self.tkinter!=None else False
        # if testmode, set false
        if self.mTestModeOn:
            self.UsingGUI=False        
        
        
        ''' using -n to set number of VF that will be enable and test instead of using config file
        # config file parameters
        self.config_numvfs=None
        #parse file
        self.Print("parse config file if exist..")
        if self.ParseConfigFile():
            self.Print("done")        
        else:
            self.Print("file not found")  
        '''     
        
        # change timeout
        if self.mTestTime!=None:
            SMI_SRIOV.SubCase1TimeOut = 200+self.mTestTime
        

        
        #self.UsingGUI=False
        self.CurrItems=[]   # ex. ["nvme0n1", Lb0], ["nvme1n1", Lb1]
        self.AvaItems=[]    # ex. ["nvme0n1", Lb0], ["nvme1n1", Lb1]
        self.root=None
                        
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
        
        # device lists, first is PF, others is VF, e.g [self.dev ] + self.VFDevices[]
        self.AllDevices=list(self.dev)
        self.VFDevices=[]
        # vf all off, nvme list
        self.VFoff_NvmeList=0
        # vf on, nvme list
        self.VFon_NvmeList=0
        
        # Mutex for multi thread, [device, TestItemID,scriptName, writeValue, rtPass]
        self.lock=threading.Lock()
        self.MutexThreadOut=[]
        self.IsPass=True
        
        # VM
        
        self.VMinfo=[]  # [ VMinfoClass, VMinfoClass ...]
        self.FIOresultList=[]
        self.NUSE = self.IdNs.NUSE.int # for trim whole disk
        
        
        # others
        self.Running=None
        
        
    # define pretest  
    def PreTest(self): 
        if self.mTestModeOn:
            self.Print("Test mode on")   

        if self.isCentOS:
            self.Print("OS: CentOS", "p")
        elif self.isUbuntu:
            self.Print("OS: Ubuntu", "p")
            if self.UserAcc=="" or self.UserPw=="":
                self.Print("For Ubuntu, please run python with current user account and password for root permission", "f")
                self.Print("E.g. python SMI_SRIOV ...(options) -acc='account' -pw='password'", "f")
                return False            
        else:
            self.Print("OS: unknow", "w")
        self.Print("")
        
        if self.Sysfs_SRIOV_Supported:
            self.Print("Linux's sysfs support SRIOV: Yes")
        else:
            self.Print("Linux's sysfs support SRIOV: No, quit all", "w"); return False
                    
        # get TotalVFs of SR-IOV Virtualization Extended Capabilities Register(PCIe Capabilities Registers)
        #self.TotalVFs = self.read_pcie(base = self.SR_IOVCAP, offset = 0x0E) + (self.read_pcie(base = self.SR_IOVCAP, offset = 0x0F)<<8)
        self.TotalVFs = int(self.shell_cmd("cat /sys/bus/pci/devices/%s/sriov_totalvfs"%self.pcie_port))
               
        self.Print("Check if TotalVFs of SR-IOV Virtualization Extended Capabilities Register(PCIe Capabilities Registers) is large then 0(SR-IOV supported)") 
        self.Print("TotalVFs: %s"%self.TotalVFs)
        if self.TotalVFs>0:
            self.Print("PCIe device support SR-IOV", "p")
        else:
            self.Print("PCIe device do not support SR-IOV, quit all", "w"); return False  
            
        # if user define test number of VF 
        if self.config_numvfs!=None:
            self.TotalVFs=self.config_numvfs
            
        self.Print("")
        self.Print("SR-IOV test number of VF : %s"%self.TotalVFs)

        
        '''    
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
        '''
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
                       
        
        self.Print("")
        nmuvfs = self.GetCurrentNumOfVF()
        self.Print("Current Num Of VF: %s"%nmuvfs, "p")   
        
        
        # if (not test mode), or (is test mode and current nmuvfs!=self.TotalVFs), do Set all VF offline
        if not self.mTestModeOn or nmuvfs!=int(self.TotalVFs):
            # reset VF 
            if nmuvfs!=0:
                self.Print("")
                self.Print("Set all VF offline")
                if not self.SetCurrentNumOfVF(0):
                    self.Print("Fail, quit all", "f"); return False  
            
        
        # if VF=0, enable all            
        nmuvfs = self.GetCurrentNumOfVF()        
        if nmuvfs==0:
            # enable all VF        
            self.Print("") 
            self.Print("Set all VF online (TotalVFs = %s)"%self.TotalVFs)
            if not self.SetCurrentNumOfVF(self.TotalVFs):
                self.Print("Create VF Fail, quit all", "f"); return False  
        else:         
        # else get AllDevices list
            # get VF list
            self.VFDevices = self.GetVFListCreatedByPF()
            # save to AllDevices
            self.AllDevices = [self.dev] + self.VFDevices
            self.Print("")
            self.Print("Created VF drive:")
            for Dev in self.VFDevices:
                self.Print("        %s"%Dev)                        
                                     
 
        # backup os nvme list            
        self.VFoff_NvmeList=self.GetCurrentNvmeList()
                
        self.Print("")            
        
        return True            
    
    # <define sub item scripts>
    SubCase1TimeOut = 1800
    SubCase1Desc = "Test if the operation of PF and VFs influences itself only"   
    SubCase1KeyWord = ""
    def SubCase1(self):
        ret_code=0       
                                                       
       
        # test all test item in all VF and can't interfere with each other
        #specificVF = self.AllDevices[1]
        #self.Print("Test when having testing in all VF, the testings can't interfere with each other")
        self.Print("")
        timeout=self.mTestTime if self.mTestTime!=None else 60
        self.Print(" Test if the operation of PF and VFs influences its controller only, timeout : %s sceond"%self.mTestTime)
        if not self.MultiThreadTest(timeout): return 1 
        
        self.Print("Done!")
        
        return ret_code

    
    SubCase2TimeOut = 1800
    SubCase2Desc = "Test Data Integrity of POR and SPOR"   
    SubCase2KeyWord = ""
    def SubCase2(self):    
        #if self.mTestModeOn:
        
        if True:
            self.Print("skip sub case")
            return 255

        # test all test item in all VF and can't interfere with each other
        #specificVF = self.AllDevices[1]
        #self.Print("Test when having testing in all VF, the testings can't interfere with each other")
        self.Print("")
        dataPattern_List=[]
        self.Print(" Write data to PF and all VFs: %s"%self.AllDevices)
        for device in self.AllDevices:
            dataPattern=randint(1, 0xFF)    
            dataPattern_List.append(dataPattern)     
            SubDUT = NVME([device])  
            SubDUT.fio_write(offset=0, size="10M", pattern=dataPattern, fio_direct=0)
            if not SubDUT.fio_isequal(offset=0, size="10M", pattern=dataPattern, fio_direct=0):
                self.Print("Fail!, FIO write data to %s with pattern %s fail, quit test", "f")
                return 0
        self.Print("Done")
        
        self.Print("")
        self.Print("Power off device and then power on..")
        self.por_reset()
        sleep(1)
        self.Print("Done")   
        
        self.Print("Check if VFs is missing after wakeup")
        Missing = False
        for Dev in self.VFDevices:
            if self.isfileExist(Dev):
                self.Print("        Pass: %s, exist"%Dev, "p")  
            else:
                self.Print("        Fail: %s, missing"%Dev, "f")    
                Missing = True
        
        if Missing:                     
            self.Print("")
            self.Print("VFs is missing after wakeup, Reset SR-IOV and check if create VFs success")
            self.Print("Set all VF offline")
            if not self.SetCurrentNumOfVF(0):
                self.Print("Fail, quit all", "f"); return 1
            self.Print("Do remove and rescan device")
            self.shell_cmd("  echo 1 > /sys/bus/pci/devices/%s/remove " %(self.pcie_port), 0.1) 
            self.shell_cmd("  echo 1 > /sys/bus/pci/rescan ", 0.1)  
            self.Print("Set all VF online (TotalVFs = %s)"%self.TotalVFs)            
            if not self.SetCurrentNumOfVF(self.TotalVFs):
                self.Print("Create VF Fail", "f"); return 1         

        self.Print("")            
        self.Print("Check data petterns in all VF and PF") 
        cnt=0
        for device in range(len(self.AllDevices)):
            dataPattern = dataPattern_List[cnt]
            if not SubDUT.fio_isequal(offset=0, size="10M", pattern=dataPattern, fio_direct=0):
                self.Print("Fail!, data changed, expect pattern = %s"%dataPattern, "f")
                self.Print("hexdump data blow ..", "f")
                CMD = "hexdump %s -n 512 -C"%SubDUT.dev
                for line in self.yield_shell_cmd(CMD):
                    self.Print( line)                
                self.Print("")   
                self.Print("quit", "f") 
                return 1  
            
        self.Print("Pass", "p")
        
        return 0

    SubCase3TimeOut = 7200
    SubCase3Desc = "Test NVMe write speed"   
    SubCase3KeyWord = ""
    def SubCase3(self):
        # note: using TotalVFs to decide the number of VM
        ret_code=0   
        
        if self.matplotlib==None:
            self.Print("matplotlib not installed!, quit test!", "f")
            return 255            
        
        self.Print("")
        self.Print("-- Start to test write speed ----------------------------")
        if not  self.DoTestSpeed("write"): return 1

        self.Print("Done!")         
        self.Print("") 
        return ret_code

        '''
        
        self.Print("Devices do FIO test  ")        
        self.Print("")
        HostFIOoutList=self.DoHostStandaloneAllDeviceFIOtest()                 
            
            
        self.Print("")                 
        # do FIO simultaneously test, start from first two nvme device, e.x.  ["/dev/nvme0n1"] and  ["/dev/nvme1n1"] 
        for num in range(1, len(self.AllDevices)):
            deviceList=self.AllDevices[:num+1]  
            self.Print("Do FIO simultaneously write test for %s"%deviceList)               
            HostFIOsimuOutList = self.DoHostSimultaneouslyFIOtest(deviceList)
            if not self.DoSpeedCompare(deviceList, HostFIOoutList, HostFIOsimuOutList): ret_code=1
            self.Print("")
        
        
       ''' 


    SubCase4TimeOut = 7200
    SubCase4Desc = "Test NVMe read speed"   
    SubCase4KeyWord = ""
    def SubCase4(self):
        # note: using TotalVFs to decide the number of VM
        ret_code=0   
        
        if self.matplotlib==None:
            self.Print("matplotlib not installed!, quit test!", "f")
            return 255            
        
        self.Print("")
        self.Print("-- Start to test read speed ----------------------------")
        if not self.DoTestSpeed("read"): return 1

        self.Print("Done!")         
        self.Print("") 
        return ret_code


                
    SubCase5TimeOut = 1800
    SubCase5Desc = "Test SMI_SmartHealthLog.py for all VF/PF"   
    SubCase5KeyWord = ""
    def SubCase5(self):             
        ret_code=0   
        

        self.Print("test SMART / Health Information")
        testScriptName= "SMI_SmartHealthLog.py"
        #testScriptName= "mtest.py"
        ret_code = 0 if self.DO_Script_Test(testScriptName, " 1,2,3,4,5,6,7,8 ") else 1
                      
        return ret_code
    
    SubCase6TimeOut = 1800
    SubCase6Desc = "Test SMI_SetGetFeatureCmd.py for all VF/PF"   
    SubCase6KeyWord = ""
    def SubCase6(self):             
        ret_code=0          
        self.Print("test SMI_SetGetFeatureCmd")
        #testScriptName= "SMI_SmartHealthLog.py"
        testScriptName= "SMI_SetGetFeatureCmd.py"
        #  with option disable pwr,  '--disablepwr=1'
        #  with option disableNsTest,  '--disableNsTest=1'
        ret_code = 0 if self.DO_Script_Test(testScriptName, "--disablepwr=1 --disableNsTest=1 ") else 1
                      
        return ret_code    
    
    
    SubCase7TimeOut = 1800
    SubCase7Desc = "Test SMI_Read.py for all VF/PF"   
    SubCase7KeyWord = ""
    def SubCase7(self):             
        ret_code=0   
        self.Print("test SMI_Read")
        testScriptName= "SMI_Read.py"
        ret_code = 0 if self.DO_Script_Test(testScriptName) else 1                      
        return ret_code

    SubCase8TimeOut = 1800
    SubCase8Desc = "Test SMI_Write.py for all VF/PF"   
    SubCase8KeyWord = ""
    def SubCase8(self):             
        ret_code=0   
        self.Print("test SMI_Write")
        testScriptName= "SMI_Write.py"
        ret_code = 0 if self.DO_Script_Test(testScriptName) else 1                      
        return ret_code    
    
    SubCase9TimeOut = 1800
    SubCase9Desc = "Test SMI_DSM.py for all VF/PF"   
    SubCase9KeyWord = ""
    def SubCase9(self):             
        ret_code=0   
        self.Print("test SMI_DSM")
        testScriptName= "SMI_DSM.py"        
        #  with option disableNsTest,  '--disableNsTest=1'
        ret_code = 0 if self.DO_Script_Test(testScriptName, "--disableNsTest=1 ") else 1                          
        return ret_code    
             
    

    SubCase10TimeOut = 6000
    SubCase10Desc = "Test SR-IOV in virtual machines(KVM/QEMU)"   
    SubCase10KeyWord = ""
    def SubCase10(self):
        # note: using TotalVFs to decide the number of VM
        ret_code=0   
        
        
        #if self.mTestModeOn: snchan
        '''
        if True:
            self.Print("skip sub case")
            return 255  
        '''    
        
        if self.paramiko==None:
            self.Print("paramiko not installed!, quit test!", "f")
            return 255
        
        self.Print("Check if kernel boot parameter intel_iommu=on at boot option(/etc/default/grub)")      
        #if self.shell_cmd("dmesg | grep IOM 2>&1 >/dev/null; echo $?") =="0":
        if self.shell_cmd("find /sys | grep dmar 2>&1 >/dev/null; echo $?") =="0":
            self.Print("Pass!", "p")
        else:
            self.Print("intel_iommu=off, quit", "p")
            return 255
        
        self.Print("")  
        self.Print("Check if tools was installed")
        if not self.isCMDExist("virsh"):
            self.Print("Cant find virsh, please install libvirt before test, quit")
            return 255
        else:
            self.Print("Pass!", "p")

        # snchan TODO1
        sleepT = 2
        SecondRun=False
        
        f_TrimAll = False#True
        f_CreateVM = True        
        f_GetVM_IP = True   # must have  
        f_OpenTerminal = False              

        f_HostFIOtest = False   #
        f_AttachPCIE = True     # better have

        f_FormatPFtoExt4=True#True
        f_MountPF=True#True
        f_CreateRawDiskImg = True#True
        f_AttachRawDisk = True#True
        RT1 = True

        testLoop=1
        f_VM_FIO_WriteTestSimultaneously = True
        f_VM_FIO_WriteTestSimultaneouslyRawDisk = False
        f_VM_FIO_ReadTestSimultaneously = False
        f_VM_FIO_ReadTestSimultaneouslyRawDisk = False
        
        f_DettachRawDisk=False
        f_UmountPF=False
        f_DetachPCIE =True   # better have or you can't find VF at next round test
        
        if SecondRun:
            f_TrimAll=False
            f_CreateVM=False
            f_FormatPFtoExt4=False
            f_MountPF=False
            f_CreateRawDiskImg=False
            f_AttachRawDisk=False
        # start ------------------------------------------------------------------------------    
        if f_TrimAll:
            self.Print("Trim whole disk for all VF/PF .. ") 
            for dev in self.AllDevices:
                SubDUT = NVME([dev]) 
                SubDUT.TrimWholeDisk()           
        
        
        # init VMinfo and VMname
        for i in range(self.TotalVFs):    
            info = self.VMinfoClass()
            info.vmName="VM%s"%i
            self.VMinfo.append(info)        
        
        if f_CreateVM:    
            self.Print("")        
            self.Print("Create virtual machines VM0 to VM%s"%(self.TotalVFs-1)) 
            CPUset=1
            RAM=1024       
            for info in self.VMinfo:
                name = info.vmName
                if not self.CreateVM(name, CPUset, RAM):
                    self.Print("Fail to create %s"%name)
                    return 1     
                else:
                    self.Print("%s was created, attach to CPU%s, RAM = %s"%(name, CPUset, RAM))   
                    CPUset=CPUset+1            
            self.Print("Done")

        # get VF list
        self.VFDevices = self.GetVFListCreatedByPF()    
        # save to AllDevices
        self.AllDevices = [self.dev] + self.VFDevices                

        if f_GetVM_IP:
            self.Print("")
            timeout=60
            self.Print("Get IP address of all VMs for ssh connection, timeout %s s"%timeout)
            for info in self.VMinfo:
                name = info.vmName
                IP = self.GetVM_IPaddr(name, timeout)
                if IP==None:
                    self.Print("Fail to get ip address : %s"%(name))
                    return 1
                self.Print("%s : %s"%(name, IP))
                info.vmIpAddr=IP
                
        sleep(2)
        if f_OpenTerminal: 
            self.Print("")       
            for info in self.VMinfo:
                name = info.vmName
                IP          = info.vmIpAddr
                self.Print("Open Terminal for %s : %s"%(name, IP))
                self.shell_cmd("/bin/gnome-terminal --maximize -- bash -c 'sshpass -p 'Smi888' ssh -o StrictHostKeyChecking=no %s; exec bash'"%(IP))
            
        if f_HostFIOtest:  
            self.Print("")
            self.Print("Host FIO write speed test")   
            self.Print("--------------------------------------")     
            for device in self.VFDevices:
                SubDUT = NVME([device])
                FIO_CMD = self.FIO_CMD(device)
                self.Print(FIO_CMD)   
                mStr = SubDUT.shell_cmd(FIO_CMD)
                speedInKbyte = self.GetFIO_Speed(mStr)
                if speedInKbyte==None:
                    self.Print("FIO fail", "f")
                    return 1
                else:
                    self.Print("FIO write %s: bw=%s MB/s"%(device, speedInKbyte/1024), "f")
            self.Print("--------------------------------------") 
        
        if f_AttachPCIE:      
            self.Print("")     
            self.Print("Create XML files for Attach/Detach PCIE to VM")
            # create xml file for attach/detach command
            VM_xml_list = self.CreateXMLforAttachDetachPCIE()        
            # check if VMname =  xml file for attach/detach command
            if len(self.VMinfo)!=len(VM_xml_list)  :
                self.Print("Number of VM(%s) != number of XML files(%s)"%(len(self.VMinfo), len(VM_xml_list)), "f")
                return 1
            else:
                # copy to VMinfo
                for i in range(len(self.VMinfo)):
                    info=self.VMinfo[i];
                    info.vmHostNVMEname=VM_xml_list[i][0]
                    info.vmXmlFilePCIE=VM_xml_list[i][1]
                    info.vmPciePort=VM_xml_list[i][2]
                self.Print("Done")
            
            
            self.Print("")
            self.Print("Attach all SR-IOV PCIE device to guest VMs")
            for info in self.VMinfo:
                VMname = info.vmName
                PCIEport = info.vmPciePort
                XMLfile = info.vmXmlFilePCIE
                NVMEname= info.vmHostNVMEname
                self.Print("Attach PCIe %s(%s) to %s"%(PCIEport, NVMEname, VMname))
                self.AttachDeviceToVM(VMname, XMLfile)
        
        if f_FormatPFtoExt4:
            self.Print("")     
            self.Print("Format PF to Ext4 format ")                
            self.FormatPFtoExt4()
                
        if f_MountPF:    
            self.Print("")     
            self.Print("Mount PF to /SRIOV_Resources/MntPF ")              
            self.MountPF()
            sleep(1)

        if f_CreateRawDiskImg:
            self.Print("")     
            self.Print("Create Raw Disk Img on /SRIOV_Resources/MntPF")  
            self.CreateRawDiskImg(numOfDisk=len(self.VMinfo), DiskSize="2G")

        if f_AttachRawDisk:      
            self.Print("")     
            self.Print("Create XML files for Attach/Detach RawDisk(located in VF) to VM")
            # create xml file for attach/detach command
            VM_xml_list = self.CreateXMLforAttachDetachRawDisk()        
            # check if VMname =  xml file for attach/detach command
            if len(self.VMinfo)!=len(VM_xml_list)  :
                self.Print("Number of VM(%s) != number of XML files(%s)"%(len(self.VMinfo), len(VM_xml_list)), "f")
                return 1
            else:
                # copy to VMinfo
                for i in range(len(self.VMinfo)):
                    info=self.VMinfo[i];
                    info.vmXmlFileRawDisk=VM_xml_list[i]
                self.Print("Done")            
            self.Print("")
            self.Print("Attach all RawDisk(located in VF) to guest VMs")
            for info in self.VMinfo:
                VMname = info.vmName
                XMLfile = info.vmXmlFileRawDisk
                self.Print("Attach raw disk %s to %s"%( XMLfile, VMname))
                self.AttachDeviceToVM(VMname, XMLfile)

        if RT1:
            return 0
        sleep(2)
        if f_VM_FIO_WriteTestSimultaneously:
            self.Print("")
            OutCSVfullPath = "./CSV/Out/SRIOV_Case10_WriteTestSimultaneously.csv"   
            self.Case10TestFunc(targetDevice="SRIOV", rw="w", OutCSVfullPath=OutCSVfullPath, testLoop=testLoop, \
                                sleepTimeForEveryLoop=sleepT, TrimAllBeforeTest=True)
       
        if f_VM_FIO_WriteTestSimultaneouslyRawDisk:
            self.Print("")
            OutCSVfullPath = "./CSV/Out/SRIOV_Case10_WriteTestSimultaneouslyRawDisk.csv"   
            self.Case10TestFunc(targetDevice="RawDisk", rw="w", OutCSVfullPath=OutCSVfullPath, testLoop=testLoop, \
                                sleepTimeForEveryLoop=sleepT, TrimAllBeforeTest=True)            
   

        #--------------------------------------------------------------        
        if f_VM_FIO_ReadTestSimultaneously:
            self.Print("")
            OutCSVfullPath = "./CSV/Out/SRIOV_Case10_ReadTestSimultaneously.csv"   
            self.Case10TestFunc(targetDevice="SRIOV", rw="r", OutCSVfullPath=OutCSVfullPath, testLoop=testLoop, \
                                sleepTimeForEveryLoop=sleepT, TrimAllBeforeTest=True)
      
        if f_VM_FIO_ReadTestSimultaneouslyRawDisk:
            self.Print("")
            OutCSVfullPath = "./CSV/Out/SRIOV_Case10_ReadTestSimultaneouslyRawDisk.csv"   
            self.Case10TestFunc(targetDevice="RawDisk", rw="r", OutCSVfullPath=OutCSVfullPath, testLoop=testLoop, \
                                sleepTimeForEveryLoop=sleepT, TrimAllBeforeTest=True)            
   
        '''
        for i in range(4):
            nvf = i+1
            sleep(1)
            self.Print("test for %sVF"%nvf) 
            #self.DoVM_FIOtest_Simultaneously(targetDevice = "SRIOV" , rw="r", numDUT=nvf)
            self.DoVM_FIOtest_Simultaneously(targetDevice = "SRIOV" , rw="w", numDUT=nvf)     
            #self.DoVM_FIOtest_Simultaneously(targetDevice = "RawDisk" , rw="r", numDUT=nvf)
            self.Print("") 
        '''

        
        

        if f_DettachRawDisk:     
            self.Print("")     
            self.Print("Create XML files for Attach/Detach RawDisk(located in VF) to VM")
            # create xml file for attach/detach command
            VM_xml_list = self.CreateXMLforAttachDetachRawDisk()        
            # check if VMname =  xml file for attach/detach command
            if len(self.VMinfo)!=len(VM_xml_list)  :
                self.Print("Number of VM(%s) != number of XML files(%s)"%(len(self.VMinfo), len(VM_xml_list)), "f")
                return 1
            else:
                # copy to VMinfo
                for i in range(len(self.VMinfo)):
                    info=self.VMinfo[i];
                    info.vmXmlFileRawDisk=VM_xml_list[i]
                self.Print("Done")            
            self.Print("")
            self.Print("Detach all RawDisk(located in VF) to guest VMs")
            for info in self.VMinfo:
                VMname = info.vmName
                XMLfile = info.vmXmlFileRawDisk
                self.Print("Detach raw disk %s to %s"%( XMLfile, VMname))
                self.DetachDeviceToVM(VMname, XMLfile)                   
            
        sleep(2)    
        if f_UmountPF:    
            # umount PF
            self.shell_cmd("sudo umount SRIOV_Resources/MntPF 2>&1 >/dev/null")            

        if f_DetachPCIE:      
            self.Print("")     
            self.Print("Get XML files for Attach/Detach PCIE to VM")
            # create xml file for attach/detach command
            VM_xml_list = self.GetCurrentXMLforAttachDetachPCIE()        
            # check if VMname =  xml file for attach/detach command
            if len(self.VMinfo)!=len(VM_xml_list)  :
                self.Print("Number of VM(%s) != number of XML files(%s)"%(len(self.VMinfo), len(VM_xml_list)), "f")
                return 1
            else:
                # copy to VMinfo
                for i in range(len(self.VMinfo)):
                    info=self.VMinfo[i];
                    for j in range(len(VM_xml_list)):
                        if info.vmName == VM_xml_list[j][3]:
                            info.vmHostNVMEname=VM_xml_list[i][0]
                            info.vmXmlFilePCIE=VM_xml_list[i][1]
                            info.vmPciePort=VM_xml_list[i][2]
                self.Print("Done")
            
            
            self.Print("")
            self.Print("Detach all SR-IOV PCIE device to guest VMs")
            for info in self.VMinfo:
                VMname = info.vmName
                PCIEport = info.vmPciePort
                XMLfile = info.vmXmlFilePCIE
                NVMEname= info.vmHostNVMEname
                self.Print("Detach PCIe %s(%s) to %s"%(PCIEport, NVMEname, VMname))
                self.DetachDeviceToVM(VMname, XMLfile)

            
        self.Print("")
        self.Print("")
        self.Print("")


        return ret_code
        

 

    SubCase11TimeOut = 1800
    SubCase11Desc = "Test S3 mode(Suspend To Ram) for SR-IOV device"   
    SubCase11KeyWord = ""
    def SubCase11(self):             
        ret_code=0
        for i in range(self.loops):
            self.Print("")
            self.Print("Loop: %s start"%i)            
            if not self.TestOSsleep("S3", self.wakeuptimer):
                ret_code=1
                break
            waitT=10
            self.Print("Loop: %s finish, wait %s s"%(i, waitT))   
            sleep(waitT)
            
        return ret_code           
    
    
    SubCase12TimeOut = 1800
    SubCase12Desc = "Test S4 mode(Suspend To Disk) for SR-IOV device"   
    SubCase12KeyWord = ""
    def SubCase12(self):             
        ret_code=0
        for i in range(self.loops):
            self.Print("")
            self.Print("Loop: %s start"%i)
            if not self.TestOSsleep("S4", self.wakeuptimer):
                ret_code=1
                break
            waitT=10
            self.Print("Loop: %s finish, wait %s s"%(i, waitT))   
            sleep(waitT)
        return ret_code   

    SubCase1TimeOut = 1800
    SubCase13Desc = "Test namespaces attach/delete/create operation"   
    SubCase13KeyWord = ""
    def SubCase13(self):             
        ret_code=0
        self.Print("Skip namespaces test")
        return 255
        
        
        TNVMCAP=self.IdCtrl.TNVMCAP.int
        TotalBlocks=TNVMCAP/512
        self.Print("TNVMCAP: 0x%X"%TNVMCAP) 
        self.Print("Total Blocks: 0x%X"%TotalBlocks)
        
        # init subdut
        SubDUTList=[]
        for dev in self.AllDevices:
            SubDUT = NVME([dev])      
            SubDUTList.append([SubDUT, SubDUT.initial_NSID])
        
        # sort order by initial_NSID and get SubDUT(remove initial_NSID)
        SubDUTList.sort(key=lambda x: x[1])
        SubDUTList=[row[0] for row in SubDUTList]
        
        self.Print("") 
        self.Print("Current namespaces info.") 
        for DUT in SubDUTList:
            Name = DUT.device
            NSID = DUT.initial_NSID
            NCAP = DUT.IdNs.NCAP.int
            CNTLID=DUT.IdCtrl.CNTLID.int
            self.Print("Device: %s, nsid: %s, CNTLID: %s, NCAP: %s"%(Name, NSID, CNTLID, NCAP)) 
        
        self.Print("") 
        CMD = "nvme delete-ns %s -n 0xffffffff"%self.device_port
        self.Print("Try to delete all ns(%s)"%CMD) 
        self.shell_cmd(CMD)
        self.Print("Check if NCAP=0 in all VF/PF")
        for DUT in SubDUTList:
            Name = DUT.device
            NCAP = DUT.IdNs.NCAP.int
            CNTLID=DUT.IdCtrl.CNTLID.int
            if NCAP != 0:
                self.Print("Device: %s, CNTLID: %s, NCAP: %s"%(Name, CNTLID, NCAP), "f")
                ret_code=1
            else:
                self.Print("Device: %s, CNTLID: %s, NCAP: %s"%(Name, CNTLID, NCAP), "p")
                
        if ret_code!=0:
            self.Print("Fail, skip", "f"); return ret_code
        else:
            self.Print("Pass", "p")
        
        self.Print("")
        self.Print("Try to create ns and attach to controller..")
        nsid = 1
        for DUT in SubDUTList:
            Name = DUT.device
            NSID = DUT.initial_NSID
            CNTLID=DUT.IdCtrl.CNTLID.int      
            numOfBlock = 0x100000 * nsid  
        

            self.Print("Create nsid=%s, number of block=0x%X, and attach to CNTLID= %s(%s)"%(nsid, numOfBlock, CNTLID, Name))
            # create ns
            CMD = "  nvme create-ns %s -s %s -c %s " %(self.dev_port, numOfBlock, numOfBlock)
            self.Print(CMD)
            self.shell_cmd(CMD)            
            # attach    
            CMD = "  nvme attach-ns %s -n %s -c %s " %(self.dev_port,nsid, CNTLID)
            self.Print(CMD)
            self.shell_cmd(CMD)
            # verify    
            NCAP = DUT.IdNs.NCAP.int
            self.Print("  current NCAP: 0x%X, expect value: 0x%X"%(NCAP, numOfBlock))
            if NCAP==numOfBlock:
                self.Print("  Pass", "p")
            else:
                self.Print("  Fail", "f")
                ret_code = 1
                return ret_code
            nsid = nsid+1
            self.Print("")
            
        self.Print("")    
        self.Print("Issue 'nvme list'")
        for line in self.yield_shell_cmd("nvme list"):
            self.Print(line)
        
        self.Print("")
        self.Print("Finish, try to reset ns ..")            
        CMD = "nvme delete-ns %s -n 0xffffffff"%self.device_port
        self.shell_cmd(CMD)   
        nsid = 1     
        for DUT in SubDUTList:
            Name = DUT.device
            CNTLID=DUT.IdCtrl.CNTLID.int      
            numOfBlock = TotalBlocks/5              
            CMD = "  nvme create-ns %s -s %s -c %s 2>&1 >/dev/null " %(self.dev_port, numOfBlock, numOfBlock)
            self.Print(CMD)
            self.shell_cmd(CMD)            
            # attach    
            CMD = "  nvme attach-ns %s -n %s -c %s 2>&1 >/dev/null " %(self.dev_port,nsid, CNTLID)
            self.Print(CMD)
            self.shell_cmd(CMD)   
            nsid = nsid+1        
        self.Print("Done")            
        self.Print("")    
        self.Print("Issue 'nvme list'")
        for line in self.yield_shell_cmd("nvme list"):
            self.Print(line)        
        
        
                
        return ret_code  
        
    
    SubCase14TimeOut = 1800
    SubCase14Desc = "Test system reboot for SR-IOV device"   
    SubCase14KeyWord = ""
    def SubCase14(self):             
        ret_code=0
        
        # if first run for the scrip, loop=1
        if not self.ResumeFromReboot:        
            self.CurrentLoopForResumeFromReboot = 0
        else:
            self.CurrentLoopForResumeFromReboot=self.CurrentLoopForResumeFromReboot+1
            
        self.Print("Current Loop: %s, Total loop: %s"%(self.CurrentLoopForResumeFromReboot, self.loops))
        
        
        # if last loop then finish
        if self.CurrentLoopForResumeFromReboot>=self.loops:
            self.Print("Finish")
            self.Print("Clear crontab job and quit test case")
            self.shell_cmd("echo "" > /etc/crontab")            
            return 0
        else:
            
            self.SetRebootTest(currentLoop = self.CurrentLoopForResumeFromReboot, resumeFromCaseNo=14, printInfo = False)   
            try:
                # flush all console messages, below syntax will call NVMECom.tee.flush()      
                sys.stdout.flush()
                sleepT = 10 if self.wakeuptimer==None else self.wakeuptimer
                self.Print("Wait %s seconds and reboot .. , if detect 'ctrl+C' then skip this case"%sleepT)
                for i in range(sleepT+1):
                    # PrintProgressBar
                    self.PrintProgressBar(i, sleepT, prefix = 'Time:', length = 20)                    
                    sleep(1)
                self.Print("Start to reboot..")    
                self.FlushConsoleMsg()
                sleep(0.5)
                os.system('reboot')
            except KeyboardInterrupt:
                self.Print("")
                self.Print("Detect ctrl+C, clear crontab job and quit test case")
                self.shell_cmd("echo "" > /etc/crontab")

        return ret_code   

    SubCase15TimeOut = 1800
    SubCase15Desc = "Test FLR(function level reset) fucntion for all VF/PF"   
    SubCase15KeyWord = ""
    def SubCase15(self):             
        ret_code=0
        isPF=True
        for Dev in self.AllDevices:
            # first is PF, others are VF
            self.Print("test FLR for %s: %s"%("PF" if isPF else "VF", Dev))
            # create SubDUT to use NVME object for specific device, e.x. /dev/nvme2n1, note that argv is type list
            SubDUT = NVME([Dev]) 
            self.Print("Issue function level reset")   
            self.FunctionLevel_reset(SubDUT)
            self.Print("Check if device is alive for %s"%Dev)
            if SubDUT.dev_alive:
                self.Print("Pass!", "p")
            else:
                self.Print("Fail, device is missing!", "f")
                ret_code = 1
            isPF = False
            self.Print("") 
            
        return ret_code       
     
    # </define sub item scripts>


    # define PostTest 
    def PostTest(self): 
        # if not test mode, reset VF to 0
        if not self.mTestModeOn:        
            self.Print("") 
            self.Print("Set all VF offline")
            if not self.SetCurrentNumOfVF(0):
                self.Print("Fail, quit all", "f"); return 1                
        
        return True 


if __name__ == "__main__":
    DUT = SMI_SRIOV(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    

