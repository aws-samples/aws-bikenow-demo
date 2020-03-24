import boto3
import json
import os
import decimal
from boto3.dynamodb.conditions import Key

# Read environment variables
STATION_REVIEW_TABLE = os.environ['STATION_REVIEW_TABLE']
STATION_REVIEW_GSI = os.environ['STATION_REVIEW_GSI']
# Initialize boto3 clients
dynamodb = boto3.resource('dynamodb') 
table = dynamodb.Table(STATION_REVIEW_TABLE)

def lambda_handler(event, context):
  status_code = 400
  try:
    # print("[DEBUG] Received event: " + json.dumps(event, indent=2))
    output = None
    if event['queryStringParameters']:
      station_id = int(event['queryStringParameters']['stationId'])
      query_result = table.query(KeyConditionExpression=Key('station_id').eq(station_id))
    else:
      user_id = event['requestContext']['identity']['cognitoIdentityId']
      query_result = table.query(IndexName=STATION_REVIEW_GSI, KeyConditionExpression=Key('user_id').eq(user_id))

    output = query_result['Items']
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
    'body': json.dumps(output, cls=DecimalEncoder)
  }

  print('[INFO] Query response: {}'.format(json.dumps(response)))

  return response

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