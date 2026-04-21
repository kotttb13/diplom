import os
import time
from typing import Any, Dict, Optional

import numpy as np
import onnx
import onnxruntime as ort
from onnxruntime.quantization import (
    CalibrationDataReader,
    QuantFormat,
    QuantType,
    quantize_dynamic,
    quantize_static,
)


class _NumpyCalibrationDataReader(CalibrationDataReader):
    def __init__(self, input_name: str, calibration_data: np.ndarray, max_samples: int = 128):
        data = calibration_data.astype(np.float32)
        if data.ndim == 0:
            data = np.expand_dims(data, axis=0)
        self._input_name = input_name
        self._samples = [{self._input_name: data[i : i + 1]} for i in range(min(len(data), max_samples))]
        self._iter = iter(self._samples)

    def get_next(self):
        return next(self._iter, None)


class ONNXQuantizer:
    def _prepare_for_quantization(self, model_path: str) -> str:
        """
        Some ONNX models miss type/shape info required by ORT quantizers.
        Run ONNX shape inference and write a temporary model for quantization.
        """
        try:
            model = onnx.load(model_path)
            model = onnx.shape_inference.infer_shapes(model)
            tmp_path = f"{os.path.splitext(model_path)[0]}_shape_inferred.onnx"
            onnx.save(model, tmp_path)
            return tmp_path
        except Exception:
            return model_path

    def dynamic_quantization(self, model_path: str, output_path: Optional[str] = None) -> str:
        output_path = output_path or self._default_output(model_path)
        prepared = self._prepare_for_quantization(model_path)
        # Dynamic quantization is most reliable for MatMul/Gemm-heavy models (e.g., transformers).
        # Quantizing Conv dynamically may produce ConvInteger which is often unsupported by CPU EP.
        try:
            quantize_dynamic(
                prepared,
                output_path,
                weight_type=QuantType.QInt8,
                op_types_to_quantize=["MatMul", "Gemm"],
                extra_options={"DefaultTensorType": onnx.TensorProto.FLOAT},
            )
        except TypeError:
            quantize_dynamic(
                prepared,
                output_path,
                weight_type=QuantType.QInt8,
                op_types_to_quantize=["MatMul", "Gemm"],
            )
        return output_path

    def static_quantization(self, model_path: str, calibration_data: Any, output_path: Optional[str] = None) -> str:
        output_path = output_path or self._default_output(model_path)
        if calibration_data is None:
            return self.dynamic_quantization(model_path, output_path)

        x_calib = calibration_data
        if isinstance(calibration_data, tuple):
            x_calib = calibration_data[0]
        if x_calib is None:
            return self.dynamic_quantization(model_path, output_path)

        prepared = self._prepare_for_quantization(model_path)
        sess = ort.InferenceSession(prepared, providers=["CPUExecutionProvider"])
        input_name = sess.get_inputs()[0].name
        reader = _NumpyCalibrationDataReader(input_name, np.asarray(x_calib))

        try:
            quantize_static(
                prepared,
                output_path,
                reader,
                op_types_to_quantize=["Conv", "MatMul", "Gemm"],
                quant_format=QuantFormat.QDQ,
                activation_type=QuantType.QUInt8,
                weight_type=QuantType.QInt8,
                per_channel=True,
                extra_options={"DefaultTensorType": onnx.TensorProto.FLOAT},
            )
        except TypeError:
            quantize_static(
                prepared,
                output_path,
                reader,
                op_types_to_quantize=["Conv", "MatMul", "Gemm"],
                quant_format=QuantFormat.QDQ,
                activation_type=QuantType.QUInt8,
                weight_type=QuantType.QInt8,
                per_channel=True,
            )
        return output_path

    def compare_metrics(self, original_path: str, quantized_path: str, x_test: np.ndarray = None) -> Dict:
        if x_test is None:
            x_test = np.zeros((1, 3, 224, 224), dtype=np.float32)
        return {
            "size_before_bytes": os.path.getsize(original_path),
            "size_after_bytes": os.path.getsize(quantized_path),
            "inference_before_ms": self._bench_onnx(original_path, x_test),
            "inference_after_ms": self._bench_onnx(quantized_path, x_test),
        }

    def _bench_onnx(self, model_path: str, x_test: np.ndarray, runs: int = 100) -> float:
        try:
            sess = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
            name = sess.get_inputs()[0].name
            sample = x_test[:1].astype(np.float32)
            for _ in range(10):
                sess.run(None, {name: sample})
            start = time.perf_counter()
            for _ in range(runs):
                sess.run(None, {name: sample})
            return (time.perf_counter() - start) * 1000 / runs
        except Exception:
            # Metrics should not break the entire optimization pipeline.
            return -1.0

    def _default_output(self, model_path: str) -> str:
        root, ext = os.path.splitext(model_path)
        return f"{root}_quantized{ext}"
