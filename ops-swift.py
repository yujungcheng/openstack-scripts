#!/usr/bin/env python3

import openstack
import sys
import os


conn = openstack.connect()
admin_id = os.environ["OS_PROJECT_ID"]
admin_name = os.environ["OS_PROJECT_NAME"]


def list_project():
    for project in conn.list_projects():
        print(f'{project.id} | {project.name}')

def set_project(project_id):
    global conn
    project = conn.get_project(project_id)
    print(f'Set to project', argv[2], f'|', f'{project.name}', "\n")
    os.environ["OS_PROJECT_ID"] = project_id
    os.environ["OS_PROJECT_NAME"] = project.name
    conn.close()
    conn = openstack.connect()

def reset_project():
    os.environ["OS_PROJECT_ID"] = admin_id
    os.environ["OS_PROJECT_NAME"] = admin_name

def list_container():
    global conn
    containers = conn.list_containers()
    # count and bytes might not up to date.
    for c in containers:
        print(f'{c.last_modified} | {c.name} | {c.count} | {c.bytes}')

def list_object(container_name):
    objects = conn.list_objects(container_name)
    if len(objects) < 1000:
        for o in objects:
            print((f'{o.last_modified} | {o.content_type} | {o.hash} | '
               f'{o.name} | {o.bytes}'))
    else:
        objects_file = "./list_object.container_name"
        print(f'object count >= 10000, write data to file {objects_file}')
        objects = []
        # ref: /usr/lib/python3/dist-packages/openstack/object_store/v1/obj.py
        for o in conn.object_store.objects(container_name):
            objects.append((f'{o.last_modified_at} | {o.content_type} | {o.etag} | '
                            f'{o.name} | {o.content_length}'))
            #objects.append((f'{o.last_modified_at} | {o.content_type} | {o.etag} | '
            #                f'{o.name} | {o.content_length} | {o.object_manifest} | '
            #                f'{o.transfer_encoding} | {o.copy_from} | {o.delete_at} | '
            #                f'{o.delete_after} | {o.is_static_large_object}'))
            if len(objects) % 10000 == 0:
                print(len(objects), f'Objects retrieved...')
        print(f'Retrieved', len(objects), f'objects, writing to file.')
        with open(objects_file, 'w') as f:
            for o in objects:
                f.write(o+"\n")

def show_container(container_name):
    c = conn.get_container(container_name)
    for key, value in c.items():
        print(f'{key}: {value}')

def show_object(container_name, object_name):
    o = conn.get_object(container_name, object_name)
    for key, value in o[0].items():
        print(f'{key}: {value}')

def main(argv):
    if len(argv) == 0:
        print(f'Missing arguments')
        exit()

    if len(argv) == 2:
        if argv[0] == "list" and argv[1] == "project":
            list_project()
    elif len(argv) >= 3:
        set_project(argv[2])

        if argv[0] == "list":
            if argv[1] == "container":
                list_container()
            elif argv[1] == "object":
                if len(argv) == 4:
                    list_object(argv[3])
                elif len(argv) == 3:
                    print(f'Missing container name')
            else:
                print(f'Inavlid argument')
        elif argv[0] == "show":
            if argv[1] == "container":
                show_container(argv[3])
            elif argv[1] == "object":
                if len(argv) == 5:
                    show_object(argv[3], argv[4])
                else:
                    print(f'Missing object name')
            else:
                print(f'Invalid arguments')


if __name__ == '__main__':
    argv = sys.argv[1:]
    main(argv)
    conn.close()
