#!/usr/bin/python
'''
nctu_cs_wired_and_wireless_topo.gy
'''

from mininet.cluster.net import MininetCluster
from mininet.cluster.placer import DFSPlacer
from mininet.log import setLogLevel
from mininet.cluster.cli import ClusterCLI as CLI
from mininet.node import Controller, RemoteController
from mininet.topo import Topo
from itertools import combinations
import mininet.ns3
from mininet.ns3 import WifiSegment

CONTROLLER_IP = "192.168.59.100"
CONTROLLER_PORT = 6633

SERVER_LIST = [ 'mininet1', 'mininet2' ]

class NCTU_EC_Topology( Topo ):

    def __init__(self, core=1, agg=6, access=6, host=5, *args, **kwargs):
        Topo.__init__(self, *args, **kwargs)
        self.core_num = core
        self.agg_num = agg
        self.access_num = access
        self.host_num = host
        self.sw_id = 1
        self.host_id = 1

        # Init switch and host list
        self.core_sw_list = []
        self.agg_sw_list = []
        self.access_sw_list = []
        self.host_list = []

        self.create_top_switch( "core", self.core_num, self.core_sw_list )

        self.handle_top_down( "agg", self.agg_num, self.core_sw_list, self.agg_sw_list )
        self.handle_top_down( "access", self.access_num, self.agg_sw_list, self.access_sw_list )

        self.handle_host( "h", self.host_num, self.host_list )

        self.handle_mesh( self.agg_sw_list )

    def create_top_switch( self, prefix_name, sw_num, sw_list):
        for i in xrange(1, sw_num+1):
            sw_list.append(self.addSwitch("{0}{1}".format(prefix_name, i), dpid='{0:x}'.format(self.sw_id)))
            self.sw_id += 1

    def handle_top_down( self, prefix_name, num, top_list, down_list):
        temp = 0
        for i in xrange(0, len(top_list)):
            for j in xrange(1, num+1):
                switch = self.addSwitch("{0}{1}".format(prefix_name, j + temp), dpid='{0:x}'.format(self.sw_id))
                self.addLink(top_list[i], switch)
                down_list.append(switch)
                self.sw_id += 1
            temp = j


    def handle_host( self, prefix_name, host_num, host_list ):
        for i in xrange(0, len(self.access_sw_list)):
            for j in xrange(0, host_num):
                host = self.addHost('{0}{1}'.format(prefix_name, self.host_id))
                # Link to access sw
                self.addLink(self.access_sw_list[i], host)
                # Append host to list
                host_list.append(host)
                self.host_id += 1

    def handle_mesh( self, sw_list ):
        for link in combinations(sw_list, 2):
            self.addLink(link[0], link[1])


def RunTestBed():

    # NCTU_EC_Topology( Core Switch, Aggregate Switch, Access Switch, Host)
    topo = NCTU_EC_Topology(core=1, agg=3, access=3, host=2)

    net = MininetCluster( controller=RemoteController, topo=topo, servers=SERVER_LIST, placement=DFSPlacer, root_node="core1", tunneling="vxlan" )
    net.addController( 'controller', controller=RemoteController, ip=CONTROLLER_IP, port=CONTROLLER_PORT )

    wifi = WifiSegment()

    """
    Create AP
    """
    ap_to_access_sw = 0
    for i in xrange(1):
        AP_NAME = "ap" + str(i)
        ap = net.addSwitch(AP_NAME, server=SERVER_LIST[0])
        mininet.ns3.setMobilityModel(ap, None)
        mininet.ns3.setPosition(ap, 0, 0, 0)
        wifi.addAp(ap, channelNumber=6, ssid="opennet-ap", port=0)
        net.addLink(ap, topo.access_sw_list[ap_to_access_sw])
        ap_to_access_sw += 1

    """
    Create Station
    """
    STA_NAME = "sta" + str(0)
    sta = net.addHost(STA_NAME, server=SERVER_LIST[0])
    mininet.ns3.setMobilityModel(sta, None)
    mininet.ns3.setPosition(sta, 0, 0, 0)
    wifi.addSta(sta, channelNumber=6, ssid="opennet-ap", port=0)

    net.start()
    mininet.ns3.start()

    """
    Post Handle
    """
    # XXX Need to fixed
    AP_NAME = "ap" + str(0)
    cmd = "ovs-vsctl add-port {0} {0}-eth0".format(AP_NAME)
    net.getNodeByName(AP_NAME).cmdPrint(cmd)

    STA_NAME = "sta" + str(0)
    cmd = "ip addr add 10.0.0.{0}/8 dev {1}-eth0".format(str(200+i), STA_NAME)
    net.getNodeByName(STA_NAME).cmdPrint(cmd)
    net.getNodeByName(STA_NAME).cmdPrint("ip addr show dev {0}-eth0".format(STA_NAME))

    """
    Show interface object in ns3
    """
    print("*** allTBintfs: {0}\n".format(mininet.ns3.allTBIntfs))
    CLI( net )
    mininet.ns3.stop()
    mininet.ns3.clear()
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    RunTestBed()
