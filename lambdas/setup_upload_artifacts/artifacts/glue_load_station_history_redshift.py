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
CREATE TEMP TABLE staging_station_status_history(LIKE public.station_status_history);

INSERT INTO staging_station_status_history
SELECT
	station_id
	,num_bikes_available
	,is_installed
	,is_returning
	,is_renting
	,TIMESTAMP 'epoch' + last_reported *INTERVAL '1 second' AS last_reported
	,year || month || day || hour AS load_partition
FROM {}.station_status_history
WHERE
	year || month || day || hour > (SELECT NVL(MAX(load_partition), '0000000000') FROM public.station_status_history);

DELETE FROM public.station_status_history
USING staging_station_status_history s
WHERE 
	station_status_history.station_id = s.station_id
	AND station_status_history.last_reported = s.last_reported;
	
INSERT INTO public.station_status_history
SELECT * FROM staging_station_status_history;

DROP TABLE staging_station_status_history;

COMMIT;
'''.format(glue_db)

# Connect to database
print('Connecting...')
con = rs_common.get_connection(db_creds)

# Run SQL statement
print("Connected. Running query...")
result = rs_common.query(con, sql)

print(result)