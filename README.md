# Introduction    
Currently the following combinations of RHEL/OSP/Contrail are supported:    
RHEL7.5/OSP11/Contrail >= 4.1.1    
RHEL7.5/OSP10/Contrail >= 4.1.1   
RHEL7.4/OSP11/Contrail >= 4.1.0    
RHEL7.4/OSP10/Contrail >= 4.1.0     
RHEL7.4/OSP11/Contrail >= 4.0.2    
RHEL7.4/OSP10/Contrail >= 4.0.2    
RHEL7.4/OSP10/Contrail >= 3.2.6    
The infrastructure section should only be used as an EXAMPLE. It is not    
considered as part of OSP/Contrail deployment.    

# Infrastructure considerations
There are many different ways on how to create the infrastructure providing    
the control plane elements. In this example all control plane functions    
are provided as Virtual Machines hosted on KVM hosts. For HA 12 VMs are needed:       

- KVM 1:    
  OpenStack Controller 1   
  Contrail Controller 1    
  Contrail Analytics 1    
  Contrail Analytics DB 1    

- KVM 2:    
  OpenStack Controller 2   
  Contrail Controller 2    
  Contrail Analytics 2    
  Contrail Analytics DB 2       

- KVM 3:    
  OpenStack Controller 3   
  Contrail Controller 3    
  Contrail Analytics 3    
  Contrail Analytics DB 3    

The shown architecture is JUST an example to illustrate a possible option    
for the control plane setup.    

Layer1:    

```
   +-----------------------------------+
   |KVM host 3                         |
 +-----------------------------------+ |
 |KVM host 2                         | |
+----------------------------------+ | |
|KVM host 1                        | | |
|    +---------------------------+ | | |
|    |    Contrail Analytics DB 1| | | |
|   ++-------------------------+ | | | |
|   |   Contrail Analytics 1   | | | | |
|  ++------------------------+ | | | | |
|  |  Contrail Controller 1  | +-+ | | |
| ++-----------------------+ | |   | | |      +----------------+
| | OpenStack Controller 1 | +-+   | | |      |Compute Node N  |
| |                        | |     | | |    +----------------+ |
| | +-----+        +-----+ +-+     | | |    |Compute Node 2  | |
| | |VNIC1|        |VNIC3| |       | | |  +----------------+ | |
| +----+--------------+----+       | | |  |Compute Node 1  | | |
|      |              |            | | |  |                | | |
|    +-+-+          +-+-+          | | |  |                | | |
|    |br0|          |br1|          | | |  |                | | |
|    +-+-+          +-+-+          | +-+  |                | | |
|      |              |            | |    |                | | |
|   +--+-+          +-+--+         +-+    | +----+  +----+ | +-+
|   |NIC1|          |NIC2|         |      | |NIC1|  |NIC2| +-+
+------+--------------+------------+      +---+-------+----+
       |              |                       |       |
+------+--------------+-----------------------+-------+--------+
|                                                              |
|                          Switch                              |
+--------------------------------------------------------------+
```

