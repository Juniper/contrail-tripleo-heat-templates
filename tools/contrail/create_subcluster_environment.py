#!/usr/bin/python
import yaml, sys, getopt, json, os
from subprocess import check_output
from string import Template


CONTROL_ONLY_HOSTNAME_PREFIX='ctrlonly'
COMPUTE_HOSTNAME_PREFIX='compute'
DPDK_HOSTNAME_PREFIX='computedpdk'
SRIOV_HOSTNAME_PREFIX='computesriov'
CONTROL_ONLY_ROLE_PREFIX='ContrailControlOnly'
COMPUTE_ROLE_PREFIX='ContrailCompute'
CONTROL_ONLY_SERVICE='../../docker/services/contrail/contrail-control-only.yaml'
COMPUTE_SERVICE='../../docker/services/contrail/contrail-vrouter.yaml'
DPDK_SERVICE='../../docker/services/contrail/contrail-vrouter-dpdk.yaml'
SRIOV_SERVICE='../../docker/services/contrail/contrail-vrouter-sriov.yaml'
CONTROL_ONLY_NIC_CONFIG='../../network/config/contrail/contrail-controller-nic-config.yaml'
COMPUTE_NIC_CONFIG='../../network/config/contrail/compute-nic-config.yaml'
DPDK_NIC_CONFIG='../../network/config/contrail/contrail-dpdk-nic-config.yaml'
SRIOV_NIC_CONFIG='../../network/config/contrail/contrail-sriov-nic-config.yaml'
COMPUTE_PRE_NETWORK='../../extraconfig/pre_network/contrail/compute_pre_network.yaml'
DPDK_PRE_NETWORK='../../extraconfig/pre_network/contrail/contrail_dpdk_pre_network.yaml'
SRIOV_PRE_NETWORK='../../extraconfig/pre_network/contrail/contrail_sriov_pre_network.yaml'
DPDK_ROLE_PREFIX='ContrailDpdk'
SRIOV_ROLE_PREFIX='ContrailSriov'
ROLES_FILE='../../roles_data_contrail_aio.yaml'
CONTRAIL_SERVICES='../../environments/contrail/contrail-services.yaml'
CONTRAIL_NET='../../environments/contrail/contrail-net.yaml'
CONTRAIL_PLUGINS='../../environments/contrail/contrail-plugins.yaml'
CONTRAIL_SUBCLUSTER='../../environments/contrail/contrail-subcluster.yaml'
CONTRAIL_STATIC_IP='../../environments/contrail/contrail-ips-from-pool-all.yaml'
CONTRAIL_SCHEDULER_HINTS='../../environments/contrail/contrail-scheduler-hints.yaml'
CONTROL_ONLY_ROLE='''###############################################################################
# Role: $ROLE_NAME #
###############################################################################
- name: $ROLE_NAME
  description: |
    ContrailController role that has all the Contrail controler services loaded
    and handles config, control and webui functions
  CountDefault: 0
  tags:
    - primary
    - contrailcontroller
  networks:
    - InternalApi
    - Tenant
  HostnameFormatDefault: '%stackname%-$HOSTNAME-%index%'
  ServicesDefault:
    - OS::TripleO::Services::AuditD
    - OS::TripleO::Services::CACerts
    - OS::TripleO::Services::CertmongerUser
    - OS::TripleO::Services::Collectd
    - OS::TripleO::Services::Docker
    - OS::TripleO::Services::Ec2Api
    - OS::TripleO::Services::Ipsec
    - OS::TripleO::Services::Kernel
    - OS::TripleO::Services::LoginDefs
    - OS::TripleO::Services::Ntp
    - OS::TripleO::Services::ContainersLogrotateCrond
    - OS::TripleO::Services::Snmp
    - OS::TripleO::Services::Sshd
    - OS::TripleO::Services::Timezone
    - OS::TripleO::Services::TripleoPackages
    - OS::TripleO::Services::TripleoFirewall
    - OS::TripleO::Services::$ROLE_NAME'''
