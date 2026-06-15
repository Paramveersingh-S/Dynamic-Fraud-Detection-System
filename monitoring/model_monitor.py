from prometheus_client import start_http_server, Summary, Counter, Histogram, Gauge
import random
import time

# Metrics
DECISION_LATENCY = Histogram('fraud_decision_latency_ms', 'Time spent processing decision')
FRAUD_SCORE = Histogram('fraud_score_distribution', 'Distribution of fraud scores')
DECISION_COUNTER = Counter('fraud_decisions_total', 'Total decisions made', ['decision_type'])
FEATURE_STORE_HIT_RATE = Gauge('feature_store_hit_rate', 'Redis cache hit rate')
KAFKA_LAG = Gauge('kafka_consumer_lag', 'Messages behind in Kafka topic')

def simulate_metrics():
    while True:
        # Simulate latency (target p99 < 50ms)
        latency = random.gauss(25, 5) if random.random() > 0.05 else random.gauss(60, 10)
        DECISION_LATENCY.observe(latency)
        
        # Simulate fraud score
        score = random.beta(0.5, 5) # heavily skewed to 0
        FRAUD_SCORE.observe(score)
        
        # Simulate decisions
        if score > 0.85:
            DECISION_COUNTER.labels(decision_type='DECLINE').inc()
        elif score > 0.5:
            DECISION_COUNTER.labels(decision_type='REVIEW').inc()
        else:
            DECISION_COUNTER.labels(decision_type='APPROVE').inc()
            
        # Infrastructure metrics
        FEATURE_STORE_HIT_RATE.set(random.uniform(0.95, 0.99))
        KAFKA_LAG.set(random.randint(0, 50))
        
        time.sleep(0.1)

if __name__ == '__main__':
    start_http_server(8000)
    print("Prometheus metrics server started on port 8000")
    simulate_metrics()
