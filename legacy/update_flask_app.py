"""
Flask App Updater for Bell Pepper Model Integration
This script updates your existing Flask app to use the trained bell pepper model
"""

import os
import shutil
from pathlib import Path

def update_flask_app_for_bell_pepper_model(
    app_file='app.py',
    model_file='models/bell_pepper_model.pt',
    backup=True
):
    """
    Update Flask app to integrate the trained bell pepper model
    
    Args:
        app_file: Path to your Flask app.py file
        model_file: Path to your trained model file
        backup: Whether to create a backup of the original app.py
    """
    
    print("🔄 Updating Flask App for Bell Pepper Model Integration")
    print("=" * 55)
    
    # Create models directory if it doesn't exist
    models_dir = Path('models')
    models_dir.mkdir(exist_ok=True)
    
    # Create backup if requested
    if backup and os.path.exists(app_file):
        backup_file = f"{app_file}.backup"
        shutil.copy2(app_file, backup_file)
        print(f"✅ Backup created: {backup_file}")
    
    # Read the current app.py
    with open(app_file, 'r') as f:
        content = f.read()
    
    # Define the updated model loading section
    updated_models_section = '''# Load models with error handling
MODELS = {
    'bell_pepper_detection': None,  # Main bell pepper detection model
    'ripeness_detection': None,     # Ripeness detection (can be same model)
    'disease_detection': None       # Disease detection (separate model if available)
}

# Try to load specialized bell pepper model
try:
    MODELS['bell_pepper_detection'] = YOLO('models/bell_pepper_model.pt')
    print("✅ Bell pepper detection model loaded successfully")
except Exception as e:
    print(f"Warning: Bell pepper model not found: {e}")
    print("Falling back to general YOLOv8 model...")
    MODELS['bell_pepper_detection'] = YOLO('yolov8n.pt')
    
# Try to load specialized models if they exist
try:
    MODELS['ripeness_detection'] = YOLO('models/bellpepper-ripeness-model.pt')
    print("✅ Ripeness detection model loaded")
except:
    print("Info: Using bell pepper model for ripeness detection")
    MODELS['ripeness_detection'] = MODELS['bell_pepper_detection']
    
try:
    MODELS['disease_detection'] = YOLO('models/bellpepper-disease-model.pt')
    print("✅ Disease detection model loaded")
except:
    print("Info: Disease detection model not found. Disease detection will be limited.")'''
    
    # Replace the existing model loading section
    import re
    
    # Pattern to match the existing model loading section
    pattern = r'# Load models with error handling.*?print\("Warning: Disease detection model not found\. Disease detection will be limited\."\)'
    
    if re.search(pattern, content, re.DOTALL):
        # Replace existing section
        content = re.sub(pattern, updated_models_section, content, flags=re.DOTALL)
        print("✅ Updated existing model loading section")
    else:
        # If pattern not found, look for simpler pattern
        simple_pattern = r'MODELS = \{.*?\}'
        if re.search(simple_pattern, content, re.DOTALL):
            content = re.sub(simple_pattern, updated_models_section, content, flags=re.DOTALL)
            print("✅ Updated MODELS dictionary")
        else:
            print("⚠️ Could not find existing model section. Manual update required.")
    
    # Update the bell pepper detection logic
    updated_detection_logic = '''            # Check if bell pepper is detected using our specialized model
            bell_peppers_detected = False
            pepper_boxes = []
            
            if result.boxes is not None:
                for box in result.boxes:
                    cls = int(box.cls.cpu().numpy()[0])
                    class_name = result.names[cls] if hasattr(result, 'names') else str(cls)
                    conf = float(box.conf.cpu().numpy()[0])
                    
                    # All detections from our specialized model are bell peppers
                    # Check confidence threshold
                    if conf > 0.5:  # Adjustable confidence threshold
                        bell_peppers_detected = True
                        xyxy = box.xyxy.cpu().numpy()[0].tolist()
                        pepper_boxes.append({
                            'bbox': xyxy,
                            'confidence': conf,
                            'class': class_name,
                            'variety': class_name  # This will be the bell pepper variety/color
                        })'''
    
    # Replace the bell pepper detection logic
    detection_pattern = r'# Check if bell peppers are detected.*?pepper_boxes\.append\(xyxy\)'
    if re.search(detection_pattern, content, re.DOTALL):
        content = re.sub(detection_pattern, updated_detection_logic, content, flags=re.DOTALL)
        print("✅ Updated bell pepper detection logic")
    
    # Update the model usage in the upload function
    upload_pattern = r'# Run general object detection first\s*results = MODELS\[\'object_detection\'\]\(filepath\)'
    replacement = "# Run bell pepper detection\n            results = MODELS['bell_pepper_detection'](filepath)"
    
    if re.search(upload_pattern, content):
        content = re.sub(upload_pattern, replacement, content)
        print("✅ Updated model usage in upload function")
    
    # Write the updated content back to the file
    with open(app_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Flask app updated successfully: {app_file}")
    
    # Create integration instructions
    instructions = f"""
# 🌶️ Bell Pepper Model Integration Complete!

## Files Updated:
- ✅ {app_file} (backup: {app_file}.backup)

## What Changed:
1. **Model Loading**: Now prioritizes your trained bell pepper model
2. **Detection Logic**: Optimized for bell pepper varieties/colors
3. **Confidence Handling**: Adjustable confidence threshold (currently 0.5)
4. **Fallback**: Falls back to general YOLOv8 if specialized model not found

## Next Steps:
1. Copy your trained model to: `{model_file}`
2. Test the updated app:
   ```bash
   python {app_file}
   ```
3. Upload bell pepper images to test detection
4. Adjust confidence threshold if needed (line with `conf > 0.5`)

## Model Performance Tuning:
- **Confidence Threshold**: Adjust `conf > 0.5` in the detection logic
- **Class Names**: Your model will return specific bell pepper varieties
- **Multiple Models**: You can add separate ripeness/disease detection models

## Troubleshooting:
- If model not found: Check the path `{model_file}`
- If low accuracy: Lower confidence threshold or retrain with more data
- If wrong detections: Verify your training data quality

Happy detecting! 🎉
"""
    
    with open('integration_instructions.md', 'w') as f:
        f.write(instructions)
    
    print(f"📝 Integration instructions saved: integration_instructions.md")
    
    return True

def create_model_config(model_path='models/bell_pepper_model.pt'):
    """Create configuration file for the bell pepper model"""
    
    config = {
        'model_info': {
            'name': 'Bell Pepper YOLOv8 Model',
            'version': '1.0',
            'description': 'Specialized YOLOv8 model for bell pepper detection and classification',
            'path': model_path,
            'confidence_threshold': 0.5,
            'nms_threshold': 0.45
        },
        'classes': {
            'note': 'Classes will be automatically loaded from the model',
            'expected_classes': [
                'bell_pepper_0', 'bell_pepper_1', 'bell_pepper_2',
                'bell_pepper_3', 'bell_pepper_4', 'bell_pepper_5'
            ]
        },
        'performance': {
            'target_fps': 30,
            'max_batch_size': 4,
            'image_size': 640
        },
        'features': {
            'color_analysis': True,
            'ripeness_detection': True,
            'disease_detection': False,
            'size_estimation': False
        }
    }
    
    import json
    with open('models/model_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Model configuration created: models/model_config.json")

def validate_integration():
    """Validate that the integration is working correctly"""
    print("\n🔍 Validating Integration...")
    print("=" * 30)
    
    # Check if required files exist
    required_files = [
        'app.py',
        'models/',
        'templates/index.html',
        'static/js/script.js'
    ]
    
    all_good = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing!")
            all_good = False
    
    # Check if models directory has the expected structure
    models_dir = Path('models')
    if models_dir.exists():
        if (models_dir / 'bell_pepper_model.pt').exists():
            print("✅ Bell pepper model found")
        else:
            print("⚠️ Bell pepper model not found - place it in models/bell_pepper_model.pt")
            all_good = False
    
    if all_good:
        print("\n🎉 Integration validation passed!")
        print("Your app is ready to use the trained bell pepper model!")
    else:
        print("\n⚠️ Some issues found. Please fix them before testing.")
    
    return all_good

if __name__ == "__main__":
    print("🌶️ Bell Pepper Model Integration Tool")
    print("=" * 40)
    
    # Update Flask app
    update_flask_app_for_bell_pepper_model()
    
    # Create model configuration
    create_model_config()
    
    # Validate integration
    validate_integration()
    
    print("\n🎯 Integration complete!")
    print("Copy your trained 'bell_pepper_model.pt' to the 'models/' directory and test your app!")
