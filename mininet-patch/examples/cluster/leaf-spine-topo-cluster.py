#!/usr/bin/python
"""
leaf-spine-topo-cluster.py

mininet1: 192.168.59.100
mininet2: 192.168.59.101
"""

from mininet.cluster.net import MininetCluster
from mininet.cluster.placer import DFSPlacer
from mininet.topolib import LeafSpineTopo
from mininet.log import setLogLevel
from mininet.cluster.cli import ClusterCLI as CLI
from mininet.node import Controller, RemoteController

def tree_topo_cluster():
    servers = [ 'mininet1', 'mininet2' ]
    topo = LeafSpineTopo( leaf=2, spine=2, fanout=2 )
    net = MininetCluster( controller=RemoteController, topo=topo, servers=servers,
                          placement=DFSPlacer, root_node="spine1", tunneling="vxlan" )
    net.addController( 'controller', controller=RemoteController, ip="192.168.59.100", port=6633)
    net.start()
    CLI( net )
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    tree_topo_cluster()
