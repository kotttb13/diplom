-- Device extensions
ALTER TABLE device ADD COLUMN IF NOT EXISTS device_type VARCHAR(64) NOT NULL DEFAULT 'android';
ALTER TABLE device ADD COLUMN IF NOT EXISTS cpu_frequency INTEGER;
ALTER TABLE device ADD COLUMN IF NOT EXISTS gpu_memory INTEGER;

-- Seed device types
INSERT INTO device_type(name)
SELECT 'raspberry_pi'
WHERE NOT EXISTS (SELECT 1 FROM device_type WHERE name = 'raspberry_pi');

INSERT INTO device_type(name)
SELECT 'linux'
WHERE NOT EXISTS (SELECT 1 FROM device_type WHERE name = 'linux');

INSERT INTO model_type(name)
SELECT 'nlp'
WHERE NOT EXISTS (SELECT 1 FROM model_type WHERE name = 'nlp');

INSERT INTO model_type(name)
SELECT 'audio'
WHERE NOT EXISTS (SELECT 1 FROM model_type WHERE name = 'audio');

-- Ensure tflite format exists
INSERT INTO model_format(name)
SELECT 'tflite'
WHERE NOT EXISTS (SELECT 1 FROM model_format WHERE name = 'tflite');
