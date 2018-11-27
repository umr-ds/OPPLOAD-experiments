import os
import glob
import collections
import multiprocessing
import multiprocessing.pool

import pandas as pd
import dpkt, socket


### helpers to find studies and experiments
def get_study_paths(base="/maci_data"):
    paths = glob.glob(os.path.join(base, "binary_files/*"))
    return sorted(paths, key=os.path.getctime)

def get_latest_study(base="/maci_data"):
    return Study(get_study_paths(base)[-1])


class Study(object):
    def __init__(self, path):
        self.path = path
        self.experiments = Study._read_experiments(path)
        self.dtnrpc = Study._generate_dtnrpc(self.experiments)
        self.sids = Study._generate_sids(self.experiments)
    
    @staticmethod
    def _read_experiments(study_path):
        experiment_paths = glob.glob(os.path.join(study_path, "*"))
        experiment_paths = sorted(experiment_paths, key=lambda p: int(p.split("/")[-1]))
        
        with multiprocessing.Pool(8) as p:
            experiments = p.map(Experiment._load_experiment, experiment_paths)
        #experiments = [Experiment(path) for path in experiment_paths]
        
        experiments = [ex for ex in experiments if ex is not None]
        
        return experiments
    
    @staticmethod
    def _generate_sids(experiments):
        annotated = []
        
        for ex in experiments:
            sids_copy = ex.sids.copy()
            for k, v in ex.params.items():
                sids_copy[k] = v
            annotated.append(sids_copy)
            
        return pd.concat(annotated, sort=False).reset_index()
    
    @staticmethod
    def _generate_dtnrpc(experiments, desc_order=["scn", "worker", "cap", "seed"]):
        annotated = []
        
        for ex in experiments:
            for k, v in ex.params.items():
                ex.dtnrpc[k] = v
            ex.dtnrpc["desc"] = "-".join([str(ex.params[k]) for k in desc_order if k in ex.params])
            annotated.append(ex.dtnrpc)
            
        return pd.concat(annotated, sort=False).reset_index()



