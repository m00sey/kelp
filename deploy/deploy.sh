#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "==> Terraform: Creating infrastructure..."
cd terraform
terraform init
terraform apply -auto-approve
cd ..

echo "==> Waiting for droplet to be ready..."
sleep 30

echo "==> Ansible: Deploying application..."
cd ansible
ansible-galaxy collection install community.docker
ansible-playbook -i inventory.ini playbook.yml

echo "==> Done!"
cd ../terraform
terraform output kelp_url
