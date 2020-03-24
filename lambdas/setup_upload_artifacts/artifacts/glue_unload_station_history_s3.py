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
args = getResolvedOptions(sys.argv,['db_creds','glue_db','rs_iam_role','dest_bucket'])
db_creds = args['db_creds']
glue_db = args['glue_db']
rs_iam_role = args['rs_iam_role']
dest_bucket = args['dest_bucket']
utc_query = datetime.utcnow() - timedelta(hours=1)

sql = '''
unload (
'select avg_num_bikes_available
	,station_id
    ,date_part(y, update_timestamp)::int as year
    ,date_part(mon, update_timestamp)::int as month
    ,date_part(d, update_timestamp)::int as day
    ,date_part(h, update_timestamp)::int as hour
    ,date_part(dw, update_timestamp)::int as day_of_week
from public.station_status_history'
)
to 's3://{}/unload/station_status_history_'
iam_role '{}'
delimiter as ','
allowoverwrite
parallel off;
'''.format(dest_bucket, rs_iam_role)

# Connect to database
print('Connecting...')
con = rs_common.get_connection(db_creds)

# Run SQL statement
print("Connected. Running query...")
result = rs_common.query(con, sql)

print(result)