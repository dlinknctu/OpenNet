"""
NS-3 integration for Mininet.

"""

import threading, time, random

from mininet.log import info, error, warn, debug
from mininet.link import Intf, Link
from mininet.node import Switch, Node
from mininet.util import quietRun, moveIntf, errRun

import ns.core 
import ns.network 
import ns.tap_bridge 
import ns.csma 
import ns.wifi 
import ns.mobility


default_duration = 3600

ns.core.GlobalValue.Bind( "SimulatorImplementationType", ns.core.StringValue( "ns3::RealtimeSimulatorImpl" ) )
ns.core.GlobalValue.Bind( "ChecksumEnabled", ns.core.BooleanValue ( "true" ) )

allTBIntfs = []
allNodes = []

def start():
    global thread
    if 'thread' in globals() and thread.isAlive():
        warn( "NS-3 simulator thread already running." )
        return
    for intf in allTBIntfs:
        if not intf.nsInstalled:
            intf.nsInstall()
    thread = threading.Thread( target = runthread )
    thread.daemon = True
    thread.start()   
    for intf in allTBIntfs:
        if not intf.inRightNamespace:
            intf.namespaceMove()
    return

def runthread():
    ns.core.Simulator.Stop( ns.core.Seconds( default_duration ) )
    ns.core.Simulator.Run()

def stop():
    ns.core.Simulator.Stop( ns.core.MilliSeconds( 1 ) )
    while thread.isAlive():
        time.sleep( 0.01 )
    return

def clear():
    ns.core.Simulator.Destroy()
    for intf in allTBIntfs:
        intf.nsInstalled = False
        intf.delete()
    for node in allNodes:
        del node.nsNode
    del allTBIntfs[:]
    del allNodes[:]
    return

def createAttributes( n0="", v0=ns.core.EmptyAttributeValue(),
                      n1="", v1=ns.core.EmptyAttributeValue(),
                      n2="", v2=ns.core.EmptyAttributeValue(),
                      n3="", v3=ns.core.EmptyAttributeValue(),
                      n4="", v4=ns.core.EmptyAttributeValue(),
                      n5="", v5=ns.core.EmptyAttributeValue(),
                      n6="", v6=ns.core.EmptyAttributeValue(),
                      n7="", v7=ns.core.EmptyAttributeValue()):
    attrs = { 'n0' : n0, 'v0' : v0, 
              'n1' : n1, 'v1' : v1,
              'n2' : n2, 'v2' : v2,
              'n3' : n3, 'v3' : v3,
              'n4' : n4, 'v4' : v4,
              'n5' : n5, 'v5' : v5,
              'n6' : n6, 'v6' : v6,
              'n7' : n7, 'v7' : v7 }
    return attrs

def setAttributes( func, typeStr, attrs):
    a = { 'n0' : "", 'v0' : ns.core.EmptyAttributeValue(), 
          'n1' : "", 'v1' : ns.core.EmptyAttributeValue(),
          'n2' : "", 'v2' : ns.core.EmptyAttributeValue(),
          'n3' : "", 'v3' : ns.core.EmptyAttributeValue(),
          'n4' : "", 'v4' : ns.core.EmptyAttributeValue(),
          'n5' : "", 'v5' : ns.core.EmptyAttributeValue(),
          'n6' : "", 'v6' : ns.core.EmptyAttributeValue(),
          'n7' : "", 'v7' : ns.core.EmptyAttributeValue() }
    a.update (attrs)
    func (typeStr, a['n0'], a['v0'], a['n1'], a['v1'], 
                   a['n2'], a['v2'], a['n3'], a['v3'],
                   a['n4'], a['v4'], a['n5'], a['v5'],
                   a['n6'], a['v6'], a['n7'], a['v7'])
        
def createMobilityHelper( mobilityType = "ns3::ConstantVelocityMobilityModel", **attrs):
    mobHelper = ns.mobility.MobilityHelper()
    setAttributes (mobHelper.SetMobilityModel, mobilityType, attrs)
    return mobHelper

def setPositionAllocate( mobHelper, posAllocateType = "ns3::RandomDiscPositionAllocator", **attrs):
    setAttributes (mobHelper.SetPositionAllocator, posAllocateType, attrs)
    return mobHelper

