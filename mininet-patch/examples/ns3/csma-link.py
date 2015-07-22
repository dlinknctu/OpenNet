from mininet.net import Mininet
from mininet.node import Node, Switch
from mininet.link import Link, Intf
from mininet.log import setLogLevel, info
from mininet.cli import CLI

import mininet.ns3
from mininet.ns3 import CSMALink


if __name__ == '__main__':
    setLogLevel( 'info' )
    info( '*** ns-3 network demo\n' )
    net = Mininet()

    info( '*** Creating Network\n' )
    h0 = Node( 'h0' )
    h1 = Node( 'h1' )

    net.hosts.append( h0 )
    net.hosts.append( h1 )

    link = CSMALink( h0, h1 )

    mininet.ns3.start()

    info( '*** Configuring hosts\n' )
    h0.setIP( '192.168.123.1/24' )
    h1.setIP( '192.168.123.2/24')

    info( '*** Network state:\n' )
    for node in h0, h1:
        info( str( node ) + '\n' )

    info( '*** Running test\n' )
    h0.cmdPrint( 'ping -c1 ' + h1.IP() )

    CLI(net)

