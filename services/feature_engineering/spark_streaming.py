import json
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TRANSACTION_SCHEMA = StructType([
    StructField("transaction_id", StringType(), True),
    StructField("user_id", StringType(), True),
    StructField("merchant_id", StringType(), True),
    StructField("merchant_category", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("currency", StringType(), True),
    StructField("timestamp", TimestampType(), True),
    StructField("card_present", BooleanType(), True),
    StructField("device_fingerprint", StringType(), True),
    StructField("ip_address", StringType(), True),
    StructField("latitude", DoubleType(), True),
    StructField("longitude", DoubleType(), True),
    StructField("billing_zip", StringType(), True),
    StructField("channel", StringType(), True),
    StructField("is_fraud", BooleanType(), True)
])

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Spark UDF implementation would go here
    return 0.0 # Placeholder for simplicity in this script

def build_streaming_pipeline(spark: SparkSession, kafka_servers="localhost:9092", redis_host="localhost"):
    logger.info("Building Spark Streaming Pipeline")
    
    # Read from Kafka
    raw_stream = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_servers) \
        .option("subscribe", "raw-transactions") \
        .option("startingOffsets", "latest") \
        .load()
    
    # Parse JSON
    transactions = raw_stream.select(
        from_json(col("value").cast("string"), TRANSACTION_SCHEMA).alias("txn")
    ).select("txn.*")
    
    # Add Watermark to handle late events
    transactions_with_watermark = transactions.withWatermark("timestamp", "30 seconds")
    
    # --- VELOCITY FEATURES (Sliding Windows) ---
    windows = {
        "1min": "1 minute",
        "5min": "5 minutes",
        "1hr": "1 hour",
        "24hr": "24 hours",
        "7d": "7 days"
    }
    
    velocity_streams = []
    
    for label, window_duration in windows.items():
        windowed_counts = transactions_with_watermark \
            .groupBy(
                window(col("timestamp"), window_duration),
                col("user_id")
            ) \
            .agg(
                count("transaction_id").alias(f"user_txn_count_{label}"),
                sum("amount").alias(f"user_amount_sum_{label}"),
                countDistinct("merchant_id").alias(f"user_distinct_merchants_{label}")
            )
            
        # In a real production setup, we would write these streaming aggregates to Redis using ForeachWriter
        velocity_streams.append(windowed_counts)

    # Note: Implementing mapGroupsWithState for geographic tracking requires Scala or complex PySpark setup.
    # We simulate the Redis writer here.
    
    class RedisWriter:
        def open(self, partition_id, epoch_id):
            import redis
            self.redis_client = redis.Redis(host=redis_host, port=6379, db=0)
            return True
            
        def process(self, row):
            user_id = row['user_id']
            # Example logic to save velocity features to Redis
            key = f"user:{user_id}:velocity"
            
            updates = {}
            for field in row.asDict():
                if field not in ['window', 'user_id'] and row[field] is not None:
                    updates[field] = row[field]
                    
            if updates:
                self.redis_client.hset(key, mapping=updates)
                self.redis_client.expire(key, 86400) # 24h TTL
                
        def close(self, error):
            self.redis_client.close()

    # Assuming we start the 1hr window stream to Redis
    query = velocity_streams[2].writeStream \
        .foreach(RedisWriter()) \
        .outputMode("update") \
        .start()
        
    return query

if __name__ == "__main__":
    spark = SparkSession.builder \
        .appName("FraudDetectionFeatureEngineering") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1") \
        .getOrCreate()
        
    spark.sparkContext.setLogLevel("WARN")
    
    query = build_streaming_pipeline(spark)
    query.awaitTermination()
