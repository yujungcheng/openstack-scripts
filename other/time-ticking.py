#!/usr/bin/env python

import time
import sys
from datetime import datetime

def main(argv):
    timestamps = []
    max_seconds = int(argv[1])
    start_ts = time.time()
    print("Started at %s" % time.time())
    print("Maximum seconds %s" % max_seconds)

    for i in range(0, max_seconds):
        timestamps.append(time.time())
        time.sleep(1)
    end_ts = time.time()

    log_filename = "timestamp.%s-to-%s__%s.log" % (start_ts, end_ts, len(timestamps))
    with open(log_filename, 'w') as log:
        for timestamp in timestamps:
            dt_obj = datetime.fromtimestamp(timestamp)
            log.write("%s | %s\n" % (timestamp, dt_obj))

if __name__ == "__main__":
    main(sys.argv)