COMPUTE_ROLE='''###############################################################################
# Role: $ROLE_NAME #
###############################################################################
- name: $ROLE_NAME
  description: |
    Basic Compute Node role
  CountDefault: 0
  networks:
    - InternalApi
    - Tenant
    - Storage
  HostnameFormatDefault: '%stackname%-$HOSTNAME-%index%'
  # Deprecated & backward-compatible values (FIXME: Make parameters consistent)
  # Set uses_deprecated_params to True if any deprecated params are used.
  disable_upgrade_deployment: True
  ServicesDefault:
    - OS::TripleO::Services::Aide
    - OS::TripleO::Services::AuditD
    - OS::TripleO::Services::CACerts
    - OS::TripleO::Services::CephClient
    - OS::TripleO::Services::CephExternal
    - OS::TripleO::Services::CertmongerUser
    - OS::TripleO::Services::Collectd
    - OS::TripleO::Services::ComputeCeilometerAgent
    - OS::TripleO::Services::ComputeNeutronCorePlugin
    - OS::TripleO::Services::ComputeNeutronL3Agent
    - OS::TripleO::Services::ComputeNeutronMetadataAgent
    - OS::TripleO::Services::Docker
    - OS::TripleO::Services::Fluentd
    - OS::TripleO::Services::Ipsec
    - OS::TripleO::Services::Iscsid
    - OS::TripleO::Services::Kernel
    - OS::TripleO::Services::LoginDefs
    - OS::TripleO::Services::MySQLClient
    - OS::TripleO::Services::NovaCompute
    - OS::TripleO::Services::NovaLibvirt
    - OS::TripleO::Services::NovaMigrationTarget
    - OS::TripleO::Services::Ntp
    - OS::TripleO::Services::ContainersLogrotateCrond
    - OS::TripleO::Services::Rhsm
    - OS::TripleO::Services::RsyslogSidecar
    - OS::TripleO::Services::Securetty
    - OS::TripleO::Services::SensuClient
    - OS::TripleO::Services::SkydiveAgent
    - OS::TripleO::Services::Snmp
    - OS::TripleO::Services::Sshd
    - OS::TripleO::Services::Timezone
    - OS::TripleO::Services::TripleoFirewall
    - OS::TripleO::Services::TripleoPackages
    - OS::TripleO::Services::Tuned
    - OS::TripleO::Services::Ptp'''

