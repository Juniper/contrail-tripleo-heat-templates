#!/bin/python
import yaml, sys, getopt, json
from subprocess import check_output

def get_system_uudi(uuid):
    introspection_data = check_output(["openstack","baremetal","introspection","data","save",uuid])
    introspection_data_json = json.loads(introspection_data)
    print json.dumps(introspection_data_json['extra']['system']['product']['uuid'])
    system_uuid_string = json.dumps(introspection_data_json['extra']['system']['product']['uuid'])
    system_uuid = system_uuid_string.replace('"','')
    return system_uuid

def readFile(inputfile):
    subcluster_dict = yaml.load(open(inputfile))
    output_list = []
    for subcluster in subcluster_dict:
        subcluster_name = subcluster['subcluster']
        subcluster_control_nodes = subcluster['control_nodes']
        subcluster_compute_nodes = subcluster['compute_nodes']
        control_node_ip_dict = { subcluster_name: [] }
        control_node_ips = []
        for control_node in subcluster_control_nodes:
            control_node_uuid = control_node['uuid']
            control_node_system_uuid = get_system_uudi(control_node_uuid)
            control_node_dict = {control_node_system_uuid: {}}
            contrail_settings = {'contrail_settings': {}}
            contrail_settings['contrail_settings']['SUBCLUSTER'] = subcluster_name
            contrail_settings['contrail_settings']['BGP_ASN'] = subcluster['asn']
            control_node_ips.append(control_node['ipaddress'])
            control_node_dict[control_node_system_uuid] = contrail_settings
            output_list.append(control_node_dict)
        control_node_ip_dict[subcluster_name] = control_node_ips
        for compute_node in subcluster_compute_nodes:
            compute_node_uuid = compute_node['uuid']
            compute_node_system_uuid = get_system_uudi(compute_node_uuid)
            compute_node_dict = {compute_node_system_uuid: {}}
            control_node_ip_string = ','.join(control_node_ip_dict[subcluster_name])
            contrail_settings = {'contrail_settings': {}}
            contrail_settings['contrail_settings']['SUBCLUSTER'] = subcluster_name
            contrail_settings['contrail_settings']['VROUTER_GATEWAY'] = compute_node['vrouter_gateway']
            contrail_settings['contrail_settings']['CONTROL_NODES'] = control_node_ip_string
            compute_node_dict[compute_node_system_uuid] = contrail_settings
            output_list.append(compute_node_dict)
    return output_list

def writeFile(outputfile,subcluster_list):
    f = open(outputfile,'w')
    header = """parameter_defaults:
  NodeDataLookup: |"""
    f.write(header + "\n")
    for line in subcluster_list:
        line_str = str(line)
        f.write("     %s\n" % line_str.replace("'",'"'))
    f.close()

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
#      if not inputfile or not outputfile:
#          print "-i or -o is missing"
#          print 'subcluster.py -i <inputfile> -o <outputfile>'
#          sys.exit()
   subcluster_list = readFile(inputfile)
   writeFile(outputfile, subcluster_list)

if __name__ == "__main__":
   main(sys.argv[1:])
