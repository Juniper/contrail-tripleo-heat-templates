#!/bin/bash
function show_help {
  echo ""
  echo ""
  echo "Usage:"
  echo "./import_contrail_container.sh -f container_outputfile -r registry -t tag [-i insecure] [-u username] [-p password] [-c certificate path]"
  echo ""
  echo "Examples:"
  echo "Pull from password protectet public registry:"
  echo "./import_contrail_container.sh -f /tmp/contrail_container -r hub.juniper.net/contrail -u USERNAME -p PASSWORD -t 1234"
  echo "#######################################################################"
  echo "Pull from dockerhub:"
  echo "./import_contrail_container.sh -f /tmp/contrail_container -r docker.io/opencontrailnightly -t 1234"
  echo "#######################################################################"
  echo "Pull from private secure registry:"
  echo "./import_contrail_container.sh -f /tmp/contrail_container -r satellite.englab.juniper.net:5443 -c http://satellite.englab.juniper.net/pub/satellite.englab.juniper.net.crt -t 1234"
  echo "#######################################################################"
  echo "Pull from private INsecure registry:"
  echo "./import_contrail_container.sh -f /tmp/contrail_container -r 10.0.0.1:5443 -i 1 -t 1234"
  echo "#######################################################################"
  echo ""
  echo "Any of the commands will create /tmp/contrail_container which will be used for importing the contrail containers:"
  echo "openstack overcloud container image upload --config-file /tmp/contrail_container"

}
OPTIND=1         # Reset in case getopts has been used previously in the shell.

# Initialize our own variables:
output_file=""
verbose=0
insecure=0
registry=""
tag=""
user=""
password=""

while getopts "h?vf:i:r:t:c:u:p:" opt; do
    case "$opt" in
    h|\?)
        show_help
        exit 0
        ;;
    v)  verbose=1
        ;;
    f)  output_file=$OPTARG
        ;;
    i)  insecure=1
        ;;
    r)  registry=$OPTARG
        ;;
    t)  tag=$OPTARG
        ;;
    c)  cert=$OPTARG
        ;;
    u)  user=$OPTARG
        ;;
    p)  password=$OPTARG
        ;;
    esac
done

shift $((OPTIND-1))

[ "${1:-}" = "--" ] && shift

#echo "verbose=$verbose, output_file='$output_file', Leftovers: $@"
#echo "outfile: $output_file"
#echo "insecure: $insecure"
#echo "registry: $registry"
#echo "tag: $tag"
#echo "user: $user"
#echo "password: $password"
missing=""
if [[ -z ${output_file} ]]; then
  missing+=" output_file (-f),"
fi

if [[ -z ${registry} ]]; then
  missing+=" registry (-r),"
fi

if [[ -z ${tag} ]]; then
  missing+=" tag (-t)"
fi

if [[ -n ${missing} ]]; then
  echo ${missing} is missing
  exit 1
fi

topology_name='contrail-analytics-snmp-topology'
if echo "$tag" | grep -q '5\.0' ; then
  topology_name='contrail-analytics-topology'
fi

CONTAINER_MAP=(
DockerContrailAnalyticsAlarmGenImageName:contrail-analytics-alarm-gen
DockerContrailAnalyticsApiImageName:contrail-analytics-api
DockerContrailAnalyticsCollectorImageName:contrail-analytics-collector
DockerContrailAnalyticsQueryEngineImageName:contrail-analytics-query-engine
DockerContrailAnalyticsSnmpCollectorImageName:contrail-analytics-snmp-collector
DockerContrailAnalyticsTopologyImageName:${topology_name}
DockerContrailCassandraImageName:contrail-external-cassandra
DockerContrailConfigApiImageName:contrail-controller-config-api
DockerContrailConfigDevicemgrImageName:contrail-controller-config-devicemgr
DockerContrailConfigSchemaImageName:contrail-controller-config-schema
DockerContrailConfigSvcmonitorImageName:contrail-controller-config-svcmonitor
DockerContrailControlControlImageName:contrail-controller-control-control
DockerContrailControlDnsImageName:contrail-controller-control-dns
DockerContrailControlNamedImageName:contrail-controller-control-named
DockerContrailHeatPluginImageName:contrail-openstack-heat-init
DockerContrailKafkaImageName:contrail-external-kafka
DockerContrailNeutronPluginImageName:contrail-openstack-neutron-init
DockerContrailNodeInitImageName:contrail-node-init
DockerContrailNodemgrImageName:contrail-nodemgr
DockerContrailNovaPluginImageName:contrail-openstack-compute-init
DockerContrailRabbitmqImageName:contrail-external-rabbitmq
DockerContrailRedisImageName:contrail-external-redis
DockerContrailStunnelImageName:contrail-external-stunnel
DockerContrailStatusImageName:contrail-status
DockerContrailVrouterAgentContainerName:contrail-vrouter-agent
DockerContrailVrouterAgentDpdkContainerName:contrail-vrouter-agent-dpdk
DockerContrailVrouterAgentImageName:contrail-vrouter-agent
DockerContrailVrouterKernelInitDpdkImageName:contrail-vrouter-kernel-init-dpdk
DockerContrailVrouterKernelInitImageName:contrail-vrouter-kernel-init
DockerContrailWebuiJobImageName:contrail-controller-webui-job
DockerContrailWebuiWebImageName:contrail-controller-webui-web
DockerContrailZookeeperImageName:contrail-external-zookeeper
)

if [[ -n ${user} && -n ${password} ]]; then
  docker login -u ${user} -p ${password} ${registry}
fi

if [[ -n ${cert} ]]; then
  registry_name=(${registry//:/ })
  [ ! -f /etc/docker/certs.d/${registry_name} ]; sudo mkdir -p /etc/docker/certs.d/${registry_name}
  (cd /etc/docker/certs.d/${registry_name}; sudo curl -s -O ${cert})
  (cd /etc/pki/ca-trust/source/anchors/; sudo curl -s -O ${cert})
  sudo update-ca-trust
  sudo systemctl restart docker
fi

if [[ ${insecure} -eq 1 ]];then
  registry_name=(${registry//\// })
  registry_string=`cat /etc/sysconfig/docker |grep INSECURE_REGISTRY |awk -F"INSECURE_REGISTRY=\"" '{print $2}'|tr "\"" " "`
  registry_string="${registry_string} --insecure-registry ${registry_name}"
  complete_string="INSECURE_REGISTRY=\"${registry_string}\""
  if [[ `grep INSECURE_REGISTRY /etc/sysconfig/docker` ]]; then
    sudo sed -i "s/^INSECURE_REGISTRY=.*/${complete_string}/" /etc/sysconfig/docker
  else
    sudo echo ${complete_string} >> /etc/sysconfig/docker
  fi
  sudo systemctl restart docker
fi

echo "container_images:" > ${output_file}
for line in `echo ${CONTAINER_MAP[*]}`
do
  thtImageName=`echo ${line} |awk -F":" '{print $1}'`
  contrailImageName=`echo ${line} |awk -F":" '{print $2}'`
  echo "- imagename: ${registry}/${contrailImageName}:${tag}" >> ${output_file}
  echo "  push_destination: 192.168.24.1:8787" >> ${output_file}
done

echo "Written ${output_file}"
echo "Upload with:"
echo "openstack overcloud container image upload --config-file ${output_file}"
