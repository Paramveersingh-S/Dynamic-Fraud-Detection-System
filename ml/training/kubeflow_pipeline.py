from kfp import dsl, compiler

@dsl.component
def validate_data(data_path: str) -> str:
    print(f"Validating data at {data_path}")
    return "Validation Passed"

@dsl.component
def compute_features(data_path: str) -> str:
    print(f"Computing features for {data_path}")
    return "features_path"

@dsl.component
def train_xgboost(features_path: str) -> str:
    print("Training XGBoost")
    return "xgb_model_path"

@dsl.component
def train_neural_network(features_path: str) -> str:
    print("Training NN")
    return "nn_model_path"

@dsl.component
def train_isolation_forest(features_path: str) -> str:
    print("Training IF")
    return "if_model_path"

@dsl.component
def evaluate_ensemble(xgb_path: str, nn_path: str, if_path: str) -> str:
    print("Evaluating Ensemble")
    return "metrics_path"

@dsl.component
def champion_challenger_comparison(challenger_metrics: str, champion_model_name: str) -> str:
    print("Comparing models")
    return "deploy" # dummy

@dsl.component
def deploy_to_production(model_version: str):
    print(f"Deploying version {model_version}")

@dsl.pipeline(name="fraud-model-retraining", description="Weekly fraud model retraining")
def fraud_retraining_pipeline(
    training_data_path: str,
    model_version: str,
    drift_threshold: float = 0.2
):
    # Step 1: Data validation
    validate_op = validate_data(data_path=training_data_path)
    
    # Step 2: Feature engineering
    feature_op = compute_features(data_path=training_data_path).after(validate_op)
    
    # Step 3: Train all models in parallel
    xgb_op = train_xgboost(features_path=feature_op.output)
    nn_op = train_neural_network(features_path=feature_op.output)
    if_op = train_isolation_forest(features_path=feature_op.output)
    
    # Step 4: Evaluate ensemble
    eval_op = evaluate_ensemble(
        xgb_path=xgb_op.output, 
        nn_path=nn_op.output, 
        if_path=if_op.output
    )
    
    # Step 5: Model comparison
    compare_op = champion_challenger_comparison(
        challenger_metrics=eval_op.output,
        champion_model_name="fraud-ensemble-champion"
    )
    
    # Step 6: Conditional deployment (kfp syntax for condition)
    with dsl.Condition(compare_op.output == "deploy"):
        deploy_op = deploy_to_production(model_version=model_version)

if __name__ == "__main__":
    compiler.Compiler().compile(fraud_retraining_pipeline, "fraud_retraining_pipeline.yaml")
    print("Pipeline compiled to fraud_retraining_pipeline.yaml")
