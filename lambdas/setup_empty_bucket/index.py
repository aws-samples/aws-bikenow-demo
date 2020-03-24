import json
import boto3
import cfnresponse
import os
from os import listdir
from os.path import isfile, join

SCRIPT_BUCKET = os.environ['SCRIPT_BUCKET']

def lambda_handler(event, context):
  s3 = boto3.resource('s3')
  response = cfnresponse.FAILED

  # Get CloudFormation parameters
  cfn_stack_id = event.get('StackId')
  cfn_request_type = event.get('RequestType')
  cfn_physicalResourceId = context.log_stream_name if event.get('ResourceProperties.PhysicalResourceId') is None else event.get('ResourceProperties.PhysicalResourceId')

  message = ''
  
  # If CloudFormation is being deleted, empty S3 bucket
  if cfn_stack_id and cfn_request_type == 'Delete':
    try:
      bucket = s3.Bucket(SCRIPT_BUCKET)
      bucket.objects.delete()
      message = 'INFO: Deleted data from S3 bucket: ' + SCRIPT_BUCKET
      response = cfnresponse.SUCCESS
    except botocore.exceptions.ClientError as e:
      # If a client error is thrown, then check that it was a 404 error.
      # If it was a 404 error, then the bucket does not exist.
      error_code = int(e.response['Error']['Code'])
      if error_code == 404:
        message = 'WARNING: Bucket does not exist: ' + SCRIPT_BUCKET
        response = cfnresponse.SUCCESS
      else:
        print('ERROR: ', e)
        message = '{}'.format(e)
    except Exception as e:
      print('ERROR: ', e)
      message = '{}'.format(e)
  else:
    message = 'INFO: Creating or updating function.'
    response = cfnresponse.SUCCESS

  cfnresponse.send(event, context, response, 
    {
      'Message': message
    },
    cfn_physicalResourceId)
  
  return {
    'statusCode': 200,
    'body': message
  }