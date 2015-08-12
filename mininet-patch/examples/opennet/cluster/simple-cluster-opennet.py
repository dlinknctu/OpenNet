#!/usr/bin/python

"""
simple-cluster-opennet.py

mininet1   mininet2
--------   --------
|      |   |      |
|  ap1========s2  |
|  |   |   |   |  |
| sta1 |   |  h2  |
|      |   |      |
--------   --------

=== : cross-link
| : link

Testing enviroment (cat /etc/hosts) :
192.168.59.100 mininet1
192.168.59.101 mininet2
"""

from mininet.log import setLogLevel
from mininet.node import Controller, RemoteController
from mininet.link import Link, Intf
from mininet.util import quietRun, errRun

from mininet.cluster.node import *
from mininet.cluster.net import *
from mininet.cluster.placer import *
from mininet.cluster.link import *
from mininet.cluster.clean import *
from mininet.cluster.cli import ClusterCLI as CLI

import mininet.ns3
from mininet.ns3 import WifiSegment

import ns.core
import ns.network
import ns.wifi
import ns.csma

def demo():
    CONTROLLER_IP="192.168.59.100"
    CONTROLLER_PORT=6633
    servers = [ 'mininet1', 'mininet2' ]

    wifi = WifiSegment()
    net = MininetCluster( controller=RemoteController, servers=servers)
    c0 = net.addController( 'c0', controller=RemoteController, ip=CONTROLLER_IP, port=CONTROLLER_PORT)

    # In mininet1
    # ap1
    ap1 = net.addSwitch('ap1')
    mininet.ns3.setMobilityModel(ap1, None)
    mininet.ns3.setPosition(ap1, 0, 0, 0)
    wifi.addAp(ap1, channelNumber=6, ssid="opennet_ap")

    # sta1
    sta1 = net.addHost('sta1', ip="10.0.0.1")
    mininet.ns3.setMobilityModel(sta1, None)
    mininet.ns3.setPosition(sta1, 0, 0, 0)
    wifi.addSta(sta1, channelNumber=6, ssid="opennet_ap")

    # In mininet2
    s2 = net.addSwitch('s2', server="mininet2")
    h2 = net.addHost('h2', ip="10.0.0.2", server="mininet2")
    net.addLink(s2, h2)

    # Cross-link between mininet1 and mininet2
    net.addLink(ap1, s2)

    net.start()
    mininet.ns3.start()

    print("Opennet is running on {hostname}".format(hostname=quietRun('hostname').strip()))
    for node in c0, ap1, sta1, h2, s2:
        print("Node {nodename} is running on {servername}".format(nodename=node, servername=node.cmd('hostname').strip()))

    net.pingAll()
    CLI( net )

    mininet.ns3.stop()
    mininet.ns3.clear()
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    demo()
