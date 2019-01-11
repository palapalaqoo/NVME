#!/bin/bash
NOWT=$(date +"%Y-%m-%d_%H:%M:%S")
TO=60


NVME_PORT=$(echo $1 |sed -e 's/\/.*\///g' |cut -c -5 )

exit_code=0
echo -e "\033[32m===========================================================\033[0m"
echo -e "\033[32mhost_read_write_commands\033[0m"
echo -e "\033[32m===========================================================\033[0m"
echo
# Data Units Read test ------------------------------------------------------------------------








#-- 0 ---------------------------------------------------------------------------------------------
echo "read 1000*512*1000 bytes and check data_units_read"

data_units_read0=$(nvme smart-log /dev/$NVME_PORT |grep data_units_read |cut -d ":" -f 2|sed 's/[^0-9]*//g')

# read 1000*512x1000 bytes
LOG_BUF=$(fio --direct=1 --iodepth=16 --ioengine=libaio --bs=32k --rw=read --numjobs=1 --size=$((1000*512*1000)) --offset=0 --filename=/dev/"$NVME_PORT"n1 --name=mdata)

data_units_read1=$(nvme smart-log /dev/$NVME_PORT |grep data_units_read |cut -d ":" -f 2|sed 's/[^0-9]*//g')

echo -e "data_units_read before read command= $data_units_read0"
echo -e "data_units_read after read command=  $data_units_read1"
if (( $(($data_units_read0 + 1000)) == $(($data_units_read1 + 0)) )); then    
    echo -e "\033[32mCheck data_units_read: PASS! \033[0m"
else
    echo -e "\033[31mCheck data_units_read: FAIL! \033[0m"
    exit_code=1
fi

#-- 1 ---------------------------------------------------------------------------------------------
echo
echo "compare 1000*512*1000 bytes and check data_units_read"

data_units_read0=$(nvme smart-log /dev/$NVME_PORT |grep data_units_read |cut -d ":" -f 2|sed 's/[^0-9]*//g')

# compare 51200x10x1000 = 1000*512x1000 bytes
for ((j=0;j<1000;j++)) do

    # compare 51200x10 = 1000*512 bytes
    for ((i=0;i<10;i++)) do
       LOG_BUF=$(cat /dev/zero | nvme compare /dev/"$NVME_PORT"n1  -s 0 -z 51200 -c 99 2>&1 > /dev/null) 
    done
done

data_units_read1=$(nvme smart-log /dev/$NVME_PORT |grep data_units_read |cut -d ":" -f 2|sed 's/[^0-9]*//g')

echo -e "data_units_read before compare command= $data_units_read0"
echo -e "data_units_read after compare command=  $data_units_read1"
if (( $(($data_units_read0 + 1000)) == $(($data_units_read1 + 0)) )); then    
    echo -e "\033[32mCheck data_units_read: PASS! \033[0m"
else
    echo -e "\033[31mCheck data_units_read: FAIL! $data_units_read0 $data_units_read1 \033[0m"
    exit_code=1
fi


#-- 2 ---------------------------------------------------------------------------------------------
echo
echo "write 1000*512*1000 bytes and check data_units_written"

data_units_written0=$(nvme smart-log /dev/$NVME_PORT |grep data_units_written |cut -d ":" -f 2|sed 's/[^0-9]*//g')

# write 1000*512x1000 bytes
LOG_BUF=$(fio --direct=1 --iodepth=16 --ioengine=libaio --bs=32k --rw=write --numjobs=1 --size=$((1000*512*1000)) --offset=0 --filename=/dev/"$NVME_PORT"n1 --name=mdata --do_verify=0 --verify=pattern --verify_pattern=0x00)
   

data_units_written1=$(nvme smart-log /dev/$NVME_PORT |grep data_units_written |cut -d ":" -f 2|sed 's/[^0-9]*//g')


echo -e "data_units_written before write command= $data_units_written0"
echo -e "data_units_written after write command=  $data_units_written1"
if (( $(($data_units_written0 + 1000)) == $(($data_units_written1 + 0)) )); then    
    echo -e "\033[32mCheck data_units_written: PASS! \033[0m"
else
    echo -e "\033[31mCheck data_units_written: FAIL! \033[0m"
    exit_code=1
fi

#-- 3 ---------------------------------------------------------------------------------------------
echo
echo "Write Uncorrectable 1024*512(4k align) bytes and check data_units_written"

