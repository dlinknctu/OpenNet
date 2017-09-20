#!/bin/bash

set -e
OPENNET_PATH=$PWD
ANSIBLE_PATH=$OPENNET_PATH/ansible
SSHDIR=$HOME/.ssh
user=$(whoami)

function Install_Ansible {

    apt-get install python-setuptools
    easy_install pip
    cd ..
    git clone https://github.com/ansible/ansible.git
    cd ansible
    git checkout v2.3.2.0-1
    pip install -r ./requirements.txt
    source ./hacking/env-setup

}

function SSH_Config_Setup {

    if [ ! -d $SSHDIR ]; then
        mkdir -p $SSHDIR
    fi
    if [ ! -f $SSHDIR/cluster_key.pub ]; then
        echo "***creating key pair"
        ssh-keygen -t rsa -C "Cluster_Edition_Key" -f $SSHDIR/cluster_key -N '' &> /dev/null
        cat $SSHDIR/cluster_key.pub >> $SSHDIR/authorized_keys
    fi
    if [ ! -f $SSHDIR/config ]; then
        echo "***configuring host"
        echo "IdentityFile $SSHDIR/cluster_key" >> $SSHDIR/config
        echo "IdentityFile $SSHDIR/id_rsa" >> $SSHDIR/config
    fi
    for host in $hosts; do
        echo "***copying public key to $host"
        ssh-keyscan -H $host >> $SSHDIR/known_hosts
        ssh-copy-id -i $SSHDIR/cluster_key.pub $user@$host &> /dev/null
        echo "***copying key pair to remote host"
        scp $SSHDIR/{cluster_key,cluster_key.pub,config} $user@$host:$SSHDIR
    done

    for host in $hosts; do
        echo "***copying known_hosts to $host"
        scp $SSHDIR/known_hosts $user@$host:$SSHDIR/cluster_known_hosts
        ssh $user@$host "
            cat $SSHDIR/cluster_known_hosts >> $SSHDIR/known_hosts
            rm $SSHDIR/cluster_known_hosts"
    done

}

function SSH_Daemon_Setup {

    if ! grep -q "Mininet Cluster Edition" /etc/ssh/sshd_config; then
        echo "***Setting /etc/ssh/sshd_config"
        echo -e "# Start Mininet Cluster Edition settings #" \
                "\nUseDNS no" \
                "\nPermitTunnel yes" \
                "\nMaxSessions 1024" \
                "\nAllowTcpForwarding yes" \
                "\n# End Mininet Cluster Edition settings #" >> /etc/ssh/sshd_config

        for host in $hosts; do
            echo "***copying sshd_config to $host"
            scp /etc/ssh/sshd_config $user@$host:$SSHDIR
            ssh $user@$host "
                sudo cp $SSHDIR/sshd_config /etc/ssh/sshd_config
                sudo rm -f $SSHDIR/sshd_config
                sudo service ssh restart"
        done
    fi

}

function Test_Network {

    cd $ANSIBLE_PATH
    ansible -m ping all

}

function Install_OpenNet {

    cd $ANSIBLE_PATH
    sed -e "s|home_location: \"*.*\"|home_location: \"$OPENNET_PATH\"|" -i group_vars/all
    ansible-playbook playbook.yml

}

if [ $# -eq 0 ]; then
    echo "examples: install.sh [master hostname] [slave1 hostname] [slave2 hostname]"
    exit
fi

echo "***Check hostname in /etc/hosts"
for i in "$@"; do
    HOST_STATUS=$(cat /etc/hosts | grep -w $i | awk '{print $2}')
    if [[ -z $HOST_STATUS ]]; then
        echo "Can Not find hostname '$i' in /etc/hosts, please check."
        echo "The format should be like:"
        echo "10.0.0.1 master"
        echo "10.0.0.2 slave1"
        echo "10.0.0.3 slave2"
        exit
    fi
    hosts+="$i "
done
echo

echo "***Check hostname in ansible/hosts"
for host in $hosts; do
    HOST_STATUS=$(cat ansible/hosts | grep -v "\[opennet-master\]" | grep -v "\[opennet-slave\]" | grep -w $host| grep -v "#" | awk '{print $1}')
    if [ -z $HOST_STATUS ]; then
        echo "Can NOT find hostname '$host' in ansible/hosts, please check."
        echo "Please append hostname '$host' in [opennet-master] or [opennet-slave] sections"
        exit
    fi
done
echo

echo "***Ready authenticating to:"
for host in $hosts; do
    echo "$host "
done

Install_Ansible
SSH_Config_Setup
SSH_Daemon_Setup
Test_Network
Install_OpenNet
cat $OPENNET_PATH/opennet_help.txt
rm $OPENNET_PATH/opennet_help.txt
