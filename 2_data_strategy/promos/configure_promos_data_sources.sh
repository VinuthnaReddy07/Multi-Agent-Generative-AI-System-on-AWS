#!/bin/bash

source ~/environment/env.sh

# Get the bucket name from Secrets manager and insert the file into the bucket
aws s3 cp promos_kb_faqs.txt s3://$WORKSHOP_S3_BUCKET/promos_policy/
echo -e "\n\nPromo Policy files successfully uploaded to S3\n"

cd ..