#!/usr/bin/python3

import time

def main():
    for i in range(3):
        try:
            print("%s - running" % i)
            raise Exception("error occur!!!")
        except Exception as e:
            print("Exception occur, retrying (%s), %s" % (i, e))
            if i == 2:
                raise Exception("Reached maximum retry.")
            time.sleep(1)

    print("I should not be printed. (%s)" % i)
    return


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Exception: %s" % e)

