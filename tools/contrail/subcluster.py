#!/usr/bin/python
import yaml, sys, getopt, json, os
from subprocess import check_output
from string import Template


HOSTNAME_PREFIX='ctrlonly'
ROLES_FILE='../../roles_data_contrail_aio.yaml'
CONTRAIL_SERVICES='../../environments/contrail/contrail-services.yaml'
CONTRAIL_NET='../../environments/contrail/contrail-net.yaml'
CONTRAIL_PLUGINS='../../environments/contrail/contrail-plugins.yaml'
CONTRAIL_SUBCLUSTER='../../environments/contrail/contrail-subcluster.yaml'
CONTRAIL_STATIC_IP='../../environments/contrail/contrail-ips-from-pool-all.yaml'
CONTROL_ONLY_ROLE='''###############################################################################
# Role: $ROLE_NAME #
###############################################################################
- name: $ROLE_NAME
  description: |
    ContrailController role that has all the Contrail controler services loaded
    and handles config, control and webui functions
  CountDefault: 1
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
    - OS::TripleO::Services::ContrailControlOnly'''

class ContrailStaticIp(object):
    def __init__(self, subcluster_yaml):
        self.subcluster_yaml = subcluster_yaml
        self.contrailStaticIp = self.createContrailStaticIp()

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
        newCapabilitiesListString="capabilities='" + newCapabilitiesListString + "'"
        output = check_output(["openstack","baremetal","node","set",uuid,'--property',newCapabilitiesListString])
        print output

    def createContrailStaticIp(self):
        subcluster_dict = self.subcluster_yaml
        if not os.path.exists(CONTRAIL_STATIC_IP):
            fh = open(CONTRAIL_STATIC_IP, "w")
            fh.close()
        contrailStaticIpFile = yaml.load(open(CONTRAIL_STATIC_IP)) or {}
        for subcluster in subcluster_dict:
            subclusterRoleName = subcluster['subcluster']
            subclusterRoleName = subclusterRoleName.capitalize()
            subclusterRoleName = 'ContrailControlOnly' + subclusterRoleName
            subclusterNetworkName = subcluster['network']
            subclusterNetworkDict = { subclusterNetworkName: [] }
            subclusterPortNetworkName = subclusterNetworkName.capitalize() + "Port"
            subclusterPortName = 'OS::TripleO::'+ subclusterRoleName + '::Ports::' + subclusterPortNetworkName
            subclusterIpsName = subclusterRoleName + 'IPs'
            subclusterHostname = subcluster['subcluster']
            subclusterHostname = subclusterHostname[0].lower() + subclusterHostname[1:]
            subclusterHostname = HOSTNAME_PREFIX + subclusterHostname
            if not 'resource_registry' in contrailStaticIpFile:
                contrailStaticIpFile['resource_registry'] = {}
            if not 'parameter_defaults' in contrailStaticIpFile:
                contrailStaticIpFile['parameter_defaults'] = {}
            resourceRegistry = contrailStaticIpFile['resource_registry']
            parameterDefaults = contrailStaticIpFile['parameter_defaults']
            subclusterIpList = []
            parameterDefaults[subclusterIpsName] = {}
            if not subclusterPortName in resourceRegistry:
                resourceRegistry[subclusterPortName] = '../../network/ports/tenant_from_pool.yaml'
            count = 0
            for control_node in subcluster['control_nodes']:
                nodeName = subclusterHostname + '-' + str(count)
                self.setProperties(control_node['uuid'],nodeName)
                count = count + 1 
                subclusterIpList.append(control_node['ipaddress'])
            subclusterIpsDict = { subclusterIpsName : {}}
            subclusterNetworkDict = { subclusterNetworkName : []}
            subclusterNetworkDict[subclusterNetworkName] = subclusterIpList
            parameterDefaults[subclusterIpsName] = subclusterNetworkDict
                
        contrailStaticIpFile['resource_registry'] = resourceRegistry
        contrailStaticIpFile['parameter_defaults'] = parameterDefaults
        return contrailStaticIpFile

class ContrailNet(object):
    def __init__(self, subcluster_yaml):
        self.subcluster_yaml = subcluster_yaml
        self.contrailNet = self.createContrailNet()

    def createContrailNet(self):
        subcluster_dict = self.subcluster_yaml
        contrailNetFile = yaml.load(open(CONTRAIL_NET))
        for subcluster in subcluster_dict:
            subclusterRoleName = subcluster['subcluster']
            subclusterRoleName = subclusterRoleName.capitalize()
            subclusterRoleName = 'ContrailControlOnly' + subclusterRoleName
            subclusterNetName = 'OS::TripleO::'+ subclusterRoleName + '::Net::SoftwareConfig'
            resourceRegistry = contrailNetFile['resource_registry']
            if not subclusterNetName in resourceRegistry:
                resourceRegistry[subclusterNetName] = '../../network/config/contrail/contrail-controller-nic-config.yaml'
        contrailNetFile['resource_registry'] = resourceRegistry
        return contrailNetFile

