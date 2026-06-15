-- Snowflake schema for analytical workloads

CREATE SCHEMA IF NOT EXISTS fraud_analytics;

CREATE TABLE fraud_analytics.transactions (
    transaction_id VARCHAR,
    user_id VARCHAR,
    merchant_id VARCHAR,
    amount FLOAT,
    timestamp TIMESTAMP_TZ,
    is_fraud BOOLEAN,
    fraud_score FLOAT,
    decision VARCHAR
) CLUSTER BY (TO_DATE(timestamp));

CREATE TABLE fraud_analytics.user_features_hourly (
    user_id VARCHAR,
    feature_hour TIMESTAMP_TZ,
    txn_count_24hr INTEGER,
    amount_sum_24hr FLOAT
) CLUSTER BY (feature_hour);

-- Snowflake Task to refresh user features hourly
CREATE TASK refresh_user_features
    WAREHOUSE = COMPUTE_WH
    SCHEDULE = '60 MINUTE'
AS
    MERGE INTO fraud_analytics.user_features_hourly AS target
    USING (
        SELECT 
            user_id, 
            DATE_TRUNC('HOUR', timestamp) as feature_hour, 
            COUNT(*) as txn_count_24hr, 
            SUM(amount) as amount_sum_24hr 
        FROM fraud_analytics.transactions 
        WHERE timestamp >= DATEADD(hour, -24, CURRENT_TIMESTAMP())
        GROUP BY 1, 2
    ) AS source
    ON target.user_id = source.user_id AND target.feature_hour = source.feature_hour
    WHEN MATCHED THEN 
        UPDATE SET target.txn_count_24hr = source.txn_count_24hr, 
                   target.amount_sum_24hr = source.amount_sum_24hr
    WHEN NOT MATCHED THEN 
        INSERT (user_id, feature_hour, txn_count_24hr, amount_sum_24hr) 
        VALUES (source.user_id, source.feature_hour, source.txn_count_24hr, source.amount_sum_24hr);
