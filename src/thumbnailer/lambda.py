from logging import debug, info
from os import environ
from os.path import splitext
from tempfile import NamedTemporaryFile

from botocore.errorfactory import ClientError

from thumbnailer.image import resize
from thumbnailer.responses import (
    generate_binary_response,
    generate_favicon_response,
    generate_json_respone,
)
from thumbnailer.s3 import KeyNotFound, download_file_from_s3, upload_file_to_s3
from thumbnailer.util import configure_logging, DEFAULT_WIDTH, DEFAULT_HEIGHT


MEDIA_BUCKET_ENV_KEY = 'MEDIA_UPLOAD_BUCKET_NAME'
THUMBS_BUCKET_ENV_KEY = 'MEDIA_THUMBS_BUCKET_NAME'


def parse_path(path):
    info(f'parsing path: {path}')
    path = path.lstrip('/')
    parts = path.split('/')

    if len(parts) > 4 or len(parts) < 2:
        raise ValueError('URL path in unexpected format.')

    if len(parts) == 4:
        # width, height, user id, filename
        w = int(parts[0])
        h = int(parts[1])
        path = '/'.join(parts[2:4])
        debug(f'width: {w}, height: {h}, path: {path}')
        return w, h, path

    if len(parts) == 3:
        # w & h are the same
        w = int(parts[0])
        h = int(parts[0])
        path = '/'.join(parts[1:3])
        debug(f'width: {w}, height: {h}, path: {path}')
        return w, h, path

    if len(parts) == 2:
        # w & h are absent
        w = DEFAULT_WIDTH
        h = DEFAULT_HEIGHT
        path = '/'.join(parts[0:2])
        debug(f'width: {w}, height: {h}, path: {path}')
        return w, h, path


def format_thumbnail_key(keyname, width, height, ext):
    return f'{keyname}-{width}x{height}{ext}'


def setup_verbose_logging(evt):
    verboseLogging = False
    qs = evt.get('queryStringParameters')
    if qs and 'verbose' in qs:
        verboseLogging = True
    configure_logging(verboseLogging)


def handler(event, context):
    setup_verbose_logging(event)

    url_path = event.get('path')
    if not url_path:
        return generate_json_respone(400, f'url path not set')

    if url_path.endswith('favicon.ico'):
        return generate_favicon_response()

    source_bucket = environ.get(MEDIA_BUCKET_ENV_KEY)
    if not source_bucket:
        return generate_json_respone(
            400, f'source bucket not configured via "{MEDIA_BUCKET_ENV_KEY}"'
        )

    thumbs_bucket = environ.get(THUMBS_BUCKET_ENV_KEY)
    if not thumbs_bucket:
        return generate_json_respone(
            400, f'thumbs bucket not configured via "{THUMBS_BUCKET_ENV_KEY}"'
        )

    try:
        width, height, key = parse_path(url_path)
    except ValueError as e:
        return generate_json_respone(400, str(e))

    keyname, ext = splitext(key)
    thumbnail_key = format_thumbnail_key(keyname, width, height, ext)

    # info(f'retrieving s3://{source_bucket}:{key} ({ext}) to s3://{thumbs_bucket}:{thumbnail_key} at dims {width}x{height}')

    with NamedTemporaryFile(suffix=ext) as temp:
        try:
            download_file_from_s3(thumbs_bucket, thumbnail_key, temp.name)
        except KeyNotFound:
            info(
                f'{thumbs_bucket}/{thumbnail_key} not found. creating it from {source_bucket}/{key}'
            )
            source_stream = download_file_from_s3(source_bucket, key, temp.name)
            resize(temp.name, width, height)
            upload_file_to_s3(thumbs_bucket, thumbnail_key, temp.name)

        info(f'returning thumbnail from file {temp.name}')
        return generate_binary_response(200, temp.name)
