#!/bin/bash
# to filling random data into all data volumes


device_id=(b c d e f g h i j)

size_MB=0

for id in ${device_id[@]}; do
  echo "- filling data to /dev/sd${id}"

  if [ "${id}" == "a" ]; then
    echo "Must not filling data to sda"
    exit 1
  fi

  if [ "${size_MB}" == "0" ]; then
    count_option=""
  else
    count_option="count=${size_MB}"
  fi

  dd if=/dev/urandom of=/dev/sd${id} bs=1M ${count_option} &

done

