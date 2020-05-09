from logging import info
from boto3 import resource
from botocore.exceptions import ClientError

DEFAULT_REGION='us-east-1'

class KeyNotFound(Exception):
  def __init__(self, message):
    super().__init__(message)

def download_file_from_s3(bucket, key, dest, region=DEFAULT_REGION):
  info(f'downloading s3://{bucket}:{key} to {dest}')
  s3 = resource('s3', region_name=region)

  try:
      s3_obj = s3.Object(bucket, key)
      s3_obj.download_file(dest)
      info(f'{key} downloaded to {dest}')
  except Exception as e: #  botocore.exceptions.ClientError
      info(f'NOT FOUND: {bucket}/{key}: {e}')
      if e.response['Error']['Code'] == "404":
        raise KeyNotFound(f'{bucket}/{key} not found')


def upload_file_to_s3(bucket, key, src, region=DEFAULT_REGION):
  info(f'uploading {src} to s3://{bucket}:{key}')
  s3 = resource('s3', region_name=region)
  s3_obj = s3.Object(bucket, key)
  s3_obj.upload_file(src)
