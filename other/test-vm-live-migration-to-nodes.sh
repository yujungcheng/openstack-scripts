#!/bin/bash
# To test instance live migration through all compute nodes.
# This script was used to identify which compute nodes cause instance hanging
# and live migration stability

#---------------------------------------------------------------------------
# define node number list
#---------------------------------------------------------------------------

# xxxx brand nodes
node_num_list_1=(76 78 77 75 37 74 72 68 70 71 73 69 66 61 67 60 65 63 57 62 64 58 55 56 59 54 39 53 48 52 51 46 42 47 49 44 50 40 41 43 45 36  38 34 35 33 32)

# yyyynbrand nodes
node_num_list_2=(13 5 2 7 6 9 12 4 11 15 3 14 10 1 19 23 24 22 18 28 29 16 21 20 27 25 17 26 30 31)

# combine all node number array
all_compute_nodes_num=("${node_num_list_1[@]}" "${node_num_list_2[@]}")


#---------------------------------------------------------------------------
# define target instance and its public IP
#---------------------------------------------------------------------------

instance_id=""
ping_address=""

#---------------------------------------------------------------------------
# get test name and source openrc file
#---------------------------------------------------------------------------

test_name=${1}
if [ -z "${test_name}" ]; then
  echo "Enter a 'test name' as first arugment."
  exit 1
fi

openrc_path="/path/to/openrc/file"
. ${openrc_path}



#---------------------------------------------------------------------------
# ping, log, wait live-migrate interval, loop control and other extra work
#---------------------------------------------------------------------------
#ping_test="false"
ping_test="true"
ping_count=30

# run another ping during the test
ping_run_background="true"

loop_sleep_interval=1
live_migrate_wait_interval=10

ping_log_dir="./ping_log"
ping_log="./${ping_log_dir}/ping.log.${test_name}"
tmp_log="${ping_log}.tmp"


# create log dir
mkdir -p ${ping_log_dir}

# remove exist log file
rm ${ping_log}



#---------------------------------------------------------------------------
# start testing
#---------------------------------------------------------------------------

# run another ping process in background, set 1800 ping count
if [ ${ping_run_background} == "true" ]; then
  ping -c 1800 ${ping_address} | while read line; do echo `date` - $line; done > ${ping_log}.ping &
fi


# ping test first before start live-migrate
if [ "${ping_test}" == "true" ]; then
  echo "[ Ping test => ${ping_address} ]"
  ping -c ${ping_count} ${ping_address}
  echo
  echo
fi


counter=0
for node_num in ${all_compute_nodes_num[@]}; do
  node_name="node${node_num}"

  echo ""
  ((counter++))

  echo "[ `date` - Count: ${counter} ]" | tee -a ${ping_log}
  #echo "------------------------------------------------------------------" | tee -a ${ping_log}
  echo "[ Live migrate => node${node_num}, check state with ${live_migrate_wait_interval} seconds interval ]"
  nova live-migration ${instance_id} ${node_name};


  curr_node=""
  curr_power_state=""
  curr_task_state=""
  curr_vm_state=""

  while [ "${curr_node}" != "${node_name}" ] && [ "${curr_task_state}" != "None" ]; do
    sleep ${live_migrate_wait_interval}

    check_output=`openstack server show ${instance_id} -f value -c OS-EXT-SRV-ATTR:host -c OS-EXT-STS:task_state -c OS-EXT-STS:power_state -c OS-EXT-STS:vm_state | tr '\n' ' '`
    check_items=( ${check_output} )

    curr_node=${check_items[0]}
    curr_power_state=${check_items[1]}
    curr_task_state=${check_items[2]}
    curr_vm_state=${check_items[3]}

    echo "- current Node: ${curr_node}"
    echo "- power State : ${curr_power_state}"
    echo "- task State  : ${curr_task_state}"
    echo "- vm State    : ${curr_vm_state}"
    echo
  done

  echo "[ Current Node => "${curr_node}" ]" | tee -a ${ping_log}

  if [ "${ping_test}" == "true" ]; then
    echo "[ Ping test => ${ping_address} ]"
    ping -c ${ping_count} ${ping_address} | tee -a ${ping_log}
  fi

  echo "[ `date` - Wait ${loop_sleep_interval} seconds for next migrate ]"
  sleep ${loop_sleep_interval}

done


# kill the ping in background
if [ ${ping_run_background} == "true" ]; then
  pkill ping
fi


#---------------------------------------------------------------------------
# refine ping log file
#---------------------------------------------------------------------------

cat ${ping_log} | grep "node\|packet" > ${tmp_log}

awk 'NR %2 == 1' ${tmp_log} > ${tmp_log}.a
awk 'NR %2 == 0' ${tmp_log} > ${tmp_log}.b

paste -d " " ${tmp_log}.a ${tmp_log}.b > ${tmp_log}.c

rm ${tmp_log}.a
rm ${tmp_log}.b

mv ${tmp_log}.c ${tmp_log}


#---------------------------------------------------------------------------
# print and output result
#---------------------------------------------------------------------------

echo
echo "==========================================="
echo "[ Ping Result ]"
echo "==========================================="
#cat ${tmp_log} | awk '{print $5,$13,$14,$15}'
cat ${tmp_log} | awk '{print $13,$14,$15}'

echo
echo "==========================================="
echo "[ Ping Round-Trip ]"
echo "==========================================="
cat ${ping_log} | grep "round-trip" | awk '{print $4}' | tr '/' \\t | tee ${ping_log}.round_trip

#cat ${ping_log} | grep "round-trip" | awk '{print $4}' | tr '/' \\t     > ${ping_log}.round_trip
#cat ${ping_log} | grep "round-trip" | awk '{print $4}' | sed "s/\// /g" > ${ping_log}.round_trip


# output drop rate file for csv sheet
cat ${tmp_log} | awk '{print $13,$14,$15}' > ${ping_log}.drop_rate
#cat ${tmp_log} | awk '{print $5}' > ${tmp_log}.node_name


rm ${tmp_log}

