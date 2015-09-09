#!/usr/bin/python
'''
nctu_cs_wired_topo.gy
'''

from mininet.cluster.net import MininetCluster
from mininet.cluster.placer import DFSPlacer
from mininet.log import setLogLevel
from mininet.cluster.cli import ClusterCLI as CLI
from mininet.node import Controller, RemoteController
from mininet.topo import Topo
from itertools import combinations

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
    topo = NCTU_EC_Topology(core=1, agg=6, access=6, host=20)

    net = MininetCluster( controller=RemoteController, topo=topo, servers=SERVER_LIST, placement=DFSPlacer, root_node="core1", tunneling="vxlan" )
    net.addController( 'controller', controller=RemoteController, ip=CONTROLLER_IP, port=CONTROLLER_PORT )
    net.start()
    CLI( net )
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    RunTestBed()
