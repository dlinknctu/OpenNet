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
    h0 = net.addHost( 'h0' )
    h1 = net.addHost( 'h1' )
    h2 = net.addHost( 'h2' )

    wifi = WIFISegment()

    wifi.addAp( h0 )
    wifi.addSta( h1 )
    wifi.addSta( h2 )

    wifi.phyhelper.EnablePcap( "Ap-trace.pcap", h0.nsNode.GetDevice( 0 ), True, True );

    info( '*** Configuring hosts\n' )
    h0.setIP( '192.168.123.1/24' )
    h1.setIP( '192.168.123.2/24')
    h2.setIP( '192.168.123.3/24')

    mininet.ns3.start()


    info( '*** Network state:\n' )
    for node in h0, h1, h2:
        info( str( node ) + '\n' )

    info( '*** Running test\n' )
    h0.cmdPrint( 'ping -c1 ' + h1.IP() )
    h0.cmdPrint( 'ping -c1 ' + h2.IP() )

    CLI(net)

