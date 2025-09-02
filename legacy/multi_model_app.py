"""
Multi-Model Bell Pepper Detection and Quality Assessment System
Combines YOLOv8 general detection + specialized bell pepper YOLOv8 + ANFIS quality analysis
"""

import os
import cv2
import numpy as np
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from ultralytics import YOLO
from PIL import Image
import torch
import skfuzzy as fuzz
from skfuzzy import control as ctrl

app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

# Multi-Model Setup
MODELS = {
    'general_detection': None,      # YOLOv8 general (80 classes)
    'bell_pepper_detection': None,  # Your trained bell pepper model
    'anfis_quality': None          # ANFIS quality assessment system
}

print("🚀 Loading Multi-Model System...")
print("=" * 40)

# Load YOLOv8 General Model (80 COCO classes)
try:
    MODELS['general_detection'] = YOLO('yolov8n.pt')
    print("✅ General YOLOv8 model loaded (80 classes)")
except Exception as e:
    print(f"❌ Failed to load general model: {e}")

# Load Specialized Bell Pepper Model
try:
    MODELS['bell_pepper_detection'] = YOLO('models/bell_pepper_model.pt')
    print("✅ Specialized bell pepper model loaded")
except Exception as e:
    print(f"❌ Failed to load bell pepper model: {e}")

