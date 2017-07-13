CREATE EXTERNAL TABLE orders (
    customer_id STRING,
    sku STRING,
    price DOUBLE,
    order_date TIMESTAMP
)
PARTITIONED BY (dt DATE)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://{{ managed_bucket_name }}/{{ orders_managed_dir }}';