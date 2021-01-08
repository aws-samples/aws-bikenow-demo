import boto3
import base64
import json
import sys
import os
import time
import pymysql
import cfnresponse
from botocore.exceptions import ClientError
from datetime import datetime, timedelta

DB_CREDS = os.environ['DB_CREDS']
DB_NAME = os.environ['DB_NAME']
DB_INSTANCE = os.environ['DB_INSTANCE']

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
    
  print("[DEBUG] Secret: " + json.dumps(secret, indent=2))
  return secret

def lambda_handler(event, context):
  message = ''
  response = cfnresponse.FAILED
  instance_status = ''

  # Get CloudFormation parameters
  cfn_stack_id = event.get('StackId')
  cfn_request_type = event.get('RequestType')
  cfn_physicalResourceId = context.log_stream_name if event.get('ResourceProperties.PhysicalResourceId') is None else event.get('ResourceProperties.PhysicalResourceId')

  if cfn_stack_id and cfn_request_type != 'Delete':
    try:
      # Wait for instance to become available before trying to connect
      while instance_status.lower() != 'available':
        # Exit if Lambda will timeout before next sleep ends
        if context.get_remaining_time_in_millis() < (30 * 1000):
          message = 'Function will timeout. Exiting with failure.'
          print('[ERROR] ', message)
          cfnresponse.send(event, context, response, 
            {
              'Message': message
            },
            cfn_physicalResourceId)

          return {
              'statusCode': 200,
              'body': json.dumps(message)
          }

        # Get instance availability status every 30 seconds
        time.sleep(30)
        rdsclient = boto3.client('rds')
        dbinstance = rdsclient.describe_db_instances(DBInstanceIdentifier=DB_INSTANCE)
        instance_status = dbinstance['DBInstances'][0]['DBInstanceStatus']
        print('[INFO] DBInstance {} status: {}. Time remaining: {} ms.'.format(DB_NAME, instance_status, context.get_remaining_time_in_millis()))

      sql_queries = [
        'DROP TABLE IF EXISTS rideTransactions;'
        ,'''
        CREATE TABLE rideTransactions
          (
            id INT NOT NULL AUTO_INCREMENT
            ,userId VARCHAR(64)
            ,stationId INT
            ,stationName VARCHAR(128)
            ,duration INT
            ,price DECIMAL(5,2)
            ,createdDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ,PRIMARY KEY (id)
          );
        '''
        ,'CREATE INDEX idxRideUserId ON rideTransactions(userId);'
        ,'CREATE INDEX idxRideStationId ON rideTransactions(stationId);'
      ]

      print('[INFO] Connecting...')
      conn_info = connection_info(DB_CREDS)
      print("[DEBUG] DB_CREDS: " + json.dumps(DB_CREDS, indent=2))
      conn = pymysql.connect(host=conn_info['host'], user=conn_info['username'], password=conn_info['password'], database=conn_info['dbname'], connect_timeout=30)
      with conn.cursor() as cur:
        for sql in sql_queries:
          print('[INFO] Executing SQL: {}'.format(sql))
          cur.execute(sql)
      conn.commit()
      conn.close()
          
      message = '[SUCCESS] Executed setup queries successfully.'
      response = cfnresponse.SUCCESS
    except Exception as e:
      print('[ERROR] ', e)
      message = '{}'.format(e)
  else:
    message = '[INFO] Deleting function.'
    response = cfnresponse.SUCCESS

  cfnresponse.send(event, context, response, 
    {
      'Message': message
    },
    cfn_physicalResourceId)

  return {
      'statusCode': 200,
      'body': json.dumps(message)
  }