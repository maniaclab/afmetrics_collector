"""
Allows you to pick a context and then lists all pods in the chosen context. A
context includes a cluster, a user, and a namespace.
Please install the pick library before running this example.
"""

import subprocess
import logging
import time

_logger = logging.getLogger(__name__)


def get_condor_jobs():

    jobs = []
    keys = ["users", "Id", "Runtime"]
    constraint = 'Owner =!= \"{}\"'.format('atlas-coffea')

    #'-completedsince', str(now - since_insecs) not working?
    try:
        with subprocess.Popen(['condor_q',
                               #'-completedsince', str(now - since_insecs),
                               '-constraint', constraint,
                               '-format',"%s ", 'Owner',
                               '-format', "%d.", 'ClusterId',
                               '-format', "%d ", 'ProcId',
                               '-format', "%d \n", 'RemoteWallClockTime'],
                               stdout=subprocess.PIPE) as process:

            jobs = [dict(zip(keys, [int(x) if i == 2 else x
                for i,x in enumerate(l.decode("utf-8").split())]))
                for l in process.stdout.readlines()]
    except Exception as error:
        _logger.error(error)

    return jobs

def get_condor_history(job_status=4, since_insecs=360):
    jobs = []
    now = time.time()
    keys = ["users", "Id", "Runtime"]
    constraint = 'JobStatus=={} && JobFinishedHookDone>={} && Owner =!= \"{}\"'.format(
                         job_status, now - since_insecs, 'atlas-coffea')
    try:
        process = subprocess.Popen(['condor_history',
                               #'-completedsince', str(now - since_insecs),
                               '-constraint', constraint,
                               '-format',"%s ", 'Owner',
                               '-format', "%d.", 'ClusterId',
                               '-format', "%d ", 'ProcId',
                               '-format', "%d \n", 'RemoteWallClockTime'],
                               stdout=subprocess.PIPE)
        jobs = [dict(zip(keys, [int(x) if i == 2 else x
                for i,x in enumerate(l.decode("utf-8").split())]))
                for l in process.stdout.readlines()]

    except Exception as error:
        _logger.error(error)
    return jobs

def main():
    get_condor_jobs()


if __name__ == '__main__':
    main()
