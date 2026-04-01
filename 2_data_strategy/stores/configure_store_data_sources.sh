#!/bin/bash

source ~/environment/env.sh

# Install required Python dependencies
echo "Installing required Python dependencies..."
pip3 install pymysql tabulate --quiet --user
echo "Dependencies installed successfully."
echo

# Load records to the RDS DB
python3 stores_load_helper_script.py
echo -e "\n\nSample stores records successfully inserted into RDS database\n"

aws s3 cp store_kb_faqs.txt s3://$WORKSHOP_S3_BUCKET/stores_policy/
echo -e "\n\nStores Policy files successfully uploaded to S3\n"

cd ..