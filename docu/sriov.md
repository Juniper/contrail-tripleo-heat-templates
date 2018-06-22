```
openstack image create --container-format bare --disk-format qcow2 --file bionic-server-cloudimg-amd64-mod.img ubuntu
openstack flavor create --public ubuntu --id auto --ram 1024 --disk 0 --vcpus 1
openstack network create --provider-physical-network sriov1 --provider-segment 3211 sriov-vn
openstack subnet create --subnet-range 172.16.99.0/24 --network sriov-vn sriov-sn
openstack port create --network sriov-vn --vnic-type direct --fixed-ip subnet=sriov-sn,ip-address=172.16.99.10 sriov-port-1
openstack server create --flavor ubuntu --image ubuntu --port sriov-port-1 --availability-zone nova:overcloud-contrailsriov-0.localdomain ubuntu-sriov-1 nova:overcloud-contrailsriov-0.localdomain ubuntu-sriov-1
```
