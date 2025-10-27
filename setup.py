#!/usr/bin/env python3
"""
PepperAI Setup Script
Automated setup and initialization for PepperAI Bell Pepper Detection System
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_banner():
    """Print the PepperAI banner"""
    print("=" * 60)
    print("🌶️  PepperAI - Bell Pepper Detection & Quality Assessment")
    print("=" * 60)
    print("Automated Setup Script")
    print("=" * 60)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def check_docker():
    """Check if Docker is installed and running"""
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Docker found: {result.stdout.strip()}")
        
        # Check if Docker daemon is running
        subprocess.run(['docker', 'info'], 
                      capture_output=True, text=True, check=True)
        print("✅ Docker daemon is running")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker not found or not running")
        print("   Please install Docker Desktop and start it")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ['uploads', 'results', 'backups', 'logs', 'instance']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def create_env_file():
    """Create .env file from .env.example if it doesn't exist"""
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            shutil.copy('.env.example', '.env')
            print("✅ Created .env file from .env.example")
            print("   Please edit .env file with your configuration")
        else:
            print("⚠️  .env.example not found, creating basic .env file")
            with open('.env', 'w') as f:
                f.write("""# PepperAI Environment Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key-change-this-in-production
DATABASE_URL=sqlite:///instance/pepperai.db
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=uploads
RESULTS_FOLDER=results
""")
    else:
        print("✅ .env file already exists")

def download_models():
    """Download required models if they don't exist"""
    models_dir = Path('models')
    models_extra_dir = Path('models_extra')
    
    # Check if models exist
    bell_pepper_model = models_dir / 'bell_pepper_model.pt'
    yolov8n_model = models_extra_dir / 'yolov8n.pt'
    yolov8n_seg_model = models_extra_dir / 'yolov8n-seg.pt'
    
    if not bell_pepper_model.exists():
        print("⚠️  Bell pepper model not found")
        print("   Please download the trained model and place it in models/")
    
    if not yolov8n_model.exists() or not yolov8n_seg_model.exists():
        print("⚠️  YOLOv8 models not found")
        print("   These will be downloaded automatically on first run")

def check_requirements():
    """Check if requirements.txt exists"""
    if os.path.exists('requirements.txt'):
        print("✅ requirements.txt found")
    else:
        print("❌ requirements.txt not found")
        return False
    return True

def main():
    """Main setup function"""
    print_banner()
    
    # Check Python version
    check_python_version()
    
    # Check Docker
    docker_available = check_docker()
    
    # Create directories
    create_directories()
    
    # Create .env file
    create_env_file()
    
    # Check requirements
    if not check_requirements():
        print("❌ Setup failed: requirements.txt not found")
        sys.exit(1)
    
    # Check models
    download_models()
    
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("=" * 60)
    
    if docker_available:
        print("\n🐳 Docker Setup:")
        print("   Windows: Run 'docker-start.bat'")
        print("   Linux/Mac: Run './docker-start.sh'")
        print("   Manual: Run 'docker-compose up --build -d'")
    else:
        print("\n🐍 Python Setup:")
        print("   1. Create virtual environment: python -m venv venv")
        print("   2. Activate virtual environment:")
        print("      - Windows: venv\\Scripts\\activate")
        print("      - Linux/Mac: source venv/bin/activate")
        print("   3. Install dependencies: pip install -r requirements.txt")
        print("   4. Run application: python app.py")
    
    print("\n📚 Documentation:")
    print("   - Docker setup: See DOCKER_README.md")
    print("   - General info: See README.md")
    print("   - Web interface: http://localhost (after starting)")
    
    print("\n🔧 Next steps:")
    print("   1. Edit .env file with your configuration")
    print("   2. Download required models (see docs/)")
    print("   3. Start the application")
    print("   4. Open http://localhost in your browser")

if __name__ == "__main__":
    main()
