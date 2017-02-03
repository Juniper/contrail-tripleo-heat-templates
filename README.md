## Undercloud preparation (on the KVM host)

# set password & subscription information
USER=
PASSWORD=
POOLID=
ROOTPASSWORD=
STACKPASSWORD=

# install basic packages
```
yum install -y libguestfs.x86_64 libguestfs-tools.noarch openvswitch virt-install virt-viewer
```

# get rhel7.3 kvm image
goto: https://access.redhat.com/downloads/content/69/ver=/rhel---7/7.3/x86_64/product-software    
download: KVM Guest Image    

# prepare networking
```
ovs-vsctl add-br brbm
cat << EOF > brbm.xml
<network>
  <name>brbm</name>
  <forward mode='bridge'/>
  <bridge name='brbm'/>
  <virtualport type='openvswitch'/>
</network>
EOF
virsh net-define brbm.xml
virsh net-start brbm
virsh net-autostart brbm
```

# prepare undercloud VM
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
  --run-command 'yum remove -y cloud-init'
  --selinux-relabel
cp undercloud.qcow2 /var/lib/libvirt/images/undercloud.qcow2
```

# install undercloud VM
```
virt-install --name undercloud \
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
  --console pty,target_type=virtio
```

# get undercloud ip
```
echo `virsh net-dhcp-leases default |grep undercloud |tail -1 |awk '{print $5}' | awk -F"/" '{print $1}'` > undercloudip
```

# ssh into undercloud
```
ssh stack@`cat undercloudip`
```

## Undercloud configuration

# create contrail repo
```
sudo mkdir /var/www/html/contrail
```

# get contrail
```
curl -o ~/contrail-install-packages_3.2.0.0-20-newton.tgz http://10.84.5.120/github-build/R3.2/LATEST/redhat70/newton/contrail-install-packages_3.2.1.0-20-newton.tgz
sudo tar zxvf ~/contrail-install-packages_3.2.0.0-20-newton.tgz -C /var/www/html/contrail/
```

# configure undercloud
```
cp /usr/share/instack-undercloud/undercloud.conf.sample ~/undercloud.conf
vi ~/undercloud.conf
```

# install undercloud openstack
```
openstack undercloud install
```

# source undercloud credentials
```
source ~/stackrc
```

# get overcloud images
```
sudo yum install rhosp-director-images rhosp-director-images-ipa
mkdir ~/images
cd ~/images
```

# upload overcloud images
```
for i in /usr/share/rhosp-director-images/overcloud-full-latest-10.0.tar /usr/share/rhosp-director-images/ironic-python-agent-latest-10.0.tar; do tar -xvf $i; done
openstack overcloud image upload --image-path /home/stack/images/
cd ~
```

# define nodes in instackenv.json    
(https://access.redhat.com/documentation/en/red-hat-openstack-platform/10/paged/director-installation-and-usage/chapter-5-configuring-basic-overcloud-requirements-with-the-cli-tools)
```
vi ~/instackenv.json
```

# import nodes
```
openstack baremetal import --json ~/instackenv.json
openstack baremetal configure boot
```

# node introspection
for node in $(openstack baremetal node list -c UUID -f value) ; do openstack baremetal node manage $node ; done
openstack overcloud node introspect --all-manageable --provide

# node profiling
```
for i in contrail-controller contrail-analytics contrail-database contrail-analytics-database contrail-tsn; do
  openstack flavor create $i --ram 4096 --vcpus 1 --disk 40
done
```

## configure overcloud

# get puppet modules
```
git clone https://github.com/Juniper/contrail-tripleo-puppet -b stable/newton ~/contrail-tripleo-puppet
git clone https://github.com/Juniper/puppet-contrail -b stable/newton ~/puppet-contrail
mkdir -p ~/usr/share/openstack-puppet/modules/tripleo
cp -r ~/contrail-tripleo-puppet/manifests ~/contrail-tripleo-puppet/lib ~/usr/share/openstack-puppet/modules/tripleo/
cp -r ~/puppet-contrail ~/usr/share/openstack-puppet/modules/contrail
tar czvf puppet-modules.tgz usr/
```

# upload puppet modules to swift
```
upload-swift-artifacts -f puppet-modules.tgz
```

# get tripleo-heat-templates
```
cp -r /usr/share/openstack-tripleo-heat-templates/ ~/tripleo-heat-templates
git clone https://github.com/Juniper/contrail-tripleo-heat-templates -b stable/newton
cp -r contrail-tripleo-heat-templates/environments/contrail ~/tripleo-heat-templates/environments
cp -r contrail-tripleo-heat-templates/puppet/services/network/* ~/tripleo-heat-templates/puppet/services/network
```

# contrail services (repo url etc.)
```
vi ~/tripleo-heat-templates/environments/contrail/contrail-services.yaml
```

# overcloud networking (if multi nic will be used only)
```
vi ~/tripleo-heat-templates/environments/contrail/contrail-net.yaml
vi ~/tripleo-heat-templates/environments/contrail/contrail-nic-config-compute.yaml
vi ~/tripleo-heat-templates/environments/contrail/contrail-nic-config.yaml
```

# static ip assignment
```
vi ~/tripleo-heat-templates/environments/contrail/ips-from-pool-all.yaml
```

# provide subscription mgr credentials (rhel_reg_password, rhel_reg_pool_id, rhel_reg_repos, rhel_reg_user and method)
```
vi ~/tripleo-heat-templates/extraconfig/pre_deploy/rhel-registration/environment-rhel-registration.yaml
```


## start overcloud installation

# single-nic:
```
openstack overcloud deploy --templates tripleo-heat-templates/ \
  --roles-file tripleo-heat-templates/environments/contrail/roles_data.yaml \
  -e tripleo-heat-templates/extraconfig/pre_deploy/rhel-registration/environment-rhel-registration.yaml \
  -e tripleo-heat-templates/extraconfig/pre_deploy/rhel-registration/rhel-registration-resource-registry.yaml \
  -e tripleo-heat-templates/environments/contrail/contrail-services.yaml \
  -e tripleo-heat-templates/environments/contrail/contrail-net-single.yaml \
  --libvirt-type qemu
```

# multi-nic:
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
