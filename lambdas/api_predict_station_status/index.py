import boto3
import json
import decimal
import os
import sys
import math
from datetime import datetime

runtime_client = boto3.client('runtime.sagemaker')
MODEL_ENDPOINT_NAME = os.environ['MODEL_ENDPOINT_NAME']

def do_predict(data, endpoint_name, content_type):
  payload = '\n'.join(data)
  response = runtime_client.invoke_endpoint(EndpointName=endpoint_name, ContentType=content_type, Body=payload)
  result = response['Body'].read()
  result = result.decode('utf-8')
  result = result.split(',')
  preds = [round(float(num)) for num in result]
  return preds

def batch_predict(data, batch_size, endpoint_name, content_type):
  items = len(data)
  arrs = []

  for offset in range(0, items, batch_size):
    if offset+batch_size < items:
      results = do_predict(data[offset:(offset+batch_size)], endpoint_name, content_type)
      arrs.extend(results)
    else:
      arrs.extend(do_predict(data[offset:items], endpoint_name, content_type))

  return arrs

# Expecting POST payload:
# {
#   'year': int,
#   'month': int,
#   'day': int,
#   'hour': int,
#   'station_ids': [int]
# }
def lambda_handler(event, context):
  status_code = 400
  try:
    #print("Received event: " + json.dumps(event, indent=2))
    operation = event['httpMethod']
    if operation == 'POST':
      input = json.loads(event['body'])
      day_of_week = datetime.strptime('{}{}{}'.format(input['year'], input['month'], input['day']), '%Y%m%d').date().isoweekday() + 1
      test_data = [','.join(map(str, [station_id, input['year'], input['month'], input['day'], input['hour'], day_of_week])) for station_id in input['station_ids']]
      #print('Test data: {}'.format(json.dumps(test_data)))

      result = batch_predict(test_data, 100, MODEL_ENDPOINT_NAME, 'text/csv')
      output = json.dumps(dict(zip(input['station_ids'], result)))
      status_code = 200
    else:
      output = 'Unsupported method: {}'.format(operation)
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
    'body': output
  }

  print('[INFO] Query response: {}'.format(json.dumps(response)))

  return response
