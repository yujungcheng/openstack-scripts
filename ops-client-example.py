#!/usr/bin/python3
'''
!!! for python2, update sha-bang to /usr/bin/python2

# OS: 18.04.2 LTS

# pip3 install
- openstackclient                4.0.0
- openstacksdk                   0.53.0
- python-openstackclient         5.4.0

# Sample output
[ environment variable ]
  * auth_url    : https://stage01-api.vaultsystems.com.au:5443
  * project_id  : 8d5f1933b703430698d2d2eb34a2f70a
  * project_name: admin
[ test - session ]
  * use v3 auth password
[ test - keystone ]
  * keystone client version: <class 'keystoneclient.v3.client.Client'>
  * tenant count: 3
  * service count: 13
  * endpoint count: 39
[ test - glance ]
  * image count: 5
[ test - nova ]
  * hypervisor count: 3
  * server count: 3
  * keypair count: 1
  * flavor count: 26
[ test - cinder ]
  * volume count: 3
  * snapsthot count: 0
  * quota gigabytes: {'reserved': 0, 'allocated': 0, 'limit': 1000, 'in_use': 73}
  * quota backup_gigabytes: {'reserved': 0, 'allocated': 0, 'limit': 1000, 'in_use': 61}
  * quota snapshots: {'reserved': 0, 'allocated': 0, 'limit': 10, 'in_use': 0}
  * quota volumes: {'reserved': 0, 'allocated': 0, 'limit': 10, 'in_use': 2}
[ test - neutron ]
  * network count: 1
  * subnet count: 1
  * router count: 1
  * agent count: 1
  * port count: 1
  * address_scopes count: 1
  * security_groups count: 1
  * security_group_rules count: 1
[ test - swift ]
  * account container count: 3
  * account object count: 5
  * container object count: backup, 5
  * container object count: container1, 0
  * container object count: volumebackups, 0
'''

import os

from keystoneauth1 import session
from keystoneauth1.identity import v3
from keystoneauth1.identity import v2
from keystoneclient import client as client_keystone
from keystoneclient.v2_0 import client as client_keystone_v2
from keystoneclient.v3 import client as client_keystone_v3

from novaclient import client as client_nova
from glanceclient.v2 import client as client_glance
from cinderclient import client as client_cinder
from neutronclient.v2_0 import client as client_neutron
from swiftclient import client as client_swift


def get_session(url, username, password, project_name,
                user_domain_id='default', project_domain_id='default', version='3'):
    if str(version) == '2':
        auth = v2.Password(auth_url=url,
                           username=username,
                           password=password,
                           tenant_name=project_name)
        print("  * use v2 auth password")
    else:
        auth = v3.Password(auth_url=url,
                           username=username,
                           password=password,
                           project_name=project_name,
                           user_domain_id=user_domain_id,
                           project_domain_id=project_domain_id)
        print("  * use v3 auth password")
    return session.Session(auth=auth)


