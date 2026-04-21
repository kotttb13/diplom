from typing import Any, Dict

import numpy as np
import tensorflow as tf


class TFLiteValidator:
    def validate(self, model_path: str, x_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        interpreter = tf.lite.Interpreter(model_path=model_path)
        interpreter.allocate_tensors()
        in_details = interpreter.get_input_details()[0]
        out_details = interpreter.get_output_details()[0]

        correct = 0
        losses = []
        for i in range(len(x_test)):
            x = x_test[i:i + 1].astype(np.float32)
            interpreter.set_tensor(in_details["index"], x)
            interpreter.invoke()
            logits = interpreter.get_tensor(out_details["index"])[0]
            pred = int(np.argmax(logits))
            true = int(y_test[i])
            if pred == true:
                correct += 1
            probs = np.clip(logits, 1e-7, 1 - 1e-7)
            one_hot = np.zeros_like(probs)
            one_hot[true] = 1.0
            losses.append(float(-np.sum(one_hot * np.log(probs))))

        return {"accuracy": correct / len(x_test), "loss": float(np.mean(losses))}
