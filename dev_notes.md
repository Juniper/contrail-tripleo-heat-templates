# on all KVM hosts

## prepare virtual bmc (on all hosts hosting overcloud nodes)

```
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

```
qemu-img create -f qcow2 /var/lib/libvirt/images/queensY.qcow2 100G
virt-resize --expand /dev/sda1 /root/rhel-server-7.4-x86_64-kvm.qcow2 /var/lib/libvirt/images/queensY.qcow2
virt-customize  -a /var/lib/libvirt/images/queensY.qcow2 \
  --run-command 'xfs_growfs /' \
  --root-password password:contrail123 \
  --hostname queensY.local \
  --run-command 'useradd stack' \
  --password stack:password:contrail123 \
  --run-command 'echo "stack ALL=(root) NOPASSWD:ALL" | tee -a /etc/sudoers.d/stack' \
  --chmod 0440:/etc/sudoers.d/stack \
  --run-command 'sed -i "s/PasswordAuthentication no/PasswordAuthentication yes/g" /etc/ssh/sshd_config' \
  --run-command 'systemctl enable sshd' \
  --run-command 'yum remove -y cloud-init' \
  --selinux-relabel
```

virsh define is missing
^^^^^^^^^^^^^^^^^^^^^^^

## get undercloud ip and log into it
```
undercloud_ip=`virsh domifaddr queensY |grep ipv4 |awk '{print $4}' |awk -F"/" '{print $1}'`
ssh ${undercloud_ip}
```

# on the undercloud

## Undercloud configuration
```
hostnamectl set-hostname queensZ.local
hostnamectl set-hostname --transient queensZ.local
vi /etc/hosts
yum localinstall -y http://satellite.englab.juniper.net/pub/katello-ca-consumer-latest.noarch.rpm
subscription-manager register --activationkey=rhel-7-osp --org=Juniper
yum install -y yum-utils
yum-config-manager --enable rhelosp-rhel-7-server-opt
tripeo_repos=`python -c 'import requests;r = requests.get("https://trunk.rdoproject.org/centos7-queens/current"); print r.text ' |grep python2-tripleo-repos|awk -F"href=\"" '{print $2}'|awk -F"\"" '{print $1}'`
yum install -y https://trunk.rdoproject.org/centos7-queens/current/${tripeo_repos}
tripleo-repos current-tripleo-dev
yum install -y python-tripleoclient
su - stack
source stackrc
cp /usr/share/instack-undercloud/undercloud.conf.sample ~/undercloud.conf
openstack undercloud install
```

## Overcloud image prep, build and upload
```
export OS_YAML="/usr/share/openstack-tripleo-common/image-yaml/overcloud-images-rhel7.yaml"
export DIB_YUM_REPO_CONF="/etc/yum.repos.d/delorean*"
export DIB_LOCAL_IMAGE=rhel-server-7.4-x86_64-kvm.qcow2
export REG_METHOD=satellite
export REG_SAT_URL="http://satellite.englab.juniper.net"
export REG_ORG="Juniper"
export REG_ACTIVATION_KEY="rhel-7-osp"
export REG_REPOS="rhel-7-server-rpms rhel-7-server-extras-rpms rhel-ha-for-rhel-7-server-rpms rhel-7-server-optional-rpms"
openstack overcloud image build --config-file /usr/share/openstack-tripleo-common/image-yaml/overcloud-images.yaml --config-file $OS_YAML
source stackrc
openstack overcloud image upload
```
## Ironic preparation

### create list with ironic nodes (adjust!!!)

```
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
### for stable
```
tripleo_tag=current-tripleo-rdo
```

### for testing
```
tripleo_tag=tripleo-ci-testing
```
### Get and upload the containers
```
tag=`openstack overcloud container image tag discover \
     --image trunk.registry.rdoproject.org/master/centos-binary-base:${tripleo_tag} \
     --tag-from-label rdo_version`

openstack overcloud container image prepare \
  --namespace trunk.registry.rdoproject.org/master \
  --tag ${tag} \
  --push-destination 192.168.24.1:8787 \
  --output-env-file ~/docker_registry.yaml \
  --output-images-file ~/overcloud_containers.yaml
openstack overcloud container image upload --config-file ~/overcloud_containers.yaml
```

## Create the roles
```
cd tripleo-heat-templates
openstack overcloud roles generate -o roles_data_contrail_aio.yaml --roles-path roles Controller Compute ContrailAIO
```
#remove tenant nw from controller role (vi roles_data_contrail_aio.yaml)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

## Configure the overcloud services
### nic templates
```
vi tripleo-heat-templates/network/config/contrail/compute-nic-config.yaml
vi tripleo-heat-templates/network/config/contrail/contrail-controller-nic-config.yaml
vi controller-nic-config.yaml
```

### contrail services config
```
vi tripleo-heat-templates/environments/contrail/contrail-services.yaml
```

### contrail net config
```
tripleo-heat-templates/environments/contrail/contrail-net.yaml
```


## deploy the stack
```
openstack overcloud deploy --templates tripleo-heat-templates \
  -e docker_registry.yaml \
  -e tripleo-heat-templates/environments/network-isolation.yaml \
  -e tripleo-heat-templates/environments/docker.yaml \
  -e tripleo-heat-templates/extraconfig/pre_deploy/rhel-registration/environment-rhel-registration.yaml \
  -e tripleo-heat-templates/environments/contrail/contrail-services.yaml \
  -e tripleo-heat-templates/environments/contrail/contrail-net.yaml \
  --roles-file tripleo-heat-templates/roles_data_contrail_aio.yaml
```

# nova patch (might not be needed)
```
docker exec -it -u root nova_compute bash
yum install -y patch
cd /usr/lib/python2.7/site-packages/
curl -O https://github.com/openstack/nova/commit/5a646d82bad6a71da28296e3ab06dc5ce2c0f716.patch
patch -f -p1 < 5a646d82bad6a71da28296e3ab06dc5ce2c0f716.patch
exit
docker restart nova_compute
```

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
