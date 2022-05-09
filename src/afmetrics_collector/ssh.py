"""
Allows you to pick a context and then lists all pods in the chosen context. A
context includes a cluster, a user, and a namespace.
Please install the pick library before running this example.
"""

import subprocess
import logging


_logger = logging.getLogger(__name__)


def get_ssh_users():
    process = subprocess.Popen(['who'],
                               stdout=subprocess.PIPE)
    #for line in process.stdout.readlines():
    #    line.decode("utf-8")
    #    _logger.debug(line)
    users = []
    [users.append(l.split()[0].decode("utf-8")) for l in process.stdout.readlines() 
            if l.split()[0].decode("utf-8") not in users]
    return users

def main():
    get_ssh_users()


if __name__ == '__main__':
    main()