Layer2 (VLAN):    
```
+-----------------------------------------------------------------------+
|                             KVM                                       |
|  +--------------+ +-----------+ +-----------+ +---------------------+ |
|  | OpenStack    | | Contrail  | | Contrail  | | Contrail Controller | |
|  | Controller   | | Analytics | | Analytics | |                     | |
|  |              | |           | | DB        | |                     | |
|  | +----------+ | | +-------+ | | +-------+ | | +-------+  +------+ | |
|  | |  VNIC1   | | | | VNIC1 | | | | VNIC1 | | | | VNIC1 |  | VNIC2| | |
|  +--------------+ +-----------+ +-----------+ +---------------------+ |
|     | | | | | |      | | | |       | | | |       | | | |        |     |
|  +---------------------------------------------------------+ +------+ |
|  |  | | | | | |      | | | |       | | | |       | | | |   | |  |   | |
|  | +------------provisioning (vlan700/native)------------+ | |  |   | |
|  | |  | | | | |        | | |         | | |         | | |   | |  |   | |
|  | | +----------internal_api (vlan710/trunk)-------------+ | |  |   | |
|  | | |  | | | |          | |           | |           | |   | |  |   | |
|  | | | +--------management (vlan730/trunk)---------------+ | |  |   | |
|  | | | |  | | |            |             |             |   | |  |   | |
|  | | | | +------external_api (vlan720/trunk)-------------+ | |  |   | |
|  | | | | |  | |                                            | |  |   | |
|  | | | | | +----storage (vlan740/trunk)------------------+ | |  |   | |
|  | | | | | |  |                                            | |  |   | |
|  | | | | | | +--storage_mgmt (vlan750/trunk)-------------+ | |  |   | |
|  | | | | | | |                                             | |  |   | | +--------------------+
|  | | | | | | |            br0                              | |  |br1| | | Compute Node       |
|  +---------------------------------------------------------+ +------+ | |                    |
|    | | | | | |                                                  |     | |                    |
| +-------------+                                              +------+ | | +-------+ +------+ |
| |   NIC1      |                                              | NIC2 | | | | NIC1  | | NIC2 | |
+-----------------------------------------------------------------------+ +--------------------+
     | | | | | |                                                  |          | | | |     |
 +-------------------------------------------------------------------------------------------+
 | |    ge0      |                                             | ge1  |     |  ge2  |  | ge3||
 | +-------------+                                             +------+     +-------+  +-----+
 |   | | | | | |                                                  |          | | | |     |   |
 |   | | | | | |            Switch                                |          | | | |     |   |
 |   | | | | | |                              tenant (no vlan) -> +----------------------+   |
 |   | | | | | |                                                             | | | |         |
 |   | | | | | +---------<-trunk--storage_mgmt (vlan750)                     | | | |         |
 |   | | | | |                                                               | | | |         |
 |   | | | | +-----------<-trunk--storage (vlan740)                          | | | |         |
 |   | | | |                                                                 | | | |         |
 |   | | | +-------------<-trunk--management (vlan730)--trunk->--------------------+         |
 |   | | |                                                                   | | |           |
 |   | | +---------------<-trunk--external_api (vlan720)--trunk->----------------+           |
 |   | |                                                                     | |             |
 |   | +-----------------<-trunk--internal_api (vlan710)--trunk->--------------+             |
 |   |                                                                       |               |
 |   +-------------------<-trunk--provisioning (vlan700)--native->-----------+               |
 |                                                                                           |
 +-------------------------------------------------------------------------------------------+
```

vSwitch configuration:    
- br0    
-- provisioning network (vlan700) is the native vlan    
-- all other networks (vlan710,20,30,40,50) are configured as trunks    
- br1    
-- tenant network is untagged    

pSwitch configuration:    
- ge0    
-- all networks (vlan700,10,20,30,40,50) are configured as trunks    
- ge1    
-- tenant network is untagged
- ge2    
-- provisioning network (vlan700) is the native vlan    
-- all other networks (vlan710,20,30,40,50) are configured as trunks    
- ge3    
-- tenant network is untagged

## Control plane KVM host preparation (KVM 1-3)

The control plane KVM hosts will host the control plane VMs. Each KVM host    
will need virtual switches and the virtual machine definitions. The tasks    
described must be done on each of the three hosts.    
NIC 1 - 3 have to be substituded with real NIC names.    

### Install basic packages
```
yum install -y libguestfs libguestfs-tools openvswitch virt-install kvm libvirt libvirt-python python-virtinst
```

### Start libvirtd & ovs
```
systemctl start libvirtd
systemctl start openvswitch
```

### Create virtual switches for the undercloud VM
```
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
```

### Define virtual machine templates
As described above, each KVM host needs at least 4 virtual machine templates.    
For lab testing the computes can be virtualized as well, with the usual    
restrictions coming with nested HV.    

```
num=0
for i in compute control contrail-controller contrail-analytics contrail-analytics-database
do
  num=$(expr $num + 1)
  qemu-img create -f qcow2 /var/lib/libvirt/images/${i}_${num}.qcow2 40G
  virsh define /dev/stdin <<EOF
$(virt-install --name ${i}_$num --disk /var/lib/libvirt/images/${i}_${num}.qcow2 --vcpus=4 --ram=16348 --network network=br0,model=virtio,portgroup=overcloud --network network=br1,model=virtio --virt-type kvm --import --os-variant rhel7 --serial pty --console pty,target_type=virtio --print-xml)
EOF
done
```

