#!/usr/bin/env python3
"""
Quick integration script for Flask app
Run this script to automatically update your Flask app
"""

import os
import shutil
from pathlib import Path

def integrate_bell_pepper_model():
    print("🌶️ Integrating Bell Pepper Model with Flask App")
    print("=" * 50)
    
    # Check if model file exists
    model_file = "bell_pepper_model.pt"
    if not os.path.exists(model_file):
        print(f"❌ Model file not found: {model_file}")
        return False
    
    # Create models directory in Flask app
    models_dir = Path("../models")  # Adjust path as needed
    models_dir.mkdir(exist_ok=True)
    
    # Copy model file
    shutil.copy2(model_file, models_dir / model_file)
    print(f"✅ Copied {model_file} to {models_dir}")
    
    print("\n🎯 Next Steps:")
    print("1. Update your Flask app.py model loading code")
    print("2. Test with bell pepper images")
    print("3. Adjust confidence thresholds as needed")
    print("\nSee README.md for detailed integration instructions!")
    
    return True

if __name__ == "__main__":
    integrate_bell_pepper_model()
