#!/bin/bash
NOWT=$(date +"%Y-%m-%d_%H:%M:%S")
TO=60


NVME_PORT=$(echo $1 |sed -e 's/\/.*\///g' |cut -c -5 )

exit_code=0
echo -e "\033[32m===========================================================\033[0m"
echo -e "\033[32mcritical_warnings\033[0m"
echo -e "\033[32m===========================================================\033[0m"
echo
# Critical Warning test ------------------------------------------------------------------------

# set all "SMART / Health Critical Warnings" in "Asynchronous Event Configuration" to 1
#nvme set-feature /dev/$NVME_PORT -f 0xB -v 0xFF


# live temperature
LiveT=$(nvme smart-log /dev/$NVME_PORT |grep "temperature" |cut -d ":" -f 2| cut -d "C" -f 1)
WCTEMP=$(nvme id-ctrl /dev/$NVME_PORT |grep wctemp |cut -d ":" -f 2| cut -d "C" -f 1)



echo
#-----------------------------------------------------------------------------------------------
# get TMPTH

TMPTH_over=$(nvme get-feature /dev/$NVME_PORT -f 0x4 |cut -d ":" -f 3|sed "s/0x//g")
TMPTH_under=$(nvme get-feature /dev/$NVME_PORT -f 0x4 -cdw11 0x100000|cut -d ":" -f 3|sed "s/0x//g")



echo "-- test the over temperature threshold Feature "
#-----------------------------------------------------------------------------------------------
#echo "Set TMPTH to 10 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold"
LOG_BUF=$(nvme set-feature /dev/$NVME_PORT -f 0x4 -v 0x11B) 

sleep 0.1

# critical warning
CWarning=$(nvme smart-log /dev/$NVME_PORT |grep "critical_warning" |cut -d ":" -f 2)
sleep 0.1
CWarningBit2=$(((CWarning&2)==2))

echo "The temperature is $LiveT C now and TMPTH is set to 10 C, Over Temperature Threshold test"
# if bit 2 = 1, means temperature is above an over temperature threshold or below an under temperature threshold
if ((  $CWarningBit2 ==1 )); then    
    echo -e "\033[32mCheck Critical Warning bit 2: PASS! \033[0m"
else
    echo -e "\033[31mCheck Critical Warning bit 2: FAIL! value: $CWarningBit2\033[0m"
    exit_code=1
fi

#-----------------------------------------------------------------------------------------------
#echo "Set TMPTH to 60 degrees Celsius and Threshold Type Select (THSEL) to Over Temperature Threshold"
LOG_BUF=$(nvme set-feature /dev/$NVME_PORT -f 0x4 -v 0x14D) 

sleep 0.1

# critical warning
CWarning=$(nvme smart-log /dev/$NVME_PORT |grep "critical_warning" |cut -d ":" -f 2)
sleep 0.1
CWarningBit2=$(((CWarning&2)==2))

echo "The temperature is $LiveT C now and TMPTH is set to 60 C, Over Temperature Threshold test"
# if bit 2 = 1, means temperature is above an over temperature threshold or below an under temperature threshold
if ((  $CWarningBit2 ==0 )); then    
    echo -e "\033[32mCheck Critical Warning bit 2: PASS! \033[0m"
else
    echo -e "\033[31mCheck Critical Warning bit 2: FAIL! value: $CWarningBit2\033[0m"
    exit_code=1
fi
#-----------------------------------------------------------------------------------------------
# reset to default value
LOG_BUF=$(nvme set-feature /dev/$NVME_PORT -f 0x4 -v 0x157) 

# if wctemp != 0
if ((  $WCTEMP !=0 )); then 
    echo
    echo "-- WCTEMP is $WCTEMP(not zero value), so have to test the under temperature threshold Feature "
    #-----------------------------------------------------------------------------------------------
    #echo "Set TMPTH to 10 degrees Celsius and Threshold Type Select (THSEL) to Under Temperature Threshold"
    LOG_BUF=$(nvme set-feature /dev/$NVME_PORT -f 0x4 -v 0x10011B) 

    sleep 0.1

    # critical warning
    CWarning=$(nvme smart-log /dev/$NVME_PORT |grep "critical_warning" |cut -d ":" -f 2)
    sleep 0.1
    CWarningBit2=$(((CWarning&2)==2))

    echo "The temperature is $LiveT C now and TMPTH is set to 10 C, Under Temperature Threshold test"
    # if bit 2 = 1, means temperature is above an over temperature threshold or below an under temperature threshold
    if ((  $CWarningBit2 ==0 )); then    
        echo -e "\033[32mCheck Critical Warning bit 2: PASS! \033[0m"
    else
        echo -e "\033[31mCheck Critical Warning bit 2: FAIL! value: $CWarningBit2\033[0m"
        exit_code=1
    fi

    #-----------------------------------------------------------------------------------------------
    #echo "Set TMPTH to 70 degrees Celsius and Threshold Type Select (THSEL) to Under Temperature Threshold"
    LOG_BUF=$(nvme set-feature /dev/$NVME_PORT -f 0x4 -v 0x10014D) 

    sleep 0.1

    # critical warning
    CWarning=$(nvme smart-log /dev/$NVME_PORT |grep "critical_warning" |cut -d ":" -f 2)
    sleep 0.1
    CWarningBit2=$(((CWarning&2)==2))

    echo "The temperature is $LiveT C now and TMPTH is set to 60 C, Under Temperature Threshold test"
    # if bit 2 = 1, means temperature is above an over temperature threshold or below an under temperature threshold
    if ((  $CWarningBit2 ==1 )); then    
        echo -e "\033[32mCheck Critical Warning bit 2: PASS! \033[0m"
    else
        echo -e "\033[31mCheck Critical Warning bit 2: FAIL! value: $CWarningBit2\033[0m"
        exit_code=1
    fi
    #-----------------------------------------------------------------------------------------------

    # reset to default value
    LOG_BUF=$(nvme set-feature /dev/$NVME_PORT -f 0x4 -v 0x100000) 

else 
    echo
    echo "-- WCTEMP is zero, no need to test the under temperature threshold Feature "

fi



# reset TMPTH
LOG_BUF=$(nvme set-feature /dev/$NVME_PORT -f 0x4 -v 0x157) 
LOG_BUF=$(nvme set-feature /dev/$NVME_PORT -f 0x4 -v 0x100000) 






exit $exit_code







