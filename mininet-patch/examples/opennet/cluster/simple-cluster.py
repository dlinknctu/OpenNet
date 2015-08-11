#!/usr/bin/python

"""
simple-cluster.py

mininet1   mininet2
--------   --------
|      |   |      |
|  s1=========s2  |
|  |   |   |   |  |
|  h1  |   |  h2  |
|      |   |      |
--------   --------

=== : cross-link
| : link

Testing enviroment (cat /etc/hosts) :
192.168.59.100 mininet1
192.168.59.101 mininet2
"""

# from mininet.examples.cluster import MininetCluster
from mininet.log import setLogLevel
from mininet.node import Controller, RemoteController
from mininet.link import Link, Intf
from mininet.util import quietRun, errRun

from mininet.cluster.node import *
from mininet.cluster.net import *
from mininet.cluster.placer import *
from mininet.cluster.link import *
from mininet.cluster.cleanup import *
from mininet.cluster.cli import ClusterCLI as CLI


def demo():
    CONTROLLER_IP="192.168.59.100"
    CONTROLLER_PORT=6633
    servers = [ 'mininet1', 'mininet2' ]

    # Tunneling options: ssh
    net = MininetCluster( controller=RemoteController, servers=servers, tunneling="ssh")
    # net = MininetCluster( controller=RemoteController, servers=servers)

    c0 = net.addController( 'c0', controller=RemoteController, ip=CONTROLLER_IP, port=CONTROLLER_PORT)

    # In mininet1
    s1 = net.addSwitch('s1')
    h1 = net.addHost('h1', ip="10.0.0.1")
    net.addLink(s1, h1)

    # In mininet2
    s2 = net.addSwitch('s2', server="mininet2")
    h2 = net.addHost('h2', ip="10.0.0.2", server="mininet2")
    net.addLink(s2, h2)

    # Cross-link between mininet1 and mininet2
    net.addLink(s1, s2)

    net.start()
    print("Mininet is running on {hostname}".format(hostname=quietRun('hostname').strip()))
    for node in c0, h1, s1, h2, s2:
        print("Node {nodename} is running on {servername}".format(nodename=node, servername=node.cmd('hostname').strip()))
    net.pingAll()
    CLI( net )
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    demo()
