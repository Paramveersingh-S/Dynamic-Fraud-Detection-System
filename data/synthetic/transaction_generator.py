import os
import uuid
import random
import time
import json
import argparse
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from kafka import KafkaProducer
from concurrent.futures import ProcessPoolExecutor

# Merchant categories
MCC_CODES = ["grocery", "gas", "travel", "restaurant", "retail", "pharmacy", "entertainment", "adult", "gambling", "electronics"]
CHANNELS = ["mobile", "web", "pos", "atm"]
CURRENCIES = ["USD"] * 90 + ["EUR", "GBP", "CAD", "MXN"]  # 90% USD

def get_random_ip():
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"

def get_random_location():
    # Roughly US bounding box
    lat = random.uniform(25.0, 49.0)
    lon = random.uniform(-125.0, -66.0)
    return lat, lon

class UserProfile:
    def __init__(self, user_id):
        self.user_id = user_id
        self.home_lat, self.home_lon = get_random_location()
        self.billing_zip = f"{random.randint(10000, 99999)}"
        self.primary_device = str(uuid.uuid4())
        self.primary_ip = get_random_ip()
        self.avg_amount = max(1.0, random.gauss(50, 20))
        self.preferred_categories = random.sample(MCC_CODES, 3)

class TransactionSimulator:
    def __init__(self, num_users=10000, num_merchants=5000):
        print(f"Initializing {num_users} users and {num_merchants} merchants...")
        self.users = {f"user_{i}": UserProfile(f"user_{i}") for i in range(num_users)}
        self.merchants = [f"merch_{i}" for i in range(num_merchants)]
        self.merchant_cats = {m: random.choice(MCC_CODES) for m in self.merchants}
        
    def generate_normal_transaction(self, user, timestamp):
        merchant_id = random.choice(self.merchants)
        merchant_category = self.merchant_cats[merchant_id]
        if random.random() < 0.7:
            merchant_category = random.choice(user.preferred_categories)
            
        amount = max(0.5, random.gauss(user.avg_amount, user.avg_amount * 0.3))
        card_present = random.random() < 0.6
        channel = random.choice(["pos", "atm"]) if card_present else random.choice(["web", "mobile"])
        
        # 95% of time, normal location
        if random.random() < 0.95:
            lat, lon = user.home_lat + random.uniform(-0.1, 0.1), user.home_lon + random.uniform(-0.1, 0.1)
        else:
            lat, lon = get_random_location()
            
        device = user.primary_device if random.random() < 0.9 else str(uuid.uuid4())
        ip = user.primary_ip if random.random() < 0.9 else get_random_ip()
        
        return {
            "transaction_id": str(uuid.uuid4()),
            "user_id": user.user_id,
            "merchant_id": merchant_id,
            "merchant_category": merchant_category,
            "amount": round(amount, 2),
            "currency": random.choice(CURRENCIES),
            "timestamp": timestamp.isoformat(),
            "card_present": card_present,
            "device_fingerprint": device,
            "ip_address": ip,
            "latitude": lat,
            "longitude": lon,
            "billing_zip": user.billing_zip,
            "channel": channel,
            "is_fraud": False
        }

    def inject_fraud_patterns(self, user, timestamp, pattern_type):
        txns = []
        if pattern_type == 1:
            # 1. Card testing: rapid small transactions (<$1) in quick succession
            for i in range(5):
                txn = self.generate_normal_transaction(user, timestamp + timedelta(seconds=i*10))
                txn["amount"] = round(random.uniform(0.1, 0.99), 2)
                txn["is_fraud"] = True
                txns.append(txn)
        elif pattern_type == 2:
            # 2. Velocity attack: many transactions in short time window
            for i in range(10):
                txn = self.generate_normal_transaction(user, timestamp + timedelta(seconds=i*30))
                txn["is_fraud"] = True
                txns.append(txn)
        elif pattern_type == 3:
            # 3. Geographic impossibility: two txns 1000 miles apart in 10 minutes
            txn1 = self.generate_normal_transaction(user, timestamp)
            txn1["latitude"], txn1["longitude"] = 40.7128, -74.0060 # NY
            txn1["is_fraud"] = True
            
            txn2 = self.generate_normal_transaction(user, timestamp + timedelta(minutes=10))
            txn2["latitude"], txn2["longitude"] = 34.0522, -118.2437 # LA
            txn2["is_fraud"] = True
            txns.extend([txn1, txn2])
        elif pattern_type == 4:
            # 4. Merchant category anomaly: first time at adult/gambling merchant
            txn = self.generate_normal_transaction(user, timestamp)
            txn["merchant_category"] = random.choice(["adult", "gambling"])
            txn["is_fraud"] = True
            txns.append(txn)
        elif pattern_type == 5:
            # 5. Amount anomaly: transaction 10x normal spend
            txn = self.generate_normal_transaction(user, timestamp)
            txn["amount"] = round(user.avg_amount * random.uniform(10, 20), 2)
            txn["is_fraud"] = True
            txns.append(txn)
        elif pattern_type == 6:
            # 6. Late night anomaly
            txn = self.generate_normal_transaction(user, timestamp.replace(hour=random.randint(2, 4)))
            txn["is_fraud"] = True
            txns.append(txn)
        elif pattern_type == 7:
            # 7. Account takeover: new device + new IP + high amount
            txn = self.generate_normal_transaction(user, timestamp)
            txn["device_fingerprint"] = str(uuid.uuid4())
            txn["ip_address"] = get_random_ip()
            txn["amount"] = round(user.avg_amount * 5, 2)
            txn["is_fraud"] = True
            txns.append(txn)
        elif pattern_type == 8:
            # 8. CNP fraud: card-not-present with mismatched billing zip
            txn = self.generate_normal_transaction(user, timestamp)
            txn["card_present"] = False
            txn["channel"] = "web"
            txn["billing_zip"] = "00000" # Mismatched
            txn["is_fraud"] = True
            txns.append(txn)
            
        return txns

