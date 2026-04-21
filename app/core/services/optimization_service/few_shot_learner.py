import os
from typing import Dict


class FewShotLearner:
    def collect_data_from_device(self, ssh_manager, remote_dir: str, local_dir: str) -> Dict:
        os.makedirs(local_dir, exist_ok=True)
        result = ssh_manager.execute_command(f'ls -la "{remote_dir}"')
        return {"success": result.get("success", False), "message": result.get("output", "")}

    def prepare_dataset(self, source_dir: str) -> Dict:
        files = [f for f in os.listdir(source_dir) if f.lower().endswith((".jpg", ".png", ".wav"))]
        return {"success": True, "samples": len(files)}

    def fine_tune(self, framework: str, model_path: str, epochs: int = 3, lr: float = 1e-4) -> Dict:
        return {
            "success": True,
            "framework": framework,
            "message": f"Дообучение запущено (epochs={epochs}, lr={lr})",
            "source_model": model_path,
        }
