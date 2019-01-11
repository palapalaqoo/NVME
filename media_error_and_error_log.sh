#!/bin/bash
NOWT=$(date +"%Y-%m-%d_%H:%M:%S")
TO=60


NVME_PORT=$(echo $1 |sed -e 's/\/.*\///g' |cut -c -5 )

exit_code=0
echo -e "\033[32m===========================================================\033[0m"
echo -e "\033[32mmedia_error_and_error_log\033[0m"
echo -e "\033[32m===========================================================\033[0m"
echo

# Data Units Read test ------------------------------------------------------------------------

# set all "SMART / Health Critical Warnings" in "Asynchronous Event Configuration" to 1
nvme set-feature /dev/$NVME_PORT -f 0xB -v0xF



#-- 3 ---------------------------------------------------------------------------------------------
echo


media_error0=$(nvme smart-log /dev/$NVME_PORT |grep media_errors|cut -d ":" -f 2|sed 's/[^0-9]*//g')
num_err_log_entries0=$(nvme smart-log /dev/$NVME_PORT |grep num_err_log_entries|cut -d ":" -f 2|sed 's/[^0-9]*//g')
echo "Write Uncorrectable 8*512(4k align) bytes and read it"
LOG_BUF=$(nvme write-uncor /dev/$NVME_PORT -s 0 -n 1 -c 7)
LOG_BUF=$(nvme read /dev/"$NVME_PORT"n1 -s 0 -z 512 -c 0)

echo
echo "check 'Media and Data Integrity Errors'"
media_error1=$(nvme smart-log /dev/$NVME_PORT |grep media_errors|cut -d ":" -f 2|sed 's/[^0-9]*//g')
if (( $(($media_error0 + 1)) == $(($media_error1 + 0)) )); then    
    echo -e "\033[32mCheck 'Media and Data Integrity Errors': PASS! $media_error0 $media_error1  \033[0m"
else
    echo -e "\033[31mCheck 'Media and Data Integrity Errors': FAIL! $media_error0 $media_error1 \033[0m"
    exit_code=1
fi

echo
echo "check 'Number of Error Information Log Entries:'"
num_err_log_entries1=$(nvme smart-log /dev/$NVME_PORT |grep num_err_log_entries|cut -d ":" -f 2|sed 's/[^0-9]*//g')
if (( $(($num_err_log_entries0 + 1)) == $(($num_err_log_entries1 + 0)) )); then    
    echo -e "\033[32mCheck 'Number of Error Information Log Entries': PASS! $num_err_log_entries0 $num_err_log_entries1  \033[0m"
else
    echo -e "\033[31mCheck 'Number of Error Information Log Entries': FAIL! $num_err_log_entries0 $num_err_log_entries1 \033[0m"
    exit_code=1
fi






# clear uncorrectable
LOG_BUF=$(cat /dev/zero | nvme write /dev/"$NVME_PORT"n1 -s 0 -z 4K -c 7 2>&1 > /dev/null)




exit $exit_code