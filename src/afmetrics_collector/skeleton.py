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

from afmetrics_collector import __version__

from afmetrics_collector.jupyter import get_jupyter_users
from afmetrics_collector.ssh import get_ssh_users
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
    parser = argparse.ArgumentParser(description="Just a Fibonacci demonstration")
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
        default=False)
    parser.add_argument(
        "-s",
        "--ssh",
        action="store_true",
        dest="ssh",
        help="collect ssh metrics",
        default=False)
    parser.add_argument(
        "-j",
        "--jupyter",
        action="store_true",
        dest="jupyter",
        help="collect jupyter metrics",
        default=False)
    parser.add_argument(
        "-b",
        "--batch",
        action="store_true",
        dest="batch",
        help="collect batch(condor) metrics",
        default=False)
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
        type=str)
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

        myobj = {'token': token,
                 'kind': 'jupyter-ml',
                 'cluster': cluster,
                 'jupyter_user_count': len(users),
                 'users': users}
        _logger.debug("post to logstash: %s", myobj)
        resp = requests.post(url, json=myobj)
        _logger.debug("post status_code:%d",resp.status_code)

        _logger.info("collecting jupyter-coffea metrics")
        users=get_jupyter_users("coffea-casa", "jhub_user")
        _logger.info("af jupyter-coffea users: %s", users)

        myobj = {'token': token,
                 'kind': 'jupyter-coffea',
                 'cluster': cluster,
                 'jupyter_user_count': len(users),
                 'users': users}
        _logger.debug("post to logstash: %s", myobj)
        resp = requests.post(url, json=myobj)
        _logger.debug("post status_code:%d",resp.status_code)

    if args.ssh:
        _logger.info("collecting ssh metrics")
        users=get_ssh_users()
        _logger.info("af ssh users: %s", users)

        myobj = {'token': token,
                 'kind': 'ssh',
                 'cluster': cluster,
                 'login_node': socket.gethostname(),
                 'ssh_user_count': len(users),
                 'users': users}
        _logger.debug("post to logstash: %s", myobj)
        resp = requests.post(url, json=myobj)
        _logger.debug("post status_code:%d",resp.status_code)

    if args.host:
        _logger.info("collecting host metrics")
        header = {'token': token,
                  'kind': 'host',
                  'cluster': cluster,
                  'login_node': socket.gethostname()}

        metrics = get_host_metrics(header=header)
        _logger.debug("af host metrics: %s", metrics)

        for metric in metrics:
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
                     'cluster': cluster,
                     'state': 'running'}
            myobj.update(job)
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
