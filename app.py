import os
from datetime import datetime, timedelta
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for, flash
from functools import wraps
from ultralytics import YOLO
from PIL import Image
import torch
from python_modules.pepper_quality_analyzer import BellPepperQualityAnalyzer
from python_modules.advanced_ai_analyzer import AdvancedPepperAnalyzer

# Import models from separate file
from models import db, User, AnalysisHistory, BellPepperDetection, PepperVariety, PepperDisease, PepperType, Notification, NotificationAttachment, NotificationRead

try:
    from disease_detection.disease_integration import PepperHealthAnalyzer
    DISEASE_DETECTION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Disease detection not available: {e}")
    print("Install disease detection dependencies: pip install torch torchvision")
    DISEASE_DETECTION_AVAILABLE = False
    PepperHealthAnalyzer = None
# import skfuzzy as fuzz
# from skfuzzy import control as ctrl

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pepperai.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# Initialize database with app
db.init_app(app)

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

# Register blueprints
from routes import history_bp, statistics_bp, export_bp, pepper_database_bp, notifications_bp
from routes.settings import settings_bp
app.register_blueprint(history_bp)
app.register_blueprint(statistics_bp)
app.register_blueprint(export_bp)
app.register_blueprint(pepper_database_bp)
app.register_blueprint(notifications_bp)
app.register_blueprint(settings_bp)

# Create database tables
with app.app_context():
    db.create_all()
    print("✅ Database tables created")

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Multi-Model Setup: General YOLOv8 + Specialized Bell Pepper + Advanced Quality Analysis + Disease Detection + AI Features
MODELS = {
    'general_detection': None,      # YOLOv8 general (80 classes)
    'bell_pepper_detection': None,  # Your trained bell pepper model
    'anfis_quality': None,         # ANFIS quality assessment system
    'cv_quality_analyzer': None,   # OpenCV + scikit-image quality analyzer
    'health_analyzer': None,       # Disease detection + health analysis
    'advanced_ai_analyzer': None   # Advanced AI features (ripeness, shelf life, nutrition)
}

print("🚀 Loading Enhanced Multi-Model System...")
print("=" * 50)

# Load YOLOv8 Segmentation Model (80 COCO classes with pixel-perfect masks)
try:
    MODELS['general_detection'] = YOLO('models_extra/yolov8n-seg.pt')  # Segmentation model
    print("✅ General YOLOv8 segmentation model loaded (80 classes with masks)")
except Exception as e:
    print(f"❌ Failed to load general segmentation model: {e}")
    # Fallback to detection model
    try:
        MODELS['general_detection'] = YOLO('models_extra/yolov8n.pt')
        print("✅ Fallback: General YOLOv8 detection model loaded")
    except Exception as e2:
        print(f"❌ Failed to load any general model: {e2}")

# Load Specialized Bell Pepper Model (try segmentation first, then detection)
try:
    # Try to load a segmentation version if available
    MODELS['bell_pepper_detection'] = YOLO('models/bell_pepper_model.pt')
    print("✅ Specialized bell pepper model loaded")
except Exception as e:
    print(f"❌ Failed to load bell pepper model: {e}")
    # Fallback to general model for bell pepper detection
    MODELS['bell_pepper_detection'] = MODELS['general_detection']

