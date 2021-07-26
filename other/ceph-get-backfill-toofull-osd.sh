#!/bin/bash

sudo ceph health detail | grep -i "current state active+remapped+backfill_toofull" | awk {'print $2'} > pglist

for line in $(cat pglist); do

  sudo ceph pg $line query | grep 'actingbackfill' -B 4 | grep -iEo '[0-9]{1,3}'

done > out.txt && sort out.txt | uniq -c

