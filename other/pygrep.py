#!/usr/bin/env python3

import sys
import argparse
import time
from datetime import datetime


def init_argparse():
    parser = argparse.ArgumentParser(description='comparing specific column/field value between two files.')
    parser.add_argument('--from-file', required=True, help='file to read items to compare')
    parser.add_argument('--to-file', required=True, help='file to be compared to items.')
    parser.add_argument('--match-column', required=False, help='column index of string to be matched. start form 1')
    parser.add_argument('--delimiter', required=False, help='delimiter to line in file. Default = " | "')
    parser.add_argument('--output', required=False, help='file name to store output to. Default output to console.')
    return parser

def print_message(msg, timestamp=True):
    p_msg = msg
    if timestamp:
        now = datetime.now()
        dt_string = now.strftime("%d-%m-%Y %H:%M:%S")
        p_msg = f'{dt_string} - {msg}'
    print(f'{p_msg}')

def build_target_match_list(filename, match_column, delimiter):
    print_message(f'Building comparison array from file {filename}, delimiter={delimiter}')
    match_array = list()
    with open(filename, 'r') as fp:
        for line in fp:
            if match_column != None:
                line_array = line.split(delimiter)
                match = line_array[match_column].rstrip()
            else:
                match = line.rstrip()
            match_array.append(match)
    return match_array

def grep_line(queue):
    match_string = queue.get()


def main(args):
    print_message(f'start comparing data.')
    from_file = args['from_file']
    to_file = args['to_file']
    if args['match_column'] is not None:
        match_column = int(args['match_column']) - 1
    else:
        match_column = None
    if args['delimiter'] is not None:
        delimiter = args['delimiter']
    else:
        delimiter = ' | '
    if args['output']  is not None:
        output = args['output']
    else:
        output = False

    target_match_list = build_target_match_list(to_file, match_column, delimiter)
    print_message("Start comparing")

    with open(from_file, 'r') as fp:
        comparing_items = []
        for line in fp:
            if match_column != None:
                line_array = line.split(delimiter)
                match = line_array[match_column].rstrip()
            else:
                match = line.rstrip(match)

            # tell if item is found or not
            if match in target_match_list:
                print(f'Y | {match}')
                target_match_list.remove(match)
            else:
                print(f'N | {match}')

            # for print all matched items
            '''
            counter = 0
            for match_item in match_array:
                if match in match_item:
                    counter += 1
                    print(f'Y | {match_item}')
            if counter == 0:
                print(f'N | {match}')
            '''

if __name__ == "__main__":
    parser = init_argparse()
    args = vars(parser.parse_args(sys.argv[1:]))
    main(args)

