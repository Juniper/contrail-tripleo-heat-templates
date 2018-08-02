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

Under- and Overcloud KVM host configuration
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

Create Overcloud VM definitions on the Overcloud KVM hosts (KVM2-4)
-------------------------------------------------------------------

.. note:: This has to be done on each of the Overcloud KVM hosts

.. note:: Define the roles and the number of that roles per Overcloud KVM host.
          This example defines:
            2x compute nodes
            1x cotrail controller node
            1x openstack controller node
  ::

    ROLES=compute:2,contrail-controller:1,control:1

.. code:: bash

  num=0
  ipmi_user=ADMIN
  ipmi_password=ADMIN
  libvirt_path=/var/lib/libvirt/images
  port_group=overcloud
  prov_switch=br0

  /bin/rm ironic_list
  IFS=',' read -ra role_list <<< "${ROLES}"
  for role in ${role_list[@]}; do
    role_name=`echo $role|cut -d ":" -f 1`
    role_count=`echo $role|cut -d ":" -f 2`
    for count in `seq 1 ${role_count}`; do
      echo $role_name $count
      qemu-img create -f qcow2 ${libvirt_path}/${role_name}_${count}.qcow2 99G
      virsh define /dev/stdin <<EOF
      $(virt-install --name ${role_name}_${count} \
  --disk ${libvirt_path}/${role_name}_${count}.qcow2 \
  --vcpus=4 \
  --ram=16348 \
  --network network=br0,model=virtio,portgroup=${port_group} \
  --network network=br1,model=virtio \
  --virt-type kvm \
  --cpu host \
  --import \
  --os-variant rhel7 \
  --serial pty \
  --console pty,target_type=virtio \
  --graphics vnc \
  --print-xml)
  EOF
      vbmc add ${role_name}_${count} --port 1623${num} --username ${ipmi_user} --password ${ipmi_password}
      vbmc start ${role_name}_${count}
      prov_mac=`virsh domiflist ${role_name}_${count}|grep ${prov_switch}|awk '{print $5}'`
      vm_name=${role_name}-${count}-`hostname -s`
      kvm_ip=`ip route get 1  |grep src |awk '{print $7}'`
      echo ${prov_mac} ${vm_name} ${kvm_ip} ${role_name} 1623${num}>> ironic_list
      num=$(expr $num + 1)
    done
  done

.. note:: There will be one ironic_list file per KVM host. The ironic_list files of all KVM hosts
          has to be combined on the Undercloud.

.. note:: example of a combined list from all three Overcloud KVM hosts:
 
         ::
          
             52:54:00:e7:ca:9a compute-1-5b3s31 10.87.64.32 compute 16230
             52:54:00:30:6c:3f compute-2-5b3s31 10.87.64.32 compute 16231
             52:54:00:9a:0c:d5 contrail-controller-1-5b3s31 10.87.64.32 contrail-controller 16232
             52:54:00:cc:93:d4 control-1-5b3s31 10.87.64.32 control 16233
             52:54:00:28:10:d4 compute-1-5b3s30 10.87.64.31 compute 16230
             52:54:00:7f:36:e7 compute-2-5b3s30 10.87.64.31 compute 16231
             52:54:00:32:e5:3e contrail-controller-1-5b3s30 10.87.64.31 contrail-controller 16232
             52:54:00:d4:31:aa control-1-5b3s30 10.87.64.31 control 16233
             52:54:00:d1:d2:ab compute-1-5b3s32 10.87.64.33 compute 16230
             52:54:00:ad:a7:cc compute-2-5b3s32 10.87.64.33 compute 16231
             52:54:00:55:56:50 contrail-controller-1-5b3s32 10.87.64.33 contrail-controller 16232
             52:54:00:91:51:35 control-1-5b3s32 10.87.64.33 control 16233

Create Undercloud VM definition on the Undercloud KVM host (KVM1)
-----------------------------------------------------------------

.. note:: This has to be done on the Undercloud KVM host only

1. Create images directory

.. code:: bash

  mkdir ~/images
  cd images

2. Getting the images

   .. note::
      Depending on the operating system the image must be retrieved
      using different methods:

      .. admonition:: CentOS
         :class: centos

         ::

             curl https://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud-1802.qcow2.xz \ 
               -o CentOS-7-x86_64-GenericCloud-1802.qcow2.xz
             zx -d images/CentOS-7-x86_64-GenericCloud-1802.qcow2.xz
             cloud_image=~/images/CentOS-7-x86_64-GenericCloud-1804_02.qcow2

      .. admonition:: RHEL
         :class: rhel

         ::
     
           Download rhel-server-7.5-update-1-x86_64-kvm.qcow2 from RedHat portal to ~/images
           cloud_image=~/images/rhel-server-7.5-update-1-x86_64-kvm.qcow2

3. Customize the Undercloud image

.. code:: bash

  undercloud_name=queensa
  undercloud_suffix=local
  root_password=contrail123
  stack_password=contrail123
  export LIBGUESTFS_BACKEND=direct
  qemu-img create -f qcow2 /var/lib/libvirt/images/${undercloud_name}.qcow2 100G
  virt-resize --expand /dev/sda1 ${cloud_image} /var/lib/libvirt/images/${undercloud_name}.qcow2
  virt-customize  -a /var/lib/libvirt/images/${undercloud_name}.qcow2 \
    --run-command 'xfs_growfs /' \
    --root-password password:${root_password} \
    --hostname ${undercloud_name}.${undercloud_suffix} \
    --run-command 'useradd stack' \
    --password stack:password:${stack_password} \
    --run-command 'echo "stack ALL=(root) NOPASSWD:ALL" | tee -a /etc/sudoers.d/stack' \
    --chmod 0440:/etc/sudoers.d/stack \
    --run-command 'sed -i "s/PasswordAuthentication no/PasswordAuthentication yes/g" /etc/ssh/sshd_config' \
    --run-command 'systemctl enable sshd' \
    --run-command 'yum remove -y cloud-init' \
    --selinux-relabel

4. Define the Undercloud virsh template

.. code:: bash

  vcpus=8
  vram=32000
  virt-install --name ${undercloud_name} \
    --disk /var/lib/libvirt/images/${undercloud_name}.qcow2 \
    --vcpus=${vcpus} \
    --ram=${vram} \
    --network network=default,model=virtio \
    --network network=br0,model=virtio,portgroup=overcloud \
    --virt-type kvm \
    --import \
    --os-variant rhel7 \
    --graphics vnc \
    --serial pty \
    --noautoconsole \
    --console pty,target_type=virtio

5. Start the Undercloud VM

.. code:: bash

  virsh start ${undercloud_name}

6. Retrieve the Undercloud IP (might take a few secconds before the IP is available

.. code:: bash

  undercloud_ip=`virsh domifaddr ${undercloud_name} |grep ipv4 |awk '{print $4}' |awk -F"/" '{print $1}'`
  ssh-copy-id ${undercloud_ip}
