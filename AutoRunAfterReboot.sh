#!/bin/sh
# set display valuable
export DISPLAY=:0
# run command
/usr/bin/gnome-terminal --maximize -- bash -c 'cd /home/root/sam/eclipse/NVME; python2.7 SMI_SRIOV.py /dev/nvme0n1 14 -l 2 -v 3  -r 14 -c 1; exec bash'

exit 0
