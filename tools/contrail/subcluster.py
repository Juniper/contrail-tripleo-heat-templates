#!/bin/python
import yaml, sys, getopt, json
from subprocess import check_output

def get_system_uuid(uuid):
    introspection_data = check_output(["openstack","baremetal","introspection","data","save",uuid])
    introspection_data_json = json.loads(introspection_data)
    system_uuid_string = json.dumps(introspection_data_json['extra']['system']['product']['uuid'])
    system_uuid = system_uuid_string.replace('"','')
    return system_uuid

def readFile(inputfile):
    subcluster_dict = yaml.load(open(inputfile))
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
            control_node_system_uuid = get_system_uuid(control_node_uuid)
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
            compute_node_system_uuid = get_system_uuid(compute_node_uuid)
            compute_node_dict = {compute_node_system_uuid: {}}
            contrail_settings = {'contrail_settings': {}}
            contrail_settings['contrail_settings']['SUBCLUSTER'] = subcluster_name
            contrail_settings['contrail_settings']['VROUTER_GATEWAY'] = compute_node['vrouter_gateway']
            contrail_settings['contrail_settings']['CONTROL_NODES'] = control_node_ip_string
            compute_node_dict[compute_node_system_uuid] = contrail_settings
            node_dict['parameter_defaults']['NodeDataLookup'][compute_node_system_uuid] = contrail_settings
            output_list.append(compute_node_dict)
    return node_dict

def writeFile(outputfile,subcluster_list):
    with open(outputfile, 'w') as subcluster_yaml:
      yaml.dump(subcluster_list, subcluster_yaml, default_flow_style=False)

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
   if not inputfile or not outputfile:
      print "-i or -o is missing"
      print 'subcluster.py -i <inputfile> -o <outputfile>'
      sys.exit()
   subcluster_list = readFile(inputfile)
   writeFile(outputfile, subcluster_list)

if __name__ == "__main__":
   main(sys.argv[1:])
