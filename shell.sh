#!/bin/bash
NOWT=$(date +"%Y-%m-%d_%H:%M:%S")
TO=60
. _DEBUG.sh




NVME_PORT=$(echo $1 |sed -e 's/\/.*\///g' |cut -c -5 )

exit_code=0
echo -e "\033[32m===========================================================\033[0m"
echo -e "\033[32mhtcm_tmt\033[0m"
echo -e "\033[32m===========================================================\033[0m"
echo

# live temperature
LiveT=$(nvme smart-log /dev/$NVME_PORT |grep "temperature" |cut -d ":" -f 2|sed "s/[^0-9]*//g")
LiveT_init=$LiveT
echo "-- test 'Thermal Management Temperature Transition Count'"
echo "   'Total Time For Thermal Management Temperature' and 'Composite Temperature'"
#-----------------------------------------------------------------------------------------------


# HCTMA
HCTMA=$(nvme id-ctrl /dev/$NVME_PORT |grep hctma |cut -d ":" -f 2|sed "s/^.0x//g")

if [ "$HCTMA" != "1" ]; then
    echo -e "\033[31mCheck HCTMA: FAIL! \033[0m"
    echo -e "\033[31mThe controller does not support host controlled thermal management! \033[0m"
    exit 1
fi


# get value from smart log 
TMT1TC=$(nvme smart-log /dev/$NVME_PORT |grep "Thermal Management T1 Trans Count" |cut -d ":" -f 2|sed "s/[^0-9]*//g")
TMT2TC=$(nvme smart-log /dev/$NVME_PORT |grep "Thermal Management T2 Trans Count" |cut -d ":" -f 2|sed "s/[^0-9]*//g")

TMT1TT=$(nvme smart-log /dev/$NVME_PORT |grep "Thermal Management T1 Total Time" |cut -d ":" -f 2|sed "s/[^0-9]*//g")
TMT2TT=$(nvme smart-log /dev/$NVME_PORT |grep "Thermal Management T2 Total Time" |cut -d ":" -f 2|sed "s/[^0-9]*//g")


# Set Thermal Management Temperature in Kelvin 
TMT1_C=$(( $LiveT+6 ))
TMT2_C=$(( $LiveT+7 ))
# C + 273.15 = K
TMT1_K=$(( $LiveT+273+6 ))
TMT2_K=$(( $LiveT+273+7 ))
TMT_K=$(( $TMT1_K*65536 + TMT2_K ))

echo
echo "Get Composite Temperature: $LiveT °C"
echo "Set Thermal Management Temperature 1(TMT1): $TMT1_C °C"
echo "Set Thermal Management Temperature 2(TMT2): $TMT2_C °C"
#echo "$TMT1_K $TMT2_K $TMT_K"


LOG_BUF=$(nvme set-feature /dev/$NVME_PORT -f 0x10 -v $TMT_K)


echo "writing data to increase temperature (time limit is 60s)"
echo
#fio --direct=1 --iodepth=1 --ioengine=libaio --bs=512 --rw=write --numjobs=1 --size=100G --offset=0 --filename=/dev/"$NVME_PORT"n1 --name=mdata --do_verify=0 --verify=pattern --verify_pattern=0xac --runtime=60  2>&1 > /dev/null &
my_pid=$!

SECONDS=0
# HCTM status, 0=normal(LiveT<TMT1_C), 1=light throttle(LiveT>TMT1_C), 2=heavy thottling(LiveT>TMT2_C)
HCTM_status=0
# test time limit is 60s
for ((;$SECONDS<60;)) do
    sleep 0.1
    LiveT=$(nvme smart-log /dev/$NVME_PORT |grep "temperature" |cut -d ":" -f 2|sed "s/[^0-9]*//g")

    if(( $LiveT >= $TMT1_C && $HCTM_status ==0 )); then
        echo "HCTM enter light throttle ststus, Composite Temperature > TMT1)"
        HCTM_status=1
    fi
    if(( $LiveT >= $TMT2_C && $HCTM_status ==1 )); then
        sleep 3s
        echo "HCTM enter heavy throttle ststus, Composite Temperature > TMT2)"
        HCTM_status=2
        break
    fi
done    

# kill writeng process
kill  $my_pid 
wait $my_pid 2>/dev/null


# get value from smart log 
TMT1TC_1=$(nvme smart-log /dev/$NVME_PORT |grep "Thermal Management T1 Trans Count" |cut -d ":" -f 2|sed "s/[^0-9]*//g")
TMT2TC_1=$(nvme smart-log /dev/$NVME_PORT |grep "Thermal Management T2 Trans Count" |cut -d ":" -f 2|sed "s/[^0-9]*//g")

TMT1TT_1=$(nvme smart-log /dev/$NVME_PORT |grep "Thermal Management T1 Total Time" |cut -d ":" -f 2|sed "s/[^0-9]*//g")
TMT2TT_1=$(nvme smart-log /dev/$NVME_PORT |grep "Thermal Management T2 Total Time" |cut -d ":" -f 2|sed "s/[^0-9]*//g")

#echo "$TMT1TC != $TMT1TC_1 && $TMT2TC != $TMT2TC_1 && $TMT1TT != $TMT1TT_1 && $TMT2TT != $TMT2TT_1 "
# 'Thermal Management Trans Count', 'Total Time'
echo
if [ $HCTM_status -eq 2 ]; then
    if (( $TMT1TC != $TMT1TC_1 && $TMT2TC != $TMT2TC_1 && $TMT1TT != $TMT1TT_1 && $TMT2TT != $TMT2TT_1 )); then 
        echo -e "\033[32mCheck smart log: PASS!\033[0m"
    else
        echo -e "\033[31mCheck smart log: FAIL!\033[0m"  
        exit_code=1
    fi
elif [ $HCTM_status -eq 1 ]; then
    echo -e "\033[31mFAIL! The temperature has never great then TMT2 in 60s, $LiveT °C now\033[0m"  
    echo -e "\033[31mPlease cool down the controller and try it again later\033[0m" 
    exit_code=1    
else
    echo -e "\033[31mFAIL! The temperature has never great then TMT1 in 60s, $LiveT °C now\033[0m"  
    echo -e "\033[31mPlease cool down the controller and try it again later\033[0m" 
    exit_code=1      
fi  

#'Composite Temperature'
if [ $LiveT_init -ne $LiveT ]; then
    echo -e "\033[32mCheck 'Composite Temperature': PASS!\033[0m"

else
    echo -e "\033[31mCheck 'Composite Temperature': FAIL! Composite Temperature has never changed\033[0m"   
    exit_code=1      
fi   

# reset
LOG_BUF=$(nvme set-feature /dev/$NVME_PORT -f 0x10 -v 0x0158015C)

echo




exit $exit_code

