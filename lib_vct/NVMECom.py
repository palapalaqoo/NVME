

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
        if gettype==0:
            return self.shell_cmd("nvme %s %s |grep %s |cut -d ':' -f 2 |sed 's/[^0-9a-zA-Z]*//g'" %(cmd, NVMECom.device, reg))[::-1]
        else:
            return self.shell_cmd("nvme %s %s |grep %s |cut -d ':' -f 2 |sed 's/[^0-9a-zA-Z]*//g'" %(cmd, NVMECom.device, reg))


















