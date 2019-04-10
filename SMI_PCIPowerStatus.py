#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
import re
import threading
import time
from time import sleep
# Import VCT modules
from lib_vct.NVME import NVME

class SMI_PCIPowerStatus(NVME):
    ScriptName = "SMI_PCIPowerStatus.py"
    Author = "Sam Chan"
    Version = "20190410"
    
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
  

    # define pretest  
    def PreTeset(self):                
        return True            

    # <define sub item scripts>
    SubCase1TimeOut = 60
    SubCase1Desc = "Test Power State"   
    SubCase1KeyWord = ""
    def SubCase1(self):
        ret_code=0
        self.Print("")
        self.PS_init = self.GetPs()
        self.Print("Current power state : %s"%self.GetPs())        
        self.Print("")
        
        for mtest in self.TestItems:
            PS = mtest[0]
            name = mtest[1]
            supported = mtest[2]
            
            self.Print("Issue command to set power state = %s"%name)
            self.SetPS(PS)            
            readPS = self.GetPs()
            self.Print("Issue command to get power state = %s"%readPS)
            self.Print("")
            
            self.Print("Check if power state was changed to new state or not")
            if readPS!=PS:
                self.Print("Fail, can't change the power state of PCI, quit!","f")
                ret_code=1
                break
            else:
                self.Print("Pass","p")
            self.Print("")
                
                
        return ret_code
    
    SubCase2TimeOut = 60
    SubCase2Desc = "Test Runtime D3 Transitions"   
    SubCase2KeyWord = ""
    def SubCase2(self):
        ret_code=0
        NormalShutdownNotification = 1
        ShutdownProcessingComplete = 2
        
        self.Print("")
        RTD3R = self.IdCtrl.RTD3R.int
        RTD3E = self.IdCtrl.RTD3E.int
        RTD3Time = RTD3R + RTD3E

        SHN = self.GetSHN()
        self.Print("Shutdown Notification = %s"%hex(SHN))
        SHST = self.GetSHST()
        self.Print("Shutdown Status = %s"%hex(SHST))
        
        
        self.Print("RTD3R(RTD3 Resume Latency) : %s ( %s microseconds )"%(hex(RTD3R), RTD3R))
        self.Print("RTD3E(RTD3 Entry Latency) : %s ( %s microseconds )"%(hex(RTD3E), RTD3E))
        
        if RTD3E==0:
            self.Print("")
            self.Print("According to NVME spec, RTD3 Entry Latency is 0h, then the host should wait for a minimum of one second")
            self.Print("So, let RTD3E = 1 second")
            RTD3E=1000000
            
        self.Print("")
        #self.Print("Sum of RTD3R and RTD3E : %s microseconds"%hex(RTD3Time))
        #self.Print("")
               
        self.Print("====================================================")
        self.Print("====================================================")             

        RTD3E_done=0
        RTD3E_Start=0
        RTD3E_Stop=0
        StartT=time.time()
        Timeout=10
        
        self.Print("Start to test RTD3 Entry Latency, time out = %s s"%Timeout)
        self.Print("Measure the latency from the time CC.SHN is set to 01b until CC.SHST is set to 10b")  
        t = threading.Thread(target = self.thread_SetRTD3)
        t.start()     
             
        self.Print( "-----------------------------------------------------------------------------------")
        self.PrintAlignString("'Shutdown Notification'", "'Shutdown Status'", "'Time in seconds'")  
        while True:            
            SHN = self.GetSHN()
            SHST = self.GetSHST()       
              
            CurrentT=time.time()
            TimeDiv=CurrentT-StartT
            
            if SHN==NormalShutdownNotification:
                if RTD3E_Start==0:
                    RTD3E_Start=TimeDiv
            # if Shutdown processing complete, then break after several loops
            if SHST==ShutdownProcessingComplete:
                if RTD3E_Stop==0:
                    RTD3E_Stop=TimeDiv
                    RTD3E_done=1
            # if is in RTD3 Entry Latency, i.e. CC.SHN is set to 01b by host software until CC.SHST is set to 10b, then mark it
            if RTD3E_Start!=0 and RTD3E_Stop==0:
                self.PrintAlignString(S0=hex(SHN), S1=hex(SHST), S2=TimeDiv, PF="pass")  
            else:
                self.PrintAlignString(S0=hex(SHN), S1=hex(SHST), S2=TimeDiv ) 
            
            # acting for more several loops if finish test
            if RTD3E_done!=0:
                RTD3E_done=RTD3E_done+1
            if RTD3E_done==4:
                break
            
            # if timeout, then break
            if TimeDiv > Timeout:
                break
            sleep(0.001)
        self.Print( "-----------------------------------------------------------------------------------")
        
        if RTD3E_done!=0:
            RTD3E_TimeDiv = RTD3E_Stop - RTD3E_Start
            RTD3E_TimeDiv = RTD3E_TimeDiv*1000000
            self.Print("Measured RTD3 Entry Latency: %s microseconds(%s - %s)"%(RTD3E_TimeDiv, "{:.6f}".format(RTD3E_Stop), "{:.6f}".format(RTD3E_Start)))
            self.Print("")     
            self.Print("Check if meatured RTD3 Entry Latency is less then RTD3E(%s microseconds) reported by controller"%RTD3E)
            if RTD3E_TimeDiv<RTD3E:
                self.Print("Pass","p")
            else:
                self.Print("Fail","f")
                ret_code=1                
        else:
            self.Print("Fail, timeout","f")
            ret_code=1   
            return ret_code
        
        
        '''
        readPS = self.GetPs()
        self.Print("Issue command to get power state = %s"%readPS)
        self.Print("")        
        sleep(1)        
        readPS = self.GetPs()
        self.Print("Issue command to get power state = %s"%readPS)
        self.Print("")            
        '''
        self.Print("====================================================")
        self.Print("====================================================")
        self.Print("")
                
        sleep(2)
        RDY = self.GetRDY()
        self.Print("Current CSTS.RDY : %s"%RDY)

        
                      
            
        RTD3R_done=0
        self.Print("Start to test RTD3 Resume Latency")   
        self.Print("Measure the latency from the exit RTD3 command until the CSTS.RDY is set to 1 ")  
        t = threading.Thread(target = self.thread_ResetRTD3)
        StartT=time.time()
        t.start()    
        
        
        
        while True:
            '''
            #SHN = self.GetSHN()
            SHST = self.GetSHST()    
            print("SHN %s, SHST %s"%( SHN,     SHST))
            #self.GetRDY()
            if SHST!=2 and self.GetRDY()==1:
                CurrentT=time.time()
                RTD3R_done=1
                break            
            '''

            if self.GetRDY()==1:
                CurrentT=time.time()
                RTD3R_done=1
                break
            
            sleep(0.001)

        if RTD3R_done!=0:
            RTD3R_TimeDiv = CurrentT-StartT
            RTD3R_TimeDiv = RTD3R_TimeDiv*1000000
            self.Print("Meatured RTD3 Resume Latency: %s microseconds"%RTD3R_TimeDiv)
            self.Print("")     
            self.Print("Check if Meatured RTD3 Resume Latency is less then RTD3R(%s microseconds) reported by controller"%RTD3R)
            if RTD3R_TimeDiv<RTD3R:
                self.Print("Pass","p")
            else:
                self.Print("Fail","f")
                ret_code=1                
        else:
            self.Print("Fail, timeout","f")
            ret_code=1   
            return ret_code            


        '''
        sleep(1)
        self.Print("Start to reset")
        self.shell_cmd("echo -n 0000:01:00.0 > /sys/bus/pci/drivers/nvme/bind")
        self.shell_cmd("echo on > /sys/bus/pci/devices/0000:01:00.0/power/control")
        self.Print("Done")
        sleep(1)
        '''
        sleep(2)        
                
        return ret_code    

    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_PCIPowerStatus(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    