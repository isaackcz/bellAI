# PepperAI - Bell Pepper Detection & Quality Assessment System

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
