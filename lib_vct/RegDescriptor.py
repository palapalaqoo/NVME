'''
Created on Aug 30, 2018

@author: root
'''

from lib_vct.NVMECom import NVMECom
class RegType(object):
    hex=0x0   # hex
    decimal=0x1     # decimal

class RegDescriptor(object,NVMECom):  
    
    def __init__(self, mcmd=None, mreg='var', bitStart=0, bitStop=65535,regType=RegType.hex, nsSpec=True, NVMEobj=None):
        self.device=NVMEobj.dev
        self.device_port=NVMEobj.dev[0:NVMEobj.dev.find("nvme")+5]        
        self.cmd = mcmd
        self.reg = mreg     
        self.bitstart = bitStart
        self.bitstop = bitStop+1
        # read value type, hex or dec, 
        # ex. MNTMT is decimal value in nvme command, so set regtype = decimal
        # if MNTMT = 12, and regtype = dec, then NVME.IdCtrl.MNTMT.int = 0x12, bingo!
        # if MNTMT = 12, and regtype = hex, then NVME.IdCtrl.MNTMT.int = 0xC, wrong value
        self.regtype=regType
        self.nsspec=nsSpec
    
    def get_reg(self, cmd, reg, gettype=0, nsSpec=True):
    #-- cmd = nvme command, show-regs, id-ctrl, id-ns
    #-- reg = register keyword in nvme command
    #-- gettype:
    #--     0:    string, ex. cc: 460001, return "100064"
    #--     1:    string, ex. cc: 460001, return "460001"
    #--     16:     int,  ex. lpa: 0xf,return 15
        if nsSpec:
            DEV=self.device
        else:
            DEV=self.device_port
        #DEV=self.device if cmd=="id-ns" else self.device_port
        mStr="nvme %s %s |grep '%s ' |cut -d ':' -f 2 |sed 's/[^0-9a-zA-Z]*//g'" %(cmd, DEV, reg)
        if gettype==0:
            return self.shell_cmd(mStr)[::-1]
        if gettype==1:
            return self.shell_cmd(mStr)
        elif gettype==16:
            return int(self.shell_cmd(mStr), 16)
    
    
    
    @property
    def str(self):
        hex_str=hex(self.int)[2:]
        return hex_str

    
    @property
    def int(self):
        mstr=self.get_reg(cmd=self.cmd, reg=self.reg, gettype=1, nsSpec=self.nsspec)
        if mstr=="":
            self.Print("Error read  %s %s"%(self.cmd, self.reg), "f")        
        if self.regtype==RegType.hex:         
            mstrint=int(mstr, 16)
        elif self.regtype==RegType.decimal:
            mstrint=int(mstr)
        totalbits=len(mstr)*4    
        totalbits = self.bitstop if self.bitstop>totalbits else totalbits
        bitstart_rev=totalbits-self.bitstop
        bitstop_rev=totalbits-self.bitstart
        mstrbin=format(mstrint, 'b').zfill(totalbits)[bitstart_rev : bitstop_rev]
        int_ret=int(mstrbin, 2)        
        return int_ret   

    def bit(self, *args):
    #-- return string
    #-- ex. Bit(7,0), return bit[7:0]
    #-- return string "00100011"  if self.ToStr = "0123" where byte[0] = 0x23, byte[1] = 0x01 (value = 0x0123), last_bit=7, first_bit=0
    #-- ex. Bit(7), return bit 7
        Len = len(args)
        if Len ==1:
            last_bit=args[0]
            first_bit=args[0]
        elif Len ==2:
            last_bit=args[0]
            first_bit=args[1]     
        else:
            return "0"      

        binstr = self.str_reverse(bin(self.int)[2:].zfill(16))        
        return self.str_reverse(binstr[first_bit:last_bit+1])
    
    def __str__(self, *args, **kwargs):      
        return self.ToStr
    