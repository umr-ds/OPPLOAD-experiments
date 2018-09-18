#!/usr/bin/env python

import threading
import subprocess
import time
import signal
import os


def execute(command, destination):
    # Execute the job!
    job_process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = job_process.communicate()

    time_bytes = str(time.time()).encode()

    with open(destination, 'ab') as log_file:
        log_file.write(b'\n----- Out ' + time_bytes + b' -----\n')
        log_file.write(out)
        log_file.write(b'\n----- Err -----\n')
        log_file.write(err)
        log_file.write(b'\n----- End -----\n')


def serval_route_print():
    _thread = threading.Timer(30, serval_route_print)
    _thread.daemon = True
    _thread.start()

    execute('servald route print', 'serval.route')


def pidstat():
    subprocess.Popen(
        [
            'bash', '-c', 'pidstat -drush -p ALL 1 >> pidstat'
        ],
        stdout=subprocess.PIPE)


def processes():
    _thread = threading.Thread(target=pidstat)
    _thread.daemon = True
    _thread.start()


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


def bwm():
    subprocess.Popen(
        [
            'bwm-ng', '--timeout=1000', '--unit=bytes', '--type=rate',
            '--output=csv', '-F', 'bwm.csv',
        ],
        stdout=subprocess.PIPE)


def netmon():
    for iface in os.listdir('/sys/class/net/'):
        if 'eth' not in iface:
            continue

        _thread = threading.Thread(target=tcpdump, args=(iface, ))
        _thread.daemon = True
        _thread.start()

    _thread = threading.Thread(target=bwm)
    _thread.daemon = True
    _thread.start()


if __name__ == '__main__':
    serval_route_print()
    processes()
    trace()
    netmon()

    signal.pause()
