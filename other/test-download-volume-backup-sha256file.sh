#!/bin/bash

rounds=12
tasks=4

sha256_object='xxxxxxxxxxxxx_sha256file'

for round in $(seq 1 ${rounds}); do

  echo "[ Round ${round} ]"
  for task in $(seq 1 ${tasks}); do
    openstack object save volumebackups ${sha256_object} --file ${task} &
    echo "downloading ${task}"
  done
  sleep 10

  total_size=$((4898955264*tasks))
  while true; do
    current_size=0

    for task in $(seq 1 ${tasks}); do
      size=$(ls -s --block-size=1 ${task} | cut -d' ' -f1)
      current_size=$((current_size+size))
    done

    if [ ${current_size} -eq ${total_size} ]; then
      echo "download completed."
      break
    fi

    echo "current download ${current_size}/${total_size}"
    sleep 10

  done

  for task in $(seq 1 ${tasks}); do
    rm -r ./${task}
  done

done

