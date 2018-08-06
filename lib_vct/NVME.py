'''
Created on Aug 3, 2018

@author: root
'''
import sys
import os
import threading
import smi_comm
from time import sleep
from lib_vct import NVMECom
from lib_vct import ControllerRegister
from lib_vct import IdCtrl
from lib_vct import IdNs

def foo1():
    print "foo!"
    
    
class NVME_VCT():
    
    
    
    
    def __init__(self, dev):
        self.dev=dev
        self.dev_alive=False        
        self.chk_dev_exist()
        
        # the start 1G start block, middle and last, 
        self.start_SB=0
        self.middle_SB=0
        self.last_SB=0
        
        if self.dev_alive:
            self.init_parameters()
        
        

    def init_parameters(self):
        self.CR = ControllerRegister.CR_(self.dev)
        self.IdCtrl = IdCtrl.IdCtrl_(self.dev)
        self.IdNs = IdNs.IdNs_(self.dev)

        # get valume of ssd
        nuse=int(self.IdNs.NUSE,16)
        # the start 1G start block
        self.start_SB=0
        # the middle 1G start block
        self.middle_SB=nuse/2-(1024*1024*2)
        # the last 1G start block
        self.last_SB=nuse-(1024*1024*2)
        
        


    def chk_dev_exist(self):
    #-- return boolean
        fd = os.popen("find %s |grep %s" %(self.dev,self.dev))
        msg = fd.read().strip()
        fd.close()
        if not msg:
            self.dev_alive=False
        else:
            self.dev_alive=True

                

   



    

    
    
    def get_CSAEL(self):
    #-- Get Log Page - Commands Supported and Effects Log
        return self.get_log(5,2048)
    
    def fio_write(self, offset, size, pattern):
        return NVMECom.shell_cmd("fio --direct=1 --iodepth=16 --ioengine=libaio --bs=64k --rw=write --filename=%s --offset=%s --size=%s --name=mdata \
        --do_verify=0 --verify=pattern --verify_pattern=%s" %(self.dev, offset, size, pattern))
    
    def fio_isequal(self, offset, size, pattern):
    #-- return boolean
        msg =  NVMECom.shell_cmd("fio --direct=1 --iodepth=16 --ioengine=libaio --bs=64k --rw=read --filename=%s --offset=%s --size=%s --name=mdata \
        --do_verify=1 --verify=pattern --verify_pattern=%s 2>&1 >/dev/null | grep 'verify failed at file\|bad pattern block offset' " %(self.dev, offset, size, pattern))

        ret=False
        if msg:
            ret=False
        else:
            ret=True
     
        return ret      
    
    def get_log(self, log_id, size):
    #-- return string byte[0]+byte[1]+byte[2]+ ...
        return NVMECom.shell_cmd(" nvme get-log %s --log-id=%s --log-len=%s -b |xxd|cut -d ':' -f 2|tr '\n' ' '|sed 's/[^0-9a-zA-Z]*//g'" %(self.dev, log_id, size))
    
    def write_SML_data(self,pattern):    
    #-- write 1G into SSD at start, midde and last address    
        # write data for testing(start, middle, last)
        self.fio_write(self.start_SB*512, "1G", pattern) 
        self.fio_write(self.middle_SB*512, "1G", pattern)
        self.fio_write(self.last_SB*512, "1G", pattern)
    
    # check  Logical Block Content Change
    def isequal_SML_data(self,pattern): 
    #-- check 1G data at start, midde and last address
        ret=False
        if self.fio_isequal(self.start_SB*512,"1G", pattern):
            ret=True
        else:
            ret=False
            return ret 
                
        if self.fio_isequal(self.middle_SB*512,"1G", pattern):
            ret=True
        else:
            ret=False
            return ret 
            
        if self.fio_isequal(self.last_SB*512,"1G", pattern):
            ret=True
        else:
            ret=False
            return ret 
        return ret

    def set_feature(self, fid, value): 
    # feature id, value
        return NVMECom.shell_cmd(" nvme set-feature %s -f %s -v %s" %(self.dev, fid, value))
     
    def get_feature(self, fid, cdw11): 
    # feature id, cdw11(If applicable)
        return NVMECom.shell_cmd(" nvme get-feature %s -f %s --cdw11=%s"%(self.dev, fid, cdw11))

        
    def asynchronous_event_request(self): 
        # create thread for asynchronous_event_request_cmd        
        t = threading.Thread(target = self.asynchronous_event_request_cmd)
        t.start()        
        sleep(0.2)
        # raising critical waning
        # set Asynchronous Event Configuration (Feature Identifier 0Bh) bit0-7 to 1
        NVMECom.shell_cmd(" nvme set-feature %s -f 0xB -v 0xff"%(self.dev), 0.5)        
        # get log page and set 'Retain Asynchronous Event(RAE) = 0' 
        NVMECom.shell_cmd(" buf=$(nvme admin-passthru %s --opcode=0x2 -r --cdw10=0x2 -l 16 2>&1 >/dev/null)"%(self.dev), 0.5)         
        # Set TMPTH to 60 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 0)
        NVMECom.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x14D"%(self.dev), 0.5) 
        # Set TMPTH to 10 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 1)
        NVMECom.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x11B"%(self.dev), 0.5) 
        # Set TMPTH to 60 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 0)
        NVMECom.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x14D"%(self.dev), 0.5) 
        # get log page and set 'Retain Asynchronous Event(RAE) = 0' 
        NVMECom.shell_cmd(" buf=$(nvme admin-passthru %s --opcode=0x2 -r --cdw10=0x2 -l 16 2>&1 >/dev/null)"%(self.dev), 0.5)     
        # Set TMPTH to 10 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 1)
        NVMECom.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x11B"%(self.dev), 0.5)  
        # Set TMPTH to 60 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 0)
        NVMECom.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x14D"%(self.dev), 0.5)           
              
        # wait thread finish
        t.join()        
        return 0          
     
    def asynchronous_event_request_cmd(self): 
        return NVMECom.shell_cmd(" nvme admin-passthru %s --opcode=0xC"%(self.dev))

    def device_self_test(self):
        return NVMECom.shell_cmd(" nvme admin-passthru %s --opcode=0x14 --namespace-id=0xffffffff --data-len=0 --cdw10=0x1 -r -s 2>&1 > /dev/null"%(self.dev))
    def nvme_format(self):
        return NVMECom.shell_cmd("  nvme format %s 2>&1 > /dev/null"%(self.dev))
    def sanitize(self):
        NVMECom.shell_cmd("  nvme sanitize %s -a 0x02 2>&1 > /dev/null"%(self.dev))    
        sleep(0.1)
        # wait for sanitize command complate
        while self.get_log(0x81, 4)[0:2] != "ff" :
            sleep(0.1)
        return 0
    def flush(self):
        NVMECom.shell_cmd(" buf=$( nvme flash %s -n 1 /dev/null)"%(self.dev)) 
        return 0
    def write(self):
        self.fio_write(self.start_SB*512, "1M", "0x11") 
        return 0  
    def read(self):
        self.fio_isequal("1M", "0x19")
        return 0     
    def write_unc(self):
        NVMECom.shell_cmd("  buf=$(nvme write-uncor %s -s 0 -n 1 -c 127 2>&1 > /dev/null) "%(self.dev)) 
        return 0      
    def compare(self):
        NVMECom.shell_cmd("  buf=$(cat /dev/zero | nvme compare %s  -s 0 -z 51200 -c 99 2>&1 > /dev/null) "%(self.dev)) 
        return 0   
    def write_zero(self):
        NVMECom.shell_cmd("  buf=$(nvme write-zeroes %s -s 0 -c 1 2>&1 > /dev/null) "%(self.dev)) 
        return 0     
    def dsm_deallo(self):
        NVMECom.shell_cmd("  buf=$(nvme dsm %s -s 0 -b 0 -d > /dev/null) "%(self.dev)) 
        return 0     


    
    
       
    
