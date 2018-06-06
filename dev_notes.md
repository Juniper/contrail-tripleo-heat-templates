# sample toplogy
## Layer 1
```
   +-------------------------------+
   |KVM host 3                     |
 +-------------------------------+ |
 |KVM host 2                     | |
+------------------------------+ | |
|KVM host 1                    | | |
|  +-------------------------+ | | |
|  |  Contrail Controller 1  | | | |
| ++-----------------------+ | | | |      +----------------+
| | OpenStack Controller 1 | | | | |      |Compute Node N  |
| |                        | | | | |    +----------------+ |
| | +-----+        +-----+ +-+ | | |    |Compute Node 2  | |
| | |VNIC1|        |VNIC2| |   | | |  +----------------+ | |
| +----+--------------+----+   | | |  |Compute Node 1  | | |
|      |              |        | | |  |                | | |
|    +-+-+          +-+-+      | | |  |                | | |
|    |br0|          |br1|      | | |  |                | | |
|    +-+-+          +-+-+      | +-+  |                | | |
|      |              |        | |    |                | | |
|   +--+-+          +-+--+     +-+    | +----+  +----+ | +-+
|   |NIC1|          |NIC2|     |      | |NIC1|  |NIC2| +-+
+------+--------------+--------+      +---+-------+----+
       |              |                   |       |
+------+--------------+-------------------+-------+--------+
|                                                          |
|                          Switch                          |
+----------------------------------------------------------+
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

# on all KVM hosts

## prepare virtual bmc (on all hosts hosting overcloud nodes)
```bash
vbmc add compute_1 --port 16230 --username admin --password contrail123
vbmc add compute_2 --port 16231 --username admin --password contrail123
vbmc add contrail-analytics-database_1 --port 16232 --username admin --password contrail123
vbmc add contrail-analytics_1 --port 16233 --username admin --password contrail123
vbmc add contrail-controller_1 --port 16234 --username admin --password contrail123
vbmc add control_1 --port 16235 --username admin --password contrail123

vbmc start compute_1
vbmc start compute_2
vbmc start contrail-analytics-database_1
vbmc start contrail-analytics_1
vbmc start contrail-controller_1
vbmc start control_1
```

## create undercloud VM on KVM host hosting the undercloud
### CentOS 7.5
```
mkdir images
curl https://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud-1802.qcow2.xz -o images/CentOS-7-x86_64-GenericCloud-1802.qcow2.xz
zx -d images/CentOS-7-x86_64-GenericCloud-1802.qcow2.xz
cloud_image=images/CentOS-7-x86_64-GenericCloud-1804_02.qcow2
```
### RHEL 7.5
Download from RedHat portal
```
cloud_image=images/rhel-server-7.5-beta-1-x86_64-kvm.qcow2
```
```
root_password=contrail123
stack_password=contrail123
undercloud_name=queensa
export LIBGUESTFS_BACKEND=direct
qemu-img create -f qcow2 /var/lib/libvirt/images/${undercloud_name}.qcow2 100G
virt-resize --expand /dev/sda1 ${cloud_image} /var/lib/libvirt/images/${undercloud_name}.qcow2
virt-customize  -a /var/lib/libvirt/images/${undercloud_name}.qcow2 \
  --run-command 'xfs_growfs /' \
  --root-password password:${root_password} \
  --hostname ${undercloud_name}.local \
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

# on the undercloud

## Undercloud installation
```
undercloud_hostname=queensa
hostnamectl set-hostname ${undercloud_hostname}.local
hostnamectl set-hostname --transient ${undercloud_hostname}.local
```
Get the undercloud ip and set the correct entries in /etc/hosts, ie:
```
undercloud_ip=192.168.122.52
echo ${undercloud_ip} ${undercloud_hostname}.local ${undercloud_hostname} >> /etc/hosts
```
### tripleo queens/current
```
tripeo_repos=`python -c 'import requests;r = requests.get("https://trunk.rdoproject.org/centos7-queens/current"); print r.text ' |grep python2-tripleo-repos|awk -F"href=\"" '{print $2}'|awk -F"\"" '{print $1}'`
yum install -y https://trunk.rdoproject.org/centos7-queens/current/${tripeo_repos}
tripleo-repos -b queens current
```

### OSP13-beta
Register with Satellite (can be done with CDN as well)
```
satellite_fqdn=satellite.englab.juniper.net
act_key=osp13
org=Juniper
yum localinstall -y http://${satellite_fqdn}/pub/katello-ca-consumer-latest.noarch.rpm
subscription-manager register --activationkey=${act_key} --org=${org}
```

```
yum install -y python-tripleoclient
su - stack
source stackrc
cp /usr/share/instack-undercloud/undercloud.conf.sample ~/undercloud.conf
openstack undercloud install
```

