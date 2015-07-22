from mininet.net import Mininet
from mininet.node import Node, Switch
from mininet.link import Link, Intf
from mininet.log import setLogLevel, info
from mininet.cli import CLI

import mininet.ns3
from mininet.ns3 import WIFISegment


if __name__ == '__main__':
    setLogLevel( 'info' )
    info( '*** ns-3 network demo\n' )
    net = Mininet()

    info( '*** Creating Network\n' )
    h0 = Node( 'h0' )
    h1 = Node( 'h1' )

    net.hosts.append( h0 )
    net.hosts.append( h1 )

    wifi = WIFISegment()

    wifi.add( h0 )
    wifi.add( h1 )
    


    info( '*** Configuring hosts\n' )
    h0.setIP( '192.168.123.1/24' )
    h1.setIP( '192.168.123.2/24')

    mininet.ns3.start()


    info( '*** Testing network connectivity\n' )
    net.pingAll()

    info( '*** Nodes positions: \n' )
    info( 'h0:', mininet.ns3.getPosition( h0 ), '\n' )
    info( 'h1:', mininet.ns3.getPosition( h1 ), '\n' )

    info( 'Testing bandwidth between h0 and h1 while 0 meters away\n' )
    net.iperf( ( h0, h1 ) )

    info( '*** Changing h1 position: \n' )
    mininet.ns3.setPosition( h1 , 46.0, 38.0, 0.0)

    info( '*** Nodes positions: \n' )
    info( 'h0:', mininet.ns3.getPosition( h0 ), '\n' )
    info( 'h1:', mininet.ns3.getPosition( h1 ), '\n' )

    info( 'Testing bandwidth between h0 and h1 while 60 meters away\n' )
    net.iperf( ( h0, h1 ) )

    info( '*** Changing h1 position: \n' )
    mininet.ns3.setPosition( h1 , 68.0, 72.0, 0.0)

    info( '*** Nodes positions: \n' )
    info( 'h0:', mininet.ns3.getPosition( h0 ), '\n' )
    info( 'h1:', mininet.ns3.getPosition( h1 ), '\n' )

    info( 'Testing bandwidth between h0 and h1 while 100 meters away\n' )
    net.iperf( ( h0, h1 ) )

    

