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
import subprocess
# Import VCT modules
from lib_vct.NVME import NVME

class SMI_SmartHealthLog(NVME):
    # Script infomation >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ScriptName = "SMI_DSM.py"
    Author = "Sam Chan"
    Version = "20181211"
    # </Script infomation> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    # <Attributes> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
  

    # </Attributes> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # <Function> >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    
    
    # </Function> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def __init__(self, argv):
        # initial parent class
        super(SMI_SmartHealthLog, self).__init__(argv)
        
        
    # <sub item scripts>
    SubCase1TimeOut = 60
    SubCase1Desc = "Test critical warnings"        
    def SubCase1(self):
        ret_code=0
        process = subprocess.Popen(["sh", "critical_warnings.sh", self.dev], stdout=subprocess.PIPE)       
        print process.communicate()[0]
        ret_code= process.returncode 

        return ret_code
        
    SubCase2TimeOut = 60
    SubCase2Desc = "Test data_units_read with read command"
    def SubCase2(self): 
        ret_code=0        
        
        data_units_read0=self.GetLog.SMART.DataUnitsRead
        self.Print("Issue get log command, data_units_read: %s"%data_units_read0)
                
        self.Print("Issue read command for 1000*512*1000 bytes")
        CMD="nvme read %s -s 0 -z 256000 -c 499  2>&1 >/dev/null "%self.dev
        for i in range(2000):            
            self.shell_cmd(CMD)


        data_units_read1=self.GetLog.SMART.DataUnitsRead
        self.Print("Issue get log command, data_units_read: %s"%data_units_read1)
                
        self.Print("Check if data_units_read has been changed(+1000)")
        
        if data_units_read1==(data_units_read0+1000):
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")    
            ret_code=1
            
        return ret_code

        
    SubCase3TimeOut = 60
    SubCase3Desc = "Test data_units_read with compare command"
    def SubCase3(self): 
        ret_code=0        
        
        data_units_read0=self.GetLog.SMART.DataUnitsRead
        self.Print("Issue get log command, data_units_read: %s"%data_units_read0)
                
        self.Print("Issue compare command for 1000*512*1000 bytes")
        CMD="dd if=/dev/zero bs=512 count=1 2>&1 > /dev/null | nvme compare %s  -s 0 -z 256000 -c 499 2>&1 > /dev/null"%self.dev
        for i in range(2000):            
            self.shell_cmd(CMD)


        data_units_read1=self.GetLog.SMART.DataUnitsRead
        self.Print("Issue get log command, data_units_read: %s"%data_units_read1)
                
        self.Print("Check if data_units_read has been changed(+1000)")
        
        if data_units_read1==(data_units_read0+1000):
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")    
            ret_code=1
            
        return ret_code

    SubCase4TimeOut = 60
    SubCase4Desc = "Test data_units_written with write command"
    def SubCase4(self): 
        ret_code=0        
        
        data_units_written0=self.GetLog.SMART.DataUnitsWritten
        self.Print("Issue get log command, data_units_written: %s"%data_units_written0)
                
        self.Print("Issue write command for 1000*512*1000 bytes")
        CMD="LOG_BUF=$(fio --direct=1 --iodepth=16 --ioengine=libaio --bs=32k --rw=write --numjobs=1 --size=$((1000*512*1000)) --offset=0 --filename=%s --name=mdata --do_verify=0 --verify=pattern --verify_pattern=0x00)"%self.dev
        self.shell_cmd(CMD)
        '''
        mThreads=self.nvme_write_multi_thread(10, 0, 1000, 0)
        for process in mThreads:
            process.join()
        '''

        data_units_written1=self.GetLog.SMART.DataUnitsWritten
        self.Print("Issue get log command, data_units_written: %s"%data_units_written1)
                
        self.Print("Check if data_units_written has been changed(+1000)")
        
        if data_units_written1==(data_units_written0+1000):
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")    
            ret_code=1
            
        return ret_code

    SubCase5TimeOut = 60
    SubCase5Desc = "Test data_units_written with Write Uncorrectable command"
    def SubCase5(self): 
        ret_code=0        
        
        data_units_written0=self.GetLog.SMART.DataUnitsWritten
        self.Print("Issue get log command, data_units_written: %s"%data_units_written0)
                
        self.Print("Issue Write Uncorrectable command for 512*1280bytes( > 512*1000 )")
        for i in range(10):
            #128*512byte
            CMD="LOG_BUF=$(nvme write-uncor %s -s 0 -n 1 -c 127 2>&1 > /dev/null)"%self.dev
            self.shell_cmd(CMD)
            
        data_units_written1=self.GetLog.SMART.DataUnitsWritten
        self.Print("Issue get log command, data_units_written: %s"%data_units_written1)
                
        self.Print("Check if data_units_written has been changed, expect no changed")
        
        if data_units_written1==data_units_written0:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")    
            ret_code=1
            
        self.Print("Clear write uncorrectable by writing zeros")
        self.nvme_write_blocks(0, 0, 128)
            
        return ret_code
        
    SubCase6TimeOut = 60
    SubCase6Desc = "Test host_read_commands and host_write_commands"
    def SubCase6(self): 
        ret_code=0        
        
        host_read_commands0=self.GetLog.SMART.HostReadCommands
        self.Print("Issue get log command, host_read_commands: %s"%host_read_commands0)
                
        self.Print("Issue read command ")
        CMD="nvme read %s -s 0 -z 256000 -c 499  2>&1 >/dev/null "%self.dev         
        self.shell_cmd(CMD)
            
        host_read_commands1=self.GetLog.SMART.HostReadCommands
        self.Print("Issue get log command, host_read_commands: %s"%host_read_commands1)
                
        self.Print("Check if host_read_commands has been changed, expect +1")
        
        if host_read_commands1==host_read_commands0+1:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")    
            ret_code=1
            
        self.Print("----------------------------------------")
        host_read_commands0=self.GetLog.SMART.HostReadCommands
        self.Print("Issue get log command, host_read_commands: %s"%host_read_commands0)
                
        self.Print("Issue compare command ")
        CMD="dd if=/dev/zero bs=512 count=1 2>&1 > /dev/null | nvme compare %s  -s 0 -z 256000 -c 499 2>&1 > /dev/null"%self.dev      
        self.shell_cmd(CMD)
            
        host_read_commands1=self.GetLog.SMART.HostReadCommands
        self.Print("Issue get log command, host_read_commands: %s"%host_read_commands1)
                
        self.Print("Check if host_read_commands has been changed, expect +1")
        
        if host_read_commands1==host_read_commands0+1:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")    
            ret_code=1

        self.Print("----------------------------------------")
        host_write_commands0=self.GetLog.SMART.HostWriteCommands
        self.Print("Issue get log command, host_write_commands: %s"%host_write_commands0)
                
        self.Print("Issue write command ")
        self.nvme_write_1_block(0, 1)
            
        host_write_commands1=self.GetLog.SMART.HostWriteCommands
        self.Print("Issue get log command, host_write_commands: %s"%host_write_commands1)
                
        self.Print("Check if host_write_commands has been changed, expect +1")
        
        if host_write_commands1==host_write_commands0+1:
            self.Print("Pass", "p")
        else:
            self.Print("Fail", "f")    
            ret_code=1          
                        
        return ret_code

        
    SubCase7TimeOut = 240
    SubCase7Desc = "Test controller busy time"
    def SubCase7(self): 
        ret_code=0
        process = subprocess.Popen(["sh", "controller_busy_time.sh", self.dev], stdout=subprocess.PIPE)       
        print process.communicate()[0]
        ret_code= process.returncode 

        return ret_code
    
    SubCase8TimeOut = 60
    SubCase8Desc = "Test media error and error log"
    def SubCase8(self): 
        ret_code=0
        process = subprocess.Popen(["sh", "media_error_and_error_log.sh", self.dev], stdout=subprocess.PIPE)       
        print process.communicate()[0]
        ret_code= process.returncode 

        return ret_code        
    # </sub item scripts>
    
    
    
    
if __name__ == "__main__":
    DUT = SMI_SmartHealthLog(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 
    
    
    
    
    
