
#1. Introduction
RedHat OpenStack Platform (OSP) provides an installer called Director (OSPD).    
OSPD is based on the OpenStack project TripleO (OOO - OpenStack on OpenStack).   
TripleO has the concept of undercloud and overcloud. The undercloud is an    
OpenStack installation which manages the deployment and lifecycle of the overcloud.    
The overcloud is the actual OpenStack installation hosting the user workloads.    
This document explains how Contrail installation is integrated into Director.    

#2. Problem statement
OSPD uses a combination of heat templates and puppet modules in order to deploy    
the overcloud. In order to integrate the Contrail deployment, Contrail based    
heat templates and puppet modules must be created.    

#3. Proposed solution
For integrating Contrail three new roles are defined:    
1. Contrail Controller    
2. Contrail Analytics    
3. Contrail Analytics Database    

Each role owns several services:    
- Contrail Controller:    
-- Contrail API
-- Contrail Control
-- Contrail Configuration Database
-- Contrail WebUI
-- Zookeeper

- Contrail Analytics:
-- Contrail Analytics

- Contrail Analytics Database:
-- Contrail Analytics Database
-- Kafka

##3.1 Alternatives considered
N/A    

##3.2 API schema changes
N/A    

##3.3 User workflow impact
Follow the Director installation manual on    
https://access.redhat.com/documentation/en-us/red_hat_openstack_platform/10/html/director_installation_and_usage/    
up to chapter 5.5. (CUSTOMIZING THE OVERCLOUD)    

### get puppet modules
```
mkdir -p ~/usr/share/openstack-puppet/modules
git clone https://github.com/Juniper/contrail-tripleo-puppet -b stable/newton ~/usr/share/openstack-puppet/modules/tripleo
git clone https://github.com/Juniper/puppet-contrail -b stable/newton ~/usr/share/openstack-puppet/modules/contrail
tar czvf puppet-modules.tgz usr/
```

### upload puppet modules to swift
```
upload-swift-artifacts -f puppet-modules.tgz
```

### get tripleo-heat-templates
```
cp -r /usr/share/openstack-tripleo-heat-templates/ ~/tripleo-heat-templates
git clone https://github.com/Juniper/contrail-tripleo-heat-templates -b stable/newton
cp -r contrail-tripleo-heat-templates/environments/contrail ~/tripleo-heat-templates/environments
cp -r contrail-tripleo-heat-templates/puppet/services/network/* ~/tripleo-heat-templates/puppet/services/network
```

### contrail services (repo url etc.)
```
vi ~/tripleo-heat-templates/environments/contrail/contrail-services.yaml
```

### overcloud networking examples
#### multi-nic
```
vi ~/tripleo-heat-templates/environments/contrail/contrail-net.yaml
vi ~/tripleo-heat-templates/environments/contrail/contrail-nic-config-compute.yaml
vi ~/tripleo-heat-templates/environments/contrail/contrail-nic-config.yaml
```
#### multi-nic with bond and vlan
```
vi ~/tripleo-heat-templates/environments/contrail/contrail-net-bond-vlan.yaml
vi ~/tripleo-heat-templates/environments/contrail/contrail-nic-config-compute-bond-vlan.yaml
vi ~/tripleo-heat-templates/environments/contrail/contrail-nic-config-vlan.yaml
```
#### single-nic
```
vi ~/tripleo-heat-templates/environments/contrail/contrail-net-single.yaml
vi ~/tripleo-heat-templates/environments/contrail/contrail-nic-config-compute-single.yaml
vi ~/tripleo-heat-templates/environments/contrail/contrail-nic-config-single.yaml
```

### static ip assignment
```
vi ~/tripleo-heat-templates/environments/contrail/ips-from-pool-all.yaml
```

## Overcloud installation

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

### multi-nic
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

### multi-nic with bond and vlan
```
openstack overcloud deploy --templates tripleo-heat-templates/ \
  --roles-file tripleo-heat-templates/environments/contrail/roles_data.yaml \
  -e tripleo-heat-templates/environments/puppet-pacemaker.yaml \
  -e tripleo-heat-templates/environments/contrail/contrail-services.yaml \
  -e tripleo-heat-templates/environments/contrail/network-isolation.yaml \
  -e tripleo-heat-templates/environments/contrail/contrail-net-bond-vlan.yaml \
  -e tripleo-heat-templates/environments/contrail/ips-from-pool-all.yaml \
  -e tripleo-heat-templates/environments/network-management.yaml \
  -e tripleo-heat-templates/extraconfig/pre_deploy/rhel-registration/environment-rhel-registration.yaml \
  -e tripleo-heat-templates/extraconfig/pre_deploy/rhel-registration/rhel-registration-resource-registry.yaml \
  --libvirt-type qemu
```


##3.4 UI changes
N/A    

##3.5 Notification impact
N/A    


#4. Implementation
##4.1 Work items
####Describe changes needed for different components such as Controller, Analytics, Agent, UI. 
####Add subsections as needed.

#5. Performance and scaling impact
##5.1 API and control plane
N/A    

##5.2 Forwarding performance
N/A    

#6. Upgrade
N/A    

#7. Deprecations
N/A    

#8. Dependencies
####Describe dependent features or components.

#9. Testing
##9.1 Unit tests
##9.2 Dev tests
##9.3 System tests

#10. Documentation Impact

#11. References
https://access.redhat.com/documentation/en/red-hat-openstack-platform/    
https://docs.openstack.org/developer/tripleo-docs/index.html
