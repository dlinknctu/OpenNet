# OpenNet
A simulator built on top of Mininet and ns-3 for Software-Defined Wireless Local Area Network (SDWLAN)  
http://www.slideshare.net/rascov/20140824-open-net  

## Feature
* Complement ns-3 by supporting channel scan behavior on Wi-Fi station (sta-wifi-scan.patch)
* Show CsmaLink and SimpleLink in NetAnim (animation-interface.patch)
* Fix runtime error when access PacketMetadata of CsmaLink [Submitted] (https://www.nsnam.org/bugzilla/show_bug.cgi?id=1787, "ns-3 bugzilla issue 1787")

## (Option 1) Use OpenNet from VM image
* OpenNet 1.1 VM image (Fedora 21) : [Download Link] (http://win.cs.nctu.edu.tw/opennet-1.1.zip)
    - user: nctuopennet
    - pw: nctuopennet

With this VM image, please following the instruction in the "Run OpenNet" section to start the simulation.  
OpenNet and corresponding tools can be found under "/home/nctuopennet/workspace".  

## (Option 2) Use install.sh

<pre>
./install.sh -a
</pre>

* Support
  * CentOS 7
  * Ubuntu 14.04.1
  * Fedora 21

## (Option 3) Build OpenNet on your own
### Prerequisite
1. Fedora 21 3.17.6-300.fc21.x86\_64 or Ubuntu 14.04.1 3.13.0-43-generic  
2. Fetch [Mininet 2.2.0] (https://github.com/mininet/mininet "Mininet")  
<pre>
$ git clone https://github.com/mininet/mininet.git
</pre>
3. Fetch [ns-3.21] (http://www.nsnam.org/ns-3-21 "ns-3.21")  
<pre>
$ curl -O -k https://www.nsnam.org/release/ns-allinone-3.21.tar.bz2
$ tar xf ns-allinone-3.21.tar.bz2
</pre>
4. Install packages for ns-3.21  
<pre>
Fedora:
$ sudo yum install gcc gcc-c++ python python-devel
$ sudo yum install make cmake glibc-devel.i686 glibc-devel.x86\_64
Ubuntu:
$ sudo apt-get install gcc g++ python python-dev
$ sudo apt-get install make cmake gcc-4.8-multilib g++-4.8-multilib
</pre>
5. Fetch and install [pygccxml] (http://sourceforge.net/projects/pygccxml/files/pygccxml/pygccxml-1.0/pygccxml-1.0.0.zip/download "pygccxml-1.0.0")  
<pre>
$ unzip pygccxml-1.0.0.zip
$ cd pygccxml-1.0.0
$ python setup.py build
$ sudo python setup.py install
</pre>
6. Install gccxml  
<pre>
$ git clone https://github.com/gccxml/gccxml.git
$ cd gccxml
$ mkdir gccxml-build
$ cd gccxml-build
$ cmake ../
$ make
$ sudo make install
$ sudo ln /usr/local/bin/gccxml /bin/gccxml
</pre>
7. Modify pygccxml parser configuration  
<pre>
Fedora:
$ sudo sed -e "s/gccxml\_path=''/gccxml\_path='\/usr\/local\/bin'/" -i /usr/lib/python2.7/site-packages/pygccxml/parser/config.py
Ubuntu:
$ sudo sed -e "s/gccxml\_path=''/gccxml\_path='\/usr\/local\/bin'/" -i /usr/local/lib/python2.7/dist-packages/pygccxml/parser/config.py
</pre>

### Install OpenNet
1. $mn: Directory of Mininet, $ns: Directory of ns-allinone-3.21, $on: Directory of OpenNet  
2. Install, patch and rebuild Mininet  
a. Install mininet  
<pre>
$ cd $mn
$ git checkout tags/2.2.0b3
$ sudo util/install.sh -fnpv
Fedora:
$ sudo sed -i 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/selinux/config
$ sudo systemctl stop firewalld.service
$ sudo systemctl disable firewalld.service
$ sudo setenforce 0
$ sudo systemctl enable openvswitch.service
$ sudo systemctl start openvswitch.service
</pre>
b. Add ns3.py into mininet  
<pre>
$ cp $on/mininet-patch/mininet/ns3.py $mn/mininet
</pre>
c. Replace mininet/node.py with the one in mininet-patch  
<pre>
$ cp $on/mininet-patch/mininet/node.py $mn/mininet
</pre>
d. Add WiFi roaming simulation script to example  
<pre>
$ cp $on/mininet-patch/examples/wifiroaming.py $mn/examples
</pre>
e. Rebuild Mininet  
<pre>
$ sudo util/install.sh -n
</pre>

3. Install, patch and Build ns-3  
a. Copy patches to the ns-3.21 folder  
<pre>
$ cd $ns/ns-3.21
`$ cp $on/ns3-patch/*.patch .`
</pre>
b. Apply patches  
<pre>
$ patch -p1 &lt; animation-interface.patch
$ patch -p1 &lt; netanim-python.patch
$ patch -p1 &lt; sta-wifi-scan.patch
</pre>
c. Patch the wscript for [issue] (https://www.nsnam.org/bugzilla/show_bug.cgi?id=1990) about using ns-3.21 with Ubuntu  
<pre>
$ sed -e "s/\['network'\]/\['internet', 'network', 'core'\]/" -i src/tap-bridge/wscript
</pre>
d. Configure ns-3  
<pre>
$ ./waf configure
Make sure
Python Bindings               : enabled
Python API Scanning Support   : enabled
</pre>
e. Scan python API  
<pre>
$ ./waf --apiscan=netanim
$ ./waf --apiscan=wifi
</pre>
f. Build ns-3  
<pre>
$ ./waf build
</pre>

## Run OpenNet
<pre>
Launch a controller at localhost:6633,
for example, a POX controller installed with Mininet can be running with:
$ sudo python pox.py forwarding.l2_learning

$ cd $ns/ns-3.21
$ sudo ./waf shell
$ cd $mn/examples
$ python wifiroaming.py
</pre>

## Reference
* Link modeling using ns-3 [Link] (https://github.com/mininet/mininet/wiki/Link-modeling-using-ns-3 "Link modeling using ns-3")
