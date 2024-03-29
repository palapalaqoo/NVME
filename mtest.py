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
from random import randint
import platform
import sys
import time
from time import sleep
import threading
import re
import subprocess
import random
import logging
import ConfigParser
import SMI_PLI
import mtest1
# Import VCT modules
from lib_vct.NVME import NVME

from lib_vct.NVMECom import OrderedAttributeClass
from lib_vct.NVMECom import NVMECom

from SMI_Identify import SMI_IdentifyCommand
import Queue
from SMI_FeatureHCTM import SMI_FeatureHCTM

class mtest(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "mtest.py"
    Author = "Sam Chan"
    Version = "20191030"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    que = Queue.Queue()
    def getDW10_DW11(self, slba):
        dw10=slba&0xFFFFFFFF
        dw11=slba>>32
        return dw10, dw11 
    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def __init__(self, argv):
        self.SetDynamicArgs(optionName="s1", optionNameFull="loops", helpMsg="number of loops", argType=str, \
                            iniFileName="SMIPowerCycleTest.ini", iniSectionName="None", iniOptionName="UGSDTimerMax")
        # initial parent class
        super(mtest, self).__init__(argv)
        a=11
        b=type(a)
        if b==str:
            pass
        
        a="11"
        b=type(a)        
        #self.inst = mtest.mtest(sys.argv)
        #self.inst.printaa()
        
        #self.instSMI_PLI = SMI_PLI.SMI_PLI(sys.argv)
        
        #self.instSMI_PLI.TimeUpFunc()
        #self.SMI_PLI = SMI_PLI.SMI_PLI(argv)


        
    def VM_shell_cmd(self, IP, CMD):
        if self.paramiko==None:
            self.Print("paramiko not installed!", "f")
        else:
            s = self.paramiko.SSHClient()
            s.set_missing_host_key_policy(self.paramiko.AutoAddPolicy())
            sleep(0.5)
            s.connect(hostname=IP, port=22, username="root", password="Smi888")
            stdin, stdout, stderr = s.exec_command(CMD)
    
            return stdout.read()
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

    def DoVM_FIOtestA0(self):
        # targetDevice = "/dev/nvme0n1" for SRIOV in all VMs
        # targetDevice = "/dev/vda" for raw disk in all VMs
        # rw: read = "r", write = "w"
        FIO_CMD = "fio --direct=0 --iodepth=128 --ioengine=libaio --bs=128k --rw=randwrite --numjobs=1 --offset=0 --filename=/dev/vda --name=mdata --do_verify=0 -size=512M --output-format=terse,normal"
        self.Print(FIO_CMD)   
        IP="192.168.122.122"
        VMname= "VM0"
        mStr = self.VM_shell_cmd(IP, FIO_CMD)
        speedInKbyte = self.GetFIO_Speed(mStr)
        if speedInKbyte==None:
            self.Print("FIO fail", "f")
            return False  
        else:   
            self.Print("FIO %s %s: bw=%.1f MiB/s,  bandwidth (KB/s):%s"%("write", VMname, speedInKbyte/float(1024), speedInKbyte), "f") 
            return True       

                       
    def DoVM_FIOtestA(self):
        # targetDevice = "/dev/nvme0n1" for SRIOV in all VMs
        # targetDevice = "/dev/vda" for raw disk in all VMs
        # rw: read = "r", write = "w"
        FIO_CMD = "fio --direct=0 --iodepth=128 --ioengine=libaio --bs=128k --rw=randwrite --numjobs=1 --offset=0 --filename=/dev/nvme0n1 --name=mdata --do_verify=0 -size=512M --output-format=terse,normal"
        self.Print(FIO_CMD)   
        IP="192.168.122.178"
        VMname= "VM0"
        mStr = self.VM_shell_cmd(IP, FIO_CMD)
        speedInKbyte = self.GetFIO_Speed(mStr)
        if speedInKbyte==None:
            self.Print("FIO fail", "f")
            return False  
        else:   
            self.Print("FIO %s %s: bw=%.1f MiB/s,  bandwidth (KB/s):%s"%("write", VMname, speedInKbyte/float(1024), speedInKbyte), "f") 
            return True        

    def DoVM_FIOtestB(self):
        # targetDevice = "/dev/nvme0n1" for SRIOV in all VMs
        # targetDevice = "/dev/vda" for raw disk in all VMs
        # rw: read = "r", write = "w"
        FIO_CMD = "fio --direct=0 --iodepth=128 --ioengine=libaio --bs=128k --rw=randwrite --numjobs=1 --offset=0 --filename=/dev/nvme0n1 --name=mdata --do_verify=0 -size=512M --output-format=terse,normal"
        self.Print(FIO_CMD)   
        IP="192.168.122.92"
        VMname= "VM1"
        mStr = self.VM_shell_cmd(IP, FIO_CMD)
        speedInKbyte = self.GetFIO_Speed(mStr)
        if speedInKbyte==None:
            self.Print("FIO fail", "f")
            return False  
        else:   
            self.Print("FIO %s %s: bw=%.1f MiB/s,  bandwidth (KB/s):%s"%("write", VMname, speedInKbyte/float(1024), speedInKbyte), "f") 
            return True             
        
    def DoVM_FIOtest0(self):   
        self.shell_cmd("fio --direct=0 --iodepth=128 --ioengine=libaio --bs=128k --rw=randwrite --numjobs=1 --offset=0 --filename=/dev/nvme0n2 --name=mdata --do_verify=0 -size=512M --output-format=terse,normal")
        
    def DoVM_FIOtest1(self):   
        self.shell_cmd("fio --direct=0 --iodepth=128 --ioengine=libaio --bs=128k --rw=randwrite --numjobs=1 --offset=0 --filename=/dev/nvme0n3 --name=mdata --do_verify=0 -size=512M --output-format=terse,normal")
    # <define sub item scripts>

    
    def mCMD(self, CMD):
        
        p = subprocess.Popen(CMD, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True,  executable='/bin/bash')           
        
        out, err = p.communicate()            

        return out        
        
        
    def PreTest(self):
        return 0    
   


            
 


    def GetHMBAttributesDataStructure(self, cdw11=0, sel=0, nsid=1, nsSpec=True):
    # get feature with status code
        fid = 13
        Value=0 
        AttributesDataStructure=[]
        SC = 0
        buf = "get-feature:0xd (Host Memory Buffer), Current value:0x000001" +\
        "       0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f" + \
        "0000: 00 40 00 00 00 a0 6f 5d 01 00 00 00 10 00 00 00 "  +\
        "0010: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 " 


        mStr="Current value:(\w+)"
              
            
        if re.search(mStr, buf):
            Value=int(re.search(mStr, buf).group(1),16)
            # Host Memory Buffer – Attributes Data Structure
            AttributesDataStructure=re.findall("\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}", buf)
            if len(AttributesDataStructure)==0:
                self.Print("Error, cant find AttributesDataStructure, raw data: %s"%buf, "f")
            AttributesDataStructure = AttributesDataStructure[0]   # find first only
            patten1 = AttributesDataStructure
            line=patten1.replace(" ", "")         
            # return list
            # put patten in to list type
            n=2
            AttributesDataStructure= [line[i:i+n] for i in range(0, len(line), n)] 
            AttributesDataStructure = [int(i, 16) for i in AttributesDataStructure]
            if len(AttributesDataStructure)!=16:
                self.Print("Error, AttributesDataStructure size incorrect, raw data: %s"%AttributesDataStructure, "f")   
                
            HSIZE = self.GetBytesFromList(AttributesDataStructure, 3, 0)
            HMDLAL = self.GetBytesFromList(AttributesDataStructure, 7, 4)  
            HMDLAU = self.GetBytesFromList(AttributesDataStructure, 11, 8)
            HMDLEC = self.GetBytesFromList(AttributesDataStructure, 15, 12)
            AttributesDataStructure = [HSIZE, HMDLAL, HMDLAU, HMDLEC]
            print AttributesDataStructure
            
        return AttributesDataStructure    
    def is_sublist(self, a, b):
        if not a: return True
        if not b: return False
        return b[:len(a)] == a or self.is_sublist(a, b[1:])   
    
    def subfinder(self, mylist, pattern):
        return list(filter(lambda x: x in pattern, mylist))
         
    class FormatClass():
        def p_getFormatTime(self, value):
            mStr = "0x%X(%s)"%(value, self.getFormatTime(value))
            return mStr
        def intToHexStr(self, value):
            return "0x%X"%value                

    def asynchronous_event_request_cmd(self): 
        mstr =  self.shell_cmd(" nvme admin-passthru %s --opcode=0xC 2>&1"%(self.dev))   
        self.que.put(mstr)
    def thread_asynchronous_event_request_cmd(self):
        # return thread        
        t = threading.Thread(target = self.asynchronous_event_request_cmd)
        t.start()   
       
        return t 
    def nvme_reset(self):
        self.status="reset"
        #implement in SMI_NVMEReset.py
        CC= self.MemoryRegisterBaseAddress+0x14
        CChex=hex(CC)
        sleep(0.5)
        self.shell_cmd("devmem2 %s w 0x00460000"%CChex)         
        sleep(0.01)       
        self.shell_cmd("  nvme reset %s "%(self.dev_port), 0.5) 
        self.status="normal"
        return 0                  
    
    def GetEN(self):
        #return self.CR.CC.bit(0)       
        CC= self.MemoryRegisterBaseAddress+0x14
        CChex=hex(CC)
        rtStr = self.shell_cmd("devmem2 %s"%CChex)
        mStr=":\s0x(\w+)"   #  Value at address 0xa1100014: 0x00460001
        if re.search(mStr, rtStr):
            rtStr=int(re.search(mStr, rtStr).group(1),16)
        else:
            print "GetEN error"
            rtStr=int(0)

        CC_EN = rtStr & 0x1
        return CC_EN     
    
    def GetRDY(self):
        #return self.CR.CSTS.bit(0) 
        CC= self.MemoryRegisterBaseAddress+0x1C
        CChex=hex(CC)
        CSTS = self.shell_cmd("devmem2 %s"%CChex)
        mStr=":\s0x(\w+)"   # Value at address 0xa110001c: 0x00000001
        if re.search(mStr, CSTS):
            CSTS=int(re.search(mStr, CSTS).group(1),16)
        else:
            print "GetRDY error"
            CSTS=int(0)

        RDY = CSTS & 0x1
        return RDY       
    def pb(self, x):
    # x = 12322, return 2'b 0011 0000 0010 0010
        bres = bin(x).replace('0b', '').replace('-', '') # If no minus, second replace doesn't do anything
        lres = len(bres) # We need the length to see how many 0s we need to add to get a quadruplets
        # We adapt the number of added 0s to get full bit quadruplets.
        # The '-' doesn't count since we want to handle it separately from the bit string
        bres = bres.zfill(lres + (4-lres%4))
        out=""
        size = len(bres)
        for i in range(size):
            out += bres[i]
            if i%4==3 and i!=size-1:
                out += " " # add space
                
        out = "2'b " + ('-' if x < 0 else '') + out # add 2'b then add  '-' if is less then 0
        
    
        return out    
    SubCase1TimeOut = 600
    def SubCase1(self):
        filePath= "PC300_v081_IdentifyController.bin"
        mStr = self.ReadFile(filePath)
        print self.hexdump(mStr)
        
                
        return 0        




    
    
if __name__ == "__main__":


    DUT = mtest(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    
