#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
import re
import threading
import time
from time import sleep
tkinter = None
# Import VCT modules
from lib_vct.NVME import NVME
from lib_vct import mStruct
#from lib_vct.NVMECom import FIOcmdWithPyPlot_

import struct


import sys
import os



import fcntl
import ctypes
class _nvme_user_io(ctypes.Structure):
    _fields_ = [
        ('opcode', ctypes.c_byte),
        ('flags', ctypes.c_byte),
        ('control', ctypes.c_ushort),
        ('nblocks', ctypes.c_ushort),
        ('rsvd', ctypes.c_ushort),
        ('metadata', ctypes.c_ulonglong),
        ('addr', ctypes.c_ulonglong),
        ('slba', ctypes.c_ulonglong),
        ('dsmgmt', ctypes.c_uint),
        ('reftag', ctypes.c_uint),
        ('apptag', ctypes.c_ushort),
        ('appmask', ctypes.c_ushort),
    ]


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


def nvme_write(ns, slba, nlb, data):
    #define NVME_IOCTL_IO_CMD    _IOWR('N', 0x43, struct nvme_passthru_cmd)
    # NVME_IOCTL_IO_CMD = ioctl_opt.IOWR(ord('N'), 0x43, _nvme_passthru_cmd)
    NVME_IOCTL_IO_CMD = 0xC0484E43

    fd = os.open("/dev/nvme0", os.O_RDONLY)
    nvme_passthru_cmd = _nvme_passthru_cmd(    0x01, # opcode
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
    print "s"
    ret = fcntl.ioctl(fd, NVME_IOCTL_IO_CMD, nvme_passthru_cmd)
    print "e"
    os.close(fd)
    return ret

'''
try:
    cwd = os.getcwd()
    import Tkinter as tk # this is for python2
except:
    self.Print("Try to  install %s/python27-tkinter-2.7.13-5.el7.x86_64.rpm"%cwd, "w")
    if sys.version_info[0] !=2.7 :
        raise Exception("Must be using Python 2.7")
        sys.exit(1)
    else:
        self.shell_cmd("yum localinstall python27-tkinter-2.7.13-5.el7.x86_64.rpm")
        try:
            import Tkinter as tk # this is for python3
        except:
            
            self.Print("Cant install %s/python27-tkinter-2.7.13-5.el7.x86_64.rpm, quit all"%cwd, "f")
            sys.exit(1)
'''


class SMI_PCIPowerStatus(NVME):

    class Point(mStruct.Struct):
        _format = mStruct.Format.LittleEndian
        CNS=0x2
        CNSs=0x2
        x = mStruct.Type.Byte1
        y = mStruct.Type.Byte2
        #z = mStruct.Type.Byte4

    def __init__(self, argv):
        # initial parent class
        super(SMI_PCIPowerStatus, self).__init__(argv)
        

        
        print self.Point.StructSize
        
        #aa=self.shell_cmd("nvme admin-passthru /dev/nvme0n1 --opcode=0x6 --data-len=16 -r --cdw10=0 --namespace-id=1 -b")
        bb='\x01\x04\x02'
        #bb=aa[0:3]
        
        p = self.Point(bb)
        
        cc=p.x
        dd=p.y

        print p.x, p.y   # Prints 1,2
        
        self.SlotItems=[]
        self.root=None
        
        
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
        

    # define pretest  
    def PreTest(self):    
        #self.shell_cmd("rpm -qa |grep python27-tkinter-2.7.13-5.el7.x86_64.rpm")
        global  tkinter   
        cwd = os.getcwd()   

        tkinter = self.import_with_auto_install()
        if tkinter==None:
            return False
        return True
    
    def ThreadCreatUI(self):
        numOfDev = 4
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
            
            # create fram for put all slot elements there
            F_slotView_oneSlot = tkinter.Frame(F_slotView)
            F_slotView_oneSlot.pack(side="left")
            
            # add header
            slotHeader = tkinter.Label( F_slotView_oneSlot, text="nvme0n1" ,relief="solid", width= ListWidth)
            slotHeader.pack(side="top")      
                  
            # add listview for current testing item
            Lb = tkinter.Listbox(F_slotView_oneSlot, height = ListHight, width= ListWidth)
            Lb.pack(side="top")
            Lb.insert(1, "Python")
            Lb.insert(2, "Perl")
            # save to SlotItems for further processing
            self.SlotItems.append(Lb)
            
            # hight in characters for list available test item  
            Lb = tkinter.Listbox(F_slotView_oneSlot, height = ListHight_ava, width= ListWidth_ava)
            Lb.pack(side="top")
            Lb.insert(1, "ava")
            Lb.insert(2, "ava1")         
            
            # ---- end per slot
        
        
        F_Info = tkinter.Frame(self.root)
        F_Info.pack(side="bottom")        
        self.root.mainloop()
        return True
                            
    
        
    # <define sub item scripts>
    SubCase1TimeOut = 2000
    SubCase1Desc = "test 1"   
    SubCase1KeyWord = ""
    def SubCase1(self):
        ret_code=0
        print time.strftime("%Y%m%d_%H:%M:%S", time.localtime())
        self.por_reset()
        self.por_reset()
        self.por_reset()
        self.por_reset()
        
        print self.pcie_port
        self.Print("hello test1")
        
        self.rmFile("./bwOut_bw.log")
        
        CMD1 = "fio --direct=1 --iodepth=1 --ioengine=libaio --bs=64K --rw=write --numjobs=1          --offset=0 --name=mtest --do_verify=0 --verify=pattern --size=0x9E81C1000        --verify_pattern=4 --filename=/dev/nvme0n1"
        
        CMD2 = "fio --direct=1 --iodepth=1 --ioengine=libaio --bs=64K --rw=write --numjobs=1 --size=3G \
         --offset=0 --filename=/dev/nvme1n1 --name=mdata --do_verify=0 --verify=pattern \
        --verify_pattern=0x17 " #--runtime=20"     
        
        CMD=[CMD1]   
        
        FIOcmdWithPyPlot = self.FIOcmdWithPyPlot_(self)
        
        averageBwList = FIOcmdWithPyPlot.RunFIOcmdWithConsoleOutAndPyplot(CMDlist = CMD, maxPlot=20, printInfo=True)
        self.Print("%s"%averageBwList)
        
        #self.RunFIOcmdWithConsoleOutAndPyplot(CMD)
        
        '''

        
        t = threading.Thread(target = self.RunFIOcmdWithConsoleOut, args=(CMD,))
        t.start()                 

        self.DrawFIO("./bwOut_bw.log")
        
        t.join(2)
        '''

        self.Print("hello test1")
        sleep(5)
        
        
        
        
        
        
        
        '''
        cdw12=self.MaxNLBofCDW12()        
        oct_val=oct(0x3A)[-3:]
        nsid=1; cdw10=0; cdw11 =0
        totalByte=(cdw12+1)*512
        count=(cdw12+1)
        self.timer.start()
        mStr=self.shell_cmd("dd if=/dev/zero bs=512 count=%s 2>&1   |tr \\\\000 \\\\%s 2>/dev/null |nvme io-passthru %s -o 0x1 -n %s -l %s -w --cdw10=%s --cdw11=%s --cdw12=%s 2>&1"%(count, oct_val, self.dev, nsid, totalByte,cdw10, cdw11, cdw12))
        self.timer.stop()
        self.Print("time = %s, msg %s, cdw12 %s"%(self.timer.time, mStr, cdw12), "f")
        '''
                
        return ret_code
    '''
    def SubCase2(self):
        ret_code=1
        cdw12=0       
        oct_val=oct(0xBC)[-3:]
        nsid=1; cdw10=0; cdw11 =0
        totalByte=(cdw12+1)*512
        count=(cdw12+1)
        self.timer.start()
        mStr=self.shell_cmd("dd if=/dev/zero bs=512 count=%s 2>&1   |tr \\\\000 \\\\%s 2>/dev/null |nvme io-passthru %s -o 0x1 -n %s -l %s -w --cdw10=%s --cdw11=%s --cdw12=%s 2>&1"%(count, oct_val, self.dev, nsid, totalByte,cdw10, cdw11, cdw12))
        self.timer.stop()
        self.Print("time = %s, msg %s, cdw12 %s"%(self.timer.time, mStr, cdw12), "f")
                
        return ret_code
    '''
    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_PCIPowerStatus(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    