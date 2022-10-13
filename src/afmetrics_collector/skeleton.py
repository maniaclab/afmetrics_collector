"""
This is a skeleton file that can serve as a starting point for a Python
console script.

# command verbose, collect ssh, jupyter metrics
afmetrics_collector -v -s -j

Besides console scripts, the header (i.e. until ``_logger``...) of this file can
also be used as template for Python modules.

Note:

References:
    - https://setuptools.pypa.io/en/latest/userguide/entry_point.html
    - https://pip.pypa.io/en/stable/reference/pip_install
"""

import argparse
import logging
import sys
import socket
import requests

# needed for debug
import json

# needed for user obfuscation
import hashlib

# needed for group filtering
import grp
import pwd

from afmetrics_collector import __version__

from afmetrics_collector.jupyter import get_jupyter_users
from afmetrics_collector.ssh import get_ssh_users, get_ssh_history
from afmetrics_collector.condor import get_condor_history, get_condor_jobs
from afmetrics_collector.host import get_host_metrics

__author__ = "Fengping Hu"
__copyright__ = "Fengping Hu"
__license__ = "MIT"

_logger = logging.getLogger(__name__)


# ---- CLI ----
# The functions defined in this section are wrappers around the main Python
# API allowing them to be called directly from the terminal as a CLI
# executable/script.


def parse_args(args):
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(description="Help for afmetrics_collector")
    parser.add_argument(
        "--version",
        action="version",
        version="afmetrics_collector {ver}".format(ver=__version__),
    )
    #parser.add_argument(dest="n", help="n-th Fibonacci number", type=int, metavar="INT")
    parser.add_argument(
        "--host",
        action="store_true",
        dest="host",
        help="collect ssh metrics",
        default=False
    )
    parser.add_argument(
        "-s",
        "--ssh",
        action="store_true",
        dest="ssh",
        help="collect ssh metrics",
        default=False
    )
    parser.add_argument(
        "-S",
        "--ssh-history",
        action="store_true",
        dest="ssh_history",
        help="collect ssh metrics from last 5 minutes (note: requires newer version of 'last' with -s option)",
        default=False
    )
    parser.add_argument(
        "-j",
        "--jupyter",
        action="store_true",
        dest="jupyter",
        help="collect jupyter metrics",
        default=False
    )
    parser.add_argument(
        "-b",
        "--batch",
        action="store_true",
        dest="batch",
        help="collect batch(condor) metrics",
        default=False
    )
    parser.add_argument(
        "-n",
        "--namespace",
        dest="ns",
        help="namespace for jupyter",
        default="af-jupyter",
        type=str,
    )
    parser.add_argument(
        '-l',
        "--label",
        dest="label",
        help="label of jupyter pods",
        default="owner",
        type=str
    )
    parser.add_argument(
        "-t",
        "--token",
        dest="token",
        help="logstash token",
        #default="af-jupyter",
        type=str,
    )
    parser.add_argument(
        "-c",
        "--cluster",
        dest="cluster",
        help="the name of the af cluster",
        default="UC-AF",
        type=str,
    )
    parser.add_argument(
        "-u",
        "--url",
        dest="url",
        help="logstash url",
        default="https://af.atlas-ml.org/",
        type=str,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
    )
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )
    parser.add_argument(
        "-o",
        "--obfuscate-users",
        action="store_true",
        dest="obf_users",
        help="hash the usernames before sending to logstash",
        default=False,
    )
    parser.add_argument(
        "-O",
        "--obfuscate-hosts",
        dest="obf_hosts",
        help="alter the hostnames before sending to logstash (usage -O \"<domain_name>\")",
        default="",
        type=str,
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        dest="debug_local",
        help="output to a local json file in current directory",
        default=False,
    )
    parser.add_argument(
        "-z",
        "--salt",
        dest="salt",
        help="add salt to user name hash for added security (usage --salt \"<salt>\")",
        default="",
        type=str,
    )
    parser.add_argument(
        "-g",
        "--group",
        dest="group",
        help="optional group to filter for. Useful on multi user/group machines (usage -g \"<groupname>\")",
        default="",
        type=str,
    )
    return parser.parse_args(args)


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )


