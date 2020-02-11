#!/bin/bash


#list containers that must be stopped before update procedure
STOP_CONTAINERS=${STOP_CONTAINERS:-'contrail_config_api contrail_analytics_api'}

echo Stopping contrail config services:
sudo docker stop $STOP_CONTAINERS