## forwarding
```
sudo iptables -A FORWARD -i br-ctlplane -o eth0 -j ACCEPT
sudo iptables -A FORWARD -i eth0 -o br-ctlplane -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
```

## set overcloud nameserver
```
openstack subnet set `openstack subnet show ctlplane-subnet -c id -f value` --dns-nameserver 8.8.8.8
```

## add an external api interface
```
sudo ip link add name vlan720 link br-ctlplane type vlan id 720
sudo ip addr add 10.2.0.254/24 dev vlan720
sudo ip link set dev vlan720 up
```

## Overcloud image download and upload to glance
```
mkdir images
cd images
```

### tripleo current

```
curl -O https://images.rdoproject.org/queens/rdo_trunk/current-tripleo-rdo/ironic-python-agent.tar
curl -O https://images.rdoproject.org/queens/rdo_trunk/current-tripleo-rdo/overcloud-full.tar
tar xvf ironic-python-agent.tar
tar xvf overcloud-full.tar
```

### OSP13-beta
```
sudo yum install rhosp-director-images rhosp-director-images-ipa
for i in /usr/share/rhosp-director-images/overcloud-full-latest-13.0.tar /usr/share/rhosp-director-images/ironic-python-agent-latest-13.0.tar ; do tar -xvf $i; done
```

```
cd
openstack overcloud image upload --image-path /home/stack/images/
```
## Ironic preparation

### create list with ironic nodes (adjust!!!)
```
cd
cat << EOM > ironic_list
52:54:00:16:54:d8 control-1-at-5b3s30 10.87.64.31 control 16235
52:54:00:2a:7d:99 compute-1-at-5b3s30 10.87.64.31 compute 16230
52:54:00:e0:54:b3 tsn-1-at-5b3s30 10.87.64.31 contrail-tsn 16231
52:54:00:d6:2b:03 contrail-controller-1-at-5b3s30 10.87.64.31 contrail-controller 16234
52:54:00:01:c1:af contrail-analytics-1-at-5b3s30 10.87.64.31 contrail-analytics 16233
52:54:00:4a:9e:52 contrail-analytics-database-1-at-5b3s30 10.87.64.31 contrail-analytics-database 16232
52:54:00:40:9e:13 control-1-at-centos 10.87.64.32 control 16235
52:54:00:1d:58:4d compute-dpdk-1-at-centos 10.87.64.32 compute-dpdk-1-at-centos 16230
52:54:00:6d:89:2d compute-2-at-centos 10.87.64.32 compute 16231
52:54:00:a8:46:5a contrail-controller-1-at-centos 10.87.64.32 contrail-controller 16234
52:54:00:b3:2f:7d contrail-analytics-1-at-centos 10.87.64.32 contrail-analytics 16233
52:54:00:59:e3:10 contrail-analytics-database-1-at-centos 10.87.64.32 contrail-analytics-database 16232
52:54:00:1d:8c:39 control-1-at-5b3s32 10.87.64.33 control 16235
52:54:00:9c:4b:bf compute-1-at-5b3s32 10.87.64.33 compute 16230
52:54:00:1d:a9:d9 compute-2-at-5b3s32 10.87.64.33 compute 16231
52:54:00:cd:59:92 contrail-controller-1-at-5b3s32 10.87.64.33 contrail-controller 16234
52:54:00:2f:81:1a contrail-analytics-1-at-5b3s32 10.87.64.33 contrail-analytics 16233
52:54:00:a1:4a:23 contrail-analytics-database-1-at-5b3s32 10.87.64.33 contrail-analytics-database 16232
EOM
```

### add overcloud nodes to ironic
```
ipmi_password=contrail123
ipmi_user=admin
while IFS= read -r line; do      mac=`echo $line|awk '{print $1}'`;   name=`echo $line|awk '{print $2}'`;   kvm_ip=`echo $line|awk '{print $3}'`;   profile=`echo $line|awk '{print $4}'`;   ipmi_port=`echo $line|awk '{print $5}'`;   uuid=`openstack baremetal node create --driver pxe_ipmitool --property cpus=4 --property memory_mb=16348 --property local_gb=100 --property cpu_arch=x86_64 --driver-info ipmi_username=${ipmi_user}  --driver-info ipmi_address=${kvm_ip} --driver-info ipmi_password=${ipmi_password} --driver-info ipmi_port=${ipmi_port} --name=${name} --property capabilities=profile:${profile},boot_option:local -c uuid -f value`;   openstack baremetal port create --node ${uuid} ${mac}; done < <(cat ironic_list)
openstack baremetal node list
DEPLOY_KERNEL=$(openstack image show bm-deploy-kernel -f value -c id)
DEPLOY_RAMDISK=$(openstack image show bm-deploy-ramdisk -f value -c id)
for i in `openstack baremetal node list -c UUID -f value`; do openstack baremetal node set $i --driver-info deploy_kernel=$DEPLOY_KERNEL --driver-info deploy_ramdisk=$DEPLOY_RAMDISK; done
for i in `openstack baremetal node list -c UUID -f value`; do openstack baremetal node show $i -c properties -f value; done
 ```