def main(args):
    """Wrapper allowing :func:`fib` to be called with string arguments in a CLI fashion

    Instead of returning the value from :func:`fib`, it prints the result to the
    ``stdout`` in a nicely formatted message.

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--verbose", "42"]``).
    """
    args = parse_args(args)
    url = args.url
    token = args.token
    cluster = args.cluster
    setup_logging(args.loglevel)
    if args.jupyter:
        _logger.info("collecting jupyter-ml metrics")
        users=get_jupyter_users(args.ns, args.label)
        _logger.info("af jupyter-ml users: %s", users)

        if args.group != "":
            # group filter
            for i, x in enumerate(users[:]):
                groups = [g.gr_name for g in grp.getgrall() if x in g.gr_mem]
                gid = pwd.getpwnam(x).pw_gid
                groups.append(grp.getgrgid(gid).gr_name)
                if args.group not in groups:
                    users.remove(x)

        if args.obf_users:
            # jupyter user hash
            for i, x in enumerate(users):
                users[i] = hashlib.sha256((args.salt+x).encode('utf-8')).hexdigest()[:8]
            
        myobj = {'token': token,
                 'kind': 'jupyter-ml',
                 'cluster': cluster,
                 'jupyter_user_count': len(users),
                 'users': users}
        
        if args.debug_local:
            # For local debugging
            json_object = json.dumps(myobj, indent=4)
            with open("jupyter-debug.json", "a") as outfile:
                outfile.write(json_object)
        else: # post to logstash
            _logger.debug("post to logstash: %s", myobj)
            resp = requests.post(url, json=myobj)
            _logger.debug("post status_code:%d",resp.status_code)

        _logger.info("collecting jupyter-coffea metrics")
        users=get_jupyter_users("coffea-casa", "jhub_user")
        _logger.info("af jupyter-coffea users: %s", users)

        if args.group != "":
            # group filter
            for i, x in enumerate(users[:]):
                groups = [g.gr_name for g in grp.getgrall() if x in g.gr_mem]
                gid = pwd.getpwnam(x).pw_gid
                groups.append(grp.getgrgid(gid).gr_name)
                if args.group not in groups:
                    users.remove(x)

        if args.obf_users:
            # jupyter-coffea user hash
            for i, x in enumerate(users):
                users[i] = hashlib.sha256((args.salt+x).encode('utf-8')).hexdigest()[:8]

        myobj = {'token': token,
                 'kind': 'jupyter-coffea',
                 'cluster': cluster,
                 'jupyter_user_count': len(users),
                 'users': users}
        if args.debug_local:
            # For local debugging
            json_object = json.dumps(myobj, indent=4)
            with open("jupyter-debug.json", "a") as outfile:
                outfile.write(json_object)
        else: # post to logstash
            _logger.debug("post to logstash: %s", myobj)
            resp = requests.post(url, json=myobj)
            _logger.debug("post status_code:%d",resp.status_code)

    if args.ssh:
        _logger.info("collecting ssh metrics")
        users=get_ssh_users()
        _logger.info("af ssh users: %s", users)

        if args.ssh_history:
            users.extend(get_ssh_history())

        if args.group != "":
            # group filter
            for i, x in enumerate(users[:]):
                groups = [g.gr_name for g in grp.getgrall() if x in g.gr_mem]
                gid = pwd.getpwnam(x).pw_gid
                groups.append(grp.getgrgid(gid).gr_name)
                if args.group not in groups:
                    users.remove(x)

        if args.obf_users:
            # ssh user hash
            for i, x in enumerate(users):
                users[i] = hashlib.sha256((args.salt+x).encode('utf-8')).hexdigest()[:8]
        
        if args.obf_hosts != "":
            # atlas ssh host obfuscation
            ssh_host_name = ''.join(['atlas',''.join([n for n in socket.gethostname() if n.isdigit()]),".",args.obf_hosts])
        else:
            ssh_host_name = socket.gethostname()

        myobj = {'token': token,
                 'kind': 'ssh',
                 'cluster': cluster,
                 'login_node': ssh_host_name,
                 'ssh_user_count': len(users),
                 'users': users}

        if args.debug_local:
            # For local debugging
            json_object = json.dumps(myobj, indent=4)
            with open("ssh.json", "a") as outfile:
                outfile.write(json_object)
        else: # post to logstash
            _logger.debug("post to logstash: %s", myobj)
            resp = requests.post(url, json=myobj)
            _logger.debug("post status_code:%d",resp.status_code)
        

    if args.host:
        _logger.info("collecting host metrics")
        if args.obf_hosts != "":
            # atlas host obfuscation
            login_host_name = ''.join(['atlas',''.join([n for n in socket.gethostname() if n.isdigit()]),".",args.obf_hosts])
        else:
            login_host_name = socket.gethostname()

        header = {'token': token,
                  'kind': 'host',
                  'cluster': cluster,
                  'login_node': login_host_name }

        metrics = get_host_metrics(header=header)
        _logger.debug("af host metrics: %s", metrics)

        for metric in metrics:
            if args.debug_local:
                # For local debugging
                json_object = json.dumps(metric, indent=4)
                with open("host.json", "a") as outfile:
                    outfile.write(json_object)
            else: # post to logstash
                _logger.debug("post to logstash: %s", metric)
                resp = requests.post(url, json=metric)
                _logger.debug("post status_code:%d",resp.status_code)

    if args.batch:
        _logger.info("collecting batch metrics - current users")
        jobs=get_condor_jobs()
        _logger.debug("af running batch jobs: %s", jobs)

        for job in jobs:
            myobj = {'token': token,
                     'kind': 'condorjob',
                     'cluster': cluster}
            myobj.update(job)

            if args.group != "":
                # group filter
                groups = [g.gr_name for g in grp.getgrall() if myobj.get('users') in g.gr_mem]
                gid = pwd.getpwnam(myobj.get('users')).pw_gid
                groups.append(grp.getgrgid(gid).gr_name)
                if args.group not in groups:
                    continue

            if args.obf_users:
                # condor user hash
                myobj.update([('users',hashlib.sha256((args.salt+myobj.get('users')).encode('utf-8')).hexdigest()[:8])])

            if args.debug_local:
                # For local debugging
                json_object = json.dumps(myobj, indent=4)
                with open("condor.json", "a") as outfile:
                    outfile.write(json_object)
            else: # post to logstash
                _logger.debug("post to logstash: %s", myobj)
                resp = requests.post(url, json=myobj)
                _logger.debug("post status_code:%d",resp.status_code)

        _logger.info("collecting batch metrics - job history")
        jobs=get_condor_history(since_insecs=360)
        _logger.debug("af finished batch jobs: %s", jobs)
        for job in jobs:
            myobj = {'token': token,
                     'kind': 'condorjob',
                     'cluster': cluster,
                     'state': 'finished'}
            myobj.update(job)
            
            if args.group != "":
                # group filter
                groups = [g.gr_name for g in grp.getgrall() if myobj.get('users') in g.gr_mem]
                gid = pwd.getpwnam(myobj.get('users')).pw_gid
                groups.append(grp.getgrgid(gid).gr_name)
                if args.group not in groups:
                    continue
            
            if args.obf_users:
                # condor user hash
                myobj.update([('users',hashlib.sha256((args.salt+myobj.get('users')).encode('utf-8')).hexdigest()[:8])])
            
            if args.debug_local:
                # For local debugging
                json_object = json.dumps(myobj, indent=4)
                with open("condor.json", "a") as outfile:
                    outfile.write(json_object)
            else: # post to logstash
                _logger.debug("post to logstash: %s", myobj)
                resp = requests.post(url, json=myobj)
                _logger.debug("post status_code:%d",resp.status_code)



    _logger.info("Script ends here")


def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    # ^  This is a guard statement that will prevent the following code from
    #    being executed in the case someone imports this file instead of
    #    executing it as a script.
    #    https://docs.python.org/3/library/__main__.html

    # After installing your project with pip, users can also run your Python
    # modules as scripts via the ``-m`` flag, as defined in PEP 338::
    #
    #     python -m afmetrics_collector.skeleton 42
    #
    run()