# Initialize ANFIS System for Quality Assessment
class ANFISQualityAssessment:
    """
    Adaptive Neuro-Fuzzy Inference System for Bell Pepper Quality Assessment
    """
    
    def __init__(self):
        self.setup_fuzzy_system()
        print("✅ ANFIS quality assessment system initialized")
    
    def setup_fuzzy_system(self):
        """Setup fuzzy logic system for bell pepper quality assessment"""
        
        # Input variables
        self.color_uniformity = ctrl.Antecedent(np.arange(0, 101, 1), 'color_uniformity')
        self.size_consistency = ctrl.Antecedent(np.arange(0, 101, 1), 'size_consistency')
        self.surface_quality = ctrl.Antecedent(np.arange(0, 101, 1), 'surface_quality')
        self.ripeness_level = ctrl.Antecedent(np.arange(0, 101, 1), 'ripeness_level')
        
        # Output variable
        self.quality_grade = ctrl.Consequent(np.arange(0, 101, 1), 'quality_grade')
        
        # Membership functions for inputs
        self.color_uniformity['poor'] = fuzz.trimf(self.color_uniformity.universe, [0, 0, 40])
        self.color_uniformity['average'] = fuzz.trimf(self.color_uniformity.universe, [20, 50, 80])
        self.color_uniformity['excellent'] = fuzz.trimf(self.color_uniformity.universe, [60, 100, 100])
        
        self.size_consistency['small'] = fuzz.trimf(self.size_consistency.universe, [0, 0, 40])
        self.size_consistency['medium'] = fuzz.trimf(self.size_consistency.universe, [20, 50, 80])
        self.size_consistency['large'] = fuzz.trimf(self.size_consistency.universe, [60, 100, 100])
        
        self.surface_quality['damaged'] = fuzz.trimf(self.surface_quality.universe, [0, 0, 30])
        self.surface_quality['fair'] = fuzz.trimf(self.surface_quality.universe, [20, 50, 80])
        self.surface_quality['pristine'] = fuzz.trimf(self.surface_quality.universe, [70, 100, 100])
        
        self.ripeness_level['unripe'] = fuzz.trimf(self.ripeness_level.universe, [0, 0, 40])
        self.ripeness_level['optimal'] = fuzz.trimf(self.ripeness_level.universe, [30, 60, 90])
        self.ripeness_level['overripe'] = fuzz.trimf(self.ripeness_level.universe, [80, 100, 100])
        
        # Output membership functions
        self.quality_grade['poor'] = fuzz.trimf(self.quality_grade.universe, [0, 0, 30])
        self.quality_grade['fair'] = fuzz.trimf(self.quality_grade.universe, [20, 40, 60])
        self.quality_grade['good'] = fuzz.trimf(self.quality_grade.universe, [50, 70, 90])
        self.quality_grade['excellent'] = fuzz.trimf(self.quality_grade.universe, [80, 100, 100])
        
        # Fuzzy rules
        self.rules = [
            ctrl.Rule(self.color_uniformity['excellent'] & self.surface_quality['pristine'] & 
                     self.ripeness_level['optimal'], self.quality_grade['excellent']),
            ctrl.Rule(self.color_uniformity['average'] & self.surface_quality['fair'] & 
                     self.ripeness_level['optimal'], self.quality_grade['good']),
            ctrl.Rule(self.color_uniformity['poor'] | self.surface_quality['damaged'], 
                     self.quality_grade['poor']),
            ctrl.Rule(self.ripeness_level['overripe'] | self.ripeness_level['unripe'], 
                     self.quality_grade['fair']),
        ]
        
        # Control system
        self.quality_ctrl = ctrl.ControlSystem(self.rules)
        self.quality_simulation = ctrl.ControlSystemSimulation(self.quality_ctrl)
    
    def analyze_pepper_image(self, pepper_crop):
        """
        Analyze a cropped bell pepper image and return quality assessment
        """
        try:
            # Convert to HSV for better color analysis
            hsv = cv2.cvtColor(pepper_crop, cv2.COLOR_BGR2HSV)
            
            # Analyze color uniformity
            color_uniformity = self._analyze_color_uniformity(hsv)
            
            # Analyze size consistency (based on contour analysis)
            size_consistency = self._analyze_size_consistency(pepper_crop)
            
            # Analyze surface quality (detect blemishes, spots)
            surface_quality = self._analyze_surface_quality(pepper_crop)
            
            # Analyze ripeness level
            ripeness_level = self._analyze_ripeness(hsv)
            
            # Run ANFIS inference
            self.quality_simulation.input['color_uniformity'] = color_uniformity
            self.quality_simulation.input['size_consistency'] = size_consistency
            self.quality_simulation.input['surface_quality'] = surface_quality
            self.quality_simulation.input['ripeness_level'] = ripeness_level
            
            # Compute result
            self.quality_simulation.compute()
            quality_score = self.quality_simulation.output['quality_grade']
            
            # Determine quality category
            if quality_score >= 80:
                quality_category = "Excellent"
            elif quality_score >= 60:
                quality_category = "Good"
            elif quality_score >= 40:
                quality_category = "Fair"
            else:
                quality_category = "Poor"
            
            return {
                'quality_score': float(quality_score),
                'quality_category': quality_category,
                'color_uniformity': float(color_uniformity),
                'size_consistency': float(size_consistency),
                'surface_quality': float(surface_quality),
                'ripeness_level': float(ripeness_level),
                'recommendations': self._get_recommendations(quality_score, ripeness_level)
            }
            
        except Exception as e:
            print(f"ANFIS analysis error: {e}")
            return {
                'quality_score': 50.0,
                'quality_category': "Unknown",
                'error': str(e)
            }
    
    def _analyze_color_uniformity(self, hsv):
        """Analyze color uniformity of the bell pepper"""
        # Calculate standard deviation of hue values
        hue_std = np.std(hsv[:,:,0])
        # Convert to 0-100 scale (lower std = higher uniformity)
        uniformity = max(0, 100 - (hue_std * 2))
        return min(100, uniformity)
    
    def _analyze_size_consistency(self, image):
        """Analyze size consistency based on contour regularity"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Find largest contour (main pepper)
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            perimeter = cv2.arcLength(largest_contour, True)
            
            if perimeter > 0:
                # Circularity measure (4*pi*area/perimeter^2)
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                return min(100, circularity * 100)
        
        return 50.0  # Default value
    
    def _analyze_surface_quality(self, image):
        """Detect blemishes and surface defects"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection to find irregularities
        edges = cv2.Canny(blurred, 50, 150)
        
        # Count edge pixels as measure of surface irregularity
        edge_pixels = np.sum(edges > 0)
        total_pixels = edges.shape[0] * edges.shape[1]
        
        # Convert to quality score (fewer edges = better quality)
        edge_ratio = edge_pixels / total_pixels
        quality = max(0, 100 - (edge_ratio * 500))
        
        return min(100, quality)
    
    def _analyze_ripeness(self, hsv):
        """Analyze ripeness based on color"""
        # Define color ranges for different ripeness stages
        # Green (unripe): H=35-85
        # Yellow (ripening): H=15-35
        # Red (ripe): H=0-15 or H=165-180
        
        h_channel = hsv[:,:,0]
        
        # Count pixels in each color range
        green_pixels = np.sum((h_channel >= 35) & (h_channel <= 85))
        yellow_pixels = np.sum((h_channel >= 15) & (h_channel < 35))
        red_pixels = np.sum((h_channel <= 15) | (h_channel >= 165))
        
        total_pixels = h_channel.size
        
        # Calculate percentages
        green_pct = green_pixels / total_pixels
        yellow_pct = yellow_pixels / total_pixels
        red_pct = red_pixels / total_pixels
        
        # Determine ripeness level (60 = optimal)
        if red_pct > 0.6:
            return 60 + (red_pct - 0.6) * 100  # Optimal to overripe
        elif yellow_pct > 0.4:
            return 40 + yellow_pct * 50  # Ripening
        else:
            return green_pct * 40  # Unripe
    
    def _get_recommendations(self, quality_score, ripeness_level):
        """Provide recommendations based on analysis"""
        recommendations = []
        
        if quality_score < 50:
            recommendations.append("Consider grading as second quality")
        
        if ripeness_level < 30:
            recommendations.append("Allow more time to ripen")
        elif ripeness_level > 80:
            recommendations.append("Use soon - optimal ripeness achieved")
        
        if quality_score >= 80:
            recommendations.append("Premium grade - suitable for export")
        
        return recommendations

# Initialize ANFIS system
try:
    MODELS['anfis_quality'] = ANFISQualityAssessment()
