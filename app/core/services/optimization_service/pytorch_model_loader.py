from typing import Dict, Tuple

import os
import torch


class PyTorchModelLoader:
    def load_model(self, model_path: str):
        # Сначала пробуем скриптовый файл.
        try:
            return torch.jit.load(model_path, map_location="cpu")
        except Exception:
            pass

        # Затем обычная сериализация.
        try:
            return torch.load(model_path, map_location="cpu", weights_only=False)
        except TypeError:
            # Старая версия без параметра.
            return torch.load(model_path, map_location="cpu")
        except Exception as e:
            err = str(e)
            if "invalid load key" in err:
                raise ValueError(
                    "Файл с расширением .pt/.pth не похож на артефакт PyTorch (torch.load не смог прочитать файл). "
                    "Часто это означает, что файл другого формата (например, ONNX), либо повреждён."
                ) from e
            # Часто класс недоступен в рантайме.
            if "Can't get attribute" in err:
                fallback_candidates = []
                root = model_path.rsplit(".", 1)[0]
                fallback_candidates.append(f"{root}_scripted.pt")
                fallback_candidates.append(model_path.replace("_full.pt", "_scripted.pt"))
                for candidate in fallback_candidates:
                    if candidate != model_path and os.path.exists(candidate):
                        return torch.jit.load(candidate, map_location="cpu")
                raise ValueError(
                    "Не удалось загрузить pickled .pt модель (класс не найден). "
                    "Используйте TorchScript-файл *_scripted.pt или ONNX."
                ) from e
            raise

    def extract_metadata(self, model) -> Dict:
        params = sum(p.numel() for p in model.parameters()) if hasattr(model, "parameters") else 0
        return {"parameters": params, "class_name": model.__class__.__name__}

    def prepare_dummy_input(self, input_shape: Tuple[int, ...]):
        return torch.randn(*input_shape)
