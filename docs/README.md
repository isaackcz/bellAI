# 🌶️ PepperAI - Bell Pepper Quality Assessment System

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3%2B-green)](https://flask.palletsprojects.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-purple)](https://github.com/ultralytics/ultralytics)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

> **Advanced AI-powered web application for automated bell pepper quality grading using YOLOv8, ANFIS, and machine learning.**

---

## 🎯 Project Overview

PepperAI is a capstone project that automates the quality grading of bell peppers using:
- **YOLOv8** for detection (general + specialized models)
- **ANFIS** (Adaptive Neuro-Fuzzy Inference System) for quality assessment
- **Advanced Computer Vision** for detailed analysis
- **Disease Detection** for health assessment
- **Web Application** with user authentication and history tracking

### Key Features

✅ **Multi-Model AI System**
- General object detection (80 COCO classes)
- Specialized bell pepper detection
- ANFIS quality grading (0-100 score)
- Disease detection and health analysis
- Advanced AI (ripeness, shelf life, nutrition)

✅ **Professional Web Interface**
- User authentication & authorization
- Traditional admin dashboard layout
- Real-time camera capture
- File upload support
- Mobile-responsive design

✅ **Comprehensive Tracking**
- Individual bell pepper database
- Analysis history
- Quality metrics storage
- Detailed pepper profiles

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Webcam (optional, for camera feature)
- 4GB+ RAM (for AI models)

### Installation

```bash
# 1. Clone or download the project
cd pepperai

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
python app.py
```

### First Time Setup

```bash
# Optional: Create admin account
python create_admin.py

# Access the application
http://localhost:5000
```

### Quick Launch

```bash
# Use the startup script (Windows)
start_pepperai.bat
```

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| **[START_HERE.md](START_HERE.md)** | 👈 **Begin here!** Quick start guide |
| [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) | Complete system overview |
| [VISUAL_GUIDE.md](VISUAL_GUIDE.md) | Visual layouts and UI guide |
| [README_AUTH.md](README_AUTH.md) | Authentication system details |
| [ADMIN_LAYOUT.md](ADMIN_LAYOUT.md) | Admin layout components |
| [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) | Code organization guide |

---

## 🎨 User Interface

### Design Philosophy
- **Google Material-inspired** aesthetic
- **Clean white backgrounds** with gradient accents
- **Indigo & purple** color scheme (#6366f1, #7c3aed)
- **Smooth animations** and transitions
- **Professional typography** (Inter font)

### Pages

1. **Login/Register** - Secure authentication
2. **Dashboard** - Statistics and recent analyses
3. **New Analysis** - Camera/upload interface
4. **Bell Pepper History** - All detected peppers
5. **Pepper Details** - Individual pepper analysis

---

## 🤖 AI Models

### Detection Models

1. **YOLOv8n-seg** - General object detection (80 classes)
2. **YOLOv8 Custom** - Specialized bell pepper detection
3. **Disease Detector** - Health and disease analysis (optional)

### Quality Assessment

1. **ANFIS System** - Fuzzy logic quality grading
2. **CV Analyzer** - Computer vision metrics
3. **Advanced AI** - Ripeness prediction, shelf life estimation

### Metrics Analyzed

- **Color Uniformity** - Consistency of color distribution
- **Size Consistency** - Shape regularity
- **Surface Quality** - Defect and blemish detection
- **Ripeness Level** - Maturity assessment
- **Health Score** - Overall health rating

---

## 📊 Database Schema

### Tables

**Users** - Account management
- Authentication credentials
- Profile information
- Role-based access

**AnalysisHistory** - Analysis sessions
- Image paths (original & annotated)
- Summary statistics
- Timestamps

**BellPepperDetection** - Individual peppers
- Quality metrics (all measurements)
- Cropped images
- Advanced analysis data
- Recommendations

---

## 🎯 Features

### Authentication & Access Control
- ✅ Secure user registration
- ✅ Login with "Remember me"
- ✅ Role-based permissions (user/admin)
- ✅ Session management
- ✅ Password hashing

### Analysis Capabilities
- ✅ Live camera capture
- ✅ File upload (JPG, PNG, GIF, WebP)
- ✅ Multi-pepper detection
- ✅ Quality grading (0-100 scale)
- ✅ Disease detection
- ✅ Advanced AI insights

### Data Management
- ✅ Individual pepper tracking
- ✅ Complete analysis history
- ✅ Pagination support
- ✅ Quality statistics
- ✅ Variety distribution

### User Interface
- ✅ Traditional admin layout
- ✅ Sidebar navigation
- ✅ Responsive design
- ✅ Mobile menu
- ✅ Animated backgrounds
- ✅ Flash messages
- ✅ Breadcrumb navigation

---

## 🏗️ Project Structure

```
pepperai/
├── app.py                      # Main Flask application
├── models.py                   # Database models
├── routes/                     # Route blueprints
│   └── history.py             # History routes
├── templates/                  # HTML templates
│   ├── base.html              # Master layout
│   ├── components/            # Reusable components
│   ├── dashboard.html         # Dashboard page
│   ├── index.html             # Analysis page
│   └── history.html           # History page
├── static/                     # Static assets
│   ├── css/                   # Stylesheets
│   ├── js/                    # JavaScript
│   └── images/                # Images & icons
├── python_modules/            # Custom Python modules
│   ├── pepper_quality_analyzer.py
│   └── advanced_ai_analyzer.py
├── disease_detection/         # Disease detection module
├── models/                    # AI model files
│   └── bell_pepper_model.pt
├── uploads/                   # User uploads
├── results/                   # Analysis results
└── pepperai.db               # SQLite database
```

---

## 🔧 Configuration

### Environment Setup

```python
# app.py configuration
SECRET_KEY = 'your-secret-key-change-in-production'
SQLALCHEMY_DATABASE_URI = 'sqlite:///pepperai.db'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
```

### Production Deployment

For production, update:
- Change `SECRET_KEY` to secure random string
- Use PostgreSQL instead of SQLite
- Enable HTTPS
- Configure proper logging
- Set debug=False

---

## 📱 Browser Support

| Browser | Version | Status |
|---------|---------|--------|
| Chrome | 90+ | ✅ Full Support |
| Firefox | 88+ | ✅ Full Support |
| Safari | 14+ | ✅ Full Support |
| Edge | 90+ | ✅ Full Support |
| Mobile | All | ✅ Responsive |

---

## 🎓 Academic Context

### Capstone Project Goals

1. ✅ **Automation** - Reduce manual grading effort
2. ✅ **Standardization** - Consistent quality assessment
3. ✅ **Efficiency** - Fast, accurate analysis
4. ✅ **Accessibility** - Web-based, user-friendly
5. ✅ **Scalability** - Handle multiple users

### Technologies Demonstrated

- **Machine Learning** - ANFIS, YOLOv8
- **Computer Vision** - OpenCV, image processing
- **Web Development** - Flask, SQLAlchemy
- **Database Design** - Relational schema
- **UI/UX Design** - Modern, responsive interface
- **Software Engineering** - Modular architecture

---

## 📊 Performance

### Analysis Speed
- **Detection:** 1-2 seconds
- **Quality Analysis:** 0.5-1 second
- **Total:** 2-5 seconds per image

### Accuracy
- **Detection:** >90% confidence (trained model)
- **Quality Grading:** ANFIS-based scoring
- **Disease Detection:** Health assessment available

---

## 🛠️ Development

### Adding New Features

```python
# 1. Add route in routes/ directory
# 2. Create template in templates/
# 3. Extend base.html
# 4. Update sidebar navigation
# 5. Add to documentation
```

### Code Organization

- **Models** → `models.py`
- **Routes** → `routes/*.py`
- **Templates** → `templates/*.html`
- **Components** → `templates/components/*.html`
- **Static** → `static/css/`, `static/js/`

---

## 🔒 Security

- ✅ Password hashing (Werkzeug)
- ✅ Session management (Flask)
- ✅ SQL injection prevention (SQLAlchemy)
- ✅ XSS protection (auto-escaping)
- ✅ CSRF protection (sessions)
- ✅ User isolation (ownership validation)

---

## 📞 Support

### Issues?

1. Check console logs for errors
2. Verify dependencies installed
3. Review documentation
4. Clear browser cache
5. Try incognito mode

### Common Solutions

```bash
# Reinstall dependencies
pip install -r requirements.txt

# Reset database
del pepperai.db
python app.py

# Check Python version
python --version  # Should be 3.8+
```

---

## 🎯 Use Cases

### For Farmers
- Grade peppers quickly
- Track quality over time
- Get storage recommendations

### For Vendors
- Assess batch quality
- Price estimation support
- Quality distribution analysis

### For Researchers
- Collect quality data
- Analyze trends
- Export for further study

### For Students
- Learn ML integration
- Understand web development
- Study quality assessment systems

---

## 🏆 Achievements

### Technical
- ✅ Multi-model AI system integrated
- ✅ Real-time image processing
- ✅ Database-driven application
- ✅ RESTful API design
- ✅ Modular architecture

### Design
- ✅ Professional UI/UX
- ✅ Consistent styling
- ✅ Mobile responsive
- ✅ Accessible interface
- ✅ Smooth animations

### Functionality
- ✅ Complete CRUD operations
- ✅ User management
- ✅ History tracking
- ✅ Quality assessment
- ✅ Report generation

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **YOLOv8** by Ultralytics
- **Flask** web framework
- **OpenCV** computer vision library
- **Google Fonts** (Inter)
- **Font Awesome** icons

---

## 🎉 Get Started!

```bash
python app.py
```

Visit: **http://localhost:5000**

Register → Login → Analyze → View History

---

## 📧 Contact

For questions about this capstone project, please refer to the documentation or check the console logs for debugging.

---

**Built with ❤️ for automated bell pepper quality assessment**

*Helping farmers, vendors, and agricultural cooperatives standardize grading and improve efficiency in post-harvest handling.*

---

## 🔗 Quick Links

- [Quick Start](START_HERE.md)
- [Visual Guide](VISUAL_GUIDE.md)
- [Complete Summary](COMPLETE_SUMMARY.md)
- [Authentication Guide](README_AUTH.md)
- [Admin Layout](ADMIN_LAYOUT.md)
- [Refactoring Details](REFACTORING_GUIDE.md)

---

**Version 2.0** - Now with complete authentication, admin dashboard, and individual pepper tracking! 🚀
