import json
import decimal
import boto3
import os
import requests
from requests_aws4auth import AWS4Auth
from boto3.dynamodb.types import TypeDeserializer

# Get Lambda run-time credentials
region = os.environ['REGION']
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token = credentials.token)

# Build Elasticsearch endpoint
es_host = 'https://{}'.format(os.environ['ES_ENDPOINT'])
es_index = 'stations'
es_type = 'station'
es_url = '{}/{}/{}/'.format(es_host, es_index, es_type)
headers = { 'Content-Type': 'application/json' }

def lambda_handler(event, context):
  delete_count = 0
  update_count = 0
  for record in event['Records']:
    # Get the primary key of the station
    station_id = record['dynamodb']['Keys']['station_id']['N']
    # If deleted form DynamoDB, remove from ES
    if record['eventName'] == 'REMOVE':
      r = requests.delete('{}{}'.format(es_url, station_id), auth = awsauth)
      delete_count += 1
    # Update record so we don't overwrite station details
    else:
      # Deserialize the image
      new_image = record['dynamodb']['NewImage']
      deserializer = TypeDeserializer()
      deserialized_image = json.dumps({k: deserializer.deserialize(v) for k, v in new_image.items()}, cls=DecimalEncoder)
      payload = {
        'doc': json.loads(deserialized_image),
        'doc_as_upsert': True
      }

      # Insert or update to ES
      r = requests.post('{}{}/_update'.format(es_url, station_id), auth = awsauth, headers = headers, json = payload)
      update_count += 1
    print('[DEBUG] Processed station_id: {}. Request response: {}'.format(station_id, r.text))
    
  message = '[INFO] Deleted {} stations. Insert or updated {} stations.'.format(delete_count, update_count)
  print(message)

'''
Decode Decimal types to JSON numeric value
'''
class DecimalEncoder(json.JSONEncoder):
  def default(self, o):
    if isinstance(o, decimal.Decimal):
      if o == int(o):
          return int(o)
      else:
          return float(o)
    return super(DecimalEncoder, self).default(o)