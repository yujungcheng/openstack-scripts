#!/usr/bin/env python3


import os
import sys
import itertools
import subprocess
import datetime
import openstack

conn = openstack.connect()


def list_project(_print=True):
    #projects = [project.id for project in conn.list_projects()]
    for project in conn.list_projects():
        if _print:
            print(f'{project.id} | {project.name}')

def list_network(project_id):
    project = conn.get_project(project_id)
    roject_conn = conn.connect_as_project(project)
    for network in roject_conn.list_networks():
        print((f'Network: {network.id} | {network.name} | '
            f'SegmentationID:{network["provider:segmentation_id"]}'))
        subnets = network.subnets
        for subnet in subnets:
            subnet_info = conn.get_subnet_by_id(subnet)
            dns_nameservers = subnet_info.dns_nameservers
            dhcp_enabled = subnet_info.enable_dhcp
            gateway_ip = subnet_info.gateway_ip
            cidr = subnet_info.cidr
            allocation_pools = subnet_info.allocation_pools
            print((f'  Subnet: {subnet} | {cidr} | {gateway_ip} | {dns_nameservers} | '
                f'{dhcp_enabled} | {allocation_pools}'))

def list_router(project_id):
    project = conn.get_project(project_id)
    project_conn = conn.connect_as_project(project)
    routers = project_conn.list_routers()
    for router in routers:
        print(f'Router: {router.id} | {router.name} | {router.status} | HA:{router.ha} | {router.created_at}')

def show_network(network_id):
    ''' show network info include subnet/port/router/route '''
    network = conn.get_network(network_id)
    if network == None:
        print(f'Network not found')
        exit()
    segmentation_id = network['provider:segmentation_id']
    subnets = ','.join(network['subnets'])

    print(f'Network: {network.id} | {network.name} | SegmentID:{segmentation_id}')
    print(f'  Project ID: {network.project_id}')
    print(f'  Subnets:')
    for subnet in network['subnets']:
        subnet_info = conn.get_subnet_by_id(subnet)
        dhcp_enabled = subnet_info.enable_dhcp
        dns_nameservers = subnet_info.dns_nameservers
        gateway_ip = subnet_info.gateway_ip
        cidr = subnet_info.cidr
        allocation_pools = subnet_info.allocation_pools
        print((f'    Subnet: {subnet} | {cidr} | {gateway_ip} | {dns_nameservers} | '
               f'{dhcp_enabled} | {allocation_pools}'))
        ext = conn.get_network_extensions()

    print(f'  Ports:')
    project_id = network.project_id
    project = conn.get_project(project_id)
    project_conn = conn.connect_as_project(project)
    ports = project_conn.list_ports()
    for p in ports:
        if p.network_id == network_id:
            print(f'    Port: {p.id} | {p.name} | {p.mac_address} | {p.status}')
            print(f'      Fixed IPs:')
            for fixed_ip in p.fixed_ips:
                print(f'        {fixed_ip["ip_address"]} | {fixed_ip["subnet_id"]}')

def show_router(router_id):
    ''' show router info include interfaces '''
    router = conn.get_router(router_id)
    if router == None:
        print(f'Router not found')
        exit()
    print(f'Router: {router.id} | {router.name} | {router.status} | HA:{router.ha} | {router.created_at}')
    r_ifs = conn.list_router_interfaces(router)
    for r_if in r_ifs:
        print(f'  Interface: {r_if.id} | {r_if.name} | {r_if.mac_address} | {r_if.status} ')
        network = conn.get_network(r_if.network_id)
        print(f'    Network: {r_if.network_id } | {network.name}')

        print(f'    FixedIPs:')
        fixed_ips = r_if.fixed_ips
        for fixed_ip in fixed_ips:
            print(f'      {fixed_ip["ip_address"]} | {fixed_ip["subnet_id"]}')

        print(f'    DNS:')
        dns_assignment = r_if.dns_assignment
        for dns in dns_assignment:
            print(f'      {dns["hostname"]} | {dns["ip_address"]} | {dns["fqdn"]}')

        print(f'    Security Groups:')
        security_groups = r_if["security_groups"]
        for sg in security_groups:
            print(f'      Security Group: {sg}')

        host_id = r_if["binding:host_id"]
        device_owner = r_if["device_owner"]
        port_security_enabled = r_if["port_security_enabled"]
        admin_state_up = r_if["admin_state_up"]
        created_at = r_if["created_at"]


def main(argv):
    if len(argv) == 0:
        print(f'Missing arguments')
        exit()
    if len(argv) >= 2:
        if argv[0] == "list":
            if argv[1] == "project":
                list_project()
            elif argv[1] == "network":
                if len(argv) == 3:
                    list_network(argv[2])
                else:
                    print(f'Missing project ID')
            elif argv[1] == "router":
                if len(argv) == 3:
                    list_router(argv[2])
                else:
                    print(f'Missing project ID')
            else:
                print(f'Invalid arguments')
        elif argv[0] == "show":
            if argv[1] == "network":
                if len(argv) == 3:
                    show_network(argv[2])
                else:
                    print(f'Missing network ID')
            elif argv[1] == "router":
                if len(argv) == 3:
                    show_router(argv[2])
                else:
                    print(f'Missing Router ID')
        else:
            print(f'Invalid arguments')
    return


if __name__ == "__main__":
    argv = sys.argv[1:]
    main(argv)
