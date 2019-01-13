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
iot = boto3.client('iot-data')
iot_host = os.environ.get('IOT_HOST')
iot_port = os.environ.get('IOT_PORT')
iot_topic = os.environ.get('IOT_TOPIC')

authorizer = CognitoUserPoolAuthorizer(
    cognitopoolname, provider_arns=[cognitopoolarn])

@app.route('/', methods=['GET'], authorizer=authorizer, cors=True)
def get_kvs_endpoint():
    #if path == '/publish_mqtt_servo':
    #    return publish_mqtt_servo(event,context)
      
    endpoint = "False"
    headers = {"Content-Type" : "application/json", "Access-Control-Allow-Origin": "*", "X-Content-Type-Options": "nosniff"}
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
        data={'url': url.get("HLSStreamingSessionURL","false")}
        res = {"statusCode" : 200,
              "body" : url.get("HLSStreamingSessionURL","false"),
              "headers" : headers}
        return res
    except ResourceNotFoundException:
        logger.debug(traceback.print_exc())
        endpoint = 'ResourceNotFoundException'
    except:
        logger.debug(traceback.print_exc())

    res = {"statusCode" : -1,
       "body" : endpoint,
       "headers" : headers}
    return res

@app.route('/mqtt/{angle}', methods=['GET'], authorizer=authorizer, cors=True)
def publish_mqtt_servo(angle):
    logger.debug('/mqtt/{angle}')
    logger.debug(angle)

    headers = {"Content-Type" : "application/json", "Access-Control-Allow-Origin": "*", "X-Content-Type-Options": "nosniff"}
    try:
        iot.publish(
            topic=iot_topic,
            qos=1,
            payload="%s" % (angle)
        )
        resp = {"statusCode" : 200,
            "body" : "ok",
            "headers" : headers
        }
        return resp
    except:
        logger.debug(traceback.print_exc())

    resp = {"statusCode" : -1,
       "body" : "error",
       "headers" : headers}
    return resp
