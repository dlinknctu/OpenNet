#!/bin/bash

set -e
OPENNET_PATH=$PWD
ANSIBLE_PATH=$OPENNET_PATH/ansible
USERDIR=$HOME/.ssh
user=$(whoami)

function Install_Ansible {

    apt-get update
    apt-get install -y software-properties-common
    apt-add-repository -y ppa:ansible/ansible
    apt-get update
    apt-get install -y ansible

}


function SSH_Config_Setup {

    if [ ! -f $USERDIR/cluster_key.pub ]; then
        echo "***creating key pair"
        ssh-keygen -t rsa -C "Cluster_Edition_Key" -f $USERDIR/cluster_key -N '' &> /dev/null
        cat $USERDIR/cluster_key.pub >> $USERDIR/authorized_keys
    fi
    if [ ! -f $USERDIR/config ]; then
        echo "***configuring host"
        echo "IdentityFile $USERDIR/cluster_key" >> $USERDIR/config
        echo "IdentityFile $USERDIR/id_rsa" >> $USERDIR/config
    fi
    for host in $hosts; do
        echo "***copying public key to $host"
        ssh-keyscan -H $host >> ~/.ssh/known_hosts
        ssh-copy-id -i $USERDIR/cluster_key.pub $user@$host &> /dev/null
        echo "***copying key pair to remote host"
        scp $USERDIR/{cluster_key,cluster_key.pub,config} $user@$host:$USERDIR
    done

    for host in $hosts; do
        echo "***copying known_hosts to $host"
        scp $USERDIR/known_hosts $user@$host:$USERDIR/cluster_known_hosts
        ssh $user@$host "
            cat $USERDIR/cluster_known_hosts >> $USERDIR/known_hosts
            rm $USERDIR/cluster_known_hosts"
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
            scp /etc/ssh/sshd_config $user@$host:$USERDIR
            ssh $user@$host "
                sudo cp $USERDIR/sshd_config /etc/ssh/sshd_config
                sudo rm -f $USERDIR/sshd_config
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
    echo "home_location: \"$OPENNET_PATH\"\n" >> group_vars/all
    ansible-playbook playbook.yml

}

if [ $# -eq 0 ]; then
    echo "examples: install.sh [master hostname] [slave1 hostname] [slave2 hostname]"
    exit
fi

echo "***Check hostname in /etc/hosts"
for i in "$@"; do
    HOST_STATUS=$(cat /etc/hosts | grep -w $i | awk '{print $2}')
    if [ -z $HOST_STATUS ]; then
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