except Exception as e:
    print(f"❌ Failed to initialize ANFIS: {e}")
    MODELS['anfis_quality'] = None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def detect_bell_peppers_two_stage(image_path):
    """
    Two-stage bell pepper detection:
    1. General YOLOv8 for initial object detection
    2. Specialized bell pepper YOLOv8 for precise pepper detection
    """
    results = {
        'general_objects': [],
        'bell_peppers': [],
        'quality_analysis': []
    }
    
    # Stage 1: General object detection
    if MODELS['general_detection']:
        general_results = MODELS['general_detection'](image_path)
        general_result = general_results[0]
        
        if general_result.boxes is not None:
            for box in general_result.boxes:
                conf = float(box.conf.cpu().numpy()[0])
                cls = int(box.cls.cpu().numpy()[0])
                class_name = general_result.names[cls]
                xyxy = box.xyxy.cpu().numpy()[0].tolist()
                
                results['general_objects'].append({
                    'class_name': class_name,
                    'confidence': conf,
                    'bbox': xyxy,
                    'class_id': cls
                })
    
    # Stage 2: Specialized bell pepper detection
    if MODELS['bell_pepper_detection']:
        pepper_results = MODELS['bell_pepper_detection'](image_path)
        pepper_result = pepper_results[0]
        
        if pepper_result.boxes is not None:
            image = cv2.imread(image_path)
            
            for i, box in enumerate(pepper_result.boxes):
                conf = float(box.conf.cpu().numpy()[0])
                cls = int(box.cls.cpu().numpy()[0])
                class_name = pepper_result.names[cls]
                xyxy = box.xyxy.cpu().numpy()[0].tolist()
                
                bell_pepper_data = {
                    'variety': class_name,
                    'confidence': conf,
                    'bbox': xyxy,
                    'class_id': cls,
                    'pepper_id': f'pepper_{i+1}'
                }
                
                # Stage 3: ANFIS Quality Analysis
                if MODELS['anfis_quality'] and conf > 0.5:
                    # Crop the bell pepper region
                    x1, y1, x2, y2 = map(int, xyxy)
                    pepper_crop = image[y1:y2, x1:x2]
                    
                    if pepper_crop.size > 0:
                        quality_analysis = MODELS['anfis_quality'].analyze_pepper_image(pepper_crop)
                        bell_pepper_data['quality_analysis'] = quality_analysis
                
                results['bell_peppers'].append(bell_pepper_data)
    
    return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S%f')
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f'img_{timestamp}.{ext}'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            # Run two-stage detection with ANFIS analysis
            detection_results = detect_bell_peppers_two_stage(filepath)
            
            # Create annotated image
            image = cv2.imread(filepath)
            annotated_image = image.copy()
            
            # Draw general objects (in blue)
            for obj in detection_results['general_objects']:
                if obj['confidence'] > 0.5:
                    x1, y1, x2, y2 = map(int, obj['bbox'])
                    cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    label = f"{obj['class_name']}: {obj['confidence']:.2f}"
                    cv2.putText(annotated_image, label, (x1, y1-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            
            # Draw bell peppers (in red) with quality info
            for pepper in detection_results['bell_peppers']:
                if pepper['confidence'] > 0.5:
                    x1, y1, x2, y2 = map(int, pepper['bbox'])
                    cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (0, 0, 255), 3)
                    
                    # Label with variety and quality
                    label = f"{pepper['variety']}: {pepper['confidence']:.2f}"
                    if 'quality_analysis' in pepper:
                        quality = pepper['quality_analysis']['quality_category']
                        score = pepper['quality_analysis']['quality_score']
                        label += f" | {quality} ({score:.0f})"
                    
                    cv2.putText(annotated_image, label, (x1, y1-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            # Save annotated image
            out_name = f'res_{timestamp}.jpg'
            out_path = os.path.join(app.config['RESULTS_FOLDER'], out_name)
            cv2.imwrite(out_path, annotated_image)
            
            # Prepare response
            response_data = {
                'result_url': f'/results/{out_name}',
                'general_objects': detection_results['general_objects'],
                'bell_peppers': detection_results['bell_peppers'],
                'summary': {
                    'total_objects': len(detection_results['general_objects']),
                    'bell_peppers_found': len(detection_results['bell_peppers']),
                    'avg_quality_score': np.mean([p.get('quality_analysis', {}).get('quality_score', 0) 
                                                 for p in detection_results['bell_peppers']]) if detection_results['bell_peppers'] else 0
                },
                'message': f"Found {len(detection_results['general_objects'])} objects, {len(detection_results['bell_peppers'])} bell peppers"
            }
            
            return jsonify(response_data)

        except Exception as e:
            return jsonify({'error': f'Processing error: {str(e)}'}), 500

    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/results/<filename>')
def serve_result(filename):
    return send_from_directory(app.config['RESULTS_FOLDER'], filename)

@app.route('/uploads/<filename>')
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    print("\n🌶️ Multi-Model Bell Pepper Detection System Ready!")
    print("=" * 50)
    print("🔍 General object detection: YOLOv8 (80 classes)")
    print("🌶️ Bell pepper detection: Specialized YOLOv8")
    print("🎯 Quality assessment: ANFIS system")
    print("🚀 Starting Flask server...")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
