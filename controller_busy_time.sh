#!/bin/bash
NOWT=$(date +"%Y-%m-%d_%H:%M:%S")
TO=60


NVME_PORT=$(echo $1 |sed -e 's/\/.*\///g' |cut -c -5 )

exit_code=0
echo -e "\033[32m===========================================================\033[0m"
echo -e "\033[32mcontroller_busy_time\033[0m"
echo -e "\033[32m===========================================================\033[0m"
echo



echo "-- test controller_busy_time Feature(fio read), about 60s "
#-----------------------------------------------------------------------------------------------
# controller_busy_time
CBT0=$(nvme smart-log /dev/$NVME_PORT |grep "controller_busy_time" |cut -d ":" -f 2| cut -d "C" -f 1)
echo $NVME_PORT
# fio write data for 61s
LOG_BUF=$(fio --direct=1 --iodepth=1 --ioengine=libaio --bs=512 --rw=read --numjobs=1 --size=100G --offset=0 --filename=/dev/"$NVME_PORT"n1 --name=mdata --runtime=61)

CBT1=$(nvme smart-log /dev/$NVME_PORT |grep "controller_busy_time" |cut -d ":" -f 2| cut -d "C" -f 1)

echo $CBT0 $CBT1

# if CBT1 - CBT0 = 1S, or CBT1 - CBT0 = 2S
if (( $(($CBT0 + 1)) == $(($CBT1 + 0)) || $(($CBT0 + 2)) == $(($CBT1 + 0)) )); then    
    echo -e "\033[32mCheck controller_busy_time: PASS! \033[0m"
else
    echo -e "\033[31mCheck controller_busy_time: FAIL! $CBT0 $CBT1 \033[0m"
    exit_code=1
fi

echo "-- test controller_busy_time Feature(fio write), about 60s "
#-----------------------------------------------------------------------------------------------
# controller_busy_time
CBT0=$(nvme smart-log /dev/$NVME_PORT |grep "controller_busy_time" |cut -d ":" -f 2| cut -d "C" -f 1)

# fio write data for 61s
LOG_BUF=$(fio --direct=1 --iodepth=1 --ioengine=libaio --bs=512 --rw=write --numjobs=1 --size=100G --offset=0 --filename=/dev/"$NVME_PORT"n1 --name=mdata --runtime=61)

CBT1=$(nvme smart-log /dev/$NVME_PORT |grep "controller_busy_time" |cut -d ":" -f 2| cut -d "C" -f 1)

echo $CBT0 $CBT1

# if CBT1 - CBT0 = 1S, or CBT1 - CBT0 = 2S
if (( $(($CBT0 + 1)) == $(($CBT1 + 0)) || $(($CBT0 + 2)) == $(($CBT1 + 0)) )); then    
    echo -e "\033[32mCheck controller_busy_time: PASS! \033[0m"
else
    echo -e "\033[31mCheck controller_busy_time: FAIL! $CBT0 $CBT1 \033[0m"
    exit_code=1
fi


exit $exit_code