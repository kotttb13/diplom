import unittest
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from core.services.model_inspection_service import ModelInspectionService


class TestModelInspectionService(unittest.TestCase):
    def test_detect_format_by_extension(self):
        self.assertEqual(ModelInspectionService.detect_format("model.h5"), "h5")
        self.assertEqual(ModelInspectionService.detect_format("model.tflite"), "tflite")
        self.assertEqual(ModelInspectionService.detect_format("model.pt"), "pt")
        self.assertEqual(ModelInspectionService.detect_format("model.unknown"), "unknown")

    def test_detect_type_by_name_and_path(self):
        self.assertEqual(ModelInspectionService.detect_type("C:/models/bert_base.onnx", "bert_base"), "nlp")
        self.assertEqual(ModelInspectionService.detect_type("C:/models/speech_model.tflite", "speech_model"), "audio")
        self.assertEqual(ModelInspectionService.detect_type("C:/models/resnet50.onnx", "resnet50"), "cv")


if __name__ == "__main__":
    unittest.main()
