#!/bin/bash

# This script can help users to configure the /etc/hosts file
# Currently only support local installation

set -e
HOSTS_COMMENT='# The following lines are desirable for OpenNet'
FIRST_LOCAL_IP=`ifconfig | grep inet | awk 'NR==1 {gsub("addr:","",$2); print $2}'`

function LOCAL_INSTALL {
    echo >> /etc/hosts
    echo "$HOSTS_COMMENT" >> /etc/hosts
    echo "$FIRST_LOCAL_IP	master" >> /etc/hosts
}

if [ $# -eq 0 ]; then
    LOCAL_INSTALL
    exit
fi
