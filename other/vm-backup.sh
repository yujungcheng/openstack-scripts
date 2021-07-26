#!/bin/bash

PREFIX='BACKUP'

# ------------------------------------------------------------------------------
if [ -z "${OS_AUTH_URL}" ]; then
  echo "Please source your openrc file first."
  exit 0
fi


if [ "$#" == "2" ]; then

  INSTANCE_NAME=$1
  DESC=$2

elif [ "$#" == "1" ]; then

  if [ "$1" == "-h" ]; then
    echo "Command usage examples: "
    echo "  vmbackup"
    echo "    - run internative mode."
    echo "  vmbackup <instance name>"
    echo "    - backup an instance"
    echo "  vmbackup <instance name> <keyword string>"
    echo "    - backup an instance with specified keyword in backuped image name"
    echo "  vmbackup <instance name1>,<instance name2>,..."
    echo "    - backup multiple instances (name seperated by comma)"
    echo "  vmbackup <instance name1>,<instance name2>,... <keyword string>"
    echo "    - backup multiple instances (name seperated by comma) with keyword in backuped image name"
    echo "  vmbackup -h"
    echo "    - show help."
    echo "!!! by default, the keyword string is current datetime in format yyyy-mm-dd-hh-MM-ss"
    exit 0
  else
    INSTANCE_NAME=$1
    DESC=`date '+%Y-%m-%d-%H-%M-%S'`
  fi

elif [ "$#" == "0" ]; then

  echo "[ Instance name list ]"
  openstack server list -f value -c Name

  echo
  if [[ "$?" != "0" ]]; then
    echo "Please source your openrc file first."
    exit 1
  fi

  echo
  echo "[ Enter name of instance to backup ]"
  read INSTANCE_NAME

  DESC=`date '+%Y-%m-%d-%H-%M-%S'`

else

  echo "Invalid arguments."
  exit 1

fi


echo
echo "[ Backup instance name and image list ]"
INSTANCE_NAME=(`echo ${INSTANCE_NAME} | sed 's/,/ /g'`)
for i in ${INSTANCE_NAME[@]}; do
  # todo: verify the instance name first

  echo "$i => ${PREFIX}_${i}_${DESC}"
done


echo
echo "[ Continue to backup? ] (type 'y' to continue)"
read CONTINUE
if [[ "$CONTINUE" -eq "y" ]]; then

  for i in ${INSTANCE_NAME[@]}; do
      echo
      echo "Backup ${i}"
      openstack server backup create --name ${PREFIX}_${i}_${DESC} ${i}
      echo "Done..."
  done

else

  echo "Stop..."
  exit 0

fi

