[< Infrastructure](infrastructure.md).................[Overcloud>](overcloud.md)

# Undercloud configuration and installation
This part describes the undercloud configuration and installation.   
Some commands are the same for OSP and Tripleo, some are different.    
Look out for ```### Tripleo``` or ```### OSP``` tag.
Do NOT execute both!     
## Undercloud installation
```
undercloud_name=`hostname -s`
undercloud_suffix=`hostname -d`
hostnamectl set-hostname ${undercloud_name}.${undercloud_suffix}
hostnamectl set-hostname --transient ${undercloud_name}.${undercloud_suffix}
```
Get the undercloud ip and set the correct entries in /etc/hosts, ie (assuming the mgmt nic is eth0):    
```
undercloud_ip=`ip addr sh dev eth0 |grep "inet " |awk '{print $2}' |awk -F"/" '{print $1}'`
echo ${undercloud_ip} ${undercloud_name}.${undercloud_suffix} ${undercloud_name} >> /etc/hosts
```

Get the repositories    
```
### Tripleo
tripeo_repos=`python -c 'import requests;r = requests.get("https://trunk.rdoproject.org/centos7-queens/current"); print r.text ' |grep python2-tripleo-repos|awk -F"href=\"" '{print $2}'|awk -F"\"" '{print $1}'`
yum install -y https://trunk.rdoproject.org/centos7-queens/current/${tripeo_repos}
tripleo-repos -b queens current
```

```
### OSP
### Register with Satellite (can be done with CDN as well)
satellite_fqdn=satellite.englab.juniper.net
act_key=osp13
org=Juniper
yum localinstall -y http://${satellite_fqdn}/pub/katello-ca-consumer-latest.noarch.rpm
subscription-manager register --activationkey=${act_key} --org=${org}
```

Install the undercloud    
```
yum install -y python-tripleoclient
su - stack
cp /usr/share/instack-undercloud/undercloud.conf.sample ~/undercloud.conf
openstack undercloud install
source stackrc
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

```
### Tripleo
curl -O https://images.rdoproject.org/queens/rdo_trunk/current-tripleo-rdo/ironic-python-agent.tar
curl -O https://images.rdoproject.org/queens/rdo_trunk/current-tripleo-rdo/overcloud-full.tar
tar xvf ironic-python-agent.tar
tar xvf overcloud-full.tar
```

```
### OSP
sudo yum install -y rhosp-director-images rhosp-director-images-ipa
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
for i in compute-dpdk contrail-controller contrail-analytics contrail-database contrail-analytics-database; do   openstack flavor create $i --ram 4096 --vcpus 1 --disk 40;   openstack flavor set --property "capabilities:boot_option"="local" --property "capabilities:profile"="${i}" ${i}; done
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
exit
su - stack
source stackrc
```

### Get and upload the containers

```
### Tripleo
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
```

```
### OSP
openstack overcloud container image prepare \
 --push-destination=192.168.24.1:8787  \
 --tag-from-label {version}-{release} \
 --output-images-file ~/local_registry_images.yaml  \
 --namespace=registry.access.redhat.com/rhosp13-beta  \
 --prefix=openstack-  \
 --tag-from-label {version}-{release}  \
 --output-env-file ~/overcloud_images.yaml
```

### Optional: adding Contrail containers to undercloud registry
setting Contrail container tag (default: latest)    
```
contrail_tag=rhel-master-132
```

##### Adding private unsecure registry to undercloud docker client
This step is only required if Contrail containers are not downloaded from hub.juniper.net or dockerhub but from a    
unsecure private registry (in this example ci-repo.englab.juniper.net:5000).        
```
contrail_registry=ci-repo.englab.juniper.net:5000
registry_string=`cat /etc/sysconfig/docker |grep INSECURE_REGISTRY |awk -F"INSECURE_REGISTRY=\"" '{print $2}'|tr "\"" " "`
registry_string="${registry_string} --insecure-registry ${contrail_registry}"
complete_string="INSECURE_REGISTRY=\"${registry_string}\""
echo ${complete_string}
if [[ `grep INSECURE_REGISTRY /etc/sysconfig/docker` ]]; then
  sudo sed -i "s/^INSECURE_REGISTRY=.*/${complete_string}/" /etc/sysconfig/docker
else
  sudo echo ${complete_string} >> /etc/sysconfig/docker
fi
sudo systemctl restart docker
```

##### Adding Contrail containers
```
contrail_tag=rhel-master-132
cat << EOM > contrail_container_list
DockerContrailAnalyticsAlarmGenImageName contrail-analytics-alarm-gen
DockerContrailAnalyticsApiImageName contrail-analytics-api
DockerContrailAnalyticsCollectorImageName contrail-analytics-collector
DockerContrailAnalyticsQueryEngineImageName contrail-analytics-query-engine
DockerContrailConfigApiImageName contrail-controller-config-api
DockerContrailConfigDevicemgrImageName contrail-controller-config-devicemgr
DockerContrailConfigSchemaImageName contrail-controller-config-schema
DockerContrailConfigSvcmonitorImageName contrail-controller-config-svcmonitor
DockerContrailControlControlImageName contrail-controller-control-control
DockerContrailControlDnsImageName contrail-controller-control-dns
DockerContrailControlNamedImageName contrail-controller-control-named
DockerContrailWebuiJobImageName contrail-controller-webui-job
DockerContrailWebuiWebImageName contrail-controller-webui-web
DockerContrailCassandraImageName contrail-external-cassandra
DockerContrailKafkaImageName contrail-external-kafka
DockerContrailRabbitmqImageName contrail-external-rabbitmq
DockerContrailZookeeperImageName contrail-external-zookeeper
DockerContrailNodeInitImageName contrail-node-init
DockerContrailNodemgrImageName contrail-nodemgr
DockerContrailNovaPluginImageName contrail-openstack-compute-init
DockerContrailHeatPluginImageName contrail-openstack-heat-init
DockerNeutronConfigImage contrail-openstack-neutron-init
DockerContrailVrouterAgentImageName contrail-vrouter-agent
DockerContrailVrouterKernelInitImageName contrail-vrouter-kernel-init
DockerContrailStatusImageName contrail-status
EOM

while IFS= read -r line
do
  thtImageName=`echo ${line} |awk '{print $1}'`
  contrailImageName=`echo ${line} |awk '{print $2}'`
  echo "- imagename: ${contrail_registry}/${contrailImageName}:${contrail_tag}" >> ~/local_registry_images.yaml
  echo "  push_destination: 192.168.24.1:8787" >> ~/local_registry_images.yaml
done < <(cat contrail_container_list)
```

### Upload containers
```
openstack overcloud container image upload --config-file ~/local_registry_images.yaml
```
The last command takes a while.


[< Infrastructure](infrastructure.md).................[Overcloud>](overcloud.md)
