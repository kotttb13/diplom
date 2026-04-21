#!/data/data/com.termux/files/usr/bin/bash
set -e
pkg update -y
pkg install -y python python-numpy
pip install --upgrade pip
pip install onnxruntime tflite-runtime