def setListPositionAllocate( mobHelper, lpa):
    mobHelper.SetPositionAllocator(lpa)
    return mobHelper

def createListPositionAllocate(**attrs):
    lpa = ns.mobility.ListPositionAllocator()
    i = 1
    while True:
        if not attrs.has_key ('x'+ str(i)) and not attrs.has_key ('y'+ str(i)) and not attrs.has_key ('z'+ str(i)):
            break
        x = attrs.get('x'+ str(i), 0)
        y = attrs.get('y'+ str(i), 0)
        z = attrs.get('z'+ str(i), 0)
        lpa.Add(ns.core.Vector(x, y, z))
        i = i+1
    return lpa

def hasMobilityModel( node ):
    if hasattr( node, 'nsNode' ) and node.nsNode is not None:
        pass
    else:
        node.nsNode = ns.network.Node()
        allNodes.append( node )
    try:
        mm = node.nsNode.GetObject(ns.mobility.MobilityModel.GetTypeId())
        return ( mm is not None )
    except AttributeError:
        warn("ns-3 mobility model not found\n")
        return False

def getMobilityModel( node ):
    ''' Return the mobility model of a node
    '''
    if hasattr( node, 'nsNode' ) and node.nsNode is not None:
        pass
    else:
        node.nsNode = ns.network.Node()
        allNodes.append( node )
    try:
        mm = node.nsNode.GetObject(ns.mobility.MobilityModel.GetTypeId())
        return mm
    except AttributeError:
        warn("ns-3 mobility model not found\n")
        return None

def setMobilityModel( node, mobHelper = None):
    ''' Set the mobility model of a node
    '''    
    if hasattr( node, 'nsNode' ) and node.nsNode is not None:
        pass
    else:
        node.nsNode = ns.network.Node()
        allNodes.append( node )
    if mobHelper is None:
        mobHelper = createMobilityHelper ()
    mobHelper.Install (node.nsNode)     

def getPosition( node ):
    ''' Return the ns-3 (x, y, z) position of a node.
    '''
    if hasattr( node, 'nsNode' ) and node.nsNode is not None:
        pass
    else:
        node.nsNode = ns.network.Node()
        allNodes.append( node )
    try:
        mm = node.nsNode.GetObject(ns.mobility.MobilityModel.GetTypeId())
        pos = mm.GetPosition()
        return (pos.x, pos.y, pos.z)
    except AttributeError:
        warn("ns-3 mobility model not found\n")
        return (0,0,0)

def setPosition( node, x = None, y = None, z = None ):
    ''' Set the ns-3 (x, y, z) position of a node.
    '''
    if hasattr( node, 'nsNode' ) and node.nsNode is not None:
        pass
    else:
        node.nsNode = ns.network.Node()
        allNodes.append( node )
    try:
        mm = node.nsNode.GetObject(ns.mobility.MobilityModel.GetTypeId())
        if x is None:
            x = 0.0
        if y is None:
            y = 0.0
        if z is None:
            z = 0.0
        pos = mm.SetPosition(ns.core.Vector(x, y, z))
    except AttributeError:
        warn("ns-3 mobility model not found, not setting position\n")


def getVelocity( node ):
    ''' Return the ns-3 (x, y, z) velocity of a node.
    '''
    if hasattr( node, 'nsNode' ) and node.nsNode is not None:
        pass
    else:
        node.nsNode = ns.network.Node()
        allNodes.append( node )
    try:
        mm = node.nsNode.GetObject(ns.mobility.ConstantVelocityMobilityModel.GetTypeId())
        vel = mm.GetVelocity()
        return (vel.x, vel.y, vel.z)
    except AttributeError:
        warn("ns-3 constant velocity mobility model not found\n")
        return (0,0,0)

def setVelocity( node, x = None, y = None, z = None ):
    ''' Set the ns-3 (x, y, z) velocity of a node.
    '''
    if hasattr( node, 'nsNode' ) and node.nsNode is not None:
        pass
    else:
        node.nsNode = ns.network.Node()
        allNodes.append( node )
    try:
        mm = node.nsNode.GetObject(ns.mobility.ConstantVelocityMobilityModel.GetTypeId())
        if x is None:
            x = 0.0
        if y is None:
            y = 0.0
        if z is None:
            z = 0.0
        vel = mm.SetVelocity(ns.core.Vector(x, y, z))
    except AttributeError:
        warn("ns-3 constant velocity mobility model not found, not setting position\n")

