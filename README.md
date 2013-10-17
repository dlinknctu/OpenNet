OpenNet
=======
A Simulator for Software-Defined Wireless Local Area Network

Feature
-------
* Support channel scan behavior on Wi-Fi station
> sta-wifi-scan.patch
* Show CsmaLink and SimpleLink in NetAnim
> animation-interface.patch

Bugfix
------
* Simulator crashes when access PacketMetadata of CsmaLink
> packet-metadata.patch

Prerequisite
------------
* Linux OS (with curl and python)

Installation
------------
The following installer will fetch, patch and build ns-3

	curl https://raw.github.com/dlinknctu/OpenNet/dev/install.py | python
