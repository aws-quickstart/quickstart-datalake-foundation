import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import lit

## @params: [JOB_NAME, datalake_submissions_database_name, datalake_curated_datasets_database_name, datalake_curated_datasets_bucket_name]
args = getResolvedOptions(
    sys.argv,
    [
        'JOB_NAME',
        'datalake_submissions_database_name',
        'datalake_curated_datasets_database_name',
        'datalake_curated_datasets_bucket_name'
    ]
)

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

## @type: DataSource
## @args: [database = "datalake-curated-datasets", table_name = "demographics_2017_05_20_json"]
## @return: datasource_demographics_json
## @inputs: []
datasource_demographics_json = glueContext.create_dynamic_frame.from_catalog(
    database=args["datalake_curated_datasets_database_name"],
    table_name="demographics_20170520_json"
)

## @type: Json2Parquet
## @args: [mapping = []]
## @return: datasource_demographics_parquet
## @inputs: [frame = datasource_demographics_json]

## @type: DataSink
## @args: [connection_type = "s3", connection_options = {"path": "s3://datalake-curated-datasets-123456789123-us-west-2/demographics_20170520_parquet/dataset=demographics/v=2017-05-20/p=parquet"}, format = "parquet"]
## @return: datasink_demographics_parquet
## @inputs: [frame = datasource_demographics_parquet]
df = datasource_demographics_json.toDF()
df = df.drop('dataset', 'v', 'p')
df.write.partitionBy('dt').parquet('s3://{}/demographics_20171206_parquet/dataset=demographics/v=2017-12-06/p=parquet'.format(args['datalake_curated_datasets_bucket_name']), mode='overwrite')

## @type: DataSource
## @args: [database = "datalake-curated-datasets", table_name = "products_2017_06_01_json"]
## @return: datasource_products_json
## @inputs: []
datasource_products_json = glueContext.create_dynamic_frame.from_catalog(
    database=args["datalake_curated_datasets_database_name"],
    table_name="products_20170601_json"
)

## @type: Json2Parquet
## @args: [mapping = []]
## @return: datasource_products_parquet
## @inputs: [frame = datasource_products_json]

## @type: DataSink
## @args: [connection_type = "s3", connection_options = {"path": "s3://datalake-curated-datasets-123456789123-us-west-2/products_2017-06-01_parquet/dataset=products/v=2017-06-01/p=parquet"}, format = "parquet"]
## @return: datasink_products_parquet
## @inputs: [frame = datasource_products_parquet]
df = datasource_products_json.toDF()
df = df.drop('dataset', 'v', 'p')
df.write.partitionBy('dt').parquet('s3://{}/products_20171206_parquet/dataset=products/v=2017-12-06/p=parquet'.format(args['datalake_curated_datasets_bucket_name']), mode='overwrite')

job.commit()