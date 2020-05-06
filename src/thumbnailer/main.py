#!/usr/bin/env python3

from sys import argv
from argparse import ArgumentParser
from logging import basicConfig, DEBUG, INFO, debug, info
from tempfile import NamedTemporaryFile
from os.path import splitext
from boto3 import resource

from PIL import Image


DEFAULT_WIDTH=222
DEFAULT_HEIGHT=222
DEFAULT_REGION='us-east-1'
THUMBNAIL_BUCKET_EXTENSION='-thumbnails'


def reorient_image(im):
    try:
        image_exif = im._getexif()
        image_orientation = image_exif[274]
        if image_orientation in (2,'2'):
            return im.transpose(Image.FLIP_LEFT_RIGHT)
        elif image_orientation in (3,'3'):
            return im.transpose(Image.ROTATE_180)
        elif image_orientation in (4,'4'):
            return im.transpose(Image.FLIP_TOP_BOTTOM)
        elif image_orientation in (5,'5'):
            return im.transpose(Image.ROTATE_90).transpose(Image.FLIP_TOP_BOTTOM)
        elif image_orientation in (6,'6'):
            return im.transpose(Image.ROTATE_270)
        elif image_orientation in (7,'7'):
            return im.transpose(Image.ROTATE_270).transpose(Image.FLIP_TOP_BOTTOM)
        elif image_orientation in (8,'8'):
            return im.transpose(Image.ROTATE_90)
        else:
            return im
    except (KeyError, AttributeError, TypeError, IndexError):
        return im


def crop_max_square(pil_img, dims, resample=Image.LANCZOS):
  '''
  Crops the largest sized square from the center area of the image, then resizes to the given dimensions.
  '''
  img = crop_center(pil_img, min(pil_img.size), min(pil_img.size))
  return img.resize(dims, resample=resample)


def crop_center(pil_img, crop_width, crop_height):
  '''
  crops the central area of the image
  '''
  img_width, img_height = pil_img.size
  return pil_img.crop(((img_width - crop_width) // 2,
                        (img_height - crop_height) // 2,
                        (img_width + crop_width) // 2,
                        (img_height + crop_height) // 2))


def resize(filename, width, height):
  info(f'resizing {filename} to {width}x{height}')
  dims = width, height
  debug(f'creating thumbnail with dimensions: {dims}')
  im = Image.open(filename)
  im_o = reorient_image(im)
  nim = crop_max_square(im_o, dims)
  nim.save(filename)


def download_file_from_s3(bucket, key, dest, region=DEFAULT_REGION):
  info(f'downloading s3://{bucket}:{key} to {dest}')
  s3 = resource('s3', region_name=region)
  s3.meta.client.download_file(bucket, key, dest)


def upload_file_to_s3(bucket, key, src, region=DEFAULT_REGION):
  info(f'uploading {src} to s3://{bucket}:{key}')
  s3 = resource('s3', region_name=region)
  s3.meta.client.upload_file(src, bucket, key)


def handler(event, context):
  for record in event['Records']:
    thumbnail_bucket = record['s3']['bucket']['name']
    key = record['s3']['object']['key']

    source_bucket = thumbnail_bucket.replace(THUMBNAIL_BUCKET_EXTENSION,'')

    keyname, ext = splitext(key)

    # https://medium.com/simple-thoughts-amplified/passing-variables-from-aws-api-gateway-to-lambda-3c5d8602081b
    width = DEFAULT_WIDTH
    height = DEFAULT_HEIGHT

    info(f'handling conversion of s3://{source_bucket}:{key} ({ext}) to s3://{thumbnail_bucket}:{key} at dims {width}x{height}')
    with NamedTemporaryFile(suffix=ext) as tmp:
      download_file_from_s3(source_bucket, key, tmp.name)
      resize(tmp.name, width, height)
      upload_file_to_s3(thumbnail_bucket, key, tmp.name)


def app(args):
  resize(args.filename, args.width, args.height)


def configure_logging(verbose):
  if verbose:
    level = DEBUG
  else:
    level = INFO

  basicConfig(
    format='[%(asctime)s][%(levelname)s] %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=level
  )


def main(argv):
  parser = ArgumentParser(prog=argv[0])
  parser.add_argument('-v', '--verbose', default=False, action='store_true')
  parser.add_argument('-f', '--filename')
  parser.add_argument('-dw', '--width', type=int, required=False, default=DEFAULT_WIDTH)
  parser.add_argument('-dh', '--height', type=int, required=False, default=DEFAULT_HEIGHT)

  args = parser.parse_args()
  configure_logging(args.verbose)

  debug(args)

  app(args)


if __name__ == '__main__':
    main(argv)