### Get provisioning interface mac addresses for ironic PXE
The virtual machines must be imported into ironic. There are different ways    
to do that. One way is to create a list of all VMs in the following format:    
MAC NODE_NAME IPMI/KVM_IP ROLE_NAME    
```
52:54:00:16:54:d8 control-1-at-5b3s30 10.87.64.31 control    
```
In order to get the initial list per KVM host the following command can be run:    
```
for i in compute control contrail-controller contrail-analytics contrail-analytics-database    
do
  prov_mac=`virsh domiflist ${i}|grep br0|awk '{print $5}'`
  echo ${prov_mac} ${i} >> ironic_list
done
```
The ironic_list file will contain MAC ROLE_NAME and must be manually extended    
to MAC NODE_NAME IPMI/KVM_IP ROLE_NAME.    
This is an example of a full list across three KVM hosts:    
```
52:54:00:16:54:d8 control-1-at-5b3s30 10.87.64.31 control
52:54:00:2a:7d:99 compute-1-at-5b3s30 10.87.64.31 compute
52:54:00:e0:54:b3 tsn-1-at-5b3s30 10.87.64.31 contrail-tsn
52:54:00:d6:2b:03 contrail-controller-1-at-5b3s30 10.87.64.31 contrail-controller
52:54:00:01:c1:af contrail-analytics-1-at-5b3s30 10.87.64.31 contrail-analytics
52:54:00:4a:9e:52 contrail-analytics-database-1-at-5b3s30 10.87.64.31 contrail-analytics-database
52:54:00:40:9e:13 control-1-at-centos 10.87.64.32 control
52:54:00:1d:58:4d compute-dpdk-1-at-centos 10.87.64.32 compute-dpdk
52:54:00:6d:89:2d compute-2-at-centos 10.87.64.32 compute
52:54:00:a8:46:5a contrail-controller-1-at-centos 10.87.64.32 contrail-controller
52:54:00:b3:2f:7d contrail-analytics-1-at-centos 10.87.64.32 contrail-analytics
52:54:00:59:e3:10 contrail-analytics-database-1-at-centos 10.87.64.32 contrail-analytics-database
52:54:00:1d:8c:39 control-1-at-5b3s32 10.87.64.33 control
52:54:00:9c:4b:bf compute-1-at-5b3s32 10.87.64.33 compute
52:54:00:1d:a9:d9 compute-2-at-5b3s32 10.87.64.33 compute
52:54:00:cd:59:92 contrail-controller-1-at-5b3s32 10.87.64.33 contrail-controller
52:54:00:2f:81:1a contrail-analytics-1-at-5b3s32 10.87.64.33 contrail-analytics
52:54:00:a1:4a:23 contrail-analytics-database-1-at-5b3s32 10.87.64.33 contrail-analytics-database
```

This list will be needed on the undercloud VM later on.    
With that the control plane VM KVM host preparation is done.    

## Undercloud preparation on the KVM host hosting the undercloud VM

The undercloud VM can be installed on one of the three KVM hosts or on a    
different one.    

### Set password & subscription information
```
export USER=<YOUR_RHEL_SUBS_USER>
export PASSWORD=<YOUR_RHEL_SUBS_PWD>
export POOLID=<YOUR_RHEL_POOL_ID>
export ROOTPASSWORD=<UNDERCLOUD_ROOT_PWD> # choose a root user password
export STACKPASSWORD=<STACK_USER_PWD> # choose a stack user password
```

### Install basic packages
```
yum install -y libguestfs libguestfs-tools openvswitch virt-install kvm libvirt libvirt-python python-virtinst
```

### Start libvirtd & ovs
```
systemctl start libvirtd
systemctl start openvswitch
```

### Create and become stack user
```
useradd -G libvirt stack
echo $STACKPASSWORD |passwd stack --stdin
echo "stack ALL=(root) NOPASSWD:ALL" | sudo tee -a /etc/sudoers.d/stack
chmod 0440 /etc/sudoers.d/stack
```
### Create ssh key
```
ssh-keygen -t dsa
```

### Adjust permissions
```
chgrp -R libvirt /var/lib/libvirt/images
chmod g+rw /var/lib/libvirt/images
```

### Get rhel 7.5 kvm image
Download rhel-server-7.5-update-1-x86_64-kvm.qcow2 from RedHat portal

### Create virtual switches for the undercloud VM (in case it runs on a
different KVM host than the overcloud VMs
```
ovs-vsctl add-br br0
ovs-vsctl add-port br0 NIC1
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
virsh net-define br0.xml
virsh net-start br0
virsh net-autostart br0
```

