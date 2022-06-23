# Analysis Facility metrics collector

AF Metrics Collector collects various metrics about user jobs from kubernetes,
batch systems and send the collected metrics as json documents to an https endpoint.

## Documents

Each document has to have a token field. To get a token for your AF, please contact Ilija Vukotic.
All documents get timestamped on the receiving end so no need to send them. Here an example of each metric.

### SSH users

this is obtained by parsing output of __who__ command.

```json
{   
    "kind": "ssh",
    "ssh_user_count": 4,
    "cluster": "UC-AF",
    "login_node": "login01.af.uchicago.edu",
    "users": [
      "brosser",
      "mhank",
      "milaivanovska",
      "rjacobse"
    ]
}
```

### Condor users

obtained by parsing output of __condor_q__ command.

```json
{   
    "kind": "condorjob",
    "cluster": "UC-AF",
    "users": "brosser",
    "state": "finished",
    "Id": "174100.63",
    "Runtime": 177
}
```

### Jupyter users

```json
{   
    "kind": "jupyter-ml",
    "cluster": "UC-AF",
    "jupyter_user_count": 4,
    "users": [
      "agolub",
      "gwatts",
      "hanhiller",
      "petya"
    ]
}
```

### Disk

One document for each disk reporting used, total and free bytes as seen from __/proc/diskstats__

```json
{   
    "kind": "DISK",    
    "cluster": "UC-AF",
    "used": 92355981312,
    "total": 1883690205184,
    "free": 1695620259840,
    "login_node": "login02.af.uchicago.edu",
    "utilization": 0.04902928361459448,
    "mount": "/scratch"
}
```

### CPU

Just a one minute load average as reported by __os.getloadavg()__.

```json
{       
    "kind": "CPU",
    "cluster": "UC-AF",
    "login_node": "login02.af.uchicago.edu",
    "load": 0.01
}
```

### Network

Differential of bytes_sent, bytes_recv and the time interval, as reported by __psutil.net_io_counters()__.

```json
{       
    "kind": "NETWORK",
    "cluster": "UC-AF",
    "login_node": "login02.af.uchicago.edu",
    "network": {
      "interval": 300.064,
      "sent": 6606414,
      "received": 11383868
    }
}
```

### Memory

Host total and available memory as reported by __psutil.virtual_memory()__. In bytes.

```json
{   
    "kind": "MEM",
    "cluster": "UC-AF",
    "login_node": "login02.af.uchicago.edu",
    "available": 265041854464,
    "total": 269903060992
}
```

## Sending documents

All the documents should be __POST__ to <https://af.atlas-ml.org>.

Note
====

This project has been set up using PyScaffold 4.2.1. For details and usage
information on PyScaffold see <https://pyscaffold.org/>.
