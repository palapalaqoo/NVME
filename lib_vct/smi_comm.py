#!/usr/bin/python

BIN_PATH="../bin"


import sys
import os
import time

sys.path.append(BIN_PATH)


def setup(result_dir):
    # cmd = "cp %s/libaio.so.1 /usr/lib64/" %(BIN_PATH)   # for baidu fio_v2.0.9
    # os.system(cmd)
    # cmd = "mkdir -p %s" %(result_dir)
    # os.system(cmd)
    # os.makedirs(result_dir)
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)


def get_test_environment(_env_path, startorend):
    cmd = "dmesg -T > %s/dmesg_%s.txt" %(_env_path,startorend)
    os.system(cmd)
    cmd = "cat /proc/cpuinfo > %s/cpu_%s.txt" %(_env_path,startorend)
    os.system(cmd)
    cmd = "cat /proc/meminfo > %s/mem_%s.txt" %(_env_path,startorend)
    os.system(cmd)
    cmd = "fdisk -l > %s/disk_%s.txt" %(_env_path,startorend)
    os.system(cmd)
    cmd = "dmidecode > %s/machine_%s.txt" %(_env_path,startorend)
    os.system(cmd)
    cmd = "lspci -i pci.ids > %s/pci_%s.txt" %(_env_path,startorend)
    os.system(cmd)
    cmd = "cat /var/log/messages > %s/log_%s.txt" %(_env_path,startorend)
    os.system(cmd)

def get_testscript_version(file, _version, _scriptname):
    cmd = "echo '%s ,version: %s' > %s/script_version" %(_scriptname, _version, file)
    send_cmd(cmd)


#####################################
# for log print
#####################################
def save_log():
    global _f_log
    # global _orig_stdout
    # _orig_stdout = sys.stdout
    _f_log = open('../result/script_stdout.txt', 'a')
    # sys.stdout = _f_log
    a=1

def close_log():
    global _f_log
    # global _orig_stdout
    # sys.stdout = _orig_stdout
    _f_log.close()
    b=2

def log_Print(log_type, message):
    _f_log = open('../result/script_stdout.txt', 'a')
    _f_log.write(message+"\n")
    _f_log.close()

    log_clr= ""
    log_end= "\033[0m"
    logType = log_type

    if log_type == "kmsg":
        log_clr =  "\033[01;31m"

    if log_type == "cmd":
        log_clr =  "\033[0;33m"

    if log_type == "debug":
        log_clr =  "\033[01;34m"

    if log_type == "warr":
        log_clr =  "\033[01;31m"

    if log_type == "pass":
        log_clr =  "\033[1;32m"

    if log_type == "fail":
        log_clr =  "\033[0;31m"

    if log_type == "info":
        log_clr =  "\033[0;36m"

    if log_type == "info_item":
        log_clr =  "\033[1;30;47m"

    if log_type == "info_title":
        log_clr =  "\033[1;37;44m"

    if log_type == "result":
        log_clr =  "\033[1;37;45m"

    print "%s %s\033[0m" %(log_clr, message)


def get_time_now():
    now = time.strftime("%Y%m%d-%H:%M:%S")
    return str(now)

def get_PID():
    return str(os.getpid())

def print_Kmsg(msg):
    cmd = "echo '[%s][%s][KMSG]%s' > /dev/kmsg" %(get_time_now(), get_PID(), msg)
    os.system(cmd)
    # print "\033[01;31m%s\033[0m" %(cmd)
    log_message = "%s" %(cmd)
    log_Print("kmsg", log_message) # lred

def print_Cmd(msg):                     # purple
    # print "\033[0;33m[%s][%s][CMD]%s\033[0m" %(get_time_now(), get_PID(), msg)
    log_message = "[%s][%s][CMD]%s" %(get_time_now(), get_PID(), msg)
    log_Print("cmd", log_message) 

def print_Debug(msg):                   # navy blue
    # print "\033[01;34m[%s][%s][DEBUG]%s\033[0m" %(get_time_now(), get_PID(), msg)
    log_message = "[%s][%s][DEBUG]%s" %(get_time_now(), get_PID(), msg)
    log_Print("debug", log_message) 

def print_Warr(msg):                    # lred
    # print "\033[01;31m[%s][%s]%s\033[0m" %(get_time_now(), get_PID(), msg)
    log_message = "[%s][%s]%s" %(get_time_now(), get_PID(), msg)
    log_Print("warr", log_message) 

def print_Pass(msg):                    # green
    # print "\033[1;32m[%s][%s]%s\033[0m" %(get_time_now(), get_PID(), msg)
    log_message = "[%s][%s]%s" %(get_time_now(), get_PID(), msg)
    log_Print("pass", log_message) 

def print_Fail(msg):                    # red
    # print "\033[0;31m[%s][%s]%s\033[0m" %(get_time_now(), get_PID(), msg)
    log_message = "[%s][%s]%s" %(get_time_now(), get_PID(), msg)
    log_Print("fail", log_message) 

def print_Info(msg):                    # cyan
    # print "\033[0;36m[%s][%s][INFO]%s\033[0m" %(get_time_now(), get_PID(), msg)
    log_message = "[%s][%s][INFO]%s" %(get_time_now(), get_PID(), msg)
    log_Print("info", log_message) 

def print_Info_item(msg):              # bg-gray,font-black
    # print "\033[1;30;47m[%s][%s]%s\033[0m" %(get_time_now(), get_PID(), msg)
    log_message = "[%s][%s]%s" %(get_time_now(), get_PID(), msg)
    log_Print("info_item", log_message) 