### Prepare undercloud VM
#### OSP10
```
export LIBGUESTFS_BACKEND=direct
qemu-img create -f qcow2 undercloud.qcow2 100G
virt-resize --expand /dev/sda1 rhel-server-7.4-x86_64-kvm.qcow2 undercloud.qcow2
virt-customize  -a undercloud.qcow2 \
  --run-command 'xfs_growfs /' \
  --root-password password:$ROOTPASSWORD \
  --hostname undercloud.local \
  --sm-credentials $USER:password:$PASSWORD --sm-register --sm-attach auto --sm-attach pool:$POOLID \
  --run-command 'useradd stack' \
  --password stack:password:$STACKPASSWORD \
  --run-command 'echo "stack ALL=(root) NOPASSWD:ALL" | tee -a /etc/sudoers.d/stack' \
  --chmod 0440:/etc/sudoers.d/stack \
  --run-command 'subscription-manager repos --enable=rhel-7-server-rpms --enable=rhel-7-server-extras-rpms --enable=rhel-7-server-rh-common-rpms --enable=rhel-ha-for-rhel-7-server-rpms --enable=rhel-7-server-openstack-10-rpms' \
  --install python-tripleoclient \
  --run-command 'sed -i "s/PasswordAuthentication no/PasswordAuthentication yes/g" /etc/ssh/sshd_config' \
  --run-command 'systemctl enable sshd' \
  --run-command 'yum remove -y cloud-init' \
  --selinux-relabel
cp undercloud.qcow2 /var/lib/libvirt/images/undercloud.qcow2
```

#### OSP11
```
export LIBGUESTFS_BACKEND=direct
qemu-img create -f qcow2 undercloud.qcow2 100G
virt-resize --expand /dev/sda1 rhel-server-7.4-x86_64-kvm.qcow2 undercloud.qcow2
virt-customize  -a undercloud.qcow2 \
  --run-command 'xfs_growfs /' \
  --root-password password:$ROOTPASSWORD \
  --hostname undercloud.local \
  --sm-credentials $USER:password:$PASSWORD --sm-register --sm-attach auto --sm-attach pool:$POOLID \
  --run-command 'useradd stack' \
  --password stack:password:$STACKPASSWORD \
  --run-command 'echo "stack ALL=(root) NOPASSWD:ALL" | tee -a /etc/sudoers.d/stack' \
  --chmod 0440:/etc/sudoers.d/stack \
  --run-command 'subscription-manager repos --enable=rhel-7-server-rpms --enable=rhel-7-server-extras-rpms --enable=rhel-7-server-rh-common-rpms --enable=rhel-ha-for-rhel-7-server-rpms --enable=rhel-7-server-openstack-11-rpms' \
  --install python-tripleoclient \
  --run-command 'sed -i "s/PasswordAuthentication no/PasswordAuthentication yes/g" /etc/ssh/sshd_config' \
  --run-command 'systemctl enable sshd' \
  --run-command 'yum remove -y cloud-init' \
  --selinux-relabel
cp undercloud.qcow2 /var/lib/libvirt/images/undercloud.qcow2
```

### Install undercloud VM
```
virt-install --name undercloud \
  --disk /var/lib/libvirt/images/undercloud.qcow2 \
  --vcpus=4 \
  --ram=16348 \
  --network network=default,model=virtio \
  --network network=br0,model=virtio,portgroup=overcloud \
  --virt-type kvm \
  --import \
  --os-variant rhel7 \
  --graphics vnc \
  --serial pty \
  --noautoconsole \
  --console pty,target_type=virtio
```

### Get undercloud ip
```
virsh domifaddr undercloud
```

### Ssh into undercloud
```
ssh stack@<UNDERCLOUD_IP>
```

# Undercloud configuration

## Configure undercloud (optionally)
```
cp /usr/share/instack-undercloud/undercloud.conf.sample ~/undercloud.conf
vi ~/undercloud.conf
```

## Install undercloud openstack
```
openstack undercloud install
```

## Source undercloud credentials
```
source ~/stackrc
```

## Get overcloud images
```
sudo yum install rhosp-director-images rhosp-director-images-ipa
mkdir ~/images
cd ~/images
```

