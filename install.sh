#!/bin/bash
#==============================================================================
#title           : install.sh
#description     : This script will install OpenNet
#                  Support Ubuntu 14.04.1, CentOS 7, Fedora 21
#==============================================================================

set -o nounset
set -e

ROOT_PATH=`pwd`
OVS_VERSION='2.3.1'
MININET_VERSION='2.2.0'
NS3_VERSION='3.21'
PYGCCXML_VERSION='1.0.0'
DIST=Unknown
RELEASE=Unknown
CODENAME=Unknown

function detect_os {

    test -e /etc/fedora-release && DIST="Fedora"
    test -e /etc/centos-release && DIST="CentOS"
    if [ "$DIST" = "Fedora" ] || [ "$DIST" = "CentOS" ]; then
        install='yum -y install'
        remove='yum -y erase'
        pkginst='rpm -ivh'
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

    grep Ubuntu /etc/lsb-release &> /dev/null && DIST="Ubuntu"
    if [ "$DIST" = "Ubuntu" ] ; then
        install='apt-get -y install'
        remove='apt-get -y remove'
        pkginst='dpkg -i'
        # Prereqs for this script
        if ! which lsb_release &> /dev/null; then
            $install lsb-release
        fi
    fi
    echo "Detected Linux distribution: $DIST $RELEASE $CODENAME"

}

function mininet {

    echo "Fetch Mininet"
    cd $ROOT_PATH
    if [ ! -d mininet ]; then
        git clone https://github.com/mininet/mininet.git
    fi

    cd $ROOT_PATH/mininet && git checkout tags/$MININET_VERSION
    cp $ROOT_PATH/mininet-patch/util/install.sh $ROOT_PATH/mininet/util/
    ./util/install.sh -fn

}

function openvswitch {

    cd $ROOT_PATH
    if [ "$DIST" = "Ubuntu" ]; then
        wget http://openvswitch.org/releases/openvswitch-$OVS_VERSION.tar.gz
        tar zxvf openvswitch-$OVS_VERSION.tar.gz && cd openvswitch-$OVS_VERSION
        #TODO Need to integrate *deb
        dpkg-checkbuilddeps
        fakeroot debian/rules binary
        dpkg -i $ROOT_PATH/openvswitch-switch_$OVS_VERSION-1_amd64.deb $ROOT_PATH/openvswitch-common_$OVS_VERSION-1_amd64.deb
    fi

    if [ "$DIST" = "CentOS" ] || [ "$DIST" = "Fedora" ]; then
        mkdir -p $ROOT_PATH/rpmbuild/SOURCES/ && cd $ROOT_PATH/rpmbuild/SOURCES/
        wget http://openvswitch.org/releases/openvswitch-$OVS_VERSION.tar.gz
        tar zxvf openvswitch-$OVS_VERSION.tar.gz && cd openvswitch-$OVS_VERSION
        rpmbuild -bb --define "_topdir $ROOT_PATH/rpmbuild" --without check rhel/openvswitch.spec
        rpm -ivh --nodeps $ROOT_PATH/rpmbuild/RPMS/x86_64/openvswitch*.rpm
        /etc/init.d/openvswitch start
    fi

}

function ns3 {

    echo "Fetch ns-$NS3_VERSION"
    cd $ROOT_PATH
    if [ ! -f ns-allinone-$NS3_VERSION.tar.bz2 ]; then
        curl -O -k https://www.nsnam.org/release/ns-allinone-$NS3_VERSION.tar.bz2
    fi
    tar xf ns-allinone-$NS3_VERSION.tar.bz2

}

function pygccxml {

    echo "Fetch and install pygccxml"
    cd $ROOT_PATH
    if [ ! -f pygccxml-$PYGCCXML_VERSION.zip ]; then
        wget http://nchc.dl.sourceforge.net/project/pygccxml/pygccxml/pygccxml-1.0/pygccxml-$PYGCCXML_VERSION.zip
    fi
    unzip -o pygccxml-$PYGCCXML_VERSION.zip && cd $ROOT_PATH/pygccxml-$PYGCCXML_VERSION
    python setup.py install

    if [ "$DIST" = "CentOS" ]; then
        sed -e "s/gccxml\_path=''/gccxml\_path='\/usr\/local\/bin'/" -i /usr/lib/python2.7/site-packages/pygccxml/parser/config.py
    fi

    if [ "$DIST" = "Ubuntu" ]; then
        sed -e "s/gccxml_path=''/gccxml_path='\/usr\/local\/bin'/" -i /usr/local/lib/python2.7/dist-packages/pygccxml/parser/config.py
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
    if [ "$DIST" = "Fedora" ] || [ "$DIST" = "CentOS" ]; then
        $install make git vim ssh unzip curl gcc wget \
        gcc-c++ python python-devel cmake glibc-devel.i686 glibc-devel.x86_64 net-tools \
        make python-devel openssl-devel kernel-devel graphviz kernel-debug-devel \
        autoconf automake rpm-build redhat-rpm-config libtool

        sed -i 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/selinux/config
        systemctl stop firewalld.service
        systemctl disable firewalld.service
        setenforce 0
    fi
    if [ "$DIST" = "Ubuntu" ] ; then
        $install gcc g++ python python-dev make cmake gcc-4.8-multilib g++-4.8-multilib \
        python-setuptools unzip curl build-essential debhelper make autoconf automake \
        patch dpkg-dev libssl-dev libncurses5-dev libpcre3-dev graphviz python-all \
        python-qt4 python-zopeinterface python-twisted-conch
    fi
    wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py -O - | python

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

    if [ "$DIST" = "Ubuntu" ]; then
        sed -e "s/\['network'\]/\['internet', 'network', 'core'\]/" -i src/tap-bridge/wscript
    fi

    ./waf configure
    ./waf --apiscan=netanim
    ./waf --apiscan=wifi
    ./waf build

}
function finish {

    echo " OpenNet installation complete."
    echo " Please try following commands to run the simulation/"
    echo " \$ cd $ROOT_PATH/ns-allinone-3.21/ns-3.21/"
    echo " \$ ./waf shell"
    echo " \$ cd $ROOT_PATH/mininet/examples"
    echo " \$ python wifiroaming.py"

}

function all {

    detect_os
    enviroment
    pygccxml
    gccxml
    ns3
    mininet
    openvswitch
    opennet
    finish

}


function usage {

    echo
    echo Usage: $(basename $0) -[$PARA] >&2
    echo "-a: Install OpenNet World"
    echo "-f: Finish message"
    echo
    exit 2

}


PARA='amdhenpgosf'
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
        s)  openvswitch;;
        f)  finish;;
        esac
    done
    shift $(($OPTIND - 1))
fi

