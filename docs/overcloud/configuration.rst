#############
Configuration
#############

.. contents:: Table of Contents

Undercloud preparation
======================

1. Login to the Undercloud VM (from the Undercloud KVM host)

   .. code:: bash

     ssh ${undercloud_ip}

2. Hostname configuration

   .. code:: bash

      undercloud_name=`hostname -s`
      undercloud_suffix=`hostname -d`
      hostnamectl set-hostname ${undercloud_name}.${undercloud_suffix}
      hostnamectl set-hostname --transient ${undercloud_name}.${undercloud_suffix}

   .. note:: Get the undercloud ip and set the correct entries in /etc/hosts, ie (assuming the mgmt nic is eth0):

   .. code:: bash

      undercloud_ip=`ip addr sh dev eth0 |grep "inet " |awk '{print $2}' |awk -F"/" '{print $1}'`
      echo ${undercloud_ip} ${undercloud_name}.${undercloud_suffix} ${undercloud_name} >> /etc/hosts`
