[< Introduction](introduction.md)...................[Undercloud>](undercloud.md)
# Infrastructure considerations

There are many different ways on how to create the infrastructure providing
the control plane elements. In this example all control plane functions
are provided as Virtual Machines hosted on KVM hosts.

- KVM 1:
 OpenStack Controller 1
 Contrail Controller 1

- KVM 2:
 OpenStack Controller 2
 Contrail Controller 2

- KVM 3:
 OpenStack Controller 3
 Contrail Controller 3

- KVM x:
  Undercloud    

# sample topology
## Layer 1
```
   +-------------------------------+                                          
   |KVM host 3                     |                                          
 +-------------------------------+ |                                          
 |KVM host 2                     | |                                          
+------------------------------+ | |                        
|KVM host 1                    | | |                        
|  +-------------------------+ | | |                        +-----------------------+  
|  |  Contrail Controller 1  | | | |                        |KVM x                  |  
| ++-----------------------+ | | | |     +----------------+ | +------------------+  |  
| | OpenStack Controller 1 | | | | |     |Compute Node N  | | | Undercloud       |  |
| |                        | | | | |   +----------------+ | | |                  |  |
| | +-----+        +-----+ +-+ | | |   |Compute Node 2  | | | | +-----+  +-----+ |  |
| | |VNIC1|        |VNIC2| |   | | | +----------------+ | | | | |VNIC1|  |VNIC2| |  |
| +----+--------------+----+   | | | |Compute Node 1  | | | | +----+--------+----+  |
|      |              |        | | | |                | | | |      |        |       |
|    +-+-+          +-+-+      | | | |                | | | |   +--+---+  +-+-+     |
|    |br0|          |br1|      | | | |                | | | |   |virbr0|  |br1|     |
|    +-+-+          +-+-+      | +-+ |                | | | |   +--+---+  +-+-+     |
|      |              |        | |   |                | | | |      |        |       |
|   +--+-+          +-+--+     +-+   | +----+  +----+ | +-+ |   +--+-+    +-+--+    |
|   |NIC1|          |NIC2|     |     | |NIC1|  |NIC2| +-+   |   |NIC1|    |NIC2|    |
+------+--------------+--------+     +---+-------+----+     +------+--------+-------+
       |              |                  |       |                 |        |         
+------+--------------+------------------+-------+-----------------+--------+-------+
|                                                                                   |
|                          Switch                                                   |
+-----------------------------------------------------------------------------------+
```

## Layer 2
```
+--------------------------------------------+
|                             KVM            |
|  +--------------+  +---------------------+ |
|  | OpenStack    |  | Contrail Controller | |
|  | Controller   |  |                     | |
|  |              |  |                     | |
|  | +----------+ |  | +-------+  +------+ | |
|  | |  VNIC1   | |  | | VNIC1 |  | VNIC2| | |
|  +--------------+  +---------------------+ |
|     | | | | | |       | | | |        |     |
|  +------------------------------+ +------+ |
|  |  | | | | | |       | | | |   | |  |   | |
|  | +--------------------------+ | |  |   | |
|  | |  | | | | |         | | |   | |  |   | |
|  | | +------------------------+ | |  |   | |
|  | | |  | | | |           | |   | |  |   | |
|  | | | +----------------------+ | |  |   | |
|  | | | |  | | |             |   | |  |   | |
|  | | | | +--------------------+ | |  |   | |
|  | | | | |  | |                 | |  |   | |
|  | | | | | +------------------+ | |  |   | |
|  | | | | | |  |                 | |  |   | |
|  | | | | | | +----------------+ | |  |   | |
|  | | | | | | |                  | |  |   | | +--------------------+
|  | | | | | | |   br0            | |  |br1| | | Compute Node       |
|  +------------------------------+ +------+ | |                    |
|    | | | | | |                       |     | |                    |
| +-------------+                   +------+ | | +-------+ +------+ |
| |   NIC1      |                   | NIC2 | | | | NIC1  | | NIC2 | |
+--------------------------------------------+ +--------------------+
    | | | | | |                       |          | | | |     |
+---------------------------------------------------------------+
| |    ge0      |                 | ge1  |     |  ge2  |  | ge3 |
| +-------------+  switch         +------+     +-------+  +-----+
|   | | | | | |                      |          | | |       |   |
|   | | | | | |                      |          | | |       |   |
|   | | | | | |  tenant (no vlan) -> +----------------------+   |
|   | | | | | |                                 | | |           |
|   | | | | | +---storage_mgmt (vlan750)        | | |           |
|   | | | | |                                   | | |           |
|   | | | | +-----storage (vlan740)             | | |           |
|   | | | |                                     | | |           |
|   | | | +-------management (vlan730)--------------+           |
|   | | |                                       | |             |
|   | | +---------external_api (vlan720)        | |             |
|   | |                                         | |             |
|   | +-----------internal_api (vlan710)----------+             |
|   |                                           |               |
|   +-------------provisioning (vlan700)--------+               |
|                                                               |
+---------------------------------------------------------------+
```