## Upload overcloud images
### OSP10
```
for i in /usr/share/rhosp-director-images/overcloud-full-latest-10.0.tar /usr/share/rhosp-director-images/ironic-python-agent-latest-10.0.tar; do tar -xvf $i; done
openstack overcloud image upload --image-path /home/stack/images/
cd ~
```
### OSP11
```
for i in /usr/share/rhosp-director-images/overcloud-full-latest-11.0.tar /usr/share/rhosp-director-images/ironic-python-agent-latest-11.0.tar; do tar -xvf $i; done
openstack overcloud image upload --image-path /home/stack/images/
cd ~
```

## Create contrail repo
```
sudo mkdir /var/www/html/contrail
```

## Get contrail
go to:    
https://www.juniper.net/support/downloads/?p=contrail#sw

### Contrail 3.2.6
and download the 3.2.6 release (Redhat 7.3 + newton)    
transfer it to the undercloud    
```
sudo tar zxvf ~/contrail-install-packages-3.2.6.0-60-redhat73newton.tgz -C /var/www/html/contrail/
```
### Contrail 4.0.2
and download the 4.0.2 release (Redhat 7 + Contrail Networking - RHOSP10)
transfer it to the undercloud    
```
sudo tar zxvf ~/contrail-install-packages_4.0.2.0-35-newton_redhat7.tgz -C /var/www/html/contrail/
```

## Import ironic nodes
In this step the fully populated ironic_list from    
infrastructure considerations/control plane KVM host preparation (KVM 1-3)/define virtual machine templates    
is needed.    
### Virtual Machines
This imports all virtual machines into ironic.    
```
ssh_user=SSH_USER
ssh_password=SSH_PASSWORD
while IFS= read -r line
do   
  mac=`echo $line|awk '{print $1}'`
  name=`echo $line|awk '{print $2}'`
  kvm_ip=`echo $line|awk '{print $3}'`
  profile=`echo $line|awk '{print $4}'`
  uuid=`ironic node-create -d pxe_ssh -p cpus=4 -p memory_mb=16348 -p local_gb=100 -p cpu_arch=x86_64 -i ssh_username=${ssh_user} -i ssh_virt_type=virsh -i ssh_address=${kvm_ip} -i ssh_password=${ssh_password} -n $name -p capabilities=profile:${profile} | tail -2|awk '{print $4}'`
  ironic port-create -a ${mac} -n ${uuid}
done < <(cat ironic_list)
```
### Physical Machines
For importing physical compute nodes the pxe_ssh driver must be replaced with    
the ipmi driver. Easiest way is to create a ironic_list_bms with only    
physical machines in it.    
```
ipmi_user=IPMI_USER
ipmi_password=IPMI_PASSWORD
while IFS= read -r line
do
  mac=`echo $line|awk '{print $1}'`
  name=`echo $line|awk '{print $2}'`
  ipmi_address=`echo $line|awk '{print $3}'`
  profile=`echo $line|awk '{print $4}'`
  uuid=`ironic node-create -d pxe_ipmitool -p cpus=4 -p memory_mb=16348 -p local_gb=100 -p cpu_arch=x86_64 -i ipmi_username=${ipmi_user} -i ipmi_address=${ipmi_address} -i ipmi_password=${ipmi_password} -n $name -p capabilities=profile:${profile} | tail -2|awk '{print $4}'`
  ironic port-create -a ${mac} -n ${uuid}
done < <(cat ironic_list_bms)
```

## Configure boot mode
```
openstack baremetal configure boot
```

## Node introspection
```
for node in $(openstack baremetal node list -c UUID -f value) ; do openstack baremetal node manage $node ; done
openstack overcloud node introspect --all-manageable --provide
```

## Node profiling
```
for i in contrail-controller contrail-analytics contrail-database contrail-analytics-database; do
  openstack flavor create $i --ram 4096 --vcpus 1 --disk 40
  openstack flavor set --property "capabilities:boot_option"="local" --property "capabilities:profile"="${i}" ${i}
done
```

# Configure overcloud

## Install tripleo-heat-templates on the undercloud
### Contrail 3.2.6
```
sudo yum localinstall /var/www/html/contrail/contrail-tripleo-heat-templates-3.2.6.0-60.el7.noarch.rpm
```
### Contrail 4.0.2
```
sudo yum localinstall /var/www/html/contrail/contrail-tripleo-heat-templates-4.0.2.0-35.el7.noarch.rpm
```
```
cp -r /usr/share/openstack-tripleo-heat-templates/ ~/tripleo-heat-templates
cp -r /usr/share/contrail-tripleo-heat-templates/environments/* ~/tripleo-heat-templates/environments
cp -r /usr/share/contrail-tripleo-heat-templates/puppet/services/network/* ~/tripleo-heat-templates/puppet/services/network
```

