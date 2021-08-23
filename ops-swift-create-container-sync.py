#!/usr/bin/env python3
# coding=UTF-8

"""
Configure container sync between two containers.
Sync direction from source container (A) to destination container (B).

Two method to get metadata of container:
  - project_conn.get_container(), custom and system metadata.
  - project_conn.object_store.get_container_metadata(), system metadata only.

Two different metadata object type.
  - project_conn.get_container, access data as HEADER key. (use keys() to view keys)
    X-Container-Sync-Key, Content-Length, X-Container-Object-Count, X-Storage-Policy, Accept-Ranges, X-Container-Sync-To, Last-Modified, X-Container-Meta-Sync-Created-At, X-Container-Bytes-Used, X-Timestamp, Content-Type, X-Trans-Id, X-Openstack-Request-Id, Date
  - project_conn.object_store.get_container_metadata(), access data as attribute.
    name, count, bytes, object_count, bytes_used, timestamp, is_newest, read_ACL, write_ACL, sync_to, sync_key, versions_location, content_type, is_content_type_detected, if_none_match, meta_temp_url_key, meta_temp_url_key_2, id, name, location

"""

import openstack
import argparse
import sys
import logging as log
from datetime import datetime


def main(args):
    log.basicConfig(level=log.INFO, format='%(asctime)s %(filename)s %(message)s',)

    src_conn = openstack.connect(cloud=args.src_cloud)
    dst_conn = openstack.connect(cloud=args.dst_cloud)

    src_project = src_conn.connect_as_project(args.src_projectname)
    if args.dst_projectname == None:
        args.dst_projectname = args.src_projectname
    dst_project = dst_conn.connect_as_project(args.dst_projectname)

    if args.dst_containername == None:
        args.dst_containername = args.src_containername

    if args.remove_sync == False:
        log.info(f'Create container sync. Sync key={args.sync_key}, Sync to={args.sync_to}')
    else:
        log.info(f'Remove container sync.')

    log.info(f'Container location.')
    print(f'  Source:')
    print(f'  - cloud name: {args.src_cloud}')
    print(f'  - project name: {args.src_projectname}')
    print(f'  - container name: {args.src_containername}')
    print(f'  Destination:')
    print(f'  - cloud name: {args.dst_cloud}')
    print(f'  - project name: {args.dst_projectname}')
    print(f'  - container name: {args.dst_containername}')

    src_container = src_project.get_container(args.src_containername)
    dst_container = dst_project.get_container(args.dst_containername)
    ''' # another way to get container object.
    containers = src_project.object_store.containers()
    for c in containers:
        if c.name == args.src_containername:
            src_container = c
            break
    containers = dst_project.object_store.containers()
    dst_container = None
    for c in containers:
        if c.name == args.dst_containername:
            dst_container = c
            break
    '''

    if src_container == False:
        log.error(f'Error, Source container not found.')
        sys.exit()
    if dst_container == False:
        log.info(f'Destination container not found, create the container.')
        dst_container = dst_project.object_store.create_container(args.dst_containername)

    src_meta = src_project.object_store.get_container_metadata(args.src_containername)
    dst_meta = dst_project.object_store.get_container_metadata(args.dst_containername)

    log.info(f'Container state before change.')
    print(f'  Source Container: "{src_meta.name}" {src_meta.object_count}/{src_meta.count} {src_meta.bytes_used}/{src_meta.bytes}')
    print(f'  - Sync to: {src_meta.sync_to}')
    print(f'  - Sync key: {src_meta.sync_key}')
    print(f'  Destination Container: "{dst_meta.name}" {dst_meta.object_count}/{dst_meta.count} {dst_meta.bytes_used}/{dst_meta.bytes}')
    print(f'  - Sync to: {dst_meta.sync_to}')
    print(f'  - Sync key: {dst_meta.sync_key}')

    if args.remove_sync == True:
        log.info(f'Unset "sync key" and "sync to".')
        src_project.object_store.set_container_metadata(args.src_containername, sync_key='')
        src_project.object_store.set_container_metadata(args.src_containername, sync_to='')
        dst_project.object_store.set_container_metadata(args.dst_containername, sync_key='')

        # delete custom metadata 'sync_created_at'
        src_project.object_store.delete_container_metadata(args.src_containername, ['sync_created_at'])
    else:
        if args.sync_key != None:
            log.info(f'Set "sync key".')
            src_project.object_store.set_container_metadata(args.src_containername, sync_key=args.sync_key)
            dst_project.object_store.set_container_metadata(args.dst_containername, sync_key=args.sync_key)
        if args.sync_to != None:
            log.info(f'Set "sync to".')  # only set at source container
            src_project.object_store.set_container_metadata(args.src_containername, sync_to=args.sync_to)

        # add custom metadata "sync_created_at"
        log.info(f'Set custom metadata "sync_created_at"')
        now = datetime.now()
        created_at = now.strftime("%d-%m-%Y %H:%M:%S")
        src_project.object_store.set_container_metadata(args.src_containername, sync_created_at=created_at)

    src_meta = src_project.object_store.get_container_metadata(args.src_containername)
    dst_meta = dst_project.object_store.get_container_metadata(args.dst_containername)
    log.info(f'Container state after change:')
    print(f'  Source Container: "{src_meta.name}"')
    print(f'  - Sync to: {src_meta.sync_to}')
    print(f'  - Sync key: {src_meta.sync_key}')

    # custom metadat might not get updated immediately
    src_meta = src_project.get_container(args.src_containername)
    if "X-Container-Meta-Sync-Created-At" in src_meta:
        print(f'  - Sync created at: {src_meta["X-Container-Meta-Sync-Created-At"]}')

    print(f'  Destination Container: "{dst_meta.name}"')
    #print(f'  - Sync to: {dst_meta.sync_to}  # should be None.')
    print(f'  - Sync key: {dst_meta.sync_key}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create container sync between two containers')
    parser.add_argument('--src-cloud', required=True, help='source cloud as defined in clouds.yaml')
    parser.add_argument('--dst-cloud', required=True, help='destination cloud as defined in clouds.yaml')
    parser.add_argument('--src-projectname', required=True, help='source project name')
    parser.add_argument('--dst-projectname', required=False, help='destination project name, use source projectname if not specified')
    parser.add_argument('--src-containername', required=True, help='source container name')
    parser.add_argument('--dst-containername', required=False, help='destination container name, use source containername if not specified')
    parser.add_argument('--sync-key', required=False, help='Sync key')
    parser.add_argument('--sync-to', required=False, help='Sync To')
    parser.add_argument('--remove-sync', action='store_true', help='Remove sync')
    args = parser.parse_args()
    main(args)
