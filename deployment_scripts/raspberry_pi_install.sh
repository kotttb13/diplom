#!/usr/bin/env bash
set -e
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip
python3 -m pip install --upgrade pip
python3 -m pip install numpy onnxruntime tflite-runtime