# Infrastructure configuration

## Physical switch
- ge0    
-- all networks (vlan700,10,20,30,40,50) are configured as trunks    
- ge1    
-- tenant network is untagged and can be a trunk    
- ge2    
-- provisioning network (vlan700) is the native vlan    
-- all other networks (vlan710,20,30,40,50) are configured as trunks    
- ge3    
-- tenant network is untagged and can be trunk    

## Control plane KVM host preparation (KVM 1-3)

### on all KVM hosts

The control plane KVM hosts will host the control plane VMs. Each KVM host    
will need virtual switches and the virtual machine definitions. The tasks    
described must be done on each of the three hosts.    
NIC 1 - 3 have to be substituted with real NIC names.    

### Install basic packages
```
yum install -y libguestfs \
libguestfs-tools \
openvswitch \
virt-install \
kvm libvirt \
libvirt-python \
python-virtinst
```

### Start libvirtd & ovs
```
systemctl start libvirtd
systemctl start openvswitch
```

### vSwitch configuration:
- br0    
-- provisioning network (vlan700) is the native vlan    
-- all other networks (vlan710,20,30,40,50) are configured as trunks    
- br1    
-- tenant network is untagged    

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

### prepare virtual bmc (on all hosts hosting overcloud nodes)
```
vbmc add compute_1 --port 16230 --username admin --password contrail123
vbmc add compute_2 --port 16231 --username admin --password contrail123
vbmc add contrail-controller_1 --port 16234 --username admin --password contrail123
vbmc add control_1 --port 16235 --username admin --password contrail123

vbmc start compute_1
vbmc start compute_2
vbmc start contrail-controller_1
vbmc start control_1
```

### Define virtual machine templates
For lab testing the computes can be virtualized as well, with the usual    
restrictions coming with nested HV.    

```
num=0
for i in compute control contrail-controller
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
for i in compute control contrail-controller
do
 prov_mac=`virsh domiflist ${i}|grep br_prov|awk '{print $5}'`
 echo ${prov_mac} ${i} >> ironic_list
done
```
The ironic_list file will contain MAC ROLE_NAME and must be manually extended    
to MAC NODE_NAME IPMI/KVM_IP ROLE_NAME.    
This is an example of a full list across three KVM hosts:    
```
52:54:00:16:54:d8 control-1-at-5b3s30 10.87.64.31 control
52:54:00:2a:7d:99 compute-1-at-5b3s30 10.87.64.31 compute
52:54:00:d6:2b:03 contrail-controller-1-at-5b3s30 10.87.64.31 contrail-controller
52:54:00:40:9e:13 control-1-at-centos 10.87.64.32 control
52:54:00:6d:89:2d compute-2-at-centos 10.87.64.32 compute
52:54:00:a8:46:5a contrail-controller-1-at-centos 10.87.64.32 contrail-controller
52:54:00:1d:8c:39 control-1-at-5b3s32 10.87.64.33 control
52:54:00:9c:4b:bf compute-1-at-5b3s32 10.87.64.33 compute
52:54:00:1d:a9:d9 compute-2-at-5b3s32 10.87.64.33 compute
52:54:00:cd:59:92 contrail-controller-1-at-5b3s32 10.87.64.33 contrail-controller
```

This list will be needed on the undercloud VM later on.    
With that the control plane VM KVM host preparation is done.    

# create Undercloud VM on KVM host hosting the Undercloud

## CentOS 7.5
```
mkdir images
curl https://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud-1802.qcow2.xz -o images/CentOS-7-x86_64-GenericCloud-1802.qcow2.xz
zx -d images/CentOS-7-x86_64-GenericCloud-1802.qcow2.xz
cloud_image=images/CentOS-7-x86_64-GenericCloud-1804_02.qcow2
```
## RHEL 7.5
Download rhel-server-7.5-update-1-x86_64-kvm.qcow2 from RedHat portal
```
mkdir ~/images
cloud_image=~/images/rhel-server-7.5-update-1-x86_64-kvm.qcow2
```
```
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
```

## virsh define undercloud VM
```
virt-install --name ${undercloud_name} \
  --disk /var/lib/libvirt/images/${undercloud_name}.qcow2 \
  --vcpus=4 \
  --ram=16348 \
  --network network=default,model=virtio \
  --network network=br0,model=virtio,portgroup=prov \
  --virt-type kvm \
  --import \
  --os-variant rhel7 \
  --graphics vnc \
  --serial pty \
  --noautoconsole \
  --console pty,target_type=virtio
```
```
virsh start ${undercloud_name}
```

## get undercloud ip and log into it
```
undercloud_ip=`virsh domifaddr ${undercloud_name} |grep ipv4 |awk '{print $4}' |awk -F"/" '{print $1}'`
ssh ${undercloud_ip}
```
[< Introduction](introduction.md)                   [Undercloud>](undercloud.md)
