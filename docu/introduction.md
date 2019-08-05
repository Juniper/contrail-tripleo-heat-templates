# Introduction

This guide will explain the deployment of Contrail/Tungsten Fabric with RHOSP/RDO using Tripleo/RHOSPd.    
The guide is split into three main chapters:    

1. [Infrastructure preparation](infrastructure.md)
2. [Undercloud configuration and installation](undercloud.md)
3. [Overcloud configuration and installation](overcloud.md)

## Supported software version combinations
Currently the following combinations of Operating System/OpenStack/Deployer/Contrail are supported:

| Operating System  | OpenStack         | Deployer              | Contrail               |
| ----------------- | ----------------- | --------------------- | ---------------------- |
| RHEL 7.6          | OSP14             | OSPd14                | Contrail 5.1           |
| CentOS 7.6        | RDO stable/rocky  | tripleo stable/rocky  | Tungsten Fabric latest |