class TBIntf( Intf ):
    def __init__( self, name, node, port=None,
                  nsNode=None, nsDevice=None, mode=None, **params ):
        """
        """
        self.name = name
        self.createTap()
        self.delayedMove = True
        if node.inNamespace:
            self.inRightNamespace = False
        else:
            self.inRightNamespace = True
        Intf.__init__( self, name, node, port , **params)
        allTBIntfs.append( self )
        self.nsNode = nsNode
        self.nsDevice = nsDevice
        self.mode = mode
        self.params = params
        self.nsInstalled = False
        self.tapbridge = ns.tap_bridge.TapBridge()
        if self.nsNode and self.nsDevice and ( self.mode or self.node ):
            self.nsInstall()
        if self.node and self.nsInstalled and self.isInstant(): # instant mode to be implemented in ns-3
            self.namespaceMove()

    def createTap( self ):
        quietRun( 'ip tuntap add ' + self.name + ' mode tap' )
        print 'ip tuntap add', self.name, 'mod tap'

    def nsInstall( self ):
        if not isinstance( self.nsNode, ns.network.Node ):
            warn( "Cannot install TBIntf to ns-3 Node: "
                  "nsNode not specified\n" )
            return
        if not isinstance( self.nsDevice, ns.network.NetDevice ):
            warn( "Cannot install TBIntf to ns-3 Node: "
                  "nsDevice not specified\n" )
            return
        if self.mode is None and self.node is not None:
            if isinstance( self.node, Switch ):
                self.mode = "UseBridge"
            else:
                self.mode = "UseLocal"
        if self.mode is None:
            warn( "Cannot install TBIntf to ns-3 Node: "
                  "cannot determine mode: neither mode nor (mininet) node specified\n" )
            return
        self.tapbridge.SetAttribute ( "Mode", ns.core.StringValue( self.mode ) )
        self.tapbridge.SetAttribute ( "DeviceName", ns.core.StringValue( self.name ) )      
        self.tapbridge.SetAttributeFailSafe ( "Instant", ns.core.BooleanValue( True ) ) # to be implemented in ns-3
        self.nsNode.AddDevice( self.tapbridge )
        self.tapbridge.SetBridgedNetDevice( self.nsDevice )
        self.nsInstalled = True

    def namespaceMove( self ):
        loops = 0
        while not self.isConnected():
            time.sleep( 0.01 )
            loops += 1
            if loops > 10:
                warn( "Cannot move TBIntf to mininet Node namespace: "
                      "ns-3 has not connected yet to the TAP interface\n" )
                return
        moveIntf( self.name, self.node )
        self.inRightNamespace = True
        # IP address has been reset while moving to namespace, needs to be set again
        if self.ip is not None:
            self.setIP( self.ip, self.prefixLen )
        # The same for 'up'
        self.isUp( True )

    def isConnected( self ):
        return self.tapbridge.IsLinkUp()

    def isInstant( self ):
        return False # to be implemented in ns-3

    def cmd( self, *args, **kwargs ):
        "Run a command in our owning node or in root namespace when not yet inRightNamespace"
        if self.inRightNamespace:
            return self.node.cmd( *args, **kwargs )
        else:
            cmd = ' '.join( [ str( c ) for c in args ] )
            return errRun( cmd )[ 0 ]

    def rename( self, newname ):
        "Rename interface"
        if self.nsInstalled and not self.isConnected():
            self.tapbridge.SetAttribute ( "DeviceName", ns.core.StringValue( newname ) )
        Intf.rename( self, newname )

    def delete( self ):
        "Delete interface"
        if self.nsInstalled:
            warn( "You can not delete once installed ns-3 device, "
                  "run mininet.ns3.clear() to delete all ns-3 devices\n" )
        else:
            Intf.delete( self )
 
