#!/usr/bin/env python3
# require python 3.6 or above

# comparing specific column/field string value between two files.
# - matching column string in each line must unique
# - use unique character or string for delimiter, default ' | '
# - output format:
#   result | counter | comparing_string [ compared_string ] | match string
#
#   result flags:
#   U - unable to find matched data line
#   Y - data line can be matched and value compared is identical
#   N - data line can be matched but value compared is not identical

import sys
import argparse
from datetime import datetime


def init_argparse():
    parser = argparse.ArgumentParser(description='comparing specific column/field value between two files.')
    parser.add_argument('--from-file', required=True, help='file to read items to compare')
    parser.add_argument('--to-file', required=True, help='file to be compared to items.')
    parser.add_argument('--compare-column', required=True, help='column index of value to be compared')
    parser.add_argument('--match-column', required=True, help='column index of string to be matched.')
    parser.add_argument('--delimiter', required=False, help='delimiter to line in file. Default = " | "')
    parser.add_argument('--output', required=False, help='file name to store output to. Default output to console.')
    parser.add_argument('--test', required=False, help='test run with first 10 data line only.')
    return parser

def print_message(msg, timestamp=True, write_to_file=False):
    p_msg = msg
    if timestamp:
        now = datetime.now()
        dt_string = now.strftime("%d-%m-%Y %H:%M:%S")
        p_msg = f'{dt_string} - {msg}'
    print(f'{p_msg}')
    if write_to_file:
        msg_fp = open(write_to_file, "a")
        msg_fp.write(p_msg+"\n")
        msg_fp.close()

def build_compared_array(filename, compare_column, match_column, delimiter):
    print_message(f'Building comparison array from file {filename}')
    compared_array = dict()
    counter = 0
    with open(filename, 'r') as fp:
        for line in fp:
            counter += 1
            line_array = line.split(delimiter)
            value = line_array[compare_column].rstrip()
            match = line_array[match_column].rstrip()
            if match in compared_array:
                print_message(f'Duplicated match: {match}')
                continue
            compared_array[match] = value
    print_message(f'Array built successfully. {counter} items.')
    return compared_array

def main(args):
    print_message(f'start comparing data.')
    from_file = args['from_file']
    to_file = args['to_file']
    compare_column = int(args['compare_column']) - 1
    match_column = int(args['match_column']) - 1
    if args['delimiter'] is not None:
        delimiter = args['delimiter']
    else:
        delimiter = ' | '
    if args['output']  is not None:
        output = args['output']
    else:
        output = False
    print_message(f'- comparing data from file {from_file}', timestamp=False)
    print_message(f'- comparing data to file {to_file}', timestamp=False)
    print_message(f'- column id to be compared : {compare_column}', timestamp=False)
    print_message(f'- column id to be matched : {match_column}', timestamp=False)
    print_message(f"- column delimiter : '{delimiter}'", timestamp=False)
    print_message(f"- output file for compared data : {output}", timestamp=False)
    print_message(f"- output file for unmatch data : {output}.unmatch", timestamp=False)
    try:
        compared_array = build_compared_array(to_file,
                                              compare_column,
                                              match_column,
                                              delimiter)
    except Exception as e:
        print_message(f'Error: {e}')
        exit(1)

    try:
        output_fp = False
        if output:
            print_message(f'create output file {output}')
            output_fp = open(output, "w")

        print_message(f'comparing data from {from_file}')
        with open(from_file, 'r') as fp:
            counter = 0
            counter_match = 0
            counter_not_match = 0
            counter_not_found = 0
            for line in fp:
                counter += 1
                line_array = line.split(delimiter)
                value = line_array[compare_column].rstrip()
                match = line_array[match_column].rstrip()
                if match in compared_array:
                    compared_value = compared_array[match]
                else:
                    print_message(f'U | {counter} | {value} ? | {match}', timestamp=False, write_to_file=f'{output}.nomatch')
                    counter_not_found += 1
                    continue
                if value == compared_value:
                    output_line = f'Y | {counter} | {value} | {match}'
                    #output_line = f'Y | {counter} | {value} {compared_value} | {match}'
                    counter_match += 1
                else:
                    output_line = f'N | {counter} | {value} {compared_value} | {match}'
                    counter_not_match += 1
                if output_fp != False:
                    output_fp.write(output_line+"\n")
                else:
                    print(f'{output_line}')
        print_message(f'data compare completed. {counter} lines compared.')
        print_message(f'- identical compared value : {counter_match}', timestamp=False)
        print_message(f'- different compared value : {counter_not_match}', timestamp=False)
        print_message(f'- not found match column   : {counter_not_found}', timestamp=False)

        if output_fp != False:
            output_fp.close()
    except Exception as e:
        print_message(f'Error: {e}')
        if output_fp != False:
            output_fp.close()
        exit(1)

if __name__ == "__main__":
    parser = init_argparse()
    args = vars(parser.parse_args(sys.argv[1:]))
    main(args)
