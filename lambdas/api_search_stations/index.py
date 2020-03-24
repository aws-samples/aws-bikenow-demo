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
es_url = '{}/{}/{}/_search'.format(es_host, es_index, es_type)
headers = { 'Content-Type': 'application/json' }

def lambda_handler(event, context):
  # Construct the search query
  query = {
    'size': 1000,
    'query': {
      'query_string': {
        'query': event['queryStringParameters']['q'],
        'fields': ['name']
      }
    }
  }
  print('[INFO] Query body: {}'.format(json.dumps(query)))

  # Get search result from ES
  r = requests.get(es_url, auth = awsauth, headers = headers, data = json.dumps(query))

  # Construct API response
  response = {
    'statusCode': r.status_code,
    'headers': {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Credentials': True,
      'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent',
      'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS,HEAD,PATCH',
      'Content-Type': 'application/json'
    },
    'body': r.text
  }
  print('[INFO] Query response: {}'.format(json.dumps(response)))

  return response