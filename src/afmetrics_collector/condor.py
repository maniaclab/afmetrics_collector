"""
Allows you to pick a context and then lists all pods in the chosen context. A
context includes a cluster, a user, and a namespace.
Please install the pick library before running this example.
"""

import subprocess
import logging
import time

_logger = logging.getLogger(__name__)


def get_condor_users():
    process = subprocess.Popen(['condor_q', '-allusers', '-run', '-format', ' %s ', 'Owner'],
                               stdout=subprocess.PIPE)
    #for line in process.stdout.readlines():
    #    line.decode("utf-8")
        #_logger.debug(line)
        #print(line)
    users = []
    [users.append(u.decode("utf-8")) for l in process.stdout.readlines() for u in l.split()
            if u.decode("utf-8") not in users and u.decode("utf-8") != "atlas-coffea"]
    #print(users)
    return users

def get_condor_jobs():

    keys = ["users", "Id", "Runtime"]
    constraint = 'Owner =!= \"{}\"'.format('atlas-coffea')
    #print(cons)
    #'-completedsince', str(now - since_insecs) not working?
    process = subprocess.Popen(['condor_q',
                                #'-completedsince', str(now - since_insecs),
                                '-constraint', constraint,
                                '-format',"%s ", 'Owner', '-format', "%d.", 'ClusterId', '-format', "%d ",
                                'ProcId', '-format', "%d \n", 'RemoteWallClockTime'],
                               stdout=subprocess.PIPE)
    #jobs = [dict(zip(keys,l.decode("utf-8").split())) for l in process.stdout.readlines()]
    jobs = [dict(zip(keys, [int(x) if i == 2 else x for i,x in enumerate(l.decode("utf-8").split())])) for l in process.stdout.readlines()]
    #print(jobs)
    return jobs

def get_condor_history(JobStatus=4, since_insecs=360):

    now = time.time()
    keys = ["users", "Id", "Runtime"]
    constraint = 'JobStatus=={} && JobFinishedHookDone>={} && Owner =!= \"{}\"'.format(
                         JobStatus, now - since_insecs, 'atlas-coffea')
    #print(cons)
    #'-completedsince', str(now - since_insecs) not working?
    process = subprocess.Popen(['condor_history',
                                #'-completedsince', str(now - since_insecs),
                                '-constraint', constraint,
                                '-format',"%s ", 'Owner', '-format', "%d.", 'ClusterId', '-format', "%d ",
                                'ProcId', '-format', "%d \n", 'RemoteWallClockTime'],
                               stdout=subprocess.PIPE)
    jobs = [dict(zip(keys, [int(x) if i == 2 else x for i,x in enumerate(l.decode("utf-8").split())])) for l in process.stdout.readlines()]
    #print(jobs)
    return jobs

def main():
    get_condor_users()


if __name__ == '__main__':
    main()

