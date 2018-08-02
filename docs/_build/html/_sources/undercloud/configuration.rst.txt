#############
Configuration
#############

.. contents:: Table of Contents

Undercloud installation & configuration
=======================================

Login to the Undercloud VM (from the Undercloud KVM host)
---------------------------------------------------------

   .. code:: bash

     ssh ${undercloud_ip}

Hostname configuration
----------------------

   .. code:: bash

      undercloud_name=`hostname -s`
      undercloud_suffix=`hostname -d`
      hostnamectl set-hostname ${undercloud_name}.${undercloud_suffix}
      hostnamectl set-hostname --transient ${undercloud_name}.${undercloud_suffix}

   .. note:: Get the undercloud ip and set the correct entries in /etc/hosts, ie (assuming the mgmt nic is eth0):

   .. code:: bash

      undercloud_ip=`ip addr sh dev eth0 |grep "inet " |awk '{print $2}' |awk -F"/" '{print $1}'`
      echo ${undercloud_ip} ${undercloud_name}.${undercloud_suffix} ${undercloud_name} >> /etc/hosts`

Setup repositories
------------------

   .. note::
      Repositoriy setup is different for CentOS and RHEL.

      .. admonition:: CentOS
         :class: centos

         ::

           tripeo_repos=`python -c 'import requests;r = requests.get("https://trunk.rdoproject.org/centos7-queens/current"); print r.text ' |grep python2-tripleo-repos|awk -F"href=\"" '{print $2}'|awk -F"\"" '{print $1}'`
           yum install -y https://trunk.rdoproject.org/centos7-queens/current/${tripeo_repos}
           tripleo-repos -b queens current

      .. admonition:: RHEL
         :class: rhel

         ::

           #Register with Satellite (can be done with CDN as well)
           satellite_fqdn=satellite.englab.juniper.net
           act_key=osp13
           org=Juniper
           yum localinstall -y http://${satellite_fqdn}/pub/katello-ca-consumer-latest.noarch.rpm
           subscription-manager register --activationkey=${act_key} --org=${org}


Install the Undercloud
----------------------

.. code:: bash

  yum install -y python-tripleoclient tmux
  su - stack
  cp /usr/share/instack-undercloud/undercloud.conf.sample ~/undercloud.conf
  openstack undercloud install
  source stackrc

Configure forwarding
--------------------

.. code:: bash

  sudo iptables -A FORWARD -i br-ctlplane -o eth0 -j ACCEPT
  sudo iptables -A FORWARD -i eth0 -o br-ctlplane -m state --state RELATED,ESTABLISHED -j ACCEPT
  sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

Configure nameserver for Overcloud nodes
----------------------------------------

.. code:: bash

  undercloud_nameserver=8.8.8.8
  openstack subnet set `openstack subnet show ctlplane-subnet -c id -f value` --dns-nameserver ${undercloud_nameserver}

Add external api interface
--------------------------

.. code:: bash

  sudo ip link add name vlan720 link br-ctlplane type vlan id 720
  sudo ip addr add 10.2.0.254/24 dev vlan720
  sudo ip link set dev vlan720 up

Add stack user to docker group
------------------------------

.. code:: bash

  newgrp docker
  exit
  su - stack
  source stackrc
