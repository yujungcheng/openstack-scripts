#!/bin/bash

router_id='Router ID'
node_name='Compute Node Name'

if [ -z "${router_id}" ]; then
  router_id=${1}
fi

if [ -z "${active_agent_id}" ]; then
  active_agent_id=`cat ./.neutron_active_agent`
fi

l3_agents=($(neutron agent-list | grep 'neutron-l3-agent' | grep -v "${node_name}" | awk '{print $2}'))

agent_count=${#l3_agents[@]}
max_count=$((agent_count-1))

# in linux
#random_agent_index=`shuf -i0-${max_count} -n 1`

# in macos
random_agent_index=$(( ( RANDOM % 10 )  + 1 ))

random_agent_id=${l3_agents[${random_agent_index}]}

echo "Add router back in agent ${random_agent_id}"
neutron l3-agent-router-add ${random_agent_id} ${router_id} 2>/dev/null

sleep 5

neutron l3-agent-list-hosting-router ${router_id} 2>/dev/null

#rm /tmp/.router_id
#rm /tmp/.neutron_active_agent

