#!/usr/bin/env python


import sys
import os
import thread

from lib_vct import NVME

ret_code=0
def verify(func,args=""):
        
        mNVME.write_SML_data("0x55")        
        ncap=mNVME.IdNs.NCAP
        nn=mNVME.IdCtrl.NN
        cap=mNVME.CR.CAP
        funcname=str(func)
        funcname=funcname[funcname.find("NVME_VCT.")+9:funcname.find("of")]        
        
        # check if opcode is supported
        if CSUPP==0:
            print "%s is not supported" %(funcname)
            return 1
            
        
        func(*args)
        
        passtest = 1
        # if LBCC=0 and data no change or LBCC=1 and data changed(XOR)
        if (LBCC==0) == mNVME.isequal_SML_data("0x55"):
            pass
        else:
            passtest = 0
        # if NCC=0 and ncap is equal to last value or NCC=1 and ncap is changed
        if (NCC==0) == (ncap==mNVME.IdNs.NCAP):
            pass
        else:
            passtest = 0       

        if (NIC==0) == (nn==mNVME.IdCtrl.NN):
            pass
        else:
            passtest = 0           
        
        if (CCC==0) == (cap==mNVME.CR.CAP):
            pass
        else:
            passtest = 0
        
        # print test command name and pass/fail     
        #print "func = %s" %(func)            
        print "test %s" %(funcname)        
        if (passtest==1):
            print  "\033[32m PASS! \033[0m"  
        else:
            print  "\033[31m FAIL! \033[0m"   
            ret_code = 1                 


# check device parameter
if len(sys.argv) == 1:
    print "Error! please input device"
    sys.exit(-1)
    
 
mNVME = NVME.NVME_VCT(sys.argv[1] )
if mNVME.dev_alive:
    print "device alive"
else:    
    print "device missing"
    sys.exit(-1)


#-- Get Log Page - Commands Supported and Effects Log
mCSAEL=mNVME.get_CSAEL()

for i in range(0,0x200): # 0 to 0xC0=admin command in spec
    mstruct=mCSAEL[i*8:(i+1)*8]
    #print "%s: %s" %(i,mstruct)
    
    buf=mstruct[1]+mstruct[0]+mstruct[3]+mstruct[2]+mstruct[5]+mstruct[4]+mstruct[7]+mstruct[6]
    mstruct=buf
    
    CSUPP = 1 if (int(mstruct[0]) & 0b0001)>=1 else 0
    LBCC = 1 if(int(mstruct[0]) & 0b0010)>=1 else 0
    NCC =1 if(int(mstruct[0]) & 0b0100)>=1 else 0
    NIC = 1 if(int(mstruct[0]) & 0b1000)>=1 else 0
    CCC = 1 if(int(mstruct[1]) & 0b0001)>=1 else 0
    CSE = 1 if(int(mstruct[4]) & 0b0111)>=1 else 0
    
    
    #print "%s: %s" %(i,mstruct)
    #print "%s: %s: %s: %s :%s: %s: %s" %(i,CSUPP,LBCC,NCC,NIC,CCC,CSE)
    if i == 0:      # Delete I/O Submission Queue
        donothing=0
        
    elif i == 1:    # Create I/O Submission Queue
        donothing=0
    elif i == 2:   # Get Log Page      
        verify(mNVME.get_log, ("3", "16"))
    elif i == 4:    # Delete I/O Completion Queue
        donothing=0  
    elif i == 5:    # Create I/O Completion Queue
        donothing=0          
    elif i == 6:   # Identify    
        verify(mNVME.Identify_command)      
    elif i == 8:    # Abort
        donothing=0              
    elif i == 9:   # Set Features    
        verify(mNVME.set_feature, ("2", "0x1"))      
    elif i == 0xA:    # Get Features
        verify(mNVME.get_feature, ("2", "0"))    
       
    elif i == 0xC:    # Asynchronous Event Request
        verify(mNVME.asynchronous_event_request)     
       
    elif i == 0xD:    # Namespace Management
        donothing=0
    elif i == 0x10:    # Firmware Commit
        donothing=0
    elif i == 0x11:    # Firmware Image Download
        donothing=0     
    elif i == 0x14:    # Device Self-test
        verify(mNVME.device_self_test)
    elif i == 0x15:    # Namespace Attachment
        donothing=0
    elif i == 0x18:    # Keep Alive
        donothing=0
    elif i == 0x19:    # Directive Send
        donothing=0                   
    elif i == 0x1A:    # Directive Receive
        donothing=0
    elif i == 0x1C:    # Virtualization Management
        donothing=0
    elif i == 0x1D:    # NVMe-MI Send
        donothing=0
    elif i == 0x1E:    # NVMe-MI Receive
        donothing=0       
    elif i == 0x7C:    # Doorbell Buffer Config
        donothing=0
    elif i == 0x7F:    # abort
        donothing=0 
    elif i == 0x80:    # format nvm
        verify(mNVME.nvme_format)
    elif i == 0x81:    # secure send
        donothing=0          
    elif i == 0x82:    # secure receive
        donothing=0    
    elif i == 0x84:    # sanitize
        verify(mNVME.sanitize)   
    #---------------------------------------------------- I/O command -------------------------------------------------------    
    elif i == 0x100:    # Flush
        verify(mNVME.flush)
    elif i == 0x101:    # write
        verify(mNVME.write)      
    elif i == 0x102:    # read
        verify(mNVME.read) 
    elif i == 0x104:    # write_unc
        verify(mNVME.write_unc) 
    elif i == 0x105:    # compare
        verify(mNVME.compare) 
    elif i == 0x108:    # write_zero
        verify(mNVME.write_zero)                
    elif i == 0x109:    # dsm_deallocate
        verify(mNVME.dsm_deallo) 
    elif i == 8:    # abort
        donothing=0
    elif i == 8:    # abort
        donothing=0
    elif i == 8:    # abort
        donothing=0       
    elif i == 8:    # abort
        donothing=0
    elif i == 8:    # abort
        donothing=0
    elif i == 8:    # abort
        donothing=0
    else:    # abort
        donothing=0  


sys.exit(ret_code)
















