#!/bin/bash
# PepperAI - Model Download Script
# Run this script to download required model files

echo "📥 Downloading PepperAI models..."

# Create models directory
mkdir -p models_extra

# Download YOLOv8 models
echo "📥 Downloading YOLOv8 models..."
wget -O models_extra/yolov8n-seg.pt https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n-seg.pt
wget -O models_extra/yolov8n.pt https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt

# Download specialized bell pepper model (if available)
echo "📥 Downloading specialized bell pepper model..."
# Note: Replace with actual download URL for your trained model
# wget -O models/bell_pepper_model.pt <your_model_url>

echo "✅ Models downloaded successfully!"
echo "🚀 You can now run the application with: python app.py"