## Contrail services (repo url etc.)
### Set Contrail version
#### Contrail 3.2.6
set ContrailVersion: 3 in ~/tripleo-heat-templates/environments/contrail/contrail-services.yaml    
```
vi ~/tripleo-heat-templates/environments/contrail/contrail-services.yaml
```
#### Contrail 4.0.2
4.0.2 is default    

## Overcloud networking
### NIC configurations
#### OSP10
```
vi ~/tripleo-heat-templates/environments/contrail/contrail-net.yaml
vi ~/tripleo-heat-templates/environments/contrail/contrail-nic-config-compute.yaml
vi ~/tripleo-heat-templates/environments/contrail/contrail-nic-config.yaml
```
#### OSP11
```
vi ~/tripleo-heat-templates/environments/contrail/contrail-net.yaml
vi ~/tripleo-heat-templates/environments/configs/contrail/contrail-nic-config-compute.yaml
vi ~/tripleo-heat-templates/environments/configs/contrail/contrail-nic-config.yaml
```

### Static ip assignment
#### OSP10
```
vi ~/tripleo-heat-templates/environments/contrail/ips-from-pool-all.yaml
```
#### OSP11
```
vi ~/tripleo-heat-templates/environments/ips-from-pool-all.yaml
```

## Provide subscription mgr credentials (rhel_reg_password, rhel_reg_pool_id, rhel_reg_repos, rhel_reg_user and method)
### OSP10
Make also sure you add the repro "rhel-7-server-openstack-10-devtools-rpms" to rhel_reg_repos as it's needed for vRouter installation
```
vi ~/tripleo-heat-templates/extraconfig/pre_deploy/rhel-registration/environment-rhel-registration.yaml
```

# Start overcloud installation
## Contrail 3.2.6
```
openstack overcloud deploy --templates tripleo-heat-templates/ \
  --roles-file tripleo-heat-templates/environments/contrail/roles_data.yaml \
  -e tripleo-heat-templates/environments/puppet-pacemaker.yaml \
  -e tripleo-heat-templates/environments/contrail/contrail-services.yaml \
  -e tripleo-heat-templates/environments/contrail/network-isolation.yaml \
  -e tripleo-heat-templates/environments/contrail/contrail-net.yaml \
  -e tripleo-heat-templates/environments/contrail/ips-from-pool-all.yaml \
  -e tripleo-heat-templates/environments/network-management.yaml \
  -e tripleo-heat-templates/extraconfig/pre_deploy/rhel-registration/environment-rhel-registration.yaml \
  -e tripleo-heat-templates/extraconfig/pre_deploy/rhel-registration/rhel-registration-resource-registry.yaml \
  --libvirt-type qemu
```

## Contrail 4.0.2
```
openstack overcloud deploy --templates tripleo-heat-templates/ \
  --roles-file tripleo-heat-templates/environments/contrail/roles_data.yaml \
  -e tripleo-heat-templates/environments/puppet-pacemaker.yaml \
  -e tripleo-heat-templates/environments/contrail/contrail-services.yaml \
  -e tripleo-heat-templates/environments/contrail/network-isolation.yaml \
  -e tripleo-heat-templates/environments/contrail/contrail-net.yaml \
  -e tripleo-heat-templates/environments/ips-from-pool-all.yaml \
  -e tripleo-heat-templates/environments/network-management.yaml \
  -e tripleo-heat-templates/extraconfig/pre_deploy/rhel-registration/environment-rhel-registration.yaml \
  -e tripleo-heat-templates/extraconfig/pre_deploy/rhel-registration/rhel-registration-resource-registry.yaml \
  --libvirt-type qemu
```

# DPDK special

For dpdk a modified overcloud image has to be created. This step can be done    
on the undercloud but will take very long if the kvm host doesn't have    
nested HV enabled. Alternatively, the overcloud image can be downloaded to the    
kvm host and be customized there.    

## Customize DPDK overcloud image

