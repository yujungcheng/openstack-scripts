#!/usr/bin/env python3


from datetime import datetime, timedelta


def get_project(conn):
    # return [project.id for project in conn.list_projects()]
    all_projects = {}
    for project in conn.list_projects():
        all_projects[project.id] = project.name
    return all_projects

def get_user(conn):
    # return [user.id for user in conn.list_users()]
    all_users = {}
    for user in conn.list_users():
        all_users[user.id] = user.name
    return all_users

def write_to_file(filename, data, mode='w'):
    try:
        with open(filename, mode) as f:
            f.write(data)
        return True
    except Exception as e:
        print(f'write_to_file error: {e}')
        return False

def format_datetime(datetime_string, add_hours=None):
    ''' expected two type of dateimte string format input'''
    try:
        dt_obj = datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%S.%f')
    except:
        dt_obj = datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%SZ')
    if add_hours == None:
        return str(dt_obj)
    return str(dt_obj + timedelta(hours=add_hours))
