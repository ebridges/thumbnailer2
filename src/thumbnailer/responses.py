from base64 import b64encode
from magic import Magic
from json import dumps
from logging import debug, info


def generate_json_respone(httpStatusCode, message):
  mesg = {
    "message": message
  }
  debug(f'response {httpStatusCode} with message: {message}')
  return {
    "isBase64Encoded": False,
    "statusCode": httpStatusCode,
    "headers": { "content-type": "text/json" },
    "body": dumps(mesg)
}


def generate_binary_response(httpStatusCode, filename):
  mime = Magic(mime=True)
  mimetype = mime.from_file(filename)
  
  info(f'generating response of {httpStatusCode} for {filename} of type {mimetype}')

  with open(filename, 'rb') as file:
    enc = b64encode(file.read())
    encoded = enc.decode('utf-8')

  return {
    "isBase64Encoded": True,
    "statusCode": httpStatusCode,
    "headers": { "content-type": mimetype },
    "body": encoded
  }


def generate_favicon_response():
  from thumbnailer import favicon_encoded

  return {
    "isBase64Encoded": True,
    "statusCode": 200,
    "headers": { "content-type": "image/x-icon" },
    "body": favicon_encoded
  }
