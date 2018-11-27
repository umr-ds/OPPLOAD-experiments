### CFG string cap "The Capabilities for workers (all capable, or some)"
### CFG string worker "Worker selection algorithm"
### CFG string scn "JIT or AOT scenario"

import time

from general import *

if __name__ == '__main__':
    logger.info("STAGE 0: start MACI experiment and CORE session")
    framework.start()
    session = make_session('/shared/tests/ring/topology.xml', {{simInstanceId}})
    time.sleep(10)

    logger.info("STAGE 1: prepare the configuration files with the provided parameters")
    prepare_job_files(session, '{{scn}}', ['n1'])
    prepare_dtnrpc_configuration(session, '{{worker}}')
    prepare_capabilities(session, '{{cap}}')

    logger.info("STAGE 1b: start position information thread")
    log_positions(session)

    logger.info("STAGE 2: start dtnrpc and allow the workers to exchange their offers")
    start_dtnrpc(session, '{{seed}}')
    time.sleep(10)


    logger.info("STAGE 3: execute a job on n1 (blocking)")
    node = session.get_object_by_name('n1')
    node.cmd_output(['bash', '-c', 'python3 -u /shared/dtnrpc/dtn_rpyc.py -c {{scn}}.jb &> client_run.log'])

    logger.info("STAGE 3 shutdown: allow the dtnrpc cleanup to happen on all nodes")
    time.sleep(10)


    logger.info("STAGE 2 shutdown: stop services")
    stop_services(session)

    logger.info("STAGE 1 shutdown: collect all logs and files")
    collect_logs(session.session_dir)

    logger.info("STAGE 0 shutdown: stop CORE session and MACI experiment")
    session.shutdown()
    framework.stop()
