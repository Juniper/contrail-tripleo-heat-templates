# For TripleO only. For testing purposes only.
# Remote computes support (subclusters).
TODO: consider another repo for this ansible

1. Define subclusters configurations in config/cluster.yaml

2. Setup undercloud node

  ```bash
  ansible-playbook -i inventory playbooks/configure_undercloud.yml
  ```

3. Configure dhcp relay manually

(see https://docs.openstack.org/tripleo-docs/latest/install/advanced_deployment/routed_spine_leaf_network.html for details)

4. Prepare tripleo heat templates

  ```bash
  ansible-playbook -i inventory playbooks/configure_tht.yml
  ```

6. Create overcloud nodes manually (potantionally can be automated)

7. Prepare overcloud nodes (set physical-network for ports and nodes capabilities for scheduling)

  ```bash
  ansible-playbook -i inventory playbooks/configure_overcloud_nodes.yml
  ```

8. deploy overcloud with included via '-e' parameter generated env files from working dir
(ususally /home/stack/):

- contrail-roles.yaml
- contrail-net.yaml
- contrail-nodes.yaml
- contrail-scheduler-hints.yaml


# Links:

- https://docs.openstack.org/tripleo-docs/latest/install/advanced_deployment/routed_spine_leaf_network.html
- https://access.redhat.com/documentation/en-us/red_hat_openstack_platform/13/pdf/spine_leaf_networking/Red_Hat_OpenStack_Platform-13-Spine_Leaf_Networking-en-US.pdf