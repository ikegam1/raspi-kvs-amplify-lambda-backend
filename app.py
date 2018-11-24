from chalice import Chalice,CognitoUserPoolAuthorizer

import logging
import os
import json
import boto3
import traceback
from botocore.vendored import requests

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

app = Chalice(app_name='auth-raspi-stream')
cognito = boto3.client('cognito-idp')
kvs = boto3.client('kinesisvideo',region_name='ap-northeast-1')
streamname = os.environ.get('KVS_STREAM_NAME')
streamarn = os.environ.get('KVS_STREAM_ARN')
cognitopoolarn = os.environ.get('COGNITO_POOL_ARN')
cognitopoolname = os.environ.get('COGNITO_POOL_NAME')
streamarn = os.environ.get('KVS_STREAM_ARN')
authorizer = CognitoUserPoolAuthorizer(
    cognitopoolname, provider_arns=[cognitopoolarn])

@app.route('/', methods=['GET'], content_types=['application/json'], authorizer=authorizer, cors=True)
def get_kvs_endpoint():
    endpoint = False
    headers = {"Content-Type" : "application/json", "Access-Control-Allow-Origin": "'*'"}
    try:
        endpoint = kvs.get_data_endpoint(
            StreamARN=streamarn,
            APIName='GET_HLS_STREAMING_SESSION_URL'
        )
        logger.debug(str(endpoint))
        if 'DataEndpoint' not in endpoint:
            raise Exception
        kvam = boto3.client('kinesis-video-archived-media',endpoint_url=endpoint.get('DataEndpoint'))
        url = kvam.get_hls_streaming_session_url(
            StreamARN=streamarn,
            Expires=3600,
            PlaybackMode="LIVE"
        )
        logger.debug(str(url))
        if 'HLSStreamingSessionURL' not in url:
            raise Exception
        res = {"statusCode" : 200,
              "body" : url.get("HLSStreamingSessionURL",False),
              "headers" : headers}
        return res
    except ResourceNotFoundException:
        logger.debug(traceback.print_exc())
        endpoint = 'ResourceNotFoundException'
    except:
        logger.debug(traceback.print_exc())
        pass

    res = {"statusCode" : -1,
       "body" : endpoint,
       "headers" : headers}
    return res

