#!/bin/bash

CONTRAIL_IMAGE_PREFIX=${CONTRAIL_IMAGE_PREFIX:-'contrail-'}
CONTRAIL_NEW_IMAGE_TAG=${CONTRAIL_NEW_IMAGE_TAG:-'latest'}

sudo docker images --format 'table {{.Repository}}:{{.Tag}}' | grep "$CONTRAIL_IMAGE_PREFIX" | sed -e "s/:[^:]\+$/:${CONTRAIL_NEW_IMAGE_TAG}/" | sort -u >/tmp/docker_images.list
echo Pulling new docker images
for image in $(cat /tmp/docker_images.list); do
    sudo docker pull $image
done
