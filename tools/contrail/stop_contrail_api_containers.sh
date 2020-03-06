#!/bin/bash


#list containers that must be stopped before update procedure
STOP_CONTAINERS=${STOP_CONTAINERS:-'contrail_config_api contrail_analytics_api'}


#Detecting containers to stop
for container in $STOP_CONTAINERS; do
    check=$(sudo docker ps --format '{{.Names}}' | grep -c "$container")
    if [ $check -gt 0 ]; then
       echo Found container $container. Stopping
       sudo docker stop $container
    fi
done

