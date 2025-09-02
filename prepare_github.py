#!/usr/bin/env python3
"""
PepperAI - GitHub Preparation Script
Cleans up large files and prepares the project for GitHub upload
"""

import os
import shutil
import glob
from pathlib import Path

def clean_large_files():
    """Remove large files that shouldn't be on GitHub"""
    
    print("🧹 Cleaning up large files for GitHub...")
    
    # Files to remove (large model files, datasets, etc.)
    files_to_remove = [
        "yolov8n-seg.pt",  # Large YOLO model
        "*.pt",  # All PyTorch models
        "*.pth",  # All PyTorch models
        "*.onnx",  # ONNX models
        "*.tflite",  # TensorFlow Lite models
    ]
    
    # Directories to clean
    dirs_to_clean = [
        "training/dataset/images",
        "training/dataset/labels", 
        "uploads",
        "results",
        "__pycache__",
        "*.pyc",
    ]
    
    # Remove large files
    for pattern in files_to_remove:
        for file_path in glob.glob(pattern, recursive=True):
            if os.path.isfile(file_path):
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                print(f"🗑️  Removing {file_path} ({size_mb:.1f} MB)")
                os.remove(file_path)
    
    # Clean directories
    for dir_pattern in dirs_to_clean:
        if "*" in dir_pattern:
            # Handle glob patterns
            for dir_path in glob.glob(dir_pattern, recursive=True):
                if os.path.isdir(dir_path):
                    print(f"🗑️  Cleaning directory: {dir_path}")
                    shutil.rmtree(dir_path, ignore_errors=True)
        else:
            # Handle specific directories
            if os.path.exists(dir_pattern):
                print(f"🗑️  Cleaning directory: {dir_pattern}")
                shutil.rmtree(dir_pattern, ignore_errors=True)
    
    # Create .gitkeep files for empty directories
    for dir_name in ["uploads", "results"]:
        Path(dir_name).mkdir(exist_ok=True)
        gitkeep_file = Path(dir_name) / ".gitkeep"
        gitkeep_file.touch(exist_ok=True)
        print(f"📁 Created {gitkeep_file}")

def create_model_download_script():
    """Create a script to download models"""
    
    script_content = """#!/bin/bash
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
"""
    
    with open("download_models.sh", "w", encoding='utf-8') as f:
        f.write(script_content)
    
    # Make it executable on Unix systems
    os.chmod("download_models.sh", 0o755)
    print("📄 Created download_models.sh script")

def create_model_download_bat():
    """Create a Windows batch script to download models"""
    
    script_content = """@echo off
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
"""
    
    with open("download_models.bat", "w", encoding='utf-8') as f:
        f.write(script_content)
    
    print("📄 Created download_models.bat script")

def update_readme_with_download_instructions():
    """Update README with model download instructions"""
    
    readme_content = """# PepperAI - Bell Pepper Detection & Quality Assessment System

## 🚀 AI-Powered Bell Pepper Quality Assessment

PepperAI is a comprehensive machine learning system that automates the quality grading of bell peppers using advanced computer vision, deep learning, and AI analysis.

### ✨ Features

- **🔍 Multi-Model Detection**: YOLOv8 + Specialized Bell Pepper Model
- **🎯 Advanced Quality Analysis**: Color uniformity, size consistency, surface quality, ripeness level
- **🦠 Disease Detection**: EfficientNet-B4 based disease classification
- **🧠 AI-Powered Insights**: Ripeness prediction, shelf life estimation, nutritional analysis
- **📱 Progressive Web App**: Mobile-optimized with PWA capabilities
- **🐳 Docker Ready**: Containerized deployment
- **📊 Real-time Analysis**: Instant results with confidence scores

### 🛠️ Technology Stack

- **Backend**: Python Flask, OpenCV, scikit-image, PyTorch
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **AI/ML**: YOLOv8, EfficientNet-B4, ANFIS-inspired quality assessment
- **Deployment**: Docker, Docker Compose

### 🚀 Quick Start

#### Prerequisites

Before running PepperAI, you need to download the required model files:

**Windows:**
```bash
download_models.bat
```

**Linux/Mac:**
```bash
chmod +x download_models.sh
./download_models.sh
```

#### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/pepperai.git
cd pepperai

# Download models (required)
./download_models.sh  # Linux/Mac
# OR
download_models.bat   # Windows

# Build and run with Docker Compose
docker-compose up --build

# Access the application
open http://localhost:5000
```

#### Manual Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/pepperai.git
cd pepperai

# Download models (required)
./download_models.sh  # Linux/Mac
# OR
download_models.bat   # Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py

# Access the application
open http://localhost:5000
```

### 📁 Project Structure

```
pepperai/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker configuration
├── docker-compose.yml              # Docker Compose setup
├── download_models.sh              # Model download script (Linux/Mac)
├── download_models.bat             # Model download script (Windows)
├── python_modules/                 # Analysis modules
│   ├── pepper_quality_analyzer.py  # Advanced CV analysis
│   └── advanced_ai_analyzer.py     # AI features
├── disease_detection/              # Disease detection system
├── models/                         # Trained models (downloaded)
├── models_extra/                   # Additional model files (downloaded)
├── static/                         # Frontend assets
├── templates/                      # HTML templates
├── uploads/                        # Uploaded images
└── results/                        # Analysis results
```

### 🎯 Model Information

- **General Detection**: YOLOv8n-seg (80 COCO classes with segmentation)
- **Bell Pepper Model**: Custom-trained YOLOv8 for bell pepper detection
- **Disease Detection**: EfficientNet-B4 fine-tuned for bell pepper diseases
- **Quality Analysis**: Custom computer vision algorithms + ANFIS-inspired system

### 🔧 Configuration

The system automatically loads the best available models:
- Falls back to general YOLOv8 if specialized model unavailable
- Graceful degradation for missing dependencies
- Configurable quality thresholds

### 📱 Mobile Features

- **PWA Support**: Install as mobile app
- **Camera Integration**: Direct photo capture
- **Responsive Design**: Optimized for all screen sizes
- **Offline Capabilities**: Service worker caching

### 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### 🙏 Acknowledgments

- YOLOv8 by Ultralytics
- OpenCV community
- PyTorch team
- Bootstrap framework

---

**Made with ❤️ for the agricultural community**
"""
    
    with open("README.md", "w", encoding='utf-8') as f:
        f.write(readme_content)
    
    print("📄 Updated README.md with download instructions")

def main():
    """Main function to prepare the project for GitHub"""
    
    print("🚀 PepperAI GitHub Preparation")
    print("=" * 50)
    
    # Clean up large files
    clean_large_files()
    
    # Create download scripts
    create_model_download_script()
    create_model_download_bat()
    
    # Update README
    update_readme_with_download_instructions()
    
    print("\n✅ Project prepared for GitHub!")
    print("\n📋 Next steps:")
    print("1. Run: git add .")
    print("2. Run: git commit -m 'Initial commit'")
    print("3. Run: git push origin main")
    print("4. Share the download scripts with users")
    
    print("\n📝 Note: Large model files have been removed.")
    print("Users will need to run the download scripts to get the models.")

if __name__ == "__main__":
    main()
