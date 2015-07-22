from mininet.net import Mininet
from mininet.node import Node, Switch
from mininet.link import Link, Intf
from mininet.log import setLogLevel, info
from mininet.cli import CLI

import mininet.ns3
from mininet.ns3 import CSMALink

import ns.csma


if __name__ == '__main__':
    setLogLevel( 'info' )
    info( '*** ns-3 network demo\n' )
    net = Mininet()

    info( '*** Creating Network\n' )
    h0 = Node( 'h0' )
    h1 = Node( 'h1' )

    net.hosts.append( h0 )
    net.hosts.append( h1 )

    link = CSMALink( h0, h1, DataRate="10Mbps")

    ns.csma.CsmaHelper().EnablePcap( "h0-trace.pcap", h0.nsNode.GetDevice( 0 ), True, True );
    ns.csma.CsmaHelper().EnablePcap( "h1-trace.pcap", h1.nsNode.GetDevice( 0 ), True, True );

    mininet.ns3.start()

    info( '*** Configuring hosts\n' )
    h0.setIP( '192.168.123.1/24' )
    h1.setIP( '192.168.123.2/24')

    info( 'Testing network connectivity\n' )
    net.pingAll()
    info( 'Testing bandwidth between h0 and h1\n' )
    net.iperf( ( h0, h1 ) )

    mininet.ns3.clear()
    net.stop()

    info( "Run: \"wireshark h0-trace.pcap\" to see packets captured in ns device\n" )


