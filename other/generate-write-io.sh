#!/bin/bash
# generate light write io.

w_interval=1
w_file='/tmp/file'
w_max_count=1000

while true; do

  $(date > ${w_file})

  for i in $(seq -w 1 ${w_max_count}); do
    echo ${i} >> "${w_file}.seq"
    #uuidgen >> "${w_file}.uuid"
    sync
    sleep ${w_interval}
  done

done