def generate_batch_data(total_records, start_date, output_file):
    simulator = TransactionSimulator(num_users=total_records // 100, num_merchants=total_records // 500)
    current_time = start_date
    records = []
    
    print(f"Generating {total_records} records...")
    while len(records) < total_records:
        user_id = random.choice(list(simulator.users.keys()))
        user = simulator.users[user_id]
        
        # 0.1% fraud rate
        if random.random() < 0.001:
            pattern = random.randint(1, 8)
            fraud_txns = simulator.inject_fraud_patterns(user, current_time, pattern)
            records.extend(fraud_txns)
            current_time += timedelta(minutes=random.randint(1, 10))
        else:
            txn = simulator.generate_normal_transaction(user, current_time)
            records.append(txn)
            current_time += timedelta(seconds=random.randint(1, 60))
            
        if len(records) % 100000 == 0:
            print(f"Generated {len(records)} records...")
            
    df = pd.DataFrame(records[:total_records])
    df.to_parquet(output_file, index=False)
    print(f"Saved to {output_file}")

def stream_to_kafka(brokers="localhost:9092", topic="raw-transactions"):
    producer = KafkaProducer(
        bootstrap_servers=brokers,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    simulator = TransactionSimulator(num_users=10000, num_merchants=5000)
    print(f"Streaming transactions to Kafka topic: {topic}")
    
    try:
        while True:
            current_time = datetime.now()
            # Simulate TPS based on hour
            hour = current_time.hour
            if 11 <= hour <= 14 or 18 <= hour <= 21:
                tps = random.randint(800, 1000) # Peak
            elif 2 <= hour <= 5:
                tps = random.randint(10, 50) # Low
            else:
                tps = random.randint(80, 120) # Baseline
                
            sleep_time = 1.0 / tps
            
            user_id = random.choice(list(simulator.users.keys()))
            user = simulator.users[user_id]
            
            if random.random() < 0.001:
                pattern = random.randint(1, 8)
                txns = simulator.inject_fraud_patterns(user, current_time, pattern)
                for txn in txns:
                    producer.send(topic, txn)
            else:
                txn = simulator.generate_normal_transaction(user, current_time)
                producer.send(topic, txn)
                
            time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        print("Stopping streaming...")
    finally:
        producer.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["batch", "stream"], required=True)
    parser.add_argument("--records", type=int, default=1000000)
    parser.add_argument("--output", type=str, default="data/synthetic/transactions.parquet")
    parser.add_argument("--brokers", type=str, default="localhost:9092")
    
    args = parser.parse_args()
    
    if args.mode == "batch":
        generate_batch_data(args.records, datetime.now() - timedelta(days=30), args.output)
    else:
        stream_to_kafka(brokers=args.brokers)
