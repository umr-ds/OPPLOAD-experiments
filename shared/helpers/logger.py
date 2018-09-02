#!/usr/bin/env python3

import threading
import subprocess
import time


def run_route_print():
    route_print_thread = threading.Timer(30, run_route_print)
    route_print_thread.daemon = True
    route_print_thread.start()

    # Execute the job!
    job_process = subprocess.Popen(
        'servald route print',
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = job_process.communicate()

    with open('serval.route', 'ab') as serval_route_file:
        serval_route_file.write(b'----- ' + str(time.time()).encode() +
                                b' -----\n')
        serval_route_file.write(out)
        serval_route_file.write(b'----------\n')


if __name__ == '__main__':
    run_route_print()

    while True:
        time.sleep(360)
