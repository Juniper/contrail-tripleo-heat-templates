##############
Infrastructure
##############

.. contents:: Table of Contents

There are many different ways on how to create the infrastructure providing
the control plane elements. In this example all control plane functions
are provided as Virtual Machines hosted on KVM hosts

- KVM 1:
  Undercloud

- KVM 2:
  OpenStack Controller 1
  Contrail Controller 1

- KVM 3:
  OpenStack Controller 2
  Contrail Controller 2

- KVM 4:
  OpenStack Controller 3
  Contrail Controller 3

Sample topology
===============

Layer 1
-------


bla::

        +-------------------------------+
        |KVM host 3                     |
      +-------------------------------+ |
      |KVM host 2                     | |
     +------------------------------+ | |
     |KVM host 1                    | | |
     |  +-------------------------+ | | |
     |  |  Contrail Controller 1  | | | |
     | ++-----------------------+ | | | |      +----------------+
     | | OpenStack Controller 1 | | | | |      |Compute Node N  |
     | |                        | | | | |    +----------------+ |
     | | +-----+        +-----+ +-+ | | |    |Compute Node 2  | |
     | | |VNIC1|        |VNIC2| |   | | |  +----------------+ | |
     | +----+--------------+----+   | | |  |Compute Node 1  | | |
     |      |              |        | | |  |                | | |
     |    +-+-+          +-+-+      | | |  |                | | |
     |    |br0|          |br1|      | | |  |                | | |
     |    +-+-+          +-+-+      | +-+  |                | | |
     |      |              |        | |    |                | | |
     |   +--+-+          +-+--+     +-+    | +----+  +----+ | +-+
     |   |NIC1|          |NIC2|     |      | |NIC1|  |NIC2| +-+
     +------+--------------+--------+      +---+-------+----+
            |              |                   |       |
     +------+--------------+-------------------+-------+--------+
     |                                                          |
     |                          Switch                          |
     +----------------------------------------------------------+
