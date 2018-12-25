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

role=`hostname -s`
role_short=`echo $role | awk -F"-" '{print $2}'`

if [[ ! 'contrailcontrollerissu|contraildpdk|novacompute|contrailtsn|contrailcontroller' =~ "$role_short" ]] ; then
  echo "Skip Issu init script for $role"
  exit 0
fi

# WARNING: docker-compose doesnt work properly with selinux,
# so it is needed to disable selinux temporary during upgrade
# procedure instead of configuring selinux policies
#
# cat <<EOF > /tmp/contrail_issu_selinux.te
# module contrail_issu_selinux 1.0;
# require {
#         type ifconfig_t;
#         type user_tmp_t;
#         type http_port_t;
#         type haproxy_exec_t;
#         type var_lib_t;
#         type var_log_t;
#         type var_run_t;
#         type container_t;
#         type container_log_t;
#         type container_var_lib_t;
#         type container_var_run_t;
#         type svirt_t;
#         type bin_t;

#         class process setrlimit;
#         class capability { kill net_bind_service setgid setuid sys_resource };
#         class tcp_socket name_bind;
#         class sock_file { create link rename unlink setattr write };
#         class dir { create add_name mounton remove_name write setattr };
#         class file { create execute execute_no_trans getattr open read unlink write };

# }

# allow ifconfig_t user_tmp_t:dir mounton;
# allow ifconfig_t haproxy_exec_t:file { execute execute_no_trans open read };
# allow ifconfig_t http_port_t:tcp_socket name_bind;

# allow ifconfig_t self:capability { kill net_bind_service setgid setuid sys_resource };
# allow ifconfig_t self:process setrlimit;

# allow ifconfig_t var_lib_t:dir { add_name remove_name write };
# allow ifconfig_t var_lib_t:file { create getattr unlink open read write append };
# allow ifconfig_t var_lib_t:sock_file { create link rename unlink setattr write };

# allow svirt_t container_var_run_t:dir { add_name remove_name write };
# allow svirt_t container_var_run_t:sock_file { create unlink };

# allow container_t container_var_lib_t:dir { create setattr add_name remove_name write };
# allow container_t container_log_t:dir { create setattr add_name remove_name write };

# allow container_t var_log_t:dir { create setattr add_name remove_name write };
# allow container_t var_log_t:file { create getattr unlink open read write append };

# allow container_t bin_t:file write;

# EOF
# /bin/checkmodule -M -m -o /tmp/contrail_issu_selinux.mod /tmp/contrail_issu_selinux.te
# /bin/semodule_package -o /tmp/contrail_issu_selinux.pp -m /tmp/contrail_issu_selinux.mod
# /sbin/semodule -i /tmp/contrail_issu_selinux.pp
setenforce 0
getenforce
#

if [[ ! 'contrailcontroller' =~ "$role_short" ]] ; then
    mkdir -p /var/crashes
    chmod 755 /var/crashes
    yum install -y docker python-docker-py python27-python-pip libselinux-python
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
    systemctl enable docker
    systemctl restart docker
    sleep 5
    if [[ -n ${contrail_registry_user} && -n ${contrail_registry_password} ]]; then
        docker login -u ${contrail_registry_user} -p ${contrail_registry_password} ${contrail_registry}
    fi
fi # if [[ ! 'contrailcontroller' =~ "$role_short" ]]

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
