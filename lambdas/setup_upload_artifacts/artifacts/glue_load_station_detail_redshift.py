import boto3
import base64
import json
import pg
import sys
from awsglue.utils import getResolvedOptions
from botocore.exceptions import ClientError
from datetime import datetime, timedelta

# Helper class for interfacing with Redshift
class rs_common:
  # Returns connection and credential information from secrets manager
  @staticmethod
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

  # Returns a connection to the cluster
  @staticmethod
  def get_connection(db_creds):

    con_params = rs_common.connection_info(db_creds)
    
    rs_conn_string = "host=%s port=%s dbname=%s user=%s password=%s" % (con_params['host'], con_params['port'], con_params['dbname'], con_params['username'], con_params['password'])
    rs_conn = pg.connect(dbname=rs_conn_string)
    rs_conn.query("set statement_timeout = 1200000")
    
    return rs_conn

  # Submits a query to the cluster
  @staticmethod
  def query(con,statement):
      res = con.query(statement)
      return res
    
# Get job args
args = getResolvedOptions(sys.argv,['db_creds','glue_db'])
db_creds = args['db_creds']
glue_db = args['glue_db']

sql = '''
BEGIN;
CREATE TEMP TABLE staging_station_detail(LIKE public.station_detail);

INSERT INTO staging_station_detail
WITH cte AS
(
  SELECT 
      ROW_NUMBER() OVER (PARTITION BY station_id ORDER BY last_updated DESC) AS rn
      ,station_id
      ,"name" AS station_name
      ,capacity
      ,CAST(lon as FLOAT) AS lon
      ,CAST(lat AS FLOAT) AS lat
      ,TIMESTAMP 'epoch' + last_updated *INTERVAL '1 second' AS last_updated
  FROM {}.station_detail_history
)
SELECT
	station_id
    ,station_name
    ,capacity
    ,lon
    ,lat
    ,last_updated
FROM cte
WHERE rn = 1;

DELETE FROM public.station_detail
USING staging_station_detail s
WHERE station_detail.station_id = s.station_id;

INSERT INTO public.station_detail
SELECT * FROM staging_station_detail;

DROP TABLE staging_station_detail;

COMMIT;
'''.format(glue_db)

# Connect to database
print('Connecting...')
con = rs_common.get_connection(db_creds)

# Run SQL statement
print("Connected. Running query...")
result = rs_common.query(con, sql)

print(result)