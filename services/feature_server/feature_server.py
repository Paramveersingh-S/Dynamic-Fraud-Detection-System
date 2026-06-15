import grpc
from concurrent import futures
import redis
import time
import numpy as np

try:
    import feature_pb2
    import feature_pb2_grpc
except ImportError:
    print("Protobuf files not generated. Run: python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. feature.proto")

class FeatureServer(feature_pb2_grpc.FeatureServerServicer):
    def __init__(self, redis_host='localhost'):
        self.redis = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)
        
    def GetFeatures(self, request, context):
        start_time = time.time()
        
        # Redis pipelining to fetch all features in 1 round trip
        pipe = self.redis.pipeline()
        pipe.hgetall(f"user:{request.user_id}:velocity")
        pipe.hgetall(f"device:{request.device_id}:stats")
        pipe.hgetall(f"merchant:{request.merchant_id}:stats")
        
        results = pipe.execute()
        user_vel = results[0] or {}
        device_stats = results[1] or {}
        merchant_stats = results[2] or {}
        
        # Compute transaction features locally
        amount_log = np.log1p(request.amount)
        
        # Assemble feature map
        feature_map = {
            "amount": request.amount,
            "amount_log": amount_log,
        }
        
        feature_map.update({k: float(v) for k, v in user_vel.items()})
        feature_map.update({k: float(v) for k, v in device_stats.items()})
        feature_map.update({k: float(v) for k, v in merchant_stats.items()})
        
        # Ensure 95 features for Model input (placeholder for now)
        ordered_features = [feature_map.get(f"feat_{i}", 0.0) for i in range(95)]
        
        latency = (time.time() - start_time) * 1000
        
        return feature_pb2.FeatureResponse(
            transaction_id=request.transaction_id,
            features=ordered_features,
            feature_map=feature_map,
            feature_retrieval_latency_ms=latency
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    feature_pb2_grpc.add_FeatureServerServicer_to_server(FeatureServer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Feature Server started on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
