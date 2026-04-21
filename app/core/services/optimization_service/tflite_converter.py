import os
from typing import Callable, Optional

import tensorflow as tf


class TFLiteConverter:
    def convert_from_saved_model(self, saved_model_dir: str, output_path: str, quantization: str = "none",
                                 representative_dataset: Optional[Callable] = None) -> str:
        converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_dir)
        self._apply_quantization(converter, quantization, representative_dataset)
        model = converter.convert()
        with open(output_path, "wb") as f:
            f.write(model)
        return output_path

    def convert_from_keras(self, keras_path: str, output_path: str, quantization: str = "none",
                           representative_dataset: Optional[Callable] = None) -> str:
        model = tf.keras.models.load_model(keras_path)
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        self._apply_quantization(converter, quantization, representative_dataset)
        tflite_model = converter.convert()
        with open(output_path, "wb") as f:
            f.write(tflite_model)
        return output_path

    def _apply_quantization(self, converter: tf.lite.TFLiteConverter, quantization: str,
                            representative_dataset: Optional[Callable]) -> None:
        if quantization == "dynamic":
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
        elif quantization == "int8":
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            if representative_dataset:
                converter.representative_dataset = representative_dataset
            converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
            converter.inference_input_type = tf.int8
            converter.inference_output_type = tf.int8
