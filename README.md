# Undercloud preparation (on the KVM host)

## set password & subscription information
```
export USER=<YOUR_RHEL_SUBS_USER> 
export PASSWORD=<YOUR_RHEL_SUBS_PWD>
export POOLID=<YOUR_RHEL_POOL_ID>
export ROOTPASSWORD=<UNDERCLOUD_ROOT_PWD> # choose a root user password
export STACKPASSWORD=<STACK_USER_PWD> # choose a stack user password
```

## install basic packages
```
yum install -y libguestfs libguestfs-tools openvswitch virt-install kvm libvirt libvirt-python python-virtinst
```

## start libvirtd & ovs
```
systemctl start libvirtd
systemctl start openvswitch
```

## create and become stack user
```
useradd -G libvirt stack
echo $STACKPASSWORD |passwd stack --stdin
echo "stack ALL=(root) NOPASSWD:ALL" | sudo tee -a /etc/sudoers.d/stack
chmod 0440 /etc/sudoers.d/stack
su - stack
```
## create ssh key
```
ssh-keygen -t dsa
```

## adjust permissions
```
sudo chgrp -R libvirt /var/lib/libvirt/images
sudo chmod g+rw /var/lib/libvirt/images
```

## get rhel 7.3 kvm image
goto: https://access.redhat.com/downloads/content/69/ver=/rhel---7/7.3/x86_64/product-software    
download: KVM Guest Image    

## prepare networking
```
sudo ovs-vsctl add-br brbm
cat << EOF > brbm.xml
<network>
  <name>brbm</name>
  <forward mode='bridge'/>
  <bridge name='brbm'/>
  <virtualport type='openvswitch'/>
</network>
EOF
sudo virsh net-define brbm.xml
sudo virsh net-start brbm
sudo virsh net-autostart brbm
```
## for multi-nic add the following networks:
```
sudo ovs-vsctl add-br br-int-api
sudo ovs-vsctl add-br br-mgmt
cat << EOF > br-int-api.xml
<network>
  <name>br-int-api</name>
  <forward mode='bridge'/>
  <bridge name='br-int-api'/>
  <virtualport type='openvswitch'/>
</network>
EOF
cat << EOF > br-mgmt.xml
<network>
  <name>br-mgmt</name>
  <forward mode='bridge'/>
  <bridge name='br-mgmt'/>
  <virtualport type='openvswitch'/>
</network>
EOF
sudo virsh net-define br-int-api.xml
sudo virsh net-start br-int-api
sudo virsh net-autostart br-int-api
sudo virsh net-define br-mgmt.xml
sudo virsh net-start br-mgmt
sudo virsh net-autostart br-mgmt

```

## define ironic nodes (single nic)
```
num=0
for i in compute control contrail-controller contrail-analytics contrail-analytics-database contrail-tsn
do
  num=$(expr $num + 1)
  qemu-img create -f qcow2 /var/lib/libvirt/images/${i}_${num}.qcow2 40G
  sudo virsh define /dev/stdin <<EOF
$(sudo virt-install --name ${i}_$num   --disk /var/lib/libvirt/images/${i}_${num}.qcow2   --vcpus=4   --ram=16348   --network network=brbm,model=virtio,mac=de:ad:be:ef:ba:0$num   --virt-type kvm   --import   --os-variant rhel7   --serial pty   --console pty,target_type=virtio --print-xml)
EOF
done
```
## define ironic nodes (multi nic)
```
num=0
for i in compute control contrail-controller contrail-analytics contrail-analytics-database contrail-tsn
do
  num=$(expr $num + 1)
  qemu-img create -f qcow2 /var/lib/libvirt/images/${i}_${num}.qcow2 40G
  sudo virsh define /dev/stdin <<EOF
$(sudo virt-install --name ${i}_$num   --disk /var/lib/libvirt/images/${i}_${num}.qcow2   --vcpus=4   --ram=16348   --network network=brbm,model=virtio,mac=de:ad:be:ef:ba:0$num --network network=br-int-api,model=virtio,mac=de:ad:be:ef:bb:0$num --network network=br-mgmt,model=virtio,mac=de:ad:be:ef:bc:0$num --virt-type kvm   --import   --os-variant rhel7   --serial pty   --console pty,target_type=virtio --print-xml)
EOF
done
```

