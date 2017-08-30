from __future__ import print_function

import os

import boto3
import urllib.parse
from aws_requests_auth.aws_auth import AWSRequestsAuth
from elasticsearch import Elasticsearch, RequestsHttpConnection, ElasticsearchException
from botocore.exceptions import ClientError
from botocore.vendored import requests
import json

CFN_SUCCESS = 'SUCCESS'
CFN_FAILED = 'FAILED'
TMP_KIBANA_JSON_PATH = '/tmp/kibana_dashboards.json'

s3 = boto3.client('s3')
s3_resource = boto3.resource('s3')
es_index = 'metadata'


def make_elasticsearch_client(elasticsearch_endpoint):
    awsauth = AWSRequestsAuth(
        aws_access_key=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
        aws_token=os.environ['AWS_SESSION_TOKEN'],
        aws_host=elasticsearch_endpoint,
        aws_region=os.environ['AWS_REGION'],
        aws_service='es'
    )
    return Elasticsearch(
        hosts=['{0}:443'.format(elasticsearch_endpoint)],
        use_ssl=True,
        connection_class=RequestsHttpConnection,
        http_auth=awsauth
    )


def handle_bucket_event(event, context):
    sns_message = json.loads(event["Records"][0]["Sns"]["Message"])
    bucket = sns_message["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(sns_message["Records"][0]["s3"]["object"]["key"])
    print(bucket, key)
    try:
        response = s3.head_object(Bucket=bucket, Key=key)
    except ClientError as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist, your bucket is in the same region as this function and necessary permissions have been granted.'.format(key, bucket))
        raise e

    metadata = {
        'key': key,
        'ContentLength': response['ContentLength'],
        'SizeMiB': response['ContentLength'] / 1024**2,
        'LastModified': response['LastModified'].isoformat(),
        'ContentType': response['ContentType'],
        'ETag': response['ETag'],
        'Dataset': key.split('/')[0]
    }
    print("METADATA: " + str(metadata))

    es_client = make_elasticsearch_client(os.environ['ELASTICSEARCH_ENDPOINT'])

    try:
        es_client.index(index=es_index, doc_type=bucket, body=json.dumps(metadata))
    except ElasticsearchException as e:
        print(e)
        print("Could not index in Elasticsearch")
        raise e


def create_metadata_visualizations(elasticsearch_endpoint):
    es_client = make_elasticsearch_client(elasticsearch_endpoint)
    es_client.index(index='.kibana', doc_type='config', id='5.1.1', body=json.dumps({'defaultIndex': 'metadata'}))
    data = {'title': 'metadata', 'timeFieldName': 'LastModified'}
    es_client.index(index='.kibana', doc_type='index-pattern', id='metadata', body=json.dumps(data))
    with open(TMP_KIBANA_JSON_PATH) as visualizations_file:
        visualizations = json.load(visualizations_file)
    for visualization in visualizations:
        es_client.index(
            index='.kibana',
            doc_type=visualization['_type'],
            id=visualization['_id'],
            body=json.dumps(visualization['_source'])
        )


def register_metadata_dashboard(event, context):
    if event['RequestType'] != 'Create':
        return send_cfnresponse(event, context, CFN_SUCCESS)
    quickstart_bucket = s3_resource.Bucket(event['ResourceProperties']['QSS3BucketName'])
    kibana_dashboards_key = os.path.join(
        event['ResourceProperties']['QSS3KeyPrefix'],
        'assets/kibana/kibana_metadata_visualizations.json'
    )
    elasticsearch_endpoint = event['ResourceProperties']['ElasticsearchEndpoint']
    try:
        quickstart_bucket.download_file(kibana_dashboards_key, TMP_KIBANA_JSON_PATH)
        create_metadata_visualizations(elasticsearch_endpoint)
        return send_cfnresponse(event, context, CFN_SUCCESS)
    except (ClientError, ElasticsearchException) as e:
        print(e)
        return send_cfnresponse(event, context, CFN_FAILED)


def send_cfnresponse(event, context, response_status):
    response_url = event['ResponseURL']
    print('CFN response url: {}'.format(response_url))

    response_body = {}
    response_body['Status'] = response_status
    response_body['Reason'] = 'See the details in CloudWatch Log Stream: ' + context.log_stream_name
    response_body['PhysicalResourceId'] = context.log_stream_name
    response_body['StackId'] = event['StackId']
    response_body['RequestId'] = event['RequestId']
    response_body['LogicalResourceId'] = event['LogicalResourceId']
    response_body['Data'] = {}

    json_response = json.dumps(response_body)
    print("Response body:\n" + json_response)

    headers = {
        'content-type': '',
        'content-length': str(len(json_response))
    }

    try:
        response = requests.put(response_url, data=json_response, headers=headers)
        print("Status code: " + response.reason)
    except Exception as e:
        print("send(..) failed executing requests.put(..): " + str(e))
