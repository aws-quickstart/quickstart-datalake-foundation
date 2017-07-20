import argparse
import json
import os
import urllib.request

from root import PROJECT_DIR

KIBANA_TEMPLATE_URL = 'https://{es_endpoint}/.kibana/{type}/{id}/'
KIBANA_DASHBOARD_PATH = os.path.join(PROJECT_DIR, 'kibana/kibana_analysis_visualizations.json')
INDEX_TO_TIME_FIELD = {
    'revenue_by_state': 'timestamp',
    'top_sku': 'timestamp'
}


def send_put_request(url, data):
    request = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf8'),
        headers={'content-type': 'application/json'},
        method='PUT'
    )
    urllib.request.urlopen(request)


def send_kibana_put(elasticsearch_endpoint, type, id, data):
    kibana_url = KIBANA_TEMPLATE_URL.format(es_endpoint=elasticsearch_endpoint, type=type, id=id)
    send_put_request(kibana_url, data)


def register_kibana_indexes(elasticsearch_endpoint):
    for index_name, time_field_name in INDEX_TO_TIME_FIELD.items():
        data = {'title': index_name, 'timeFieldName': time_field_name}
        send_kibana_put(elasticsearch_endpoint, type='index-pattern', id=index_name, data=data)


def load_json(json_path):
    with open(json_path) as visualizations_file:
        return json.load(visualizations_file)


def import_visualizations(elasticsearch_endpoint):
    for visualization_json in load_json(KIBANA_DASHBOARD_PATH):
        send_kibana_put(
            elasticsearch_endpoint,
            type=visualization_json['_type'],
            id=visualization_json['_id'],
            data=visualization_json["_source"]
        )


def parse_args():
    parser = argparse.ArgumentParser(description='Quick start App')
    parser.add_argument('--elasticsearch-endpoint', required=True, help='Elasticsearch endpoint')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    register_kibana_indexes(args.elasticsearch_endpoint)
    import_visualizations(args.elasticsearch_endpoint)