def main():
    auth_url = os.environ['OS_AUTH_URL']
    username = os.environ['OS_USERNAME']
    password = os.environ['OS_PASSWORD']

    if "OS_PROJECT_NAME" in os.environ:
        project_name = os.environ['OS_PROJECT_NAME']
    elif "OS_TENANT_NAME" in os.environ:
        project_name = os.environ['OS_TENANT_NAME']
    if "OS_PROJECT_ID" in os.environ:
        project_id = os.environ['OS_PROJECT_ID']
    elif "OS_TENANT_ID" in os.environ:
        project_id = os.environ['OS_TENANT_ID']

    print("[ environment variable ]")
    print("  * auth_url    : %s" % auth_url)
    print("  * project_id  : %s" % project_id)
    print("  * project_name: %s" % project_name)

    try:
        print("[ test - session ]")
        # create v3 session if "v2.0" is not specified in AUTH_URL.
        if auth_url.endswith('/v2.0') or auth_url.endswith('/v2.0/'):
            auth_session = get_session(auth_url, username, password, project_name, version='2')
        else:
            if not (auth_url.endswith('/v3') or auth_url.endswith('/v3/')):
                if auth_url[-1] == '/':
                    auth_url += 'v3'
                else:
                    auth_url += '/v3'
            auth_session = get_session(auth_url, username, password, project_name, version='3')
    except Exception as e:
        print(e)

    try:
        print("[ test - keystone ]")
        #keystone = client_keystone_v2.Client(session=auth_session) # use v2
        #keystone = client_keystone_v3.Client(session=auth_session) # use v3
        keystone = client_keystone.Client(session=auth_session) # let keystone client decide v2 or v3 base on session
        print("  * keystone client version: %s" % type(keystone))

        if hasattr(keystone, 'tenants'):
            tenants = keystone.tenants.list()
        if hasattr(keystone, 'projects'):
            tenants = keystone.projects.list()
        print("  * tenant count: %s" % len(tenants))
        services = keystone.services.list()
        print("  * service count: %s" % len(services))
        endpoints = keystone.endpoints.list()
        print("  * endpoint count: %s" % len(endpoints))
    except Exception as e:
        print(e)

    try:
        print("[ test - glance ]")
        glance = client_glance.Client('2', session=auth_session)
        images = glance.images.list() # return a python generator; https://docs.openstack.org/mitaka/user-guide/sdk_manage_images.html
        images_list = list(images)
        print("  * image count: %s" %len(images_list))
    except Exception as e:
        print(e)

    try:
        print("[ test - nova ]")
        nova = client_nova.Client(2, session=auth_session)
        hypervisors = nova.hypervisors.list()
        print("  * hypervisor count: %s" % len(hypervisors))
        servers = nova.servers.list()
        print("  * server count: %s" % len(servers))
        keypairs = nova.keypairs.list()
        print("  * keypair count: %s" % len(keypairs))
        flavors = nova.flavors.list()
        print("  * flavor count: %s" % len(flavors))
    except Exception as e:
        print(e)

    try:
        print("[ test - cinder ]")
        cinder = client_cinder.Client('2.0', session=auth_session)
        volumes = cinder.volumes.list()
        print("  * volume count: %s" % len(volumes))
        snapshots = cinder.volume_snapshots.list()
        print("  * snapsthot count: %s" % len(snapshots))
        quotas = cinder.quotas.get(tenant_id=project_id, usage=True)
        print("  * quota gigabytes: %s" % (quotas.gigabytes))
        print("  * quota backup_gigabytes: %s" % (quotas.backup_gigabytes))
        print("  * quota snapshots: %s" % (quotas.snapshots))
        print("  * quota volumes: %s" % (quotas.volumes))
    except Exception as e:
        print(e)

    try:
        print("[ test - neutron ]")
        neutron = client_neutron.Client(session=auth_session)
        networks = neutron.list_networks()
        print("  * network count: %s" % len(networks))
        subnets = neutron.list_subnets()
        print("  * subnet count: %s" % len(subnets))
        routers = neutron.list_routers()
        print("  * router count: %s" % len(routers))
        agents = neutron.list_agents()
        print("  * agent count: %s" % len(agents))
        ports = neutron.list_ports()
        print("  * port count: %s" % len(ports))
        address_scopes = neutron.list_address_scopes()
        print("  * address_scopes count: %s" % len(address_scopes))
        security_groups = neutron.list_security_groups()
        print("  * security_groups count: %s" % len(security_groups))
        security_group_rules = neutron.list_security_group_rules()
        print("  * security_group_rules count: %s" % len(security_group_rules))
    except Exception as e:
        print(e)

    try:
       print("[ test - swift ]")
       swift = client_swift.Connection(session=auth_session)
       account = swift.get_account()[0]
       containers = swift.get_account()[1]
       account_container_count = account['x-account-container-count']
       print("  * account container count: %s" % account_container_count)
       account_object_count = account['x-account-object-count']
       print("  * account object count: %s" % account_object_count)
       for container in containers:
          name = container['name']
          count = container['count']
          print("  * container object count: %s, %s" % (name, count))
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()

