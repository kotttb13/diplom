import os
import time
from typing import Dict

import numpy as np
import psutil
import tensorflow as tf


class Benchmarker:
    def measure_inference_time(self, interpreter: tf.lite.Interpreter, x_sample: np.ndarray,
                               warmup: int = 10, runs: int = 100) -> float:
        input_details = interpreter.get_input_details()[0]
        for _ in range(warmup):
            interpreter.set_tensor(input_details["index"], x_sample.astype(np.float32))
            interpreter.invoke()
        start = time.perf_counter()
        for _ in range(runs):
            interpreter.set_tensor(input_details["index"], x_sample.astype(np.float32))
            interpreter.invoke()
        return ((time.perf_counter() - start) * 1000) / runs

    def measure_memory_usage(self) -> float:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)

    def build_report(self, original_size: float, optimized_size: float, before_ms: float, after_ms: float,
                     acc_before: float = None, acc_after: float = None) -> Dict:
        return {
            "size_before_mb": original_size,
            "size_after_mb": optimized_size,
            "inference_before_ms": before_ms,
            "inference_after_ms": after_ms,
            "accuracy_before": acc_before,
            "accuracy_after": acc_after,
        }
