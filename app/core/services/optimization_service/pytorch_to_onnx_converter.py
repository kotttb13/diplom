from typing import Dict, Tuple

import torch


class PyTorchToONNXConverter:
    def convert(self, model, output_path: str, dummy_input: torch.Tensor,
                input_name: str = "input", output_name: str = "output") -> Dict:
        model.eval()
        torch.onnx.export(
            model,
            dummy_input,
            output_path,
            input_names=[input_name],
            output_names=[output_name],
            dynamic_axes={input_name: {0: "batch"}, output_name: {0: "batch"}},
            opset_version=13,
        )
        return {"success": True, "onnx_path": output_path}
