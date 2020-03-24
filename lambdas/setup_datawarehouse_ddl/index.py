import boto3
import base64
import json
import sys
import os
import time
import psycopg2
import cfnresponse
from botocore.exceptions import ClientError
from datetime import datetime, timedelta

DB_CREDS = os.environ['DB_CREDS']
GLUE_DB = os.environ['GLUE_DB']
IAM_ROLE_ARN = os.environ['IAM_ROLE_ARN']
REDSHIFT_NAME = os.environ['REDSHIFT_NAME']

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

def lambda_handler(event, context):
  message = ''
  response = cfnresponse.FAILED
  cluster_status = ''

  # Get CloudFormation parameters
  cfn_stack_id = event.get('StackId')
  cfn_request_type = event.get('RequestType')
  cfn_physicalResourceId = context.log_stream_name if event.get('ResourceProperties.PhysicalResourceId') is None else event.get('ResourceProperties.PhysicalResourceId')

  if cfn_stack_id and cfn_request_type != 'Delete':
    try:
      # Wait for cluster to become available before trying to connect
      while cluster_status != 'Available':
        # Exit if Lambda will timeout before next sleep ends
        if context.get_remaining_time_in_millis() < (30 * 1000):
          message = 'Function will timeout. Exiting with failure.'
          print('ERROR: ', message)
          cfnresponse.send(event, context, response, 
            {
              'Message': message
            },
            cfn_physicalResourceId)

          return {
              'statusCode': 200,
              'body': json.dumps(message)
          }

        # Get cluster availability status every 30 seconds
        time.sleep(30)
        rsclient = boto3.client('redshift')
        clusters = rsclient.describe_clusters(ClusterIdentifier=REDSHIFT_NAME)
        cluster_status = clusters['Clusters'][0]['ClusterAvailabilityStatus']
        print('INFO: Cluster {} status: {}. Time remaining: {} ms.'.format(REDSHIFT_NAME, cluster_status, context.get_remaining_time_in_millis()))

      create_spectrum_schema_sql = ''
      create_status_history_table_sql = ''

      with open('sql/create_spectrum_schema.sql', 'r') as spectrum_sql_file:
        create_spectrum_schema_sql = spectrum_sql_file.read()
        create_spectrum_schema_sql = create_spectrum_schema_sql.replace('${GLUE_DB}', GLUE_DB).replace('${IAM_ROLE_ARN}', IAM_ROLE_ARN)

      with open('sql/create_status_history_table.sql', 'r') as table_sql_file:
        create_status_history_table_sql = table_sql_file.read()

      print('INFO: Connecting...')
      conn_info = connection_info(DB_CREDS)
      with psycopg2.connect(dbname=conn_info['dbname'], host=conn_info['host'], port=conn_info['port'], user=conn_info['username'], password=conn_info['password']) as conn:
        with conn.cursor() as cur:
          print('INFO: Executing SQL: {}'.format(create_spectrum_schema_sql))
          cur.execute(create_spectrum_schema_sql)
          print('INFO: Executing SQL: {}'.format(create_status_history_table_sql))
          cur.execute(create_status_history_table_sql)
          
      message = 'SUCCESS: Executed setup queries successfully.'
      response = cfnresponse.SUCCESS
    except Exception as e:
      print('ERROR: ', e)
      message = '{}'.format(e)
  else:
    message = 'INFO: Deleting function.'
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