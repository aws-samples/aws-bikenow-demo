import json
import os
from os import listdir
from os.path import isfile, join

SCRIPT_BUCKET = 'mybucket'
SCRIPT_FOLDER = 'artifacts'

# Copy Glue script files to S3 bucket
script_path = 'artifacts'
#my_bucket = s3.Bucket(SCRIPT_BUCKET)

for path, subdirs, files in os.walk(script_path):
	path = path.replace("\\","/")
	directory_name = path.replace(script_path, "")
	
	for file in files:
		print(SCRIPT_FOLDER + directory_name + '/' + file)