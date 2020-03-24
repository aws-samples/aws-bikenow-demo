import json
import boto3
import cfnresponse
import os
from os import listdir
from os.path import isfile, join

SCRIPT_BUCKET = os.environ['SCRIPT_BUCKET']
SCRIPT_FOLDER = os.environ['SCRIPT_FOLDER']

def lambda_handler(event, context):
  s3 = boto3.resource('s3')
  response = cfnresponse.FAILED

  # Get CloudFormation parameters
  cfn_stack_id = event.get('StackId')
  cfn_request_type = event.get('RequestType')
  cfn_physicalResourceId = context.log_stream_name if event.get('ResourceProperties.PhysicalResourceId') is None else event.get('ResourceProperties.PhysicalResourceId')

  message = ''
  
  if cfn_stack_id and cfn_request_type != 'Delete':
    try:
      # Copy Glue script files to S3 bucket
      script_path = 'artifacts'
      my_bucket = s3.Bucket(SCRIPT_BUCKET)
      for path, subdirs, files in os.walk(script_path):
        path = path.replace("\\","/")
        directory_name = path.replace(script_path,"")

        for file in files:
          my_bucket.upload_file(os.path.join(path, file), SCRIPT_FOLDER + directory_name + '/' + file)

      message = 'INFO: Copied script files to: ' + SCRIPT_BUCKET
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
    'body': message
  }