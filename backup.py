

import os
from time import sleep

class NVMECom(object):
    


def shell_cmd(cmd, sleep_time=0):
    fd = os.popen(cmd)
    msg = fd.read().strip()
    fd.close()
    sleep(sleep_time)
    return msg 

def get_reg(dev, cmd, reg, type=0):
#-- cmd = nvme command, show-regs, id-ctrl, id-ns
#-- reg = register keyword in nvme command
    if type==0:
        return shell_cmd("nvme %s %s |grep %s |cut -d ':' -f 2 |sed 's/[^0-9a-zA-Z]*//g'" %(cmd, dev, reg))[::-1]
    else:
        return shell_cmd("nvme %s %s |grep %s |cut -d ':' -f 2 |sed 's/[^0-9a-zA-Z]*//g'" %(cmd, dev, reg))

