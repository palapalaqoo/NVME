find ./ -name "*.py" -execdir chmod u+x {} +

NVME_PORT=$(echo $1 |sed -e 's/\/.*\///g' |cut -c -5 )

./SMI_NVMeReset.py /dev/"$NVME_PORT"n1
