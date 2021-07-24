#!/usr/bin/python3
'''
Get rbd du output in json format.
  "rbd du -p <Pool Name> --format json"

Sample json output
{"images":[{"name":"volume-2b537c04-d79b-4170-ad17-9f91fd9138ce","snapshot":"volume-d7f3b3a0-e8d6-4e42-bebc-b2447010b88b.clone_snap","provisioned_size":3221225472,"used_size":1090519040},
           {"name":"volume-2b537c04-d79b-4170-ad17-9f91fd9138ce","provisioned_size":3221225472,"used_size":0},
           {"name":"volume-364b575f-8941-4f04-908e-3753dc133468","snapshot":"snapshot-9c5f7f90-609a-426e-9a2e-ae2eaf105fb5","provisioned_size":2147483648,"used_size":0},
           {"name":"volume-364b575f-8941-4f04-908e-3753dc133468","provisioned_size":2147483648,"used_size":0},
           {"name":"volume-5279235b-18b0-457b-9958-340d95076172","provisioned_size":26843545600,"used_size":16177430528},
           {"name":"volume-a15666fc-27df-4242-a27f-fa181c6cf59e","provisioned_size":3221225472,"used_size":1090519040},
           {"name":"volume-b0d4d3c9-6166-45b8-a252-6829722a1258","provisioned_size":2147483648,"used_size":0},
           {"name":"volume-d7f3b3a0-e8d6-4e42-bebc-b2447010b88b","provisioned_size":3221225472,"used_size":0}],
 "total_provisioned_size":40802189312,
 "total_used_size":18358468608}

'''

import sys
import time
import json
import openstack

from common import format_datetime


delimiter = '|'

def main(argv):
    try:
        rbd_df_json_file = argv[0]
        #print(rbd_df_json_file)

        fp = open(rbd_df_json_file)
        rbd_df_json_data = json.load(fp)
        fp.close()

        images = rbd_df_json_data['images']
        total_provisioned_size = rbd_df_json_data['total_provisioned_size']
        total_used_size = rbd_df_json_data['total_used_size']
        print(f'total_used_size/total_provisioned_size: {total_used_size}/{total_provisioned_size}\n')
    except Exception as e:
        print(e)
        sys.exit(1)

    try:
        conn = openstack.connect()
        for image in images:
            name = image['name']
            volume_id = name.replace('volume-', '').replace('.deleted', '')
            provisioned_size = str(image['provisioned_size'])
            used_size = str(image['used_size'])
            if 'snapshot'  in image:
                snapshot = image['snapshot']
                if ".deleted" not in name:
                    volume = conn.get_volume(volume_id)
                    volume_name = volume.name
                    created_at = format_datetime(volume.created_at, add_hours=10)
                    volume_tenant_id = volume.__dict__['os-vol-tenant-attr:tenant_id']
                    try:
                        volume_tenant = conn.get_project(volume_tenant_id)
                        tenant_name = volume_tenant.name
                    except Exception as e:
                        tenant_name = "Unknown (deleted)"
                    try:
                        snap_created_at = "Unknown"
                        if "snapshot-" in snapshot:  # a snapshot created from a volume
                            snapshot_id = snapshot.replace('snapshot-', '')
                            snap = conn.get_volume_snapshot_by_id(snapshot_id)
                            snap_created_at = format_datetime(snap.created_at, add_hours=10)
                        elif ".clone_snap" in snapshot:  # volume created from a volume (snapshot created from source volume)
                            child_volume_id = snapshot.replace('volume-', '').replace('.clone_snap', '')
                            vol = conn.get_volume(child_volume_id)
                            snap_created_at = format_datetime(vol.created_at, add_hours=10)
                    except Exception as e:
                        snap_created_at = "Unknown (deleted)"
                    volume_info = (tenant_name, created_at, volume_id, volume_name, provisioned_size, used_size, snap_created_at, snapshot)
            else:
                if ".deleted" not in name:
                    volume = conn.get_volume(volume_id)
                    volume_name = volume.name
                    created_at = format_datetime(volume.created_at, add_hours=10)
                    volume_tenant_id = volume.__dict__['os-vol-tenant-attr:tenant_id']
                    try:
                        volume_tenant = conn.get_project(volume_tenant_id)
                        tenant_name = volume_tenant.name
                    except Exception as e:
                        tenant_name = "Unknown (deleted)"
                    volume_info = (tenant_name, created_at, volume_id, volume_name, provisioned_size, used_size)

            print(f' {delimiter} '.join(volume_info))
    except Exception as e:
        print("Error: %s" % e)


if __name__ == '__main__':
    main(sys.argv[1:])

