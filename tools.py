#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import python built-ins
import sys
# Import VCT modules
from lib_vct.NVME import NVME

class tools(NVME):
    ScriptName = "tools.py"
    Author = ""
    Version = ""
    
    def __init__(self, argv):
        self.SetDynamicArgs(optionName="k", optionNameFull="kernel number", \
                            helpMsg="kernel number to be boot"\
                            "\ne.x. '-k 0'", argType=int, default=65536)            
        # initial parent class
        super(tools, self).__init__(argv)
        
        self.paraK = self.GetDynamicArgs(0) 

    # define pretest, if not return 0 , skip all subcases
    def PreTest(self):        
        return 0            

    # <define sub item scripts>
    SubCase1TimeOut = 60
    SubCase1Desc = "list all boot kernel"   
    SubCase1KeyWord = ""
    def SubCase1(self):
        
        self.Print("current kernel")
        CMD = "uname -r"
        mStr = self.shell_cmd(CMD)
        self.Print(mStr, "f")        
        
        self.Print("current GRUB_DEFAULT must = saved")
        CMD = "grep GRUB_DEFAULT /etc/default/grub"
        mStr = self.shell_cmd(CMD)
        self.Print(mStr, "f")
        if mStr!="GRUB_DEFAULT=saved":
            self.Print("please using'vi /etc/default/grub' to make GRUB_DEFAULT=saved", "f")
        
                
        self.Print("current all kernel")
        CMD = "awk -F\\' '$1==\"menuentry \" {print $2}\' /etc/grub2.cfg" # cmd is  awk -F\' '$1=="menuentry " {print $2}' /etc/grub2.cfg
        mStr = self.shell_cmd(CMD)
        self.Print(mStr, "f")
        
        return 0

    SubCase2TimeOut = 60
    SubCase2Desc = "change default boot kernel"   
    SubCase2KeyWord = ""
    def SubCase2(self):
        if self.paraK==65536:
            self.Print("missing -k parameter", "f")
            return 1
        
        self.Print("current /boot/grub2/grubenv")
        CMD = "grep saved /boot/grub2/grubenv"
        mStr = self.shell_cmd(CMD)
        self.Print(mStr, "f")
                
        self.Print("set to %s"%self.paraK)
        CMD = "grub2-set-default %s"%self.paraK
        mStr = self.shell_cmd(CMD)
        self.Print(mStr, "f")
        
        self.Print("current /boot/grub2/grubenv")
        CMD = "grep saved /boot/grub2/grubenv"
        mStr = self.shell_cmd(CMD)
        self.Print(mStr, "f")
        
        
        self.Print("build your GRUB2 configuration(not uefi)")
        CMD = "grub2-mkconfig -o /boot/grub2/grub.cfg"
        mStr = self.shell_cmd(CMD)
        self.Print(mStr, "f")
        self.Print("build your GRUB2 configuration(uefi)")
        CMD = "grub2-mkconfig -o /boot/efi/EFI/centos/grub.cfg"
        mStr = self.shell_cmd(CMD)
        self.Print(mStr, "f")        
        return 0



    # </define sub item scripts>

    # define PostTest  
    def PostTest(self): 
        return True 


if __name__ == "__main__":
    DUT = tools(sys.argv ) 
    DUT.RunScript()
    DUT.Finish() 

    
    
    
    