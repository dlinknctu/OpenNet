#!/usr/bin/python

"""
This example shows how to create an empty Mininet object
(without a topology object) and add nodes to it manually.
"""

from mininet.net import Mininet
from mininet.node import OVSController
from mininet.cli import CLI
from mininet.log import setLogLevel, info

import mininet.ns3                          # line added
from mininet.ns3 import CSMALink            # line added

def emptyNet():

    "Create an empty network and add nodes to it."

    net = Mininet( controller=OVSController )

    info( '*** Adding controller\n' )
    net.addController( 'c0' )

    info( '*** Adding hosts\n' )
    h1 = net.addHost( 'h1', ip='10.0.0.1' )
    h2 = net.addHost( 'h2', ip='10.0.0.2' )

    info( '*** Adding switch\n' )
    s3 = net.addSwitch( 's3' )

    info( '*** Creating links\n' )
    CSMALink( h1, s3, DataRate="10Mbps" )   # line modified
    CSMALink( h2, s3, DataRate="100Mbps" )  # line modified

    info( '*** Starting network\n')
    net.start()
    mininet.ns3.start()                     # line added

    info( '*** Running CLI\n' )
    CLI( net )

    info( '*** Stopping network' )
    mininet.ns3.clear()                     # line added
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    emptyNet()
