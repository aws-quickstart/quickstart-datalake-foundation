DROP TABLE IF EXISTS product_category_distribution;
CREATE TABLE product_category_distribution AS
SELECT product_category, COUNT(*) AS orders_count
FROM orders JOIN {{ external_schema_name }}.{{ products_parquet_table_name }} ON orders.sku = {{ products_parquet_table_name }}.sku
WHERE {{ products_parquet_table_name }}.dt = '2016-12-31'
GROUP BY product_category;