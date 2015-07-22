from mininet.net import Mininet
from mininet.node import Node, Switch
from mininet.link import Link, Intf
from mininet.log import setLogLevel, info
from mininet.cli import CLI

import mininet.ns3
from mininet.ns3 import TBIntf

import ns.network


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

#   NS part ------------------------------------------------------

    channel = ns.network.SimpleChannel()

    h0ns = ns.network.Node()
    device0 = ns.network.SimpleNetDevice()
    device0.SetChannel(channel)
    h0ns.AddDevice(device0)

    h1ns = ns.network.Node()
    device1 = ns.network.SimpleNetDevice()
    device1.SetChannel(channel)
    h1ns.AddDevice(device1)

    h2ns = ns.network.Node()
    device2 = ns.network.SimpleNetDevice()
    device2.SetChannel(channel)
    h2ns.AddDevice(device2)

#   NS part END --------------------------------------------------

 

    tb0 = TBIntf(name="tap0", node=h0, port=None, nsNode=h0ns, nsDevice=device0)

    tb1 = TBIntf("tap1", h1, nsNode=h1ns, nsDevice=device1)

    tb2 = TBIntf("tap2", h2)
    tb2.nsNode = h2ns
    tb2.nsDevice = device2


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

    

