import boto3
import logging
from time import sleep
from multiprocessing import Process


from botocore.errorfactory import ClientError


def get_crawler_state(glue_client, crawler_name):
    response = glue_client.get_crawler(
        Name=crawler_name
    )
    return response['Crawler']['State']


def crawl_after_job(glue_client, job_name, job_run_id, crawler_name):
    log = logging.getLogger('job_poll')

    while True:
        log.info('Waiting')
        sleep(30)
        response = glue_client.get_job_run(
            JobName=job_name,
            RunId=job_run_id
        )
        job_run_state = response['JobRun']['JobRunState']
        log.info('Job run state: {}'.format(job_run_state))
        if job_run_state == 'SUCCEEDED':
            log.info('SUCCEEDED so break')
            break

    try:
        log.info('Trying to run crawler')
        glue_client.start_crawler(
            Name=crawler_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'CrawlerRunningException':
            log.info('Crawler already running. Waiting additional 30 seconds')
            sleep(30)
            crawl_after_job(glue_client, job_name, job_run_id, crawler_name)
        else:
            log.exception(e)
    log.info('Finished')


def run_aws_glue_crawler(config):
    log = logging.getLogger(__name__)

    client = boto3.client('glue', region_name=config['region_name'])
    curated_datasets_crawler_name = config['curated_datasets_crawler_name']
    job_name = config['curated_datasets_job_name']

    try:
        client.start_crawler(
            Name=curated_datasets_crawler_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'CrawlerRunningException':
            log.info('Crawler already running')
        else:
            log.exception(e)
            raise e

    while True:
        sleep(10)
        curated_state = get_crawler_state(client, curated_datasets_crawler_name)
        log.info("Curated crawler state: {}".format(curated_state))
        if curated_state != 'RUNNING':
            break

    try:
        response = client.start_job_run(
            JobName=job_name
        )
        job_run_id = response['JobRunId']
        p = Process(target=crawl_after_job, args=(client, job_name, job_run_id, curated_datasets_crawler_name))
        p.start()
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConcurrentRunsExceededException':
            log.info('Job already running')
        else:
            log.exception(e)
            raise e
