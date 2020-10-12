import json
import decimal
import boto3
import os
from boto3.dynamodb.types import TypeDeserializer
from datetime import datetime

client = boto3.client('firehose')
comprehend_client = boto3.client('comprehend')
FIREHOSE_STREAM_NAME = os.environ['FIREHOSE_STREAM_NAME']

def lambda_handler(event, context):
    record_count = 0
    for record in event['Records']:
      try:
        # Get the primary key of the station
        station_id = record['dynamodb']['Keys']['station_id']['N']
        if record['eventName'] != 'REMOVE':
          new_image = record['dynamodb']['NewImage']

          new_dt = datetime.strptime(new_image['create_date']['S'], '%Y-%m-%d %H:%M:%S.%f')
          new_image['create_date'] = {'N': int(new_dt.timestamp())}

          sentiment = comprehend_client.detect_sentiment(
            Text=new_image['review']['S']
            ,LanguageCode='en'
          )

          new_image['sentiment'] = {'S': sentiment['Sentiment']}
          new_image['sentiment_mixed'] = {'N': sentiment['SentimentScore']['Mixed']}
          new_image['sentiment_neutral'] = {'N': sentiment['SentimentScore']['Neutral']}
          new_image['sentiment_positive'] = {'N': sentiment['SentimentScore']['Positive']}
          new_image['sentiment_negative'] = {'N': sentiment['SentimentScore']['Negative']}

          deserializer = TypeDeserializer()
          payload = json.dumps({k: deserializer.deserialize(v) for k, v in new_image.items()}, cls=DecimalEncoder)
      
          response = client.put_record(
            DeliveryStreamName = FIREHOSE_STREAM_NAME,
            Record = { 'Data': payload + '\r\n' }
          )

          print('[DEBUG] Processed station_id: {}. Request response: {}'.format(station_id, payload))
          record_count += 1
      except Exception:
        pass # JSON encoder to Decimal sometimes throws exception with inexact rounding. Skip these. Fix later.

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