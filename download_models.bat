@echo off
REM PepperAI - Model Download Script (Windows)
REM Run this script to download required model files

echo 📥 Downloading PepperAI models...

REM Create models directory
if not exist models_extra mkdir models_extra

REM Download YOLOv8 models
echo 📥 Downloading YOLOv8 models...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n-seg.pt' -OutFile 'models_extra/yolov8n-seg.pt'"
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt' -OutFile 'models_extra/yolov8n.pt'"

REM Download specialized bell pepper model (if available)
echo 📥 Downloading specialized bell pepper model...
REM Note: Replace with actual download URL for your trained model
REM powershell -Command "Invoke-WebRequest -Uri '<your_model_url>' -OutFile 'models/bell_pepper_model.pt'"

echo ✅ Models downloaded successfully!
echo 🚀 You can now run the application with: python app.py
pause
