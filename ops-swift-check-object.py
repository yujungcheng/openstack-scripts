#!/usr/bin/env python3
'''
Scan objects in a container.

Object could exist in contianer database but actual data object does not exist on disk.
Multithread is implemented for scan large amount of objects.

Work in Python 3.7.9, openstacksdk (0.46.0-0ubuntu1) (apt install)

Arguments:
 --cloud <cloud name>                     name defined in cloud.yaml file.
 --projectname <project name/ID>          project name or ID
 --container <container name>             container name
 --worker <number>                        optional, number of concorrent worker to check. default 128
 --resume                                 optional, resume from last checked object
 --objectlistfile <file path>             optional, read object name form file (base on result file from this script)

v1.0 - initial version
v1.1 - able to read object name from file, add result file name with cloud name
v1.2 - code refine
'''

import os
import time
import argparse
import logging
import openstack
import urllib.parse

from datetime import datetime
from openstack import exceptions

import _thread
from threading import Thread
from queue import Queue


delimiter = '|'
queue_size = 1000
result_log_file = './results.log'


class Worker(Thread):
    def __init__(self, log, task_queue, done_queue, stop_task=None):
        Thread.__init__(self)
        self.log = log
        self.task_queue = task_queue
        self.done_queue = done_queue

        self.stop_task = stop_task
        self.project_conn = None
        self.container_name = None
        self.task_get_count = 0
        self.max_retry = 5

    def set_worker(self, conn=None, container_name=None):
        self.project_conn = conn
        self.container_name = container_name

    def run(self):
        while True:
            try:
                task = self.task_queue.get()
                self.task_get_count += 1

                if task is self.stop_task:
                    break

                statistic = {'200': 0, '404': 0, '504': 0}
                for i in range(self.max_retry):
                    result = self.check_swift_object_func(task)
                    self.log.debug((f'{self.name} {delimiter} {self.task_get_count} '
                                    f'{delimiter} {task} {delimiter} {result}'))
                    if isinstance(result, dict):
                        statistic['200'] += 1
                        break
                    elif result == 404:
                        statistic['404'] += 1
                        time.sleep(1)
                    elif result == 504:
                        statistic['504'] += 1
                        time.sleep(10)

                self.task_queue.task_done()
                task['result'] = result
                task['statistic'] = statistic
                self.done_queue.put(task)
            except Exception as e:
                self.log.error("%s could not execute task. task name = %s, %s" %(self.name, task, e))
                continue

    def check_swift_object_func(self, task, return_meta=True):
        try:
            object_name = task['object_name']
            # https://docs.openstack.org/swift/latest/api/object_api_v1_overview.html
            #   You must UTF-8-encode and then URL-encode container and object names before you call the API binding.
            #   If you use an API binding that performs the URL-encoding for you, do not URL-encode the names before you call the API binding.
            #   Otherwise, you double-encode these names. Check the length restrictions against the URL-encoded string.
            object_name = object_name.encode(encoding='UTF-8', errors='strict')
            object_name = urllib.parse.quote(object_name)
            result = self.project_conn.object_store.get_object_metadata(object_name, self.container_name)
            return {'create_method': result.create_method,
                    'timestamp': result.timestamp,
                    'last_modified_at': result.last_modified_at,
                    'etag': result.etag,
                    'size': str(result.content_length),
                    'manifest': str(result.object_manifest)}

        except exceptions.ResourceNotFound as e:  # HTTP 404 is missing from swift backend storage
            #print(f'ResourceNotFound: {e}')
            now = datetime.now()
            dt_string = now.strftime("%d-%m-%Y %H:%M:%S")
            logging.debug(f'ResourceNotFound@{dt_string}: {e}')
            return 404
        except exceptions.HttpException as e:  # HTTP 504, for example. network/application issue
            #print(f'HttpException: {e}')
            now = datetime.now()
            dt_string = now.strftime("%d-%m-%Y %H:%M:%S")
            logging.debug(f'HttpException@{dt_string}: {e}')
            return 504


# check task result thread function
def check_task_result(log, done_queue, output_file, project_name, container_name,
                      result_log_file=result_log_file):
    collect_count = 0
    success_count = 0
    fail_count = 0
    while True:
        try:
            task = done_queue.get()
            now = datetime.now()
            dt_string = now.strftime("%d-%m-%Y %H:%M:%S")
            if task == None:
                log.info((f'Total {collect_count} task collected, '
                          f'{success_count} valid objects, '
                          f'{fail_count} lost objects.'))
                with open(result_log_file, 'a') as writer:
                    writer.write((f'{dt_string} {delimiter} '
                                  f'{project_name} {delimiter} '
                                  f'{container_name} {delimiter} '
                                  f'{collect_count} tasks {delimiter} '
                                  f'{success_count} success  {delimiter} '
                                  f'{fail_count} fails {delimiter} '
                                  f'{output_file}\n'))
                done_queue.task_done()
                break

            collect_count += 1
            object_name = task['object_name']
            result = task['result']
            statistic = task['statistic']

            log.debug((f'{dt_string} {delimiter} '
                       f'{collect_count} {delimiter} '
                       f'{result} {delimiter} '
                       f'{statistic["200"]}/{statistic["404"]}/{statistic["504"]} {delimiter}'
                       f'{object_name}'))

            if statistic["200"] == 1:
                success_count += 1
                checked_data = (dt_string, str(collect_count), "OK",
                                result["create_method"],
                                result["timestamp"],
                                result["last_modified_at"],
                                result["etag"],
                                result["size"],
                                result["manifest"],
                                object_name)
            else:
                fail_count += 1
                checked_data = (dt_string, str(collect_count), "NO", object_name)

            write_data = f' {delimiter} '.join(checked_data)
            with open(output_file, 'a') as writer:
                writer.write(f'{write_data}\n')
            done_queue.task_done()
        except Exception as e:
            log.info(f'Error occur when collect task result {result}. {e}')
            #continue