class ContrailStaticIp(object):
    def __init__(self, subcluster_yaml,roleTypeList):
        self.subcluster_yaml = subcluster_yaml
        if not os.path.exists(CONTRAIL_STATIC_IP):
            fh = open(CONTRAIL_STATIC_IP, "w")
            fh.close()
        contrailStaticIpFile = yaml.load(open(CONTRAIL_STATIC_IP)) or {}
        if not 'resource_registry' in contrailStaticIpFile:
            contrailStaticIpFile['resource_registry'] = {}
        if not 'parameter_defaults' in contrailStaticIpFile:
            contrailStaticIpFile['parameter_defaults'] = {}
        self.resourceRegistry = contrailStaticIpFile['resource_registry']
        self.parameterDefaults = contrailStaticIpFile['parameter_defaults']
        if 'controlOnly' in roleTypeList:
            self.createContrailStaticIp(CONTROL_ONLY_ROLE_PREFIX,CONTROL_ONLY_HOSTNAME_PREFIX,'control_nodes')
        if 'vrouter' in roleTypeList:
            self.createContrailStaticIp(COMPUTE_ROLE_PREFIX,COMPUTE_HOSTNAME_PREFIX, 'compute_nodes')
        if 'dpdk' in roleTypeList:
            self.createContrailStaticIp(DPDK_ROLE_PREFIX,DPDK_HOSTNAME_PREFIX, 'dpdk_nodes')
        if 'sriov' in roleTypeList:
            self.createContrailStaticIp(SRIOV_ROLE_PREFIX,SRIOV_HOSTNAME_PREFIX, 'sriov_nodes')
        contrailStaticIpFile['resource_registry'] = self.resourceRegistry
        contrailStaticIpFile['parameter_defaults'] = self.parameterDefaults
        self.contrailStaticIp = contrailStaticIpFile

    def setProperties(self,uuid,nodeName):
        properties = check_output(["openstack","baremetal","node","show",uuid,'-c','properties','-f','json'])
        properties_json = json.loads(properties)
        capabilitiesString = properties_json['properties']['capabilities']
        capabilitiesList = capabilitiesString.split(',')
        newCapabilitiesList = []
        nodeExists = False
        for capability in capabilitiesList:
            capabilityItem = capability.split(':')
            if capabilityItem[0] == 'node':
                capabilityItem[1] = nodeName
                capabilityItemString = ':'.join(capabilityItem)
                newCapabilitiesList.append(capabilityItemString)
                nodeExists = True
            else:
                capabilityItemString = ':'.join(capabilityItem)
                newCapabilitiesList.append(capabilityItemString)
        if not nodeExists:
            newCapabilitiesList.append('node:' + nodeName)
        newCapabilitiesListString = ','.join(newCapabilitiesList)
        newCapabilitiesListString="capabilities=" + newCapabilitiesListString
        check_output(["openstack","baremetal","node","set",uuid,'--property',newCapabilitiesListString])

    def createContrailStaticIp(self,ROLE_PREFIX, HOSTNAME_PREFIX, nodeType):
        subcluster_dict = self.subcluster_yaml
        for subcluster in subcluster_dict:
            if nodeType not in subcluster:
                continue
            subclusterRoleName = subcluster['subcluster']
            subclusterRoleName = subclusterRoleName.capitalize()
            subclusterRoleName = ROLE_PREFIX + subclusterRoleName
            subclusterNetworkName = subcluster['network']
            subclusterNetworkDict = { subclusterNetworkName: [] }
            subclusterPortNetworkName = subclusterNetworkName.capitalize() + "Port"
            subclusterPortName = 'OS::TripleO::'+ subclusterRoleName + '::Ports::' + subclusterPortNetworkName
            subclusterIpsName = subclusterRoleName + 'IPs'
            subclusterHostname = subcluster['subcluster']
            subclusterHostname = subclusterHostname[0].lower() + subclusterHostname[1:]
            subclusterHostname = HOSTNAME_PREFIX + subclusterHostname
            subclusterIpList = []
            count = 0
            for node in subcluster[nodeType]:
                nodeName = subclusterHostname + '-' + str(count)
                self.setProperties(node['uuid'],nodeName)
                count = count + 1
                if 'ipaddress' in node:
                    subclusterIpList.append(node['ipaddress'])
            if len(subclusterIpList) > 0:
                self.parameterDefaults[subclusterIpsName] = {}
                self.resourceRegistry[subclusterPortName] = '../../network/ports/'+ subclusterNetworkName + '_from_pool.yaml'
                subclusterIpsDict = { subclusterIpsName : {}}
                subclusterNetworkDict = { subclusterNetworkName : []}
                subclusterNetworkDict[subclusterNetworkName] = subclusterIpList
                self.parameterDefaults[subclusterIpsName] = subclusterNetworkDict

