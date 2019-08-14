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
import xml.etree.ElementTree as ET
import paramiko
import json
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
        vmXmlFile=None
        vmPciePort=None   
        vmIpAddr=None
                    
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

    # set vf, if success, set AllDevices where AllDevices[0] is PF, others is VF 
    def SetCurrentNumOfVF(self, value):
        value=int(value)
        path="/sys/class/block/%s/device/device/sriov_numvfs"%self.dev[5:]
        if self.isfileExist(path):
            if self.shell_cmd("echo %s > %s 2>&1  ; echo $?"%(value, path))!="0" :
                self.Print("command fail", "f"); return False
            else:
                if value!=0: 
                    # wait for os to create drive        
                    sleep(2)
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
    def TestWriteRead(self, SubDUT, writeValue):
    # SubDUT type is NVME
        # write 10M data with writeValue
        SubDUT.fio_write(offset=0, size="10M", pattern=writeValue, nsid=1, devPort=SubDUT.dev_port)
        if SubDUT.fio_isequal(offset=0, size="10M", pattern=writeValue, nsid=1):
            return True
        else:
            self.Print("Device: %s TestWriteRead fail: expected pattern is %s"%(SubDUT, writeValue), "f")
            return False
           
    
    def TestWriteCompare(self, SubDUT, writeValue):
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
        if SubDUT.fio_isequal(offset=0, size="10M", pattern=0, nsid=1):
            return True
        else:
            self.Print("Device: %s TestWriteFormatRead fail: expected pattern is %s"%(SubDUT, 0), "f")
            return False         
   
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
        if not SubDUT.WaitSanitizeFinish(240): return False            
        # expected pattern = 0
        if SubDUT.fio_isequal(offset=0, size="10M", pattern=0, nsid=1):
            return True
        else:
            self.Print("Device: %s TestWriteSanitizeRead fail: expected pattern is %s"%(SubDUT, 0), "f")
            return False    
    
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

    def nvme_reset(self, SubDUT, writeValue):
        rtcode = self.shell_cmd("  nvme reset %s; echo $? "%(SubDUT.dev_port), 0.5)
        sleep(1) 
        return True if rtcode=="0" else False
    
    def hot_reset(self, SubDUT, writeValue):
        self.shell_cmd("  echo 1 > /sys/bus/pci/devices/%s/remove " %(SubDUT.pcie_port), 0.1) 
        self.shell_cmd("  echo 1 > /sys/bus/pci/rescan ", 0.1)
        sleep(1)     
        return True        
    
    def FunctionLevel_reset(self, SubDUT, writeValue):       
        SubDUT.write_pcie(SubDUT.PXCAP, 0x9, SubDUT.IFLRV)
        sleep(1)
        self.shell_cmd("  echo 1 > /sys/bus/pci/devices/%s/reset " %(SubDUT.pcie_port), 1) 
        if SubDUT.dev_alive:            
            return True        
        else:
            return False     
    
    def DeleteCreateAttach_NS(self, SubDUT, writeValue):        
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
            # first is PF, other if VF
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
            # (highlightbackground="brown", highlightcolor="brown", highlightthickness=2, bd=0) for brown border color
            # create frame for put all slot elements there
            F_slotView_oneSlot = tkinter.Frame(F_slotView, relief="flat",  highlightbackground="brown", highlightcolor="brown", highlightthickness=2, bd=0)
            F_slotView_oneSlot.pack(side="left")
            
            # add header
            Dev = self.AllDevices[slot]
            slotHeader = tkinter.Label( F_slotView_oneSlot, text=Dev , width= ListWidth,relief="flat", highlightbackground="brown", highlightcolor="brown", highlightthickness=2, bd=0) # Dev="nvme0n1"
            slotHeader.pack(side="top")      
                  
            # add listview for current testing item
            Lb = tkinter.Listbox(F_slotView_oneSlot, height = ListHight, width= ListWidth, relief="flat")
            Lb.pack(side="top")
            # save to CurrItems for further processing, ex. ["nvme0n1", Lb0], ["nvme1n1", Lb1]
            self.CurrItems.append([Dev, Lb])
            
            # add header

            slotHeader = tkinter.Label( F_slotView_oneSlot, text="Available test items" , width= ListWidth,relief="flat", highlightbackground="brown", highlightcolor="brown", highlightthickness=2, bd=0) # Dev="nvme0n1"
            slotHeader.pack(side="top")  
                        
            # hight in characters for list available test item  
            Lb = tkinter.Listbox(F_slotView_oneSlot, height = ListHight_ava, width= ListWidth_ava,relief="flat")
            Lb.pack(side="top")
            # save to CurrItems for further processing
            self.AvaItems.append([Dev, Lb]) 
            
            # create frame space
            F_slotView_space = tkinter.Frame(F_slotView,  width=10)
            F_slotView_space.pack(side="left")            
            # ---- end per slot
        
        F_Info = tkinter.Frame(self.root)
        F_Info.pack(side="bottom")        
        self.root.mainloop()
        return True       
                
                
    def GetVMList(self):
    # return [id, name, state]
        rtList=[]
        mStr=self.shell_cmd("virsh list --all| sed 1,2d")   # remove first line for re.search            
        OneVM = re.findall("\S+\s+\w+\s+\w+", mStr)
        if OneVM!=None:
            for mVM in OneVM:
                # id may equal '-', means not active
                Id =re.search("(\S+)\s+(\w+)\s+(\w+)", mVM).group(1)
                if Id=="-":
                    Id=0
                else:
                    Id =int(Id)
                    
                Name =re.search("(\S+)\s+(\w+)\s+(\w+)", mVM).group(2)
                State =re.search("(\S+)\s+(\w+)\s+(\w+)", mVM).group(3)
                rtList.append([Id, Name, State])
            return rtList
        else:
            return None
                
    def AttachPCIEtoVM(self, VMname, XMLfile):
        fullPath="./SRIOV_Resources/%s"%XMLfile
        self.shell_cmd("virsh attach-device %s %s"%(VMname, fullPath))
        
    def DetachPCIEtoVM(self, VMname, XMLfile):
        fullPath="./SRIOV_Resources/%s"%XMLfile
        self.shell_cmd("virsh detach-device %s %s"%(VMname, fullPath))    
    
    def CreateXMLforAttachDetachPCIE(self):
        #Create XML("AttachDetachPCIE.xml") file for attach/detach pci, command as below(VF0 is the name of VM)
        # virsh attach-device VF0 AttachDetachPCIE.xml 
        # virsh detach-device VF0 AttachDetachPCIE.xml  
        
        VM_xml_list=[]
        
        # for all VF devices
        for device in self.VFDevices:
                              
            SubDUT = NVME([device]) 
            fileName = "AttachDetachPCIE_%s.xml"%SubDUT.pcie_port
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
            VM_xml_list.append([ device, fileName, SubDUT.pcie_port])   
        return VM_xml_list    
    
    def CreateVM(self, VMname):
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
        
        # create VM
        CMD="virt-install -n %s -r 1024 --os-type=linux --disk %s,device=disk,bus=ide -w  bridge=virbr0,model=virtio \
        --vnc  --import   --os-variant rhel7 --noautoconsole"%(VMname, VMfullPath)
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
        s = paramiko.SSHClient()
        s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        sleep(0.5)
        s.connect(hostname=IP, port=22, username="root", password="Smi888")
        stdin, stdout, stderr = s.exec_command(CMD)

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
    
    def GetFIO_Speed(self, FIOresult):
        # FIOresult, where command  --output-format=terse 
        findall = re.findall("([^;]*);", FIOresult)
        if len(findall)>0:
            read_BW_in_KBs = findall[6]
            write_BW_in_KBs = findall[47]
            return int(write_BW_in_KBs)
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
        
    def DoVM_FIOtest(self, info):
        # all nvme device in VM is /dev/nvme0n1
        FIO_CMD = self.FIO_CMD("/dev/nvme0n1")
        IP=info.vmIpAddr
        device= info.vmName
        mStr = self.VM_shell_cmd(IP, FIO_CMD)
        speedInKbyte = self.GetFIO_Speed(mStr)
        if speedInKbyte==None:
            self.Print("FIO fail", "f")
            return False  
        else:   
            self.Print("FIO write %s: bw=%.1f MiB/s,  bandwidth (KB/s):%s"%(device, speedInKbyte/float(1024), speedInKbyte), "f") 
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
        
    def FIO_CMD(self, device):
        # output format terse,normal
        return "fio --direct=1 --iodepth=16 --ioengine=libaio --bs=2M --rw=write --numjobs=1 \
            --offset=0 --filename=%s --name=mdata --do_verify=0  \
            --output-format=terse,normal --runtime=5"%(device)        
        
    def DO_Script_Test(self, testScriptName, option=""):
        # ex. testScriptName = 'SMI_SmartHealthLog.py'
        for device in self.AllDevices:            
            self.Print("") 
            self.Print("python %s %s"%(testScriptName, device) )
            self.Print("")
            # ex. Log/sublog/devnvme0n1/SMI_SmartHealthLog/
            logPath="Log/sublog/%s/%s"%(device.replace("/",""), testScriptName.replace(".py",""))
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
        PF_PciePort=self.pcie_port
        # get device bus and device number, remove function number
        PF_BusDeviceNum = PF_PciePort[:-2]
        # get nvme list adll devices
        NvmeList=self.GetCurrentNvmeList()
        for device in NvmeList:
            Port = self.GetPciePort(device)
            BusDeviceNum = Port[:-2]
            # if not PF device and (bus and device num) is the same, than it is VF from PF
            if PF_PciePort!=Port and PF_BusDeviceNum==BusDeviceNum:
                mList.append(device)
        return mList
    
    def __init__(self, argv): 
        # initial new parser if need, -t -d -s -p was used, dont use it again
        self.AddParserArgs(optionName="n", optionNameFull="numofvf", helpMsg="number of VF that will be enable and test", argType=int) 
                
        # initial parent class
        super(SMI_SRIOV, self).__init__(argv)      
        
        # get new parser if need, where args order is the same with initial order
        # config_numvfs = int or None
        self.config_numvfs = self.GetDynamicArgs(0)       
        
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
        
        # UI define
        self.UsingGUI=self.CheckTkinter()
        #self.UsingGUI=False
        self.CurrItems=[]   # ex. ["nvme0n1", Lb0], ["nvme1n1", Lb1]
        self.AvaItems=[]    # ex. ["nvme0n1", Lb0], ["nvme1n1", Lb1]
        self.root=None
                
        # get TotalVFs of SR-IOV Virtualization Extended Capabilities Register(PCIe Capabilities Registers)
        #self.TotalVFs = self.read_pcie(base = self.SR_IOVCAP, offset = 0x0E) + (self.read_pcie(base = self.SR_IOVCAP, offset = 0x0F)<<8)
        self.TotalVFs = self.shell_cmd("cat /sys/class/block/nvme0n1/device/device/sriov_totalvfs")
        
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
        
        
        # others
        self.Running=None
        
        
    # define pretest  
    def PreTest(self): 
               
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
                    
        if self.Sysfs_SRIOV_Supported:
            self.Print("Linux's sysfs support SRIOV: Yes")
        else:
            self.Print("Linux's sysfs support SRIOV: No", "w")    
        
        self.Print("")
        nmuvfs = self.GetCurrentNumOfVF()
        self.Print("Current Num Of VF: %s"%nmuvfs, "p")   
        
        
        # if test mode, no need to reset VF     
        if not self.mTestModeOn:
            # reset VF 
            if nmuvfs!="0":
                self.Print("")
                self.Print("Set all VF offline")
                if not self.SetCurrentNumOfVF(0):
                    self.Print("Fail, quit all", "f"); return False  
        
        # if VF=0, enable all            
        nmuvfs = self.GetCurrentNumOfVF()        
        if nmuvfs=="0":
            # enable all VF        
            self.Print("") 
            self.Print("Set all VF online (TotalVFs = %s)"%self.TotalVFs)
            if not self.SetCurrentNumOfVF(self.TotalVFs):
                self.Print("Create VF Fail, quit all", "f"); return 1  
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
    SubCase2Desc = "Test power cycle"   
    SubCase2KeyWord = ""
    def SubCase2(self):
        ret_code=0       
        if self.mTestModeOn:
            self.Print("skip sub case")
            return 0

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
             
        self.Print("")            
        self.Print("Check data petterns in all VF and PF") 
        cnt=0
        for device in range(len(self.AllDevices)):
            dataPattern = dataPattern_List[cnt]
            if not SubDUT.fio_isequal(offset=0, size="10M", pattern=dataPattern, fio_direct=0):
                self.Print("Fail!, data changed, expect pattern = %s"%dataPattern, "f")
                self.Print("hexdump data blow ..", "f")
                self.shell_cmd("hexdump %s -n 512 -C"%SubDUT.dev)
                self.Print("")   
                self.Print("quit", "f") 
                return 1  
            
        self.Print("Pass")
            
        
        self.Print("") 
        self.Print("Set all VF offline")
        if not self.SetCurrentNumOfVF(0):
            self.Print("Fail, quit all", "f"); return 1
        
        self.Print("Done!")
        
        return ret_code

    SubCase3TimeOut = 1800
    SubCase3Desc = "Test SR-IOV in virtual machines"   
    SubCase3KeyWord = ""
    def SubCase3(self):
        # note: using TotalVFs to decide the number of VM
        ret_code=0   
        
        if self.mTestModeOn:
            self.Print("skip sub case")
            return 0        

        
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
        
        # start ------------------------------------------------------------------------------    
        # init VMinfo and VMname
        for i in range(self.TotalVFs):    
            info = self.VMinfoClass()
            info.vmName="VM%s"%i
            self.VMinfo.append(info)

        self.Print("")        
        self.Print("Create virtual machines VM0 to VM%s"%(self.TotalVFs-1))        
        for info in self.VMinfo:
            name = info.vmName
            if not self.CreateVM(name):
                self.Print("Fail to create %s"%name)
                return 1
        self.Print("Done")

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
        ''' snchan  
        self.Print("")
        self.Print("Host FIO write speed test")   
        self.Print("--------------------------------------")     
        for device in self.VFDevices:
            SubDUT = NVME([device])
            FIO_CMD = self.FIO_CMD(device)   
            mStr = SubDUT.shell_cmd(FIO_CMD)
            speedInKbyte = self.GetFIO_Speed(mStr)
            if speedInKbyte==None:
                self.Print("FIO fail", "f")
                return 1
            else:
                self.Print("FIO write %s: bw=%s MB/s"%(device, speedInKbyte/1024), "f")
        self.Print("--------------------------------------") 
          
        self.Print("")     
        self.Print("Create XML files for Attach Detach PCIE to VM")
        # create xml file for attach/detach command
        VM_xml_list = self.CreateXMLforAttachDetachPCIE()        
        # check if VMname =  xml file for attach/detach command
        if len(self.VMinfo)!=len(VM_xml_list)  :
            self.Print("Number of VM != number of XML files", "f")
            return 1
        else:
            # copy to VMinfo
            for i in range(len(self.VMinfo)):
                info=self.VMinfo[i];
                info.vmHostNVMEname=VM_xml_list[i][0]
                info.vmXmlFile=VM_xml_list[i][1]
                info.vmPciePort=VM_xml_list[i][2]
            self.Print("Done")
            
        
        self.Print("")
        self.Print("Attach all SR-IOV PCIE device to guest VMs")
        for info in self.VMinfo:
            VMname = info.vmName
            PCIEport = info.vmPciePort
            XMLfile = info.vmXmlFile
            NVMEname= info.vmHostNVMEname
            self.Print("Attach PCIe %s(%s) to %s"%(PCIEport, NVMEname, VMname))
            self.AttachPCIEtoVM(VMname, XMLfile)
        
        
        '''
        '''
        self.Print("")
        self.Print("Virtual machine FIO write speed test") 
        self.Print("--------------------------------------") 
        for info in self.VMinfo:            
            if not self.DoVM_FIOtest(info): return 1                
        self.Print("--------------------------------------") 
        '''
        self.Print("")
        self.Print("Virtual machine FIO write speed test, all VMs do FIO simultaneously ")
        mThreads = [] 

        for info in self.VMinfo:            
            t = threading.Thread(target = self.DoVM_FIOtest, args=(info,))
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
        
        self.Print("")
        self.Print("")
        self.Print("")

        
        
        
        
        
            

        
        
        
        
        
        
        
        
        
        
        
        return ret_code
        
        
    SubCase4TimeOut = 1800
    SubCase4Desc = "Test NVMe device speed"   
    SubCase4KeyWord = ""
    def SubCase4(self):
        # note: using TotalVFs to decide the number of VM
        ret_code=0   
        
        
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
        self.Print("") 
        self.Print("Set all VF offline")
        if not self.SetCurrentNumOfVF(0):
            self.Print("Fail, quit all", "f"); return 1
        '''
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
        ret_code = 0 if self.DO_Script_Test(testScriptName) else 1
                      
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
        ret_code = 0 if self.DO_Script_Test(testScriptName, "--disablepwr=1") else 1
                      
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
        ret_code = 0 if self.DO_Script_Test(testScriptName) else 1                      
        return ret_code    
        
    
    
    '''
    SubCase2TimeOut = 1800
    SubCase2Desc = "Enable all VF with all Flexible Resources"   
    SubCase2KeyWord = ""
    def SubCase2(self):
        ret_code=0       
        
        
        self.Print("") 
        self.Print("Set all VF offline")
        if not self.SetCurrentNumOfVF(0):
            self.Print("Fail, quit all", "f"); return 1   
        
        # backup os nvme list            
        self.VFoff_NvmeList=self.GetCurrentNvmeList()
        
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
        self.VFon_NvmeList=self.GetCurrentNvmeList()
        self.VFDevices = list(set(self.VFon_NvmeList) - set(self.VFoff_NvmeList)).sort()
        NumOfVF=len(self.SecondaryControllerList)
        self.Print("Check if linux os create %s NVMe device under folder /dev/"%NumOfVF)
        self.Print("")
        for Dev in self.VFDevices:
            self.Print(Dev)
        if NumOfVF==len(self.VFDevices):
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
        
        #--------------------
        self.Print("")     
        self.Print("Try to run SMI_DSM.py for nvme1n1")   
        self.write        
        print "rtcode=%s"%self.RunSMIScript("SMI_SubProcess/mtest.py", "%s 1,3"%self.dev)     
        
        self.Print("")    
        if self.VI_ResourceSupported:
            VIResourcesFlexibleTotal=self.PCCStructure.VIFRT
            # minimum number of VQ Resources that may be assigned is two 
        # ----------------------        
           

        self.AllDevices = [self.dev] + ["/dev/nvme1n1"] + ["/dev/nvme2n1"]
        self.MultiThreadTest(10)
        
        return ret_code
    '''
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

    
    
    
    