def init_argparse():
    parser = argparse.ArgumentParser(description='Find the objects in a swift container that are missing from disk.')
    parser.add_argument('--cloud', required=True, help='the cloud as defined in clouds.yaml')
    parser.add_argument('--projectname', required=True, help='openstack customer project name')
    parser.add_argument('--containername', required=True, help='openstack swift container name')
    parser.add_argument('--worker', default=32 , help='number of worker threads (default 32)')
    parser.add_argument('--resume', action='store_true', help='resume from last checked object')
    parser.add_argument('--objectlistfile', default=False, help='read objects from object list file')
    return parser

def main(args):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(filename)s %(levelname)s %(message)s',)
    logging.info(f'Connecting in to cloud: {args.cloud}')
    conn = openstack.connect(cloud=args.cloud)
    logging.info(f'Switching into project: {args.projectname}')
    project_conn = conn.connect_as_project(args.projectname)
    logging.info(f'Using container: {args.containername}')
    container_name = args.containername
    logging.info(f'Set max workers to {args.worker}')
    max_worker = int(args.worker)
    logging.info(f'Object list file: {args.objectlistfile}')
    object_list_file = args.objectlistfile
    output_file = f'result.{args.cloud}.{args.projectname}.{args.containername}.txt'
    logging.info(f'Output file name: {output_file}')

    if args.resume:
        last_line = False
        with open(f'{output_file}', 'rb') as f:
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b'\n':
                f.seek(-2, os.SEEK_CUR)
            last_line = f.readline().decode()
        if last_line:
            line_arr = last_line.split(delimiter)
            last_object_name = line_arr[-1]
            last_object_count = int(line_arr[1])
            logging.info(f'Resume from last checked object {last_object_name}, count {last_object_count}')

    # initialize queues
    task_queue = Queue(queue_size)
    done_queue = Queue()

    # initialize thread workers
    logging.info(f'Initialize worker threads')
    workers = [ Worker(logging, task_queue, done_queue) for i in range(max_worker) ]
    for worker in workers:  # set connection & container name and start each worker
        worker.set_worker(conn.connect_as_project(args.projectname), container_name)
        worker.start()

    # initialize a thread for collecting done tasks.
    logging.info(f'Initialize collector thread')
    collector = _thread.start_new_thread(check_task_result, (logging, done_queue, output_file,
                                                             args.projectname, container_name))

    # submit tasks
    logging.info(f'Submitting tasks.')
    try:
        submit_counter = 0
        if object_list_file == False:  # get object list from swift
            # another method to get object list, but only return max 10000 objects by default
            '''
            object_list = project_conn.list_objects(container_name)
            for obj in object_list:
            '''
            for obj in project_conn.object_store.objects(container_name): # return a iterator to go through all objects
                if args.resume and submit_counter < last_object_count:
                    submit_counter += 1
                    continue
                task = {'object_name': obj.name}
                logging.debug(f'put task {task}')
                task_queue.put(task)
                submit_counter += 1
        else:  # read object list from file
            object_list = open(object_list_file, 'r')
            for obj_line in object_list:
                if args.resume and submit_counter < last_object_count:
                    submit_counter += 1
                    continue
                obj_info = obj_line.split(delimiter)
                obj_name = obj_info[-1]  # last item should be object name
                task = {'object_name': obj_name.strip()}
                logging.debug(f'put task {task}')
                task_queue.put(task)
                submit_counter += 1
        logging.info(f'Total {submit_counter} tasks submited')

    except Exception as e:
        logging.error(f'Fail to submit tasks. {e}')

    # submit stop signal task to stop worker threads
    logging.debug(f'Sent None task to stop worker thread')
    for i in range(max_worker):
        task_queue.put(None)

    logging.info(f'Waitng worker threads finish')
    for worker in workers:
        worker.join()

    # put stop signal task to stop collector thread
    logging.debug(f'Sent None task to stop collector thread')
    done_queue.put(None)

    logging.info(f'Wating collector thread finish')
    done_queue.join()

    logging.info("Main thread exited")


if __name__ == '__main__':
    parser = init_argparse()
    args = parser.parse_args()
    main(args)

