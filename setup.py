'''
Created on Jul 26, 2019

@author: root
'''
import re
import os
import sys

def shell_cmd(cmd):
    #print to command log      
    fd = os.popen(cmd)
    msg = fd.read().strip()
    fd.close()
    return msg 

BootType=""
print "Check system booted as EFI/UEFI or BIOS"
if shell_cmd("[ -d /sys/firmware/efi ] && echo UEFI || echo BIOS")=="UEFI":
    print "EFI/UEFI"
    BootType="UEFI"
else:
    print "BIOS"
    BootType="BIOS"

print ""
print "Check if intel_iommu=on"      
if shell_cmd("dmesg | grep 'IOMMU enabled' 2>&1 >/dev/null; echo $?") =="0":
    print "Pass!"
else:
    print "intel_iommu=off"    
    print ""
    print "Start to set intel_iommu=on"
    # load file
    with open('/etc/default/grub', 'r') as file:
        # read a list of lines into data
        data = file.readlines()
    if data==None:
        print "Can't find file: /etc/default/grub"
        sys.exit(1)
    
    #print data
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
        print "Can't find string: GRUB_CMDLINE_LINUX"
        print "ex GRUB_CMDLINE_LINUX=\"crashkernel=auto rd.lvm.lv=centos/root rd.lvm.lv=centos/swap rhgb quiet\""
        sys.exit(1)        
        
    # set enable
    print ""
    if BootType=="UEFI":
        TargetFile="/boot/efi/EFI/centos/grub.cfg"
    else:
        TargetFile="/boot/grub2/grub.cfg"
    print "make config to file: %s"%TargetFile
    shell_cmd("grub2-mkconfig -o %s"%TargetFile) 

        
        
    print "system need to reboot for enable iommu!"
    
    
sys.exit(0)
    
    
    
    