import json
import decimal
import boto3
import os
from boto3.dynamodb.types import TypeDeserializer

client = boto3.client('firehose')
FIREHOSE_STREAM_NAME = os.environ['FIREHOSE_STREAM_NAME']

def lambda_handler(event, context):
    record_count = 0
    for record in event['Records']:
      # Get the primary key of the station
      station_id = record['dynamodb']['Keys']['station_id']['N']
      if record['eventName'] != 'REMOVE':
        new_image = record['dynamodb']['NewImage']
        deserializer = TypeDeserializer()
        payload = json.dumps({k: deserializer.deserialize(v) for k, v in new_image.items()}, cls=DecimalEncoder)
        
        response = client.put_record(
          DeliveryStreamName = FIREHOSE_STREAM_NAME,
          Record = { 'Data': payload + '\r\n' }
        )

        print('[DEBUG] Processed station_id: {}. Request response: {}'.format(station_id, payload))
        record_count += 1

    print("[INFO] Processed {} records.".format(str(record_count)))

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