import json
import time
import datetime
import urllib.request
import boto3
import decimal
import os

# Read environment variables
STATION_STATUS_URL = os.environ['STATION_STATUS_URL']
STATION_STATUS_TABLE = os.environ['STATION_STATUS_TABLE']

# Initialize boto3 clients
dynamodb = boto3.resource('dynamodb') 
table = dynamodb.Table(STATION_STATUS_TABLE)

def lambda_handler(event, context):
  message = ''
  try:
    # Request latest bike station status data
    web_request = urllib.request.urlopen(STATION_STATUS_URL)
    station_status_data = json.loads(web_request.read().decode())

    # Parse through each bike station and update table
    station_count = 0
    with table.batch_writer(overwrite_by_pkeys=['station_id']) as batch:
      for station in station_status_data['data']['stations']:
        station_count += 1
        new_station = {}
        new_station['station_id'] = int(station['station_id'])
        new_station['last_reported'] = int(station['last_reported'])
        new_station['num_bikes_available'] = int(station['num_bikes_available'])
        new_station['is_installed'] = bool(station['is_installed'])
        new_station['is_returning'] = bool(station['is_returning'])
        new_station['is_renting'] = bool(station['is_renting'])
        
        # new_station['num_bikes_disabled'] = int(station['num_bikes_disabled'])
        # new_station['num_docks_available'] = int(station['num_docks_available'])
        # new_station['num_ebikes_available'] = int(station['num_ebikes_available'])
        # new_station['num_docks_disabled'] = int(station['num_docks_disabled'])
        batch.put_item(Item = new_station)
    message = '[INFO] Updated {} stations.'.format(station_count)
  except Exception as e:
    message = '[ERROR] {}'.format(e)
    
  print(message)

