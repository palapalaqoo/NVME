'''
Created on Jul 26, 2019

@author: root
'''
import re
import os
import sys
from time import sleep

def shell_cmd(cmd):
    #print to command log      
    fd = os.popen(cmd)
    msg = fd.read().strip()
    fd.close()
    return msg 

def isCMDExist(cmd):
    CMD= "command -v %s 2>&1 >/dev/null ; echo $?"%cmd
    if shell_cmd(CMD)=="0":
        return True
    else:
        return False  

#------------------------------------------------------------------------------------------------------------------------------------------
print "------------------------------------"   
package = "virsh"
print "check if QEMU/KVM(%s) was installed"%package
if not isCMDExist(package):
    print "Not install , Try to install package"   
    shell_cmd("sudo yum install -y qemu-kvm qemu-img virt-manager libvirt libvirt-python libvirt-client virt-install virt-viewer")
    sleep(0.5)
    if isCMDExist(package):
        print "Install success!"
    else:
        print "Install fail!" 
        sys.exit(1)
print "Installed!"
print "------------------------------------"   
#------------------------------------------------------------------------------------------------------------------------------------------
filePath = "/etc/libvirt/qemu.conf"
print "check if The user for QEMU processes run by the system instance is root in %s"%filePath
rt = shell_cmd("cat /etc/libvirt/qemu.conf |grep 'user = \"root\"'")
if re.search("^user = \"root\"", rt):
    print "Pass"
else:
    print "user is not root in %s"%filePath
    print "try to set user = \"root\" .."
    
    # read
    with open(filePath, 'r') as content_file:
        data = content_file.read()       
    
    # if find ^#user = \"root\", remove #
    if re.search("^#user = \"root\"", rt):
        data=data.replace("#user = \"root\"", "user = \"root\"") # remove #    
    else:   # add new line
        data=data+"\nuser = \"root\"\n"

    # write back
    with open(filePath, 'w') as mfile:
        mfile.writelines( data ) 
              
    # check again
    rt = shell_cmd("cat /etc/libvirt/qemu.conf |grep 'user = \"root\"'")
    if re.search("^user = \"root\"", rt):
        print "Success to set 'user = \"root\" in %s"%filePath
        print "restart libvirtd"
        shell_cmd("systemctl restart libvirtd")
    else:
        print "Fail to set 'user = \"root\" in %s"%filePath
        sys.exit(1)


if not isCMDExist(package):
    print "Not install , Try to install package"   
    shell_cmd("sudo yum install -y qemu-kvm qemu-img virt-manager libvirt libvirt-python libvirt-client virt-install virt-viewer")
    sleep(0.5)
    if isCMDExist(package):
        print "Install success!"
    else:
        print "Install fail!" 
        sys.exit(1)
print "Installed!"
print "------------------------------------"   

#------------------------------------------------------------------------------------------------------------------------------------------
package = "matplotlib"
print "check if module %s was installed"%package
try:
    __import__(package)
except ImportError:
    print "Not install , Try to install package"   
    shell_cmd("sudo yum install -y python2-matplotlib")
    sleep(0.5)
    try:
        __import__(package)
        print "Install success!"
    except ImportError:
        print "Install fail!" 
        sys.exit(1)
print "Installed!"        
print "------------------------------------"   
#------------------------------------------------------------------------------------------------------------------------------------------
package = "paramiko"
filePath = "SMI_SetUpResourcesZips"
print "check if module %s was installed"%package
try:
    __import__(package)
except ImportError:
    print "Not install , Try to install package"   
    shell_cmd("yum install -y python-devel.x86_64")
    shell_cmd("cd %s; tar -xzf pycrypto-2.6.tar.gz ; cd pycrypto-2.6 ; python setup.py install"%filePath)
    shell_cmd("cd %s; tar -xzf paramiko-1.14.0.tar.gz ; cd paramiko-1.14.0 ; python setup.py install"%filePath)
    shell_cmd("cd %s; tar -xzf ecdsa-0.11.tar.gz ; cd ecdsa-0.11 ; python setup.py install"%filePath)
    sleep(0.5)
    
    
    try:
        __import__(package)
        print "Install success!"
    except ImportError:
        print "Install fail!" 
        sys.exit(1)
print "Installed!"    
print "------------------------------------"   
#------------------------------------------------------------------------------------------------------------------------------------------
BootType=""
print "Check system booted as EFI/UEFI or BIOS"
if shell_cmd("[ -d /sys/firmware/efi ] && echo UEFI || echo BIOS")=="UEFI":
    print "Booted type: EFI/UEFI"
    BootType="UEFI"
else:
    print "Booted type: BIOS"
    BootType="BIOS"
print "------------------------------------"   

print "Check if intel_iommu=on"      
#if shell_cmd("dmesg | grep 'IOMMU enabled' 2>&1 >/dev/null; echo $?") =="0":
if shell_cmd("find /sys | grep dmar 2>&1 >/dev/null; echo $?") =="0":
    print "intel_iommu = on, pass!"
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


print "------------------------------------"    
print "Finish"    
sys.exit(0)
    
    
    
    