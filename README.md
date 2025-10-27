# 🌶️ PepperAI - Bell Pepper Detection & Quality Assessment System

A comprehensive AI-powered system for detecting, analyzing, and assessing the quality of bell peppers using computer vision and machine learning.

## ✨ Features

- **Multi-Model Detection**: YOLOv8 general detection + specialized bell pepper detection
- **Quality Assessment**: Advanced computer vision analysis for ripeness, size, and surface quality
- **Disease Detection**: Health analysis and disease identification
- **User Management**: Complete authentication and user management system
- **Real-time Analysis**: Live camera capture and instant analysis
- **Data Export**: Export analysis results and statistics
- **Fully Dockerized**: Complete containerization for easy deployment

## 🚀 Quick Start

### Option 1: Docker (Recommended)

**Windows:**
```cmd
# Clone the repository
git clone https://github.com/isaackcz/bellAI.git
cd bellAI

# Start the application
docker-start.bat
```

**Linux/macOS:**
```bash
# Clone the repository
git clone https://github.com/isaackcz/bellAI.git
cd bellAI

# Make scripts executable
chmod +x docker-start.sh

# Start the application
./docker-start.sh
```

### Option 2: Python Setup

```bash
# Clone the repository
git clone https://github.com/isaackcz/bellAI.git
cd bellAI

# Run setup script
python setup.py

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

## 🌐 Access the Application

Once started, open your browser and navigate to:
- **Web Interface**: http://localhost
- **Health Check**: http://localhost/health
- **Direct App**: http://localhost:5000 (bypasses nginx)

## 📋 Prerequisites

- **Docker**: Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- **Python**: 3.8+ (if not using Docker)
- **Memory**: At least 4GB RAM available for Docker
- **Storage**: At least 2GB free disk space

## 🐳 Docker Architecture

The system includes the following services:

- **pepperai**: Main Flask application
- **nginx**: Reverse proxy and static file server
- **redis**: Caching and session storage
- **backup**: Automated database backup service

## 📁 Project Structure

```
pepperai/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Multi-service orchestration
├── .env.example          # Environment variables template
├── setup.py              # Automated setup script
├── static/               # Static assets (CSS, JS, images)
├── templates/            # HTML templates
├── routes/               # Flask route blueprints
├── python_modules/       # Custom Python modules
├── disease_detection/    # Disease detection modules
├── models/               # AI model files
├── nginx/                # Nginx configuration
├── uploads/              # User uploaded images
├── results/              # Analysis results
└── docs/                 # Documentation
```

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Key variables to configure:
- `SECRET_KEY`: Flask secret key (change in production)
- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis connection string
- `MAX_CONTENT_LENGTH`: Maximum file upload size

### Model Files

The system requires the following model files:

1. **Bell Pepper Model**: `models/bell_pepper_model.pt`
2. **YOLOv8 Models**: `models_extra/yolov8n.pt` and `models_extra/yolov8n-seg.pt`

These will be downloaded automatically on first run, or you can download them manually.

## 🎯 Usage

### Web Interface

1. **Login/Register**: Create an account or login
2. **Upload Image**: Upload a bell pepper image for analysis
3. **Live Camera**: Use the camera for real-time analysis
4. **View Results**: See detailed analysis results including:
   - Detection confidence
   - Quality assessment
   - Disease detection
   - Size and ripeness analysis

### API Endpoints

- `POST /analyze`: Upload image for analysis
- `GET /health`: Health check endpoint
- `GET /api/statistics`: Get analysis statistics
- `GET /api/history`: Get analysis history

## 📊 Features in Detail

### Detection Capabilities

- **General Object Detection**: 80 COCO classes with YOLOv8
- **Bell Pepper Detection**: Specialized model for bell peppers
- **Segmentation**: Pixel-perfect masks for precise analysis
- **Multi-scale Detection**: Detects peppers at various sizes

### Quality Assessment

- **Color Analysis**: Ripeness assessment based on color
- **Size Analysis**: Size consistency and grading
- **Surface Quality**: Defect detection and surface analysis
- **Shape Analysis**: Shape consistency and symmetry

### Disease Detection

- **Health Analysis**: Overall plant health assessment
- **Disease Identification**: Common pepper diseases
- **Symptom Analysis**: Visual symptom detection
- **Treatment Recommendations**: Suggested treatments

## 🛠️ Development

### Running in Development Mode

```bash
# Set development environment
export FLASK_ENV=development
export DEBUG=True

# Run the application
python app.py
```

### Docker Development

```bash
# Build and run in development mode
docker-compose -f docker-compose.dev.yml up --build
```

## 📚 Documentation

- **[Docker Setup](DOCKER_README.md)**: Complete Docker deployment guide
- **[API Documentation](docs/)**: Detailed API documentation
- **[User Guide](docs/USER_GUIDE.md)**: User interface guide
- **[Admin Guide](docs/ADMIN_GUIDE.md)**: Administration guide

## 🔒 Security

- **Authentication**: Secure user authentication system
- **Authorization**: Role-based access control
- **Input Validation**: Comprehensive input validation
- **File Upload Security**: Secure file upload handling
- **HTTPS Ready**: SSL/TLS configuration support

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**:
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

2. **Docker Deployment**:
   ```bash
   docker-compose up -d
   ```

3. **Health Check**:
   ```bash
   curl http://localhost/health
   ```

### Scaling

- **Horizontal Scaling**: Multiple app instances behind nginx
- **Database Scaling**: PostgreSQL for production
- **Caching**: Redis for session and data caching
- **CDN**: Static file delivery optimization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ultralytics**: YOLOv8 implementation
- **OpenCV**: Computer vision library
- **Flask**: Web framework
- **Docker**: Containerization platform

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/isaackcz/bellAI/issues)
- **Documentation**: [Project Wiki](https://github.com/isaackcz/bellAI/wiki)
- **Email**: [Contact Information]

## 🔄 Changelog

### v1.0.0 (Latest)
- Complete Docker containerization
- Production-ready deployment
- Enhanced security features
- Comprehensive documentation
- Multi-service architecture

---

**PepperAI** - Revolutionizing bell pepper quality assessment with AI! 🌶️✨