class SimpleSegment( object ):
    def __init__( self ):
        self.channel = ns.network.SimpleChannel()

    def add( self, node, port=None, intfName=None ):
        if hasattr( node, 'nsNode' ) and node.nsNode is not None:
            pass
        else:
            node.nsNode = ns.network.Node()
            allNodes.append( node )
        device = ns.network.SimpleNetDevice()
        device.SetChannel(self.channel)
        device.SetAddress (ns.network.Mac48Address.Allocate ())
        node.nsNode.AddDevice(device)
        if port is None:
            port = node.newPort()
        if intfName is None:
            intfName = Link.intfName( node, port ) # classmethod
        tb = TBIntf( intfName, node, port, node.nsNode, device )
        return tb


class SimpleLink( SimpleSegment, Link ):
    def __init__( self, node1, node2, port1=None, port2=None,
                  intfName1=None, intfName2=None ):
        SimpleSegment.__init__( self )
        intf1 = SimpleSegment.add( self, node1, port1, intfName1 )
        intf2 = SimpleSegment.add( self, node2, port2, intfName2 )
        intf1.link = self
        intf2.link = self
        self.intf1, self.intf2 = intf1, intf2


class CSMASegment( object ):
    def __init__( self, DataRate=None, Delay=None ):
        self.channel = ns.csma.CsmaChannel()
        if DataRate is not None:
            self.channel.SetAttribute( "DataRate", ns.network.DataRateValue( ns.network.DataRate( DataRate ) ) )
        if Delay is not None:
            self.channel.SetAttribute( "Delay", ns.core.TimeValue( ns.core.Time( Delay ) ) )

    def add( self, node, port=None, intfName=None ):
        if hasattr( node, 'nsNode' ) and node.nsNode is not None:
            pass
        else:
            node.nsNode = ns.network.Node()
            allNodes.append( node )
        device = ns.csma.CsmaNetDevice()
        queue = ns.network.DropTailQueue()
        device.Attach(self.channel)
        device.SetQueue(queue)
        device.SetAddress (ns.network.Mac48Address.Allocate ())
        node.nsNode.AddDevice(device)
        if port is None:
            port = node.newPort()
        if intfName is None:
            intfName = Link.intfName( node, port ) # classmethod
        tb = TBIntf( intfName, node, port, node.nsNode, device )
        return tb


class CSMALink( CSMASegment, Link ):
    def __init__( self, node1, node2, port1=None, port2=None,
                  intfName1=None, intfName2=None, DataRate=None, Delay=None ):
        CSMASegment.__init__( self, DataRate, Delay )
        intf1 = CSMASegment.add( self, node1, port1, intfName1 )
        intf2 = CSMASegment.add( self, node2, port2, intfName2 )
        intf1.link = self
        intf2.link = self
        self.intf1, self.intf2 = intf1, intf2

