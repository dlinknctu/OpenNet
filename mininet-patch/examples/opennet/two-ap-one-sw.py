#!/usr/bin/python

"""
+---------+ +---------+ +---------+
|   NS3   | | Mininet | |   NS3   |
|   AP0   +-+ Switch  +-+   AP1   |
+----+----+ +---------+ +----+----+
     |                       |
+----+----+             +----+----+
|  NS3    |             |  NS3    |
|  Station|             |  Station|
+---------+             +---------+
"""


from mininet.net import Mininet
from mininet.node import Node, Switch, RemoteController
from mininet.link import Link, Intf
from mininet.log import setLogLevel, info
from mininet.cli import CLI

import mininet.ns3
from mininet.ns3 import WifiSegment

import ns.core
import ns.network
import ns.wifi
import ns.csma
import ns.wimax
import ns.uan
import ns.netanim

from mininet.opennet import *

def main():

    net = Mininet()
    net.addController('c0', controller=RemoteController, ip="127.0.0.1", port=6633)

    sw0 = net.addSwitch('sw0', ip=None)

    ap0 = net.addAP('ap0', ip=None)
    mininet.ns3.setMobilityModel(ap0, None)
    mininet.ns3.setPosition(ap0, 0, 0, 0)

    ap1 = net.addAP('ap1', ip=None)
    mininet.ns3.setMobilityModel(ap1, None)
    mininet.ns3.setPosition(ap1, 10, 10, 0)

    sta0 = net.addStation('sta0', ip="10.0.0.1")
    mininet.ns3.setMobilityModel(sta0, None)
    mininet.ns3.setVelocity(sta0, 0, 5, 0)

    sta1 = net.addStation('sta1', ip="10.0.0.2")
    mininet.ns3.setMobilityModel(sta1, None)
    mininet.ns3.setVelocity(sta1, 5, 0, 0)

    wifi = WifiSegment(standard=ns.wifi.WIFI_PHY_STANDARD_80211g)
    wifi.addAp(ap0, channelNumber=11, ssid="opennet_0")
    wifi.addAp(ap1, channelNumber=11, ssid="opennet_1")

    wifi.addSta(sta0, channelNumber=11, ssid="opennet_0")
    wifi.addSta(sta1, channelNumber=11, ssid="opennet_1")

    net.addLink(sw0, ap0)
    net.addLink(sw0, ap1)

    net.start()
    mininet.ns3.start()

    sta0.cmdPrint('ping -c2 ' + sta1.IP())
    sta1.cmdPrint('ping -c2 ' + sta0.IP())

    CLI(net)

    mininet.ns3.stop()
    mininet.ns3.clear()
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    main()
