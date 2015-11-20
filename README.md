OpenNet
=======
A simulator built on top of Mininet and ns-3 for Software-Defined Wireless Local Area Network (SDWLAN)  
http://www.slideshare.net/rascov/20140824-open-net

Feature
-------
* Complement ns-3 by supporting channel scan behavior on Wi-Fi station (sta-wifi-scan.patch)
* Show CsmaLink and SimpleLink in NetAnim (animation-interface.patch)
* Fix runtime error when access PacketMetadata of CsmaLink, [Submitted] (https://www.nsnam.org/bugzilla/show_bug.cgi?id=1787, "ns-3 bugzilla issue 1787")

Build OpenNet on your own - Use install.sh
------------------------------------------
Supports Ubuntu 14.04.3  

    $ sudo su -
    # apt-get install git ssh
    # git clone https://github.com/dlinknctu/OpenNet.git
    # cd OpenNet
    # ./configure.sh
    # ./install.sh master

After a successful installation, the script will show "OpenNet installation complete."  

Run OpenNet
-----------
Before using OpenNet, you need to prepare SDN controller by yourself.  
Please try following commands to run the simulation:  

    $ sudo su -
    # cd OpenNet
    # ./waf_shell.sh
    # cd ../../mininet/examples/opennet
    # python wifiroaming.py

Do not type "sudo python wifiroaming.py", sudo will affect the environment  
variable required by simulation.  

If the simulation script cannot connect to the controller,  
stop the network-manager may help.  

    # service network-manager stop

Start the network-manager service after the simulation.  

    # service network-manager start

Run NetAnim
-----------
Use NetAnim to open the XML file in the directory /tmp/xml.  
Click "Play Animation" button can start the animation.  

    $ sudo su -
    # cd OpenNet/ns-allinone-$NS3_VERSION/netanim-$NETANIM_VERSION
    # ./NetAnim

Reference
---------
* Link modeling using ns-3, [Link] (https://github.com/mininet/mininet/wiki/Link-modeling-using-ns-3 "Link modeling using ns-3")

