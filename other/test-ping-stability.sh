#!/bin/bash


TARGET_IP=""
WAITTIME_SEC=1000    # for linux in seconds, for mac os in milliseconds
MAX_PING_COUNT=3600    # in seconds, about 1 hour
LOG_FILE='./ping-stability-output.log'
STATUS_FILE='./last-status'

echo "`date` - Start ping stability test to ${TARGET_IP}." | tee -a ${LOG_FILE}

counter=0
while true; do

    counter=$((counter + 1))

    output=`ping -c 1 -W ${WAITTIME_SEC} ${TARGET_IP} | grep "64 bytes"`
    size=${#output}
    echo $size
    if [[ ${size} -gt 10 ]]; then
        echo "`date` - ${counter} - ping ${TARGET_IP} success." | tee -a ${LOG_FILE}
        echo "success" > ${STATUS_FILE}
    else
        echo "`date` - ${counter} - ping ${TARGET_IP} fail." | tee -a ${LOG_FILE}
        echo "fail" > ${STATUS_FILE}
    fi

    if [[ ${counter} -gt ${MAX_PING_COUNT} ]]; then
        break
    fi

    sleep 1
done

