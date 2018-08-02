#############
Configuration
#############

.. contents:: Table of Contents

Physical switch
===============

+------+---------------+-------------+
| Port | Trunked Vlans | Native Vlan |
+======+===============+=============+
| ge0  |    -          |    -        |
+------+---------------+-------------+
| ge1  | 700, 720      |    -        |
+------+---------------+-------------+
| ge2  | 700, 710, 720,|    -        |
|      | 730, 740, 750 |             |
+------+---------------+-------------+
| ge3  |    -          |    -        |
+------+---------------+-------------+
| ge4  | 710, 730      | 700         |
+------+---------------+-------------+
| ge5  |    -          |    -        |
+------+---------------+-------------+

Under- and overcloud KVM host configuration
===========================================

Under- and Overcloud KVM hosts will need virtual switches and    
virtual machine definitions configured.    
The KVM host operating system can be any decent Linux supporting     
KVM and OVS. In this example a RHEL/CentOS based system is used.    
In case of RHEL the system must be subscriped.

Install basic packages
----------------------

.. code:: bash

  yum install -y libguestfs \
    libguestfs-tools \
    openvswitch \
    virt-install \
    kvm libvirt \
    libvirt-python \
    python-virtualbmc \
    python-virtinst

Start libvirtd and ovs
----------------------

.. code:: bash

  systemctl start libvirtd
  systemctl start openvswitch

vSwitch configuration
---------------------

+-------+---------------+-------------+
| Bridge| Trunked Vlans | Native Vlan |
+=======+===============+=============+
| br0   | 710, 720, 730 | 700         |
|       | 740, 750      |             |
+-------+---------------+-------------+
| br1   |   -           |    -        |
+-------+---------------+-------------+

Create bridges
^^^^^^^^^^^^^^

.. code:: bash

  ovs-vsctl add-br br0
  ovs-vsctl add-br br1
  ovs-vsctl add-port br0 NIC1
  ovs-vsctl add-port br1 NIC2
  cat << EOF > br0.xml
  <network>
    <name>br0</name>
    <forward mode='bridge'/>
    <bridge name='br0'/>
    <virtualport type='openvswitch'/>
    <portgroup name='overcloud'>
      <vlan trunk='yes'>
        <tag id='700' nativeMode='untagged'/>
        <tag id='710'/>
        <tag id='720'/>
        <tag id='730'/>
        <tag id='740'/>
        <tag id='750'/>
      </vlan>
    </portgroup>
  </network>
  EOF
  cat << EOF > br1.xml
  <network>
    <name>br1</name>
    <forward mode='bridge'/>
    <bridge name='br1'/>
    <virtualport type='openvswitch'/>
  </network>
  EOF
  virsh net-define br0.xml
  virsh net-start br0
  virsh net-autostart br0
  virsh net-define br1.xml
  virsh net-start br1
  virsh net-autostart br1

Create Undercloud VM definition on the Undercloud KVM host
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: This has to be done on the Undercloud KVM host only
