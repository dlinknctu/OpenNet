# OpenNet Tutorial

This tutorial describes features, background knowledge, and design of OpenNet.

*The tutorial assumes all commands is under root privilege.*

## Part 1. Basic of OpenNet Development

OpenNet is an SDN emulator which integrates Mininet and NS-3. But Mininet is based on Python, while NS-3 is written in C++, how to make them work together? Fortunately, NS-3 supports Python binding, NS-3 model libraries can be imported as Python modules. Based on this fundamental, OpenNet provides interfaces to let Mininet emulation scripts can use NS-3 models easily.  

Development of OpenNet has two aspects: Mininet and NS-3. Mininet is responsible for emulating OpenFlow switches, construct environment, and providing CLI. NS-3 is responsible for emulating models which Mininet does not have.  

### OpenNet Directories

- ansible: Automate deployment tool, used to install OpenNet
- doc: Documents
- mininet: Customized version of mininet, cloned from dlinknctu/mininet
- ns3-patch: NS-3 patch files
- ns-allinone-3.xx: Directory of NS-3

### Apply modification of Mininet or NS-3

Mininet:
```shell
./mininet/util/install.sh -n
```

NS-3:
```shell
cd ns-allinone-3.xx/ns-3.xx/
./waf build
./waf install
```

### Notable Directories and Files

- mininet/examples/opennet: Directory which contains example scripts of OpenNet
- mininet/bin/opennet-agent.py: A Python daemon, used to construct distributed NS-3 emulation environment
- mininet/mininet/lte.py: Interface of (distributed) LTE emulation
- mininet/mininet/wifi.py: Interface of distributed Wi-Fi emulation
- mininet/mininet/ns3.py: Interface of Wi-Fi emulation
- mininet/mininet/opennet.py: Utilities about NetAnim and pcap

## Part 2. Background Knowledge

### Mininet Cluster

Mininet can construct SDN emulation via OpenFlow switch utilities, Linux network utilities, and Linux system call. These construct instructions also can be dispatched to multiple physical hosts via SSH, in order to create large scale SDN emulation environment.  

If cross-host link exists, Mininet cluster will create respective tunnel to keep connectivity of topology.  

### Linux TUN/TAP

Linux TUN/TAP is software-based network interface card, provides packet RX/TX interfaces without physical medium. TUN works with IP frames. TAP works with Ethernet frames.  

### NS-3 Emulation

In simulation mode, NS-3 simulate virtual network in user-space process, Linux host can not interact with the isolated virtual network. But in emulation mode, there are two modules allow Linux host to interact with NS-3: TapBridge and FdNetDevice.  

TapBridge is an NS-3 bridge connects NS-3 NetDevice and Linux TAP, let packets from Linux host can be forwarded to NS-3 Channel. TapBridge uses file descriptor (FD) as junction of Linux host and NS-3.  

FdNetDevice is an NS-3 NetDevice which does not connect to NS-3 Channel. Instead, FdNetDevice connects to Linux TAP via corresponding FD and lets packets from NS-3 APP can be forwarded to Linux host. FdNetDevice can be considered as combination of NetDevice and TapBridge, because it not only can let NS-3 APP receive and transmit packets but also have an FD of Linux TAP as junction of Linux and NS-3.  

### VT-Mininet

Mininet can’t guarantee performance fidelity under high workload, particular when exceed capability of available CPU cores.  

VT-Mininet use virtual time system to trade time with CPU resource. VT-Mininet can create Linux namespace which use virtual time system and make system call returns virtual time instead of system time. Ratio btw real time and virtual time is called TDF (Time Dilation Factor). When TDF = 100, every 100 real second equals to 1 virtual second.  

## Part 3. Advanced Features

### Distributed Emulation of Mininet

OpenNet can distributes emulation among multiple physical hosts, each physical host handles a small set of topologies. Since dispatching of Mininet entities is achieved with SSH, distributed emulation feature requires that user should setup SSH authentication before use this feature.

Set new password for root (on each physical host):
```shell
passwd
```

Enable root login with password (on each physical host):
```shell
passwd -u root
sed -e "s/PermitRootLogin without-password/PermitRootLogin yes/" -i /etc/ssh/sshd_config
service ssh restart
```

Setup mapping between hostname and IP address in /etc/hosts (on master host):
```shell
vim /etc/hosts
```

Setup SSH authentication (on master host), 192.168.1.1 should be replaced to corresponging IP address:
```shell
./mininet/util/clustersetup.sh -p master 192.168.1.1
```

Disable root login with password (on each physical host):
```shell
passwd -l root
sed -e "s/PermitRootLogin yes/PermitRootLogin without-password/" -i /etc/ssh/sshd_config
service ssh restart
```

### Distributed Emulation of NS-3

Distributed emulation of NS-3 is achieved with OpenNet agent. OpenNet agent is a Python daemon which includes a TCP server, the TCP server makes OpenNet agent can accept connection and spawn a process to receive dispatch commands. Since dispatch commands are in format of Python code, the process can compile dispatch commands and execute commands.

### Time Dilation Mechanism

Frequency of SIB transmission is very high in LTE emulation, an ordinary x86 CPU core can not afford such emulation workload. Emulation scenario with 2 eNodeBs will utilize 100% CPU usage. Time dilation mechanism can trade time with CPU resource, so OpenNet adopt time dilation mechanism to improve performance. OpenNet uses TDF to adjust ratio btw real time and virtual time, user can specify TDF in OpenNet UDN emulation script.  

Time dilation mechanism in OpenNet has three parts:

* Virtual time in Mininet namespaces
  Make system call returns virtual time instead of system time.
  
* Network delay on virtual interfaces
  Use Linux traffic control to add network delay and slowdown interfaces.
  
* Virtual time in NS-3 LTE
  Make scheduling in NS-3 LTE uses virtual time.

"Virtual time in Mininet namespaces" requires kernel patch:
```shell
git clone https://github.com/kansokusha/VirtualTimeForMininet
cd VirtualTimeForMininet
./install -a
sed -e "s/GRUB_DEFAULT=0/GRUB_DEFAULT=\"Advanced options for Ubuntu>Ubuntu, with Linux 3.16.3\"/" -i /etc/default/grub
update-grub
```
