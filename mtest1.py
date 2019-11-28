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
import sys
import time
from time import sleep
import threading
import re

# Import VCT modules
from lib_vct.NVME import NVME
from lib_vct.NVMECom import deadline

class mtest1(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "mtest1.py"
    Author = "Sam Chan"
    Version = "20191030"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    

    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def __init__(self, argv):
        # initial parent class
        super(mtest1, self).__init__(argv)
        self.paramiko = self.ImportModuleWithAutoYumInstall("paramiko", None)      
        
    def VM_shell_cmd(self, IP, CMD):
        
        if self.paramiko==None:
            self.Print("paramiko not installed!", "f")
        else:
            self.lock.acquire()
            s = self.paramiko.SSHClient()
            s.set_missing_host_key_policy(self.paramiko.AutoAddPolicy())

            s.connect(hostname=IP, port=22, username="root", password="Smi888")
            stdin, stdout, stderr = s.exec_command(CMD)
            self.lock.release()
    
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

    IP1="192.168.122.129"  
    IP2="192.168.122.183"                  
    def DoVM_FIOtestA(self):
        # targetDevice = "/dev/nvme0n1" for SRIOV in all VMs
        # targetDevice = "/dev/vda" for raw disk in all VMs
        # rw: read = "r", write = "w"
        
        
        FIO_CMD = "fio --direct=0 --iodepth=128 --ioengine=libaio --bs=128k --rw=randwrite --numjobs=1 --offset=0 --filename=/dev/nvme0n1 --name=mdata --do_verify=0 -size=512M --output-format=terse,normal"
        self.Print(FIO_CMD)   
        IP=mtest1.IP1
        VMname= "VM0"
        FIO_CMD = FIO_CMD + ">> fioOut &"
        mStr = self.VM_shell_cmd(IP, "rm -f fioOut")
        mStr = self.VM_shell_cmd(IP, FIO_CMD)
        
    def DoVM_FIOtestAS(self):
        IP=mtest1.IP1
        for cnt in range(10):
            sleep(1)
            mStr = int(self.VM_shell_cmd(IP, "cat fioOut 2>&1 >/dev/null ; echo $?"))
            if mStr==0: # fio finish, file exist
                mStr = self.VM_shell_cmd(IP, "cat fioOut")               
                speedInKbyte = self.GetFIO_Speed(mStr)
                if speedInKbyte==None:
                    self.Print("FIO fail", "f")
                    return False  
                else:   
                    self.Print("FIO %s %s: bw=%.1f MiB/s,  bandwidth (KB/s):%s"%("write", "VM0", speedInKbyte/float(1024), speedInKbyte), "f") 
                    return True
        return False  

    def DoVM_FIOtestB(self):
        # targetDevice = "/dev/nvme0n1" for SRIOV in all VMs
        # targetDevice = "/dev/vda" for raw disk in all VMs
        # rw: read = "r", write = "w"
        FIO_CMD = "fio --direct=0 --iodepth=128 --ioengine=libaio --bs=128k --rw=randwrite --numjobs=1 --offset=0 --filename=/dev/nvme0n1 --name=mdata --do_verify=0 -size=512M --output-format=terse,normal"
        self.Print(FIO_CMD)  
        IP=mtest1.IP2 
        VMname= "VM1"
        FIO_CMD = FIO_CMD + ">> fioOut &"
        mStr = self.VM_shell_cmd(IP, "rm -f fioOut")
        mStr = self.VM_shell_cmd(IP, FIO_CMD)
        
        for cnt in range(10):
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
   
   
    def DoVM_FIOtestBS(self):
        IP=mtest1.IP2
        for cnt in range(10):
            sleep(1)
            mStr = int(self.VM_shell_cmd(IP, "cat fioOut 2>&1 >/dev/null ; echo $?"))
            if mStr==0: # fio finish, file exist
                mStr = self.VM_shell_cmd(IP, "cat fioOut")               
                speedInKbyte = self.GetFIO_Speed(mStr)
                if speedInKbyte==None:
                    self.Print("FIO fail", "f")
                    return False  
                else:   
                    self.Print("FIO %s %s: bw=%.1f MiB/s,  bandwidth (KB/s):%s"%("write", "VM1", speedInKbyte/float(1024), speedInKbyte), "f") 
                    return True
        return False     
        
    def DoVM_FIOtest0(self):   
        self.shell_cmd("fio --direct=0 --iodepth=128 --ioengine=libaio --bs=128k --rw=randwrite --numjobs=1 --offset=0 --filename=/dev/nvme0n2 --name=mdata --do_verify=0 -size=512M --output-format=terse,normal")
        
    def DoVM_FIOtest1(self):   
        self.shell_cmd("fio --direct=0 --iodepth=128 --ioengine=libaio --bs=128k --rw=randwrite --numjobs=1 --offset=0 --filename=/dev/nvme0n3 --name=mdata --do_verify=0 -size=512M --output-format=terse,normal")
    # <define sub item scripts>
    SubCase1TimeOut = 2000
    SubCase1Desc = "test 1"   
    SubCase1KeyWord = ""
    def SubCase1(self):

        print self.KMGT_reverse("1k")
        print self.KMGT_reverse("1M")
        print self.KMGT_reverse("1G")
        print self.KMGT_reverse("1.2k")
        print self.KMGT_reverse("4k")
        print self.KMGT_reverse("1280k")
        print self.KMGT_reverse("640k")
        return 0

       
        #self.stdoutBk.write(u"\u001b[s")
        
        for i in range(20):
            self.PrintProgressBar(i+1, 20, length = 50)
            
            sleep(0.1)
                       
                       
        #self.Print("done")

            

        '''
        t = threading.Thread(target = self.DoVM_FIOtestA)
        t.start() 
        mThreads.append(t) 
        
        t = threading.Thread(target = self.DoVM_FIOtestB)
        t.start() 
        mThreads.append(t) 



       
        for process in mThreads:
            process.join()
            self.Print("Done ++")    
        '''      
        
        
        
        
        
        

        
        
        
        
        
        return 0        
        
        
        



    
    
if __name__ == "__main__":
    DUT = mtest1(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 
    
    
    
    
    
