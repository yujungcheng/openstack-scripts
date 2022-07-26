#!/usr/bin/python
""" Check Loadbalancer status include listener and member status.
    Usage: ./osp-loadbalancer-check.py -c <Cloud Name> [ <LoadBalancer ID> <LoadBalancer ID> ... ]
    Arguments:
      -c <cloud name>  # require clouds.yaml
    
    execute command without specify loadbalancer ID to list of load balancer.
"""

import sys
import yaml
import argparse
import openstack

def get_ip_addresses(conn):
    """ return IP addresses info in dict
    """
    ports = {}
    for port in conn.network.ports():
        if len(port.fixed_ips) != 0:
            ports[port.id] = {'address': port.fixed_ips[0]['ip_address'], 'name': port.name}
    ip_addresses = {}
    for trunk in conn.network.trunks():
        trunk_port_id = trunk.port_id
        trunk_name = trunk.name.split('.')[0]
        if trunk.port_id in ports:
            address = ports[trunk.port_id]['address']
            ip_addresses[address] = {'node': trunk_name, 'vlan': None}
        for subport in trunk.sub_ports:
            if subport['port_id'] in ports:
                address = ports[subport['port_id']]['address']
                ip_addresses[address] = {'node': trunk_name, 
                                         'vlan': subport['segmentation_id']}
    return ip_addresses
            
def get_servers(conn):  # unused
    """ return IP and server hostname dict
        each server should have single IP assigned
    """
    servers = {}
    for server in conn.compute.servers():
        for key, values in server.addresses.items():
            for value in values:
                #print("%s %s" % (value['addr'], server.name.split('.')[0]))
                servers[value['addr']] = server.name.split('.')[0]
    return servers

def main(args):
    #print(args)
    cloud_name = args.cloud_name
    output_format = args.output_format
    list_loadbalancer = args.list_loadbalancer
    lb_ids = args.lb

    conn = openstack.connect(cloud=cloud_name)    
    addresses = get_ip_addresses(conn)

    if list_loadbalancer == True or len(lb_ids) == 0:
        for lb in conn.load_balancer.load_balancers():
            print("%s %s" % (lb.id, lb.name)) 
        exit(0)

    lbs_status = []
    for lb_id in lb_ids:
        lb = conn.load_balancer.get_load_balancer(lb_id)
        lb_status = {}
        lb_status['id'] = lb_id
        lb_status['name'] = lb.name
        lb_status['created_at'] = lb.created_at
        lb_status['updated_at'] = lb.updated_at
        lb_status['is_admin_state_up'] = lb.is_admin_state_up
        lb_status['vip_address'] = lb.vip_address
        lb_status['vip_port'] = lb.vip_port_id
        lb_status['vip_network_id'] = lb.vip_network_id
        #status['listeners'] = lb.listeners
        #status['pools'] = lb.pools

        lss_status = []
        listener_ids = lb.listeners
        for listener_id in listener_ids:
            ls = conn.load_balancer.get_listener(listener_id)
            ls_status = {}
            ls_status['id'] = ls.id
            ls_status['name'] = ls.name
            ls_status['created_at'] = ls.created_at 
            ls_status['updated_at'] = ls.updated_at
            #ls_status['allowed_cidrs'] = ls.allowed_cidrs  # not support 
            ls_status['is_admin_state_up'] = ls.is_admin_state_up
            ls_status['operating_status'] = ls.operating_status 
            ls_status['protocol'] = ls.protocol 
            ls_status['protocol_port'] = ls.protocol_port
            ls_status['provisioning_status'] = ls.provisioning_status
            ls_status['default_pool_id'] = ls.default_pool_id

            pl = conn.load_balancer.get_pool(ls.default_pool_id)
            ls_status['lb_algorithm'] = pl.lb_algorithm
            ls_status['pool_name'] = pl.name
            ls_status['operating_status'] = pl.operating_status
            #ls_status['tls_enabled']  = pl.tls_enabled  # not support
            #ls_status['members'] = pl.members

            mms_status = []
            for mm in conn.load_balancer.members(ls.default_pool_id):
                mm_status = {}
                mm_status['id'] = mm.id
                mm_status['name'] = mm.name
                mm_status['node'] = ""
                if mm.address in addresses:
                    mm_status['node'] = addresses[mm.address]['node']
                    mm_status['vlan'] = addresses[mm.address]['vlan']
                mm_status['created_at'] = mm.created_at
                mm_status['updated_at'] = mm.updated_at
                mm_status['address'] = mm.address
                mm_status['is_admin_state_up'] = mm.is_admin_state_up
                mm_status['operating_status'] = mm.operating_status
                #mm_status['weight'] = mm.weight
                #mm_status['backup'] = mm.backup
                mms_status.append(mm_status)

            ls_status['members_status'] = mms_status
            lss_status.append(ls_status)

        lb_status['listeners_status'] = lss_status

        if output_format == "yaml":
            print("---")
            print(yaml.safe_dump(lb_status, default_flow_style=False))
        elif output_format == "simple":
            print("")
            print("%s | admin_up=%s, vip=%s" % (
                lb_status['name'], lb_status['is_admin_state_up'], lb_status['vip_address']))
            for ls_status in lb_status['listeners_status']:
                print("    %s:%s | admin_up=%s, operating_status=%s" % (
                    ls_status['protocol'], ls_status['protocol_port'], ls_status['is_admin_state_up'],
                    ls_status['operating_status']))
                for mm_status in ls_status['members_status']:
                    print("        %s | name=%s, node=%s, vlan=%s, admin_up=%s, operating_status=%s" % (
                    mm_status['address'], mm_status['name'], mm_status['node'], mm_status['vlan'],
                    mm_status['is_admin_state_up'], mm_status['operating_status']))
        else:
            # print dict obj
            print(lb_status)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get load balancer status.')
    parser.add_argument("-c", "--cloud-name", default="openstack", type=str, required=True, help="cloud name")
    parser.add_argument("-o", "--output-format",  default="simple", type=str, help="output format, [yaml, dict, simple], default simple")
    parser.add_argument("-l", "--list-loadbalancer", action='store_true', help="list load balancer")
    parser.add_argument("lb", nargs=argparse.REMAINDER, help='load balancer ID')
    args = parser.parse_args()
    main(args)
