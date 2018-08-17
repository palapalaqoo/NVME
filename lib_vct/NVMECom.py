

import os
from time import sleep

class NVMECom():   
    device="null"

    def set_NVME_dev(self, value):
        NVMECom.device=value


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
    #--     16:     hex,  ex. lpa: 0xf,return 15
        if gettype==0:
            return self.shell_cmd("nvme %s %s |grep %s |cut -d ':' -f 2 |sed 's/[^0-9a-zA-Z]*//g'" %(cmd, NVMECom.device, reg))[::-1]
        if gettype==1:
            return self.shell_cmd("nvme %s %s |grep %s |cut -d ':' -f 2 |sed 's/[^0-9a-zA-Z]*//g'" %(cmd, NVMECom.device, reg))
        elif gettype==16:
            return int(self.shell_cmd("nvme %s %s |grep %s |cut -d ':' -f 2 |sed 's/[^0-9a-zA-Z]*//g'" %(cmd, NVMECom.device, reg)), 16)

    def str_reverse(self, mstr):
        return mstr[::-1]
    def get_log(self, log_id, size):
    #-- return string byte[0]+byte[1]+byte[2]+ ...
    #-- ex. return string "0123" where byte[0] = 0x01, byte[1] = 0x23
    #-- size, size in bytes
        return self.shell_cmd(" nvme get-log %s --log-id=%s --log-len=%s -b |xxd|cut -d ':' -f 2|tr '\n' ' '|sed 's/[^0-9a-zA-Z]*//g'" %(NVMECom.device, log_id, size))

    def str2int(self, mstr):
    #-- return integer form string
    #-- ex. return intger 8976 if string = "0123" where byte[0] = 0x01, byte[1] = 0x23 (value = 0x2310)
        mstr0="".join(map(str.__add__, mstr[-2::-2] ,mstr[-1::-2]))
        return int(mstr0, 16)

    













