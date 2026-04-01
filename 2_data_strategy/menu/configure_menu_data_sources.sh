#!/bin/bash

source ~/environment/env.sh

aws s3 cp menu_records.json s3://$WORKSHOP_S3_BUCKET/menu/
echo -e "\n\nMenu items successfully uploaded to S3\n"

# Get the bucket name from Secrets manager and insert the file into the bucket
aws s3 cp menu_items_kb_faqs.txt s3://$WORKSHOP_S3_BUCKET/menu_policy/
echo -e "\n\nMenu Policy files successfully uploaded to S3\n"

cd ..