# Simplified Quality Assessment System (ANFIS-inspired without scikit-fuzzy dependency)
class ANFISQualityAssessment:
    """Simplified Quality Assessment System for Bell Pepper Analysis"""
    
    def __init__(self):
        print("✅ Quality assessment system initialized (simplified version)")
    
    def fuzzy_inference(self, color_uniformity, size_consistency, surface_quality, ripeness_level):
        """Simple fuzzy inference without external library"""
        # Normalize inputs (0-100)
        normalized_inputs = [color_uniformity, size_consistency, surface_quality, ripeness_level]
        
        # Simple weighted scoring system based on ANFIS principles
        weights = [0.25, 0.20, 0.30, 0.25]  # Surface quality has highest weight
        weighted_score = sum(w * v for w, v in zip(weights, normalized_inputs))
        
        # Apply fuzzy rules (simplified)
        # Rule 1: If all metrics are high (>80), quality is excellent
        if all(metric > 80 for metric in normalized_inputs):
            quality_boost = 10
        # Rule 2: If surface quality is low (<30), quality is poor
        elif surface_quality < 30:
            quality_boost = -20
        # Rule 3: If ripeness is very low or very high, reduce quality
        elif ripeness_level < 20 or ripeness_level > 90:
            quality_boost = -10
        # Rule 4: Average performance
        else:
            quality_boost = 0
        
        final_score = max(0, min(100, weighted_score + quality_boost))
        return final_score
    
    def analyze_pepper_image(self, pepper_crop):
        """Analyze a cropped bell pepper image and return quality assessment"""
        try:
            hsv = cv2.cvtColor(pepper_crop, cv2.COLOR_BGR2HSV)
            
            # Analyze color uniformity
            color_uniformity = self._analyze_color_uniformity(hsv)
            size_consistency = self._analyze_size_consistency(pepper_crop)
            surface_quality = self._analyze_surface_quality(pepper_crop)
            ripeness_level = self._analyze_ripeness(hsv)
            
            # Run simplified fuzzy inference
            quality_score = self.fuzzy_inference(color_uniformity, size_consistency, surface_quality, ripeness_level)
            
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
            print(f"Quality analysis error: {e}")
            return {
                'quality_score': 50.0,
                'quality_category': "Unknown",
                'color_uniformity': 50.0,
                'size_consistency': 50.0,
                'surface_quality': 50.0,
                'ripeness_level': 50.0,
                'error': str(e)
            }
    
    def _analyze_color_uniformity(self, hsv):
        hue_std = np.std(hsv[:,:,0])
        uniformity = max(0, 100 - (hue_std * 2))
        return min(100, uniformity)
    
    def _analyze_size_consistency(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            perimeter = cv2.arcLength(largest_contour, True)
            
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                return min(100, circularity * 100)
        
        return 50.0
    
    def _analyze_surface_quality(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        
        edge_pixels = np.sum(edges > 0)
        total_pixels = edges.shape[0] * edges.shape[1]
        edge_ratio = edge_pixels / total_pixels
        quality = max(0, 100 - (edge_ratio * 500))
        
        return min(100, quality)
    
    def _analyze_ripeness(self, hsv):
        h_channel = hsv[:,:,0]
        
        green_pixels = np.sum((h_channel >= 35) & (h_channel <= 85))
        yellow_pixels = np.sum((h_channel >= 15) & (h_channel < 35))
        red_pixels = np.sum((h_channel <= 15) | (h_channel >= 165))
        
        total_pixels = h_channel.size
        
        green_pct = green_pixels / total_pixels
        yellow_pct = yellow_pixels / total_pixels
        red_pct = red_pixels / total_pixels
        
        if red_pct > 0.6:
            return 60 + (red_pct - 0.6) * 100
        elif yellow_pct > 0.4:
            return 40 + yellow_pct * 50
        else:
            return green_pct * 40
    
    def _get_recommendations(self, quality_score, ripeness_level):
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

# Initialize Computer Vision Quality Analyzer
try:
    MODELS['cv_quality_analyzer'] = BellPepperQualityAnalyzer()
    print("✅ Advanced CV Quality Analyzer loaded (OpenCV + scikit-image)")
except Exception as e:
    print(f"❌ Failed to initialize CV Quality Analyzer: {e}")
    MODELS['cv_quality_analyzer'] = None

# Initialize Disease Detection & Health Analyzer
if DISEASE_DETECTION_AVAILABLE:
    try:
        # Try to load with pre-trained disease model if available
        disease_model_path = None
        if os.path.exists('models/disease_model.pth'):
            disease_model_path = 'models/disease_model.pth'
        
        MODELS['health_analyzer'] = PepperHealthAnalyzer(disease_model_path)
        print("✅ Disease Detection & Health Analyzer loaded")
    except Exception as e:
        print(f"❌ Failed to initialize Health Analyzer: {e}")
        MODELS['health_analyzer'] = None
else:
    MODELS['health_analyzer'] = None
    print("⚠️ Disease detection disabled - install dependencies to enable")

# Initialize Advanced AI Analyzer
try:
    MODELS['advanced_ai_analyzer'] = AdvancedPepperAnalyzer()
    print("✅ Advanced AI Analyzer loaded (ripeness prediction, shelf life, nutrition)")
except Exception as e:
    print(f"❌ Failed to initialize Advanced AI Analyzer: {e}")
    MODELS['advanced_ai_analyzer'] = None

# Bell pepper characteristics database
BELL_PEPPER_CLASSES = {
    # Ripeness stages
    'unripe': {'color_range': [(35, 20, 20), (85, 255, 255)], 'description': 'Green, not ready for harvest'},
    'ripening': {'color_range': [(10, 50, 50), (25, 255, 255)], 'description': 'Turning from green to yellow/red'},
    'ripe': {'color_range': [(0, 50, 50), (10, 255, 255)], 'description': 'Fully red and ready for harvest'},
    'overripe': {'color_range': [(0, 0, 0), (180, 50, 50)], 'description': 'Past prime, may show deterioration'},
    
    # Common diseases
    'bacterial_spot': {'symptoms': 'Small, watery lesions on leaves and fruits'},
    'blossom_end_rot': {'symptoms': 'Dark, sunken area on the blossom end of fruit'},
    'anthracnose': {'symptoms': 'Sunken, circular lesions with black centers'},
    'healthy': {'symptoms': 'No signs of disease or deterioration'}
}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_health_status(health_score):
    """Convert health score to status description"""
    if health_score >= 80:
        return 'Excellent Health'
    elif health_score >= 60:
        return 'Good Health'
    elif health_score >= 40:
        return 'Fair Health'
    else:
        return 'Poor Health'

def calculate_iou(box1, box2):
    """Calculate Intersection over Union (IoU) between two bounding boxes"""
    x1_inter = max(box1[0], box2[0])
    y1_inter = max(box1[1], box2[1])
    x2_inter = min(box1[2], box2[2])
    y2_inter = min(box1[3], box2[3])
    
    if x2_inter <= x1_inter or y2_inter <= y1_inter:
        return 0.0
    
    inter_area = (x2_inter - x1_inter) * (y2_inter - y1_inter)
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
    
    union_area = box1_area + box2_area - inter_area
    return inter_area / union_area if union_area > 0 else 0.0

def filter_overlapping_detections(boxes, conf_threshold=0.5, iou_threshold=0.3, model_names=None):
    """Apply custom NMS to filter overlapping detections"""
    if len(boxes) == 0:
        return []
    
    # Convert to list of dictionaries for easier handling
    detections = []
    for box in boxes:
        conf = float(box.conf.cpu().numpy()[0])
        cls = int(box.cls.cpu().numpy()[0])
        xyxy = box.xyxy.cpu().numpy()[0].tolist()
        
        # Get class name from model if available
        class_name = 'bell_pepper'
        if model_names and cls < len(model_names):
            class_name = model_names[cls]
        
        if conf >= conf_threshold:
            detections.append({
                'confidence': conf,
                'class_id': cls,
                'class_name': class_name,
                'bbox': xyxy
            })
    
    # Sort by confidence (highest first)
    detections.sort(key=lambda x: x['confidence'], reverse=True)
    
    # Apply NMS
    filtered = []
    for current in detections:
        is_duplicate = False
        for kept in filtered:
            iou = calculate_iou(current['bbox'], kept['bbox'])
            if iou > iou_threshold:
                is_duplicate = True
                break
        
        if not is_duplicate:
            filtered.append(current)
    
    return filtered

def is_bell_pepper_region(general_box, pepper_boxes, iou_threshold=0.3):
    """Check if a general detection overlaps significantly with bell pepper detections"""
    for pepper_box in pepper_boxes:
        iou = calculate_iou(general_box, pepper_box['bbox'])
        if iou > iou_threshold:
            return True
    return False

def draw_arrow_from_text_to_object(image, text_pos, object_center, color, thickness=2):
    """Draw a curved arrow from text label to object center"""
    text_x, text_y = text_pos
    obj_x, obj_y = object_center
    
    # Calculate arrow start and end points
    arrow_start = (text_x, text_y)
    arrow_end = (obj_x, obj_y)
    
    # Calculate control point for curved arrow (Bezier curve)
    control_x = (text_x + obj_x) // 2
    control_y = min(text_y, obj_y) - 30  # Curve upward
    
    # Draw curved line using multiple line segments
    points = []
    for t in range(21):  # 21 points for smooth curve
        t_norm = t / 20.0
        # Quadratic Bezier curve formula
        x = int((1-t_norm)**2 * text_x + 2*(1-t_norm)*t_norm * control_x + t_norm**2 * obj_x)
        y = int((1-t_norm)**2 * text_y + 2*(1-t_norm)*t_norm * control_y + t_norm**2 * obj_y)
        points.append((x, y))
    
    # Draw the curved line
    for i in range(len(points) - 1):
        cv2.line(image, points[i], points[i+1], color, thickness)
    
    # Draw arrowhead at the end
    import math
    # Calculate angle for arrowhead
    if len(points) >= 2:
        dx = points[-1][0] - points[-2][0]
        dy = points[-1][1] - points[-2][1]
        angle = math.atan2(dy, dx)
        
        # Arrowhead parameters
        arrow_length = 15
        arrow_angle = math.pi / 6  # 30 degrees
        
        # Calculate arrowhead points
        x1 = int(obj_x - arrow_length * math.cos(angle - arrow_angle))
        y1 = int(obj_y - arrow_length * math.sin(angle - arrow_angle))
        x2 = int(obj_x - arrow_length * math.cos(angle + arrow_angle))
        y2 = int(obj_y - arrow_length * math.sin(angle + arrow_angle))
        
        # Draw arrowhead
        cv2.line(image, (obj_x, obj_y), (x1, y1), color, thickness)
        cv2.line(image, (obj_x, obj_y), (x2, y2), color, thickness)

def create_smart_mask_from_bbox(image, bbox, padding=5):
    """Create a smart mask from bounding box using image processing"""
    x1, y1, x2, y2 = map(int, bbox)
    
    # Add padding and ensure within image bounds
    h, w = image.shape[:2]
    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(w, x2 + padding)
    y2 = min(h, y2 + padding)
    
    # Crop the region
    roi = image[y1:y2, x1:x2]
    
    if roi.size == 0:
        return np.zeros((h, w), dtype=np.uint8)
    
    # Convert to different color spaces for better segmentation
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)
    
    # Use multiple techniques to create a mask
    # 1. Edge detection
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    
    # 2. Color-based segmentation (focus on pepper colors)
    # Bell peppers are usually red, yellow, green, or orange
    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 50, 50])
    upper_red2 = np.array([180, 255, 255])
    lower_yellow = np.array([15, 50, 50])
    upper_yellow = np.array([35, 255, 255])
    lower_green = np.array([35, 30, 30])
    upper_green = np.array([85, 255, 255])
    
    # Create color masks
    mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    
    # Combine color masks
    color_mask = cv2.bitwise_or(cv2.bitwise_or(mask_red1, mask_red2), 
                               cv2.bitwise_or(mask_yellow, mask_green))
    
    # 3. Texture-based segmentation using GrabCut
    try:
        # Initialize with a rectangle slightly inside the bbox
        rect_margin = 10
        rect = (rect_margin, rect_margin, 
                roi.shape[1] - 2*rect_margin, roi.shape[0] - 2*rect_margin)
        
        if rect[2] > 0 and rect[3] > 0:
            mask_grabcut = np.zeros(roi.shape[:2], np.uint8)
            bgd_model = np.zeros((1, 65), np.float64)
            fgd_model = np.zeros((1, 65), np.float64)
            
            cv2.grabCut(roi, mask_grabcut, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
            grabcut_mask = np.where((mask_grabcut == 2) | (mask_grabcut == 0), 0, 1).astype('uint8')
        else:
            grabcut_mask = np.ones(roi.shape[:2], dtype=np.uint8)
    except:
        grabcut_mask = np.ones(roi.shape[:2], dtype=np.uint8)
    
    # Combine all masks
    combined_mask = cv2.bitwise_and(color_mask, grabcut_mask * 255)
    
    # If color-based segmentation fails, use GrabCut only
    if np.sum(combined_mask) < 100:  # Very small mask
        combined_mask = grabcut_mask * 255
    
    # Morphological operations to clean up the mask
    kernel = np.ones((3, 3), np.uint8)
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel, iterations=1)
    
    # Fill holes
    combined_mask = cv2.medianBlur(combined_mask, 5)
    
    # Create full-size mask
    full_mask = np.zeros((h, w), dtype=np.uint8)
    full_mask[y1:y2, x1:x2] = combined_mask
    
    return full_mask

