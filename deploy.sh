#!/bin/sh

ENV_FILE = $1

if [ ! -f "$ENV_FILE" ];
  echo "Usage: $0 /path/to/env/file"
  exit 1
fi

source ${ENV_FILE}

TEST_OBJECT="063c88b8-beb6-4f1c-9496-2742ef8bef32/091bb0bf-b460-483b-ae68-0d1047f12867"
EXT="jpg"
DIM_W=222
DIM_H=222
TEST_KEY="${TEST_OBJECT}-${DIM_W}x${DIM_H}.${EXT}"
TEST_PATH="${TEST_OBJECT}.${EXT}"

function main() {
  if [ -f requirements.txt ];
  then
    rm requirements.txt
  fi

  poetry export -f requirements.txt > requirements.txt
  archive=$(lgw lambda-archive --config-file=lgw.cfg)
  lgw lambda-deploy --config-file=lgw.cfg --lambda-file=${archive}
  #lambda_smoke_test
  lgw gw-deploy --verbose --config-file=lgw.cfg
  lgw domain-add --config-file=lgw.cfg
  #api_smoke_test
}

function lambda_smoke_test {
  echo "Testing lambda invocation and lambda response."
  AWS_PAGER="" aws lambda invoke --function-name elektrum-thumbnailer --payload "'`cat tests/payload.json|base64`'" response.json
  actual=$(cat response.json| jq -r .body | base64 -d -i - -o - | identify - | awk '{print $3}')
  expected="${DIM_W}x${DIM_H}"
  if [ "${actual}" != "${expected}" ];
  then
    echo "Lambda invocation failed to resize thumbnail as expected."
    exit 1
  fi
  if [ -e response.json ];
  then
    rm -f response.json
  fi
  echo "Lambda invocation and lambda response tested successfully."
}

function api_smoke_test {
  echo "Testing API response and thumbnail copying."
  aws s3 rm s3://${MEDIA_THUMBS_BUCKET_NAME}/${TEST_KEY}
  aws s3 ls s3://${MEDIA_THUMBS_BUCKET_NAME}/${TEST_KEY}
  if [ $? -eq 0 ]; then
      echo 'Deleting test thumbnail did not succeed.'
      exit 1
  else
      echo 'Thumbnail does not exist, as expected.'
  fi

  echo "downloading thumbnail from: https://${AWS_API_DOMAIN_NAME}/${DIM_W}/${DIM_H}/${TEST_PATH}"
  curl --verbose https://${AWS_API_DOMAIN_NAME}/${DIM_W}/${DIM_H}/${TEST_PATH}

  aws s3 ls s3://${MEDIA_THUMBS_BUCKET_NAME}/${TEST_KEY}
  if [ $? -eq 0 ]; then
      echo 'Thumbnail created successfully.'
  else
      echo 'Creating test thumbnail did not succeed.'
      exit 1
  fi
  aws s3 rm s3://${MEDIA_THUMBS_BUCKET_NAME}/${TEST_KEY}
  echo "API tested successfully."
}

main
