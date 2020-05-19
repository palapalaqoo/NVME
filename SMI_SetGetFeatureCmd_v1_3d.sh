
#!/bin/sh

help(){
    echo "**********************************"
    echo "Ver: 1.0.0    Author:Sam         "
    echo "Date: 20180601"
    echo "**********************************"
    echo "Usage: $0 dev_name"
    echo "Example: $0 /dev/nvme0n1"
    exit 1
}
# if no option input
if [[ $# < 1 ]]; then
	#help
	exit 1
fi
# get input options
DEV_LIST=$1
# Check device path exist or not.
if [ -n "${DEV_LIST}" ];then
    for DEV in ${DEV_LIST};do
        DEV=`basename ${DEV}`
        dev_full_path=`find /dev/ -name ${DEV}`
        if [ `echo ${dev_full_path} | wc -w` -eq 0 ];then
            echo "${DEV}: no such device or partition"
            exit 1
        fi
    done
fi


#stdbuf -e 4096 -o 4096 ./SMI_SetGetFeatureCmd.py ${dev_full_path}
stdbuf -eL -oL python SMI_SetGetFeatureCmd.py ${dev_full_path} -v 1.3d
#echo ${dev_full_path}
