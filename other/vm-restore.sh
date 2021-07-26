#!/bin/bash

PREFIX='BACKUP'

# ------------------------------------------------------------------------------
function get_server_value() {
    local vm_name=$1
    local field=$2
    value=`openstack server show $vm_name -f value -c ${field}`
    echo $value
}


if [ -z "${OS_AUTH_URL}" ]; then
  echo "Please source your openrc file first."
  exit 0
fi


# Get instance name and image name to restore
# ------------------------------------------------------------------------------
if [ $# -ge 2 ]; then
#if [ "$#" == "2" ]; then

  INSTANCE_NAME=$1
  IMAGE_NAME=$2

  # ensure image backup exist
  openstack image show ${IMAGE_NAME} &> /dev/null
  if [ $? -ne 0 ]; then
    echo "Image ${IMAGE_NAME} not found..."
    exit 1
  fi

  # ensure instance exist
  openstack server show ${INSTANCE_NAME} &> /dev/null
  if [ $? -ne 0 ]; then
    echo "Instance ${INSTANCE_NAME} not exist..."
    exit 1
  fi

else

  echo "[ Instance name list ]"
  openstack server list -f value -c Name

  if [[ "$?" != "0" ]]; then
    echo "Please source your openrc file first."
    exit 1
  fi

  echo
  echo "[ Enter name of instance to restore ]"
  read INSTANCE_NAME

  echo
  echo "[ Backup image name list ]"
  openstack image list -f value -c Name | grep "${PREFIX}_${INSTANCE_NAME}"

  echo
  echo "[ Enter name of image backup to restore ]"
  read IMAGE_NAME

fi

if [ -z "${INSTANCE_NAME}" ]; then
  echo "Invalid instance name."
  exi 1
fi

if [ -z "${IMAGE_NAME}" ]; then
  echo "Invalid image name."
  exi 1
fi


# Retreve exist instance spec
# ------------------------------------------------------------------------------
echo
echo "[ Get network address ]"
address=$(get_server_value ${INSTANCE_NAME} 'addresses')
echo ${address}

echo
echo "[ Get flavor name ]"
flavor=$(get_server_value ${INSTANCE_NAME} 'flavor')
echo ${flavor}

echo
echo "[ Get key name ]"
key_name=$(get_server_value ${INSTANCE_NAME} 'key_name')
echo ${key_name}

echo
echo "[ Get attached volume]"
volumes=($(get_server_value ${INSTANCE_NAME} 'volumes_attached'))
echo ${volumes[@]}


# Generate instance create command
# ------------------------------------------------------------------------------
COMMAND="openstack server create"

flavor=($flavor)
flavor_name="${flavor[0]}"

COMMAND="${COMMAND} --flavor ${flavor_name}"
COMMAND="${COMMAND} --image ${IMAGE_NAME}"
COMMAND="${COMMAND} --key-name ${key_name}"

# attach nic
IFS='; ' read -r -a address <<< "$address"
for addr in "${address[@]}"; do
  addr=(${addr//=/ })
  net_id=`openstack network show ${addr[0]} -f value -c id`
  COMMAND="${COMMAND} --nic net-id=${net_id},v4-fixed-ip=${addr[1]}"
done

# attach volumes
for vol in "${volumes[@]}"; do
  vol_id=`echo $vol | sed -e "s/'//g" -e "s/id=//g"`
  vol_dev=`openstack volume show ${vol_id} -f json | grep '"device"' | sed -e 's/"device": "\/dev\///g' -e 's/",//g' -e 's/ //g'`
  COMMAND="${COMMAND} --block-device-mapping ${vol_dev}=${vol_id}:::0"
done

COMMAND="${COMMAND} ${INSTANCE_NAME}"


# Start instance restoration
# ------------------------------------------------------------------------------
if [[ $# -eq 3 && "$3" == "-y" ]] ; then
    CONTINUE='y'
else
  echo
  echo "[ Restore instance '${INSTANCE_NAME}' from image '${IMAGE_NAME}' ] (type 'y' to continue)"
  read CONTINUE
fi

if [[ "$CONTINUE" != "y" ]]; then
  echo "Stop..."
  exit 0
fi

echo "Start..."
echo "- delete exist instance..."
openstack server delete ${INSTANCE_NAME}

echo "- create instance..."
echo "- command: ${COMMAND}"
${COMMAND}

# Check return code
if [[ "$?" != "0" ]]; then
  echo "Error..."
  exit 1
fi

echo "Done..."

