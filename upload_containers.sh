#!/bin/bash

getopt --test > /dev/null
if [[ $? -ne 4 ]]; then
    echo "I’m sorry, `getopt --test` failed in this environment."
    exit 1
fi

OPTIONS=l:r:t:c:
LONGOPTIONS=local:,remote:,tag:,cert:

# -temporarily store output to be able to check for errors
# -e.g. use “--options” parameter by name to activate quoting/enhanced mode
# -pass arguments only via   -- "$@"   to separate them correctly
PARSED=$(getopt --options=$OPTIONS --longoptions=$LONGOPTIONS --name "$0" -- "$@")
if [[ $? -ne 0 ]]; then
    # e.g. $? == 1
    #  then getopt has complained about wrong arguments to stdout
    exit 2
fi
# read getopt’s output this way to handle the quoting right:
eval set -- "$PARSED"

# now enjoy the options in order and nicely split until we see --
while true; do
    case "$1" in
        -l|--local)
            local_registry="$2"
            shift 2
            ;;
        -r|--remote)
            remote_registry="$2"
            shift 2
            ;;
        -t|--tag)
            tag="$2"
            shift 2
            ;;
        -c|--cert)
            cert_url="$2"
            shift 2
            ;;
        --)
            shift
            break
            ;;
        *)
            echo "Programming error"
            exit 3
            ;;
    esac
done

# handle non-option arguments
#if [[ $# -ne 1 ]]; then
#    echo "$0: A single input file is required."
#    exit 4
#fi

echo "remote registry: $remote_registry, local registry: $local_registry"
if [[ -n ${cert_url} ]]; then
  registry_name=(${remote_registry//:/ }) 
  mkdir -p /etc/docker/certs.d/${registry_name}
  (cd /etc/docker/certs.d/${registry_name}; curl -O ${cert_url})   
  (cd /etc/pki/ca-trust/source/anchors/; curl -O ${cert_url}) 
  update-ca-trust 
  systemctl restart docker
fi
for image in contrail-analytics-alarm-gen \
contrail-analytics-api \
contrail-analytics-collector \
contrail-analytics-query-engine \
contrail-controller-config-api \
contrail-controller-config-devicemgr \
contrail-controller-config-schema \
contrail-controller-config-svcmonitor \
contrail-controller-control-control \
contrail-controller-control-dns \
contrail-controller-control-named \
contrail-controller-webui-job \
contrail-controller-webui-web \
contrail-external-cassandra \
contrail-external-kafka \
contrail-external-rabbitmq \
contrail-external-zookeeper \
contrail-node-init \
contrail-nodemgr \
contrail-openstack-compute-init \
contrail-openstack-heat-init \
contrail-openstack-neutron-init \
contrail-status \
contrail-vrouter-agent \
contrail-vrouter-kernel-init
do
   echo ${remote_registry}/${image}:${tag} ${local_registry}/${image}:${tag}
   docker pull ${remote_registry}/${image}:${tag}
   docker tag ${remote_registry}/${image}:${tag} ${local_registry}/${image}:${tag}
   docker push ${local_registry}/${image}:${tag}
done
#./upload_containers.sh -l 192.168.24.1:8787 -r satellite.englab.juniper.net:5443 -t queens-master-139-rhel -c http://satellite.englab.juniper.net/pub/satellite.englab.juniper.net.cert
