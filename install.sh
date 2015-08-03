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
MININET_VERSION='2.2.1'
NS3_VERSION='3.22'
PYGCCXML_VERSION='1.0.0'
NETANIM_VERSION='3.105'
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
        DEB_BUILD_OPTIONS='parallel=2 nocheck' fakeroot debian/rules binary
        dpkg -i $ROOT_PATH/openvswitch-switch_$OVS_VERSION*.deb $ROOT_PATH/openvswitch-common_$OVS_VERSION*.deb \
                $ROOT_PATH/openvswitch-pki_$OVS_VERSION*.deb
    fi

    if [ "$DIST" = "CentOS" ] || [ "$DIST" = "Fedora" ]; then
        mkdir -p $ROOT_PATH/rpmbuild/SOURCES/ && cd $ROOT_PATH/rpmbuild/SOURCES/
        wget http://openvswitch.org/releases/openvswitch-$OVS_VERSION.tar.gz
        tar zxvf openvswitch-$OVS_VERSION.tar.gz && cd openvswitch-$OVS_VERSION
        rpmbuild -bb --define "_topdir $ROOT_PATH/rpmbuild" --without check rhel/openvswitch.spec
        rpm -ivh --replacepkgs --replacefiles --nodeps $ROOT_PATH/rpmbuild/RPMS/x86_64/openvswitch*.rpm
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

    if [ "$DIST" = "Fedora" ] || [ "$DIST" = "CentOS" ]; then
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
    if [ ! -L /bin/gccxml ]; then
        ln -s /usr/local/bin/gccxml /bin/gccxml
    fi

}

function enviroment {

    echo "Prepare Enviroment"
    if [ "$DIST" = "Fedora" ] || [ "$DIST" = "CentOS" ]; then
        $install make git vim openssh openssh-server unzip curl gcc wget \
        gcc-c++ python python-devel cmake glibc-devel.i686 glibc-devel.x86_64 net-tools \
        make python-devel openssl-devel kernel-devel graphviz kernel-debug-devel \
        autoconf automake rpm-build redhat-rpm-config libtool \
        mercurial qt4 qt4-devel qt-devel qt-config

        SELINUX_STATUS="$(grep SELINUX=disabled /etc/selinux/config)"
        if [ $? -eq 1 ]; then
            sed -i 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/selinux/config
            setenforce 0
        fi
        systemctl stop firewalld.service
        systemctl disable firewalld.service
    fi
    if [ "$DIST" = "Ubuntu" ] ; then
        $install gcc g++ python python-dev make cmake gcc-4.8-multilib g++-4.8-multilib \
        python-setuptools unzip curl build-essential debhelper make autoconf automake \
        patch dpkg-dev libssl-dev libncurses5-dev libpcre3-dev graphviz python-all \
        python-qt4 python-zopeinterface python-twisted-conch uuid-runtime \
        qt4-dev-tools
    fi
    wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py -O - | python

}

function opennet {

    echo "Install OpenNet"
    cd $ROOT_PATH
    echo "Patch Mininet"
    cp $ROOT_PATH/mininet-patch/mininet/* $ROOT_PATH/mininet/mininet/
    cp -R $ROOT_PATH/mininet-patch/examples/* $ROOT_PATH/mininet/examples/
    cp -R $ROOT_PATH/mininet-patch/util/* $ROOT_PATH/mininet/util/
    cd $ROOT_PATH/mininet/mininet
    patch -p2 < node.patch
    patch -p2 < net.patch
    cd $ROOT_PATH/mininet/examples
    patch -p2 < whoami.patch
    cd $ROOT_PATH/mininet/util
    patch -p2 < clustersetup.patch

    #rebuild mininet
    $ROOT_PATH/mininet/util/install.sh -n

    echo "Patch NS3"
    cp $ROOT_PATH/ns3-patch/*.patch $ROOT_PATH/ns-allinone-$NS3_VERSION/ns-$NS3_VERSION
    cd $ROOT_PATH/ns-allinone-$NS3_VERSION/ns-$NS3_VERSION
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

function netanim {

    echo "Build NetAnim"
    cd $ROOT_PATH/ns-allinone-$NS3_VERSION/netanim-$NETANIM_VERSION
    qmake-qt4 NetAnim.pro
    make
}

function finish {

    echo "======================================================================="
    echo " OpenNet installation complete."
    echo " Before using OpenNet, you need to prepare SDN controller by yourself."
    echo "======================================================================="
    echo " Please try following commands to run the simulation"
    echo " \$ ./waf_shell.sh"
    echo " \$ cd $ROOT_PATH/mininet/examples/opennet"
    echo " \$ python wifiroaming.py"

}

function waf {

    WAF_SHELL=$ROOT_PATH/waf_shell.sh
    echo "#!/bin/sh" > $WAF_SHELL
    echo "cd $ROOT_PATH/ns-allinone-$NS3_VERSION/ns-$NS3_VERSION/" >> $WAF_SHELL
    echo "./waf shell" >> $WAF_SHELL
    chmod +x $WAF_SHELL

}

function all {

    detect_os
    enviroment
    pygccxml
    gccxml
    ns3
    netanim
    mininet
    openvswitch
    opennet
    waf
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


PARA='amdhenipgoswf'
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
        i)  netanim;;
        p)  pygccxml;;
        g)  gccxml;;
        o)  opennet;;
        s)  openvswitch;;
        w)  waf;;
        f)  finish;;
        esac
    done
    shift $(($OPTIND - 1))
fi

