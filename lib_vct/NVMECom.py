

import os
from time import sleep
from argparse import ArgumentParser
import re

class NVMECom():   
    device="null"
    mTestModeOn=False

    def set_NVMECom_par(self, son):
        # set NVMECom parameters from subclass
        NVMECom.device=son.dev
        NVMECom.mTestModeOn=son.TestModeOn

    def shell_cmd(self, cmd, sleep_time=0):
        fd = os.popen(cmd)
        msg = fd.read().strip()
        fd.close()
        sleep(sleep_time)
        return msg 
    
    def get_reg(self, cmd, reg, gettype=0):
    #-- cmd = nvme command, show-regs, id-ctrl, id-ns
    #-- reg = register keyword in nvme command
    #-- gettype:
    #--     0:    string, ex. cc: 460001, return "100064"
    #--     1:    string, ex. cc: 460001, return "460001"
    #--     16:     int,  ex. lpa: 0xf,return 15
        if gettype==0:
            return self.shell_cmd("nvme %s %s |grep '%s ' |cut -d ':' -f 2 |sed 's/[^0-9a-zA-Z]*//g'" %(cmd, NVMECom.device, reg))[::-1]
        if gettype==1:
            return self.shell_cmd("nvme %s %s |grep '%s ' |cut -d ':' -f 2 |sed 's/[^0-9a-zA-Z]*//g'" %(cmd, NVMECom.device, reg))
        elif gettype==16:
            return int(self.shell_cmd("nvme %s %s |grep '%s ' |cut -d ':' -f 2 |sed 's/[^0-9a-zA-Z]*//g'" %(cmd, NVMECom.device, reg)), 16)

    def str_reverse(self, mstr):
        return mstr[::-1]
    def get_log(self, log_id, size):
    #-- return string byte[0]+byte[1]+byte[2]+ ...
    #-- ex. return string "0123" where byte[0] = 0x01, byte[1] = 0x23
    #-- size, size in bytes
        return  self.shell_cmd(" nvme get-log %s --log-id=%s --log-len=%s -b |xxd -ps |cut -d ':' -f 2|tr '\n' ' '|sed 's/[^0-9a-zA-Z]*//g'" %(NVMECom.device, log_id, size))

    def get_log2byte(self, log_id, size):
    #-- return list [ byte[0], byte[1], byte[2], ... ]
    #-- size, size in bytes
    #-- usage: mStr=get_log2byte(7, 512)=[01, 23, 45, 67, 89]
    #-- mStr[0]='01' , mStr[1]='23'  
        line = self.get_log(log_id, size)
        n=2
        return [line[i:i+n] for i in range(0, len(line), n)]       
    
    def get_log_passthru(self, LID, size, RAE=0, LSP=0, LPO=0):
    #-- return list [ byte[0], byte[1], byte[2], ... ]
    #-- size, size in bytes
    #-- usage: mStr=get_log2byte(7, 512)=[01, 23, 45, 67, 89]
    #-- mStr[0]='01' , mStr[1]='23'  
    #--RAE: Retain Asynchronous Event
    #--LSP: Log Specific Field
    #--LPO: Log Page Offset in byte
        NUMDL=int(size/4-1) & 0xFFFF
        NUMDU=int(size/4-1) >>16
        CDW10_int= (NUMDL<<16) + (RAE<<15) + (LSP <<8) + LID
        CDW10= '0x{:02x}'.format(CDW10_int)
        
        LPOL=LPO & 0xFFFFFFFF
        LPOU= LPO >> 32
        
        #cmd="nvme admin-passthru %s --opcode=0x2 -r --cdw10=0x007F0008 -l 512 2>&1 "%mNVME.dev
        cmd="nvme admin-passthru %s --opcode=0x2 -r --cdw10=%s --cdw11=%s --cdw12=%s --cdw13=%s -l %s 2>&1 "%(NVMECom.device, CDW10, NUMDU, LPOL, LPOU, size)
        mbuf=self.shell_cmd(cmd)
        line="0"
        # if command success
        if re.search("NVMe command result:00000000", mbuf):
            patten=re.findall("\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}\s\w{2}", mbuf)            
            patten1= ''.join(patten)
            line=patten1.replace(" ", "")
    
        # put patten in to list type
        n=2
        return [line[i:i+n] for i in range(0, len(line), n)]    
    
     
    def str2int(self, strin):
    #-- return integer form string
    #-- ex. return intger 8976 if string = "0123" where byte[0] = 0x01, byte[1] = 0x23 (value = 0x2310)
        #check if string is legal or not
        if strin=="":
            mstr="0"
            self.Print("Error: input string for function str2int() is null", "f")
        else:
            mstr=strin
        mstr0="".join(map(str.__add__, mstr[-2::-2] ,mstr[-1::-2]))
        return int(mstr0, 16)
    class color:
        BLACK   = '\033[30m'
        RED     = '\033[31m'
        GREEN   = '\033[32m'
        YELLOW  = '\033[33m'
        BLUE    = '\033[34m'
        MAGENTA = '\033[35m'
        CYAN    = '\033[36m'
        WHITE   = '\033[37m'
        RESET = '\033[0m'
    def Print(self, msg, mtype):
        # mtype
        # p/P: pass, print msg with green color
        # f/F: false, print msg with red color
        # w/W: warnning, print msg with yellow color
        # t/T: test mode, will not print anything
        
        if mtype=="p" or mtype=="P":    
            print  self.color.GREEN +"%s" %(msg)  +self.color.RESET
        elif mtype=="f" or mtype=="F":  
            print  self.color.RED +"%s" %(msg)  +self.color.RESET
        elif mtype=="w" or mtype=="W":  
            print  self.color.YELLOW +"%s" %(msg)  +self.color.RESET            
        elif mtype=="t" or mtype=="T":  
            if NVMECom.mTestModeOn:
                print  self.color.CYAN +"%s" %(msg)  +self.color.RESET
        else:
            print "%s" %(msg)
            

    def ParserArgv(self, argv):
        # argv[1]: device path
        # argv[2]: script test mode on
        parser = ArgumentParser()
        parser.add_argument("dev", help="device", type=str)
        parser.add_argument("-t", "--t", help="script test mode on", action="store_true")
        
        args = parser.parse_args()
        
        mDev=args.dev
        mTestModeOn=True if args.t else False
        
        return mDev, mTestModeOn
        
    def GetPCIERegBase(self):
        # System Bus (PCI Express) Registers base offset in int format
        PMCAP=0
        MSICAP=0
        MSIXCAP=0
        PXCAP=0
        AERCAP=0
        buf=self.shell_cmd("lspci -v -s %s" %(self.pcie_port))
        
        mStr="Capabilities: \[(.+?)\] Power Management"
        if re.search(mStr, buf):
            PMCAP=int(re.search(mStr, buf).group(1),16)
            
        mStr="Capabilities: \[(.+?)\] MSI"
        if re.search(mStr, buf):
            MSICAP=int(re.search(mStr, buf).group(1),16)
            
        mStr="Capabilities: \[(.+?)\] Express Endpoint"
        if re.search(mStr, buf):
            PXCAP=int(re.search(mStr, buf).group(1),16)
            
        mStr="Capabilities: \[(.+?)\] MSI-X"
        if re.search(mStr, buf):
            MSIXCAP=int(re.search(mStr, buf).group(1),16)
            
        mStr="Capabilities: \[(.+?)\] Advanced Error Reporting"
        if re.search(mStr, buf):
            AERCAP=int(re.search(mStr, buf).group(1),16)        

        return PMCAP, MSICAP, PXCAP, MSIXCAP, AERCAP










