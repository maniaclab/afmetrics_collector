"""
Allows you to pick a context and then lists all pods in the chosen context. A
context includes a cluster, a user, and a namespace.
Please install the pick library before running this example.
"""


import logging

from kubernetes import client, config
from kubernetes.client import configuration

_logger = logging.getLogger(__name__)


def get_jupyter_users(namespace, label):
    """get list of users running jupyter notebooks

    Args:
      namespace (str): namespace
      label (str): the name of label of ownership

    Returns:
      users: list of users
    """

    # Configs can be set in Configuration class directly or using helper utility
    config.load_kube_config()

    v1 = client.CoreV1Api()
    _logger.debug("Listing pods:")
    ret = v1.list_namespaced_pod(namespace, label_selector=label)
    for i in ret.items:
        _logger.debug("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
    users = []
    [users.append(i.metadata.labels['owner']) for i in ret.items if i.metadata.labels['owner'] not in users]
    _logger.debug("users:%s", users )
    return users

def main():
    get_jupyter_users("af-jupyter", "owner")


if __name__ == '__main__':
    main()