class ContrailSchedulerHints(object):
    def __init__(self, subcluster_yaml, roleTypeList):
        self.subcluster_yaml = subcluster_yaml
        if not os.path.exists(CONTRAIL_SCHEDULER_HINTS):
            fh = open(CONTRAIL_SCHEDULER_HINTS, "w")
            fh.close()
        contrailSchedulerHintsFile = yaml.load(open(CONTRAIL_SCHEDULER_HINTS)) or {}
        if not 'parameter_defaults' in contrailSchedulerHintsFile:
            contrailSchedulerHintsFile['parameter_defaults'] = {}
        self.parameterDefaults = contrailSchedulerHintsFile['parameter_defaults']
        if 'controlOnly' in roleTypeList:
            self.createContrailSchedulerHint(CONTROL_ONLY_ROLE_PREFIX, CONTROL_ONLY_HOSTNAME_PREFIX)
        if 'vrouter' in roleTypeList:
            self.createContrailSchedulerHint(COMPUTE_ROLE_PREFIX, COMPUTE_HOSTNAME_PREFIX)
        if 'dpdk' in roleTypeList:
            self.createContrailSchedulerHint(DPDK_ROLE_PREFIX, DPDK_HOSTNAME_PREFIX)
        if 'sriov' in roleTypeList:
            self.createContrailSchedulerHint(SRIOV_ROLE_PREFIX, SRIOV_HOSTNAME_PREFIX)
        contrailSchedulerHintsFile['parameter_defaults'] = self.parameterDefaults
        self.contrailSchedulerHints = contrailSchedulerHintsFile

    def createContrailSchedulerHint(self, ROLE_PREFIX, HOSTNAME_PREFIX):
        subcluster_dict = self.subcluster_yaml
        for subcluster in subcluster_dict:
            subclusterRoleName = subcluster['subcluster']
            subclusterRoleName = subclusterRoleName.capitalize()
            subclusterRoleName = ROLE_PREFIX + subclusterRoleName
            subclusterHostname = subcluster['subcluster']
            subclusterHostname = subclusterHostname[0].lower() + subclusterHostname[1:]
            subclusterHostname = HOSTNAME_PREFIX + subclusterHostname + '-%index%'
            subclusterSchedulerHintName = subclusterRoleName + 'SchedulerHints'
            self.parameterDefaults[subclusterSchedulerHintName] = { 'capabilities:node': subclusterHostname}

class ContrailNet(object):
    def __init__(self, subcluster_yaml, roleTypeList):
        self.subcluster_yaml = subcluster_yaml
        contrailNetFile = yaml.load(open(CONTRAIL_NET))
        self.resourceRegistry = contrailNetFile['resource_registry']
        if 'controlOnly' in roleTypeList:
            self.createContrailNet(CONTROL_ONLY_ROLE_PREFIX, CONTROL_ONLY_NIC_CONFIG)
        if 'vrouter' in roleTypeList:
            self.createContrailNet(COMPUTE_ROLE_PREFIX, COMPUTE_NIC_CONFIG)
        if 'dpdk' in roleTypeList:
            self.createContrailNet(DPDK_ROLE_PREFIX, DPDK_NIC_CONFIG)
        if 'sriov' in roleTypeList:
            self.createContrailNet(SRIOV_ROLE_PREFIX, SRIOV_NIC_CONFIG)
        contrailNetFile['resource_registry'] = self.resourceRegistry
        self.contrailNet = contrailNetFile

    def createContrailNet(self, ROLE_PREFIX, NIC_CONFIG):
        subcluster_dict = self.subcluster_yaml
        for subcluster in subcluster_dict:
            subclusterRoleName = subcluster['subcluster']
            subclusterRoleName = subclusterRoleName.capitalize()
            subclusterRoleName = ROLE_PREFIX + subclusterRoleName
            subclusterNetName = 'OS::TripleO::'+ subclusterRoleName + '::Net::SoftwareConfig'
            self.resourceRegistry[subclusterNetName] = NIC_CONFIG

