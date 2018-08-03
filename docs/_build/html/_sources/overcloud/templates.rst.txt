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
| storage      | 740  | OpenStack CTRL          |
+--------------+------+-------------------------+
| storage_mgmt | 750  | OpenStack CTRL          |
+--------------+------+-------------------------+
| tenant       |  -   | Contrail CTRL, Computes |
+--------------+------+-------------------------+

Network activation in roles_data
--------------------------------

The networks must be activated per role in the roles_data file:

.. note::

  .. admonition:: OpenStack Controller

    ::

      vi ~/tripleo-heat-templates
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
