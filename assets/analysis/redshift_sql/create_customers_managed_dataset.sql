DROP TABLE IF EXISTS customers;
CREATE TABLE customers (
    customer_id VARCHAR(100) encode zstd,
    first_name VARCHAR(50) encode zstd,
    last_name VARCHAR(50) encode zstd,
    region VARCHAR(20) encode zstd,
    state VARCHAR(20) encode zstd,
    geoid VARCHAR(20) encode zstd,
    marital_status VARCHAR(20) encode zstd,
    education_level VARCHAR(20) encode zstd
)
distkey(customer_id)
sortkey(customer_id);

COPY customers
FROM 's3://{{ managed_bucket_name }}/{{ customers_managed_path }}'
IAM_ROLE '{{ redshift_role_arn }}'
DELIMITER ','
REGION '{{ region_name }}';