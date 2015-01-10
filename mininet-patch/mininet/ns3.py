"""
NS-3 integration for Mininet.

 Mininet                                               Mininet
 node 1                                                node 2
+---------+                                           +---------+
| name    |                                           | name    |
| space 1 |                                           | space 2 |
| ------- |                                           |---------|
| shell   |                                           | shell   |
| ------- |                                           |---------|
| Linux   |                                           | Linux   |
| network |                                           | network |
| stack   |       ns-3              ns-3              | stack   |
| ------  |       node 1            node 2            |---------|
| TAP     |      |===========|     |===========|      | TAP     |
| intf.   |<-fd->| TapBridge |     | TapBridge |<-fd->| intf.   |
+---------+      | --------- |     | --------- |      +---------+
                 | ns-3      |     | ns-3      |
                 | net       |     | net       |
                 | device    |     | device    |
                 +-----------+     +-----------+
                       ||               ||
                  +---------------------------+
                  |        ns-3 channel       |
                  +---------------------------+
               |<------------------------------->|
                           ns-3 process
                      in the root namespace

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

# Default duration of ns-3 simulation thread. You can freely modify this value.

default_duration = 3600

# Set ns-3 simulator type to realtime simulator implementation.
# You can find more information about realtime modes here:
# http://www.nsnam.org/docs/release/3.17/manual/singlehtml/index.html#realtime
# http://www.nsnam.org/wiki/index.php/Emulation_and_Realtime_Scheduler

ns.core.GlobalValue.Bind( "SimulatorImplementationType", ns.core.StringValue( "ns3::RealtimeSimulatorImpl" ) )

# Enable checksum computation in ns-3 devices. By default ns-3 does not compute checksums - it is not needed
# when it runs in simulation mode. However, when it runs in emulation mode and exchanges packets with the real
# world, bit errors may occur in the real world, so we need to enable checksum computation.

ns.core.GlobalValue.Bind( "ChecksumEnabled", ns.core.BooleanValue ( "true" ) )

# Arrays which track all created TBIntf objects and Mininet nodes which has assigned an underlying ns-3 node.

allTBIntfs = []
allNodes = []

# These four global functions below are used to control ns-3 simulator thread. They are global, because
# ns-3 has one global singleton simulator object.

def start():
    """ Start the simulator thread in background.
        It should be called after configuration of all ns-3 objects
        (TBintfs, Segments and Links).
        Attempt of adding an ns-3 object when simulator thread is
        running may result in segfault. You should stop it first."""
    global thread
    if 'thread' in globals() and thread.isAlive():
        warn( "NS-3 simulator thread already running." )
        return
    # Install all TapBridge ns-3 devices not installed yet.
    for intf in allTBIntfs:
        if not intf.nsInstalled:
            intf.nsInstall()
    # Set up the simulator thread.
    thread = threading.Thread( target = runthread )
    thread.daemon = True
    # Start the simulator thread (this is where fork happens).
    # FORK!
    thread.start()
    # FORK:PARENT
    # Code below is executed in the parent thread.
    # Move all tap interfaces not moved yet to the right namespace.
    for intf in allTBIntfs:
        if not intf.inRightNamespace:
            intf.namespaceMove()
    return

def runthread():
    """ Method called in the simulator thread on its start.
        Should not be called manually."""
    # FORK:CHILD
    # Code below is executed in the simulator thread after the fork.
    # Stop event must be scheduled before simulator start. Not scheduling it
    # may lead leads to segfault.
    ns.core.Simulator.Stop( ns.core.Seconds( default_duration ) )
    # Start simulator. Function below blocks the Python thread and returns when simulator stops.
    ns.core.Simulator.Run()

def stop():
    """ Stop the simulator thread now."""
    # Schedule a stop event.
    ns.core.Simulator.Stop( ns.core.MilliSeconds( 1 ) )
    # Wait until the simulator thread stops.
    while thread.isAlive():
        time.sleep( 0.01 )
    return

def clear():
    """ Clear ns-3 simulator.
        It should be called when simulator is stopped."""
    ns.core.Simulator.Destroy()
    for intf in allTBIntfs:
        intf.nsInstalled = False
        #intf.delete()
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

# Functions for manipulating nodes positions. Nodes positioning is useful in
# wireless channel simulations: distance between nodes affects received signal power
# and, thus, throughput.
# Node positions are stored in the underlying ns-3 node (not in Mininet node itself).

def getPosition( node ):
    """ Return the ns-3 (x, y, z) position of a Mininet node.
        Coordinates are in the 3D Cartesian system.
        The unit is meters.
        node: Mininet node"""
    # Check if this Mininet node has assigned the underlying ns-3 node.
    if hasattr( node, 'nsNode' ) and node.nsNode is not None:
        # If it is assigned, go ahead.
        pass
    else:
        # If not, create new ns-3 node and assign it to this Mininet node.
        node.nsNode = ns.network.Node()
        allNodes.append( node )
    try:
        # Get postion coordinates from the ns-3 node
        mm = node.nsNode.GetObject( ns.mobility.MobilityModel.GetTypeId() )
        pos = mm.GetPosition()
        return ( pos.x, pos.y, pos.z )
    except AttributeError:
        warn( "ns-3 mobility model not found\n" )
        return ( 0, 0, 0 )

def setPosition( node, x, y, z ):
    """ Set the ns-3 (x, y, z) position of a Mininet node.
        Coordinates are in the 3D Cartesian system.
        The unit is meters.
        node: Mininet node
        x: integer or float x coordinate
        y: integer or float y coordinate
        z: integer or float z coordinate"""
    # Check if this Mininet node has assigned the underlying ns-3 node.
    if hasattr( node, 'nsNode' ) and node.nsNode is not None:
        # If it is assigned, go ahead.
        pass
    else:
        # If not, create new ns-3 node and assign it to this Mininet node.
        node.nsNode = ns.network.Node()
        allNodes.append( node )
    try:
        mm = node.nsNode.GetObject( ns.mobility.MobilityModel.GetTypeId() )
        if x is None:
            x = 0.0
        if y is None:
            y = 0.0
        if z is None:
            z = 0.0
        # Set postion coordinates in the ns-3 node
        pos = mm.SetPosition( ns.core.Vector( x, y, z ) )
    except AttributeError:
        warn( "ns-3 mobility model not found, not setting position\n" )

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

# TBIntf is the main workhorse of the module. TBIntf is a tap Linux interface located on Mininet
# node, which is bridged with ns-3 device located on ns-3 node.

class TBIntf( Intf ):
    """ Interface object that is bridged with ns-3 emulated device.
        This is a subclass of Mininet basic Inft object. """

    def __init__( self, name, node, port=None,
                  nsNode=None, nsDevice=None, mode=None, **params ):
        """name: interface name (e.g. h1-eth0)
           node: owning Mininet node (where this intf most likely lives)
           link: parent link if we're part of a link #TODO
           nsNode: underlying ns-3 node
           nsDevice: ns-3 device which the tap interface is bridged with
           mode: mode of TapBridge ns-3 device (UseLocal or UseBridge)
           other arguments are passed to config()"""
        self.name = name
        # Create a tap interface in the system, ns-3 TapBridge will connect to that interface later.
        self.createTap()
        # Set this Intf to be delayed move. This tells Mininet not to move the interface to the right
        # namespace during Intf.__init__(). Therefore, the interface must be moved manually later.
        # Actually, interfaces are moved right after the simulator thread start, in the start() global
        # function.
        self.delayedMove = True
        # If this node is running in its own namespace...
        if node.inNamespace:
            # ...this interface is not yet in the right namespace (it is in the root namespace just after
            # creation) and should be moved later.
            self.inRightNamespace = False
        else:
            # ...interface should stay in the root namespace, so it is in right namespace now.
            self.inRightNamespace = True
        # Initialize parent Intf object.
        Intf.__init__( self, name, node, port , **params)
        allTBIntfs.append( self )
        self.nsNode = nsNode
        self.nsDevice = nsDevice
        self.mode = mode
        self.params = params
        self.nsInstalled = False
        # Create TapBridge ns-3 device.
        self.tapbridge = ns.tap_bridge.TapBridge()
        # If ns-3 node and bridged ns-3 device are set and TapBridge mode is known...
        if self.nsNode and self.nsDevice and ( self.mode or self.node ):
            # ...call nsInstall().
            self.nsInstall()

    def createTap( self ):
        """Create tap Linux interface in the root namespace."""
        quietRun( 'ip tuntap add ' + self.name + ' mode tap' )

    def nsInstall( self ):
        """Install TapBridge ns-3 device in the ns-3 simulator."""
        if not isinstance( self.nsNode, ns.network.Node ):
            warn( "Cannot install TBIntf to ns-3 Node: "
                  "nsNode not specified\n" )
            return
        if not isinstance( self.nsDevice, ns.network.NetDevice ):
            warn( "Cannot install TBIntf to ns-3 Node: "
                  "nsDevice not specified\n" )
            return
        # If TapBridge mode has not been set explicitly, determine it automatically basing on
        # a Mininet node type. You can find more about TapBridge modes there:
        # http://www.nsnam.org/docs/release/3.18/models/singlehtml/index.html#tap-netdevice
        if self.mode is None and self.node is not None:
            # If Mininet node is some kind of Switch...
            if isinstance( self.node, Switch ):
                # ...use "UseBridge" mode. In this mode there may be many different L2 devices with
                # many source addresses on the Linux side of TapBridge, but bridged ns-3 device must
                # support SendFrom().
                self.mode = "UseBridge"
            else:
                # ...in the other case use "UseLocal" mode. In this mode there may be only one L2 source device
                # on the Linux side of TapBridge (TapBridge will change source MAC address of all packets coming
                # from the tap interface to the discovered address of this interface). In this mode bridged ns-3
                # device does not have to support SendFrom() (it uses Send() function to send packets).
                self.mode = "UseLocal"
        if self.mode is None:
            warn( "Cannot install TBIntf to ns-3 Node: "
                  "cannot determine mode: neither mode nor (mininet) node specified\n" )
            return
        # Set all required TapBridge attributes.
        self.tapbridge.SetAttribute ( "Mode", ns.core.StringValue( self.mode ) )
        self.tapbridge.SetAttribute ( "DeviceName", ns.core.StringValue( self.name ) )
        self.tapbridge.SetAttributeFailSafe ( "Instant", ns.core.BooleanValue( True ) ) # to be implemented in ns-3
        # Add TapBridge device to the ns-3 node.
        self.nsNode.AddDevice( self.tapbridge )
        # Set this TapBridge to be bridged with the specified ns-3 device.
        self.tapbridge.SetBridgedNetDevice( self.nsDevice )
        # Installation is done.
        self.nsInstalled = True

    def namespaceMove( self ):
        """Move tap Linux interface to the right namespace."""
        loops = 0
        # Wait until ns-3 process connects to the tap Linux interface. ns-3 process resides in the root
        # network namespace, so it must manage to connect to the interface before it is moved to the node
        # namespace. After interface move ns-3 process will not see the interface.
        while not self.isConnected():
            time.sleep( 0.01 )
            loops += 1
            if loops > 10:
                warn( "Cannot move TBIntf to mininet Node namespace: "
                      "ns-3 has not connected yet to the TAP interface\n" )
                return
        # Wait a little more, just for be sure ns-3 process not miss that.
        time.sleep( 0.01 )
        # Move interface to the right namespace.
        moveIntf( self.name, self.node )
        self.inRightNamespace = True
        # IP address has been reset while moving to namespace, needs to be set again.
        if self.ip is not None:
            self.setIP( self.ip, self.prefixLen )
        # The same for 'up'.
        self.isUp( True )

    def isConnected( self ):
        """Check if ns-3 TapBridge has connected to the Linux tap interface."""
        return self.tapbridge.IsLinkUp()

    def cmd( self, *args, **kwargs ):
        "Run a command in our owning node namespace or in the root namespace when not yet inRightNamespace."
        if self.inRightNamespace:
            return self.node.cmd( *args, **kwargs )
        else:
            cmd = ' '.join( [ str( c ) for c in args ] )
            return errRun( cmd )[ 0 ]

    def rename( self, newname ):
        "Rename interface"
        # If TapBridge is installed in ns-3, but ns-3 has not connected to the Linux tap interface yet...
        if self.nsInstalled and not self.isConnected():
            # ...change device name in TapBridge to the new one.
            self.tapbridge.SetAttribute ( "DeviceName", ns.core.StringValue( newname ) )
        Intf.rename( self, newname )

    def delete( self ):
        "Delete interface"
        if self.nsInstalled:
            warn( "You can not delete once installed ns-3 device, "
                  "run mininet.ns3.clear() to delete all ns-3 devices\n" )
        else:
            Intf.delete( self )

# Network segment is a Mininet object consistng of ns-3 channel of a specific type. This can be seen as
# an equivalent of collision domain. Many Mininet nodes can be connected to the one network segment.
# During connecting, Mininet creates ns-3 device of particular type in the underlying  ns-3 node.
# Then it connects this ns-3 device to the segment's ns-3 channel. Next, Mininet creates TBIntf in the
# specified Mininet node and bridges this tap interface with the ns-3 device created formerly.

# Network link is a subclass of network segment. It is a network segment with only two nodes connected.
# Moreover, network link is a subclass of Mininet Link. It means that you can use it like standard Mininet
# Link and alternatively with it: it supports all methods of its superclass and constructor arguments order
# is the same.

# SimpleChannel is the simplest channel model available in ns-3. Many devices can be connected to it
# simultaneously. Devices supports SendFrom(), therefore it can be used in "UseBridge" mode (for example
# for connecting switches). There is no implemented channel blocking - many devices can transmit
# simultaneously. Data rate and channel delay can not be set. However, one can
# set the receiver error model in SimpleNetDevice to simulate packet loss. You can find more information
# about the SimpleChannel in its source code and here:
# http://www.nsnam.org/docs/doxygen/classns3_1_1_simple_channel.html

class SimpleSegment( object ):
    """The simplest channel model available in ns-3.
       SimpleNetDevice supports SendFrom()."""
    def __init__( self ):
        self.channel = ns.network.SimpleChannel()

    def add( self, node, port=None, intfName=None, mode=None ):
        """Connect Mininet node to the segment.
           node: Mininet node
           port: node port number (optional)
           intfName: node tap interface name (optional)
           mode: TapBridge mode (UseLocal or UseBridge) (optional)"""
        # Check if this Mininet node has assigned an underlying ns-3 node.
        if hasattr( node, 'nsNode' ) and node.nsNode is not None:
            # If it is assigned, go ahead.
            pass
        else:
            # If not, create new ns-3 node and assign it to this Mininet node.
            node.nsNode = ns.network.Node()
            allNodes.append( node )
        # Create ns-3 device.
        device = ns.network.SimpleNetDevice()
        device.SetAddress (ns.network.Mac48Address.Allocate ())
        # Connect this device to the segment's channel.
        device.SetChannel(self.channel)
        # Add this device to the ns-3 node.
        node.nsNode.AddDevice(device)
        # If port number is not specified...
        if port is None:
            # ...obtain it automatically.
            port = node.newPort()
        # If interface name is not specified...
        if intfName is None:
            # ...obtain it automatically.
            intfName = node.name + '-eth' + repr( port )
        # In the specified Mininet node, create TBIntf bridged with the 'device'.
        tb = TBIntf( intfName, node, port, node.nsNode, device, mode )
        return tb


class SimpleLink( SimpleSegment, Link ):
    """Link between two nodes using the SimpleChannel ns-3 model"""
    def __init__( self, node1, node2, port1=None, port2=None,
                  intfName1=None, intfName2=None ):
        """Create simple link to another node, making two new tap interfaces.
        node1: first Mininet node
        node2: second Mininet node
        port1: node1 port number (optional)
        port2: node2 port number (optional)
        intfName1: node1 interface name (optional)
        intfName2: node2 interface name (optional)"""
        SimpleSegment.__init__( self )
        intf1 = SimpleSegment.add( self, node1, port1, intfName1 )
        intf2 = SimpleSegment.add( self, node2, port2, intfName2 )
        intf1.link = self
        intf2.link = self
        self.intf1, self.intf2 = intf1, intf2

# CsmaChannel is a more advanced model, built up upon SimpleChannel model. CsmaChannel is an equivalent
# of Ethernet channel, with CSMA blocking during transmission. Moreover, data rate and channel delay can
# be set (notice: setting high delay can result in low data rate, as channel is considered blocked for the
# trasmission of next packet for the delay interval after transmission start).
# You can find more information about CsmaChannel and CsmaNetDevice here:
# http://www.nsnam.org/docs/release/3.18/models/singlehtml/index.html#document-csma

class CSMASegment( object ):
    """Equivalent of the Ethernet channel
       CsmaNetDevice supports SendFrom()"""
    def __init__( self, DataRate=None, Delay=None ):
        """DataRate: forced data rate of connected devices (optional), for example: 10Mbps, default: no-limit
           Delay: channel trasmission delay (optional), for example: 10ns, default: 0"""
        self.channel = ns.csma.CsmaChannel()
        if DataRate is not None:
            self.channel.SetAttribute( "DataRate", ns.network.DataRateValue( ns.network.DataRate( DataRate ) ) )
        if Delay is not None:
            self.channel.SetAttribute( "Delay", ns.core.TimeValue( ns.core.Time( Delay ) ) )

    def add( self, node, port=None, intfName=None, mode=None ):
        """Connect Mininet node to the segment.
           node: Mininet node
           port: node port number (optional)
           intfName: node tap interface name (optional)
           mode: TapBridge mode (UseLocal or UseBridge) (optional)"""
        # Check if this Mininet node has assigned an underlying ns-3 node.
        if hasattr( node, 'nsNode' ) and node.nsNode is not None:
            # If it is assigned, go ahead.
            pass
        else:
            # If not, create new ns-3 node and assign it to this Mininet node.
            node.nsNode = ns.network.Node()
            allNodes.append( node )
        # Create ns-3 device.
        device = ns.csma.CsmaNetDevice()
        # Create queue used in the device.
        queue = ns.network.DropTailQueue()
        # Connect this device to the segment's channel.
        device.Attach(self.channel)
        # Set ns-3 device to use created queue.
        device.SetQueue(queue)
        device.SetAddress (ns.network.Mac48Address.Allocate ())
        # Add this device to the ns-3 node.
        node.nsNode.AddDevice(device)
        # If port number is not specified...
        if port is None:
            # ...obtain it automatically.
            port = node.newPort()
        # If interface name is not specified...
        if intfName is None:
            # ...obtain it automatically.
            intfName = node.name + '-eth' + repr( port )
        # In the specified Mininet node, create TBIntf bridged with the 'device'.
        tb = TBIntf( intfName, node, port, node.nsNode, device, mode )
        return tb


class CSMALink( CSMASegment, Link ):
    """Link between two nodes using the CsmaChannel ns-3 model"""
    def __init__( self, node1, node2, port1=None, port2=None,
                  intfName1=None, intfName2=None, DataRate=None, Delay=None ):
        """Create Ethernet link to another node, making two new tap interfaces.
        node1: first Mininet node
        node2: second Mininet node
        port1: node1 port number (optional)
        port2: node2 port number (optional)
        intfName1: node1 interface name (optional)
        intfName2: node2 interface name (optional)
        DataRate: forced data rate of connected devices (optional), for example: 10Mbps, default: no-limit
        Delay: channel trasmission delay (optional), for example: 10ns, default: 0"""
        CSMASegment.__init__( self, DataRate, Delay )
        intf1 = CSMASegment.add( self, node1, port1, intfName1 )
        intf2 = CSMASegment.add( self, node2, port2, intfName2 )
        intf1.link = self
        intf2.link = self
        self.intf1, self.intf2 = intf1, intf2

# Wifi model in ns-3 is much more complicated than wired models. Fortunatelly, there are many
# tutorials and examples of its usage in the net. Moreover, there is a large community of researchers
# and programmers around it.
# You can find more information about Wifi ns-3 model here:
# http://www.nsnam.org/docs/release/3.18/models/singlehtml/index.html#document-wifi

# In order to facilitate its usage, it provides a series of helpers. Helpers are objects which provides
# fucntions used to create and set up of various components of Wifi model.

class WIFISegment( object ):
    """Equivalent of radio WiFi channel.
       Only Ap and WDS devices support SendFrom()."""
    def __init__( self ):
        # Helpers instantiation.
        self.channelhelper = ns.wifi.YansWifiChannelHelper.Default()
        self.phyhelper = ns.wifi.YansWifiPhyHelper.Default()
        self.wifihelper = ns.wifi.WifiHelper.Default()
        self.machelper = ns.wifi.NqosWifiMacHelper.Default()
        # Setting channel to phyhelper.
        self.channel = self.channelhelper.Create()
        self.phyhelper.SetChannel( self.channel )

    def add( self, node, port=None, intfName=None, mode=None ):
        """Connect Mininet node to the segment.
           Will create WifiNetDevice with Mac type specified in
           the MacHelper (default: AdhocWifiMac).
           node: Mininet node
           port: node port number (optional)
           intfName: node tap interface name (optional)
           mode: TapBridge mode (UseLocal or UseBridge) (optional)"""
        # Check if this Mininet node has assigned an underlying ns-3 node.
        if hasattr( node, 'nsNode' ) and node.nsNode is not None:
            # If it is assigned, go ahead.
            pass
        else:
            # If not, create new ns-3 node and assign it to this Mininet node.
            node.nsNode = ns.network.Node()
            allNodes.append( node )
        # Install new device to the ns-3 node, using provided helpers.
        device = self.wifihelper.Install( self.phyhelper, self.machelper, node.nsNode ).Get( 0 )
        mobilityhelper = ns.mobility.MobilityHelper()
        # Install mobility object to the ns-3 node.
        mobilityhelper.Install( node.nsNode )
        # If port number is not specified...
        if port is None:
            # ...obtain it automatically.
            port = node.newPort()
        # If interface name is not specified...
        if intfName is None:
            # ...obtain it automatically.
            intfName = node.name + '-eth' + repr( port )
        # In the specified Mininet node, create TBIntf bridged with the 'device'.
        tb = TBIntf( intfName, node, port, node.nsNode, device, mode )
        return tb

    def addAdhoc( self, node, port=None, intfName=None, mode=None ):
        """Connect Mininet node to the segment.
           Will create WifiNetDevice with AdhocWifiMac.
           Devices in that mode does not support SendFrom().
           node: Mininet node
           port: node port number (optional)
           intfName: node tap interface name (optional)
           mode: TapBridge mode (UseLocal or UseBridge) (optional)"""
        self.machelper.SetType ("ns3::AdhocWifiMac")
        return self.add( node, port, intfName, mode )

    def addAp( self, node, port=None, intfName=None, mode=None, ssid="default-ssid" ):
        """Connect Mininet node to the segment.
           Will create WifiNetDevice with ApWifiMac (access point).
           Devices in that mode supports SendFrom() (can be used on switches).
           node: Mininet node
           port: node port number (optional)
           intfName: node tap interface name (optional)
           mode: TapBridge mode (UseLocal or UseBridge) (optional)
           ssid: network SSID (optional)"""
        self.machelper.SetType ("ns3::ApWifiMac", "Ssid", ns.wifi.SsidValue (ns.wifi.Ssid(ssid)),
                                "BeaconGeneration", ns.core.BooleanValue(True),
                                "BeaconInterval", ns.core.TimeValue(ns.core.Seconds(2.5)))
        return self.add( node, port, intfName, mode )

    def addSta( self, node, port=None, intfName=None, mode=None, ssid="default-ssid" ):
        """Connect Mininet node to the segment.
           Will create WifiNetDevice with StaWifiMac (client station).
           Devices in that mode does not support SendFrom().
           node: Mininet node
           port: node port number (optional)
           intfName: node tap interface name (optional)
           mode: TapBridge mode (UseLocal or UseBridge) (optional)
           ssid: network SSID (optional)"""
        self.machelper.SetType ("ns3::StaWifiMac", "Ssid", ns.wifi.SsidValue (ns.wifi.Ssid(ssid)))
        return self.add( node, port, intfName, mode )


class WIFIApStaLink( WIFISegment, Link ):
    """Link between two nodes using infrastructure WiFi channel."""
    def __init__( self, node1, node2, port1=None, port2=None,
                  intfName1=None, intfName2=None, ssid="default-ssid" ):
        """Create infractructure WiFi link to another node, making two new tap interfaces.
        node1: first Mininet node (access point)
        node2: second Mininet node (client station)
        port1: node1 port number (optional)
        port2: node2 port number (optional)
        intfName1: node1 interface name (optional)
        intfName2: node2 interface name (optional)
        ssid: network SSID (optional)"""
        WIFISegment.__init__( self )
        intf1 = WIFISegment.addAp( self, node1, port1, intfName1, ssid=ssid )
        intf2 = WIFISegment.addSta( self, node2, port2, intfName2, ssid=ssid )
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
            intfName = node.name + '-eth' + repr( port )
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

# WIFIBridgeLink uses WDSWifiMac mode, which (as for now) is not a part of ns-3 official release. You can add
# it to ns-3 using this patch: http://gist.github.com/piotrjurkiewicz/6483675

# With the infrastructure mode it is posiible to connect hosts (Sta devices) with switches (Ap devices).
# However, you can't connect two switches (two Distribution Systems). In order to do that, you must use all
# four address fields in 802.11 frame. Such mode is called WDS mode or 4-address mode (4A) or even bridge mode.

class WIFIBridgeLink( WIFISegment, Link ):
    """Link between two nodes using WDS WiFi channel.
       This link bridges two distribution systems, so two
       switches can be connected on the both sides of link."""
    def __init__( self, node1, node2, port1=None, port2=None,
                  intfName1=None, intfName2=None ):
        """Create WDS bridge, making two new tap interfaces.
        node1: first Mininet node
        node2: second Mininet node
        port1: node1 port number (optional)
        port2: node2 port number (optional)
        intfName1: node1 interface name (optional)
        intfName2: node2 interface name (optional)"""
        WIFISegment.__init__( self )
        # It this case the order of TBIntf and ns-3 device creation is reversed:
        # TBIntfs (and thus tap interfaces) are created before ns-3 WifiNetDevices.
        # Tap interfaces must be created earlier, becauses Mac addresses of the paired
        # node must be provided when setting WDSWifiMac.
        # NODE 1
        # Check if this Mininet node has assigned an underlying ns-3 node.
        if hasattr( node1, 'nsNode' ) and node1.nsNode is not None:
            # If it is assigned, go ahead.
            pass
        else:
            # If not, create new ns-3 node and assign it to this Mininet node.
            node1.nsNode = ns.network.Node()
            allNodes.append( node1 )
        mobilityhelper1 = ns.mobility.MobilityHelper()
        # Install mobility object to the ns-3 node.
        mobilityhelper1.Install( node1.nsNode )
        # If port number is not specified...
        if port1 is None:
            # ...obtain it automatically.
            port1 = node1.newPort()
        # If interface name is not specified...
        if intfName1 is None:
            # ...obtain it automatically.
            intfName1 = node1.name + '-eth' + repr( port1 )
        # ns-3 device is not specified in the following call, so nsInstall() will nor occur automatically.
        tb1 = TBIntf( intfName1, node1, port1, node1.nsNode )
        # NODE 2
        # Check if this Mininet node has assigned an underlying ns-3 node.
        if hasattr( node2, 'nsNode' ) and node2.nsNode is not None:
            # If it is assigned, go ahead.
            pass
        else:
            # If not, create new ns-3 node and assign it to this Mininet node.
            node2.nsNode = ns.network.Node()
            allNodes.append( node2 )
        mobilityhelper2 = ns.mobility.MobilityHelper()
        # Install mobility object to the ns-3 node.
        mobilityhelper2.Install( node2.nsNode )
        # If port number is not specified...
        if port2 is None:
            # ...obtain it automatically.
            port2 = node2.newPort()
        # If interface name is not specified...
        if intfName2 is None:
            # ...obtain it automatically.
            intfName2 = node2.name + '-eth' + repr( port2 )
        # ns-3 device is not specified in the following call, so nsInstall() will nor occur automatically.
        tb2 = TBIntf( intfName2, node2, port2, node2.nsNode )
        # NODE 1
        # Set Mac type and paired device Mac address for the node 1.
        self.machelper.SetType ("ns3::WDSWifiMac",
                                "ReceiverAddress", ns.network.Mac48AddressValue( ns.network.Mac48Address( tb2.MAC() ) ) )
        # Create and install WifiNetDevice.
        device1 = self.wifihelper.Install( self.phyhelper, self.machelper, node1.nsNode ).Get( 0 )
        # Set nsDevice in TapBridge the the created one.
        tb1.nsDevice = device1
        # Install TapBridge to the ns-3 node.
        tb1.nsInstall()
        # NODE 2
        # Set Mac type and paired device Mac address for the node 2.
        self.machelper.SetType ("ns3::WDSWifiMac",
                                "ReceiverAddress", ns.network.Mac48AddressValue( ns.network.Mac48Address( tb1.MAC() ) ) )
        # Create and install WifiNetDevice.
        device2 = self.wifihelper.Install( self.phyhelper, self.machelper, node2.nsNode ).Get( 0 )
        # Set nsDevice in TapBridge the the created one.
        tb2.nsDevice = device2
        # Install TapBridge to the ns-3 node.
        tb2.nsInstall()
        #
        tb1.link = self
        tb2.link = self
        self.intf1, self.intf2 = tb1, tb2