def print_Info_title(msg):              # bg-blue,font-white
    # print "\033[1;37;44m[%s][%s]---------- %s ----------\033[0m" %(get_time_now(), get_PID(), msg)
    log_message = "[%s][%s]---------- %s ----------" %(get_time_now(), get_PID(), msg)
    log_Print("info_title", log_message) 

def print_Result(msg):                  # bg-purple,font-white
    # print "\033[1;37;45m[%s][%s][RET]%s\033[0m" %(get_time_now(), get_PID(), msg)
    log_message = "[%s][%s][RET]%s" %(get_time_now(), get_PID(), msg)
    log_Print("result", log_message) 

def send_cmd(cmd):
    print_Cmd(cmd)
    os.system(cmd)


#####################################
# cmd: dd write/read | cp | cmp | rm  [NOT Yet]
#####################################
def cmp_2file(_srcfile, _destfile):
    cmd = "cmp %s %s" %(_srcfile, _destfile)
    print_Cmd(cmd)
    fd = os.popen(cmd)
    sReturn = fd.read().strip()
    fd.close()
    if sReturn.find("differ") > -1:
        print_Fail("Got differ: %s !" %(sReturn))
        return False
    if sReturn.find("EOF") > -1:
        print_Fail("Got EOF: %s !" %(sReturn))
        return False

    return True


#####################################
# kill test tool process (FIO, dd)
#####################################
def kill_ps_byName(psName):
    cmd = "ps -aux | grep %s | awk '{print $2}' | xargs kill -9" %(psName)
    send_cmd(cmd)


def kill_ps_FIO():
    cmd = "ps -aux | grep fio | awk '{print $2}' | xargs kill -9"
    send_cmd(cmd)


def kill_ps_dd():
    cmd = "ps -aux | grep dd | awk '{print $2}' | xargs kill -9"
    send_cmd(cmd)


def kill_ps_smi_ctrlPowerDev():
    cmd = "ps -aux | grep smi_ctrlPowerDev | awk '{print $2}' | xargs kill -9"
    send_cmd(cmd)

def chk_proc_fio():
    # filter message 1
    cmd = "ps -all | grep 'fio'"
    print_Cmd(cmd)
    fd = os.popen(cmd)
    sReturn = fd.read().strip()
    fd.close()
    if sReturn.find("fio") > -1:
        return False   

    return True


#####################################
# check dmesg message
#####################################
def chk_dmesg_got_err_msg():
    # filter message 1
    cmd = "dmesg -T | grep 'nvm'"
    print_Cmd(cmd)
    fd = os.popen(cmd)
    sReturn = fd.read().strip()
    fd.close()
    if sReturn.find("Buffer I/O error on dev lnvm") > -1:
        print_Warr("[dmesg]: %s" %(sReturn) )
        print_Fail("Buffer I/O error on dev lnvm.")
        return False
    if sReturn.find("command timeout") > -1:
        print_Fail("command timeout.")
        return False

    # filter message 2
    # cmd = "dmesg -T"
    # print_Cmd(cmd)
    # fd = os.popen(cmd)
    # sReturn = fd.read().strip()
    # fd.close()
    # if sReturn.find("Buffer I/O error on dev os") > -1:
    #     print_Warr("[dmesg]: %s" %(sReturn) )
    #     print_Fail("Buffer I/O error on dev os.")
    #     return False
    # if sReturn.find("Buffer I/O error on dev p0vol") > -1:
    #     print_Warr("[dmesg]: %s" %(sReturn) )
    #     print_Fail("Buffer I/O error on dev p0vol")
    #     return False
    # if sReturn.find("SMI-VCT TestScript failed!") > -1:
    #     print_Warr("[dmesg]: %s" %(sReturn) )
    #     print_Fail("SMI-VCT TestScript failed!")
    #     return False

    return True


#####################################
# for linux pcie_aspm 
#####################################
def set_pcie_aspm_policy(state):
    # [default] performance powersave powersupersave
    # $echo "performance" > /sys/module/pcie_aspm/parameters/policy
    # $echo "powersave" > /sys/module/pcie_aspm/parameters/policy
    # $echo "powersupersave" > /sys/module/pcie_aspm/parameters/policy
    cmd = "echo '%s' > /sys/module/pcie_aspm/parameters/policy" %(state)
    send_cmd(cmd)
    time.sleep(3)

def get_pcie_aspm_policy():
    # $cat /sys/module/pcie_aspm/parameters/policy
    cmd = "cat /sys/module/pcie_aspm/parameters/policy"
    send_cmd(cmd)
    time.sleep(1)

def get_pcie_aspm_policy_outFile(_outFile):
    # cat /sys/module/pcie_aspm/parameters/policy | awk -F '[' '{print $2}'| awk -F ']' '{print $1}'
    cmd = "cat /sys/module/pcie_aspm/parameters/policy | tee -a %s" %(_outFile)
    send_cmd(cmd)
    time.sleep(1)

def chk_get_pcie_aspm_policy():
    ret = False
    curr_ps_mode = 0
    fd = os.popen("cat /sys/module/pcie_aspm/parameters/policy | awk -F '[' '{print $2}'| awk -F ']' '{print $1}'")
    curr_aspm_policy = fd.read().strip()
    fd.close()
    print_Debug("curr_aspm_policy: %s." %(curr_aspm_policy))
    return curr_aspm_policy