data_units_written0=$(nvme smart-log /dev/$NVME_PORT |grep data_units_written |cut -d ":" -f 2|sed 's/[^0-9]*//g')
# command write-uncor -c value from 0 to 511, and 4k align, e.g. 7 15 23 ... 503 511 
# write-uncor 128*512x10 = 1280*512 bytes
for ((i=0;i<10;i++)) do
   LOG_BUF=$(nvme write-uncor /dev/$NVME_PORT -s 0 -n 1 -c 127 2>&1 > /dev/null)
done

data_units_written1=$(nvme smart-log /dev/$NVME_PORT |grep data_units_written |cut -d ":" -f 2|sed 's/[^0-9]*//g')

echo -e "data_units_written before write command= $data_units_written0"
echo -e "data_units_written after write command=  $data_units_written1"
if (( $(($data_units_written0 + 0)) == $(($data_units_written1 + 0)) )); then    
    echo -e "\033[32mCheck data_units_written: PASS! \033[0m"
else
    echo -e "\033[31mCheck data_units_written: FAIL! \033[0m"
    exit_code=1
fi


# to make sure the data is readable(not Uncorrectable), write data into flash
LOG_BUF=$(cat /dev/zero | nvme write /dev/"$NVME_PORT"n1 -s 0 -z 64K -c 128 2>&1 > /dev/null)


#-- 4 ---------------------------------------------------------------------------------------------
echo
echo "send 1 read command and check host_read_commands"

host_read_commands0=$(nvme smart-log /dev/$NVME_PORT |grep host_read_commands |cut -d ":" -f 2|sed 's/[^0-9]*//g')
LOG_BUF=$(nvme read /dev/"$NVME_PORT"n1 -s 0 -z 51200 -c 99 2>&1 > /dev/null) 
host_read_commands1=$(nvme smart-log /dev/$NVME_PORT |grep host_read_commands |cut -d ":" -f 2|sed 's/[^0-9]*//g')

echo -e "host_read_commands before read command= $host_read_commands0"
echo -e "host_read_commands after read command=  $host_read_commands1"
if (( $(($host_read_commands0 + 1)) == $(($host_read_commands1 + 0)) )); then    
    echo -e "\033[32mCheck host_read_commands: PASS! \033[0m"
else
    echo -e "\033[31mCheck host_read_commands: FAIL! \033[0m"
    exit_code=1
fi

#-- 5 ---------------------------------------------------------------------------------------------
echo
echo "send 1 compare command and check host_read_commands" 
host_read_commands0=$(nvme smart-log /dev/$NVME_PORT |grep host_read_commands |cut -d ":" -f 2|sed 's/[^0-9]*//g')
LOG_BUF=$(cat /dev/zero | nvme compare /dev/"$NVME_PORT"n1  -s 0 -z 51200 -c 99 2>&1 > /dev/null)
host_read_commands1=$(nvme smart-log /dev/$NVME_PORT |grep host_read_commands |cut -d ":" -f 2|sed 's/[^0-9]*//g')

echo -e "host_read_commands before read command= $host_read_commands0"
echo -e "host_read_commands after read command=  $host_read_commands1"
if (( $(($host_read_commands0 + 1)) == $(($host_read_commands1 + 0)) )); then    
    echo -e "\033[32mCheck host_read_commands: PASS! \033[0m"
else
    echo -e "\033[31mCheck host_read_commands: FAIL! \033[0m"
    exit_code=1
fi


#-- 6 ---------------------------------------------------------------------------------------------
echo
echo "send 1 write command and check host_write_commands"

host_write_commands0=$(nvme smart-log /dev/$NVME_PORT |grep host_write_commands |cut -d ":" -f 2|sed 's/[^0-9]*//g')
# command write -c value from 0 to 511
LOG_BUF=$(cat /dev/zero | nvme write /dev/"$NVME_PORT"n1 -s 0 -z 51200 -c 99 2>&1 > /dev/null) 
host_write_commands1=$(nvme smart-log /dev/$NVME_PORT |grep host_write_commands |cut -d ":" -f 2|sed 's/[^0-9]*//g')

echo -e "host_write_commands before write command= $host_write_commands0"
echo -e "host_write_commands after write command=  $host_write_commands1"
if (( $(($host_write_commands0 + 1)) == $(($host_write_commands1 + 0)) )); then    
    echo -e "\033[32mCheck host_write_commands: PASS! \033[0m"
else
    echo -e "\033[31mCheck host_write_commands: FAIL! $host_write_commands0 $host_write_commands1 \033[0m"
    exit_code=1
fi






exit $exit_code