def analyze_color(image_path):
    """
    Analyze the color characteristics of detected bell peppers
    """
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Define mask for bell pepper colors (green to red)
    lower_green = np.array([35, 20, 20])
    upper_green = np.array([85, 255, 255])
    lower_yellow = np.array([10, 50, 50])
    upper_yellow = np.array([25, 255, 255])
    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 50, 50])
    upper_red2 = np.array([180, 255, 255])
    
    # Create masks for different color ranges
    mask_green = cv2.inRange(image, lower_green, upper_green)
    mask_yellow = cv2.inRange(image, lower_yellow, upper_yellow)
    mask_red = cv2.inRange(image, lower_red1, upper_red1) + cv2.inRange(image, lower_red2, upper_red2)
    
    # Calculate percentage of each color
    total_pixels = mask_green.size
    green_percentage = np.sum(mask_green > 0) / total_pixels * 100
    yellow_percentage = np.sum(mask_yellow > 0) / total_pixels * 100
    red_percentage = np.sum(mask_red > 0) / total_pixels * 100
    
    # Determine ripeness stage based on color percentages
    if red_percentage > 60:
        ripeness = 'ripe'
    elif yellow_percentage > 40:
        ripeness = 'ripening'
    elif green_percentage > 70:
        ripeness = 'unripe'
    else:
        ripeness = 'unknown'
    
    return {
        'green_percentage': green_percentage,
        'yellow_percentage': yellow_percentage,
        'red_percentage': red_percentage,
        'ripeness_stage': ripeness,
        'description': BELL_PEPPER_CLASSES.get(ripeness, {}).get('description', 'Unknown stage')
    }

def detect_diseases(image_path):
    """
    Detect diseases in bell peppers using a specialized model
    """
    if MODELS['disease_detection'] is None:
        return []  # Return empty if model not available
    
    # Run inference
    results = MODELS['disease_detection'](image_path)
    result = results[0]
    
    # Extract disease information
    diseases = []
    if result.boxes is not None:
        for box in result.boxes:
            conf = float(box.conf.cpu().numpy()[0])
            cls = int(box.cls.cpu().numpy()[0])
            
            # Get class name
            class_name = result.names[cls] if hasattr(result, 'names') else str(cls)
            
            diseases.append({
                'disease': class_name,
                'confidence': conf,
                'symptoms': BELL_PEPPER_CLASSES.get(class_name, {}).get('symptoms', 'Unknown symptoms')
            })
    
    return diseases

