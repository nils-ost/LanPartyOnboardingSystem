#!/bin/bash

echo -e "\n\n"
read -p "Do you like to set up prometheus metrics endpoints for monitoring LPOS? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    sed -i 's/enable_monitoring.*/enable_monitoring: true/g' ansible/vars.yml
else
    sed -i 's/enable_monitoring.*/enable_monitoring: false/g' ansible/vars.yml
fi

apt update
apt install -y openssh-server python3 virtualenv
virtualenv -p /usr/bin/python3 venv
venv/bin/pip install ansible

echo -e "\n\n#####################################\nHandover to Ansible\n#####################################\n\n"
cd ansible
../venv/bin/ansible-galaxy install -r roles/requirements.yml
../venv/bin/ansible-playbook local.yml
