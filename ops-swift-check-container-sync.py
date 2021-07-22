#!/usr/bin/env python3
'''
Compare two given containers, in the same or different regions.
Assume that "container A" has been configured with container-sync to "container B",
and that container-sync is working.

Usage:
  Run "ops-swift-list-container-sync.py" to generate container sync json file.
  Run "ops-swift-check-container-sync.py <Container Sync Json File>"

Python 3.6.9

Tested with pip3 installed package:
  openstackclient                4.0.0
  openstacksdk                   0.41.0
  python-openstackclient         5.0.0

'''

import openstack
import json
import sys


if len(sys.argv) < 2:
    print(f"missing container sync list file.")
    sys.exit()

container_json_file = sys.argv[1]
print(f"Container sync list file: {container_json_file}")
print("-"*80)

with open(container_json_file) as f:
    comparisons = json.load(f)

# our list contains sets of two containers (A and B). We assume that A syncs to B.
for comparison in comparisons:
    connection_a = openstack.connect(cloud=comparison[0].get('region'))
    connection_b = openstack.connect(cloud=comparison[1].get('region'))
    project_a = connection_a.connect_as_project(comparison[0])
    project_b = connection_b.connect_as_project(comparison[1])
    container_a = None
    container_b = None

    try:
        project_name = connection_b.get_project(f'{comparison[1]["id"]}').name
        comparison[1]['name'] = project_name
        #print(f'Target project {comparison[1]["id"]} exist. {project_name}')
    except Exception as e:
        print(f'Error, Target project {comparison[1]["id"]} has been deleted. {e}', end='\n')
        #print(f'{comparison[0].get("name")}, None, None, None, None, None, None', end='\n')
        continue

    # make sure the containers actually exist
    try:
        for container in project_a.list_containers():
            if container.name == comparison[0].get('container'):
                container_a = container
    except Exception as e:
        project_a = comparison[0]
        print(f'Error, A:{project_a}, {e}')
        continue
    try:
        for container in project_b.list_containers():
            if container.name == comparison[1].get('container'):
                container_b = container
    except Exception as e:
        project_b = comparison[1]
        print(f'Error, B:{project_b}, {e}')
        continue
    '''
    print(f'A: {container_a.count} objects, {container_a.bytes / 1024 / 1024 / 1024:.2f} GB '
          f'[{container_a.name}, {comparison[0].get("name")}, {project_a.current_location.region_name})')
    print(f'B: {container_b.count} objects, {container_b.bytes / 1024 / 1024 / 1024:.2f} GB '
          f'[{container_b.name}, {comparison[1].get("name")}, {project_b.current_location.region_name})')
    print(f'A: {container_a.count} objects, {container_a.bytes / 1024:.2f} KB '
          f'[{container_a.name}, {comparison[0].get("name")}, {project_a.current_location.region_name})')
    print(f'B: {container_b.count} objects, {container_b.bytes / 1024:.2f} KB '
          f'[{container_b.name}, {comparison[1].get("name")}, {project_b.current_location.region_name})')
    '''
    project_a_name = {comparison[0].get("name")}
    project_b_name = {comparison[1].get("name")}
    container_a_name = comparison[0].get('container')
    container_b_name = comparison[1].get('container')

    if container_a == None:
        print(f'!!! ERROR: source container {container_a_name} not found in {comparison[0].get("name")} to sync to container {container_b_name} in {comparison[1].get("name")} !!!')
        continue
    if container_b == None:
        print(f'!!! ERROR: target container {container_b_name} not found in {comparison[1].get("name")} to sync from container {container_a_name} in {comparison[0].get("name")} !!!')
        continue
    if container_a.count == None or container_b.count == None or container_a.bytes == None or container_b.bytes == None:
        print(f'!!! ERROR: unexpect None Value. {project_a_name} {container_a_name} => {project_a_name} {container_a_name} | count: {container_a.count} <=> ${container_b.count}, bytes: {container_a.bytes} <=> {container_b.bytes} !!!')
        continue

    try:
        if container_b.count == 0 or container_a.count == 0:
            count_ratio = '0%'
        else:
            count_ratio = f'{container_b.count / container_a.count:.4%}'

        if container_b.bytes == 0 or container_a.bytes == 0:
            bytes_ratio = '0%'
        else:
            bytes_ratio = f'{container_b.bytes / container_a.bytes:.4%}'

        if container_a.count == container_b.count and container_a.bytes == container_b.bytes:
            synced = 'Yes'
        else:
            synced = 'No'

        print(f'{comparison[0].get("name")}, '
              f'{container_a.name}, '
              f'{container_a.count}, '
              f'{container_a.bytes}, '
              f'{comparison[1].get("name")}, '
              f'{container_b.name}, '
              f'{container_b.count}, '
              f'{container_b.bytes}, '
              f'{synced}, '
              f'{count_ratio} objects, '
              f'{bytes_ratio} bytes', end='\n')
        '''
        print(f'🔄 container-sync progress: '
              f'{container_b.count / container_a.count:.2%} objects, '
              f'{container_b.bytes / container_a.bytes:.2%} bytes.', end='\n\n')
        '''
    except Exception as e:
        print(f'Error: {container_a.count} - {container_a.bytes} : {container_b.count} - {container_b.bytes}', end='\n\n')
