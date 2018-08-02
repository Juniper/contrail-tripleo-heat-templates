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

.. code:: bash

  undercloud_nameserver=8.8.8.8
  openstack subnet set `openstack subnet show ctlplane-subnet -c id -f value` --dns-nameserver ${undercloud_nameserver}

4. Add external api interface

.. code:: bash

  sudo ip link add name vlan720 link br-ctlplane type vlan id 720
  sudo ip addr add 10.2.0.254/24 dev vlan720
  sudo ip link set dev vlan720 up

Overcloud image preparation
===========================

1. Create image directory

.. code:: bash

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

.. code:: bash

  cd
  openstack overcloud image upload --image-path /home/stack/images/

Ironic perparation
==================

1. Get the ironic_list files from the three Overcloud KVM hosts and combine it

2. Add the Overcloud VMs to Ironic

.. code:: bash

  ipmi_password=ADMIN
  ipmi_user=ADMIN
  while IFS= read -r line; do
    mac=`echo $line|awk '{print $1}'`
    name=`echo $line|awk '{print $2}'`
    kvm_ip=`echo $line|awk '{print $3}'`
    profile=`echo $line|awk '{print $4}'`
    ipmi_port=`echo $line|awk '{print $5}'`
    uuid=`openstack baremetal node create --driver ipmi \
                                          --property cpus=4 \
                                          --property memory_mb=16348 \
                                          --property local_gb=100 \
                                          --property cpu_arch=x86_64 \
                                          --driver-info ipmi_username=${ipmi_user}  \
                                          --driver-info ipmi_address=${kvm_ip} \
                                          --driver-info ipmi_password=${ipmi_password} \
                                          --driver-info ipmi_port=${ipmi_port} \
                                          --name=${name} \
                                          --property capabilities=profile:${profile},boot_option:local \
                                          -c uuid -f value`
    openstack baremetal port create --node ${uuid} ${mac}
  done < <(cat ironic_list)
  
  DEPLOY_KERNEL=$(openstack image show bm-deploy-kernel -f value -c id)
  DEPLOY_RAMDISK=$(openstack image show bm-deploy-ramdisk -f value -c id)
  
  for i in `openstack baremetal node list -c UUID -f value`; do
    openstack baremetal node set $i --driver-info deploy_kernel=$DEPLOY_KERNEL --driver-info deploy_ramdisk=$DEPLOY_RAMDISK
  done
  
  for i in `openstack baremetal node list -c UUID -f value`; do
    openstack baremetal node show $i -c properties -f value
  done

3. Overcloud node introspection

.. code:: bash

  for node in $(openstack baremetal node list -c UUID -f value) ; do
    openstack baremetal node manage $node
  done
  openstack overcloud node introspect --all-manageable --provide

Flavor creation
===============

.. code:: bash

  for i in compute-dpdk \
  compute-sriov \
  contrail-controller \
  contrail-analytics \
  contrail-database \
  contrail-analytics-database; do
    openstack flavor create $i --ram 4096 --vcpus 1 --disk 40
    openstack flavor set --property "capabilities:boot_option"="local" \
                         --property "capabilities:profile"="${i}" ${i}
  done

Create Tripleo-Heat-Template copy
=================================

.. code:: bash

  cp -r /usr/share/openstack-tripleo-heat-templates/ tripleo-heat-templates
  git clone https://github.com/juniper/contrail-tripleo-heat-templates -b stable/queens
  cp -r contrail-tripleo-heat-templates/* tripleo-heat-templates/

Add stack user to docker group
==============================

.. code:: bash

  newgrp docker
  exit
  su - stack
  source stackrc

Get and upload containers
=========================

1. Create OpenStack container file

   .. note::

            .. admonition:: tripleo
                     :class: tripleo

                           ::

                             openstack overcloud container image prepare \
                               --namespace docker.io/tripleoqueens \
                               --tag current-tripleo \
                               --tag-from-label rdo_version \
                               --output-env-file=~/overcloud_images.yaml

                             tag=`grep "docker.io/tripleoqueens" docker_registry.yaml |tail -1 |awk -F":" '{print $3}'`

                             openstack overcloud container image prepare \
                               --namespace docker.io/tripleoqueens \
                               --tag ${tag} \
                               --push-destination 192.168.24.1:8787 \
                               --output-env-file=~/overcloud_images.yaml \
                               --output-images-file=~/local_registry_images.yaml

            .. admonition:: OSP13
                     :class: osp13

                           ::

                             openstack overcloud container image prepare \
                              --push-destination=192.168.24.1:8787  \
                              --tag-from-label {version}-{release} \
                              --output-images-file ~/local_registry_images.yaml  \
                              --namespace=registry.access.redhat.com/rhosp13  \
                              --prefix=openstack-  \
                              --tag-from-label {version}-{release}  \
                              --output-env-file ~/overcloud_images.yaml

2. Upload OpenStack containers

.. code:: bash

  openstack overcloud container image upload --config-file ~/local_registry_images.yaml

3. Create Contrail container file

.. note:: this step is optional. If not done, Contrail containers can be downloaded from external registries.

.. code:: bash

  cd ~/tripleo-heat-templates/tools/contrail
  ./import_contrail_container.sh -f container_outputfile -r registry -t tag [-i insecure] [-u username] [-p password] [-c certificate pat
h]

.. note:: Examples:

         code:: bash
           # Pull from password protectet public registry:
          ./import_contrail_container.sh -f /tmp/contrail_container -r hub.juniper.net/contrail -u USERNAME -p PASSWORD -t 1234

          # Pull from dockerhub:
          ./import_contrail_container.sh -f /tmp/contrail_container -r docker.io/opencontrailnightly -t 1234

          # Pull from private secure registry:
          ./import_contrail_container.sh -f /tmp/contrail_container -r satellite.englab.juniper.net:5443 -c http://satellite.englab.juniper.net/pub/satellite.englab.juniper.net.crt -t 1234

          # Pull from private INsecure registry:
          ./import_contrail_container.sh -f /tmp/contrail_container -r 10.0.0.1:5443 -i 1 -t 1234


4. Upload Contrail containers to Undercloud registry

.. note:: this step is optional, If not done, Contrail containers can be downloaded from external registries.

.. code:: bash

  openstack overcloud container image upload --config-file /tmp/contrail_container