class ContrailServices(object):
    def __init__(self, subcluster_yaml):
        self.subcluster_yaml = subcluster_yaml
        self.contrailServices = self.createContrailServices()

    def createContrailServices(self):
        subcluster_dict = self.subcluster_yaml
        contrailServicesFile = yaml.load(open(CONTRAIL_SERVICES))
        for subcluster in subcluster_dict:
            subclusterRoleName = subcluster['subcluster']
            subclusterRoleName = subclusterRoleName.capitalize()
            subclusterRoleName = 'ContrailControlOnly' + subclusterRoleName
            subclusterRoleNetworkName = subclusterRoleName + 'Network'
            subclusterRoleCountName = subclusterRoleName + 'Count'
            subclusterRoleFlavorName = subclusterRoleName + 'Flavor'
            parameterDefaults = contrailServicesFile['parameter_defaults']
            contrailServiceNetMap = parameterDefaults['ServiceNetMap']
            if not subclusterRoleNetworkName in contrailServiceNetMap:
                contrailServiceNetMap[subclusterRoleNetworkName] = subcluster['network']
            controlNodeCount = 0
            for controlNode in subcluster['control_nodes']:
                controlNodeCount = controlNodeCount + 1
            parameterDefaults[subclusterRoleCountName] = controlNodeCount
            parameterDefaults[subclusterRoleFlavorName] = 'baremetal'
        parameterDefaults['ServiceNetMap'] = contrailServiceNetMap
        contrailServicesFile['parameter_defaults'] = parameterDefaults
        return contrailServicesFile
            

class ContrailPlugin(object):
    def __init__(self, subcluster_yaml):
        self.subcluster_yaml = subcluster_yaml
        self.contrailPlugin = self.createContrailPlugin()

    def createContrailPlugin(self):
        subcluster_dict = self.subcluster_yaml
        pluginFile = yaml.load(open(CONTRAIL_PLUGINS))
        for subcluster in subcluster_dict:
            subclusterRoleName = subcluster['subcluster']
            subclusterRoleName = subclusterRoleName.capitalize()
            subclusterRoleName = 'ContrailControlOnly' + subclusterRoleName
            subclusterPluginName = 'OS::TripleO::Services::' + subclusterRoleName
            subclusterPreNetworkConfig = 'OS::TripleO::' + subclusterRoleName + '::PreNetworkConfig'
            subclusterExtraConfigPre = 'OS::TripleO::' + subclusterRoleName + 'ExtraConfigPre'
            subcluster
            resourceRegistry = pluginFile['resource_registry']
            subclusterPluginExists = False
            if not subclusterPluginName in resourceRegistry:
                resourceRegistry[subclusterPluginName] = '../../docker/services/contrail/contrail-control-only.yaml'
                resourceRegistry[subclusterExtraConfigPre] = '../../extraconfig/pre_deploy/contrail/contrail-init.yaml'
        pluginFile['resource_registry'] = resourceRegistry
        return pluginFile

class ContrailRole(object):
    def __init__(self, subcluster_yaml):
        self.subcluster_yaml = subcluster_yaml
        self.subclusterString = self.createRole()

    def createRole(self):
        subcluster_dict = self.subcluster_yaml
        roleFile = yaml.load(open(ROLES_FILE))
        contrailControlOnlyRole = Template(CONTROL_ONLY_ROLE)
        subclusterRoleList = []
        subclusterString = ''
        for subcluster in subcluster_dict:
            subclusterRoleName = subcluster['subcluster']
            subclusterRoleName = subclusterRoleName.capitalize()
            subclusterRoleName = 'ContrailControlOnly' + subclusterRoleName
            subclusterRoleExists = False
            for role in roleFile:
                if role['name'] == subclusterRoleName:
                    subclusterRoleExists = True
            if not subclusterRoleExists:
                subclusterHostname = subcluster['subcluster']
                subclusterHostname = subclusterHostname[0].lower() + subclusterHostname[1:]
                subclusterHostname = HOSTNAME_PREFIX + subclusterHostname
                subclusterRole = contrailControlOnlyRole.substitute(ROLE_NAME=subclusterRoleName,HOSTNAME=subclusterHostname)
                subclusterRoleList.append(subclusterRole)
        for subclusterRole in subclusterRoleList:
            subclusterString += subclusterRole
            subclusterString += '\n'
        return subclusterString
        

class ContrailSubcluster(object):
    def __init__(self, subcluster_yaml):
        self.subcluster_yaml = subcluster_yaml
        subcluster = self.createSubcluster()

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

#   contrailSubcluster = ContrailSubcluster(subcluster_yaml)
#   writeYaml(CONTRAIL_SUBCLUSTER,contrailSubcluster.subcluster)

#   contrailRole = ContrailRole(subcluster_yaml)
#   writeFile(ROLES_FILE,contrailRole.subclusterString)

#   contrailSubclusterPlugin = ContrailPlugin(subcluster_yaml)
#   writeYaml(CONTRAIL_PLUGINS,contrailSubclusterPlugin.contrailPlugin)

#   contrailServiceFile = ContrailServices(subcluster_yaml)
#   writeYaml(CONTRAIL_SERVICES,contrailServiceFile.contrailServices)

#   contrailNet = ContrailNet(subcluster_yaml)
#   writeYaml(CONTRAIL_NET,contrailNet.contrailNet)

   contrailStaticIp = ContrailStaticIp(subcluster_yaml)
   writeYaml(CONTRAIL_STATIC_IP,contrailStaticIp.contrailStaticIp)

if __name__ == "__main__":
   main(sys.argv[1:])