class WifiSegment( object ):
    def __init__( self, channelHelper = ns.wifi.YansWifiChannelHelper.Default(),
                        maxChannelNumber = 11, standard = ns.wifi.WIFI_PHY_STANDARD_80211a,
                        stationManager = "ns3::ArfWifiManager", **attrs):
        self.wifiHelper = ns.wifi.WifiHelper.Default ()
        setAttributes (self.wifiHelper.SetRemoteStationManager, stationManager, attrs)
        self.wifiHelper.SetStandard (standard)
        self.channel = channelHelper.Create ()
        self.maxChannelNumber = maxChannelNumber
        self.baseSsid = 'ssid'
        self.aps = []
        self.stas = []

    def __del__( self ):
        for ap in self.aps:
            del ap
        for sta in self.stas:
            del sta
        del self.aps[:]
        del self.stas[:]

    def add( self, node, phyHelper, macHelper, port=None, intfName=None ):
        if phyHelper is None or macHelper is None:
            warn( "phyHelper and macHelper must not be none.\n" )
            return None
        if hasattr( node, 'nsNode' ) and node.nsNode is not None:
            pass
        else:
            node.nsNode = ns.network.Node()
            allNodes.append( node )
        phyHelper.SetChannel (channel = self.channel)
        device = self.wifiHelper.Install (phyHelper, macHelper, node.nsNode).Get(0)
        node.nsNode.AddDevice (device)
        device.SetAddress (ns.network.Mac48Address.Allocate ())
        node.nsNode.AddDevice (device)
        if port is None:
            port = node.newPort()
        if intfName is None:
            intfName = Link.intfName( node, port ) # classmethod
        tb = TBIntf( intfName, node, port, node.nsNode, device)
        return tb

    def addAp( self, node, channelNumber, ssid=None, enableQos=False, port=None, intfName=None, **attrs):
        if ssid is None:
            ssid = self.baseSsid + str(len (self.aps) + 1)
        if channelNumber <= 0 or channelNumber > self.maxChannelNumber:
            channelNumber = random.randint (1, self.maxChannelNumber)
            warn("illegal channel number, choose a random channel number %s.\n", channelNumber)
        phyHelper = ns.wifi.YansWifiPhyHelper().Default()
        phyHelper.Set ("ChannelNumber", ns.core.UintegerValue(channelNumber))
        if enableQos:
            macHelper = ns.wifi.QosWifiMacHelper.Default()
        else:
            macHelper = ns.wifi.NqosWifiMacHelper.Default()
        
        setAttributes (macHelper.SetType, "ns3::ApWifiMac", attrs)
        tb = self.add (node, phyHelper, macHelper, port, intfName)
        if type( ssid ) is str:
            wifissid = ns.wifi.Ssid (ssid)
        else:
            wifissid = ssid
        try:
            tb.nsDevice.GetMac ().SetAttribute ("Ssid", ns.wifi.SsidValue (wifissid))
        except:
            warn("the type of wifissid isn't ssidvalue.\n")
            wifissid = ns.wifi.Ssid (self.baseSsid + str(len (self.aps) + 1))
            tb.nsDevice.GetMac ().SetAttribute ("Ssid", ns.wifi.SsidValue (wifissid))
        self.aps.append(tb)
        return tb

    def addSta( self, node, channelNumber, ssid=None, enableQos=False, enableScan = True, port=None, intfName=None, **attrs):
        if ssid is None:
            ssid = ""
        if channelNumber <= 0 or channelNumber > self.maxChannelNumber:
            channelNumber = random.randint (1, self.maxChannelNumber)
            warn("illegal channel number, choose a random channel number %s.\n", channelNumber)
        phyHelper = ns.wifi.YansWifiPhyHelper().Default()
        phyHelper.Set ("ChannelNumber", ns.core.UintegerValue(channelNumber))
        if enableQos:
            macHelper = ns.wifi.QosWifiMacHelper.Default()
        else:
            macHelper = ns.wifi.NqosWifiMacHelper.Default()
        setAttributes (macHelper.SetType, "ns3::StaWifiMac", attrs)
        tb = self.add (node, phyHelper, macHelper, port, intfName)     
        if type( ssid ) is str:
            wifissid = ns.wifi.Ssid (ssid)
        else:
            wifissid = ssid
        try:
            tb.nsDevice.GetMac ().SetAttribute ("Ssid", ns.wifi.SsidValue (wifissid))
        except:
            warn("the type of wifissid isn't ssidvalue.\n")
            tb.nsDevice.GetMac ().SetAttribute ("Ssid", ns.wifi.SsidValue (""))
        if enableScan:
            tb.nsDevice.GetMac ().SetAttribute ("ScanType", ns.core.EnumValue (ns.wifi.StaWifiMac.ACTIVE))
            tb.nsDevice.GetMac ().SetAttribute ("MaxScanningChannelNumber", ns.core.UintegerValue(self.maxChannelNumber))
        else:
            tb.nsDevice.GetMac ().SetAttribute ("ScanType", ns.core.EnumValue (ns.wifi.StaWifiMac.NOTSUPPORT))
        self.stas.append(tb)
        return tb

    @staticmethod
    def createChannelHelper():
        channel = ns.wifi.YansWifiChannelHelper ()
        return channelHelper

    def addChannelPropagationLoss( channelHelper, propagationLossType, **attrs ):
        setAttributes (channelHelper.AddPropagationLoss, propagationLossType, attrs)
        return channelHelper

    def setChannelPropagationDelay( channelHelper, propagationDelayType, **attrs ):
        setAttributes (channelHelper.AddPropagationLoss, propagationDelayType, attrs)
        return channelHelper
        
