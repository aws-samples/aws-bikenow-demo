import boto3
import json
import os
from boto3.dynamodb.conditions import Key
from datetime import datetime

# Read environment variables
STATION_REVIEW_TABLE = os.environ['STATION_REVIEW_TABLE']
# Initialize boto3 clients
dynamodb = boto3.resource('dynamodb') 
table = dynamodb.Table(STATION_REVIEW_TABLE)

def lambda_handler(event, context):
  status_code = 400
  try:
    # print("[DEBUG] Received event: " + json.dumps(event, indent=2))
    user_id = event['requestContext']['identity']['cognitoIdentityId']
    input = json.loads(event['body'])
    input['user_id'] = user_id
    input['create_date'] = str(datetime.utcnow())
    
    print('[DEBUG] Received input: ' + json.dumps(input))
    table.put_item(Item=input)

    output = '[SUCCESS] Review posted successfully.'
    status_code = 200

  except Exception as e:
    print('ERROR: ', e)
    output = '{}'.format(e)

  # Construct API response
  response = {
    'statusCode': status_code,
    'headers': {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Credentials': True,
      'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent',
      'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS,HEAD,PATCH',
      'Content-Type': 'application/json'
    },
    'body': json.dumps(output)
  }

  print('[INFO] Query response: {}'.format(json.dumps(response)))

  return response