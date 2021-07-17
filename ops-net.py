#!/usr/bin/env python3


import os
import sys
import itertools
import subprocess
import datetime
import openstack

conn = openstack.connect()


def list_project():
    for project in conn.list_projects():
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
    for subnet_id in network['subnets']:
        s = conn.get_subnet_by_id(subnet_id)
        print((f'    Subnet: {s.id} | {s.cidr} | {s.gateway_ip} | {s.dns_nameservers} | '
               f'DHCP:{s.enable_dhcp}'))
        print(f'      DHCP Allocation Pools:')
        allocation_pools = s.allocation_pools
        for pool in allocation_pools:
            print(f'        {pool["start"]} - {pool["end"]}')
        
    print(f'  Ports:')
    project_id = network.project_id 
    project = conn.get_project(project_id)
    project_conn = conn.connect_as_project(project)
    ports = project_conn.list_ports()
    for p in ports:
        if p.network_id == network_id:
            print(f'    Port: {p.id} | {p.name} | {p.status}')
            print(f'      MAC Address: {p.mac_address}')
            print(f'      Device ID: {p.device_id}')
            print(f'      Fixed IPs:')
            for fixed_ip in p.fixed_ips:
                print(f'        {fixed_ip["ip_address"]} | {fixed_ip["subnet_id"]}')

def show_router(router_id):
    ''' show router info include interfaces '''
    router = conn.get_router(router_id)
    if router == None:
        print(f'Router not found')
        exit()
    print((f'Router: {router.id} | {router.name} | {router.status} | HA:{router.ha} | '
           f'{router.external_gateway_info} | {router.created_at}'))
    ifs = conn.list_router_interfaces(router)
    for i in ifs:
        print(f'  Interface: {i.id} | {i.name} | {i.mac_address} | {i.status} ')
        network = conn.get_network(i.network_id)
        print(f'    Network: {i.network_id } | {network.name}')

        print(f'    Binding Host ID: {i["binding:host_id"]}')
        print(f'    Device Owner: {i["device_owner"]}')
        print(f'    Port Security Enabled: {i["port_security_enabled"]}')
        print(f'    Admin State Up: {i["admin_state_up"]}')
        print(f'    Created At: {i["created_at"]}')
        
        print(f'    FixedIPs:')
        fixed_ips = i.fixed_ips
        for fixed_ip in fixed_ips:
            print(f'      {fixed_ip["ip_address"]} | {fixed_ip["subnet_id"]}')

        print(f'    DNS:')
        dns_assignment = i.dns_assignment
        for dns in dns_assignment:
            print(f'      {dns["hostname"]} | {dns["ip_address"]} | {dns["fqdn"]}')

        print(f'    Security Groups:')
        security_groups = i["security_groups"]
        for sg in security_groups:
            print(f'      Security Group: {sg}')


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
