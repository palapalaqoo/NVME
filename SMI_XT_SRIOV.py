#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
from time import sleep
import re

# Import VCT modules
from lib_vct.NVME import NVME

class SMI_XT_SRIOV(NVME):
    ScriptName = "SMI_XT_SRIOV.py"
    Author = "Sam"
    Version = "20200226"
    
    
    def GetCurrentMaxHMB(self):
    # return none or interger
        HMB_filename = "/sys/module/nvme/parameters/max_host_mem_size_mb"
        if not self.isfileExist(HMB_filename):
            return None
        else:            
            return int(self.shell_cmd("cat %s"%HMB_filename) )
            
    def TestHMB(self, TargetMHMB):
        HLStr = self.UseStringStyle("max_host_mem_size_mb=%s"%TargetMHMB, fore="red")
        self.Print("1) Try to reload NVMe driver with %s"%HLStr)
        self.ReloadNVMeDriverWithSpecificParameter("max_host_mem_size_mb=%s"%TargetMHMB)
        CurrentMHMB = self.GetCurrentMaxHMB()
        if CurrentMHMB!=TargetMHMB:
            self.Print("Fail to set max_host_mem_size_mb=%s"%TargetMHMB, "f")
            return False
        self.Print("Success!", "p")    
        self.Print("") 
        
        self.Print("2) Check if device is still working after Reload NVMe driver ")
        if not self.ctrl_alive:
            self.Print("Device is missing", "f")
            return False      
        self.Print("Pass!", "p")         
        self.Print("") 
        
        self.Print("3) Enable all VF") 
        if not self.EnableAllVF(): return False        
        self.Print("") 
        
        self.Print("4) Disable all VF") 
        if not self.DisableAllVF(): return False
        self.Print("")        
        
        return True    
    def GetVFListCreatedByPF(self):
    # e.x. mList=[/dev/nvme1n1 , /dev/nvme2n1 ]
        mList=[]
        
        PFPort = self.GetPciePort(self.dev)
        # if created VF is nvme1n1 nvme2n1 ...
        if PFPort.find("nvme-subsys")==-1: 
            PF_PciePort=self.pcie_port
            # 0000:02:00.0, bus=0000, dev=02, func=00.0
            # get device bus and device number, remove function number
            PF_BusDeviceNum = PF_PciePort[:-5]
            # get nvme list all devices
            NvmeList=self.GetCurrentNvmeList()
            for device in NvmeList:
                Port = self.GetPciePort(device)                            
                BusDeviceNum = Port[:-5]
                # if not PF device and (bus and device num) is the same, than it is VF from PF
                if PF_BusDeviceNum==BusDeviceNum and device!=self.dev:
                    mList.append(device)           
        # if created VF is nvme0n1 nvme0n2 ...
        else:     
            # get nvme list all devices
            NvmeList=self.GetCurrentNvmeList()
            for device in NvmeList:
                Port = self.GetPciePort(device)  
                # if Port = nvme-subsys0 and not PF
                if Port == PFPort and device!=self.dev:
                    mList.append(device) 
        return mList

    def GetCurrentNvmeList(self):
        mStr=self.shell_cmd("nvme list")
        return re.findall("/dev/nvme\d+n\d+", mStr)
        
    # set vf, if success, set AllDevices where AllDevices[0] is PF, others is VF 
    def SetCurrentNumOfVF(self, value):
        value=int(value)
        #path="/sys/class/block/%s/device/device/sriov_numvfs"%self.dev[5:]
        path="/sys/bus/pci/devices/%s/sriov_numvfs"%self.pcie_port
        if self.isfileExist(path):
            if self.shell_cmd("echo %s > %s 2>&1  ; echo $?"%(value, path))!="0" :
                self.Print("command fail", "f"); return False
            else:
                if value!=0: 
                    # wait for os to create drive        
                    sleep(2)
                    # get VF list
                    self.VFDevices = self.GetVFListCreatedByPF()
                    # save to AllDevices
                    self.AllDevices = [self.dev] + self.VFDevices
                    self.Print("Check if linux os create %s NVMe device under folder /dev/"%value)
                    self.Print("Created VF drive:")
                    for Dev in self.VFDevices:
                        self.Print("        %s"%Dev)
                    if value==len(self.VFDevices):
                        self.Print("Pass","p")
                    else:
                        self.Print("Fail", "f"); return False
        else:
            self.Print("Can't find file: %s"%path, "f"); return False
        
        return True 
        
    def EnableAllVF(self):
        # enable all VF        
        self.Print("") 
        self.Print("Set all VF online (TotalVFs = %s)"%self.TotalVFs)
        if not self.SetCurrentNumOfVF(self.TotalVFs):
            self.Print("Create VF Fail, quit all", "f"); return False  
        else: 
            return True

    def DisableAllVF(self):
        # disable all VF        
        self.Print("Set all VF offline")
        if not self.SetCurrentNumOfVF(0):
            self.Print("Fail, quit all", "f"); return False
        else: 
            self.Print("Done", "p")
            return True 
    
    def __init__(self, argv):
        self.SetDynamicArgs(optionName="l", optionNameFull="loops", helpMsg="number of loops for cases", argType=int)
        # initial parent class
        super(SMI_XT_SRIOV, self).__init__(argv)

        self.loops = self.GetDynamicArgs(0)
        # set defalut loop =1   
        self.loops=1 if self.loops==None else self.loops        
        
        #check OS is isCentOS or Ubuntu
        self.isCentOS = True if self.shell_cmd("cat /etc/os-release |grep 'CentOS' 2>&1 >/dev/null; echo $?")=="0" else False
        self.isUbuntu = True if self.shell_cmd("cat /etc/os-release |grep 'Ubuntu' 2>&1 >/dev/null; echo $?")=="0" else False
        
        # device lists, first is PF, others is VF, e.g [self.dev ] + self.VFDevices[]
        self.AllDevices=list(self.dev)
        self.VFDevices=[]
        

            
            
    # define pretest  
    def PreTest(self):  
        self.Sysfs_SRIOV_Supported= True if self.GetCurrentNumOfVF()!=None else False
        if self.Sysfs_SRIOV_Supported:
            self.Print("Linux's sysfs support SRIOV: Yes")
        else:
            self.Print("Linux's sysfs support SRIOV: No, quit all", "w"); return False
                    
        self.TotalVFs = int(self.shell_cmd("cat /sys/bus/pci/devices/%s/sriov_totalvfs"%self.pcie_port))               
        self.Print("Check if TotalVFs of SR-IOV Virtualization Extended Capabilities Register(PCIe Capabilities Registers) is large then 0(SR-IOV supported)") 
        self.Print("TotalVFs: %s"%self.TotalVFs)
        if self.TotalVFs>0:
            self.Print("PCIe device support SR-IOV", "p")
        else:
            self.Print("PCIe device do not support SR-IOV, quit all", "w"); return False          
        
        self.Print("")
        nmuvfs = self.GetCurrentNumOfVF()
        self.Print("Current Num Of VF: %s"%nmuvfs, "p")   
               
              
        return True            

    # <define sub item scripts>
    SubCase1TimeOut = 1800
    SubCase1Desc = "Test Host Memory Buffer"   
    SubCase1KeyWord = ""
    def SubCase1(self):      
        ret_code=0
        
        self.Print("Check if crontroller support HMB or not (identify HMPRE >0)")
        if self.IdCtrl.HMPRE.int==0:
            self.Print("crontroller is not support HMB, quit", "w")
            return 255      
        self.Print("Crontroller support HMB feature", "p")  
        
        self.Print("Check if current linux kernel support HMB or not")
        MHMB = self.GetCurrentMaxHMB()
        if MHMB==None:
            self.Print("Kernel is not support HMB, please use linux kernel 4.13+", "w")
            return 255
        self.Print("Kernel support HMB feature", "p")
        self.Print("Current max_host_mem_size_mb: %s"%MHMB)      
           
        for i in range(self.loops):
            self.Print("")
            self.Print("-- Current Loop: %s, Total loop: %s"%(i, self.loops), "b")
            
            TargetMHMB=0
            if not self.TestHMB(TargetMHMB): return 1
            TargetMHMB=MHMB
            if not self.TestHMB(TargetMHMB): return 1       
                 
            

            
                                 
                
                
  
                
        
        return ret_code     
    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_XT_SRIOV(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    