#!/bin/bash

set -e

exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

export DEBIAN_FRONTEND=noninteractive

apt update -y
apt-get upgrade -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold"

apt-get install -y python3-pip python3-venv git

echo "Starting deployment..."

cd /home/ubuntu || exit

git clone https://github.com/jt96/hybrid-rag-infrastructure.git

chown -R ubuntu:ubuntu hybrid-rag-infrastructure

cd hybrid-rag-infrastructure || exit
python3 -m venv venv
# shellcheck disable=SC1091
source venv/bin/activate

pip install torch==2.9.1 torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

echo "GOOGLE_API_KEY=placeholder" > .env
echo "PINECONE_API_KEY=placeholder" >> .env
echo "PINECONE_INDEX_NAME=placeholder" >> .env

echo "Setup Complete! App is ready to run."