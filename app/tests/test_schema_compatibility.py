import unittest
import pathlib
import sys

from sqlalchemy import create_engine, inspect, text

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from core.database.initialization_db import ensure_schema_compatibility


class TestSchemaCompatibility(unittest.TestCase):
    def test_ensure_schema_compatibility_adds_device_columns(self):
        engine = create_engine("sqlite:///:memory:")
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE device (
                        id INTEGER PRIMARY KEY,
                        type_id INTEGER,
                        ip_address VARCHAR(128),
                        architecture VARCHAR(128),
                        memory_gb FLOAT,
                        ram_gb FLOAT,
                        cpu_core INTEGER,
                        last_seen DATETIME
                    )
                    """
                )
            )

        ensure_schema_compatibility(engine)
        cols = {c["name"] for c in inspect(engine).get_columns("device")}
        self.assertIn("device_type", cols)
        self.assertIn("cpu_frequency", cols)
        self.assertIn("gpu_memory", cols)


if __name__ == "__main__":
    unittest.main()