## prepare undercloud VM
```
export LIBGUESTFS_BACKEND=direct
qemu-img create -f qcow2 undercloud.qcow2 100G
virt-resize --expand /dev/sda1 rhel-guest-image-7.3-35.x86_64.qcow2 undercloud.qcow2
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
sudo cp undercloud.qcow2 /var/lib/libvirt/images/undercloud.qcow2
```

## install undercloud VM (single nic)
```
sudo virt-install --name undercloud \
  --disk /var/lib/libvirt/images/undercloud.qcow2 \
  --vcpus=4 \
  --ram=16348 \
  --network network=default,model=virtio \
  --network network=brbm,model=virtio \
  --virt-type kvm \
  --import \
  --os-variant rhel7 \
  --graphics vnc \
  --serial pty \
  --noautoconsole \
  --console pty,target_type=virtio
```

## install undercloud VM (multi nic)
```
sudo virt-install --name undercloud \
  --disk /var/lib/libvirt/images/undercloud.qcow2 \
  --vcpus=4 \
  --ram=16348 \
  --network network=default,model=virtio \
  --network network=brbm,model=virtio \
  --network network=br-int-api,model=virtio \
  --virt-type kvm \
  --import \
  --os-variant rhel7 \
  --graphics vnc \
  --serial pty \
  --noautoconsole \
  --console pty,target_type=virtio
```

## get undercloud ip (depending on the number of attempts their might be multiple leases)
```
sudo virsh net-dhcp-leases default |grep undercloud
```

## ssh into undercloud
```
ssh stack@<UNDERCLOUD_IP>
```

# Undercloud configuration

## configure undercloud
```
cp /usr/share/instack-undercloud/undercloud.conf.sample ~/undercloud.conf
vi ~/undercloud.conf
```

## install undercloud openstack
```
openstack undercloud install
```

## source undercloud credentials
```
source ~/stackrc
```

## get overcloud images
```
sudo yum install rhosp-director-images rhosp-director-images-ipa
mkdir ~/images
cd ~/images
```

## upload overcloud images
```
for i in /usr/share/rhosp-director-images/overcloud-full-latest-10.0.tar /usr/share/rhosp-director-images/ironic-python-agent-latest-10.0.tar; do tar -xvf $i; done
openstack overcloud image upload --image-path /home/stack/images/
cd ~
```

## create contrail repo
```
sudo mkdir /var/www/html/contrail
```

## get contrail
```
curl -o ~/contrail-install-packages_3.2.0.0-21-newton.tgz http://10.84.5.120/github-build/R3.2/LATEST/redhat70/newton/contrail-install-packages_3.2.1.0-21-newton.tgz
sudo tar zxvf ~/contrail-install-packages_3.2.0.0-21-newton.tgz -C /var/www/html/contrail/
```

## Ironic Node definiton

