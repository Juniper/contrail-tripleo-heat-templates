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

3. Setup repositories

   .. note::
      Repositoriy setup is different for CentOS and RHEL.

      .. admonition:: CentOS
         :class: centos

         ::

           tripeo_repos=`python -c 'import requests;r = requests.get("https://trunk.rdoproject.org/centos7-queens/current"); print r.text ' |grep
           python2-tripleo-repos|awk -F"href=\"" '{print $2}'|awk -F"\"" '{print $1}'`
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

Undercloud installation & configuration
=======================================

1. install the Undercloud

.. code:: bash

  yum install -y python-tripleoclient tmux
  su - stack
  cp /usr/share/instack-undercloud/undercloud.conf.sample ~/undercloud.conf
  openstack undercloud install
  source stackrc

2. configure forwarding

.. code:: bash

  sudo iptables -A FORWARD -i br-ctlplane -o eth0 -j ACCEPT
  sudo iptables -A FORWARD -i eth0 -o br-ctlplane -m state --state RELATED,ESTABLISHED -j ACCEPT
  sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

3. Configure nameserver for Overcloud nodes

.. code::bash

  undercloud_nameserver=8.8.8.8
  openstack subnet set `openstack subnet show ctlplane-subnet -c id -f value` --dns-nameserver ${undercloud_nameserver}

4. Add external api interface

.. code::bash

  sudo ip link add name vlan720 link br-ctlplane type vlan id 720
  sudo ip addr add 10.2.0.254/24 dev vlan720
  sudo ip link set dev vlan720 up

Overcloud image preparation
===========================

1. Create image directory

.. code::bash

  mkdir images
  cd images

2. Get images

   .. note::

            .. admonition:: tripleo
                     :class: tripleo

                           ::

                             curl -O https://images.rdoproject.org/queens/rdo_trunk/current-tripleo-rdo/ironic-python-agent.tar
                             curl -O https://images.rdoproject.org/queens/rdo_trunk/current-tripleo-rdo/overcloud-full.tar
                             tar xvf ironic-python-agent.tar
                             tar xvf overcloud-full.tar

            .. admonition:: OSP13
                     :class: OSP13

                           ::
                          
                             sudo yum install -y rhosp-director-images rhosp-director-images-ipa
                             for i in /usr/share/rhosp-director-images/overcloud-full-latest-13.0.tar /usr/share/rhosp-director-images/ironic-python-agent-latest-13.0.tar ; do tar -xvf $i; done

3. Upload images

.. code::bash

  cd
  openstack overcloud image upload --image-path /home/stack/images/
