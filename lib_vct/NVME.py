'''
Created on Aug 3, 2018

@author: root
'''
import sys
import os
import threading
import math
import re
#import smi_comm
from time import sleep
from lib_vct.NVMECom import NVMECom
from lib_vct import ControllerRegister
from lib_vct import IdCtrl
from lib_vct import IdNs
from lib_vct.GetLog import GetLog
from lib_vct.Flow import Flow
import re

def foo1():
    print "foo!"
    
    
class NVME(object, NVMECom):
    
    
    @property
    def dev_alive(self):
        return self.dev_exist()    
    
    
    def __init__(self, argv):
        
        # self.dev = /dev/nvme0n1
        self.dev, self.TestModeOn =  self.ParserArgv(argv)
        # self.dev_port = /dev/nvme0
        self.dev_port=self.dev[0:self.dev.find("nvme")+5]
        # self.dev_ns = 1
        self.dev_ns=self.dev[-1:]
        
             
       
        
        # the start 1G start block, middle and last, 
        self.start_SB=0
        self.middle_SB=0
        self.last_SB=0
        
        if self.dev_alive:
            self.init_parameters()
            self.status="normal"
        else:
            self.Print("Error! Can't find device of %s"%self.dev, "f")
            self.Print( "Quit all the test items!", "f")
            sys.exit(1)            

    def init_parameters(self):
        self.set_NVMECom_par(self)
        self.CR = ControllerRegister.CR_()
        self.IdCtrl = IdCtrl.IdCtrl_()
        self.IdNs = IdNs.IdNs_()
        self.GetLog = GetLog.GetLog_(self)
        self.Flow=Flow.Flow_(self)
        
        self.pcie_port = self.shell_cmd(" udevadm info %s  |grep P: |cut -d '/' -f 5" %(self.dev_port))         
        self.bridge_port = "0000:" + self.shell_cmd("echo $(lspci -t | grep : |cut -c 8-9):$(lspci -t | grep $(echo %s | cut -c6- |sed 's/:/]----/g') |cut -d '-' -f 2)" %(self.pcie_port))
        self.CNTLID=self.IdCtrl.CNTLID.int 

        # get valume of ssd
        ncap=self.IdNs.NCAP.int
        # the start 1G start block
        self.start_SB=0
        # the middle 1G start block
        self.middle_SB=ncap/2-(1024*1024*2)
        # the last 1G start block
        self.last_SB=ncap-(1024*1024*2)
        
        self.MDTSinByte=int(math.pow(2, 12+self.CR.CAP.MPSMIN.int) * math.pow(2, self.IdCtrl.MDTS.int))
        self.MDTSinBlock=self.MDTSinByte/512
        
        # get System Bus (PCI Express) Registers, int format
        self.PMCAP, self.MSICAP, self.PXCAP, self.MSIXCAP, self.AERCAP=self.GetPCIERegBase()
        # Initiate Function Level Reset value        
        self.IFLRV= self.read_pcie(self.PXCAP, 0x9) + (1<<7)
        
    
    def read_pcie(self, base, offset):    
        # read pcie register, return byte data in int format       
        hex_str_addr=hex(base + offset)[2:]
        return int(self.shell_cmd("setpci -s %s %s.b " %(self.pcie_port, hex_str_addr)),16)
    def write_pcie(self, base, offset, value):    
        # write pcie register, ex. setpci -s 0000:02:00.0 79.b=A0    
        hex_str_addr=hex(base + offset)[2:]
        hex_str_value=hex(value)[2:]
        self.shell_cmd("setpci -s %s %s.b=%s " %(self.pcie_port, hex_str_addr, hex_str_value))
    

    def dev_exist(self, nsid=-1):
    #-- return boolean
    #-- default device=self.dev, ex. "/dev/nvme0n1
        DEV=self.dev_port+"n%s"%nsid
        if nsid==-1:
            DEV=self.dev
        buf=self.shell_cmd("find %s 2> /dev/null |grep %s " %(DEV,DEV))
        if not buf:
            return False
        else:
            return True
        

                
    def ns_exist(self, nsid):
    #-- check if name space exist or not 
    #-- return boolean
        buf=self.shell_cmd("nvme id-ns %s -n %s 2>&1 |grep INVALID_NS" %(self.dev_port,nsid))
        if buf:
            return False
        else:
            return True
        
   
    def DeleteNs(self, nsid):
    #-- Delete name space exist or not 
        self.shell_cmd("nvme delete-ns %s -n %s 2>&1 >/dev/null " %(self.dev_port,nsid))
        
    def CreateNs(self, SizeInBlock=2097152):
    #-- Create name space, default size = 1G
    #-- return created nsid
        SIB=SizeInBlock
        buf=self.shell_cmd("nvme create-ns %s -s %s -c %s -f 0 -d 0 -m 0 2>&1" %(self.dev_port, SIB, SIB))
        # create-ns: Success, created nsid:5
        mStr="created nsid:(\d+)"
        nsid=-1
        if re.search(mStr, buf):
            nsid=int(re.search(mStr, buf).group(1),16)    
        return nsid

        
        
    def AttachNs(self, nsid):
    #-- 
        self.shell_cmd("nvme attach-ns %s -n %s -c %s 2>&1 >/dev/null " %(self.dev_port,nsid, self.CNTLID))
    
    def DetachNs(self, nsid):
    #-- 
        self.shell_cmd("nvme detach-ns %s -n %s -c %s 2>&1 >/dev/null " %(self.dev_port,nsid, self.CNTLID))
    
    
    def get_CSAEL(self):
    #-- Get Log Page - Commands Supported and Effects Log
        return self.get_log(5,2048)
    
    def fio_write(self, offset, size, pattern, nsid=1):
        DEV=self.dev_port+"n%s"%nsid 
        return self.shell_cmd("fio --direct=1 --iodepth=16 --ioengine=libaio --bs=64k --rw=write --filename=%s --offset=%s --size=%s --name=mdata \
        --do_verify=0 --verify=pattern --verify_pattern=%s" %(DEV, offset, size, pattern))
    
    def fio_isequal(self, offset, size, pattern, nsid=1, fio_bs="64k"):
    #-- return boolean
        DEV=self.dev_port+"n%s"%nsid 
        msg =  self.shell_cmd("fio --direct=1 --iodepth=16 --ioengine=libaio --bs=%s --rw=read --filename=%s --offset=%s --size=%s --name=mdata \
        --do_verify=1 --verify=pattern --verify_pattern=%s 2>&1 >/dev/null | grep 'verify failed at file\|bad pattern block offset\| io_u error' " %(fio_bs, DEV, offset, size, pattern))

        ret=False
        if msg:
            ret=False
        else:
            ret=True
     
        return ret      
    

    def Identify_command(self):
        return self.get_reg("id-ctrl", "nn")
        
    def write_SML_data(self,pattern):    
    #-- write 1G into SSD at start, midde and last address    
        # write data for testing(start, middle, last)
        size="1M"
        self.fio_write(self.start_SB*512, size, pattern) 
        self.fio_write(self.middle_SB*512, size, pattern)
        self.fio_write(self.last_SB*512, size, pattern)
    
    # check  Logical Block Content Change
    def isequal_SML_data(self,pattern): 
    #-- check 1G data at start, midde and last address
        ret=False
        size="1M"
        if self.fio_isequal(self.start_SB*512,size, pattern):
            ret=True
        else:
            ret=False
            return ret 
                
        if self.fio_isequal(self.middle_SB*512,size, pattern):
            ret=True
        else:
            ret=False
            return ret 
            
        if self.fio_isequal(self.last_SB*512,size, pattern):
            ret=True
        else:
            ret=False
            return ret 
        return ret

    def set_feature(self, fid, value, SV=0, Data=None): 
    # feature id, value
    # if sv=1 and have data in
    # CMD = echo "\\255\\255\\255\\255\\255\\255" |nvme set-feature %s -f %s -n %s -v %s -s 2>&1
        
        CMD=""
        if Data!=None:
            CMD="echo -n -e \""+ Data + "\" | "
        
        CMD = CMD + "nvme set-feature %s -f %s -v %s " %(self.dev, fid, value)
        
        # feature is not namespace specific
        if fid!=0x10 and fid!=0x80 :
            CMD = CMD + "-n %s "%self.dev_ns
        
        if SV!=0:
            CMD = CMD + "-s "            
        CMD = CMD +"2>&1 "

        return self.shell_cmd(CMD)
    
        
     
    def get_feature(self, fid, cdw11=0, sel=0): 
    # feature id, cdw11(If applicable)
        return self.shell_cmd(" nvme get-feature %s -f %s --cdw11=%s -s %s 2>&1"%(self.dev, fid, cdw11, sel))

        
    def asynchronous_event_request(self): 
        # create thread for asynchronous_event_request_cmd        
        t = threading.Thread(target = self.asynchronous_event_request_cmd)
        t.start()        
        sleep(0.2)
        # raising critical waning
        # set Asynchronous Event Configuration (Feature Identifier 0Bh) bit0-7 to 1
        self.shell_cmd(" nvme set-feature %s -f 0xB -v 0xff"%(self.dev), 0.5)        
        # get log page and set 'Retain Asynchronous Event(RAE) = 0' 
        self.shell_cmd(" buf=$(nvme admin-passthru %s --opcode=0x2 -r --cdw10=0x2 -l 16 2>&1 >/dev/null)"%(self.dev), 0.5)         
        # Set TMPTH to 60 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 0)
        self.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x14D"%(self.dev), 0.5) 
        # Set TMPTH to 10 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 1)
        self.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x11B"%(self.dev), 0.5) 
        # Set TMPTH to 60 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 0)
        self.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x14D"%(self.dev), 0.5) 
        # get log page and set 'Retain Asynchronous Event(RAE) = 0' 
        self.shell_cmd(" buf=$(nvme admin-passthru %s --opcode=0x2 -r --cdw10=0x2 -l 16 2>&1 >/dev/null)"%(self.dev), 0.5)     
        # Set TMPTH to 10 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 1)
        self.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x11B"%(self.dev), 0.5)  
        # Set TMPTH to 60 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold (Critical warning = 0)
        self.shell_cmd(" nvme set-feature %s -f 0x4 -v 0x14D"%(self.dev), 0.5)           
              
        # wait thread finish
        t.join()        
        return 0          
     
    def asynchronous_event_request_cmd(self): 
        return self.shell_cmd("  buf=$(nvme admin-passthru %s --opcode=0xC 2>&1 >/dev/null)"%(self.dev))

    def device_self_test(self):
        return self.shell_cmd(" nvme admin-passthru %s --opcode=0x14 --namespace-id=0xffffffff --data-len=0 --cdw10=0x1 -r -s 2>&1 > /dev/null"%(self.dev))
    def nvme_format(self):
        return self.shell_cmd("  nvme format %s 2>&1 > /dev/null"%(self.dev))
    def sanitize(self):
        self.shell_cmd("  nvme sanitize %s -a 0x02 2>&1 > /dev/null"%(self.dev))    
        sleep(0.1)
        # wait for sanitize command complate
        while self.GetLog.SanitizeStatus.SPROG != 65535 :
            sleep(0.5)
        return 0
    def flush(self):
        self.fio_write(self.start_SB*512, "1M", "0x11") 
        self.shell_cmd(" buf=$( nvme flush %s -n 1 2>&1 > /dev/null)"%(self.dev)) 
        return 0
    def write(self):
        self.fio_write(self.start_SB*512, "1M", "0x11") 
        return 0  
    def read(self):
        self.fio_isequal(0, "1M", "0x19")
        return 0     
    def write_unc(self, SLB=0, BlockCnt=127):
        self.shell_cmd("  buf=$(nvme write-uncor %s -s %s -n %s -c %s 2>&1 > /dev/null) "%(self.dev, SLB, self.dev_ns, BlockCnt)) 
        return 0      
    def compare(self):
        self.shell_cmd("  buf=$(dd if=/dev/zero bs=512 count=1 2>&1 > /dev/null | nvme compare %s  -s 0 -z 51200 -c 99 2>&1 > /dev/null) "%(self.dev)) 
        return 0   
    def write_zero(self):
        self.shell_cmd("  buf=$(nvme write-zeroes %s -s 0 -c 1 2>&1 > /dev/null) "%(self.dev)) 
        return 0     
    def dsm_deallo(self):
        self.shell_cmd("  buf=$(nvme dsm %s -s 0 -b 1 -d 2>&1 >  /dev/null) "%(self.dev)) 
        return 0     

    def nvme_reset(self):
        self.status="reset"
        self.shell_cmd("  nvme reset %s "%(self.dev_port), 0.5) 
        self.status="normal"
        return 0     
    def subsystem_reset(self):
        self.status="reset"
        self.shell_cmd("  nvme subsystem-reset %s  "%(self.dev_port), 0.5) 
        self.shell_cmd("  rm -f %s* "%(self.dev_port))
        self.shell_cmd("  echo 1 > /sys/bus/pci/devices/%s/reset " %(self.pcie_port))  
        self.hot_reset() 
        self.status="normal"        
        return 0         
    def hot_reset(self):
        self.status="reset"
        self.shell_cmd("  echo 1 > /sys/bus/pci/devices/%s/remove " %(self.pcie_port), 0.5) 
        self.shell_cmd("  echo 1 > /sys/bus/pci/rescan ", 2)     
        self.status="normal"
        return 0         
    def link_reset(self):
        self.status="reset"
        self.shell_cmd("  setpci -s %s 3E.b=50 " %(self.bridge_port), 0.5) 
        self.shell_cmd("  setpci -s %s 3E.b=10 " %(self.bridge_port), 0.5) 
        self.shell_cmd("  echo 1 > /sys/bus/pci/devices/%s/reset " %(self.bridge_port), 0.5) 
        self.shell_cmd("  rm -f %s* "%(self.dev_port))
        #self.shell_cmd("  echo 1 > /sys/bus/pci/devices/%s/reset " %(self.pcie_port)) 
        self.hot_reset()
        self.status="normal"
        return 0  
    def FunctionLevel_reset(self):
        self.status="reset"        
        self.write_pcie(self.PXCAP, 0x9, self.IFLRV)
        sleep(0.2)
        self.shell_cmd("  rm -f %s* "%(self.dev_port))
        self.shell_cmd("  echo 1 > /sys/bus/pci/devices/%s/reset " %(self.pcie_port))  
        self.hot_reset() 
        self.status="normal"
        return 0      
        
    def por_reset(self):
        self.status="reset"
        self.shell_cmd("/usr/local/sbin/PWOnOff %s por off 2>&1 > /dev/null" %(self.dev_port), 0.1) 
        self.shell_cmd("/usr/local/sbin/PWOnOff %s por on 2>&1 > /dev/null" %(self.dev_port), 0.1) 
        self.status="normal"
        return 0            
    
    def spor_reset(self):
        self.status="reset"
        self.shell_cmd("/usr/local/sbin/PWOnOff %s spor off 2>&1 > /dev/null" %(self.dev_port), 0.1) 
        self.shell_cmd("/usr/local/sbin/PWOnOff %s spor on 2>&1 > /dev/null" %(self.dev_port), 0.1) 
        self.status="normal"
        return 0  
    
    def nvme_write_1_block(self, value, block, nsid=1):
        # write 1 block data, ex, nvme_write_1_block(0x32,0)
        # if csts.rdy=0, return false
        # value, value to write        
        # block, block to  write  
        '''
        oct_val=oct(value)[-3:]
        if self.dev_alive and self.status=="normal":
            self.shell_cmd("  buf=$(dd if=/dev/zero bs=512 count=1 2>&1   |tr \\\\000 \\\\%s 2>/dev/null | nvme write %s --start-block=%s --data-size=512 2>&1 > /dev/null) "%(oct_val, self.dev, block))   
        else:
            return False
        '''
        
        oct_val=oct(value)[-3:]
        #if self.dev_alive and self.status=="normal":  
        if self.dev_alive :                    
            slba=block
            cdw10=slba&0xFFFFFFFF
            cdw11=slba>>32    
            mStr=self.shell_cmd("dd if=/dev/zero bs=512 count=1 2>&1   |tr \\\\000 \\\\%s 2>/dev/null |nvme io-passthru %s -o 0x1 -n %s -l 512 -w --cdw10=%s --cdw11=%s 2>&1"%(oct_val, self.dev, nsid, cdw10, cdw11))
            #retCommandSueess=bool(re.search("NVMe command result:00000000", mStr))
            '''
            retCommandSueess=bool(re.search("ABORT_REQ", mStr))          
            if retCommandSueess==True:
                print "%s, abort at block %s" %(mStr,block)
            '''
        else:
            return False            
            
        
        return True   
    def nvme_write_blocks(self, value, sb, nob):
        # value, value to write        
        # sb, start block   
        # nob, number of block to write
        # ex, sb=0, nob=4, write 0, 1, 2, 3 blocks
        i=0
        while i<nob: 
            if self.nvme_write_1_block(value, sb+i):
                i=i+1
        
    def nvme_write_multi_thread(self, thread, sbk, bkperthr,value):
        #ex, nvme_write_multi_thread(2, 100, 200, 0x54)
        # thread0 write 200 blocks from 100th block
        # thread1 write 200 blocks from 300th block
        # total write (thread x  bkperthr)=2 x 200=400 blocks from 100th block to 500th block
        # ---------------------------------------
        # thread,  number of threads 
        # sbl,  start block 
        # bkperthr,  block per threads 
        # value,  value to write
        # ---------------------------------------
        # return thread can using following statement to check if all process is finished or not in main program
        #    mThreads=nvme_write_multi_thread(2, 100, 200, 0x54)
        #    for process in mThreads:
        #        process.join()  
        
        thread_w=thread
        block_w=bkperthr             
        RetThreads = []        
        for i in range(thread_w):                
            t = threading.Thread(target = self.nvme_write_blocks, args=(value, sbk+block_w*i, block_w,))
            t.start() 
            RetThreads.append(t)     
        return RetThreads
    
        
    def GetAllLbaf(self):
    # return LBAF[[0, MS, LBADS, RP], [1, MS, LBADS, RP].. ,[15, MS, LBADS, RP]] , all value is interger
        buf=self.shell_cmd(" nvme id-ns %s 2>&1"%(self.dev))
        LBAFs=[]
        for i in range(16):
            #LBA Format Data Structure
            # LFDS = [LBA Format, MS, LBADS, RP]
            LFDS=[]
            MS=0
            LBADS=0
            RP=0      
            
            # get LFDS
            try:
                mStr="lbaf\s+%s\s.+ms:(\d+).+lbads:(\d+).+rp:(\d+)"%i
                if re.search(mStr, buf):
                    MS=int(re.search(mStr, buf).group(1))
                    LBADS=int(re.search(mStr, buf).group(2))
                    RP=int(re.search(mStr, buf).group(3))           
            except Exception as error:        
                print "Got exception at LBAF%s"%i   
             
            LFDS.extend([i, MS, LBADS, RP])
            LBAFs.append(LFDS)
        
        return LBAFs
    
    def ResetNS(self):
    # Reset all namespaces to namespace 1 and kill other namespaces"
        nn=self.IdCtrl.NN.int
        TNVMCAP=self.IdCtrl.TNVMCAP.int
        TotalBlocks=TNVMCAP/512
        
        for i in range(1, nn+1):        
            # delete NS
            #if self.ns_exist(i):
            self.DeleteNs(i)    
        self.shell_cmd("nvme reset %s"%self.dev_port)      
        # Create namespaces=1, and attach it
        i=1    
        sleep(0.2)
        CreatedNSID=self.CreateNs(TotalBlocks)        
        if CreatedNSID != i:
            print "create namespace error!"    
            return False  
        else:
            sleep(0.2)
            self.AttachNs(i)
            sleep(0.2)
            self.shell_cmd("  nvme reset %s " % (self.dev_port))
            return True     
               
    def CreateMultiNs(self):        
        # Create namespcaes form nsid 1 to nsid %MaxNs, size 1G, and attach to the controller
        # return MaxNs, ex, MaxNs=8, indicate the NS from 1 to 8
        # check if controller supports the Namespace Management and Namespace Attachment commands or not
        NsSupported=True if self.IdCtrl.OACS.bit(3)=="1" else False
        NN=self.IdCtrl.NN.int
        if NsSupported:
            #print "controller supports the Namespace Management and Namespace Attachment commands"            
            # set max test namespace <=8
            MaxNs=8 if NN>8 else NN
            print  "create namespcaes form nsid 1 to nsid %s, size 1G, and attach to the controller"%MaxNs       
            error=0            
            for i in range(1, NN+1):        
                # delete NS
                self.DeleteNs(i)    
            self.shell_cmd("nvme reset %s"%self.dev_port)           
            # Create namespaces, and attach it
            for i in range(1, MaxNs+1):
                sleep(0.2)
                CreatedNSID=self.CreateNs()        
                if CreatedNSID != i:
                    print "create namespace error!"    
                    error=1
                    break
                else:
                    sleep(0.2)
                    self.AttachNs(i)
                    sleep(0.2)            
                    self.shell_cmd("  nvme reset %s " % (self.dev_port))     
                    
            # if creat ns error          
            if error==1:
                self.Print(  "create namespcaes Fail, reset to namespaces 1" ,"w")
                self.ResetNS()
                MaxNs=1
 
            return MaxNs
    
    
# ==============================================================    
class DevWakeUpAllTheTime():
# make device wake up all the time
# issue compare command to make it wake up
# Usage:
#    DWUATT=DevWakeUpAllTheTime(mNVME)
#    DWUATT.Start()  
#    DWUATT.Stop()  

    def __init__(self, nvme):
        self._NVME = nvme
        self._Start = 0
        
    def _Compare(self):
        while self._Start == 1:
            self._NVME.shell_cmd("  buf=$(dd if=/dev/zero bs=512 count=1 2>&1 > /dev/null | nvme compare %s  -s 0 -z 51200 -c 99 2>&1 > /dev/null) "%(self._NVME.dev)) 
        
    def Start(self):
        self._Start = 1
        self._Thread = threading.Thread(target = self._Compare)  
        self._Thread.start() 
            
    def Stop(self):    
        self._Start = 0
        sleep(0.2)










    
    
    
    
    
    
    
    
    
