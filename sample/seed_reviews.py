import boto3
import json
import os
from boto3.dynamodb.conditions import Key
from datetime import datetime

# Read environment variables
STATION_REVIEW_TABLE = 'station_review'
# Initialize boto3 clients
dynamodb = boto3.resource('dynamodb') 
table = dynamodb.Table(STATION_REVIEW_TABLE)

with open('seed_reviews.json') as f:
  reviews = json.load(f)

row_count = 0
for r in reviews:
  r['create_date'] = datetime.fromtimestamp(r['create_date'] / 1e3).strftime('%Y-%m-%d %H:%M:%S.%f')
  table.put_item(Item=r)
  row_count = row_count + 1
  if row_count % 1000 == 0:
    print('Processed {} records.'.format(row_count))

print('Finished seeding reviews.')