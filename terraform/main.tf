provider "aws" {
  region = "us-east-1"
}

# MSK Cluster for Kafka
resource "aws_msk_cluster" "kafka" {
  cluster_name           = "fraud-kafka-cluster"
  kafka_version          = "3.2.0"
  number_of_broker_nodes = 3
  broker_node_group_info {
    instance_type   = "kafka.m5.large"
    client_subnets  = ["subnet-xyz"]
    security_groups = ["sg-xyz"]
  }
}

# ElastiCache for Redis (Online Feature Store)
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "fraud-feature-store"
  engine               = "redis"
  node_type            = "cache.m4.large"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
}

# EKS Cluster for Kubeflow and Model Serving
resource "aws_eks_cluster" "k8s" {
  name     = "fraud-detection-eks"
  role_arn = "arn:aws:iam::123456789012:role/eks-role"
  vpc_config {
    subnet_ids = ["subnet-xyz"]
  }
}

# RDS for PostgreSQL (Supabase / Offline Storage)
resource "aws_db_instance" "postgres" {
  allocated_storage    = 100
  engine               = "postgres"
  engine_version       = "15.3"
  instance_class       = "db.t3.large"
  identifier           = "fraud-db"
  username             = "postgres"
  password             = "supersecret"
  skip_final_snapshot  = true
}
