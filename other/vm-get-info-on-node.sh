#!/bin/bash

#openstack server list --all-project --host node71 -c ID -f value | xargs -L1 -I {} sh -c "openstack server show {} -c project_id -f value" | xargs -L1 -I {} sh -c "openstack project show {}"

# get node name
node_name=$1
if [ "${node_name}" == "" ]; then
  echo "Require compute node name as first argument."
  exit 1
fi

instance_IDs=($(openstack server list --all-project --host ${node_name} -c ID -f value))

echo "VM UUID | VM Status | Project Name | VM Name"
echo "----------------------------------------------------------------------"
for id in ${instance_IDs[@]}; do
    instance_info=($(openstack server show -f value -c name -c id -c project_id -c status ${id}))
    vm_id=${instance_info[0]}
    vm_name=${instance_info[1]}
    vm_project_id=${instance_info[2]}
    vm_status=${instance_info[3]}

    project_name=$(openstack project show -c name -f value ${vm_project_id})

    echo "${vm_id} | ${vm_status} | ${project_name} | ${vm_name}"
done

