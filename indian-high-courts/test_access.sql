INSTALL httpfs; 
LOAD httpfs;
INSTALL parquet; 
LOAD parquet;

-- Test various possible file paths
.timer on

-- Try 2023 data
SELECT 'Testing 2023 data' as test_name;
SELECT COUNT(*) FROM read_parquet('s3://indian-high-court-judgments/metadata/parquet/year=2023/court=*/bench=*/metadata.parquet');

-- Try specific court/bench
SELECT 'Testing specific path' as test_name;
SELECT * FROM read_parquet('s3://indian-high-court-judgments/metadata/parquet/year=2023/court=01_01/bench=db/metadata.parquet') LIMIT 5;