#!/usr/bin/env python3
# Monitoring object disk and partions change when rebalance object ring

import subprocess
import datetime
import time
import sys
import os


def get_object_partitons_count(disk_path):
    folder_count = 0
    for folders in os.listdir(disk_path+"/objects/"):
        folder_count += 1
    return folder_count

def get_disk_usage():
    usage = {}
    p = subprocess.run(["df | grep node | awk '{print $1,$2,$3,$4,$6}'"],
                       shell=True,
                       universal_newlines=True,
                       stdout=subprocess.PIPE)
    output = p.stdout
    output_arr = output.split('\n')
    for line in output_arr:
        item_arr = line.split(' ')
        object_partion_count = ""
        if len(item_arr) == 5:
            object_partion_count = get_object_partitons_count(item_arr[4])
            usage[item_arr[0]] = (int(item_arr[1]),
                                  int(item_arr[2]),
                                  int(item_arr[3]),
                                  object_partion_count,)
    return usage

def compare_disk_usage(old_usage, new_usage):
    title = ["disk", "size(KB)", "used(KB)", "avai(KB)", "used diff(KB)", "avai diff(KB)",
             "part count", "part diff"]
    print("{: <16} {: >16} {: >16} {: >16} {: >16} {: >16} {: >16} {: >16}".format(*title))
    print("-"*137)
    for disk, usage in new_usage.items():
        if disk in old_usage:
            old_disk_usage = old_usage[disk]
            used_diff = usage[1] - old_disk_usage[1]
            avai_diff = usage[2] - old_disk_usage[2]
            part_diff = usage[3] - old_disk_usage[3]
            disk_diff = [disk, usage[0], usage[1], usage[2], used_diff, avai_diff, usage[3], part_diff]
            print("{: <16} {: >16} {: >16} {: >16} {: >16} {: >16} {: >16} {: >16}".format(*disk_diff))
        else:
            print("%s not found in old usage" % disk)


def main(interval):
    old_usage = get_disk_usage()
    time.sleep(interval)
    while True:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("%s" % now, flush=True)
        new_usage = get_disk_usage()
        compare_disk_usage(old_usage, new_usage)
        old_usage = new_usage
        time.sleep(interval)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1].isdigit():
            main(int(sys.argv[1]))
        else:
            print("Invalid interval value.")
    else:
        main(60)

