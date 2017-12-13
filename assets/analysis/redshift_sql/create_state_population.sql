DROP TABLE IF EXISTS state_population;
CREATE TABLE state_population AS (
  SELECT state, SUM(population) AS population FROM {{ external_schema_name }}.{{ demographics_parquet_table_name }} GROUP BY state
);