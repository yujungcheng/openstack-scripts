#!/usr/bin/env python3
""" Compare File-1 and File-2 to find lines in File-1 do not exist in File-2 """

import sys


def file_line_to_list(filepath):
    lines = []
    with open(filepath, 'r') as fp:
        for line in fp:
            lines.append(line)
    return lines

def main(argv):
    #print(f'{argv}')

    file1 = argv[1]
    file2 = argv[2]

    print(f'build File1 list...')
    file1_lines = file_line_to_list(file1)
    print(f'build File2 list...')
    file2_lines = file_line_to_list(file2)

    file1_count = len(file1_lines)
    file2_count = len(file2_lines)
    print(f'- File1 {file1_count}\n- File2 {file2_count}')

    # find line in file1 not exist in file2
    print(f'- File1 line not exist in File2')
    progress = 0
    for line in file1_lines:
        if line not in file2_lines:
            print(f'{line}')
        progress += 1
        if progress % 10000 == 0:
            print(f'{-- processed {progress} line}')

if __name__ == '__main__':
    main(sys.argv)
