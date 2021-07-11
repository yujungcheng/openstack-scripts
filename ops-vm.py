#!/usr/bin/env python3
''' This script is to extract instance detail such as
volume, network, security grup and actions (events).

Tested on Ubuntu 18.04 with package install
- python3-openstacksdk 0.17.2-0ubuntu1~cloud0

Source admin tenancy/project OpenRC file in order to use.

* If project / user deleted, represent their name as None or ID.
* Convert timestamp to timezone AEST (assume UTC timezone DB).
'''

import os
import sys
import argparse
import itertools
import subprocess
import datetime
import openstack


#os.environ['OS_IDENTITY_API_VERSION'] = '3'
conn = openstack.connect()
opsvm_data_file = "opsvm.data.tmp"

all_projects = {}
all_users = {}


def run_cmd(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.stdout.readlines()

def write(data):
    with open(opsvm_data_file, 'w') as f:
        f.write(data)

def format_datetime(datetime_string, timezone=None):
    return

def convert_power_status(state):
    power_state = ['No State', 'Running', 'Blocked', 'Paused', 'Shutdown', 'Shutoff',
                   'Crashed', 'Pmsuspended', 'No State']
    return power_state[int(state)]

def list_project(_print=True):
    #projects = [project.id for project in conn.list_projects()]
    for project in conn.list_projects():
        if _print:
            print(f'{project.id} | {project.name}')
        all_projects[project.id] = project.name

def list_user(_print=True):
    users = []
    for user in conn.list_users():
        if _print:
            print(f'{user.id} | {user.name}')
        all_users[user.id] = user.name

def list_vm(project_id):
    list_project(_print=False)
    if project_id not in all_projects:
        print(f'Project {project_id} not found')
        exit(1)
    project = conn.get_project(project_id)
    project_conn = conn.connect_as_project(project)
    for server in project_conn.compute.servers():
        print(f'{server.id} | {server.vm_state} | {server.name}')

def show_vm(vm):
    try:
        server = conn.compute.get_server(vm)
    except Exception as e:
        print(e)
        exit(1)
    '''
    pairs = ["%s=%s" % (k, v) for k, v in dict(itertools.chain(
        server._body.attributes.items(),
        server._header.attributes.items(),
        server._uri.attributes.items())).items()]
    '''
    vm_info = {}
    for key, value in dict(itertools.chain(server._body.attributes.items(),
                                           server._header.attributes.items(),
                                           server._uri.attributes.items()
                                           )).items():
        #print(f'{key} = {value}')
        vm_info[key] = value
    project = conn.get_project(server.project_id)
    user = conn.get_user(server.user_id)
    if user == None:
        user_name = None
        user_email = None
    else:
        user_name = user.name
        user_email = user.email

    power_state =  convert_power_status(vm_info["OS-EXT-STS:power_state"])

    interfaces = conn.compute.server_interfaces(server.id)
    vm_interfaces = {}
    for interface in interfaces:
        if_info = {}
        port = conn.get_port(interface.port_id)
        if_info['name'] = port.name
        if_info['security_groups'] = port.security_groups
        if_info['created_at'] = port.created_at
        if_info['state'] = interface.port_state
        if_info['port_id'] = interface.port_id
        if_info['mac'] = interface.mac_addr
        if_info['fixed_ips'] = interface.fixed_ips
        if_info['tap_name'] = None  # todo: get tap inerface with statistic
        if interface.net_id in vm_interfaces:
            vm_interfaces[interface.net_id].append(if_info)
        else:
            vm_interfaces[interface.net_id] = [if_info]

    flavor_info = conn.get_flavor(server.flavor['id'])
    volume_attached = vm_info['os-extended-volumes:volumes_attached']

    project_conn = conn.connect_as_project(project.name)
    all_security_groups = project_conn.network.security_groups(project_id=server.project_id)
    security_groups = {}
    for security_group in all_security_groups:
        security_groups[security_group.name] = security_group

    print(f'Instnace: {server.id} | {server.name}')
    print(f'  Status: {vm_info["OS-EXT-STS:vm_state"]}')
    print(f'  Power State: {power_state}')
    print(f'  Launched At: {vm_info["OS-SRV-USG:launched_at"]}')
    print(f'  Project ID: {server.project_id} | {project.name}')
    print(f'  User ID: {server.user_id} | {user_name} | Email:{user_email}')
    print(f'  Key Name: {server.key_name}')
    print(f'  Hypervisor Hostname: {vm_info["OS-EXT-SRV-ATTR:hypervisor_hostname"]}')
    print(f'  Instance Name: {vm_info["OS-EXT-SRV-ATTR:instance_name"]}')
    print(f'  Flavor: {flavor_info.id} | {flavor_info.name}')

    print(f'  Properties:')
    for key, value in server.metadata.items():
        print(f'    Property: {key}={value}')

    print(f'  Attached Volumes:')
    for volume in volume_attached:
        vol_info = conn.get_volume_by_id(volume['id'])
        print((f'    Volume: {vol_info.id} | {vol_info.name} | {vol_info.volume_type} | '
            f'{vol_info.size}GB'))
        for attachment in vol_info.attachments:
            print((f'      attachment: {attachment.attachment_id} | {attachment.device} | '
                f'{attachment.attached_at}'))

    print(f'  Networks:')
    vm_addresses = server.addresses
    for network_name, value in vm_addresses.items():
        network = project_conn.get_network(network_name)
        segmentation_id = network['provider:segmentation_id']
        subnets = ','.join(network['subnets'])
        print(f'    Network: {network.id} | {network_name} | SegmentID:{segmentation_id}')
        print(f'      Subnets:')
        for subnet in network['subnets']:
            subnet_info = conn.get_subnet_by_id(subnet)
            dhcp_enabled = subnet_info.enable_dhcp
            dns_nameservers = subnet_info.dns_nameservers
            gateway_ip = subnet_info.gateway_ip
            cidr = subnet_info.cidr
            allocation_pools = subnet_info.allocation_pools
            #print((f'        Subnet: {subnet} | {cidr} | {gateway_ip} | {dns_nameservers} | '
            #    f'{dhcp_enabled} | {allocation_pools}'))
            print((f'        Subnet: {subnet} | {cidr} | {gateway_ip} | {dns_nameservers} | '
                f'{dhcp_enabled}'))
        print(f'      Ports:')
        net_interfaces = vm_interfaces[network.id]
        for net_if in net_interfaces:
            print((f'        Port: {net_if["port_id"]} | {net_if["mac"]} | {net_if["name"]} | '
                f'{net_if["state"]}'))
            for fixed_ip in net_if['fixed_ips']:
                print((f'          Address: {fixed_ip["ip_address"]} | '
                    f'Subnet ID:{fixed_ip["subnet_id"]}'))

    print(f'  Security Groups:')
    #vm_sgs = conn.compute.fetch_server_security_groups(server.id) # not support
    vm_security_groups = set([ a_dict['name'] for a_dict in server.security_groups ])
    for vm_security_group in vm_security_groups:
        security_group = security_groups[vm_security_group]
        print(f'    Security Group: {security_group.id} | {security_group.name}')
        rules = security_group.security_group_rules
        for rule in rules:
            print((f'      Rule: {rule["direction"]} | {rule["protocol"]} | '
                f'{rule["port_range_min"]}:{rule["port_range_max"]} | '
                f'{rule["remote_ip_prefix"]} | {rule["remote_group_id"]}'))

    print(f'  Last 5 Events:')
    output = run_cmd(f'openstack server event list -f value --long {server.id}')
    event_count = 0
    for line in output:
        line_arr = line.decode('utf-8').strip().split(' ')
        if len(line_arr) == 7:
            if line_arr[5] in all_projects:
                line_arr[5] = all_projects[line_arr[5]]
            if line_arr[6] in all_users:
                line_arr[6] = all_users[line_arr[6]]
            print(f'    Event: {line_arr[2]} | {line_arr[3]} | {line_arr[5]} | {line_arr[6]}')
            event_count += 1
        if event_count == 5:
            break
    print()

def main(args):
    now = datetime.datetime.now()
    print(f'{now}...\n')
    if args['project']:
        list_project()
    elif args['user']:
        list_user()
    elif args['vm']:
        project_id = args['vm']
        list_vm(project_id)
    else:
        list_project(_print=False)
        list_user(_print=False)
        vms = args['vms']
        for vm in vms:
            show_vm(vm)
    print()


if __name__ == "__main__":
    parser =  argparse.ArgumentParser(description='openstack command warpper warpper')
    parser.add_argument('--project', action='store_true', help='list project')
    parser.add_argument('--user', action='store_true', help='list user')
    parser.add_argument('--vm', help='list project vm.')
    parser.add_argument('--write', help='write to file')
    parser.add_argument('vms', nargs='*')
    args = vars(parser.parse_args(sys.argv[1:]))
    main(args)
