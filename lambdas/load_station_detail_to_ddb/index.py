import json
import time
import datetime
import urllib.request
import boto3
import decimal
import os

# Read environment variables
STATION_DETAIL_URL = os.environ['STATION_DETAIL_URL']
STATION_DETAIL_TABLE = os.environ['STATION_DETAIL_TABLE']

# Initialize boto3 clients
dynamodb = boto3.resource('dynamodb') 
table = dynamodb.Table(STATION_DETAIL_TABLE)

def lambda_handler(event, context):
  message = ''
  try:
    # Request latest bike station details data
    web_request = urllib.request.urlopen(STATION_DETAIL_URL)
    station_detail_data = json.loads(web_request.read().decode())

    # Get last_update from root
    last_updated = int(station_detail_data['last_updated'])

    # Parse through each bike station and update table
    station_count = 0
    with table.batch_writer(overwrite_by_pkeys=['station_id']) as batch:
      for station in station_detail_data['data']['stations']:
        station_count += 1
        new_station = {}
        new_station['station_id'] = int(station['station_id'])
        new_station['name'] = str(station['name'])
        new_station['lat'] = str(station['lat'])
        new_station['lon'] = str(station['lon'])
        new_station['last_updated'] = last_updated

        if 'capacity' in station:
          new_station['capacity'] = int(station['capacity'])

        batch.put_item(Item = new_station)
    message = '[INFO] Updated {} stations.'.format(station_count)
  except Exception as e:
    message = '[ERROR] {}'.format(e)
    
  print(message)

