#!/bin/bash


CONTRAIL_CURRENT_IMAGE_TAG=2020-01-26
#CONTRAIL_NEW_IMAGE_TAG=${CONTRAIL_IMAGE_TAG:-'latest'}
CONTRAIL_NEW_IMAGE_TAG=latest

SSH_USER=heat-admin
#SSH_OPTIONS='-i ~/.ssh/id_rsa'


#Use command openstack flavor list for get list of your flavors
FLAVORS=(contrail-controller compute)

#list containers that must be stopped before update procedure
declare -A STOP_CONTAINER=( ["contrail-controller"]="contrail_config_api contrail_config_nodemgr contrail_config_schema contrail_config_svc_monitor contrail_config_device_manager contrail_analytics_api contrail_analytics_nodemgr contrail_analytics_collector")


#Creating scripts for every flavor
for flavor in ${FLAVORS[@]}; do
    echo Creating script /tmp/${flavor}_update.sh;
    cat <<EOF > /tmp/${flavor}_update_images.sh
#!/bin/bash
sudo docker images --format 'table {{.Repository}}:{{.Tag}}' | egrep "contrail.*:${CONTRAIL_CURRENT_IMAGE_TAG}" | sed -e s/:${CONTRAIL_CURRENT_IMAGE_TAG}\$/:${CONTRAIL_NEW_IMAGE_TAG}/ | grep -v IMAGE >/tmp/docker_images.list
echo Pulling new docker images
for image in \$(cat /tmp/docker_images.list); do
    sudo docker pull \$image
done
EOF
    chmod 755 /tmp/${flavor}_update_images.sh
    if [[ ! -z ${STOP_CONTAINER["$flavor"]+x} ]]; then
        cat <<EOF > /tmp/${flavor}_stop_containers.sh
echo Stopping contrail config services:
sudo docker stop contrail_config_api contrail_config_nodemgr contrail_config_schema contrail_config_svc_monitor contrail_config_device_manager contrail_analytics_api contrail_analytics_nodemgr contrail_analytics_collector
EOF
        chmod 755 /tmp/${flavor}_stop_containers.sh
    fi
done

#Running scripts on the nodes
#Pull new images on the nodes
for flavor in ${FLAVORS[@]}; do
    echo "======= flavor: ${flavor} ======="
    for ip_addr in $(openstack server list --flavor ${flavor} -f value -c Networks | cut -d '=' -f 2); do
        echo "node: ${ip_addr}  Pulling new docker images:"
        scp ${SSH_OPTIONS} /tmp/${flavor}_update_images.sh ${SSH_USER}@${ip_addr}:/tmp/contrail_update_images.sh
        ssh ${SSH_OPTIONS} ${SSH_USER}@${ip_addr} /tmp/contrail_update_images.sh
    done
done

#Stoping config_api/analytics_api containers
echo STOPPING PLAN FOR CONTRAIL API CONTAINERS:

for flavor in ${FLAVORS[@]}; do
    echo Node-flavor: $flavor:
    echo "    Stop containers:"
    for cnt in ${STOP_CONTAINER["$flavor"]}; do
        echo "     - $cnt"
    done
done
echo Please type 'YES' for continue or ^C for exit
while read STOP_NOW; do
   if [[ "$STOP_NOW" == "YES" ]]; then
      break
   else
      echo Please type 'YES' for continue or ^C for exit
   fi
done

echo STOPPING CONTRAIL API CONTAINERS
for flavor in ${FLAVORS[@]}; do
    if [[ ! -z ${STOP_CONTAINER["$flavor"]+x} ]]; then
        echo "======= flavor: ${flavor} ======="
        for ip_addr in $(openstack server list --flavor ${flavor} -f value -c Networks | cut -d '=' -f 2); do
            echo "Node: ${ip_addr}  Stopping contrail api containers"
            scp ${SSH_OPTIONS} /tmp/${flavor}_stop_containers.sh ${SSH_USER}@${ip_addr}:/tmp/contrail_stop_containers.sh
            ssh ${SSH_OPTIONS} ${SSH_USER}@${ip_addr} /tmp/contrail_stop_containers.sh
        done
    fi
done

