#!/usr/bin/env python3

import threading
import subprocess
import time
import signal
import os

from _thread import start_new_thread


def execute(command, destination):
    # Execute the job!
    job_process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = job_process.communicate()

    time_bytes = str(time.time()).encode()

    with open(destination, 'ab') as log_file:
        log_file.write(b'----- Out' + time_bytes + b' -----\n')
        log_file.write(out)
        log_file.write(b'----- Err -----\n')
        log_file.write(err)
        log_file.write(b'----- End -----\n')


def serval_route_print():
    _thread = threading.Timer(30, serval_route_print)
    _thread.daemon = True
    _thread.start()

    execute('servald route print', 'serval.route')


def ps_aux():
    _thread = threading.Timer(10, ps_aux)
    _thread.daemon = True
    _thread.start()

    execute('ps aux', 'ps.aux')


def trace():
    _thread = threading.Timer(10, trace)
    _thread.daemon = True
    _thread.start()

    execute('cat coord.xy', 'trace.xy')


def tcpdump(iface):
    subprocess.Popen(
        [
            'tcpdump', '-n', '-e', '-s', '200', '-i', iface, '-w',
            '{}.pcap'.format(iface)
        ],
        stdout=subprocess.PIPE)


def netmon():
    for iface in os.listdir('/sys/class/net/'):
        if 'eth' not in iface:
            continue

        start_new_thread(tcpdump, (iface, ))


if __name__ == '__main__':
    serval_route_print()
    ps_aux()
    trace()
    netmon()

    signal.pause()
