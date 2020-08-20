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
# Import VCT modules
from lib_vct.NVME import NVME


class mtest1(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "mtest1.py"
    Author = "Sam Chan"
    Version = "20191030"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    def getDW10_DW11(self, slba):
        dw10=slba&0xFFFFFFFF
        dw11=slba>>32
        return dw10, dw11 
    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def __init__(self, argv):
        self.SetDynamicArgs(optionName="s1", optionNameFull="loops", helpMsg="number of loops, default = 1", argType=int)
        # initial parent class
        super(mtest1, self).__init__(argv)
        self.loops = self.GetDynamicArgs(0) 

        
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
   
    
    SubCase1TimeOut = 600
    def SubCase1(self):




        for i in range(20):
            self.SmartCheck.isRunOncePass()
            sleep(2)

        
        
        
        aa = 5

        
        '''
        print self.SmartCheck.isRunning()
        self.SmartCheck.start()
        
        self.SmartCheck.stop()
                
        import os
        import signal
        import subprocess    
        
        # find current bash pid
        CMDps = "ps -aux |grep bash"
        rePattern =  "(\d+)\s+.*pts/(\d+)\s" # first is pid, 2th is pts  # root     20775  0.0  0.0 115580  3600 pts/1    Ss   10:02   0:00 bash
        ptsList0 = []

        for line in self.yield_shell_cmd(CMDps):
            if re.search(rePattern, line):
                # pid=int(re.search(rePattern, line).group(1))
                value=int(re.search(rePattern, line).group(2)) 
                ptsList0.append(value)
                
        CMD = "python SMI_SmartCheck/SMI_SmartCheck.py /dev/nvme0 -s SMART.ini -p 1 -l ./SmartLog/exampleLog2 2>&1"
        p = subprocess.Popen("/bin/gnome-terminal -- bash -c '%s; exec bash'"%CMD,shell=True, stdout=subprocess.PIPE)
        # do something here...
        
        # wait for creating gnome-terminal and get pid by check if pts/x which x is new one
        GnomePid = None
        timeMax = 50 # 1 for 0.1s
        while GnomePid==None:
            # find current bash pid
            for line in self.yield_shell_cmd(CMDps):
                if re.search(rePattern, line):              
                    pid=int(re.search(rePattern, line).group(1))                                           
                    value1=int(re.search(rePattern, line).group(2)) 
                    if value1 not in ptsList0: # find  
                        GnomePid = pid                    
                        break
            timeMax = timeMax -1            
            if timeMax==0:# time up
                break            
            sleep(0.1)
        # end while
            
        if GnomePid ==None: return False

        sleep(5)


        self.shell_cmd("kill -9 %s"%GnomePid)
        '''
        #p.kill()
        #p.send_signal(signal.SIGKILL)
        #p_pid = p.pid  # get the process id
        #os.kill(p_pid, signal.SIGKILL)      

        '''
        self.SmartCheck.start()
        sleep(1)
        self.SmartCheck.stop()        
        
        cmd = "python SMI_SmartCheck/SMI_SmartCheck.py /dev/nvme0 -s SMsART.ini -p 1 -l ./SmartLog/exampleLog2 2>&1"
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=open("/dev/stdout", 'w'))

        print proc.poll()
        print proc.poll()
        sleep(1)
        print proc.poll()
        print proc.poll()
        print proc.poll()
        
        #while (True):
            #print proc.poll()
            # Do something...
            #line = proc.stdout.readline()[:-1]
            #self.Print( line)
    
        if proc.wait() != 0: exit(1)
        print proc.poll()

        exit(0)
        '''
        
        
        

        '''
        for i in range(10):
            self.PrintProgressBar(i, 10, prefix="hihi", showPercent=True)
            sleep(1)
        '''
         
            
        self.Print("Wait")

                   
        
        
        
        
        

        
        
        
        
        
        return 0        
        
        
        



    
    
if __name__ == "__main__":


            
                       

    DUT = mtest1(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    
