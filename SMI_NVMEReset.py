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
import os
import ctypes
from random import randint
import fcntl
# Import VCT modules
from lib_vct.NVME import NVME

class SMI_NVMeReset(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_NVMeReset.py"
    Author = "Sam Chan"
    Version = "20210809"
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

       

    
    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

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
    
    def nvme_write(self, ns, slba, nlb, data):
        #define NVME_IOCTL_IO_CMD    _IOWR('N', 0x43, struct nvme_passthru_cmd)
        # NVME_IOCTL_IO_CMD = ioctl_opt.IOWR(ord('N'), 0x43, _nvme_passthru_cmd)
        NVME_IOCTL_IO_CMD = 0xC0484E43
    
        fd = os.open("/dev/nvme0", os.O_RDONLY)
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
    
    def initTestItems(self):
        # self.TestItems=[[description, function, supported],[description, function,supported],..]
        
        self.TestItems.append([self.ControllerReset, self.nvme_reset, True])
        
        if self.NSSRSupport:
            self.TestItems.append([self.NVMESubsystemReset, self.subsystem_reset, True])
        else:
            self.TestItems.append([self.NVMESubsystemReset, self.subsystem_reset, False])
            
        self.TestItems.append([self.PCIExpressHotReset, self.hot_reset, True])    
        
        self.TestItems.append([self.DataLinkDown, self.link_reset, True]) 
        
        self.TestItems.append([self.FunctionLevelReset, self.FunctionLevel_reset, True])
        
    def StartDstAndGetStatus(self, triggerFunc):
        self.Flow.DST.EventTriggeredMessage="Tool will trigger '%s' command as DST execution >= 1%% "%triggerFunc.__name__
        #print progress
        self.Flow.DST.ShowProgress=True   
        self.Flow.DST.ShowMessage=True
        # set DST command nsid
        self.Flow.DST.SetNSID(0xFFFFFFFF)#0x1
        # set DST type : 1= Short device self-test operation, 2= extended device self-test operation
        self.Print("Short device self-test operation, DST type : 1")
        self.Flow.DST.SetDstType(1)  
        # set Event
        self.Flow.DST.SetEventTrigger(triggerFunc)                   
        # set Threshold = 1 to raise event
        self.Flow.DST.SetEventTriggerThreshold(1)
            
        # start DST flow and get device self test status 
        DSTS=self.Flow.DST.Start() 
        return DSTS       
    
    def FindPatten(self, offset, size, SearchPatten):
        #return string, if no finding, return ""
        # example:       '00ba000 cdcd cdcd cdcd cdcd cdcd cdcd cdcd cdcd'  
        # SearchPatten = 0xcd, and return 0x00ba000
        find=""
        HexPatten = format(SearchPatten, '02x')
        buf=self.shell_cmd("hexdump %s -n %s -s %s 2>/dev/null"%(self.dev, size, offset,  )) 
        # example:       '00ba000 cdcd cdcd cdcd cdcd cdcd cdcd cdcd cdcd'  
        mStr="[^\n](\w*)%s"%((" "+HexPatten*2)*8)
        if re.search(mStr, buf):       
            find="0x"+re.search(mStr, buf).group(1)   
        return find 
     
    def nvme_reset_with_delay(self):
        sleep(0.1)
        self.nvme_reset()
        return 0                
    
    def GetTestItem(self, ResetType):
        rtResetType=None
        rtResetFunction=None
        rtResetSupport=False     
        for mItem in self.TestItems:  
            if mItem[0]==ResetType:
                rtResetType=mItem[0]
                rtResetFunction=mItem[1]
                rtResetSupport=mItem[2]
        return rtResetType, rtResetFunction, rtResetSupport
 
    
    def TestStopsProcessingAnyOutstandingAdminCommand(self, ResetType):
        self.Print("Reset type: %s"%( ResetType))
        self.Print ("Test if reset occur, controller stops processing any outstanding Admin command")
        self.Print ("Test if device self-test operation(admin command) was aborted due to the reset commands"  )
        self.Print ("")
        rtCode=0
        
        rtResetType, rtResetFunction, rtResetSupport=self.GetTestItem(ResetType) 
        
        if self.IdCtrl.OACS.bit(4)=="0":
            self.Print ("Controller does not support the DST operation, quit this test item!")
            return 0   
        elif not rtResetSupport:
            self.Print ("Controller does not support the %s, quit this test item!"%ResetType)
            return 0              
        else:
            # start DST, if DST progress>1, issue reset in reset_func, after DST finish, get status code
            DSTS=self.StartDstAndGetStatus(rtResetFunction)
            # check status code
            if DSTS!=-1:        
                # get bit 3:0        
                DSTSbit3to0 = DSTS & 0b00001111
                self.Print ("result of the device self-test operation from Get Log Page : %s" %hex(DSTSbit3to0))
                self.Print ("Check the result of the device self-test operation , expected result:  0x2(Operation was aborted by a Controller Level Reset)")
                if DSTSbit3to0==2:
                    self.Print("Reset type: %s, PASS"%(rtResetType), "p")
                else:
                    self.Print("Reset type: %s, Fail"%(rtResetType), "f")
                    

                    self.Print("")
                    self.Print("Issue command for Device Self-test Log with offset=0: ")
                    CMD = "nvme admin-passthru /dev/nvme0n1 --opcode=0x2 -r --cdw10=0x70006 --cdw11=0 --cdw12=0 --cdw13=0 -l 32 2>&1"
                    self.Print(CMD)
                    mStr = self.shell_cmd(CMD)
                    self.Print(mStr)

                    LogPageOffsetSupport = True if self.IdCtrl.LPA.bit(2)=="1" else False
                    if LogPageOffsetSupport:                    
                        self.Print("")
                        self.Print("Issue command for Device Self-test Log with offset=4: ")
                        CMD = "nvme admin-passthru /dev/nvme0n1 --opcode=0x2 -r --cdw10=0x60006 --cdw11=0 --cdw12=4 --cdw13=0 -l 28 2>&1"
                        self.Print(CMD)
                        mStr = self.shell_cmd(CMD)
                        self.Print(mStr)                    
                    
                    
                    
                    rtCode = 1                         
            else:
                self.Print ("Controller does not support the DST operation"     )
                     
            return rtCode
    
    
    def TestStopsProcessingAnyOutstandingIOCommand(self, ResetType):
        rtResetType, rtResetFunction, rtResetSupport=self.GetTestItem(ResetType) 
        self.Print("Reset type: %s"%( ResetType))
        self.Print ("Test if reset occur, controller stops processing any outstanding IO command")
        self.Print ("Test if write command was aborted due to the reset commands"  )
        self.Print ("")
        rtCode=0
        if not rtResetSupport:
            self.Print ("Controller does not support the %s, quit this test item!"%ResetType)
            return 0              
        else:     
            
            TestPatten=randint(1, 0xFF)
            thread_w=32 #5
            block_w=16 #1024
            total_byte_w=block_w*thread_w *512
            # write data for a reset test= total_byte_w to (total_byte_w*MaxLoopPerResetTest)
            MaxLoopPerResetTest = 100   
            MaxAddress= (total_byte_w*MaxLoopPerResetTest)
            self.Print ("Create %s thread to write data(%s) to controller from 0x0 to %s "%(thread_w, hex(TestPatten), hex(MaxAddress)  ))
            self.Print ("While data was writing, issue reset operation, if data is not matched by read command, then pass this test")            
            self.Print ("")

            LoopPass = False                
            FirstMissingAddr=0
                         
                        
            # start to write and test command was abort or not
            for i in range(MaxLoopPerResetTest):     
                
                StartBlockOffSet=(block_w*thread_w*i)
                StartAddrOffSet=StartBlockOffSet*512
                EndBlockOffSet=(block_w*thread_w*(i+1))
                EndAddrOffSet=EndBlockOffSet*512
            
                # clear SSD data to 0x0
                self.fio_write(StartAddrOffSet, total_byte_w, 0x0)                      
                
                # show progress
                mSuffix="addr: %s - %s"%(hex(StartAddrOffSet),  hex(EndAddrOffSet)    )
                self.PrintProgressBar(StartAddrOffSet, MaxAddress, prefix = 'Write area:',suffix=mSuffix, length = 50)
                
                # write data using multi thread
                mThreads = self.nvme_write_multi_thread(thread_w, StartBlockOffSet, block_w, TestPatten)
                
                # check if all process finished 
                reset_cnt=0
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
                        sleep(0.1)                                                                
                        rtResetFunction()
                        reset_cnt=reset_cnt+1                                
                        sleep(0.5)                                
                
                if not self.dev_alive:
                    rtCode=1
                    self.Print("Error! after reset, device is missing, quit test", "f")
                    print ""
                    return 1
             
                # if TestModeOn then print pattern, e.g. python SMI_NVMEReset.py /dev/nvme0n1 -t     
                if self.mTestModeOn:    
                    print ("==========================================")
                    print "reset_cnt: %s"%reset_cnt
                    print ("Byte = %s"%(hex(total_byte_w)) )
                    mStr = self.shell_cmd("hexdump %s -n %s -s %s "%(self.dev, total_byte_w, StartAddrOffSet))
                    print (mStr)  
                    print ("==========================================")           
                                     
                # if have 00 and TestPatten in flash, then pass the test(f_write TestPatten)
                SearchPatten=0
                find_00 = self.FindPatten(StartAddrOffSet, total_byte_w, SearchPatten)
                SearchPatten=TestPatten    
                find_patten = self.FindPatten(StartAddrOffSet, total_byte_w, SearchPatten)
                            
                # controller reset can't verify data integrity, so let data integrity test = pass
                # if (find_00 and find_patten) or reset_type_name==self.ControllerReset: then, finish for i in range(MaxLoopPerResetTest):
                if (find_00!="" and find_patten!="") :
                    FirstMissingAddr = find_00
                    LoopPass = True                             
                    break
                
            # <end of for i in range(MaxLoopPerResetTest)>                
            print ""
            if LoopPass :         
                self.Print("Pass, write command was aborted at %s"%FirstMissingAddr, "p")
            else:
                self.Print("Fail", "f")
                rtCode=1            
            self.Print("")
            
        #<end of if not rtResetSupport>           
        return rtCode         
    
    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def __init__(self, argv):
        # initial parent class
        super(SMI_NVMeReset, self).__init__(argv)
        
        # <Parameter>
        self.NSSRSupport=True if self.CR.CAP.NSSRS.int==1 else False
        self.TestItems=[]
        # </Parameter>      
        
        self.ControllerReset = "Controller Reset"
        self.NVMESubsystemReset = "NVM Subsystem Reset"
        self.PCIExpressHotReset = "PCI Express Hot reset"
        self.DataLinkDown = "Data Link Down"
        self.FunctionLevelReset = "Function Level Reset"
        
        
        self.initTestItems()
        
        
    # <sub item scripts> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    SubCase1TimeOut = 60
    SubCase1Desc = "Test The Admin Queue registers (AQA, ASQ, or ACQ)"  
    def SubCase1(self):  
        self.Print ("Test The Admin Queue registers (AQA, ASQ, or ACQ) are not reset as part of a controller reset")
        self.Print ("" )
        ret_code=0
        RDY = self.GetRDY()
        
        self.Print ("Check if CSTS.RDY is set to 1 before reset:")
        if RDY==1:
            self.Print("Pass")
        else:
            self.Print("Fail, exit sub case!", "f")
            ret_code=1
            return ret_code

                        
        AQA = self.CR.AQA.str    
        ASQ = self.CR.ASQ.str   
        ACQ = self.CR.ACQ.str    

        '''
        ++ nvme reset command time slot in seconds(reference)
        
        0.657428: nvme_setup_cmd: nvme0: qid=0, cmdid=19, nsid=0, flags=0x0, meta=0x0, cmd=(nvme_admin_delete_sq sqid=1)
        0.662209: nvme_setup_cmd: nvme0: qid=0, cmdid=21, nsid=0, flags=0x0, meta=0x0, cmd=(nvme_admin_delete_cq cqid=1)
        
        0.700230: nvme_setup_cmd: nvme0: qid=0, cmdid=28, nsid=0, flags=0x0, meta=0x0, cmd=(nvme_admin_create_cq cqid=1, qsize=255, cq_flags=0x3, irq_vector=1)
        0.701252: nvme_setup_cmd: nvme0: qid=0, cmdid=29, nsid=0, flags=0x0, meta=0x0, cmd=(nvme_admin_create_sq sqid=1, qsize=255, sq_flags=0x1, cqid=1)        
        '''
                      
        self.Print ("Issue NVME reset (Controller disable)"        )
        self.Print ("")
        # delay 0.1 prevent thred run before self.GetEN
        t = threading.Thread(target = self.nvme_reset_with_delay)
        t.start()
        
        self.Print ("Wait for CC.EN = 0")
        while True:
            if self.GetEN()==0: break
        
        self.Print ("CC.EN = 0 now, timer start here")
        self.timer.start("float")

        self.Print ("Wait for CSTS.RDY = 0")
        while True:
            if self.GetRDY()==0: break        
        
        self.Print ("CSTS.RDY = 0 now, timer stop here")
        T0 = self.timer.time
        self.Print ("time usage for CSTS.RDY to transition from ‘1’ to ‘0’ after CC.EN transitions from ‘1’ to ‘0’ is less then %s second"%format(T0, '.6f'))
        self.Print ("")
        
        self.Print ("Wait for CC.EN = 1")
        while True:
            if self.GetEN()==1: break     

        self.Print ("CC.EN = 1 now, timer start here")
        self.timer.start("float")
        
        #self.Print("CSTS.RDY = 0", "p")
        self.Print ("Wait for CSTS.RDY = 1")
        while True:
            if self.GetRDY()==1: break 
        
        self.Print ("CSTS.RDY = 1 now, timer stop here")
        T1 = self.timer.time
        self.Print ("time usage for CSTS.RDY to transition from ‘0’ to ‘1’ after CC.EN transitions from ‘0’ to ‘1’ is less then %s second"%format(T1, '.6f'))
        self.Print ("")
        
        sleep(1)
        TimeOut = self.CR.CAP.TO.int
        TimeOutInSecond = TimeOut*0.5
        self.Print ("ControllerRegister.CAP.Timeout (TO): %s, i.e. %s second"%(TimeOut, TimeOutInSecond))
        self.Print ("Check if time usage for CSTS.RDY is <= CAP.Timeout")
        if T0 > TimeOutInSecond or T1 > TimeOutInSecond:
            self.Print ("Fail", "f")
            ret_code=1
        else:
            self.Print ("Pass", "p")
                    
        
        t.join()
        self.Print ("")
        self.Print ("compare AQA, ASQ, ACQ after reset")
        self.Print ("before reset: AQA = %s" %(AQA))
        self.Print ("before reset: ASQ = %s" %(ASQ))
        self.Print ("before reset: ACQ = %s" %(ACQ))
        self.Print ("after reset: AQA = %s" %(self.CR.AQA.str))
        self.Print ("after reset: ASQ = %s" %(self.CR.ASQ.str))
        self.Print ("after reset: ACQ = %s" %(self.CR.ACQ.str))
        
        if AQA!=self.CR.AQA.str or ASQ!=self.CR.ASQ.str or ACQ!=self.CR.ACQ.str:
            self.Print("Fail", "f")
            ret_code=1
        else:
            self.Print("Pass", "p")        
        sleep(0.1)
        
        return ret_code
    
    SubCase2TimeOut = 60
    SubCase2Desc = "Test if all supported reset is working"    
    def SubCase2(self):
        self.Print ("Check if all supported reset is working"  )
        ret_code=0    

        self.Print ("")
        for mItem in self.TestItems:     
            reset_type_name=mItem[0]
            reset_func=mItem[1]
            reset_support= mItem[2]
            if not reset_support:
                self.Print("Controller does not support the %s" %reset_type_name)
            else:
                self.Print ("issue " + reset_type_name)
                self.Print ("Check if controller is working after reset")
                reset_func()
                sleep(0.5)
                if self.dev_alive:
                    self.Print("PASS", "p")
                else:
                    self.Print("FAIL, exit", "f")
                    ret_code = 1
                self.Print("")
                    
        return ret_code

    SubCase3TimeOut = 600
    SubCase3Desc = "Test if stop processing any outstanding Admin command - Controller Reset"        
    def SubCase3(self):        
        ret_code = self.TestStopsProcessingAnyOutstandingAdminCommand(self.ControllerReset)
        return ret_code
    
    SubCase4TimeOut = 600
    SubCase4Desc = "Test if stop processing any outstanding Admin command - NVME Subsystem Reset"        
    def SubCase4(self):        
        ret_code = self.TestStopsProcessingAnyOutstandingAdminCommand(self.NVMESubsystemReset)
        return ret_code    
    
    SubCase5TimeOut = 600
    SubCase5Desc = "Test if stop processing any outstanding Admin command - PCI Express Hot reset"        
    def SubCase5(self):        
        ret_code = self.TestStopsProcessingAnyOutstandingAdminCommand(self.PCIExpressHotReset)
        return ret_code
    
    SubCase6TimeOut = 600
    SubCase6Desc = "Test if stop processing any outstanding Admin command - Data Link Down"        
    def SubCase6(self):        
        ret_code = self.TestStopsProcessingAnyOutstandingAdminCommand(self.DataLinkDown)
        return ret_code    
    
    SubCase7TimeOut = 600
    SubCase7Desc = "Test if stop processing any outstanding Admin command - Function Level Reset"        
    def SubCase7(self):        
        ret_code = self.TestStopsProcessingAnyOutstandingAdminCommand(self.FunctionLevelReset)
        return ret_code    
    
    '''
    SubCase8TimeOut = 1200
    SubCase8Desc = "Test if stop processing any outstanding IO command - Controller Reset"        
    def SubCase8(self):        
        ret_code = self.TestStopsProcessingAnyOutstandingIOCommand(self.ControllerReset)
        return ret_code
    
    SubCase9TimeOut = 1200
    SubCase9Desc = "Test if stop processing any outstanding IO command - NVME Subsystem Reset"        
    def SubCase9(self):        
        ret_code = self.TestStopsProcessingAnyOutstandingIOCommand(self.NVMESubsystemReset)
        return ret_code    
    
    SubCase10TimeOut = 1200
    SubCase10Desc = "Test if stop processing any outstanding IO command - PCI Express Hot reset"        
    def SubCase10(self):        
        ret_code = self.TestStopsProcessingAnyOutstandingIOCommand(self.PCIExpressHotReset)
        return ret_code
    
    SubCase11TimeOut = 1200
    SubCase11Desc = "Test if stop processing any outstanding IO command - Data Link Down"        
    def SubCase11(self):        
        ret_code = self.TestStopsProcessingAnyOutstandingIOCommand(self.DataLinkDown)
        return ret_code    
    
    SubCase12TimeOut = 1200
    SubCase12Desc = "Test if stop processing any outstanding IO command - Function Level Reset"        
    def SubCase12(self):        
        ret_code = self.TestStopsProcessingAnyOutstandingIOCommand(self.FunctionLevelReset)
        return ret_code                  
    '''
    # </sub item scripts> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    
    
    
if __name__ == "__main__":
    DUT = SMI_NVMeReset(sys.argv )
    DUT.RunScript()
    DUT.Finish() 
    
    
    
    
    
