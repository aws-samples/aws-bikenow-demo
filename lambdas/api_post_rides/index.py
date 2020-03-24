import boto3
import base64
import json
import os
import pymysql

DB_CREDS = os.environ['DB_CREDS']
DB_NAME = os.environ['DB_NAME']

def connection_info(db_creds):
  session = boto3.session.Session()
  client = session.client(
    service_name='secretsmanager'
  )

  get_secret_value_response = client.get_secret_value(SecretId=db_creds)

  if 'SecretString' in get_secret_value_response:
    secret = json.loads(get_secret_value_response['SecretString'])
  else:
    secret = json.loads(base64.b64decode(get_secret_value_response['SecretBinary']))
    
  return secret

# Expecting POST payload:
# {
#   'station_id': int,
#   'station_name': string,
#   'duration': int,
#   'price': float
# }
def lambda_handler(event, context):
  status_code = 400
  try:
    # print("[DEBUG] Received event: " + json.dumps(event, indent=2))
    user_id = event['requestContext']['identity']['cognitoIdentityId']
    input = json.loads(event['body'])
    sql = '''
          INSERT INTO	rideTransactions
          (
            userId
            ,stationId
            ,stationName
            ,duration
            ,price
          )
          VALUES
          (
            "{}"
            ,{}
            ,"{}"
            ,{}
            ,{}
          );
          '''.format(user_id, input['station_id'], input['station_name'], input['duration'], input['price'])

    print('[INFO] Connecting...')
    conn_info = connection_info(DB_CREDS)
    conn = pymysql.connect(conn_info['host'], user=conn_info['username'], passwd=conn_info['password'], db=conn_info['dbname'], connect_timeout=30)
    with conn.cursor() as cur:
      print('[INFO] Executing SQL: {}'.format(sql))
      cur.execute(sql)
    conn.commit()
    conn.close()
    status_code = 200
    output = '[SUCCESS] Executed insert query successfully.'

  except Exception as e:
    print('[ERROR] ', e)
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