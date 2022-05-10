"""
Allows you to pick a context and then lists all pods in the chosen context. A
context includes a cluster, a user, and a namespace.
Please install the pick library before running this example.
"""

import subprocess
import logging


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

def main():
    get_condor_users()


if __name__ == '__main__':
    main()

