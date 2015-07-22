#!/usr/bin/python

"""
This example shows how to create an empty Mininet object
(without a topology object) and add nodes to it manually.
"""

from mininet.net import Mininet
from mininet.node import OVSController
from mininet.link import Link
from mininet.cli import CLI
from mininet.log import setLogLevel, info

import mininet.ns3
from mininet.ns3 import WIFIBridgeLink

def emptyNet():

    "Create an empty network and add nodes to it."
    "[h1]<---network-a--->[s3]<--wifi-bridge-->[s4]<---network-b--->[h2]"

    net = Mininet( controller=OVSController )

    info( '*** Adding controllers\n' )
    net.addController( 'c0' )
    net.addController( 'c1' )

    info( '*** Adding hosts\n' )
    h1 = net.addHost( 'h1', ip='10.0.0.1' )
    h2 = net.addHost( 'h2', ip='10.0.0.2' )

    info( '*** Adding switches\n' )
    s3 = net.addSwitch( 's3' )
    s4 = net.addSwitch( 's4' )

    info( '*** Creating links\n' )
    Link( s3, h1 )
    WIFIBridgeLink( s3, s4 )
    Link( s4, h2 )

    info( '*** Starting network\n')
    net.start()
    mininet.ns3.start()

    info( '*** Running CLI\n' )
    CLI( net )

    info( '*** Stopping network' )
    mininet.ns3.stop()
    mininet.ns3.clear()
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    emptyNet()
