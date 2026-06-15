import os
import json

def export_xgboost_to_onnx(xgb_model, feature_count: int, save_path: str):
    from onnxmltools.convert import convert_xgboost
    from onnxmltools.utils import save_model
    from skl2onnx.common.data_types import FloatTensorType
    
    onnx_model = convert_xgboost(xgb_model, initial_types=[
        ("features", FloatTensorType([None, feature_count]))
    ])
    save_model(onnx_model, save_path)

TRITON_ENSEMBLE_CONFIG = """
name: "fraud_ensemble"
platform: "ensemble"
max_batch_size: 256
input [{ name: "INPUT__0" data_type: TYPE_FP32 dims: [95] }]
output [{ name: "fraud_score" data_type: TYPE_FP32 dims: [1] }]
ensemble_scheduling {
  step [
    { model_name: "xgboost_fraud" model_version: 1
      input_map { key: "features" value: "INPUT__0" }
      output_map { key: "probabilities" value: "xgb_score" } },
    { model_name: "fraud_nn" model_version: 1
      input_map { key: "input" value: "INPUT__0" }
      output_map { key: "output" value: "nn_score" } },
    { model_name: "fraud_combiner" model_version: 1
      input_map { key: "xgb" value: "xgb_score" key: "nn" value: "nn_score" }
      output_map { key: "fraud_score" value: "fraud_score" } }
  ]
}
"""

def generate_triton_config(base_path: str):
    os.makedirs(os.path.join(base_path, "fraud_ensemble"), exist_ok=True)
    with open(os.path.join(base_path, "fraud_ensemble", "config.pbtxt"), "w") as f:
        f.write(TRITON_ENSEMBLE_CONFIG.strip())

if __name__ == "__main__":
    generate_triton_config("model_repository")
    print("Triton ensemble config generated at model_repository/fraud_ensemble/config.pbtxt")
