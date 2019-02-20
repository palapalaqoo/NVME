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

class SMI_NVMeReset(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_NVMeReset.py"
    Author = "Sam Chan"
    Version = "20190125"
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

       

    
    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    

    def mReset(self):
        


        CC= self.MemoryRegisterBaseAddress+0x14
        CChex=hex(CC)
        self.shell_cmd("devmem2 %s w 0x00460000"%CChex, 1)
        self.shell_cmd("  nvme reset %s "%(self.dev_port), 0.5) 


        
        return 0       

    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def __init__(self, argv):
        # initial parent class
        super(SMI_NVMeReset, self).__init__(argv)
        
        
    # <sub item scripts> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    SubCase1TimeOut = 60
    SubCase1Desc = "Test "  
    def SubCase1(self): 

        self.Print ("Test if reset occur, controller stops processing any outstanding IO command")
        self.Print ("Test if write command was aborted due to the reset commands"  )
        
        ret_code=0       
     
        # start to write and test command was abort or not
        patten=0x5A
        thread_w=10
        block_w=1024 
        total_byte_w=block_w*thread_w *512
        
        # clear SSD data to 0x0
        self.fio_write(0, total_byte_w, 0x0)        
        
        # write data using multy thread
        mThreads = self.nvme_write_multi_thread(thread_w, 0, block_w, patten)
        
        # check if all process finished 
        reset_cnt=0
        while True:        
            allfinished=1
            for process in mThreads:
                if process.is_alive():
                    allfinished=0
        
            # if all process finished then, quit while loop, else  send reset command
            if allfinished==1:        
                break
            else:
                #self.mReset()
                reset_cnt=reset_cnt+1
                sleep(0.5)
                        
        print  "send reset command %s times while writing data is in progress"%(reset_cnt)

                    
        return ret_code 


    # </sub item scripts> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    
    
    
if __name__ == "__main__":
    DUT = SMI_NVMeReset(sys.argv )
    DUT.RunScript()
    DUT.Finish() 
    
    
    
    
    