class ContrailServices(object):
    def __init__(self, subcluster_yaml, roleTypeList):
        self.subcluster_yaml = subcluster_yaml
        contrailServicesFile = yaml.load(open(CONTRAIL_SERVICES))
        self.parameterDefaults = contrailServicesFile['parameter_defaults']
        self.contrailServiceNetMap = self.parameterDefaults['ServiceNetMap']
        if 'controlOnly' in roleTypeList:
            self.createContrailServices(CONTROL_ONLY_ROLE_PREFIX, 'control_nodes')
        if 'vrouter' in roleTypeList:
            self.createContrailServices(COMPUTE_ROLE_PREFIX, 'compute_nodes')
        if 'dpdk' in roleTypeList:
            self.createContrailServices(DPDK_ROLE_PREFIX, 'dpdk_nodes')
        if 'sriov' in roleTypeList:
            self.createContrailServices(SRIOV_ROLE_PREFIX, 'sriov_nodes')
        self.parameterDefaults['ServiceNetMap'] = self.contrailServiceNetMap
        contrailServicesFile['parameter_defaults'] = self.parameterDefaults
        self.contrailServices = contrailServicesFile

    def createContrailServices(self, ROLE_PREFIX, roleType):
        subcluster_dict = self.subcluster_yaml
        for subcluster in subcluster_dict:
            if roleType not in subcluster:
                continue
            subclusterRoleName = subcluster['subcluster']
            subclusterRoleName = subclusterRoleName.capitalize()
            subclusterRoleName = ROLE_PREFIX + subclusterRoleName
            subclusterRoleNetworkName = subclusterRoleName + 'Network'
            subclusterRoleCountName = subclusterRoleName + 'Count'
            subclusterRoleFlavorName = 'Overcloud' + subclusterRoleName + 'Flavor'
            if not subclusterRoleNetworkName in self.contrailServiceNetMap:
                self.contrailServiceNetMap[subclusterRoleNetworkName] = subcluster['network']
            nodeCount = 0
            for node in subcluster[roleType]:
                 nodeCount = nodeCount + 1
            self.parameterDefaults[subclusterRoleCountName] = nodeCount
            self.parameterDefaults[subclusterRoleFlavorName] = 'baremetal'

class ContrailPlugin(object):
    def __init__(self, subcluster_yaml, roleTypeList):
        self.subcluster_yaml = subcluster_yaml
        pluginFile = yaml.load(open(CONTRAIL_PLUGINS))
        self.resourceRegistry = pluginFile['resource_registry']
        if 'controlOnly' in roleTypeList:
            self.createContrailPlugin(CONTROL_ONLY_ROLE_PREFIX, CONTROL_ONLY_SERVICE)
        if 'vrouter' in roleTypeList:
            self.createContrailPlugin(COMPUTE_ROLE_PREFIX, COMPUTE_SERVICE, COMPUTE_PRE_NETWORK)
        if 'dpdk' in roleTypeList:
            self.createContrailPlugin(DPDK_ROLE_PREFIX, DPDK_SERVICE, DPDK_PRE_NETWORK)
        if 'sriov' in roleTypeList:
            self.createContrailPlugin(SRIOV_ROLE_PREFIX, SRIOV_SERVICE, SRIOV_PRE_NETWORK)
        pluginFile['resource_registry'] = self.resourceRegistry
        self.contrailPlugin = pluginFile

    def createContrailPlugin(self, ROLE_PREFIX, servicePath, preNetwork=False):
        subcluster_dict = self.subcluster_yaml
        for subcluster in subcluster_dict:
            subclusterRoleName = subcluster['subcluster']
            subclusterRoleName = subclusterRoleName.capitalize()
            subclusterRoleName = ROLE_PREFIX + subclusterRoleName
            subclusterPluginName = 'OS::TripleO::Services::' + subclusterRoleName
            subclusterPreNetworkConfig = 'OS::TripleO::' + subclusterRoleName + '::PreNetworkConfig'
            subclusterExtraConfigPre = 'OS::TripleO::' + subclusterRoleName + 'ExtraConfigPre'
            subclusterPluginExists = False
            self.resourceRegistry[subclusterPluginName] = servicePath
            self.resourceRegistry[subclusterExtraConfigPre] = '../../extraconfig/pre_deploy/contrail/contrail-init.yaml'
            if preNetwork:
                self.resourceRegistry[subclusterPreNetworkConfig] = preNetwork


