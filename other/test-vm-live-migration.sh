#!/usr/bin/env bash

# ------------------------------------------------------------------------------
# Variables
# ------------------------------------------------------------------------------

TEST_COUNT=1
INSTANCE_ID=""
INSTANCE_IP=""


# ------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------

function random_select() {
    local item_list=("$@")

    rand=$[$RANDOM % ${#item_list[@]}]
    echo "${item_list[$rand]}"
}

function ping_test() {
    success_counter=0
    counter=0

    while true; do
        counter=$((counter + 1))

        output=`ping -c 1 ${INSTANCE_IP} | grep "64 bytes"`
        size=${#output}

        if [[ ${size} -gt 10 ]]; then
            echo "`date` - ${counter} - ping ${INSTANCE_IP} success."
            success_counter=$((success_counter + 1))
        else
            echo "`date` - ${counter} - ping ${INSTANCE_IP} fail."
        fi

        if [[ ${success_counter} -gt 4 ]]; then
            break
        fi

        sleep 1
    done
}

# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------
node_list=($(openstack host list | grep compute | awk '{print $2}'))

for i in `seq 1 ${TEST_COUNT}`; do
    echo "`date` - live migrate loop ${i}"

    current_node=`openstack server show ${INSTANCE_ID} | grep 'hypervisor_hostname' | awk '{print $4}'`
    #echo ${current_node}

    while true; do
        next_node=$(random_select "${node_list[@]}")

        if [[ ${current_node} != ${next_node} ]]; then
            #echo ${next_node}
            break
        fi
        sleep 1
    done

    echo "`date` - live migrate from ${current_node} to ${next_node}"
    openstack server migrate --live ${next_node} ${INSTANCE_ID}

    echo "`date` - live migrate command issued, sleep 5 seconds."
    sleep 5

    while true; do
        current_node=`openstack server show ${INSTANCE_ID} | grep 'hypervisor_hostname' | awk '{print $4}'`
        if [[ ${current_node} == ${next_node} ]]; then
            break
        fi
    done
    echo "`date` - live migrate to ${next_node} successfully."

    echo "`date` - ping test to the live migrated instance."
    ping_test

done