@app.route('/')
def landing():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/health')
def health_check():
    """Health check endpoint for Docker and load balancers"""
    try:
        # Check if database is accessible
        db.session.execute('SELECT 1')
        
        # Check if models are loaded
        models_status = {
            'general_detection': MODELS['general_detection'] is not None,
            'bell_pepper_detection': MODELS['bell_pepper_detection'] is not None,
            'cv_quality_analyzer': MODELS['cv_quality_analyzer'] is not None,
            'advanced_ai_analyzer': MODELS['advanced_ai_analyzer'] is not None,
            'health_analyzer': MODELS['health_analyzer'] is not None
        }
        
        # Check if required directories exist
        import os
        dirs_exist = {
            'uploads': os.path.exists(app.config['UPLOAD_FOLDER']),
            'results': os.path.exists(app.config['RESULTS_FOLDER']),
            'instance': os.path.exists('instance')
        }
        
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'models': models_status,
            'directories': dirs_exist,
            'version': '1.0.0'
        }
        
        return jsonify(health_status), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 503

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            
            if remember:
                session.permanent = True
            
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash(f'Welcome back, {user.full_name or user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not all([username, email, password, confirm_password]):
            flash('All fields are required.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('register.html')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(username=username, email=email, full_name=full_name)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    recent_analyses = AnalysisHistory.query.filter_by(user_id=user.id).order_by(AnalysisHistory.created_at.desc()).limit(10).all()
    
    # Statistics
    total_analyses = AnalysisHistory.query.filter_by(user_id=user.id).count()
    total_peppers = db.session.query(db.func.sum(AnalysisHistory.peppers_found)).filter_by(user_id=user.id).scalar() or 0
    avg_quality = db.session.query(db.func.avg(AnalysisHistory.avg_quality)).filter_by(user_id=user.id).scalar() or 0
    
    # Quality Distribution
    excellent_count = BellPepperDetection.query.filter_by(user_id=user.id).filter(BellPepperDetection.quality_score >= 80).count()
    good_count = BellPepperDetection.query.filter_by(user_id=user.id).filter(BellPepperDetection.quality_score >= 60, BellPepperDetection.quality_score < 80).count()
    fair_count = BellPepperDetection.query.filter_by(user_id=user.id).filter(BellPepperDetection.quality_score >= 40, BellPepperDetection.quality_score < 60).count()
    poor_count = BellPepperDetection.query.filter_by(user_id=user.id).filter(BellPepperDetection.quality_score < 40).count()
    
    # Variety Distribution (top 5)
    variety_stats = db.session.query(
        BellPepperDetection.variety,
        db.func.count(BellPepperDetection.id).label('count')
    ).filter_by(user_id=user.id).group_by(BellPepperDetection.variety).order_by(db.func.count(BellPepperDetection.id).desc()).limit(5).all()
    
    # Recent activity chart (last 7 days)
    from datetime import datetime, timedelta
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_peppers = BellPepperDetection.query.filter_by(user_id=user.id).filter(BellPepperDetection.created_at >= seven_days_ago).all()
    
    # Group by date
    daily_counts = {}
    for pepper in recent_peppers:
        date_key = pepper.created_at.strftime('%Y-%m-%d')
        if date_key not in daily_counts:
            daily_counts[date_key] = 0
        daily_counts[date_key] += 1
    
    # Fill in missing dates with 0
    activity_data = []
    for i in range(7):
        date = (datetime.utcnow() - timedelta(days=6-i)).strftime('%Y-%m-%d')
        activity_data.append({
            'date': date,
            'count': daily_counts.get(date, 0)
        })
    
    return render_template('dashboard.html', 
                         user=user, 
                         recent_analyses=recent_analyses,
                         total_analyses=total_analyses,
                         total_peppers=total_peppers,
                         avg_quality=round(avg_quality, 1),
                         excellent_count=excellent_count,
                         good_count=good_count,
                         fair_count=fair_count,
                         poor_count=poor_count,
                         variety_stats=variety_stats,
                         activity_data=activity_data)

@app.route('/profile')
@login_required
def profile():
    user = User.query.get(session['user_id'])
    
    # Get user statistics
    total_analyses = AnalysisHistory.query.filter_by(user_id=user.id).count()
    total_peppers = db.session.query(db.func.sum(AnalysisHistory.peppers_found)).filter_by(user_id=user.id).scalar() or 0
    avg_quality = db.session.query(db.func.avg(AnalysisHistory.avg_quality)).filter_by(user_id=user.id).scalar() or 0
    
    # Get recent activity (last 20 analyses)
    recent_activity = AnalysisHistory.query.filter_by(user_id=user.id)\
        .order_by(AnalysisHistory.created_at.desc())\
        .limit(20)\
        .all()
    
    # Get activity stats by date (last 30 days)
    from datetime import timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_analyses_count = AnalysisHistory.query.filter(
        AnalysisHistory.user_id == user.id,
        AnalysisHistory.created_at >= thirty_days_ago
    ).count()
    
    # Get quality distribution for user's peppers
    quality_distribution = db.session.query(
        BellPepperDetection.quality_category,
        db.func.count(BellPepperDetection.id)
    ).filter_by(user_id=user.id)\
     .group_by(BellPepperDetection.quality_category)\
     .all()
    
    quality_stats = {category: count for category, count in quality_distribution}
    
    return render_template('profile.html',
                         user=user,
                         total_analyses=total_analyses,
                         total_peppers=total_peppers,
                         avg_quality=round(avg_quality, 1),
                         recent_activity=recent_activity,
                         recent_analyses_count=recent_analyses_count,
                         quality_stats=quality_stats)

@app.route('/analyze')
@login_required
def analyze():
    return render_template('index.html')

@app.route('/static/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

@app.route('/static/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/json')

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    # Accepts multipart/form-data with 'image' field
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']
    if not file:
        return jsonify({'error': 'No selected file'}), 400

    # Handle both file uploads and camera captures (blobs)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S%f')
    
    # Get file extension, default to jpg if not present (for camera captures)
    if file.filename and '.' in file.filename:
        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext not in app.config['ALLOWED_EXTENSIONS']:
            return jsonify({'error': 'Invalid file type'}), 400
    else:
        # Default to jpg for camera captures/blobs
        ext = 'jpg'
    
    filename = f'img_{timestamp}.{ext}'
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        file.save(filepath)

        # Multi-stage detection: General + Specialized + ANFIS
        try:
            detection_results = {
                'general_objects': [],
                'bell_peppers': [],
                'quality_analysis': []
            }
            
            # Stage 1: General object detection (80 COCO classes) - collect all first
            general_detections = []
            if MODELS['general_detection']:
                general_results = MODELS['general_detection'](filepath)
                general_result = general_results[0]
                
                if general_result.boxes is not None:
                    for box in general_result.boxes:
                        conf = float(box.conf.cpu().numpy()[0])
                        cls = int(box.cls.cpu().numpy()[0])
                        class_name = general_result.names[cls]
                        xyxy = box.xyxy.cpu().numpy()[0].tolist()
                        
                        general_detections.append({
                            'class_name': class_name,
                            'confidence': conf,
                            'bbox': xyxy,
                            'class_id': cls
                        })
            
            # Stage 2: Specialized bell pepper detection with smart filtering
            bell_peppers_detected = False
            if MODELS['bell_pepper_detection']:
                pepper_results = MODELS['bell_pepper_detection'](filepath, conf=0.3, iou=0.5)  # Lower conf, higher IOU for better NMS
                pepper_result = pepper_results[0]
                
                if pepper_result.boxes is not None:
                    image = cv2.imread(filepath)
                    
                    # Apply additional NMS and filtering
                    model_names = pepper_result.names if hasattr(pepper_result, 'names') else None
                    filtered_peppers = filter_overlapping_detections(
                        pepper_result.boxes, 
                        conf_threshold=0.5, 
                        iou_threshold=0.3,
                        model_names=model_names
                    )
                    
                    for i, box_data in enumerate(filtered_peppers):
                        conf = box_data['confidence']
                        cls = box_data['class_id']
                        class_name = box_data['class_name']
                        xyxy = box_data['bbox']
                        
                        bell_peppers_detected = True
                        
                        bell_pepper_data = {
                            'variety': class_name,
                            'confidence': conf,
                            'bbox': xyxy,
                            'class_id': cls,
                            'pepper_id': f'pepper_{i+1}'
                        }
                        
                        # Stage 3: Advanced Quality Analysis + Save Cropped Image
                        # Crop the bell pepper region with padding
                        x1, y1, x2, y2 = map(int, xyxy)
                        
                        # Add padding to avoid edge effects and show more context
                        h, w = image.shape[:2]
                        pad = 35  # Increased padding for better context visibility
                        x1 = max(0, x1 - pad)
                        y1 = max(0, y1 - pad)
                        x2 = min(w, x2 + pad)
                        y2 = min(h, y2 + pad)
                        
                        pepper_crop = image[y1:y2, x1:x2]
                        
                        if pepper_crop.size > 0:
                            # Save cropped pepper image
                            crop_name = f'crop_{timestamp}_{i+1}.jpg'
                            crop_path = os.path.join(app.config['RESULTS_FOLDER'], crop_name)
                            cv2.imwrite(crop_path, pepper_crop, [cv2.IMWRITE_JPEG_QUALITY, 95])
                            
                            # Run advanced quality analysis using OpenCV + scikit-image
                            quality_analysis = None
                            if MODELS['cv_quality_analyzer']:
                                try:
                                    # Use the advanced computer vision analyzer
                                    metrics = MODELS['cv_quality_analyzer'].analyze_pepper_quality(pepper_crop)
                                    recommendations = MODELS['cv_quality_analyzer'].get_quality_recommendations(metrics)
                                    
                                    # Determine quality category based on overall score
                                    overall_score = metrics['overall_quality']
                                    if overall_score >= 80:
                                        quality_category = "Excellent"
                                    elif overall_score >= 60:
                                        quality_category = "Good"
                                    elif overall_score >= 40:
                                        quality_category = "Fair"
                                    else:
                                        quality_category = "Poor"
                                    
                                    quality_analysis = {
                                        'quality_score': overall_score,
                                        'quality_category': quality_category,
                                        'color_uniformity': metrics['color_uniformity'],
                                        'size_consistency': metrics['size_consistency'],
                                        'surface_quality': metrics['surface_quality'],
                                        'ripeness_level': metrics['ripeness_level'],
                                        'recommendations': recommendations
                                    }
                                except Exception as e:
                                    print(f"CV Quality Analysis error: {e}")
                                    quality_analysis = None
                            
                            # Fallback to ANFIS if CV analyzer fails
                            if quality_analysis is None and MODELS['anfis_quality']:
                                try:
                                    quality_analysis = MODELS['anfis_quality'].analyze_pepper_image(pepper_crop)
                                except Exception as e:
                                    print(f"ANFIS Quality Analysis error: {e}")
                                    quality_analysis = {
                                        'quality_score': 50.0,
                                        'quality_category': "Unknown",
                                        'color_uniformity': 50.0,
                                        'size_consistency': 50.0,
                                        'surface_quality': 50.0,
                                        'ripeness_level': 50.0,
                                        'recommendations': ["Unable to analyze quality"]
                                    }
                            
                            # Stage 3C: Advanced AI Analysis (Ripeness, Shelf Life, Nutrition, Variety)
                            if MODELS['advanced_ai_analyzer'] and quality_analysis:
                                try:
                                    # Convert quality_analysis to metrics format for advanced analyzer
                                    metrics = {
                                        'overall_quality': quality_analysis['quality_score'],
                                        'color_uniformity': quality_analysis['color_uniformity'],
                                        'size_consistency': quality_analysis['size_consistency'],
                                        'surface_quality': quality_analysis['surface_quality'],
                                        'ripeness_level': quality_analysis['ripeness_level']
                                    }
                                    
                                    # Get comprehensive advanced analysis
                                    advanced_features = MODELS['advanced_ai_analyzer'].analyze_advanced_features(
                                        pepper_crop, metrics
                                    )
                                    
                                    # Add advanced analysis to pepper data
                                    bell_pepper_data['advanced_analysis'] = advanced_features
                                    bell_pepper_data['ripeness_prediction'] = advanced_features.get('ripeness_prediction')
                                    bell_pepper_data['shelf_life'] = advanced_features.get('shelf_life_estimation')
                                    bell_pepper_data['nutrition'] = advanced_features.get('nutritional_analysis')
                                    bell_pepper_data['variety'] = advanced_features.get('variety_classification', {}).get('predicted_variety', class_name)
                                    bell_pepper_data['market_analysis'] = advanced_features.get('market_analysis')
                                    
                                    # Enhanced recommendations combining all analyses
                                    enhanced_recommendations = advanced_features.get('advanced_recommendations', [])
                                    quality_analysis['recommendations'].extend(enhanced_recommendations)
                                    
                                    print(f"✅ Advanced AI analysis for pepper {i+1}: {advanced_features.get('variety_classification', {}).get('predicted_variety', 'unknown')} variety")
                                    
                                except Exception as e:
                                    print(f"Advanced AI analysis error: {e}")
                                    bell_pepper_data['advanced_analysis'] = {'error': str(e)}
                            
                            bell_pepper_data['quality_analysis'] = quality_analysis
                            bell_pepper_data['crop_url'] = f'/results/{crop_name}'
                        
                        detection_results['bell_peppers'].append(bell_pepper_data)
            
            # Stage 3: Filter general objects to remove bell pepper regions (avoid duplicates)
            for general_obj in general_detections:
                # Only add general objects that don't significantly overlap with bell peppers
                if not is_bell_pepper_region(general_obj['bbox'], detection_results['bell_peppers']):
                    detection_results['general_objects'].append(general_obj)
            
            # Create annotated image
            image = cv2.imread(filepath)
            annotated_image = image.copy()
            
            # No colored overlays needed - using arrows only
            # overlay = np.zeros_like(annotated_image, dtype=np.uint8)
            
            # Process general objects with segmentation masks
            if hasattr(general_result, 'masks') and general_result.masks is not None:
                for i, obj in enumerate(detection_results['general_objects']):
                    if obj['confidence'] > 0.5 and i < len(general_result.masks.data):
                        # Get the segmentation mask
                        mask = general_result.masks.data[i].cpu().numpy()
                        
                        # Resize mask to match image dimensions
                        mask_resized = cv2.resize(mask, (annotated_image.shape[1], annotated_image.shape[0]))
                        mask_binary = (mask_resized > 0.5).astype(np.uint8)
                        
                        # No colored overlay - just use mask for center calculation
                        
                        # Calculate object center and place label with arrow
                        y_coords, x_coords = np.where(mask_binary == 1)
                        if len(y_coords) > 0:
                            # Calculate center of the object
                            obj_center_x = int(np.mean(x_coords))
                            obj_center_y = int(np.mean(y_coords))
                            
                            # Position label away from object
                            label = f"{obj['class_name']}: {obj['confidence']:.2f}"
                            # High-quality font rendering with anti-aliasing
                            font_scale = 0.8
                            font_thickness = 2
                            font = cv2.FONT_HERSHEY_DUPLEX  # Better font for readability
                            label_size = cv2.getTextSize(label, font, font_scale, font_thickness)[0]
                            
                            # Smart label positioning to avoid overlap
                            label_x = max(10, obj_center_x - 150)
                            label_y = max(30, obj_center_y - 80)
                            
                            # Ensure label stays within image bounds
                            if label_x + label_size[0] > annotated_image.shape[1] - 10:
                                label_x = annotated_image.shape[1] - label_size[0] - 10
                            
                            # Draw label background
                            cv2.rectangle(annotated_image, (label_x - 4, label_y - 20), 
                                        (label_x + label_size[0] + 8, label_y + 5), (255, 100, 50), -1)
                            cv2.putText(annotated_image, label, (label_x, label_y), 
                                       font, font_scale, (255, 255, 255), font_thickness, cv2.LINE_AA)
                            
                            # Draw arrow from label to object center
                            draw_arrow_from_text_to_object(annotated_image, 
                                                         (label_x + label_size[0]//2, label_y + 5),
                                                         (obj_center_x, obj_center_y),
                                                         (255, 100, 50), 2)
            else:
                # Fallback to bounding boxes if no masks available
                for obj in detection_results['general_objects']:
                    if obj['confidence'] > 0.5:
                        x1, y1, x2, y2 = map(int, obj['bbox'])
                        # No colored overlay - just calculate center for arrow
                        
                        # Calculate object center for arrow
                        obj_center_x = (x1 + x2) // 2
                        obj_center_y = (y1 + y2) // 2
                        
                        # Position label with smart placement
                        label = f"{obj['class_name']}: {obj['confidence']:.2f}"
                        # High-quality font rendering with anti-aliasing
                        font_scale = 0.8
                        font_thickness = 2
                        font = cv2.FONT_HERSHEY_DUPLEX  # Better font for readability
                        label_size = cv2.getTextSize(label, font, font_scale, font_thickness)[0]
                        
                        label_x = max(10, obj_center_x - 150)
                        label_y = max(30, obj_center_y - 80)
                        
                        if label_x + label_size[0] > annotated_image.shape[1] - 10:
                            label_x = annotated_image.shape[1] - label_size[0] - 10
                        
                        # Draw label with background
                        cv2.rectangle(annotated_image, (label_x - 4, label_y - 20), 
                                    (label_x + label_size[0] + 8, label_y + 5), (255, 100, 50), -1)
                        cv2.putText(annotated_image, label, (label_x, label_y), 
                                   font, font_scale, (255, 255, 255), font_thickness, cv2.LINE_AA)
                        
                        # Draw arrow to object center
                        draw_arrow_from_text_to_object(annotated_image, 
                                                     (label_x + label_size[0]//2, label_y + 5),
                                                     (obj_center_x, obj_center_y),
                                                     (255, 100, 50), 2)
            
            # Process bell peppers with smart masking (works for both detection and segmentation models)
            for i, pepper in enumerate(detection_results['bell_peppers']):
                # Check if we have segmentation masks first
                if hasattr(pepper_result, 'masks') and pepper_result.masks is not None and i < len(pepper_result.masks.data):
                    # Use true segmentation mask
                    mask = pepper_result.masks.data[i].cpu().numpy()
                    mask_resized = cv2.resize(mask, (annotated_image.shape[1], annotated_image.shape[0]))
                    mask_binary = (mask_resized > 0.5).astype(np.uint8)
                else:
                    # Create smart mask from bounding box using computer vision
                    print(f"🎯 Creating smart mask for bell pepper {i+1}")
                    mask_binary = create_smart_mask_from_bbox(annotated_image, pepper['bbox'])
                
                # Choose arrow color based on quality
                pepper_color = [50, 100, 255]  # Default red-orange
                if 'quality_analysis' in pepper:
                    quality_score = pepper['quality_analysis']['quality_score']
                    if quality_score >= 80:
                        pepper_color = [50, 200, 50]   # Green for excellent
                    elif quality_score >= 60:
                        pepper_color = [50, 150, 255]  # Orange for good
                    elif quality_score >= 40:
                        pepper_color = [50, 100, 200]  # Yellow-orange for fair
                    else:
                        pepper_color = [50, 50, 255]   # Red for poor
                
                # No colored overlay - just use color for arrow and label
                
                # Calculate object center and place label with arrow
                y_coords, x_coords = np.where(mask_binary == 1)
                if len(y_coords) > 0:
                    # Calculate center of the bell pepper
                    obj_center_x = int(np.mean(x_coords))
                    obj_center_y = int(np.mean(y_coords))
                    
                    # Create comprehensive label
                    label = f"{pepper['variety']}: {pepper['confidence']:.2f}"
                    if 'quality_analysis' in pepper:
                        quality = pepper['quality_analysis']['quality_category']
                        score = pepper['quality_analysis']['quality_score']
                        label += f" | {quality} ({score:.0f})"
                    
                    # High-quality font rendering with anti-aliasing for bell peppers
                    font_scale = 0.9
                    font_thickness = 2
                    font = cv2.FONT_HERSHEY_DUPLEX  # Better font for readability
                    label_size = cv2.getTextSize(label, font, font_scale, font_thickness)[0]
                    
                    # Smart label positioning to avoid overlap
                    label_x = max(10, obj_center_x - 200)
                    label_y = max(35, obj_center_y - 100)
                    
                    # Ensure label stays within image bounds
                    if label_x + label_size[0] > annotated_image.shape[1] - 10:
                        label_x = annotated_image.shape[1] - label_size[0] - 10
                    if label_y < 35:
                        label_y = obj_center_y + 100
                    
                    # Draw label background with pepper color
                    cv2.rectangle(annotated_image, (label_x - 6, label_y - 25), 
                                (label_x + label_size[0] + 12, label_y + 8), pepper_color, -1)
                    cv2.putText(annotated_image, label, (label_x + 3, label_y), 
                               font, font_scale, (255, 255, 255), font_thickness, cv2.LINE_AA)
                    
                    # Draw curved arrow from label to bell pepper center
                    draw_arrow_from_text_to_object(annotated_image, 
                                                 (label_x + label_size[0]//2, label_y + 8),
                                                 (obj_center_x, obj_center_y),
                                                 pepper_color, 3)
                else:
                    # Fallback to bounding box label if mask creation failed
                    x1, y1, x2, y2 = map(int, pepper['bbox'])
                    obj_center_x = (x1 + x2) // 2
                    obj_center_y = (y1 + y2) // 2
                    
                    label = f"{pepper['variety']}: {pepper['confidence']:.2f}"
                    if 'quality_analysis' in pepper:
                        quality = pepper['quality_analysis']['quality_category']
                        score = pepper['quality_analysis']['quality_score']
                        label += f" | {quality} ({score:.0f})"
                    
                    # High-quality font rendering with anti-aliasing for bell peppers (fallback)
                    font_scale = 0.9
                    font_thickness = 2
                    font = cv2.FONT_HERSHEY_DUPLEX  # Better font for readability
                    label_size = cv2.getTextSize(label, font, font_scale, font_thickness)[0]
                    
                    # Smart positioning
                    label_x = max(10, obj_center_x - 200)
                    label_y = max(35, obj_center_y - 100)
                    
                    if label_x + label_size[0] > annotated_image.shape[1] - 10:
                        label_x = annotated_image.shape[1] - label_size[0] - 10
                    
                    # Choose color for fallback
                    fallback_color = [50, 100, 255]  # Default red-orange
                    if 'quality_analysis' in pepper:
                        quality_score = pepper['quality_analysis']['quality_score']
                        if quality_score >= 80:
                            fallback_color = [50, 200, 50]   # Green for excellent
                        elif quality_score >= 60:
                            fallback_color = [50, 150, 255]  # Orange for good
                        elif quality_score >= 40:
                            fallback_color = [50, 100, 200]  # Yellow-orange for fair
                        else:
                            fallback_color = [50, 50, 255]   # Red for poor
                    
                    # Draw label background
                    cv2.rectangle(annotated_image, (label_x - 6, label_y - 25), 
                                (label_x + label_size[0] + 12, label_y + 8), fallback_color, -1)
                    cv2.putText(annotated_image, label, (label_x + 3, label_y), 
                               font, font_scale, (255, 255, 255), font_thickness, cv2.LINE_AA)
                    
                    # Draw arrow to object center
                    draw_arrow_from_text_to_object(annotated_image, 
                                                 (label_x + label_size[0]//2, label_y + 8),
                                                 (obj_center_x, obj_center_y),
                                                 fallback_color, 3)
            
            # No overlay blending needed - using arrows only
            annotated_bgr = annotated_image

            out_name = f'res_{timestamp}.jpg'
            out_path = os.path.join(app.config['RESULTS_FOLDER'], out_name)
            
            # Save with high quality (95% JPEG quality)
            cv2.imwrite(out_path, annotated_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])

            # Save analysis to history
            import json
            avg_quality = np.mean([p.get('quality_analysis', {}).get('quality_score', 0) 
                                 for p in detection_results['bell_peppers']]) if detection_results['bell_peppers'] else 0
            
            analysis = AnalysisHistory(
                user_id=session['user_id'],
                image_path=filepath,
                result_path=out_path,
                peppers_found=len(detection_results['bell_peppers']),
                avg_quality=float(avg_quality),
                analysis_data=json.dumps(detection_results['bell_peppers'][:3])  # Store first 3 peppers summary
            )
            db.session.add(analysis)
            db.session.flush()  # Get analysis.id before saving peppers
            
            # Save each individual bell pepper detection to database
            for pepper_data in detection_results['bell_peppers']:
                qa = pepper_data.get('quality_analysis', {})
                
                # Extract crop filename from crop_url
                crop_filename = None
                if pepper_data.get('crop_url'):
                    crop_filename = pepper_data['crop_url'].replace('/results/', '')
                
                pepper_detection = BellPepperDetection(
                    analysis_id=analysis.id,
                    user_id=session['user_id'],
                    pepper_id=pepper_data.get('pepper_id', 'unknown'),
                    variety=pepper_data.get('variety', 'Bell Pepper'),
                    confidence=float(pepper_data.get('confidence', 0)),
                    crop_path=crop_filename,
                    quality_score=float(qa.get('quality_score', 0)),
                    quality_category=qa.get('quality_category', 'Unknown'),
                    color_uniformity=float(qa.get('color_uniformity', 0)),
                    size_consistency=float(qa.get('size_consistency', 0)),
                    surface_quality=float(qa.get('surface_quality', 0)),
                    ripeness_level=float(qa.get('ripeness_level', 0)),
                    advanced_analysis=json.dumps(pepper_data.get('advanced_analysis', {})),
                    disease_analysis=json.dumps(pepper_data.get('disease_analysis', {})),
                    recommendations=json.dumps(qa.get('recommendations', [])),
                    health_status=pepper_data.get('health_status', 'Unknown'),
                    overall_health_score=float(pepper_data.get('overall_health_score', 0))
                )
                db.session.add(pepper_detection)
            
            db.session.commit()
            print(f"✅ Saved {len(detection_results['bell_peppers'])} peppers to database")
            
            # Prepare multi-model response
            response_data = {
                'result_url': f'/results/{out_name}',
                'general_objects': detection_results['general_objects'],
                'bell_peppers': detection_results['bell_peppers'],
                'summary': {
                    'total_objects': len(detection_results['general_objects']),
                    'bell_peppers_found': len(detection_results['bell_peppers']),
                    'avg_quality_score': avg_quality
                },
                'message': f"Found {len(detection_results['general_objects'])} objects, {len(detection_results['bell_peppers'])} bell peppers"
            }
            
            return jsonify(response_data)

        except Exception as e:
            print(f"Processing error: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Processing error: {str(e)}'}), 500
    
    except Exception as e:
        print(f"File save error: {str(e)}")
        return jsonify({'error': f'Error saving file: {str(e)}'}), 500

@app.route('/results/<filename>')
def serve_result(filename):
    return send_from_directory(app.config['RESULTS_FOLDER'], filename)

@app.route('/uploads/<filename>')
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/search')
@login_required
def search():
    """
    Comprehensive search across the entire database
    Searches: Users, Analysis History, Bell Pepper Detections, Pepper Types, Diseases, Varieties
    """
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'results': [], 'message': 'Search query must be at least 2 characters long'})
    
    results = {
        'analyses': [],
        'peppers': [],
        'varieties': [],
        'diseases': [],
        'users': [],
        'total_count': 0
    }
    
    try:
        user_id = session.get('user_id')
        user_role = session.get('role', 'user')
        
        # Search Analysis History (accessible to current user only, or all for admins)
        if user_role == 'admin':
            analyses_query = AnalysisHistory.query
        else:
            analyses_query = AnalysisHistory.query.filter_by(user_id=user_id)
        
        analyses = analyses_query.join(User, AnalysisHistory.user_id == User.id).filter(
            db.or_(
                AnalysisHistory.analysis_data.contains(query),
                User.username.contains(query),
                User.full_name.contains(query)
            )
        ).order_by(AnalysisHistory.created_at.desc()).limit(20).all()
        
        for analysis in analyses:
            results['analyses'].append({
                'id': analysis.id,
                'type': 'analysis',
                'title': f'Analysis #{analysis.id}',
                'description': f'{analysis.peppers_found} peppers found, avg quality: {analysis.avg_quality:.1f}',
                'user': analysis.user.full_name or analysis.user.username,
                'date': analysis.created_at.strftime('%Y-%m-%d %H:%M'),
                'url': f'/history#analysis-{analysis.id}',
                'scroll_target': f'analysis-{analysis.id}',
                'metadata': {
                    'peppers_found': analysis.peppers_found,
                    'avg_quality': analysis.avg_quality,
                    'image_path': analysis.image_path
                }
            })
        
        # Search Bell Pepper Detections (accessible to current user only, or all for admins)
        if user_role == 'admin':
            peppers_query = BellPepperDetection.query
        else:
            peppers_query = BellPepperDetection.query.filter_by(user_id=user_id)
            
        peppers = peppers_query.filter(
            db.or_(
                BellPepperDetection.variety.contains(query),
                BellPepperDetection.quality_category.contains(query),
                BellPepperDetection.health_status.contains(query),
                BellPepperDetection.pepper_id.contains(query)
            )
        ).order_by(BellPepperDetection.created_at.desc()).limit(20).all()
        
        for pepper in peppers:
            results['peppers'].append({
                'id': pepper.id,
                'type': 'pepper',
                'title': f'{pepper.variety} - {pepper.pepper_id}',
                'description': f'Quality: {pepper.quality_category} ({pepper.quality_score:.1f}/100)',
                'health': pepper.health_status,
                'date': pepper.created_at.strftime('%Y-%m-%d %H:%M'),
                'url': f'/history#pepper-{pepper.id}',
                'scroll_target': f'pepper-{pepper.id}',
                'metadata': {
                    'variety': pepper.variety,
                    'quality_score': pepper.quality_score,
                    'quality_category': pepper.quality_category,
                    'confidence': pepper.confidence,
                    'crop_url': f'/results/{pepper.crop_path}' if pepper.crop_path else None
                }
            })
        
        # Search Pepper Varieties (accessible to all authenticated users)
        varieties = PepperVariety.query.filter(
            db.or_(
                PepperVariety.name.contains(query),
                PepperVariety.description.contains(query),
                PepperVariety.characteristics.contains(query)
            )
        ).limit(15).all()
        
        for variety in varieties:
            results['varieties'].append({
                'id': variety.id,
                'type': 'variety',
                'title': variety.name,
                'description': variety.description or 'Bell pepper variety information',
                'color': variety.color,
                'date': variety.created_at.strftime('%Y-%m-%d') if variety.created_at else None,
                'url': f'/pepper-database#variety-{variety.id}',
                'scroll_target': f'variety-{variety.id}',
                'metadata': {
                    'type_id': variety.type_id,
                    'storage': variety.storage,
                    'nutritional_highlights': variety.nutritional_highlights
                }
            })
        
        # Search Pepper Diseases (accessible to all authenticated users)
        diseases = PepperDisease.query.filter(
            db.or_(
                PepperDisease.name.contains(query),
                PepperDisease.scientific_name.contains(query),
                PepperDisease.description.contains(query),
                PepperDisease.symptoms.contains(query),
                PepperDisease.treatment.contains(query)
            )
        ).limit(15).all()
        
        for disease in diseases:
            results['diseases'].append({
                'id': disease.id,
                'type': 'disease',
                'title': disease.name,
                'description': disease.description or 'Disease information',
                'severity': disease.severity,
                'affected_parts': disease.affected_parts,
                'date': disease.created_at.strftime('%Y-%m-%d') if disease.created_at else None,
                'url': f'/pepper-database#disease-{disease.id}',
                'scroll_target': f'disease-{disease.id}',
                'metadata': {
                    'scientific_name': disease.scientific_name,
                    'color': disease.color,
                    'icon': disease.icon
                }
            })
        
        # Search Users (admin only)
        if user_role == 'admin':
            users = User.query.filter(
                db.or_(
                    User.username.contains(query),
                    User.email.contains(query),
                    User.full_name.contains(query)
                )
            ).filter(User.id != user_id).limit(10).all()  # Exclude current user
            
            for user in users:
                # Get user stats
                total_analyses = AnalysisHistory.query.filter_by(user_id=user.id).count()
                total_peppers = db.session.query(db.func.sum(AnalysisHistory.peppers_found)).filter_by(user_id=user.id).scalar() or 0
                
                results['users'].append({
                    'id': user.id,
                    'type': 'user',
                    'title': user.full_name or user.username,
                    'description': f'{user.email} - {total_analyses} analyses, {total_peppers} peppers',
                    'role': user.role,
                    'last_login': user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never',
                    'date': user.created_at.strftime('%Y-%m-%d') if user.created_at else None,
                    'url': f'/users#user-{user.id}',
                    'scroll_target': f'user-{user.id}',
                    'metadata': {
                        'username': user.username,
                        'email': user.email,
                        'total_analyses': total_analyses,
                        'total_peppers': total_peppers
                    }
                })
        
        # Calculate total count
        results['total_count'] = (
            len(results['analyses']) + 
            len(results['peppers']) + 
            len(results['varieties']) + 
            len(results['diseases']) + 
            len(results['users'])
        )
        
        # Create summary message
        if results['total_count'] == 0:
            message = f'No results found for "{query}"'
        else:
            message = f'Found {results["total_count"]} results for "{query}"'
            
        results['message'] = message
        results['query'] = query
        
        return jsonify(results)
        
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({'error': 'Search failed', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)