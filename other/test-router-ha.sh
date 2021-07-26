#!/bin/bash

ROUTER_ID="Router UUID"
MAX_TEST_COUNT=1
LOG_FILE='/tmp/neutron_router_ha.log'

PING_CHECK_IP="Router IP"
WAITTIME_SEC=1    # for linux in seconds, for mac os in milliseconds
ACTION_SLEEP_SEC=10  # take longer time to ensure HA status after add/delete agent

PING_PASS_COUNT=5
PING_FAIL_COUNT=5

declare -a L3_AGENT_LIST
# ==============================================================================


function log(){
    local msg=${@}
    echo "[`date`] - ${msg}" | tee -a ${LOG_FILE}
}

function get_l3_agent() {
    L3_AGENTS=($(neutron l3-agent-list-hosting-router ${ROUTER_ID} -f value -c id -c host -c ha_state 2>/dev/null | sed 's/ /_/g'))
    log "check router l3 agent"
    for agent in ${L3_AGENTS[@]}; do
        log "- agent: `echo ${agent} | sed 's/_/ /g'`"
    done
    L3_AGENT_LIST=($(neutron l3-agent-list-hosting-router ${ROUTER_ID} -f value -c id -c ha_state 2>/dev/null | sed 's/ /_/g'))
}

function do_ping_test(){
    ping_pass_counter=0
    ping_fail_counter=0
    counter=0

    log "ping to router."

    start_ts=`date +"%s"`
    while true; do
        counter=$((counter + 1))

        output=`ping -c 1 -W ${WAITTIME_SEC} ${PING_CHECK_IP} | grep "64 bytes"`
        size=${#output}

        if [[ ${size} -gt 10 ]]; then
            log "${counter} - ping ${PING_CHECK_IP} success."
            ping_pass_counter=$((ping_pass_counter + 1))
        else
            log "${counter} - ping ${PING_CHECK_IP} fail."
            ping_fail_counter=$((ping_fail_counter + 1))
        fi

        # if ping tested more than a current packets, break loop
        if [[ ${ping_pass_counter} -eq ${PING_PASS_COUNT} ]]; then
            #log "ping to router pass."
            break
        fi
        if [[ ${ping_fail_counter} -eq ${PING_FAIL_COUNT} ]]; then
            #log "ping to router fail."
            break
        fi

        sleep 1
    done
    end_ts=`date +"%s"`

    ping_time=$((end_ts - start_ts))
    #log "ping check takes ${ping_time} seconds. [ ${ping_pass_counter} pass ] [ ${ping_fail_counter} fail ]"
}

function do_ping_test2() {
    log "test ping to router."

    start_ts=`date +"%s"`
    while true; do
        ping_status=`ssh 199.34.10.9 -l cirros -i ~/.ssh/mac-cloud.key "~/get-last-ping-status.sh"`
        if [[ ${ping_status} == 'success' ]]; then
            log "success ping to router."
            break
        fi
        sleep 1
    done
    end_ts=`date +"%s"`

    ping_time=$((end_ts - start_ts))
    log "ping test takes ${ping_time} seconds."
}

function do_sleep() {
    log "sleep ${ACTION_SLEEP_SEC} seconds"
    sleep ${ACTION_SLEEP_SEC}
}


# ==============================================================================
#echo "" >> ${LOG_FILE}
rm -r ${LOG_FILE}

log "=========================================================================="
log "Start Router HA Test - Router ID ${ROUTER_ID}"
log "Test ${MAX_TEST_COUNT} times"
log "Router's IP address ${PING_CHECK_IP}"
log "=========================================================================="

# do ping test before test
do_ping_test

TEST_COUNTER=0
for i in `seq 1 ${MAX_TEST_COUNT}`; do

    log "---------------- test count ${i} ----------------"

    # show agent list
    get_l3_agent

    for agent_str in ${L3_AGENT_LIST[@]}; do
        #echo ${agent}

        # choose active agent
        if [[ ${agent_str} = *"active"* ]]; then
            agent_id=`echo ${agent_str} | sed 's/_active//g'`

            # Remove active router
            # ---------------------------------------------------
            log "delete active router agent ${agent_id}"
            neutron l3-agent-router-remove ${agent_id} ${ROUTER_ID} &>/dev/null

            # Sleep 30 seconds
            # ---------------------------------------------------
            do_sleep

            # Get agent list
            # ---------------------------------------------------
            get_l3_agent

            # Check router by ping
            # ---------------------------------------------------
            do_ping_test

            # Add deleted router back
            # ---------------------------------------------------
            log "add back deleted router agent ${agent_id}"
            neutron l3-agent-router-add ${agent_id} ${ROUTER_ID} &>/dev/null

            # sleep 30 seconds
            # ---------------------------------------------------
            do_sleep

            # show agent list
            # ---------------------------------------------------
            get_l3_agent

            # Ping checking
            # ---------------------------------------------------
            do_ping_test

            # remove/add router done... increase test counter
            TEST_COUNTER=$((TEST_COUNTER + 1))
            break
        fi

    done

    do_sleep

done

log "End Router HA Test"

