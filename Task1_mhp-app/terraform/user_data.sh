#!/bin/bash
set -euxo pipefail

# Log all setup output for debugging
exec > /var/log/user_data_setup.log 2>&1

# Install dependencies
dnf update -y
dnf install -y python3.12 python3.12-pip git

# Clone the repo
git clone -b ${branch_name} --single-branch ${repo_url} /home/ec2-user/app

# Set up the backend
cd /home/ec2-user/app/Task1_mhp-app/backend

python3.12 -m pip install -r requirements.txt

cp .env.example .env

# Fix ownership so ec2-user owns everything
chown -R ec2-user:ec2-user /home/ec2-user/app

# Start the server as ec2-user (not root)
sudo -u ec2-user bash -c '
  cd /home/ec2-user/app/Task1_mhp-app/backend
  nohup python3.12 run.py > /home/ec2-user/server.log 2>&1 &
'
