import os


class ModelInspectionService:
    SUPPORTED_EXTENSIONS = {"h5", "keras", "onnx", "pb", "tflite", "pt", "pth"}

    @staticmethod
    def detect_format(file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower().lstrip(".")
        return ext if ext in ModelInspectionService.SUPPORTED_EXTENSIONS else "unknown"

    @staticmethod
    def detect_type(file_path: str, model_name: str = "") -> str:
        probe = f"{file_path} {model_name}".lower()
        if any(k in probe for k in ["bert", "gpt", "llm", "nlp", "text", "token"]):
            return "nlp"
        if any(k in probe for k in ["audio", "wav", "speech", "asr", "voice"]):
            return "audio"
        return "cv"