```
cp /home/stack/images/overcloud-full.qcow2 /home/stack/images/overcloud-full-dpdk.qcow2
export LIBGUESTFS_BACKEND=direct
/usr/bin/virt-customize  -a /home/stack/images/overcloud-full-dpdk.qcow2 \
  --sm-credentials $USER:password:$PASSWORD --sm-register --sm-attach auto \
  --run-command 'subscription-manager repos --enable=rhel-7-server-rpms --enable=rhel-7-server-extras-rpms --enable=rhel-7-server-rh-common-rpms --enable=rhel-ha-for-rhel-7-server-rpms --enable=rhel-7-server-openstack-10-rpms --enable=rhel-7-server-openstack-10-devtools-rpms' \
  --copy-in /etc/yum.repos.d/contrail.repo:/etc/yum.repos.d \
  --run-command 'yum install -y contrail-vrouter-utils contrail-vrouter-dpdk contrail-vrouter-dpdk-init' \
  --run-command 'rm -fr /var/cache/yum/*' \
  --run-command 'yum clean all' \
  --run-command 'rm -rf /etc/yum.repos.d/contrail.repo' \
  --run-command 'subscription-manager unregister' \
  --selinux-relabel
```

## Upload modified dpdk image to glance

```
glance image-create --name overcloud-full-dpdk --container-format bare --disk-format qcow2 --file overcloud-full-dpdk.qcow2
openstack image set overcloud-full-dpdk --property kernel_id=`glance image-list |grep bm-deploy-kernel |awk '{print $2}'` --property ramdisk_id=`glance image-list |grep bm-deploy-ramdisk |awk '{print $2}'`
```

## Profile ironic node with DPDK

```
ironic node-update $DPDK_NODE_UUID replace properties/capabilities=profile:contrail-dpdk,cpu_hugepages:true,cpu_txt:true,boot_option:local,cpu_aes:true,cpu_vt:true,cpu_hugepages_1g:true
openstack flavor create contrail-dpdk --ram 4096 --vcpus 1 --disk 40
openstack flavor set --property "capabilities:boot_option"="local" --property "capabilities:profile"="contrail-dpdk" contrail-dpdk
```

Where $DPDK_NODE_UUID is the ironic UUID of the DPDK node    

## Additional DPDK parameters

More DPDK parameters can be configured in:    

```
tripleo-heat-templates/environments/contrail/contrail-net.yaml
```

# TSN special

In case of EVPN VXLAN Provisioning when more than 2 TSN nodes are present, user should provide per TSN node specific hiera data with "contrail::vrouter::tsn_servers" containing a pair of TSNs.

```
vi tripleo-heat-templates/environments/contrail/contrail-tsn-servers.yaml
```

The TSN interface used for the vrouter has to be configured:    

```
tripleo-heat-templates/environments/contrail/contrail-net.yaml
```

## deploy
```
openstack overcloud deploy --templates tripleo-heat-templates/ \
  --roles-file tripleo-heat-templates/environments/contrail/roles_data_contrail.yaml \
  -e .tripleo/environments/deployment-artifacts.yaml \
  -e tripleo-heat-templates/environments/contrail/contrail-services.yaml \
  -e tripleo-heat-templates/environments/contrail/contrail-net-single.yaml \
  -e contrail_controller_vip_env.yaml \
  -e misc_opts.yaml \
  -e tripleo-heat-templates/environments/contrail/contrail-tsn-servers.yaml
```


# SR-IOV special

If you are enabling SR-IOV on a system you should complete the following:

## enable the Intel Input-Output Memory Management Unit (IOMMU) on Linux

For SR-IOV on compute nodes iommu should be enabled.

```
sed 's/^\(GRUB_CMDLINE_LINUX=".*\)"/\1 intel_iommu=on iommu=pt"/g' -i /etc/default/grub ;
grub2-mkconfig -o /etc/grub2.cfg
reboot
```

## edit contrail-sriov.yaml file

```
vi tripleo-heat-templates/environments/contrail/contrail-sriov.yaml
```

- set NeutronSriovNumVFs: number of VFs that needs to be configured for a physical interface
- set NovaPCIPassthrough: the white list of PCI devices available to VMs

## deploy
```
openstack overcloud deploy --templates tripleo-heat-templates/ \
  --roles-file tripleo-heat-templates/environments/contrail/roles_data_contrail.yaml \
  -e .tripleo/environments/deployment-artifacts.yaml \
  -e tripleo-heat-templates/environments/contrail/contrail-services.yaml \
  -e tripleo-heat-templates/environments/contrail/contrail-net-single.yaml \
  -e contrail_controller_vip_env.yaml \
  -e misc_opts.yaml \
  -e tripleo-heat-templates/environments/contrail/contrail-sriov.yaml
```
