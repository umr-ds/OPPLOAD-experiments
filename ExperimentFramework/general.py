# -*- coding: utf-8 -*-

import time
import os
import shutil
import threading
import sys
import logging
import errno

import nacl.hash
from nacl.encoding import HexEncoder
from nacl.bindings import crypto_sign_seed_keypair, crypto_sign_ed25519_sk_to_curve25519, crypto_scalarmult_base

from core import logger as core_logger
from core.service import ServiceManager
from core.xml import xmlsession
from core.emulator.coreemu import CoreEmu
from core.netns.nodes import CoreNode

import framework

_ch = logging.StreamHandler(sys.stdout)
_ch.setLevel(logging.DEBUG)
_ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger = logging.getLogger("maci")
logger.addHandler(_ch)
logger.setLevel(logging.DEBUG)

job_template = '''client_sid={client_sid}
{w1} denoise /shared/tests/sample_image.jpg 0.5 | energy:2
{w2} scale ## 110% | energy:1
{w3} crop ## 90% | energy:1
{w4} bw ## | energy:2
{w5} detect ## | energy:5
'''

caps_great = {
    'energy': 1000,
    'disk_space': 1024**2 * 100,
    'cpu_load': 4 - 0.00,
    'memory': 1024**2 * 10,
}

caps_ok = {
    'energy': 5,
    'disk_space': 1024**2 * 10,
    'cpu_load': 4 - 0.30,
    'memory': 1024**2 * 1,
}

caps_bad = {
    'energy': 1,
    'disk_space': 1024**2 * 1,
    'cpu_load': 4 - 0.70,
    'memory': 1024**2 * 0.2,
}

caps_not = {
    'energy': 0,
    'disk_space': 0,
    'cpu_load': 4 - 4,
    'memory': 1024**2 * 0,
}


def start_dtnrpc(session, seed):
    for obj in session.objects.itervalues():
        if type(obj) is CoreNode:
            seed_path = '{}/{}.conf/random.seed'.format(session.session_dir, obj.name)
            with open(seed_path, "w") as seed_file:
                seed_file.write("{}".format(obj.objid + int(seed)))
            obj.cmd(['bash', '-c', 'nohup python3 -u /shared/dtnrpc/dtn_rpyc.py -s &> worker_run.log &'])


def prepare_add_file(input_file):
    total_file_size = os.path.getsize(input_file)

    if total_file_size > 20000000:
        too_big_file = open(input_file, 'rb')

        def get_chunk():
            return too_big_file.read(20000000)

        chunk_count = 0
        for chunk in iter(get_chunk, ''):
            chunk_path = '{}_chunk{}'.format(input_file, chunk_count)
            with open(chunk_path, 'wb') as chunk_file:
                chunk_file.write(chunk)
                framework.addBinaryFile(chunk_path)
            chunk_count = chunk_count + 1

        too_big_file.close()

    else:
        framework.addBinaryFile(input_file)


def collect_logs(session_dir):
    for root, _, files in os.walk(session_dir):
        for f in files:
            src_file_path = os.path.join(root, f)

            if 'blob' in src_file_path:
                continue
            if 'serval.log' in src_file_path:
                continue
            if '.conf' not in src_file_path:
                continue

            session_dir_trailing = '{}/'.format(session_dir)
            new_file_name = src_file_path.replace(session_dir_trailing,
                                                  '').replace('/', '_')
            dst_file_path = '{}/{}'.format(os.getcwd(), new_file_name)

            try:
                shutil.move(src_file_path, dst_file_path)
                prepare_add_file(new_file_name)
            except IOError:
                continue

    prepare_add_file('core_session.log')
    prepare_add_file('parameters.py')
    prepare_add_file('log.txt')


def make_session(topo_path, _id):

    fh = logging.FileHandler('core_session.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s'
        ))
    core_logger.addHandler(fh)

    coreemu = CoreEmu()
    session = coreemu.create_session(_id=_id)
    ServiceManager.add_services('/root/.core/myservices')

    xmlsession.open_session_xml(session, topo_path, start=True)

    return session

def stop_services(session):
    for obj in session.objects.itervalues():
        if type(obj) is CoreNode:

            # kill dtnrpc (blocking)
            obj.cmd(['bash', '-c', 'killall -w python3'])

            # stop all core services
            session.services.stopnodeservices(obj)


