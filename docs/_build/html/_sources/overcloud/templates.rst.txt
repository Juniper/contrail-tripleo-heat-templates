#########
Templates
#########

.. contents:: Table of Contents

The customization of the Overcloud is done in a set of different yaml templates

Network customization
=====================

In order to customize the network, different networks have to be defined and the
Overcloud nodes NIC layout has to be configured. Tripleo supports a flexible 
way of customizing the network. In this example the following networks are used:

+--------------+------+-------------------------+
| Network      | Vlan | Overcloud Nodes         |
+==============+======+=========================+
| provisioning |  -   | All                     | 
+--------------+------+-------------------------+
| internal_api | 710  | All                     |
+--------------+------+-------------------------+
| external_api | 720  | OpenStack CTRL          |
+--------------+------+-------------------------+
| storage      | 740  | OpenStack CTRL, Computes|
+--------------+------+-------------------------+
| storage_mgmt | 750  | OpenStack CTRL          |
+--------------+------+-------------------------+
| tenant       |  -   | Contrail CTRL, Computes |
+--------------+------+-------------------------+

Network activation in roles_data
--------------------------------

The networks must be activated per role in the roles_data file:

.. note:: vi ~/tripleo-heat-templates/roles_data_contrail_aio.yaml

  .. admonition:: OpenStack Controller

    ::

      ###############################################################################
      # Role: Controller                                                            #
      ###############################################################################
      - name: Controller
        description: |
          Controller role that has all the controler services loaded and handles
          Database, Messaging and Network functions.
        CountDefault: 1
        tags:
          - primary
          - controller
        networks:
          - External
          - InternalApi
          - Storage
          - StorageMgmt


  .. admonition:: Compute

    ::

      ###############################################################################
      # Role: Compute                                                               #
      ###############################################################################
      - name: Compute
        description: |
          Basic Compute Node role
        CountDefault: 1
        networks:
          - InternalApi
          - Tenant
          - Storage


  .. admonition:: Contrail Controller

    ::

      ###############################################################################
      # Role: ContrailController                                                    #
      ###############################################################################
      - name: ContrailController
        description: |
          ContrailController role that has all the Contrail controler services loaded
          and handles config, control and webui functions
        CountDefault: 1
        tags:
          - primary
          - contrailcontroller
        networks:
          - InternalApi
          - Tenant

  .. admonition:: Contrail DPDK

    ::

      ###############################################################################
      # Role: ContrailDpdk                                                          #
      ###############################################################################
      - name: ContrailDpdk
        description: |
          Contrail Dpdk Node role
        CountDefault: 0
        tags:
          - contraildpdk
        networks:
          - InternalApi
          - Tenant
          - Storage

  .. admonition:: Contrail SRIOV

    ::

      ###############################################################################
      # Role: ContrailSriov
      ###############################################################################
      - name: ContrailSriov
        description: |
          Contrail Sriov Node role
        CountDefault: 0
        tags:
          - contrailsriov
        networks:
          - InternalApi
          - Tenant
          - Storage

  .. admonition:: Contrail TSN

    ::

      ###############################################################################
      # Role: ContrailTsn
      ###############################################################################
      - name: ContrailTsn
        description: |
          Contrail Tsn Node role
        CountDefault: 0
        tags:
          - contrailtsn
        networks:
          - InternalApi
          - Tenant
          - Storage

Network interface configuration
-------------------------------

There are NIC configuration files per role.

.. note:: vi ~/tripleo-heat-templates/network/config/contrail

  .. admonition:: OpenStack Controller

    :doc:`nics/controller-nic-config.rst`