class ContrailRole(object):
    def __init__(self, subcluster_yaml, roleTypeList):
        self.subcluster_yaml = subcluster_yaml
        subcluster_dict = self.subcluster_yaml
        contrailControlOnlyRole = Template(CONTROL_ONLY_ROLE)
        contrailComputeRole = Template(COMPUTE_ROLE)
        subclusterRoleList = []
        subclusterString = ''
        if 'controlOnly' in roleTypeList:
            subclusterString += self.createRole(contrailControlOnlyRole, CONTROL_ONLY_HOSTNAME_PREFIX, CONTROL_ONLY_ROLE_PREFIX)
        if 'vrouter' in roleTypeList:
            subclusterString += self.createRole(contrailComputeRole, COMPUTE_HOSTNAME_PREFIX, COMPUTE_ROLE_PREFIX)
        if 'dpdk' in roleTypeList:
            subclusterString += self.createRole(contrailComputeRole, DPDK_HOSTNAME_PREFIX, DPDK_ROLE_PREFIX)
        if 'sriov' in roleTypeList:
            subclusterString += self.createRole(contrailComputeRole, SRIOV_HOSTNAME_PREFIX, SRIOV_ROLE_PREFIX)
        self.subclusterString = subclusterString

    def createRole(self, roleTemplate, hostnamePrefix, rolePrefix):
        roleFile = yaml.load(open(ROLES_FILE))
        subcluster_dict = self.subcluster_yaml
        subclusterRoleList = []
        subclusterString = ''
        for subcluster in subcluster_dict:
            subclusterRoleName = subcluster['subcluster']
            subclusterRoleName = subclusterRoleName.capitalize()
            subclusterRoleName = rolePrefix + subclusterRoleName
            subclusterRoleExists = False
            for role in roleFile:
                if role['name'] == subclusterRoleName:
                    subclusterRoleExists = True
            if not subclusterRoleExists:
                subclusterHostname = subcluster['subcluster']
                subclusterHostname = subclusterHostname[0].lower() + subclusterHostname[1:]
                subclusterHostname = hostnamePrefix + subclusterHostname
                subclusterRole = roleTemplate.substitute(ROLE_NAME=subclusterRoleName,HOSTNAME=subclusterHostname)
                subclusterRoleList.append(subclusterRole)
        for subclusterRole in subclusterRoleList:
            subclusterString += subclusterRole
            subclusterString += '\n'
        return subclusterString

class ContrailSubcluster(object):
    def __init__(self, subcluster_yaml):
        self.subcluster_yaml = subcluster_yaml
        self.subcluster = self.createSubcluster()

    def getSystemUUID(self,uuid):
        introspection_data = check_output(["openstack","baremetal","introspection","data","save",uuid])
        introspection_data_json = json.loads(introspection_data)
        system_uuid_string = json.dumps(introspection_data_json['extra']['system']['product']['uuid'])
        system_uuid = system_uuid_string.replace('"','')
        return system_uuid

    def createSubcluster(self):
        subcluster_dict = self.subcluster_yaml
        output_list = []
        node_dict = { "parameter_defaults" : { "NodeDataLookup": {}}}
        for subcluster in subcluster_dict:
            subcluster_name = subcluster['subcluster']
            subcluster_control_nodes = subcluster['control_nodes']
            subcluster_compute_nodes = subcluster['compute_nodes']
            control_node_ip_dict = { subcluster_name: [] }
            control_node_ips = []
            for control_node in subcluster_control_nodes:
                control_node_ips.append(control_node['ipaddress'])
            control_node_ip_dict[subcluster_name] = control_node_ips
            control_node_ip_string = ','.join(control_node_ip_dict[subcluster_name])
            for control_node in subcluster_control_nodes:
                control_node_uuid = control_node['uuid']
                control_node_system_uuid = self.getSystemUUID(control_node_uuid)
                control_node_dict = {control_node_system_uuid: {}}
                contrail_settings = {'contrail_settings': {}}
                contrail_settings['contrail_settings']['SUBCLUSTER'] = subcluster_name
                contrail_settings['contrail_settings']['BGP_ASN'] = subcluster['asn']
                contrail_settings['contrail_settings']['CONTROL_NODES'] = control_node_ip_string
                control_node_dict[control_node_system_uuid] = contrail_settings
                node_dict['parameter_defaults']['NodeDataLookup'][control_node_system_uuid] = contrail_settings
                output_list.append(control_node_dict)
            for compute_node in subcluster_compute_nodes:
                compute_node_uuid = compute_node['uuid']
                compute_node_system_uuid = self.getSystemUUID(compute_node_uuid)
                compute_node_dict = {compute_node_system_uuid: {}}
                contrail_settings = {'contrail_settings': {}}
                contrail_settings['contrail_settings']['SUBCLUSTER'] = subcluster_name
                contrail_settings['contrail_settings']['VROUTER_GATEWAY'] = compute_node['vrouter_gateway']
                contrail_settings['contrail_settings']['CONTROL_NODES'] = control_node_ip_string
                compute_node_dict[compute_node_system_uuid] = contrail_settings
                node_dict['parameter_defaults']['NodeDataLookup'][compute_node_system_uuid] = contrail_settings
                output_list.append(compute_node_dict)
        return node_dict

