OpenNet
=======
A simulator built on top of Mininet and ns-3 for Software-Defined Wireless Local Area Network (SDWLAN)

Feature
-------
* Complement ns-3 by supporting channel scan behavior on Wi-Fi station (sta-wifi-scan.patch)
* Show CsmaLink and SimpleLink in NetAnim (animation-interface.patch)
* Fix runtime error when access PacketMetadata of CsmaLink (packet-metadata.patch)

Prerequisite
------------
1. Fetch and install [Mininet](https://github.com/mininet/mininet "Mininet")
2. Fetch and install [ns-3](http://www.nsnam.org/ns-3-18 "ns-3.18")
3. Apply [patches](https://github.com/mininet/mininet/wiki/Link-modeling-using-ns-3 "Link modeling using ns-3") to link Mininet with ns-3

Install OpenNet
--------------------
1. Patch and revbuild Mininet <br/>
a. Replace mininet/ns3.py with the one in mininet-patch
<pre>cp mininet-patch/mininet/ns3.py mininet/mininet</pre>
b. Add WiFi roaming simulation script to example
<pre>cp mininet-patch/examples/wifiroaming.py mininet/examples</pre>
c. Rebuild Mininet <br/>
<pre>cd mininet <br/>make install</pre>

2. Patch and rebuild ns-3 <br/>
a. Copy patches to the ns-3 root folder
<pre>cp ns3-patch/*.patch ns-allinone-3.18</pre>
b. Apply patches
<pre>cd ns-allinone-3.18
patch -p1 &lt; sta-wifi-scan.patch
patch -p1 &lt; animation-interface.patch
patch -p1 &lt; packet-metadata.patch
patch -p1 &lt; netanim-python.patch</pre>
c. Scan python API
<pre>./waf --apiscan=netanim</pre>
d. Rebuild ns-3
<pre>cd ns-3.18
./waf build</pre>

Run OpenNet
-----------
> <pre>cd ns-allinone-3.18/ns-3.18
./waf --pyrun ../../mininet/examples/wifiroaming.py
</pre>