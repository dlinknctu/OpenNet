#!/bin/bash

set -o nounset
set -e
set -x

ROOT_PATH=`pwd`
OVS_RELEASE='2.3.1'
MININET_VERSION='2.2.0'
DIST=Unknown
RELEASE=Unknown
CODENAME=Unknown

function detect_os {

    test -e /etc/fedora-release && DIST="Fedora"
    test -e /etc/centos-release && DIST="CentOS"
    if [ "$DIST" = "Fedora" ] || [ "$DIST" = "CentOS" ]; then
        install='sudo yum -y install'
        remove='sudo yum -y erase'
        pkginst='sudo rpm -ivh'
        # Prereqs for this script
        if ! which lsb_release &> /dev/null; then
            $install redhat-lsb-core
        fi
    fi
    if which lsb_release &> /dev/null; then
        DIST=`lsb_release -is`
        RELEASE=`lsb_release -rs`
        CODENAME=`lsb_release -cs`
    fi
    echo "Detected Linux distribution: $DIST $RELEASE $CODENAME"
}

function mininet {
    echo "Fetch Mininet"
    cd $ROOT_PATH
    if [ ! -d mininet ]; then
        git clone https://github.com/mininet/mininet.git
    fi

    cp mininet-patch/util/install.sh mininet/util/
    cd $ROOT_PATH/mininet && git checkout tags/$MININET_VERSION

    ./util/install.sh -fn
    mkdir -p $ROOT_PATH/rpmbuild/SOURCES/ && cd $ROOT_PATH/rpmbuild/SOURCES/
    wget http://openvswitch.org/releases/openvswitch-$OVS_RELEASE.tar.gz
    tar zxvf openvswitch-$OVS_RELEASE.tar.gz && cd openvswitch-$OVS_RELEASE
    rpmbuild -bb --define "_topdir $ROOT_PATH/rpmbuild" --without check rhel/openvswitch.spec
    rpm -ivh --nodeps $ROOT_PATH/rpmbuild/RPMS/x86_64/openvswitch*.rpm
    /etc/init.d/openvswitch start
}

function ns3 {

    echo "Fetch ns-3.21"
    cd $ROOT_PATH
    if [ ! -f ns-allinone-3.21.tar.bz2 ]; then
        curl -O -k https://www.nsnam.org/release/ns-allinone-3.21.tar.bz2
    fi
    tar xf ns-allinone-3.21.tar.bz2

}

function pygccxml {

    echo "Fetch and install pygccxml"
    cd $ROOT_PATH
    if [ ! -f pygccxml-1.0.0.zip ]; then
        wget http://nchc.dl.sourceforge.net/project/pygccxml/pygccxml/pygccxml-1.0/pygccxml-1.0.0.zip
    fi
    unzip -o pygccxml-1.0.0.zip && cd $ROOT_PATH/pygccxml-1.0.0
    python setup.py install

    if [ "$DIST" = "CentOS" ]; then
        sed -e "s/gccxml\_path=''/gccxml\_path='\/usr\/local\/bin'/" -i /usr/lib/python2.7/site-packages/pygccxml/parser/config.py
    fi

}

function gccxml {

    echo "Install gccxml"
    cd $ROOT_PATH
    if [ ! -d gccxml ]; then
        git clone https://github.com/gccxml/gccxml.git
    fi
    cd gccxml
    mkdir -p gccxml-build && cd gccxml-build
    cmake ../
    make
    make install
    ln -s /usr/local/bin/gccxml /bin/gccxml

}

function enviroment {

    echo "Prepare Enviroment"
    yum update
    yum install -y make git vim ssh unzip curl gcc wget \
    gcc-c++ python python-devel cmake glibc-devel.i686 glibc-devel.x86_64 net-tools \
    make python-devel openssl-devel kernel-devel graphviz kernel-debug-devel autoconf \
    automake rpm-build redhat-rpm-config libtool 

    sed -i 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/selinux/config
    systemctl stop firewalld.service
    systemctl disable firewalld.service
    setenforce 0

}

function opennet {

    echo "Install OpenNet"
    cd $ROOT_PATH
    cp mininet-patch/mininet/ns3.py mininet/mininet/
    cp mininet-patch/mininet/node.py mininet/mininet/
    cp mininet-patch/examples/wifiroaming.py mininet/examples/

    #rebuild mininet
    $ROOT_PATH/mininet/util/install.sh -n

    #patch
    cp $ROOT_PATH/ns3-patch/*.patch $ROOT_PATH/ns-allinone-3.21/ns-3.21
    cd $ROOT_PATH/ns-allinone-3.21/ns-3.21
    patch -p1 < animation-interface.patch
    patch -p1 < netanim-python.patch
    patch -p1 < sta-wifi-scan.patch

    ./waf configure
    ./waf --apiscan=netanim
    ./waf --apiscan=wifi
    ./waf build

}
function finish {

    echo "\$ sudo $ROOT_PATH/ns-allinone/ns-3.21/waf shell"
    echo "\$ cd $ROOT_PATH/mininet/examples"
    echo "\$ python wifiroaming.py"

}

function all {
    detect_os
    enviroment
    pygccxml
    gccxml
    ns3
    mininet
    opennet
    finish
}


function usage {
    echo
    echo Usage: $(basename $0) -[$PARA] >&2
    echo
    exit 2
}


PARA='amdhenpgo'
if [ $# -eq 0 ]
then
    usage
else
    while getopts $PARA OPTION
    do
        case $OPTION in
        a)  all;;
        m)  mininet;;
        d)  detect_os;;
        h)  usage;;
        e)  enviroment;;
        n)  ns3;;
        p)  pygccxml;;
        g)  gccxml;;
        o)  opennet;;
        esac
    done
    shift $(($OPTIND - 1))
fi

