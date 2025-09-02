# 🌶️ Bell Pepper YOLOv8 Detection Model

## Model Information
- **Model Type**: YOLOv8 Nano (optimized for speed and efficiency)
- **Training Date**: 2025-09-01 06:57:12
- **Dataset Size**: 495 training, 124 validation images
- **Classes**: 6 bell pepper varieties
- **Image Size**: 640px
- **Epochs Trained**: 150

## Performance Metrics
- **mAP@0.5**: 0.362 (36.2%)
- **mAP@0.5:0.95**: 0.200 (20.0%)
- **Precision**: 0.667 (66.7%)
- **Recall**: 0.389 (38.9%)
- **Model Size**: 6.0 MB
- **Parameters**: 3,006,818

## Classes Detected
- 0
- 1
- 2
- 3
- 4
- 5

## Usage in Python
```python
from ultralytics import YOLO

# Load your trained model
model = YOLO('bell_pepper_model.pt')

# Run inference on an image
results = model('path/to/bell_pepper_image.jpg')

# Process results
for result in results:
    boxes = result.boxes  # Bounding boxes
    for box in boxes:
        conf = box.conf.item()  # Confidence score
        cls = box.cls.item()    # Class ID
        class_name = result.names[int(cls)]  # Class name
        print(f"Detected {class_name} with {conf:.2f} confidence")
```

## Integration with Your Flask App

### Step 1: Update Model Loading
Replace the model loading in your `app.py`:

```python
# Replace this line:
MODELS = {
    'object_detection': YOLO('yolov8n.pt'),  # General model
    # ...
}

# With this:
MODELS = {
    'bell_pepper_detection': YOLO('models/bell_pepper_model.pt'),  # Your trained model
    'ripeness_detection': YOLO('models/bell_pepper_model.pt'),     # Same model for ripeness
    'disease_detection': None  # Add disease model later if needed
}
```

### Step 2: Update Detection Logic
In your upload function, change:

```python
# From:
results = MODELS['object_detection'](filepath)

# To:
results = MODELS['bell_pepper_detection'](filepath)
```

### Step 3: Update Bell Pepper Detection
Your model now automatically detects bell peppers, so update the detection logic:

```python
# All detections from your model are bell peppers
bell_peppers_detected = len(result.boxes) > 0 if result.boxes is not None else False

# Each detection will have a specific bell pepper class
for box in result.boxes:
    cls = int(box.cls.cpu().numpy()[0])
    class_name = result.names[cls]  # This will be bell_pepper_1, bell_pepper_2, etc.
    conf = float(box.conf.cpu().numpy()[0])
    
    # Use confidence threshold
    if conf > 0.5:  # Adjust this threshold as needed
        # Process detected bell pepper
        pepper_variety = class_name  # The specific variety/color
```

## Recommended Confidence Thresholds
- **High Precision**: 0.7+ (fewer false positives)
- **Balanced**: 0.5 (good balance)
- **High Recall**: 0.3+ (catch more peppers, but may have false positives)

## Model Performance Analysis
- **Best for**: Bell pepper detection and variety classification
- **Strengths**: Fast inference, good accuracy on bell peppers
- **Use cases**: Quality control, agricultural automation, inventory management

## Troubleshooting
1. **Low detections**: Lower confidence threshold to 0.3-0.4
2. **Too many false positives**: Increase confidence threshold to 0.6-0.7
3. **Wrong varieties**: Your model distinguishes 6 varieties - check class mappings
4. **Performance issues**: Model is optimized for speed, but ensure GPU is available

## Next Steps
1. Copy `bell_pepper_model.pt` to your Flask app's `models/` directory
2. Update your Flask app using the integration code above
3. Test with real bell pepper images
4. Fine-tune confidence thresholds based on your specific needs
5. Consider collecting more data for classes with lower performance

---
**Created with ❤️ using YOLOv8 and the RGBD Pepper Dataset**
