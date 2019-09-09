#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
from time import sleep
import re


# Import VCT modules
from lib_vct.NVME import NVME

class SMI_SetUp(NVME):
    ScriptName = "SMI_SetUp.py"
    Author = ""
    Version = ""
    
    def __init__(self, argv):
        # initial parent class
        super(SMI_SetUp, self).__init__(argv)
        self.Version=2 if sys.version_info[0] < 3 else 3

    # define pretest  
    def PreTest(self):        
        return True            

    # <define sub item scripts>
    SubCase1TimeOut = 60
    SubCase1Desc = "install QEMU/KVM"   
    SubCase1KeyWord = ""
    def SubCase1(self):
        ret_code=0
        package = "virsh"
        self.Print("check if QEMU/KVM was installed"%package)        
        if not self.isCMDExist(package):
            self.Print("Not install , Try to install package"   )
            self.shell_cmd("sudo yum install -y qemu-kvm qemu-img virt-manager libvirt libvirt-python libvirt-client virt-install virt-viewer")
            sleep(0.5)
            if self.isCMDExist(package):
                self.Print("Install success!")
            else:
                self.Print("Install fail!", "f" )
                ret_code=1
        else:
            self.Print("Installed!"        )
        
        self.Print("")
        self.Print("check if enable intel virtualization technology option in BIOS")
        mStr = self.shell_cmd("lsmod | grep kvm")  
        if re.search("kvm-intel", mStr):
            self.Print("Pass, enabled")
        else:
            self.Print("Fail, not enabled", "f")
            self.Print("Please enable intel virtualization technology in BIOS", "f")
            ret_code=1
            
        return ret_code
    
    SubCase2TimeOut = 60
    SubCase2Desc = "install matplotlib"       
    def SubCase2(self):
        ret_code=0
        package = "matplotlib"
        self.Print("check if module %s was installed"%package)
        try:
            __import__(package)
            self.Print("Installed!"                )
        except ImportError:
            self.Print("Not install , Try to install package"   )
            self.shell_cmd("sudo yum install -y python%s-matplotlib"%self.Version)
            sleep(0.5)
            try:
                __import__(package)
                self.Print("Install success!")
            except ImportError:
                self.Print("Install fail!" , "f")
                ret_code = 1

        return ret_code
    
    SubCase3TimeOut = 60
    SubCase3Desc = "install paramiko(ssh tool)"       
    def SubCase3(self):
        ret_code=0    
        package = "paramiko"
        self.Print("check if module %s was installed"%package)
        try:
            __import__(package)
            self.Print("Installed!"                )
        except ImportError:
            self.Print("Not install , Try to install package"   )
            '''
            self.shell_cmd("cd SMI_SetUpResources; tar -xzf pycrypto-2.6.tar.gz ; cd pycrypto-2.6 ; python setup.py install")
            self.shell_cmd("cd SMI_SetUpResources; tar -xzf paramiko-1.14.0.tar.gz ; cd paramiko-1.14.0 ; python setup.py install")
            self.shell_cmd("cd SMI_SetUpResources; tar -xzf ecdsa-0.11.tar.gz ; cd ecdsa-0.11 ; python setup.py install")
            '''
            self.shell_cmd("cd SMI_SetUpResources/pycrypto-2.6 ; python setup.py install")
            self.shell_cmd("cd SMI_SetUpResources/paramiko-1.14.0 ; python setup.py install")
            self.shell_cmd("cd SMI_SetUpResources/cd ecdsa-0.11 ; python setup.py install")            
            sleep(0.5)  
            try:
                __import__(package)
                self.Print("Install success!")
            except ImportError:
                self.Print("Install fail!" ,"f")
                ret_code=1

    
        return ret_code
    
    SubCase4TimeOut = 60
    SubCase4Desc = "check if intel_iommu=on"       
    def SubCase4(self):
        ret_code=0       
        
        BootType=""
        self.Print("Check system booted as EFI/UEFI or BIOS")
        if self.shell_cmd("[ -d /sys/firmware/efi ] && echo UEFI || echo BIOS")=="UEFI":
            self.Print("EFI/UEFI")
            BootType="UEFI"
        else:
            self.Print("BIOS")
            BootType="BIOS"
        
        self.Print("")
        self.Print("Check if intel_iommu=on"      )
        #if shell_cmd("dmesg | grep 'IOMMU enabled' 2>&1 >/dev/null; echo $?") =="0":
        if self.shell_cmd("find /sys | grep dmar 2>&1 >/dev/null; echo $?") =="0":
            self.Print("intel_iommu = on, pass!")
        else:
            self.Print("intel_iommu=off"    )
            self.Print("")
            self.Print("Start to set intel_iommu=on")
            # load file
            with open('/etc/default/grub', 'r') as file:
                # read a list of lines into data
                data = file.readlines()
            if data==None:
                self.Print("Can't find file: /etc/default/grub")
                sys.exit(1)
            
            #self.Print(data)
            # now change the line, note that you have to add a newline
            done = False
            lineNo=0
            for line in data:
                mStr="GRUB_CMDLINE_LINUX"
                # find line
                if re.search(mStr, line):                    
                    if re.search("\"(.*)\"", line):
                        parameters = re.search("\"(.*)\"", line).group(1)       
                                    
                        # if find old, then remove it                 
                        parameters = parameters.replace(" intel_iommu=on", "")
                        parameters = parameters.replace(" intel_iommu=off", "")                        
                        # add new string, ex GRUB_CMDLINE_LINUX="crashkernel=auto rd.lvm.lv=centos/root rd.lvm.lv=centos/swap rhgb quiet"
                        parameters_new = parameters + " intel_iommu=on"                        
                        # add prefix    
                        line="GRUB_CMDLINE_LINUX=\"%s\"\n"%parameters_new
                            
                        #write back to data
                        data[lineNo]=line
                        done=True                    
                lineNo=lineNo+1                    
            if done:
                # and write everything back
                with open('/etc/default/grub', 'w') as file:
                    file.writelines( data )    
            else:
                self.Print("Can't find string: GRUB_CMDLINE_LINUX")
                self.Print("ex GRUB_CMDLINE_LINUX=\"crashkernel=auto rd.lvm.lv=centos/root rd.lvm.lv=centos/swap rhgb quiet\"")
                sys.exit(1)        
                
            # set enable
            self.Print("")
            if BootType=="UEFI":
                TargetFile="/boot/efi/EFI/centos/grub.cfg"
            else:
                TargetFile="/boot/grub2/grub.cfg"
            self.Print("make config to file: %s"%TargetFile)
            self.shell_cmd("grub2-mkconfig -o %s"%TargetFile)       
            self.Print("system need to reboot for enable iommu!"        )
        
        return ret_code 
    
    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = SMI_SetUp(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    