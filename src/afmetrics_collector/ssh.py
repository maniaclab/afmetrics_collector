"""
Allows you to pick a context and then lists all pods in the chosen context. A
context includes a cluster, a user, and a namespace.
Please install the pick library before running this example.
"""

import subprocess
import logging


_logger = logging.getLogger(__name__)


def get_ssh_users():
    users = []
    try:
        with subprocess.Popen(['who'], stdout=subprocess.PIPE) as process:
            any(users.append(l.split()[0].decode("utf-8")) for l in process.stdout.readlines()
                    if l.split()[0].decode("utf-8") not in users)
    except Exception as error:
        _logger.error(error)

    _logger.debug("ssh users: %s", users)
    return users

def get_ssh_history():
    users = []
    try:
        with subprocess.Popen(['/usr/bin/last -w -s -5min | head -n -2'], shell=True, stdout=subprocess.PIPE) as process:
            any(users.append(l.split()[0].decode("utf-8")) for l in process.stdout.readlines()
                    if l.split()[0].decode("utf-8") not in users)
    except Exception as error:
        _logger.error(error)

    _logger.debug("ssh users: %s", users)
    return users

def main():
    get_ssh_users()


if __name__ == '__main__':
    main()
