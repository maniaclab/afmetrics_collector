"""
Get host metrics: cpu, memory, network and disks

This module persist network stats in a file(memfile, default path: /run/afmetrics.json)
to help calculate network io metrics

"""

import os
import time
import shutil
import json
import socket
import psutil

class Xdisks:
    """A container for disks"""
    def __init__(self, disks):
        self.disks = [Xdisk(d) for d in disks]
        self.last_update = None
        #self.update()

    def update(self):
        file_path = '/proc/diskstats'
        # ref: http://lxr.osuosl.org/source/Documentation/iostats.txt
        columns_disk = ['m', 'mm', 'dev', 'reads', 'rd_mrg', 'rd_sectors',
                        'ms_reading', 'writes', 'wr_mrg', 'wr_sectors',
                        'ms_writing', 'cur_ios', 'ms_doing_io', 'ms_weighted']
        lines = open(file_path, 'r').readlines()
        self.last_update = time.time()
        for line in lines:
            if line == '':
                continue
            split = line.split()
            if len(split) != len(columns_disk):
                continue
            data = dict(zip(columns_disk, split))
            # change values to ints.
            for key in data:
                if key != 'dev':
                    data[key] = int(data[key])
            # get Xdisk with this data['dev'] device and set values
            for disk in self.disks:
                if disk.device == data['dev']:
                    if self.last_update and disk.iostat_previous:
                        for k in data:
                            if k == 'dev':
                                continue
                            disk.iostat[k] = data[k] - disk.iostat_previous[k]
                        # this is not incremented
                        disk.iostat['cur_ios'] = data['cur_ios']
                    disk.iostat_previous = data
                    break

    def report(self):
        for disk in self.disks:
            print(disk)
        print('--------------------------------------')


class Xdisk:
    """Xdisk class implments disk metrics collections"""
    def __init__(self, path, lwm=0.95, hwm=0.98):
        self.path = path
        self.lwm = lwm
        self.hwm = hwm
        self.device = ''
        self.iostat_previous = {}
        self.iostat = {}
        self.set_device()

    def __str__(self):
        res = '{:20} device: {:10} used: {}% '.format(
            self.path, self.device, int(self.get_utilization() * 100))
        for k, v in self.iostat.items():
            res += k + ':' + str(v)+' '
        return res

    def get_space(self):
        return shutil.disk_usage(self.path)

    def get_utilization(self):
        (total, used, free) = shutil.disk_usage(self.path)
        return (total, used, free, used / total)

    def get_free_space(self):
        (total, used, free) = shutil.disk_usage(self.path)
        return free

    def set_device(self):
        file_path = '/etc/mtab'
        lines = open(file_path, 'r').readlines()
        for line in lines:
            if line == '':
                continue
            w = line.split(' ')
            if w[1] == self.path:
                self.device = w[0].replace('/dev/', '')
                break


class XNode:
    """XNode class implments node metrics collections"""
    def __init__(self, state_persistence_file="/run/afmetrics.json"):
        self.state_persistence_file = state_persistence_file
        try:
            file_p = open(state_persistence_file, "r")
            self.data_prev = json.load(file_p)
            file_p.close()
        except:
            self.data_prev = {}

        timestamp = int(time.time() * 1000)
        if self.data_prev.get("timestamp", 0) < timestamp - 3600*1000:
            with open(state_persistence_file, "w") as f:
                net_io = psutil.net_io_counters()
                self.data_prev = {'sent' : net_io.bytes_sent,
                                  'received' : net_io.bytes_recv,
                                  'timestamp': int(time.time() * 1000)}
                jdata=json.dumps(self.data_prev)
                f.write(jdata)


    def get_load(self):
        return os.getloadavg()  # 1, 5, 15 min

    def get_memory(self):
        mem = psutil.virtual_memory()
        return mem.total, mem.available

    def get_network(self):
        net_io = psutil.net_io_counters()
        timestamp = int(time.time() * 1000)
        res = {
            'sent': net_io.bytes_sent - self.data_prev["sent"],
            'received': net_io.bytes_recv - self.data_prev["received"],
            'interval': (timestamp - self.data_prev["timestamp"])/1000
        }
        mydata = {'sent' : net_io.bytes_sent,
                  'received' : net_io.bytes_recv,
                  'timestamp': timestamp}
        jdata=json.dumps(mydata)
        with open(self.state_persistence_file,"w") as f:
            f.write(jdata)

        return res


def get_host_metrics(header={}, disks=["/home", "/data", "/scratch"]):

    xd = Xdisks(disks)
    no = XNode()

    data = []

    load_rec = header.copy()
    load_rec['kind'] = "CPU"
    (load_rec['load'], *rest) = no.get_load()
    data.append(load_rec)

    mem_rec = header.copy()
    mem_rec['kind'] = "MEM"
    (mem_rec['total'], mem_rec['available']) =  no.get_memory()
    data.append(mem_rec)

    netw_rec = header.copy()
    netw_rec['kind'] = "NETWORK"
    netw_rec['network'] = no.get_network()
    data.append(netw_rec)

    for disk in xd.disks:
        disk_rec = header.copy()
        disk_rec['kind'] = "DISK"
        if disk.device:
            disk_rec['device'] = disk.device
        disk_rec['mount'] = disk.path
        (disk_rec['total'], disk_rec['used'], disk_rec['free'], \
                disk_rec["utilization"]) = disk.get_utilization()
        for k, v in disk.iostat.items():
            disk_rec[k] = v
        data.append(disk_rec)

    return data


if __name__ == "__main__":

    while True:
        header = {'token': '',
                 'kind': 'host',
                 'cluster': '',
                 'login_node': socket.gethostname()
                 }
        metrics = get_host_metrics(header=header)
        print (metrics)
        time.sleep(5)
