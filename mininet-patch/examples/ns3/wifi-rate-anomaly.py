from mininet.net import Mininet
from mininet.node import Node, Switch
from mininet.link import Link, Intf
from mininet.log import setLogLevel, info
from mininet.cli import CLI

import mininet.ns3
from mininet.ns3 import WIFISegment

import ns.core
import ns.wifi


if __name__ == '__main__':
    setLogLevel( 'info' )
    info( '*** ns-3 network demo\n' )
    net = Mininet()

    info( '*** Creating Network\n' )
    h0 = Node( 'h0' )
    h1 = Node( 'h1' )
    h2 = Node( 'h2' )

    net.hosts.append( h0 )
    net.hosts.append( h1 )
    net.hosts.append( h2 )

    wifi = WIFISegment()


    wifi.machelper.SetType ( "ns3::AdhocWifiMac" )

    # set datarate for node h0
    wifi.wifihelper.SetRemoteStationManager( "ns3::ConstantRateWifiManager",
                                             "DataMode", ns.core.StringValue( "OfdmRate54Mbps" ) )
    wifi.add( h0 )

    # set datarate for node h1   
    wifi.wifihelper.SetRemoteStationManager( "ns3::ConstantRateWifiManager",
                                             "DataMode", ns.core.StringValue( "OfdmRate6Mbps" ) )
    wifi.add( h1 )

    # set datarate for node h2
    wifi.wifihelper.SetRemoteStationManager( "ns3::ConstantRateWifiManager",
                                             "DataMode", ns.core.StringValue( "OfdmRate54Mbps" ) )
    wifi.add( h2 )
    


    info( '*** Configuring hosts\n' )
    h0.setIP( '192.168.123.1/24' )
    h1.setIP( '192.168.123.2/24')
    h2.setIP( '192.168.123.3/24')

    mininet.ns3.start()


    info( '*** Testing network connectivity\n' )
    net.pingAll()

    info( '*** Starting TCP iperf server on h2\n' )
    h2.sendCmd( "iperf -s" )

    info( '*** Testing bandwidth between h0 and h2 while h1 is not transmitting\n' )
    h0.cmdPrint( "iperf -c 192.168.123.3" )

    info( '*** Testing bandwidth between h0 and h2 while h1 is transmitting at 6Mbps\n' )
    h1.sendCmd( "iperf -c 192.168.123.3" )
    h0.cmdPrint( "iperf -c 192.168.123.3" )

    CLI(net)