def log_positions(session):
    _thread = threading.Timer(10, log_positions, args=[session])
    _thread.daemon = True
    _thread.start()

    for obj in session.objects.itervalues():
        if type(obj) is CoreNode:

            pos_file_path = '{}/{}.conf/coord.xy'.format(
                session.session_dir, obj.name)

            with open(pos_file_path, 'w') as pos_file:
                x, y, _ = obj.position.get()

                pos_file.write('{} {}'.format(x, y))


def generate_serval_keys(name):
    node_hash = HexEncoder.decode(nacl.hash.sha256(name.encode("utf-8")))
    sign_pk, sign_sk = crypto_sign_seed_keypair(node_hash)
    box_sk = crypto_sign_ed25519_sk_to_curve25519(sign_sk)
    box_pk = crypto_scalarmult_base(box_sk)

    rhiz_pk = HexEncoder.decode(nacl.hash.sha256(("rhizome"+name).encode("utf-8")))

    keys = {
        "sign_pk": HexEncoder.encode(sign_pk).decode("ascii").upper(),
        "box_sk":  HexEncoder.encode( box_sk).decode("ascii").upper(),
        "sign_sk": HexEncoder.encode(sign_sk).decode("ascii").upper(),
        "box_pk":  HexEncoder.encode( box_pk).decode("ascii").upper(),
        "sid":     HexEncoder.encode( box_pk).decode("ascii").upper(),
        "rhiz_pk": HexEncoder.encode(rhiz_pk).decode("ascii").upper(),
    }
    return keys


def prepare_job_files(session, scn, clients):
    for obj in session.objects.itervalues():
        if not type(obj) is CoreNode:
            continue
        if obj.name not in clients:
            continue

        client_sid = generate_serval_keys(obj.name)["sid"]

        dst_path = '{}/{}.conf/{}.jb'.format(session.session_dir, obj.name,
                                                scn)

        if scn == 'jit':
            job_dict = {
                'client_sid': client_sid,
                'w1': 'any',
                'w2': 'any',
                'w3': 'any',
                'w4': 'any',
                'w5': 'any',
            }
        elif scn == 'aot':
            job_dict = {
                'client_sid': client_sid,
                'w1': generate_serval_keys("n3")["sid"],
                'w2': generate_serval_keys("n5")["sid"],
                'w3': generate_serval_keys("n7")["sid"],
                'w4': generate_serval_keys("n9")["sid"],
                'w5': generate_serval_keys("n11")["sid"],
            }

        with open(dst_path, "w") as jit_dst_file:
            jit_dst_file.write(job_template.format(**job_dict))


def prepare_dtnrpc_configuration(session, algo):
    for obj in session.objects.itervalues():
        if type(obj) is CoreNode:

            obj.cmd_output(['bash', '-c', 'cp -r /shared/dtnrpc_configs/* .'])
            obj.cmd_output(['bash', '-c', 'echo "api.restful.newsince_timeout=5" >> serval.conf'])

            rpc_conf_file_path = '{}/{}.conf/rpc.conf'.format(
                session.session_dir,
                obj.name)

            with open(rpc_conf_file_path, 'a') as rpc_conf_file:
                rpc_conf_file.write('server={}'.format(algo))


def prepare_capabilities(session, cap):
    #20% great, 40% okay, 30% bad, 10%

    probs = [
        caps_ok,
        caps_bad,
        caps_great,
        caps_not,
        caps_ok,
        caps_bad,
        caps_great,
        caps_ok,
        caps_bad,
        caps_ok,
    ]

    probs_ptr = 0

    for obj in session.objects.itervalues():
        if not type(obj) is CoreNode:
            continue

        rpc_caps_file_path = '{}/{}.conf/rpc.caps'.format(
            session.session_dir, obj.name)

        node_cap = caps_great

        if cap == 'some':
            node_cap = probs[probs_ptr]
            probs_ptr = (probs_ptr + 1) % len(probs)

        with open(rpc_caps_file_path, 'a') as rpc_caps_file:
            content = "\n".join(
                ["{}={}".format(k, v) for k, v in node_cap.iteritems()])
            rpc_caps_file.write(content + '\n')


def link_movement(movement):
    movement_path = '/shared/tests/mobile/{}.ns_movement'.format(movement)
    link_name = '/shared/tests/mobile/movement.ns_movement'
    try:
        os.symlink(movement_path, link_name)
    except OSError, e:
        if e.errno == errno.EEXIST:
            os.remove(link_name)
            os.symlink(movement_path, link_name)
        else:
            raise e
