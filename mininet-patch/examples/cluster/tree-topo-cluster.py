#!/usr/bin/python
"""
tree-topo-cluster.py

s1====s3
|      | \
s2    h3 h4
| \
h1 h2

===: cross-link
|: link

ubuntu1: 192.168.59.100
ubuntu2: 192.168.59.101
"""

from mininet.cluster.net import MininetCluster
from mininet.cluster.placer import SwitchBinPlacer
from mininet.topolib import TreeTopo
from mininet.log import setLogLevel
from mininet.cluster.cli import ClusterCLI as CLI
from mininet.node import Controller, RemoteController

def tree_topo_cluster():
    servers = [ 'mininet1', 'mininet2' ]
    topo = TreeTopo( depth=2, fanout=2 )
    # Tunneling options: ssh (default), vxlan, gre
    net = MininetCluster( controller=RemoteController, topo=topo, servers=servers,
                          placement=SwitchBinPlacer, tunneling="gre" )
    net.addController( 'controller', controller=RemoteController, ip="192.168.59.100", port=6633)
    net.start()
    net.pingAll()
    CLI( net )
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    tree_topo_cluster()
