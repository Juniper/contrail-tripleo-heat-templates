#!/bin/bash
# The scripts takes as parameters the following environment variables:
#   contrail_registry_insecure
#   contrail_registry_cert_url
#   contrail_registry
#   contrail_registry_user
#   contrail_registry_password
#
export LOGFILE=/tmp/contrail_container_trace_full.txt
exec > >(tee -a $LOGFILE)
exec 2>&1
echo "=================== $(date) ==================="
set -xv

cat <<EOF > /tmp/contrail_issu_selinux.te
module contrail_issu_selinux 1.0;

require {
        type ifconfig_t;
        type user_tmp_t;
        type haproxy_exec_t;
        type var_lib_t;
        type http_port_t;
        type container_var_run_t;
        type svirt_t;
        type var_run_t;
        type virtlogd_t;
        type spc_t;
        type container_t;
        type container_log_t;
        type dhcpc_t;
        type NetworkManager_t;
        type unconfined_service_t;
        class process { setrlimit signal signull };
        class capability { kill net_bind_service setgid setuid sys_resource };
        class tcp_socket name_bind;
        class sock_file { create link rename unlink setattr write };
        class dir { add_name mounton remove_name write search };
        class file { create execute execute_no_trans getattr open read append unlink write };
}

#============= ifconfig_t ==============
allow ifconfig_t user_tmp_t:dir mounton;
allow ifconfig_t haproxy_exec_t:file { execute execute_no_trans open read };
allow ifconfig_t http_port_t:tcp_socket name_bind;
allow ifconfig_t self:capability { kill net_bind_service setgid setuid sys_resource };
allow ifconfig_t self:process setrlimit;
allow ifconfig_t var_lib_t:dir { add_name remove_name write };
allow ifconfig_t var_lib_t:file { create getattr unlink open read write };
allow ifconfig_t var_lib_t:sock_file { create link rename unlink setattr write };

#============= svirt_t ==============
allow svirt_t container_var_run_t:dir { add_name remove_name write };
allow svirt_t container_var_run_t:sock_file { create unlink };
allow svirt_t var_run_t:sock_file { create unlink };

#============= container_t ==============
allow container_t container_log_t:dir { add_name write };
allow container_t container_log_t:file { append create open };

#============= dhcpc_t ==============
allow dhcpc_t var_run_t:file { read write };

#============= NetworkManager_t ==============
allow NetworkManager_t unconfined_service_t:process { signal signull };
allow NetworkManager_t var_run_t:file { getattr open read unlink };

#============= virtlogd_t ==============
allow virtlogd_t spc_t:dir search;
allow virtlogd_t spc_t:file { open read };

EOF

/bin/checkmodule -M -m -o /tmp/contrail_issu_selinux.mod /tmp/contrail_issu_selinux.te
/bin/semodule_package -o /tmp/contrail_issu_selinux.pp -m /tmp/contrail_issu_selinux.mod
/sbin/semodule -i /tmp/contrail_issu_selinux.pp

# WARNING: docker-compose doesnt work properly with selinux,
# so it is needed to disable selinux temporary during upgrade
# procedure instead of configuring selinux policies
setenforce 0
getenforce
#

mkdir -p /var/crashes
chmod 755 /var/crashes
yum install -y docker python-docker-py libselinux-python
if ! yum install -y python-paunch ; then
    yum install -y --enablerepo=rhel-7-server-openstack-13-rpms python-paunch
fi
if ! yum install -y python27-python-pip ; then
    yum install -y --enablerepo=rhel-server-rhscl-7-rpms python27-python-pip
fi
if ! yum install -y python27-python-devel ; then
    yum install -y --enablerepo=rhel-server-rhscl-7-rpms python27-python-devel
fi

source scl_source enable python27
pip install --upgrade pip
pip install docker-compose
if [[ -n ${contrail_registry_cert_url} ]]; then
    registry_name=(${contrail_registry//:/ })
    mkdir -p /etc/docker/certs.d/${registry_name}
    (cd /etc/docker/certs.d/${registry_name}; curl -O ${contrail_registry_cert_url})
    (cd /etc/pki/ca-trust/source/anchors/; curl -O ${contrail_registry_cert_url})
    update-ca-trust
fi
if [[ ${contrail_registry_insecure,,} == 'true' ]]; then
    registry_name=(${contrail_registry//\// })
    found=0
    registries=`cat /etc/sysconfig/docker |grep INSECURE_REGISTRY |awk -F"--insecure-registry" '{$1="";print $0;}' |tr  "\"" " "`
    for reg in $registries; do if [[ ${reg} == ${contrail_registry} ]]; then found=1; fi; done
    if [[ ${found} -eq 0 ]]; then
        registry_string=`cat /etc/sysconfig/docker |grep INSECURE_REGISTRY |awk -F"INSECURE_REGISTRY=\"" '{print $2}'|tr "\"" " "`
        registry_string="${registry_string} --insecure-registry ${registry_name}"
        complete_string="INSECURE_REGISTRY=\"${registry_string}\""
        echo ${complete_string}
        if [[ `grep INSECURE_REGISTRY /etc/sysconfig/docker` ]]; then
            sed -i "s/^INSECURE_REGISTRY=.*/${complete_string}/" /etc/sysconfig/docker
        else
            echo ${complete_string} >> /etc/sysconfig/docker
        fi
    fi
fi

# enable docker live-restore
cur_opt_line=$(cat /etc/sysconfig/docker | grep 'OPTIONS=' | awk -F 'OPTIONS=' '{print($2)}' | tr -d "'")
if ! echo "$cur_opt_line" | grep -q 'log-driver' ; then
    cur_opt_line+=" --log-driver=journald"
fi
if ! echo "$cur_opt_line" | grep -q 'signature-verification' ; then
    cur_opt_line+=" --signature-verification=false"
fi
if ! echo "$cur_opt_line" | grep -q 'live-restore' ; then
    cur_opt_line+=" --live-restore"
fi
sed -i '/OPTIONS=/d' /etc/sysconfig/docker
echo "OPTIONS='$cur_opt_line'" >> /etc/sysconfig/docker

systemctl enable docker
systemctl restart docker
sleep 10
if [[ -n ${contrail_registry_user} && -n ${contrail_registry_password} ]]; then
    docker login -u ${contrail_registry_user} -p ${contrail_registry_password} ${contrail_registry}
fi

# enable local ssh connect for ISSU (ansible and issu sync)
user_name=${contrail_issu_ssh_user:-'heat-admin'}
if [[ -n "contrail_issu_ssh_public_key" && -n "contrail_issu_ssh_private_key" ]] ; then
    if [[ ! -d "/home/${user_name}/.ssh" ]] ; then
        mkdir -p /home/${user_name}/.ssh
        chmod 700 /home/${user_name}/.ssh
        chown ${user_name}:${user_name} /home/${user_name}/.ssh
    fi
    pushd /home/${user_name}/.ssh/
    if [[ ! -f ./authorized_keys ]] ; then
        echo "$contrail_issu_ssh_public_key" >> ./authorized_keys
        chmod 600 ./authorized_keys
        chown ${user_name}:${user_name} ./authorized_keys
    else
        echo "$contrail_issu_ssh_public_key" >> ./authorized_keys
    fi
    echo "$contrail_issu_ssh_public_key" > ./issu_id_rsa.pub
    chown ${user_name}:${user_name} ./issu_id_rsa.pub

    echo "$contrail_issu_ssh_private_key" > ./issu_id_rsa
    chmod 600 ./issu_id_rsa
    chown ${user_name}:${user_name} ./issu_id_rsa
fi