### introspect the nodes
```
for node in $(openstack baremetal node list -c UUID -f value) ; do openstack baremetal node manage $node ; done
openstack overcloud node introspect --all-manageable --provide
```

## create the flavors
```
for i in contrail-controller contrail-analytics contrail-database contrail-analytics-database; do   openstack flavor create $i --ram 4096 --vcpus 1 --disk 40;   openstack flavor set --property "capabilities:boot_option"="local" --property "capabilities:profile"="${i}" ${i}; done
```

## create tht template copy
```
cp -r /usr/share/openstack-tripleo-heat-templates/ tripleo-heat-templates
git clone https://github.com/juniper/contrail-tripleo-heat-templates -b stable/queens
cp -r contrail-tripleo-heat-templates/* tripleo-heat-templates/
```

## Tripleo container management

```
newgrp docker
```

### Get and upload the containers
#### tripleo

```
openstack overcloud container image prepare \
   --namespace docker.io/tripleoqueens \
#  --tag current-tripleo \
  --tag-from-label rdo_version \
  --output-env-file ~/docker_registry.yaml

tag=`grep "docker.io/tripleoqueens" docker_registry.yaml |tail -1 |awk -F":" '{print $3}'`

openstack overcloud container image prepare \
  --namespace docker.io/tripleoqueens \
  --tag ${tag} \
  --push-destination 192.168.24.1:8787 \
  --output-env-file ~/docker_registry.yaml \
  --output-images-file ~/overcloud_containers.yaml
```
openstack overcloud container image upload --config-file ~/overcloud_containers.yaml
#### OSP13-beta
```
openstack overcloud container image prepare \
 --push-destination=192.168.24.1:8787  \
 --tag-from-label {version}-{release} \
 --output-images-file=/home/stack/local_registry_images.yaml  \
 --namespace=registry.access.redhat.com/rhosp13-beta  \
 --prefix=openstack-  \
 --tag-from-label {version}-{release}  \
 --output-env-file=/home/stack/overcloud_images.yaml
```

```
openstack overcloud container image upload --config-file ~/overcloud_images.yaml
```
The last command takes a while.

## overcloud config files
### nic templates
```
tripleo-heat-templates/network/config/contrail/compute-nic-config.yaml
tripleo-heat-templates/network/config/contrail/contrail-controller-nic-config.yaml
tripleo-heat-templates/network/config/contrail/controller-nic-config.yaml
```
### overcloud network config
```
tripleo-heat-templates/environments/contrail/contrail-net.yaml
```
### overcloud service config
```
tripleo-heat-templates/environments/contrail/contrail-services.yaml
```
#### Patch tripleoclient for OSP13-beta
see https://review.openstack.org/#/c/564692/

### deploy the stack

##tripleo
```
openstack overcloud deploy --templates tripleo-heat-templates \
  -e docker_registry.yaml \
  -e tripleo-heat-templates/environments/network-isolation.yaml \
  -e tripleo-heat-templates/environments/docker.yaml \
  -e tripleo-heat-templates/environments/contrail/contrail-services.yaml \
  -e tripleo-heat-templates/environments/contrail/contrail-net.yaml \
  --roles-file tripleo-heat-templates/roles_data_contrail_aio.yaml
```
##  OSP13-beta 
openstack overcloud deploy --templates tripleo-heat-templates \
  -e overcloud_images.yaml \
  -e tripleo-heat-templates/environments/network-isolation.yaml \
  -e tripleo-heat-templates/environments/contrail/contrail-services.yaml \
  -e tripleo-heat-templates/environments/contrail/contrail-net.yaml \
  --roles-file tripleo-heat-templates/roles_data_contrail_aio.yaml

# quick VM start
```
source overcloudrc
curl -O http://download.cirros-cloud.net/0.3.5/cirros-0.3.5-x86_64-disk.img
openstack image create --container-format bare --disk-format qcow2 --file cirros-0.3.5-x86_64-disk.img cirros
openstack flavor create --public cirros --id auto --ram 64 --disk 0 --vcpus 1
openstack network create net1
openstack subnet create --subnet-range 1.0.0.0/24 --network net1 sn1
nova boot --image cirros --flavor cirros --nic net-id=`openstack network show net1 -c id -f value` --availability-zone nova:overcloud-novacompute-0.localdomain c1
nova list
```
