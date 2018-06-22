# vrouter_standard
NIC configuration:    
~/tripleo-heat-templates/config/network/contrail/compute-nic-bond-config.yaml   
```

```
~/tripleo-heat-templates/environments/contrail/contrai-net.yaml
```
resource_registry:
  OS::TripleO::Compute::Net::SoftwareConfig: ../../network/config/contrail/compute-nic-bond-config.yaml
```
~/tripleo-heat-templates/environments/contrail/contrai-services.yaml
```
parameter_defaults:
  ServiceNetMap:
    ContrailVrouterNetwork: tenant
  ContrailSettings:
    VROUTER_GATEWAY: 10.0.0.1
```