def writeYaml(outputfile,inputYaml):
    with open(outputfile, 'w') as yamlFile:
        yaml.dump(inputYaml, yamlFile, default_flow_style=False)

def writeFile(outputfile,inputString):
    with open(outputfile, 'a') as writeFile:
        writeFile.write(inputString)

def main(argv):
    inputfile = ''
    outputfile = ''
    try:
       opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
    except getopt.GetoptError:
       print 'subcluster.py -i <inputfile> -o <outputfile>'
       sys.exit(2)
    for opt, arg in opts:
       if opt == '-h':
          print 'subcluster.py -i <inputfile> -o <outputfile>'
          sys.exit()
       elif opt in ("-i", "--ifile"):
          inputfile = arg
       elif opt in ("-o", "--ofile"):
          outputfile = arg
    if not inputfile:
       print "-i is missing"
       print 'subcluster.py -i <inputfile>'
       sys.exit()

    subcluster_yaml = yaml.load(open(inputfile))

    roleTypeList = []
    createControlOnlyRole = False
    createComputeRole = False
    createComputeDpdkRole = False
    createComputeSriovRole = False
    for subcluster in subcluster_yaml:
        if 'control_nodes' in subcluster:
            roleTypeList.append('controlOnly')
        if 'compute_nodes' in subcluster:
            roleTypeList.append('vrouter')
        if 'dpdk_nodes' in subcluster:
            roleTypeList.append('dpdk')
        if 'sriov_nodes' in subcluster:
            roleTypeList.append('sriov')

    contrailSubcluster = ContrailSubcluster(subcluster_yaml)
    writeYaml(CONTRAIL_SUBCLUSTER,contrailSubcluster.subcluster)

    contrailRole = ContrailRole(subcluster_yaml,roleTypeList)
    writeFile(ROLES_FILE,contrailRole.subclusterString)

    contrailSchedulerHints = ContrailSchedulerHints(subcluster_yaml,roleTypeList)
    writeYaml(CONTRAIL_SCHEDULER_HINTS,contrailSchedulerHints.contrailSchedulerHints)

    contrailSubclusterPlugin = ContrailPlugin(subcluster_yaml,roleTypeList)
    writeYaml(CONTRAIL_PLUGINS,contrailSubclusterPlugin.contrailPlugin)

    contrailServiceFile = ContrailServices(subcluster_yaml,roleTypeList)
    writeYaml(CONTRAIL_SERVICES,contrailServiceFile.contrailServices)

    contrailNet = ContrailNet(subcluster_yaml,roleTypeList)
    writeYaml(CONTRAIL_NET,contrailNet.contrailNet)

    contrailStaticIp = ContrailStaticIp(subcluster_yaml,roleTypeList)
    print 'Creating static ip list in %s' % CONTRAIL_STATIC_IP
    writeYaml(CONTRAIL_STATIC_IP,contrailStaticIp.contrailStaticIp)

if __name__ == "__main__":
   main(sys.argv[1:])