## Option 1
### define nodes in instackenv.json (option 1)   
(https://access.redhat.com/documentation/en/red-hat-openstack-platform/10/paged/director-installation-and-usage/chapter-5-configuring-basic-overcloud-requirements-with-the-cli-tools)
```
vi ~/instackenv.json
```

### import nodes
```
openstack baremetal import --json ~/instackenv.json
```

## Option 2
### define nodes with CLI 
```
ssh_address=IP_OF_KVM_HOST
ssh_user=stack
ssh_key=SSH_KEY_OF_SSH_USER (/home/stack/.ssh/id_dsa on kvm host)
num=0
for i in compute control contrail-controller contrail-analytics contrail-database contrail-analytics-database contrail-tsn
do
  num=$(expr $num + 1)
  ironic node-create -d pxe_ssh -p cpus=4 -p memory_mb=16348 -p local_gb=40 -p cpu_arch=x86_64 -i ssh_username=${ssh_user} -i ssh_virt_type=virsh -i ssh_address=${ssh_address} -i ssh_key_contents=${ssh_key} -n ${i}-${num} -p capabilities=profile:${i} 
  ironic port-create -a "de:ad:be:ef:ba:0${num}" -n `openstack baremetal node show ${i}-${num} -c uuid -f value`
done
```

## configure boot mode
```
openstack baremetal configure boot
```

## node introspection
```
for node in $(openstack baremetal node list -c UUID -f value) ; do openstack baremetal node manage $node ; done
openstack overcloud node introspect --all-manageable --provide
```

## node profiling
```
for i in contrail-controller contrail-analytics contrail-database contrail-analytics-database contrail-tsn; do
  openstack flavor create $i --ram 4096 --vcpus 1 --disk 40
  openstack flavor set --property "capabilities:boot_option"="local" --property "capabilities:profile"="${i}" ${i}
done
```

# configure overcloud

## get puppet modules
```
mkdir -p ~/usr/share/openstack-puppet/modules
git clone https://github.com/Juniper/contrail-tripleo-puppet -b stable/newton ~/usr/share/openstack-puppet/modules/tripleo
git clone https://github.com/Juniper/puppet-contrail -b stable/newton ~/usr/share/openstack-puppet/modules/contrail
tar czvf puppet-modules.tgz usr/
```

## upload puppet modules to swift
```
upload-swift-artifacts -f puppet-modules.tgz
```

## get tripleo-heat-templates
```
cp -r /usr/share/openstack-tripleo-heat-templates/ ~/tripleo-heat-templates
git clone https://github.com/Juniper/contrail-tripleo-heat-templates -b stable/newton
cp -r contrail-tripleo-heat-templates/environments/contrail ~/tripleo-heat-templates/environments
cp -r contrail-tripleo-heat-templates/puppet/services/network/* ~/tripleo-heat-templates/puppet/services/network
```

## contrail services (repo url etc.)
```
vi ~/tripleo-heat-templates/environments/contrail/contrail-services.yaml
```

## overcloud networking
### multi-nic
```
vi ~/tripleo-heat-templates/environments/contrail/contrail-net.yaml
vi ~/tripleo-heat-templates/environments/contrail/contrail-nic-config-compute.yaml
vi ~/tripleo-heat-templates/environments/contrail/contrail-nic-config.yaml
```
### single-nic
```
vi ~/tripleo-heat-templates/environments/contrail/contrail-net-single.yaml
vi ~/tripleo-heat-templates/environments/contrail/contrail-nic-config-compute-single.yaml
vi ~/tripleo-heat-templates/environments/contrail/contrail-nic-config-single.yaml
```

## static ip assignment
```
vi ~/tripleo-heat-templates/environments/contrail/ips-from-pool-all.yaml
```

## provide subscription mgr credentials (rhel_reg_password, rhel_reg_pool_id, rhel_reg_repos, rhel_reg_user and method)
```
vi ~/tripleo-heat-templates/extraconfig/pre_deploy/rhel-registration/environment-rhel-registration.yaml
```
## set overcloud nameserver
```
neutron subnet-show
neutron subnet-update <SUBNET-UUID> --dns-namserver NAMESERVER_IP
```

# start overcloud installation

## single-nic
```
openstack overcloud deploy --templates tripleo-heat-templates/ \
  --roles-file tripleo-heat-templates/environments/contrail/roles_data.yaml \
  -e tripleo-heat-templates/extraconfig/pre_deploy/rhel-registration/environment-rhel-registration.yaml \
  -e tripleo-heat-templates/extraconfig/pre_deploy/rhel-registration/rhel-registration-resource-registry.yaml \
  -e tripleo-heat-templates/environments/contrail/contrail-services.yaml \
  -e tripleo-heat-templates/environments/contrail/contrail-net-single.yaml \
  --libvirt-type qemu
```

## multi-nic
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
