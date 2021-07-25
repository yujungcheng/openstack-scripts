#!/usr/bin/env python3
# Query openstack database to instance last start/stop/create action.

import sys
import mysql.connector

global nova_cursor
global cinder_cursor
nova_db = mysql.connector.connect(host="127.0.0.1",
                                  user="root",
                                  passwd="********",
                                  database="nova")
nova_cursor = nova_db.cursor()
cinder_db = mysql.connector.connect(host="127.0.0.1",
                                    user="root",
                                    passwd="********",
                                    database="cinder")
cinder_cursor = cinder_db.cursor()


def execute_nova_query(sql):
    nova_cursor.execute(sql)
    return nova_cursor.fetchall()

def execute_cinder_query(sql):
    cinder_cursor.execute(sql)
    return cinder_cursor.fetchall()


def main():
    if len(sys.argv) <= 1:
        sys.exit(1)

    project_id = sys.argv[1]

    sql = "SELECT created_at, uuid, display_name, root_gb FROM instances WHERE `project_id`='%s'" % project_id
    #print(sql)
    instance_result = execute_nova_query(sql)
    #print(result)

    for instance_item in instance_result:
        instance_created_at = instance_item[0]
        uuid = instance_item[1]
        name = instance_item[2]
        size = instance_item[3]

        sql = "SELECT mountpoint FROM volume_attachment WHERE instance_uuid='%s' AND attach_status='attached'" % uuid
        volume_result = execute_cinder_query(sql)
        attached_volumes = list()
        for volume_item in volume_result:
            mount_point = volume_item[0]
            device_name = mount_point.replace("/dev/", "")
            attached_volumes.append(device_name)
        attached_volume = ",".join(attached_volumes)

        sql = "SELECT created_at, action FROM instance_actions WHERE `instance_uuid`='%s' AND (`action`='start' OR `action`='create' OR `action`='stop') ORDER BY created_at DESC limit 1" % uuid
        action_result = execute_nova_query(sql)
        for action_item in action_result:
            action_created_at = action_item[0]
            action_name = action_item[1]
            print("%s|%s|%s|%s|%s|%s" % (instance_created_at, name, size, attached_volume, action_created_at, action_name))


if __name__ == '__main__':
    main()

