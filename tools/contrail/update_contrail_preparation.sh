#!/bin/bash

my_file="$(readlink -e "$0")"
my_dir="$(dirname $my_file)"

#New contrail version
CONTRAIL_NEW_IMAGE_TAG=${CONTRAIL_IMAGE_TAG:-'latest'}

#Prefix for all contrail containers
CONTRAIL_IMAGE_PREFIX=${CONTRAIL_IMAGE_PREFIX:-'contrail-'}

#Containers which must be stopped before update procedure
STOP_CONTAINERS=${STOP_CONTAINERS:-'contrail_config_api contrail_analytics_api'}

SSH_USER=heat-admin
#Specific identity key can be specified in SSH_OPTIONS
#SSH_OPTIONS='-i ~/.ssh/id_rsa -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
SSH_OPTIONS='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'


#Running scripts on the nodes
#Pull new images on the nodes
for ip_addr in $(openstack server list -f value -c Networks | cut -d '=' -f 2); do
    echo "node: ${ip_addr}  Pulling new docker images:"
    scp ${SSH_OPTIONS} $my_dir/pull_new_contrail_images.sh ${SSH_USER}@${ip_addr}:/tmp/
    ssh ${SSH_OPTIONS} ${SSH_USER}@${ip_addr} CONTRAIL_IMAGE_PREFIX=${CONTRAIL_IMAGE_PREFIX} CONTRAIL_NEW_IMAGE_TAG=${CONTRAIL_NEW_IMAGE_TAG} /tmp/pull_new_contrail_images.sh
done

#Stoping config_api/analytics_api containers
echo STOPPING CONTRAIL API CONTAINERS
for ip_addr in $(openstack server list -f value -c Networks | cut -d '=' -f 2); do
    echo "Node: ${ip_addr}  Stopping contrail api containers"
    STOP_CONTAINERS_ESC=$(echo $STOP_CONTAINERS | sed -e 's/ /\\ /g')
    scp ${SSH_OPTIONS} $my_dir/stop_contrail_api_containers.sh ${SSH_USER}@${ip_addr}:/tmp/
    ssh ${SSH_OPTIONS} ${SSH_USER}@${ip_addr} STOP_CONTAINERS="${STOP_CONTAINERS_ESC}" /tmp/stop_contrail_api_containers.sh
done

