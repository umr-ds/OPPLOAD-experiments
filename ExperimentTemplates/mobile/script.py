### CFG int clients "Number of clients"
### CFG int movement "Mobility model of the nodes"
### CFG string worker "Worker selection algorithm"
### CFG string scn "JIT or AOT scenario"
### CFG string cap "Capabilities of workers (just placeholder for eval)"

import signal
import subprocess

from general import *

class Alarm(Exception):
    pass

def alarm_handler(_, __):
    raise Alarm

client_list = ['n1', 'n2', 'n4', 'n6', 'n8', 'n10', 'n12', 'n13', 'n14', 'n15']
__cap = '{{cap}}'

if __name__ == '__main__':
    logger.info("STAGE 0: start MACI experiment and CORE session")
    framework.start()

    logger.info("STAGE 1: prepare the configuration files with the provided parameters")
    link_movement({{movement}})

    session = make_session('/shared/tests/mobile/topology.xml', {{simInstanceId}})
    prepare_job_files(session, '{{scn}}', client_list[:{{clients}}])
    prepare_dtnrpc_configuration(session, '{{worker}}')
    prepare_capabilities(session, 'some')

    logger.info("STAGE 1b: start position information thread")
    log_positions(session)

    logger.info("STAGE 2: start dtnrpc and allow the workers to exchange their offers")
    start_dtnrpc(session, '{{seed}}')
    time.sleep(10)

    logger.info("STAGE 3: execute the jobs on the nodes")
    client_processes = [
        subprocess.Popen(
            'vcmd -c {}/{} -- bash -c "python3 -u /shared/dtnrpc/dtn_rpyc.py -c {{scn}}.jb &> client_run.log"'.
            format(session.session_dir, client),
            shell=True) for client in client_list[:{{clients}}]
    ]

    logger.info("STAGE 3b: set alarm signal to 30 minutes")
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(30 * 60)

    logger.info("STAGE 3c: wait for jobs to complete")
    try:
        for process in client_processes:
            process.wait()

        signal.alarm(0)

    except Alarm:
        logger.info("STAGE 3 shutdown: timeout, killing all remaining jobs")
        for process in client_processes:
            try:
                process.kill()
            except OSError:
                continue

    logger.info("STAGE 2 shutdown: stop services")
    stop_services(session)

    logger.info("STAGE 1 shutdown: collect all logs and files")
    collect_logs(session.session_dir)

    logger.info("STAGE 0 shutdown: stop CORE session and MACI experiment")
    session.shutdown()
    framework.stop()
