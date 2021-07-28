#!/usr/bin/env python3
'''
In a given region, look through every project and list the swift containers that
are configured to sync their contents to another container.
The relevant cloud (region) must be configured somewhere like `clouds.yaml`.

Python 3.6.9

pip3 package:
openstackclient                4.0.0
openstacksdk                   0.41.0
python-openstackclient         5.0.0
'''

import openstack
import operator
import json
import sys


if len(sys.argv) < 2:
    print(f"missing cloud name argument.")
    sys.exit()

cloud_name = sys.argv[1]
print(f"Cloud name: {cloud_name}")
print("-"*80)

conn = openstack.connect(cloud=cloud_name)

all_source_containers = []
all_syncing_containers = []
container_compare_list = []

for project in conn.identity.projects():
    # for testing, only check admin project
    #if project.name != "admin":
    #    continue
    if project.name == "service" or project.name == "admin":
        continue

    if project.is_enabled:
        # with swift you need to perform operations (like container list) from inside the project itself
        print(f'switching into project: {project.name}')

        try:
            container_project = conn.connect_as_project({'id': project.id, 'name': project.name})
        except:
            container_project = conn.connect_as_project({'id': project.id, 'name': project.name})

        try:
            project_containers = container_project.list_containers()
        except:
            project_containers = container_project.list_containers()

        for container in project_containers:

            # try again if error raised, such as Gateway Time-out
            '''
            try:
              metadata = container_project.get_container(container.name)
            except:
              metadata = container_project.get_container(container.name)
            '''

            # give try 5 times if exception raised
            for x in range(0, 5):
                try:
                    metadata = container_project.get_container(container.name)
                except:
                    #fail_get_containers.append(container.name)
                    metadata = None
                    continue

            if metadata == None:
                print(f'[{project.name}] {container.name} ---- Fail to get container info.')
                continue

            # there is only 'x-container-sync-to' metadata.
            # unfortunately there is no 'x-container-sync-FROM', so we can't check the other direction
            try:
                if metadata.get('x-container-sync-to'):
                    all_source_containers.append(f"{cloud_name},{project.name},{container.name},sync_enabled")
                    print(f'[{project.name}] {container.name} ({container.count} objects) -> '
                          f'{metadata.get("x-container-sync-to") }')
                    container['project'] = project.name
                    all_syncing_containers.append(container)

                    # Generate compare pair
                    source_container = {"region": cloud_name,
                                        "id": project.id,
                                        "name": project.name,
                                        "container": container.name}

                    sync_to_str = metadata.get("x-container-sync-to")
                    sync_array = sync_to_str.split('/')
                    target_container = {"region": sync_array[2].replace('udlm-', ''),
                                        "id": sync_array[4].replace('AUTH_', ''),
                                        "container": sync_array[5]}
                    compare = [source_container, target_container]
                    container_compare_list.append(compare)
                else:
                    all_source_containers.append(f"{cloud_name},{project.name},{container.name},sync_disabled")

            except AttributeError:
                pass  # some containers have no metadata at all, for unknown reasons



with open(f'containers.sync.{cloud_name}.json', 'w') as jsonfile:
    json.dump(container_compare_list, jsonfile, indent=4)

with open(f'containers.all.{cloud_name}.txt', 'w') as textfile:
    for source_container in all_source_containers:
        textfile.write(source_container+'\n')

print("-"*80)
print(f"Sync configured container list file : containers.sync.{cloud_name}.json")
print(f"All scanned container list file     : containers.all.{cloud_name}.txt")

'''
# Get top 10 results
for key in 'bytes', 'count':
    print(f'\nTop 10 containers by {key}:')
    all_syncing_containers.sort(key=operator.itemgetter(key), reverse=True)

    for index, container in enumerate(all_syncing_containers[:10]):
        print(f'{index+1}.  [{container.project}] {container.name}: '
              f'{container.count} objects, {container.bytes / 1024 / 1024 / 1024:.2f} GB')
'''

