#! /bin/bash

set -x

function error_exit
{
#   ----------------------------------------------------------------
#   Function for exit due to fatal program error
#       Accepts 3 arguments:
#               line #
#               string containing descriptive error message
#               exit code
#   ----------------------------------------------------------------


    echo "${PROGNAME}: ${1:-''} ${2:-'Unknown Error'}" 1>&2
    exit ${3:-1}
}

function find_dev_by_mac () {
mac=$1;
[ -z "$mac" ] || for dev in /sys/class/net/*; do
    [ $mac = $(cat $dev/address) ] && [ $(basename $dev) != vhost0 ] && \
         echo $(basename $dev) && return
done
}

source /opt/contrail/bin/vrouter-functions.sh

function create_virtual_gateway() {

    echo "$(date): Adding intreface vgw for virtual gateway"
    #    sysctl -w net.ipv4.ip_forward=1
    echo 1 > /proc/sys/net/ipv4/ip_forward
    vgw_array=(${vgw_subnet_ip//,/ })
    vgw_intf_array=(${vgw_intf//,/ })
    i=0
    #for element in "${vgw_array[@]}"
    for ((i=0;i<${#vgw_array[@]};++i))
       do
       vif --create ${vgw_intf_array[i]} --mac 00:00:5e:00:01:00
       if [ $? != 0 ]
           then
           echo "$(date): Error adding intreface vgw"
       fi

       ifconfig ${vgw_intf_array[i]} up
       vgw_subnet=${vgw_array[i]}
       echo $vgw_subnet
       vgw_subnet_array=$(echo $vgw_subnet | tr ";" "\n")
       for element in $vgw_subnet_array
       do
           echo "$(date): Adding route for $element with interface ${vgw_intf_array[i]}"
           route add -net $element dev ${vgw_intf_array[i]}
       done
   done
}

insert_vrouter &>> $LOG
echo "$(date): Value $vgw_subnet_ip" &>> $LOG
if [ $vgw_subnet_ip != __VGW_SUBNET_IP__ ]
then
    echo "$(date): Creating VGW Intreface as VGW Subnet is present" &>> $LOG
    create_virtual_gateway &>>$LOG
fi

exit

# source /etc/contrail/agent_param
# ip link set dev $dev up
