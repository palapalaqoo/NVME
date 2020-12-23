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

class mtest(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "mtest.py"
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
        self.SetDynamicArgs(optionName="s1", optionNameFull="loops", helpMsg="number of loops", argType=str, \
                            iniFileName="SMIPowerCycleTest.ini", iniSectionName="None", iniOptionName="UGSDTimerMax")
        # initial parent class
        super(mtest, self).__init__(argv)
        self.loops = self.GetDynamicArgs(0) 
        
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
   


            
 
    class Ordered(OrderedAttributeClass):

        
        LogIdentifier = OrderedAttributeClass.MyOrderedField((2,3,4))
        TNEV = OrderedAttributeClass.MyOrderedField((3,3,4))
        TLL = OrderedAttributeClass.MyOrderedField((4,3,4))
        
        def __init__(self):
            self.LogRevision = OrderedAttributeClass.MyOrderedField([5,6])
            self.LogHeaderLength = OrderedAttributeClass.MyOrderedField([5,6])
            self.Timestamp = OrderedAttributeClass.MyOrderedField([5,6])
        '''
        LogRevision = OrderedAttributeClass.MyOrderedField([5,6])
        LogHeaderLength = OrderedAttributeClass.MyOrderedField([5,6])
        Timestamp = OrderedAttributeClass.MyOrderedField([5,6])
        POH = OrderedAttributeClass.MyOrderedField([5,6])
        PowerCycleCount = OrderedAttributeClass.MyOrderedField([5,6])
        VID = OrderedAttributeClass.MyOrderedField([5,6])  
        '''
        def XXXX(self):
            print "XXXX here"

    
    
    SubCase1TimeOut = 600
    def SubCase1(self):
        kk=2
        aa = self.AdminCMDDataStrucToListOrString(strIn, ReturnType, BytesOfElement)
        ordered = self.Ordered()
        ss=ordered.getOrderedAttributesList_init()

        #self.Ordered.ordered_fields = ["aaaaa", "ss5555"]
        ss=ordered.getOrderedAttributesList_init()
        ordered.setOrderedAttributesList_init("TNEV", 88888)
        ss=ordered.getOrderedAttributesList_init()
        
        ss=self.Ordered.getOrderedAttributesList_init()
        
        ss = ordered.getOrderedAttributesList_curr()
        print ordered.TNEV 
        ordered.TNEV = 456
        kk = getattr(ordered, "TNEV")
        bb= ordered.getOrderedAttributesList_curr()
        '''
        aa= dir(ordered)
        print aa
        bb = ordered.__dict__.items()
        print bb
        ordered.TNEV = 456
        kk = ordered.getList()
        '''
        bb= ordered.ordered_fields
        print bb
        
        bb= ordered.getOrderedAttributesList_curr()
        print bb     
        print ordered.TNEV   
        print getattr(ordered, "TNEV")

        return 0        
        
        
        



    
    
if __name__ == "__main__":


            
                       
    print mtest

    DUT = mtest(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    
