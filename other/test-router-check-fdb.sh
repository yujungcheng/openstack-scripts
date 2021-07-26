#!/bin/bash
# Check all compute node's FDB (forward database) to a router
# This script is to check FDB is populated correctlly to
# all compute nodes or not.


# soure openrc file
source openrc_file.sh

# get router id or skip to fetch all routers
router_id=${1}
if [ -z "${router_id}" ]; then
  router_ids=($(openstack router list -f value -c ID))
else
  router_ids=(${router_id})
fi

# node number range
start_node_number=1
end_node_number=77

# node number to skip check.
skip_node=(46)

# temp folder for store FDB
fdb_dir="/tmp/fdb_dir"

#---------------------------------------------------------------
# initial
#---------------------------------------------------------------
mac=""
ip=""
mkdir -p ${fdb_dir}
clear
def_skip="false"
skip=${def_skip}
router_ha_ip_prefix="169.254"
node_lo_ip_prefix="10.10"

#---------------------------------------------------------------
# fetch FDB  from nodes
#---------------------------------------------------------------
echo "[ `date` ] Fetching FDB from nodes"

for i in $(seq ${start_node_number} ${end_node_number}); do
  node_name="node${i}"

  for j in ${skip_node}; do
    if [ "${i}" == "${j}" ]; then
      skip="true"
      break
    fi
  done

  if [ "${skip}" == "false" ]; then
    ssh ${node_name} "bridge fdb show" > ${fdb_dir}/${node_name}
  fi
  skip=${def_skip}

done

#---------------------------------------------------------------
# Scan FDB data for routers
#---------------------------------------------------------------
echo "[ `date` ] Read router FDB data"
for router_id in ${router_ids[@]}; do

  # check active router's node IP
  r_node=`openstack network agent list --router ${router_id} --long -f value -c Host -c "HA State" | grep active | sed s/\ active//g`
  node_ip=`ssh ${r_node} "ip a show lo | grep ${node_lo_ip_prefix}"`
  node_ip=`echo ${node_ip} | awk '{print \$2}'`
  echo "Router: ${router_id} (Node Name/IP = ${r_node}/${node_ip})"

  # check fdb
  ip_macs=($(openstack port list --router ${router_id} -f value -c "MAC Address" -c "Fixed IP Addresses" | grep -v "${router_ha_ip_prefix}" | awk '{print $1,$2}' | sed 's/ /__/g'))
  for ip_mac in ${ip_macs[@]}; do
    #echo $ip_mac
    mac=`echo "${ip_mac}" | sed -e s/__/\ /g | awk '{print $1}'`
    ip=`echo "${ip_mac}"  | sed s/__/\ /g | awk '{print $2}' | sed -e s/ip_address\=//g -e s/\'//g -e s/\,//g`

    echo " MAC IP: ${mac} ${ip}"

    for i in $(seq ${start_node_number} ${end_node_number}); do
      node_name="node${i}"
      for j in ${skip_node}; do
        if [ "${i}" == "${j}" ]; then
          skip="true"
          break
        fi
      done

      if [ "${skip}" == "false" ]; then
        output=`grep -re "${mac}" ${fdb_dir}/${node_name} | grep dst`
        if [ ! -z "${output}" ]; then
          echo " > ${node_name} ${output}"
        fi
      fi
      skip=${def_skip}
    done

  done
  echo
done