class Experiment(object):
    def __init__(self, path):
        self.path = path
        self.params = Experiment._read_params(path)
        self.dtnrpc = Experiment._parse_dtnrpc(path)
        self.pidstat = Experiment._parse_pidstat(path)
        #self.pcap = Experiment._parse_pcaps(path)
        self.bwm = Experiment._parse_bwms(path)
        self.sids = Experiment._read_sids(path)
        
    def __repr__(self):
        return "Experiment({})".format(", ".join(["{}: {}".format(k,v) for k,v in self.params.items()]))

    @staticmethod
    def _load_experiment(path):
        try:
            return Experiment(path)
        except Exception as ex:
            print("Loading {} failed, exception: {}".format(path, ex))
            return None
    
    @staticmethod
    def _read_sids(experiment_path):
        sids = []
        for sid_path in glob.glob(os.path.join(experiment_path, "*.conf_serval.sid")):
            node = os.path.basename(sid_path).split(".")[0]
            with open(sid_path, "r") as sid_file:
                sid = sid_file.read()
            sids.append((node, sid))
        
        return pd.DataFrame(sids, columns=["node", "sid"])
            
    
    @staticmethod
    def _read_params(experiment_path):
        '''reads the experiment parameters'''
        with open(os.path.join(experiment_path, "parameters.py")) as parameters_file:
            parameters = parameters_file.read()
        params = eval(parameters.splitlines()[0].split("=")[1].strip())

        return params

    @staticmethod
    def _parse_dtnrpc_log_line(line):
        '''parses on line of a dtnrpc log.'''
        log = [val.strip() for val in line.split("|")]
        if len(log) == 4:
            log.insert(4, "")
        return log[:5]

    @staticmethod
    def _parse_dtnrpc_log(log_path):
        '''parses one dtnrpc log file.'''
        with open(log_path, "r") as log_file:
            log = [Experiment._parse_dtnrpc_log_line(l) for l in log_file.readlines()]
            log_df = pd.DataFrame(log, columns=["ts", "log", "level", "job", "msg"])
            log_df["ts"] = pd.to_datetime(log_df["ts"])
            log_df["node"] = os.path.basename(log_path).split(".")[0]
            log_df["logtype"] = log_path.split("_")[-1].split(".")[0]
        return log_df

    @staticmethod
    def _parse_dtnrpc(experiment_path):
        '''parses and joins all dtnrpc log files of an experiment.'''
        log_paths = glob.glob(os.path.join(experiment_path, "*.conf_client.log")) + glob.glob(os.path.join(experiment_path, "*.conf_worker.log"))
        
        parsed_logs = [Experiment._parse_dtnrpc_log(path) for path in log_paths]
        
        logs_df = pd.concat(parsed_logs).sort_values(by='ts').reset_index()
        logs_df["dt"] = (logs_df["ts"] - logs_df["ts"].iloc[0]).dt.total_seconds()

        return logs_df
    
    PIDSTAT_NUMERICS = ['UID', 'PID', '%usr', '%system', '%guest', '%wait', '%CPU', 
                        'CPU', 'minflt/s', 'majflt/s', 'VSZ', 'RSS', '%MEM', 'StkSize', 
                        'StkRef', 'kB_rd/s', 'kB_wr/s', 'kB_ccwr/s', 'iodelay']
    
    @staticmethod
    def _parse_pidstat_file(pidstat_path):
        node = os.path.basename(pidstat_path).split(".")[0]
        modify_date = pd.to_datetime(int(os.path.getmtime(pidstat_path)), unit='s').date()

        with open(pidstat_path, "r") as pidstat_file:
            snaps = pidstat_file.read().split("\n\n")
            csv_header = snaps[1].splitlines()[0].split()[1:]
            stats_list = [line.split() 
                          for snap in snaps[1:] 
                          for line in snap.splitlines()[1:]]

            pidstat_df = pd.DataFrame(stats_list, columns=csv_header)

            # prepend log modification date time, convert to datetime
            pidstat_df["Time"] = str(modify_date) + " " + pidstat_df["Time"]
            pidstat_df["Time"] = pd.to_datetime(pidstat_df["Time"])
            pidstat_df["node"] = node

            pidstat_df[Experiment.PIDSTAT_NUMERICS] = pidstat_df[Experiment.PIDSTAT_NUMERICS].apply(pd.to_numeric)

        return pidstat_df

    @staticmethod
    def _parse_pidstat(experiment_path):
        pidstat_paths = glob.glob(os.path.join(experiment_path, "*.conf_pidstat"))
        
        parsed_pidstats = [Experiment._parse_pidstat_file(path) for path in pidstat_paths]
        
        pidstat_df = pd.concat(parsed_pidstats)
        
        pidstat_df = pidstat_df.sort_values(["Time", "node"]).reset_index()
        pidstat_df["dt"] = (pidstat_df["Time"] - pidstat_df["Time"].iloc[0]).dt.total_seconds()
        
        return pidstat_df
    

    @staticmethod
    def _parse_pcap_file2(pcap_path):
        node = os.path.basename(pcap_path).split(".")[0]

        pcap_file = open(pcap_path,'rb')
        rows = []

        for ts, pkt in dpkt.pcap.Reader(pcap_file):
            eth = dpkt.ethernet.Ethernet(pkt) 
            if eth.type != dpkt.ethernet.ETH_TYPE_IP:
                continue

            ip = eth.data

            rows.append([ts, socket.inet_ntoa(ip.src), socket.inet_ntoa(ip.dst), int(ip.len)])

        capframe = pd.DataFrame(rows, columns=["ts", "ip_src", "ip_dst", "size"])
        capframe["ts"] = pd.to_datetime(capframe["ts"], unit="s")
        capframe.set_index(pd.DatetimeIndex(capframe['ts']))
        capframe["node"] = node

        return capframe

    @staticmethod
    def _parse_pcaps(experiment_path):
        pcap_paths = glob.glob(os.path.join(experiment_path, "*.conf_eth0.pcap"))

        with multiprocessing.pool.ThreadPool(len(pcap_paths)) as p:
            parsed_pcaps = p.map(Experiment._parse_pcap_file2, pcap_paths)
        df = pd.concat(parsed_pcaps)

        return df.sort_values(["node", "ts"]).reset_index()

    BWM_HEADERS = ["ts", "iface", "bytes_out/s", "bytes_in/s", "bytes_total/s", "bytes_in", "bytes_out", "packets_out/s", "packets_in/s", "packets_total/s", "packets_in", "packets_out", "errors_out/s", "errors_in/s", "errors_in", "errors_out"]

    @staticmethod
    def _parse_bwm(bwm_path):
        df = pd.read_csv(bwm_path, sep=";", names=Experiment.BWM_HEADERS)
        df["ts"] = pd.to_datetime(df["ts"], unit="s")
        df["node"] = os.path.basename(bwm_path).split(".")[0]

        return df

    @staticmethod
    def _parse_bwms(experiment_path):
        bwm_paths = glob.glob(os.path.join(experiment_path, "*.conf_bwm.csv"))

        parsed_bwms = [Experiment._parse_bwm(p) for p in bwm_paths]
        df = pd.concat(parsed_bwms, sort=False)
        df = df.sort_values(["ts", "node"]).reset_index()
        
        df["dt"] = (df["ts"] - df["ts"].iloc[0]).dt.total_seconds()
        
        return df

