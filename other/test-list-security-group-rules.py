#!/usr/bin/env python3

import openstack, sys


def main():
    if len(sys.argv) == 1:
        print(f'Missing project ID argument.')
        return

    project_id = sys.argv[1]
    conn = openstack.connect()
    sec_group_rules = [i for i in conn.network.security_group_rules() if i['project_id'] == project_id]
    for r in sec_group_rules:
        #print(f'{r}')
        print((f'{r.id} {r.direction} {r.protocol} {r.port_range_max} {r.remote_ip_prefix} {r.remote_group_id}'))


if __name__ == '__main__':
    main()

