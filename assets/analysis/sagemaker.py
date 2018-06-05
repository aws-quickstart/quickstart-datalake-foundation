import json

import boto3


def inference_sales(config, days: str) -> float:
    client = boto3.client('sagemaker-runtime', region_name=config['region_name'])
    response = client.invoke_endpoint(
        EndpointName=config['sm_model_endpoint_name'],
        Body=bytes(days, 'utf-8'),
        ContentType='text/csv',
        Accept='application/json'
    )

    response_bytes = response['Body'].read()
    response_json = json.loads(response_bytes.decode('utf-8'))
    result_json = response_json['predictions'][0]
    return result_json
