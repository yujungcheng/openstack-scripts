#!/bin/bash
# this is to add a user to all project or defined project list

user="${1}"
project_list_file="${2}"

list_file="/tmp/project_id_list.txt"

if [ "$#" == "1" ]; then

  openstack project list -f value -c ID > ${list_file}

elif [ "$#" == "2" ]; then

  if [ -f "${2}" ]; then
    list_file=${2}
  else
    openstack project list -f value -c ID > ${list_file}
  fi
else
  echo "Arguments: <username> [ project list file path ]"
  exit 0
fi

echo
echo "Project list file = ${list_file}"

while IFS= read -r line; do
  echo "- add ${user} to  _member_ role in project ${line}."
  openstack role add --user ${user} --project ${line} _member_
done < "${list_file}"

echo
echo "Completed"

