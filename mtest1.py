#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
import re
import threading
import time
from time import sleep
import struct
import fcntl
import subprocess
# import ioctl_opt
import ctypes
import os
import time
import datetime
import linecache
# Import VCT modules
from lib_vct.NVME import NVME

class SMI_PCIPowerStatus(NVME):

    def SetPS(self, psValue):
        self.write_pcie(self.PMCAP, 0x4, psValue)
        
    def GetPs(self):
    # return int
        PMCS = self.read_pcie(self.PMCAP, 0x4)       
        return PMCS & 0b0011
    
    def initTestItems(self):
        # self.TestItems=[[PS, name, supported],[PS, name, supported],..]
        
        CurrentPS = self.PS_init+1
        
        if CurrentPS==0:
            self.TestItems.append([3, "D3Hot state", True])
            self.TestItems.append([0, "D0 state", True])
        elif CurrentPS==3:
            self.TestItems.append([0, "D0 state", True])             
            self.TestItems.append([3, "D3Hot state", True])
        else:
            self.TestItems.append([3, "D3Hot state", True])
            self.TestItems.append([0, "D0 state", True])
                    
            
    def GetSHN(self):
        mStr = self.shell_cmd("devmem2 %s "%self.Reg_CC)        
        if re.search(": (.*)", mStr):
            value = int(re.search(": (.*)", mStr).group(1),16)
        else:
            value = 0      
        SHN = (value >> 14) & 0b11
        return SHN

    def GetSHST(self):
        mStr = self.shell_cmd("devmem2 %s "%self.Reg_CSTS)        
        if re.search(": (.*)", mStr):
            value = int(re.search(": (.*)", mStr).group(1),16)
        else:
            value = 0      
        CSTS = (value >> 2) & 0b11
        return CSTS

    def GetRDY(self):
        mStr = self.shell_cmd("devmem2 %s "%self.Reg_CSTS)        
        if re.search(": (.*)", mStr):
            value = int(re.search(": (.*)", mStr).group(1),16)
        else:
            value = 0      
        RDY = (value ) & 0b1
        RDY = 0 if value==0xffffffff else RDY
        return RDY  
                                    
    def thread_SetRTD3(self):
        self.shell_cmd("echo auto > /sys/bus/pci/devices/%s/power/control"%self.pcie_port)
        self.shell_cmd("echo -n %s > /sys/bus/pci/drivers/nvme/unbind"%self.pcie_port)
        
    def thread_ResetRTD3(self):
        self.shell_cmd("echo -n %s > /sys/bus/pci/drivers/nvme/bind"%self.pcie_port)
        self.shell_cmd("echo on > /sys/bus/pci/devices/%s/power/control"%self.pcie_port)        
        
    def PrintAlignString(self,S0, S1, S2="", PF="default"):            
        mStr = "{:<4}{:<30}{:<30}{:<30}".format("", S0, S1, S2)
        if PF=="pass":
            self.Print( mStr , "p")        
        elif PF=="fail":
            self.Print( mStr , "f")      
        else:
            self.Print( mStr )      
                    
    def __init__(self, argv):
        # initial parent class
        super(SMI_PCIPowerStatus, self).__init__(argv)
        
        # save initial values        
        self.PS_init = self.GetPs()
        self.Print("Initial value of power state : %s"%self.PS_init) 
        
        self.TestItems=[]
        self.initTestItems()
        
        self.Reg_CC=hex(self.MemoryRegisterBaseAddress+0x14)
        self.Reg_CSTS=hex(self.MemoryRegisterBaseAddress+0x1C)
        self.mT=0

    # define pretest  
    def PreTeset(self):                
        return True            










    class _nvme_passthru_cmd(ctypes.Structure):
        _fields_ = [
            ('opcode', ctypes.c_byte),
            ('flags', ctypes.c_byte),
            ('rsvd1', ctypes.c_ushort),
            ('nsid', ctypes.c_uint),
            ('cdw2', ctypes.c_uint),
            ('cdw3', ctypes.c_uint),
            ('metadata', ctypes.c_ulonglong),
            ('addr', ctypes.c_ulonglong),
            ('metadata_len', ctypes.c_uint),
            ('data_len', ctypes.c_uint),
            ('cdw10', ctypes.c_uint),
            ('cdw11', ctypes.c_uint),
            ('cdw12', ctypes.c_uint),
            ('cdw13', ctypes.c_uint),
            ('cdw14', ctypes.c_uint),
            ('cdw15', ctypes.c_uint),
            ('timeout_ms', ctypes.c_uint),
            ('result', ctypes.c_uint),
        ]
    
    def nvme_write(self, nvmePort, ns, slba, nlb, data):
        #define NVME_IOCTL_IO_CMD    _IOWR('N', 0x43, struct nvme_passthru_cmd)
        # NVME_IOCTL_IO_CMD = ioctl_opt.IOWR(ord('N'), 0x43, _nvme_passthru_cmd)
        NVME_IOCTL_IO_CMD = 0xC0484E43
    
        #fd = os.open("/dev/nvme0", os.O_RDONLY)
        fd = os.open("%s"%nvmePort, os.O_RDONLY)
        nvme_passthru_cmd = self._nvme_passthru_cmd(    0x01, # opcode
                                    0, # flags = os.O_RDONLY if (0x01 & 1) else os.O_WRONLY | os.O_CREAT, # opcode & 1 ? O_RDONLY : O_WRONLY | O_CREAT
                                    0, # rsvd1
                                    ns, # nsid
                                    0, # cdw2
                                    0, # cdw3
                                    0, # metadata
                                    id(data)+36, # addr
                                    0, # metadata_len
                                    len(data), # data_len
                                    slba&0xffffffff, # cdw10= SLBA&0xffffffff
                                    (slba&0xffffffff00000000)>>32, # cdw11= (SLBA&0xffffffff00000000)>>32
                                    nlb, # cdw12= (LR<<31)|(FUA<<30)|((PRINFO&0xf)<<26)|((DTYPE&0xf)<<20)|NLB
                                    0, # cdw13= DSM
                                    0, # cdw14= ILBRT
                                    0, # cdw15= ((LBATM&0xffff)<<16)|(LBAT&0xffff)
                                    0, # timeout_ms
                                    0, # result
        )
    
        ret = fcntl.ioctl(fd, NVME_IOCTL_IO_CMD, nvme_passthru_cmd)
        os.close(fd)
        return ret
    
    def WWW(self, thread):        
        thread_w=thread          
        RetThreads = []        
        data =''.join(chr(0x2F) for x in range(0x200))
        for i in range(thread_w):                
            t = threading.Thread(target = self.WWW_1, args=(data,))
            t.start() 
            RetThreads.append(t)     
        return RetThreads
        
    def WWW_1(self, data):
        while self.mT<5:
            rt=self.nvme_write("/dev/nvme0", 1, 0, 0, data) 
            if rt != 0:
                print "Error rtcode: %s"%rt
        #print threading.current_thread().name+" finish"





    def SubProcessThread(self, scriptName):
        p = subprocess.Popen("cd SMI_SRIOV_SubProcess; python %s /dev/nvme0n1"%scriptName, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True)           
        while p.poll() is None:
            sleep(0.5)
        retcode = p.returncode
        print     "recode=%s"%retcode
        
    def Run_SMI_SRIOV_SubProcess_Script(self, scriptName):
        logFolder="SMI_SRIOV_SubProcess/Log/"
        self.RmFolder(logFolder)
        logPathWithUniversalCharacter="SMI_SRIOV_SubProcess/Log/*.logcolor"
        t=threading.Thread(target=self.SubProcessThread, args=(scriptName,))
        t.start()        
        cnt=0        

        while True:            
            # if file exist    
            logPath=self.shell_cmd("find %s 2> /dev/null |grep %s " %(logPathWithUniversalCharacter,logPathWithUniversalCharacter))
            if logPath: 
                # print new line
                if self.isfileExist(logPath):            
                    count = len(open(logPath).readlines(  ))
                    if count>cnt:
                        for ptr in range(cnt, count):
                            linecache.clearcache()
                            line = linecache.getline(logPath, ptr+1)                    
                            sys.stdout.write(line)
                        cnt = count            

            if not t.is_alive():
                break   
            

    # <define sub item scripts>
    SubCase1TimeOut = 60
    SubCase1Desc = "1111111111111111111Test Power State"   
    SubCase1KeyWord = ""
    def SubCase1(self):

        self.Run_SMI_SRIOV_SubProcess_Script("mtest.py")

   
        
        

        

        #retcode = subprocess.call(["python", "SMI_SRIOV_SubProcess/mtest.py", "/dev/nvme0n1"])        
        #print "Return code of test.py is ", retcode
        
        #self.shell_cmd("cd SMI_SRIOV_SubProcess; python mtest.py /dev/nvme0n1 &")
        #p = subprocess.Popen("cd SMI_SRIOV_SubProcess; python mtest.py /dev/nvme0n1", shell=True, stderr=subprocess.PIPE)
        #p = subprocess.Popen("cd SMI_SRIOV_SubProcess; python mtest.py /dev/nvme0n1", stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True)

                             
            
            
    # end of print new line    

 
                    
        print "done"   
            
            
        
        
        
        
        
        
        cmd = "python mtest.py /dev/nvme0n1"
         
        ''' 
        p = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True)
         
        while True:
            line = p.stdout.readline()
            if not line: break                  
        '''
         

                
                        
                
        return 0    

    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_PCIPowerStatus(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    