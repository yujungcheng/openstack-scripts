#!/bin/bash

debug="true"

# ----------------------------------------------------------
# set openrc file path, node name and tickeit number
# ----------------------------------------------------------
openrc_file="/path/to/openrc/file"
node_name=${1}
ticket_number=${2}


if [ -z "${node_name}" ] || [ -z "${ticket_number}" ]; then
  echo "Usage: "
  echo "  nova_compute_evacuate.sh <node name> <tickit number>"
  exit 1
fi


# ensure node name and ticket number for disable-reason
echo
echo "[`date`] check node name and ticket number"
echo "Node name => ${node_name}"
echo "Ticket Number => ${ticket_number}"


echo
echo "[`date`] proceed? (press 'y' to proceed)"
read proceed
if [ ${proceed} != 'y' ]; then
  exit 1
fi


# source openrc file
echo
echo "[`date`] source OpenStack openrc file"
echo ". ${openrc_file}"
. ${openrc_file}

openstack service list > /dev/null 2>&1
if [ $? != 0 ]; then
  echo "Error: source openrc file not successful"
  exit 1
fi


# ----------------------------------------------------------
# define functions
# ----------------------------------------------------------

function proceed() {
  read proceed
  if [ "${proceed}" != 'y' ]; then
    echo "Exit!"
    exit 1
  fi
}

function exec_cmd() {
  local cmd=${1}
  if [ "${debug}" == "true" ]; then
    echo ${cmd}
  fi
  echo `${cmd}`
}

function instance_status() {
  local instance_id=${1}

}

function wait_migration() {
  local loop_interval=10
  local loop_max=100

  check_output=`openstack server show ${instance_id} -f value -c OS-EXT-SRV-ATTR:host -c OS-EXT-STS:task_state -c OS-EXT-STS:power_state -c OS-EXT-STS:vm_state | tr '\n' ' '`
  check_items=( ${check_output} )

  curr_node=${check_items[0]}
  curr_power_state=${check_items[1]}
  curr_task_state=${check_items[2]}
  curr_vm_state=${check_items[3]}

  local curr_node="${1}"
  local curr_task_state="${2}"
  local curr_power_state=${}

  while [ "${curr_node}" != "${node_name}" ] && [ "${curr_task_state}" != "None" ]; do
    echo ""

  done

}

# ----------------------------------------------------------
# disable nova-compute and network agent services
# ----------------------------------------------------------
echo
echo "[`date`] disable services on ${node_name}"
echo openstack compute service set --disable-reason ${ticket_number} --disable ${node_name} nova-compute
openstack compute service set --disable-reason ${ticket_number} --disable ${node_name} nova-compute
sleep 1

agents=(`openstack network agent list --host ${node_name} -f value -c ID`)
for agent_id in ${agents[@]}; do
  echo openstack network agent set --disable ${agent_id}
  openstack network agent set --disable ${agent_id}
  sleep 1
done

sleep 1

# ----------------------------------------------------------
# check service status
# ----------------------------------------------------------
echo
echo "[`date`] services disabled, check service status..."
echo openstack compute service list --host ${node_name}
openstack compute service list --host ${node_name}

echo "openstack network agent list --host ${node_name} -c ID -c 'Agent Type' -c Host -c Alive -c Status -c Binary"
openstack network agent list --host ${node_name} -c ID -c "Agent Type" -c Host -c Alive -c Status -c Binary


# ----------------------------------------------------------
# live migrate / migrate instances
# ----------------------------------------------------------

# list all instances
echo
echo "[`date`] Check instances on ${node_name}"
echo openstack server list --host ${node_name} --all-projects -c ID -c Name -c Status -c Image -c Flavor
openstack server list --host ${node_name} --all-projects -c ID -c Name -c Status -c Image -c Flavor


# ask to do live-mgrate/cold-migrate or not
echo
echo "[ live-migrate/migrate those instances? ] (press 'y' to proceed)"
read proceed

if [ ${proceed} == 'y' ]; then

  all_instances=(`openstack server list --host ${node_name} --all-projects -f value -c ID -c Status -c Flavor | sed 's/ /__/g'`)

  for instance in ${all_instances[@]}; do

    instance_id=`echo ${instance} | sed 's/__/ /g' | awk '{print $1}'`
    instance_status=`echo ${instance} | sed 's/__/ /g' | awk '{print $2}'`
    instance_flavor=`echo ${instance} | sed 's/__/ /g' | awk '{print $3}'`
    #echo "${instance_id} ${instance_status} ${instance_flavor}"

    if [ "${instance_status}" == "SHUTOFF" ]; then

      echo "openstack server migrate ${instance_id}"
      openstack server migrate ${instance_id}
      echo "wait 10 seconds..."; sleep 10

    elif [ "${instance_status}" == "ACTIVE" ] || [ "${instance_status}" == "PAUSED" ]; then

      echo "nova live-migration ${instance_id}"
      nova live-migration ${instance_id}
      # base on size of flavor to sleep
      if [ "${instance_flavor}" == "62C496R128D" ]; then
        echo "wait 300 seconds..."; sleep 300
      elif [ "${instance_flavor}" == *"C256R"* ] || [ "${instance_flavor}" == *"C248R"* ]; then
        echo "wait 240 seconds..."; sleep 240
      elif [ "${instance_flavor}" == *"C128R"* ] || [ "${instance_flavor}" == *"C124R"* ]; then
        echo "wait 120 seconds..."; sleep 120
      elif [ "${instance_flavor}" == *"C64R"* ] || [ "${instance_flavor}" == *"C62R"* ] || [ "${instance_flavor}" == "GPU_"* ]; then
        echo "wait 60 seconds..."; sleep 60
      else
        echo "wait 30 seconds..."; sleep 30
      fi

    else

      echo "!!! Skip live-migrate/migrate ${instance_id} !!!"

    fi

    #openstack server show ${instance_id} -c name -c OS-EXT-SRV-ATTR:host -c OS-EXT-STS:power_state -c OS-EXT-STS:task_state -c OS-EXT-STS:vm_state
    sleep 1

  done

  echo
  echo "[`date`] check instances on ${node_name}"
  echo openstack server list --host ${node_name} --all-projects -c ID -c Name -c Status -c Image -c Flavor
  openstack server list --host ${node_name} --all-projects -c ID -c Name -c Status -c Image -c Flavor

fi


echo
echo "//////////////////////////////////////////////////"
echo "To enable services back, use follow commands"
echo "//////////////////////////////////////////////////"
echo openstack compute service set --enable ${node_name} nova-compute
for agent_id in ${agents[@]}; do
  echo "openstack network agent set --enable ${agent_id}"
done

echo openstack compute service list --host ${node_name}
echo openstack network agent list --host ${node_name}

echo
echo "[`date`] Check qemu-kvm processes on node ${node_name}"
echo "  Before you reboot ${node_name}, run command below to ensure no qemu-kvm process on the node."
echo "  ssh ${node_name}  ps aux | grep kvm"

