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

# Load environment variables from .env file (for local development)
from dotenv import load_dotenv
load_dotenv()

# Import models from separate file
from models import db, User, AnalysisHistory, BellPepperDetection, PepperVariety, PepperDisease, PepperType, Notification, NotificationAttachment, NotificationRead
from sqlalchemy import text

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

# Resolve absolute base paths to avoid SQLite path issues
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
DEFAULT_DB_PATH = os.path.join(INSTANCE_DIR, 'pepperai.db')

# Ensure instance directory exists before DB init
os.makedirs(INSTANCE_DIR, exist_ok=True)

# Configuration from environment variables with safe absolute fallbacks
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Resolve DATABASE_URL, forcing sqlite paths to absolute if provided relative
env_db_url = os.getenv('DATABASE_URL')
if env_db_url and env_db_url.startswith('sqlite:///'):
    _path = env_db_url.replace('sqlite:///', '', 1)
    if not os.path.isabs(_path):
        _path = os.path.join(BASE_DIR, _path)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{_path}'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = env_db_url or f'sqlite:///{DEFAULT_DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
_upload_env = os.getenv('UPLOAD_FOLDER', os.path.join(BASE_DIR, 'uploads'))
_results_env = os.getenv('RESULTS_FOLDER', os.path.join(BASE_DIR, 'results'))
app.config['UPLOAD_FOLDER'] = _upload_env if os.path.isabs(_upload_env) else os.path.join(BASE_DIR, _upload_env)
app.config['RESULTS_FOLDER'] = _results_env if os.path.isabs(_results_env) else os.path.join(BASE_DIR, _results_env)
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))  # 16MB default
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# Redis configuration (for Docker environment)
app.config['REDIS_URL'] = os.getenv('REDIS_URL', None)

# Flask environment settings
app.config['ENV'] = os.getenv('FLASK_ENV', 'development')
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', '0') == '1'

# Print configuration info on startup (hide sensitive data)
print("\n" + "="*60)
print("🔧 PepperAI Configuration Loaded")
print("="*60)
print(f"📍 Environment: {app.config['ENV']}")
print(f"🐛 Debug Mode: {app.config['DEBUG']}")
print(f"🗄️  Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
print(f"📁 Upload Folder: {app.config['UPLOAD_FOLDER']}")
print(f"📊 Results Folder: {app.config['RESULTS_FOLDER']}")
print(f"📦 Max Upload Size: {app.config['MAX_CONTENT_LENGTH'] / (1024*1024):.1f}MB")
print(f"🔴 Redis: {app.config['REDIS_URL'] if app.config['REDIS_URL'] else 'Not configured'}")
print(f"🔑 Secret Key: {'Set (secured)' if app.config['SECRET_KEY'] != 'dev-secret-key-change-in-production' else '⚠️  Using default (INSECURE!)'}")
print("="*60 + "\n")

# Initialize database with app
db.init_app(app)

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)
os.makedirs('instance', exist_ok=True)

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

# Import enhanced validation pipeline
from validation_pipeline import get_validation_pipeline

# Multi-Model Setup: General YOLOv8 + Specialized Bell Pepper + Advanced Quality Analysis + Disease Detection + AI Features
MODELS = {
    'general_detection': None,      # YOLOv8 general (80 classes)
    'bell_pepper_detection': None,  # Your trained bell pepper model
    'anfis_quality': None,         # ANFIS quality assessment system
    'cv_quality_analyzer': None,   # OpenCV + scikit-image quality analyzer
    'health_analyzer': None,       # Disease detection + health analysis
    'advanced_ai_analyzer': None,  # Advanced AI features (ripeness, shelf life, nutrition)
    'validation_pipeline': None    # Enhanced multi-layer validation pipeline
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

# Initialize Enhanced Validation Pipeline
try:
    MODELS['validation_pipeline'] = get_validation_pipeline()
    print("✅ Enhanced Validation Pipeline loaded (multi-layer validation with pre-trained classifier)")
except Exception as e:
    print(f"❌ Failed to initialize Validation Pipeline: {e}")
    MODELS['validation_pipeline'] = None

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

def validate_pepper_color(crop_image):
    """Check if crop has pepper-like colors (HSV filter) and reject skin tones"""
    hsv = cv2.cvtColor(crop_image, cv2.COLOR_BGR2HSV)
    
    # First, check for skin tones and reject them
    # Skin tone range in HSV (covers various skin colors)
    lower_skin = np.array([0, 10, 60])
    upper_skin = np.array([25, 150, 255])
    skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)
    skin_percentage = (np.sum(skin_mask > 0) / (crop_image.shape[0] * crop_image.shape[1])) * 100
    
    # If more than 30% is skin-colored, reject it
    if skin_percentage > 30:
        print(f"  └─ Rejected: {skin_percentage:.1f}% skin tone detected")
        return False
    
    # Pepper color ranges: red, yellow, orange, green (more saturated than skin)
    lower_red1 = np.array([0, 80, 80])  # Increased saturation from 50 to 80
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 80, 80])  # Increased saturation
    upper_red2 = np.array([180, 255, 255])
    lower_yellow = np.array([20, 100, 100])  # Increased saturation and hue
    upper_yellow = np.array([35, 255, 255])
    lower_green = np.array([35, 50, 50])  # Keep green sensitive
    upper_green = np.array([85, 255, 255])
    lower_orange = np.array([10, 100, 100])  # Increased saturation
    upper_orange = np.array([20, 255, 255])
    
    # Create masks
    mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    mask_orange = cv2.inRange(hsv, lower_orange, upper_orange)
    
    # Combine all pepper color masks
    combined_mask = cv2.bitwise_or(cv2.bitwise_or(mask_red1, mask_red2),
                                   cv2.bitwise_or(cv2.bitwise_or(mask_yellow, mask_green), mask_orange))
    
    # Calculate percentage of pepper-colored pixels
    total_pixels = crop_image.shape[0] * crop_image.shape[1]
    pepper_pixels = np.sum(combined_mask > 0)
    pepper_percentage = (pepper_pixels / total_pixels) * 100
    
    # Require at least 50% pepper-colored pixels (increased from 40%)
    is_valid = pepper_percentage >= 50.0
    if not is_valid:
        print(f"  └─ Rejected: Only {pepper_percentage:.1f}% pepper-colored pixels")
    return is_valid

def validate_pepper_texture(crop_image):
    """Analyze texture and contour to detect bell pepper's characteristic wavy/lobed shape"""
    if crop_image.size == 0:
        return False
    
    # Convert to grayscale for texture analysis
    gray = cv2.cvtColor(crop_image, cv2.COLOR_BGR2GRAY)
    
    # 1. Edge detection to find contours (peppers have distinct lobes)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        print(f"  └─ Rejected: No clear contours detected")
        return False
    
    # Get the largest contour
    largest_contour = max(contours, key=cv2.contourArea)
    
    # 2. Analyze contour complexity (peppers have wavy edges, apples are smooth circles)
    perimeter = cv2.arcLength(largest_contour, True)
    area = cv2.contourArea(largest_contour)
    
    if area < 100:  # Too small to analyze
        return True  # Give benefit of doubt for small crops
    
    # Circularity: 4π × area / perimeter²
    # Perfect circle = 1.0, irregular shapes < 0.8
    # Peppers are typically 0.5-0.8, apples 0.85-1.0
    circularity = (4 * np.pi * area) / (perimeter * perimeter) if perimeter > 0 else 0
    
    # Reject very circular objects (likely apples/tomatoes, not peppers)
    if circularity > 0.88:
        print(f"  └─ Rejected: Too circular ({circularity:.3f}), likely apple/tomato")
        return False
    
    # 3. Check for bell pepper's characteristic "blocky" shape using approximation
    epsilon = 0.02 * perimeter
    approx = cv2.approxPolyDP(largest_contour, epsilon, True)
    num_vertices = len(approx)
    
    # Bell peppers when viewed from top/side have 4-8 vertices (blocky/lobed)
    # Apples have many more vertices (smooth curve) or very few (circle)
    # We want something in between
    if num_vertices < 4:
        print(f"  └─ Rejected: Too simple shape ({num_vertices} vertices)")
        return False
    
    # 4. Texture variance (peppers have slight surface variations, apples are very smooth)
    # Calculate standard deviation of intensity
    std_dev = np.std(gray)
    
    # Very low variance suggests overly smooth surface (like a shiny apple)
    if std_dev < 15:
        print(f"  └─ Rejected: Surface too smooth (std: {std_dev:.1f}), likely apple")
        return False
    
    print(f"  └─ Texture OK: circularity={circularity:.3f}, vertices={num_vertices}, texture_std={std_dev:.1f}")
    return True

def validate_pepper_shape(bbox, image_shape=None):
    """Check if bounding box has pepper-like aspect ratio and reasonable size"""
    x1, y1, x2, y2 = bbox
    width = x2 - x1
    height = y2 - y1
    
    if width == 0 or height == 0:
        return False
    
    # Check minimum size (peppers should be reasonably sized, not tiny fragments)
    min_dimension = min(width, height)
    if min_dimension < 50:  # Minimum 50 pixels in smallest dimension
        print(f"  └─ Rejected: Too small ({min_dimension:.0f}px)")
        return False
    
    aspect_ratio = height / width
    # Peppers are typically 0.8-2.0 (tightened range from 0.6-3.0)
    # Fingers and hands often exceed these ratios
    if not (0.8 <= aspect_ratio <= 2.0):
        print(f"  └─ Rejected: Invalid aspect ratio ({aspect_ratio:.2f})")
        return False
    
    # Check area relative to bounding box (peppers are fairly "solid")
    # This helps reject thin/elongated objects like fingers
    bbox_area = width * height
    if image_shape is not None:
        img_height, img_width = image_shape[:2]
        # Reject if detection is too large (> 80% of image, likely not a single pepper)
        if bbox_area > (img_height * img_width * 0.8):
            print(f"  └─ Rejected: Too large relative to image")
            return False
    
    return True

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

def _clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))

def _rects_overlap(a, b, margin=2):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (ax2 + margin < bx1 or bx2 + margin < ax1 or ay2 + margin < by1 or by2 + margin < ay1)

def _truncate_text(text, max_chars=18):
    return text if len(text) <= max_chars else text[: max_chars - 1] + "…"

def _text_size(text, font, font_scale, thickness):
    size, _ = cv2.getTextSize(text, font, font_scale, thickness)
    return size

def _draw_label_with_alpha(img, x, y, w, h, color, alpha=0.7):
    x1, y1 = int(x), int(y)
    x2, y2 = int(x + w), int(y + h)
    overlay = img.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, thickness=-1)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

# Label rendering defaults (UI-only config)
LABEL_ALPHA = 0.7
MAX_LABEL_CHARS = 18

def _place_label_collision_free(img_w, img_h, pref_x, pref_y, w, h, anchor_box, occupied):
    """
    Try to place label rectangle (w,h) near preferred (pref_x,pref_y) and avoid overlap.
    If above overlaps, try shifting up, then below, then to the right of the anchor.
    Returns (x, y) top-left and a boolean indicating whether a leader line to object center is recommended.
    """
    # Start above
    candidates = []
    # above the anchor
    candidates.append((_clamp(pref_x, 0, img_w - w), _clamp(pref_y - h - 6, 0, img_h - h)))
    # below the anchor
    candidates.append((_clamp(pref_x, 0, img_w - w), _clamp(pref_y + 6, 0, img_h - h)))
    # right of anchor box
    if anchor_box is not None:
        ax1, ay1, ax2, ay2 = anchor_box
        right_x = _clamp(ax2 + 8, 0, img_w - w)
        mid_y = _clamp((ay1 + ay2) // 2 - h // 2, 0, img_h - h)
        candidates.append((right_x, mid_y))
        left_x = _clamp(ax1 - w - 8, 0, img_w - w)
        candidates.append((left_x, mid_y))

    # try vertical shifts to avoid overlap
    for x, y in list(candidates):
        rect = (x, y, x + w, y + h)
        y_try = y
        attempts = 0
        while any(_rects_overlap(rect, r) for r in occupied) and attempts < 10 and y_try > 0:
            y_try = _clamp(y_try - (h + 4), 0, img_h - h)
            rect = (x, y_try, x + w, y_try + h)
            attempts += 1
        if not any(_rects_overlap(rect, r) for r in occupied):
            occupied.append(rect)
            return (x, y_try), True

    # As a last resort, stack at the top with incremental x
    for y in (4, h + 8, 2 * (h + 8)):
        for x in range(4, img_w - w - 4, max(w // 2, 40)):
            rect = (x, y, x + w, y + h)
            if not any(_rects_overlap(rect, r) for r in occupied):
                occupied.append(rect)
                return (x, y), True

    # Fallback: place within bounds (may overlap)
    x = _clamp(pref_x, 0, img_w - w)
    y = _clamp(pref_y, 0, img_h - h)
    occupied.append((x, y, x + w, y + h))
    return (x, y), True

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
    
    # 1) Create priors for GrabCut: mark probable background where leaf-green dominates
    lower_green_bg = np.array([35, 60, 40])
    upper_green_bg = np.array([85, 255, 255])
    green_bg = cv2.inRange(hsv, lower_green_bg, upper_green_bg)
    # probable foreground seeds: red/orange/yellow plus central area
    lower_red1 = np.array([0, 70, 60]);  upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 70, 60]); upper_red2 = np.array([180, 255, 255])
    lower_orange = np.array([10, 70, 60]); upper_orange = np.array([25, 255, 255])
    lower_yellow = np.array([25, 70, 60]); upper_yellow = np.array([35, 255, 255])
    fg_color = cv2.inRange(hsv, lower_red1, upper_red1) | cv2.inRange(hsv, lower_red2, upper_red2) | cv2.inRange(hsv, lower_orange, upper_orange) | cv2.inRange(hsv, lower_yellow, upper_yellow)
    # central ellipse seed
    center_mask = np.zeros(roi.shape[:2], np.uint8)
    cy, cx = roi.shape[0] // 2, roi.shape[1] // 2
    ry, rx = max(8, roi.shape[0] // 4), max(8, roi.shape[1] // 4)
    cv2.ellipse(center_mask, (cx, cy), (rx, ry), 0, 0, 360, 255, -1)
    fg_seed = cv2.bitwise_or(fg_color, center_mask)
    # Prepare GrabCut mask with seeds
    GC_BGD, GC_FGD, GC_PR_BGD, GC_PR_FGD = 0, 1, 2, 3
    gc_mask = np.full(roi.shape[:2], GC_PR_BGD, np.uint8)
    gc_mask[green_bg > 0] = GC_BGD
    gc_mask[fg_seed > 0] = GC_PR_FGD
    try:
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)
        cv2.grabCut(roi, gc_mask, None, bgd_model, fgd_model, 4, cv2.GC_INIT_WITH_MASK)
        grabcut_mask = np.where((gc_mask == GC_FGD) | (gc_mask == GC_PR_FGD), 1, 0).astype('uint8')
    except Exception:
        grabcut_mask = np.ones(roi.shape[:2], dtype=np.uint8)
    
    # 2) Edge emphasis to avoid including flat leaves
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 120)
    edges = cv2.dilate(edges, np.ones((3,3), np.uint8), iterations=1)
    edge_mask = cv2.threshold(edges, 0, 255, cv2.THRESH_BINARY)[1]
    
    # Combine: foreground must also overlap edge or fg_color to keep solid pepper, not flat leaf
    color_or_edge = cv2.bitwise_or(fg_seed, edge_mask)
    combined_mask = cv2.bitwise_and(grabcut_mask * 255, (color_or_edge > 0).astype(np.uint8) * 255)
    
    # Morphological operations to clean up the mask
    kernel = np.ones((3, 3), np.uint8)
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel, iterations=1)
    
    # Fill holes
    combined_mask = cv2.medianBlur(combined_mask, 5)
    try:
        # keep largest component only
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats((combined_mask > 0).astype(np.uint8), connectivity=8)
        if num_labels > 1:
            largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
            combined_mask = (labels == largest_label).astype(np.uint8) * 255
    except Exception:
        pass
    
    # Create full-size mask
    full_mask = np.zeros((h, w), dtype=np.uint8)
    full_mask[y1:y2, x1:x2] = combined_mask
    
    return full_mask

def _cv_ripeness_from_hsv(bgr_image):
    """
    Compute ripeness strictly from the cutout's HSV colors using detailed bands:
    - Green (Unripe)
    - Light Green → Yellowish-Green (Early Ripening)
    - Yellow (Mid)
    - Orange (Advanced)
    - Red (Fully Ripe)
    - Deep Red / Maroon (Very Ripe)
    - Dull Red / Dark Brownish / Purplish (Overripe)
    - Brown → Black Spots (Spoiling) -> penalty
    Returns score 0-100 and stage label.
    """
    if bgr_image is None or bgr_image.size == 0:
        return {'score': 0.0, 'stage': 'unknown', 'bands': {}}
    hsv = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    # Keep only sufficiently bright/saturated pixels to avoid noise
    valid = (s >= 30) & (v >= 40)
    total = int(np.count_nonzero(valid))
    if total == 0:
        return {'score': 0.0, 'stage': 'unknown', 'bands': {}}
    # Band masks (Hue ranges in OpenCV: 0..180)
    green = valid & (h >= 35) & (h <= 85) & (s >= 60)  # strong green
    light_green = valid & (h >= 30) & (h < 35)  # yellowish-green
    yellow = valid & (h >= 20) & (h < 30)
    orange = valid & (h >= 10) & (h < 20)
    red1 = valid & (h <= 10)
    red2 = valid & (h >= 170)
    red = red1 | red2
    # Deep red/maroon: red with lower V or high S, moderate V
    deep_red = red & (v < 120)
    # Dull red / brownish / purplish (overripe): low saturation or very low V near red/purple
    dull_red = (valid & (((h <= 15) | (h >= 165)) & (s < 50))) | (valid & (h >= 140) & (h < 165) & (v < 120))
    # Spoiling dark spots: very low V regardless of hue but not background (use valid mask)
    dark_spots = (v < 60) & (s < 80) & valid
    # Percentages
    pct = lambda m: (int(np.count_nonzero(m)) / total) * 100.0
    bands = {
        'green': pct(green),
        'light_green': pct(light_green),
        'yellow': pct(yellow),
        'orange': pct(orange),
        'red': pct(red),
        'deep_red': pct(deep_red),
        'dull_red': pct(dull_red),
        'dark_spots': pct(dark_spots)
    }
    # Weighted score (0..100), later bands mean riper except dull/overripe which reduces
    weights = {
        'green': 10.0,
        'light_green': 30.0,
        'yellow': 45.0,
        'orange': 65.0,
        'red': 85.0,
        'deep_red': 92.0,
        'dull_red': 70.0  # overripe dull lowers perceived ripeness quality
    }
    score = 0.0
    for k, w in weights.items():
        score += bands[k] * (w / 100.0)
    # Penalty for dark spots (spoilage)
    score -= min(20.0, bands['dark_spots'] * 0.4)
    score = float(max(0.0, min(100.0, score)))
    # Aggregate coarse groups for dominance logic
    green_total = bands['green'] + bands['light_green']
    yellow_total = bands['yellow'] + bands['orange']
    red_total = bands['red'] + bands['deep_red']
    overripe_total = bands['dull_red']
    # Find dominant and secondary
    groups = {
        'green': green_total,
        'yellow_orange': yellow_total,
        'red': red_total,
        'overripe': overripe_total
    }
    dominant_group = max(groups.items(), key=lambda kv: kv[1])[0]
    # secondary: highest among remaining
    secondary_group = max({k:v for k,v in groups.items() if k != dominant_group}.items(), key=lambda kv: kv[1])[0]
    # Determine stage label with mix rules
    stage_label = 'unknown'
    # thresholds to consider "significant" secondary
    secondary_sig = groups[secondary_group] >= 15.0
    if dominant_group == 'overripe':
        stage_label = 'overripe'
    elif dominant_group == 'red':
        stage_label = 'ripe' if not secondary_sig else 'ripening'
    elif dominant_group == 'yellow_orange':
        stage_label = 'ripening'
    elif dominant_group == 'green':
        stage_label = 'unripe' if not secondary_sig else 'ripening'
    details = {
        'dominant': dominant_group,
        'secondary': secondary_group,
        'groups': groups
    }
    return {'score': score, 'stage': stage_label, 'bands': bands, 'details': details}

def _gray_world_white_balance(bgr):
    """Simple gray-world white balance to normalize color cast."""
    try:
        b, g, r = cv2.split(bgr.astype(np.float32))
        mean_b, mean_g, mean_r = np.mean(b), np.mean(g), np.mean(r)
        mean_gray = (mean_b + mean_g + mean_r) / 3.0
        scale_b = mean_gray / (mean_b + 1e-6)
        scale_g = mean_gray / (mean_g + 1e-6)
        scale_r = mean_gray / (mean_r + 1e-6)
        b = np.clip(b * scale_b, 0, 255)
        g = np.clip(g * scale_g, 0, 255)
        r = np.clip(r * scale_r, 0, 255)
        balanced = cv2.merge((b, g, r)).astype(np.uint8)
        return balanced
    except Exception:
        return bgr

def _cv_ripeness_from_lab(bgr_image):
    """
    LAB-based ripeness estimator (more robust than HSV to lighting).
    - White balance + CLAHE on L
    - Use a* (green↔red) and b* (blue↔yellow) dominance
    Returns {'score','stage','bands','details'}
    """
    if bgr_image is None or bgr_image.size == 0:
        return {'score': 0.0, 'stage': 'unknown', 'bands': {}, 'details': {}}
    # Pre-normalize
    img = _gray_world_white_balance(bgr_image)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    L, A, B = cv2.split(lab)
    try:
        # CLAHE on L to stabilize brightness
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        L = clahe.apply(L)
        lab = cv2.merge((L, A, B))
    except Exception:
        pass
    # Valid pixels: non-black in original
    valid = np.any(img > 0, axis=2)
    total = int(np.count_nonzero(valid))
    if total == 0:
        return {'score': 0.0, 'stage': 'unknown', 'bands': {}, 'details': {}}
    # Center a*, b* around 0
    a = A.astype(np.int16) - 128
    b = B.astype(np.int16) - 128
    l = L.astype(np.int16)
    # Adaptive thresholds from percentiles
    a_pos = np.percentile(a[valid], 60)  # positive a threshold
    a_neg = -np.percentile((-a[valid]), 60)  # negative a threshold (green)
    b_pos = np.percentile(b[valid], 60)  # yellow side
    # Fixed floors to avoid too small thresholds
    a_pos = max(a_pos, 8)
    a_neg = min(a_neg, -8)
    b_pos = max(b_pos, 6)
    # Masks
    red_mask = valid & (a > a_pos)
    deep_red_mask = red_mask & (l < 120)
    green_mask = valid & (a < a_neg)
    yellow_mask = valid & (b > b_pos) & (a > 0)
    dull_overripe_mask = valid & (np.abs(a) < 10) & (b < 5) & (l < 120)
    dark_spots_mask = valid & (l < 60)
    pct = lambda m: (int(np.count_nonzero(m)) / total) * 100.0
    bands = {
        'green': pct(green_mask),
        'yellow_orange': pct(yellow_mask),
        'red': pct(red_mask),
        'deep_red': pct(deep_red_mask),
        'dull_overripe': pct(dull_overripe_mask),
        'dark_spots': pct(dark_spots_mask)
    }
    # Groups and dominance
    green_total = bands['green']
    yellow_total = bands['yellow_orange']
    red_total = bands['red'] + 0.5 * bands['deep_red']  # bonus for deep red
    overripe_total = bands['dull_overripe']
    groups = {'green': green_total, 'yellow_orange': yellow_total, 'red': red_total, 'overripe': overripe_total}
    dominant = max(groups.items(), key=lambda kv: kv[1])[0]
    # Stage logic
    if dominant == 'overripe':
        stage = 'overripe'
    elif dominant == 'red':
        stage = 'ripe' if green_total < 15 and yellow_total < 20 else 'ripening'
    elif dominant == 'yellow_orange':
        stage = 'ripening'
    else:
        stage = 'unripe' if (red_total < 15 and yellow_total < 15) else 'ripening'
    # Score 0..100 with penalties
    score = 0.0
    score += green_total * 0.15
    score += yellow_total * 0.55
    score += (bands['red'] * 0.85 + bands['deep_red'] * 0.95)
    score -= min(20.0, bands['dull_overripe'] * 0.4)
    score -= min(25.0, bands['dark_spots'] * 0.5)
    score = float(max(0.0, min(100.0, score)))
    details = {'groups': groups, 'dominant': dominant}
    return {'score': score, 'stage': stage, 'bands': bands, 'details': details}

def _cv_secondary_estimates_cv_only(ripeness_pct, surface_quality, size_consistency, bgr_cutout):
    """
    CV-only estimations for:
      - Nutrition (vitamin C, calories, estimated weight)
      - Shelf life (days for room/refrigerated/optimal)
      - Market analysis (grade and price)
    Inputs come from the SAME SOURCE as Ripeness Prediction:
      - ripeness_pct: LAB-based ripeness score (0-100)
      - surface_quality, size_consistency: from CV metrics (0-100)
      - bgr_cutout: masked pepper cutout used for analysis
    Returns nutrition, shelf, market objects matching the frontend schema.
    """
    # Weight proxy from non-zero cutout pixels (simple area heuristic)
    try:
        nonzero = int(np.count_nonzero(cv2.cvtColor(bgr_cutout, cv2.COLOR_BGR2GRAY)))
        weight_g = int(np.clip(140 + nonzero // 1100, 120, 380))
    except Exception:
        weight_g = 200
    # Vitamin C scales with ripeness and weight (bounded)
    vitc_per_100 = 100 + ripeness_pct * 2.3  # mg per 100g
    vitamin_c = float(np.clip(vitc_per_100 * (weight_g / 100.0), 80, 500))
    calories = 62.0  # constant per pepper (approx)
    highlights = []
    if vitamin_c >= 250: highlights.append('Excellent vitamin C source (≥250mg)')
    if ripeness_pct >= 55: highlights.append('High in antioxidants')
    if size_consistency >= 70: highlights.append('Uniform size – good for packing')
    nutrition = {
        'per_pepper': {'vitamin_c': round(vitamin_c), 'calories': round(calories)},
        'estimated_weight_g': int(weight_g),
        'nutritional_highlights': highlights
    }
    # Shelf life base: decreases as ripeness and surface defects increase
    room_days_base = float(np.clip(6.5 - ripeness_pct/22.0 - max(0.0, 70 - surface_quality)/60.0, 2.0, 8.0))
    refrigerated_days_base = room_days_base * 2.5
    optimal_days_base = np.clip((room_days_base + refrigerated_days_base)/2.0 + 5.0 - ripeness_pct/22.0, 4.0, 18.0)
    # Defect severity bands based on surface quality
    if surface_quality < 40:
        severity = 'severe'
        shelf_mult = 0.50
        vitc_mult = 0.90
        grade_penalty = 2
    elif surface_quality < 60:
        severity = 'moderate'
        shelf_mult = 0.65
        vitc_mult = 0.95
        grade_penalty = 1
    elif surface_quality < 75:
        severity = 'minor'
        shelf_mult = 0.80
        vitc_mult = 1.00
        grade_penalty = 1
    else:
        severity = 'none'
        shelf_mult = 1.00
        vitc_mult = 1.00
        grade_penalty = 0
    # Apply severity to shelf life
    room_days = round(float(np.clip(room_days_base * shelf_mult, 1.0, 8.0)), 1)
    refrigerated_days = round(float(np.clip(refrigerated_days_base * shelf_mult, 1.0, 18.0)), 1)
    optimal_days = round(float(np.clip(optimal_days_base * shelf_mult, 4.0, 18.0)), 1)
    if severity != 'none':
        optimal_days = float(min(optimal_days, 12.0))
    shelf = {
        'room_temperature': {'days': round(room_days, 1)},
        'refrigerated': {'days': refrigerated_days},
        'optimal_storage': {'days': optimal_days}
    }
    # Market grade: combine CV scores (no price)
    combined = 0.45 * ripeness_pct + 0.40 * surface_quality + 0.15 * size_consistency
    if combined >= 85:
        grade, desc = 'Grade A', 'Premium grade, fresh market'
    elif combined >= 65:
        grade, desc = 'Grade B', 'Commercial grade, processing'
    else:
        grade, desc = 'Grade C', 'Lower grade, food service'
    # Apply grade penalty for defects
    if grade_penalty > 0:
        if grade == 'Grade A':
            grade = 'Grade B' if grade_penalty == 1 else 'Grade C'
            desc = 'Commercial grade, processing' if grade == 'Grade B' else 'Lower grade, food service'
        elif grade == 'Grade B' and grade_penalty >= 1:
            grade = 'Grade C'
            desc = 'Lower grade, food service'
    market = {'grade': grade, 'grade_description': desc}
    # Carrier-based shelf life estimates (derived from ripeness and base days)
    # Heuristics: truck (refrigerated) ~0.9*refrigerated, truck (non-refrig) ~0.7*room
    # boat (slow/humid) ~0.6*refrigerated, air_cargo (fast/cool) ~min(1.3*refrigerated, 18)
    carrier = {
        'truck_refrigerated': {'days': round(float(np.clip(refrigerated_days * 0.9, 1.0, 18.0)), 1)},
        'truck_non_refrigerated': {'days': round(float(np.clip(room_days * 0.7, 0.5, 12.0)), 1)},
        'boat': {'days': round(float(np.clip(refrigerated_days * 0.6, 0.5, 14.0)), 1)},
        'air_cargo': {'days': round(float(np.clip(refrigerated_days * 1.2, 1.0, 18.0)), 1)}
    }
    shelf['carrier'] = carrier
    # Apply nutrition adjustment and highlights for defects
    vitamin_c = float(np.clip(vitamin_c * vitc_mult, 80, 500))
    nutrition['per_pepper']['vitamin_c'] = round(vitamin_c)
    if severity != 'none':
        # Remove size highlight if defects and add warning badge
        nutrition['nutritional_highlights'] = [h for h in nutrition['nutritional_highlights'] if 'Uniform size' not in h]
        nutrition['nutritional_highlights'].insert(0, 'Defects detected – inspect/trim; use soon')
        # Add shelf note
        shelf['note'] = 'Use soon – defects may accelerate spoilage'
    return nutrition, shelf, market
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
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'healthy'}), 200
        
    except Exception as e:
        # In production we prefer the container to stay up; report degraded but 200
        return jsonify({'status': 'degraded', 'error': str(e)}), 200

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
            forbidden_zones = []  # Regions confirmed as non-pepper objects
            
            # Define non-pepper object classes that should block pepper detection
            NON_PEPPER_OBJECTS = [
                'apple', 'orange', 'banana', 'lemon', 'strawberry', 
                'tomato', 'person', 'hand', 'carrot', 'broccoli',
                'pineapple', 'watermelon', 'grape', 'peach', 'pear'
            ]
            
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
                        
                        # Mark high-confidence non-pepper detections as forbidden zones
                        if class_name.lower() in NON_PEPPER_OBJECTS and conf > 0.6:
                            forbidden_zones.append({
                                'class_name': class_name,
                                'confidence': conf,
                                'bbox': xyxy
                            })
                            print(f"⛔ Forbidden zone: {class_name} ({conf:.2f}) - will block pepper detection in this region")
            
            # Stage 2: Specialized bell pepper detection with smart filtering
            bell_peppers_detected = False
            if MODELS['bell_pepper_detection']:
                pepper_results = MODELS['bell_pepper_detection'](filepath, conf=0.65, iou=0.5)  # High confidence threshold to reduce false positives
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
                    
                    pepper_count = 0
                    for i, box_data in enumerate(filtered_peppers):
                        conf = box_data['confidence']
                        cls = box_data['class_id']
                        class_name = box_data['class_name']
                        xyxy = box_data['bbox']
                        
                        print(f"\n🔍 Validating detection {i+1}: {class_name} ({conf:.2f})")
                        
                        # EARLY REJECTION: Check if this detection overlaps with forbidden zones
                        is_in_forbidden_zone = False
                        for forbidden in forbidden_zones:
                            iou = calculate_iou(xyxy, forbidden['bbox'])
                            if iou > 0.3:  # Significant overlap
                                print(f"  ⛔ REJECTED: Overlaps with {forbidden['class_name']} (IoU: {iou:.2f})")
                                print(f"     General YOLO identified this as {forbidden['class_name']} with {forbidden['confidence']*100:.1f}% confidence")
                                is_in_forbidden_zone = True
                                break
                        
                        if is_in_forbidden_zone:
                            continue  # Skip this detection entirely
                        
                        # Crop for validation
                        x1, y1, x2, y2 = map(int, xyxy)
                        h, w = image.shape[:2]
                        x1_clip, y1_clip = max(0, x1), max(0, y1)
                        x2_clip, y2_clip = min(w, x2), min(h, y2)
                        temp_crop = image[y1_clip:y2_clip, x1_clip:x2_clip]
                        
                        if temp_crop.size == 0:
                            continue
                        
                        # Use enhanced validation pipeline if available
                        if MODELS['validation_pipeline']:
                            is_valid, failed_stage = MODELS['validation_pipeline'].full_validation(
                                temp_crop, xyxy, image.shape
                            )
                            if not is_valid:
                                print(f"  ❌ Validation failed at stage: {failed_stage}")
                                continue
                        else:
                            # Fallback to original validation
                            if not validate_pepper_shape(xyxy, image.shape):
                                continue
                            if not validate_pepper_color(temp_crop):
                                continue
                            if not validate_pepper_texture(temp_crop):
                                continue
                        
                        print(f"  ✅ Valid bell pepper detected!")
                        
                        bell_peppers_detected = True
                        pepper_count += 1
                        
                        bell_pepper_data = {
                            'variety': class_name,
                            'confidence': conf,
                            'bbox': xyxy,
                            'class_id': cls,
                            'pepper_id': f'pepper_{pepper_count}'
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
                        
                        # Build a mask for transparent crop (prefer segmentation mask if available)
                        mask_full = None
                        try:
                            if hasattr(pepper_result, 'masks') and pepper_result.masks is not None:
                                # Use segmentation mask corresponding to this filtered detection index if available
                                # We approximate by picking the mask with highest IoU with the bbox used
                                masks_tensor = pepper_result.masks.data
                                best_iou = -1.0
                                best_mask = None
                                for m_idx in range(len(masks_tensor)):
                                    m = masks_tensor[m_idx].cpu().numpy()
                                    m_resized = cv2.resize(m, (w, h))
                                    ys, xs = np.where(m_resized > 0.5)
                                    if len(xs) == 0:
                                        continue
                                    bx1, by1, bx2, by2 = int(np.min(xs)), int(np.min(ys)), int(np.max(xs)), int(np.max(ys))
                                    iou_val = calculate_iou([x1 + pad, y1 + pad, x2 - pad, y2 - pad], [bx1, by1, bx2, by2])
                                    if iou_val > best_iou:
                                        best_iou = iou_val
                                        best_mask = (m_resized > 0.5).astype(np.uint8)
                                if best_mask is not None:
                                    mask_full = best_mask
                        except Exception:
                            mask_full = None
                        
                        if mask_full is None:
                            # Fallback: create smart mask from bbox on the full image
                            mask_full = create_smart_mask_from_bbox(image, [x1 + pad, y1 + pad, x2 - pad, y2 - pad])
                        
                        # Crop the mask to the same padded region
                        mask_crop = mask_full[y1:y2, x1:x2] if mask_full is not None else None
                        if mask_crop is None or mask_crop.size == 0:
                            # If mask creation failed, use solid mask (no transparency)
                            mask_crop = np.ones(pepper_crop.shape[:2], dtype=np.uint8) * 255
                        else:
                            # Clean mask edges slightly
                            kernel = np.ones((3, 3), np.uint8)
                            mask_crop = cv2.morphologyEx(mask_crop, cv2.MORPH_CLOSE, kernel, iterations=1)
                            mask_crop = (mask_crop > 0).astype(np.uint8) * 255
                        
                        # Try removing leaf-green pixels if pepper shows strong red/orange
                        try:
                            hsv_crop = cv2.cvtColor(pepper_crop, cv2.COLOR_BGR2HSV)
                            # Color ranges
                            lower_red1 = np.array([0, 80, 60])
                            upper_red1 = np.array([10, 255, 255])
                            lower_red2 = np.array([170, 80, 60])
                            upper_red2 = np.array([180, 255, 255])
                            lower_orange = np.array([10, 80, 60])
                            upper_orange = np.array([25, 255, 255])
                            lower_green_leaf = np.array([35, 60, 40])
                            upper_green_leaf = np.array([85, 255, 255])
                            
                            red_mask = cv2.inRange(hsv_crop, lower_red1, upper_red1) | cv2.inRange(hsv_crop, lower_red2, upper_red2)
                            orange_mask = cv2.inRange(hsv_crop, lower_orange, upper_orange)
                            green_mask = cv2.inRange(hsv_crop, lower_green_leaf, upper_green_leaf)
                            
                            total = float(pepper_crop.shape[0] * pepper_crop.shape[1])
                            red_orange_pct = (np.sum((red_mask > 0) | (orange_mask > 0)) / total) if total > 0 else 0.0
                            green_pct = (np.sum(green_mask > 0) / total) if total > 0 else 0.0
                            
                            # If red/orange dominates, subtract green leaf regions from mask
                            if red_orange_pct > green_pct + 0.05:
                                mask_crop = cv2.bitwise_and(mask_crop, cv2.bitwise_not(green_mask))
                                # Re-clean after subtraction
                                kernel = np.ones((3, 3), np.uint8)
                                mask_crop = cv2.morphologyEx(mask_crop, cv2.MORPH_OPEN, kernel, iterations=1)
                                mask_crop = cv2.medianBlur(mask_crop, 3)
                        except Exception:
                            pass
                        
                        # Keep only the largest connected component to avoid stray leaves
                        try:
                            num_labels, labels, stats, _ = cv2.connectedComponentsWithStats((mask_crop > 0).astype(np.uint8), connectivity=8)
                            if num_labels > 1:
                                # Skip background (label 0)
                                largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
                                mask_crop = (labels == largest_label).astype(np.uint8) * 255
                        except Exception:
                            pass
                        
                        # Tight crop around the refined mask to fit the object
                        ys, xs = np.where(mask_crop > 0)
                        if len(xs) > 0 and len(ys) > 0:
                            min_x, max_x = int(np.min(xs)), int(np.max(xs))
                            min_y, max_y = int(np.min(ys)), int(np.max(ys))
                            # Add tiny margin but keep inside bounds
                            margin = 2
                            min_x = max(0, min_x - margin)
                            min_y = max(0, min_y - margin)
                            max_x = min(mask_crop.shape[1] - 1, max_x + margin)
                            max_y = min(mask_crop.shape[0] - 1, max_y + margin)
                            mask_crop_tight = mask_crop[min_y:max_y+1, min_x:max_x+1]
                            pepper_crop_tight = pepper_crop[min_y:max_y+1, min_x:max_x+1]
                            # Save overlay-friendly bbox relative to original image for frontend masks
                            try:
                                pepper['bbox'] = {
                                    'x': int((x1) + min_x),
                                    'y': int((y1) + min_y),
                                    'width': int(max_x - min_x + 1),
                                    'height': int(max_y - min_y + 1)
                                }
                            except Exception:
                                pass
                        else:
                            mask_crop_tight = mask_crop
                            pepper_crop_tight = pepper_crop
                        
                        # Feather alpha edges to get product-style soft cutout
                        try:
                            # Blur only slightly to keep edges crisp but not jagged
                            feathered_alpha = cv2.GaussianBlur(mask_crop_tight, (0, 0), sigmaX=1.2, sigmaY=1.2)
                            # Re-normalize to 0-255
                            alpha_tight = np.clip(feathered_alpha, 0, 255).astype(np.uint8)
                        except Exception:
                            alpha_tight = mask_crop_tight
                        
                        # Create masked (transparent) PNG
                        transparent_name = f'crop_{timestamp}_{i+1}_transparent.png'
                        transparent_path = os.path.join(app.config['RESULTS_FOLDER'], transparent_name)
                        try:
                            b, g, r = cv2.split(pepper_crop_tight)
                            rgba = cv2.merge((b, g, r, alpha_tight))
                            cv2.imwrite(transparent_path, rgba)
                            bell_pepper_data['transparent_png_url'] = f'/results/{transparent_name}'
                        except Exception as _:
                            bell_pepper_data['transparent_png_url'] = None
                        
                        if pepper_crop.size > 0:
                            # Save cropped pepper image
                            crop_name = f'crop_{timestamp}_{i+1}.jpg'
                            crop_path = os.path.join(app.config['RESULTS_FOLDER'], crop_name)
                            cv2.imwrite(crop_path, pepper_crop, [cv2.IMWRITE_JPEG_QUALITY, 95])
                            
                            # Run advanced quality analysis using OpenCV + scikit-image
                            quality_analysis = None
                            if MODELS['cv_quality_analyzer']:
                                try:
                                    # Build a definitive analysis input from the mask (no background leakage)
                                    # Ensure we have a binary mask aligned to the tight crop
                                    binary_alpha = (mask_crop_tight > 0).astype(np.uint8) * 255
                                    # Strict requirement: must analyze masked cutout only
                                    nonzero_pixels = int(np.count_nonzero(binary_alpha))
                                    if nonzero_pixels < 25:
                                        raise ValueError("Empty/invalid mask for analysis")
                                    # Create a clean BGR image where background is blacked out
                                    analysis_input = cv2.bitwise_and(pepper_crop_tight, pepper_crop_tight, mask=binary_alpha)
                                    # Save a tiny preview beside the transparent PNG for verification
                                    try:
                                        preview_name = f'crop_{timestamp}_{i+1}_analysis_input_preview.png'
                                        preview_path = os.path.join(app.config['RESULTS_FOLDER'], preview_name)
                                        b_p, g_p, r_p = cv2.split(analysis_input)
                                        rgba_preview = cv2.merge((b_p, g_p, r_p, binary_alpha))
                                        cv2.imwrite(preview_path, rgba_preview)
                                        bell_pepper_data['analysis_input_preview_url'] = f'/results/{preview_name}'
                                    except Exception:
                                        pass
                                    
                                    # Use masked image only
                                    metrics = MODELS['cv_quality_analyzer'].analyze_pepper_quality(analysis_input)
                                    # Override/augment ripeness using robust LAB estimator (fallback to HSV)
                                    try:
                                        ripeness_lab = _cv_ripeness_from_lab(analysis_input)
                                        metrics['ripeness_level'] = ripeness_lab['score']
                                        bell_pepper_data['ripeness_bands'] = ripeness_lab['bands']
                                        bell_pepper_data['ripeness_groups'] = ripeness_lab.get('details', {}).get('groups')
                                        # Debug: print LAB groups and score
                                        print(f"   [DBG] LAB ripeness score={metrics['ripeness_level']:.1f} groups={bell_pepper_data['ripeness_groups']}")
                                    except Exception as _:
                                        try:
                                            ripeness_hsv = _cv_ripeness_from_hsv(analysis_input)
                                            metrics['ripeness_level'] = ripeness_hsv['score']
                                            bell_pepper_data['ripeness_bands'] = ripeness_hsv['bands']
                                            bell_pepper_data['ripeness_groups'] = ripeness_hsv.get('details', {}).get('groups')
                                            print(f"   [DBG] HSV fallback ripeness score={metrics['ripeness_level']:.1f}")
                                        except Exception:
                                            print("   [DBG] Ripeness estimation failed (both LAB and HSV).")
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
                                    # Keep consistency: analyze masked cutout when available
                                    binary_alpha = (mask_crop_tight > 0).astype(np.uint8) * 255
                                    nonzero_pixels = int(np.count_nonzero(binary_alpha))
                                    if nonzero_pixels < 25:
                                        raise ValueError("Empty/invalid mask for ANFIS analysis")
                                    analysis_input = cv2.bitwise_and(pepper_crop_tight, pepper_crop_tight, mask=binary_alpha)
                                    quality_analysis = MODELS['anfis_quality'].analyze_pepper_image(analysis_input)
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
                            
                            # Stage 3C: CV-based Ripeness Prediction (consistent with LAB estimator)
                            if quality_analysis:
                                try:
                                    # Prefer LAB-based estimate
                                    ripeness_est = _cv_ripeness_from_lab(analysis_input)
                                    ripeness_pct = float(ripeness_est['score'])
                                    stage = ripeness_est['stage']
                                    # Days heuristic by stage and distance to 90 (ripe)
                                    if stage == 'ripe':
                                        harvest_note = 'Use soon – optimal quality'
                                        days_to_optimal = 0.0
                                    elif stage == 'ripening':
                                        harvest_note = 'Approaching optimal harvest time'
                                        days_to_optimal = max(0.0, (85 - ripeness_pct) / 5.0)
                                    elif stage == 'overripe':
                                        harvest_note = 'Past optimal – quality declining'
                                        days_to_optimal = 0.0
                                    else:
                                        harvest_note = 'Early harvest time – good for storage'
                                        days_to_optimal = max(0.0, (60 - ripeness_pct) / 3.5)
                                    
                                    bell_pepper_data['ripeness_prediction'] = {
                                        'current_stage': stage,
                                        'ripeness_percentage': round(ripeness_pct, 1),
                                        'harvest_recommendation': harvest_note,
                                        'days_to_optimal_harvest': round(days_to_optimal, 1)
                                    }
                                    # Debug: compare bar vs prediction
                                    try:
                                        bar_val = float(quality_analysis.get('ripeness_level', 0.0))
                                    except Exception:
                                        bar_val = -1
                                    print(f"   [DBG] Ripeness bar={bar_val:.1f} vs prediction={ripeness_pct:.1f} ({stage})")
                                except Exception as e:
                                    print(f"CV-based ripeness prediction error: {e}")
                            
                            # Stage 3D: CV-only secondary estimates (nutrition, shelf life, market)
                            try:
                                ripeness_pct = float(quality_analysis.get('ripeness_level', 0.0))
                                surface_quality = float(quality_analysis.get('surface_quality', 0.0))
                                size_consistency = float(quality_analysis.get('size_consistency', 0.0))
                                nutrition, shelf, market = _cv_secondary_estimates_cv_only(
                                    ripeness_pct, surface_quality, size_consistency, analysis_input
                                )
                                bell_pepper_data['nutrition'] = nutrition
                                bell_pepper_data['shelf_life'] = shelf
                                bell_pepper_data['market_analysis'] = market
                                print(f"   [DBG] Secondary: weight={nutrition['estimated_weight_g']}g, room={shelf['room_temperature']['days']}d, grade={market['grade']}")
                            except Exception as e:
                                print(f"Secondary CV estimates error: {e}")
                        
                        # Stage 3E: Usage Recommendations (Salad Suitability, Cooking, etc.)
                        # Use the SAME ripeness percentage source as ripeness_prediction
                        try:
                            # Get ripeness percentage from ripeness_prediction (same source as displayed)
                            ripeness_pred = bell_pepper_data.get('ripeness_prediction', {})
                            ripeness_pct = float(ripeness_pred.get('ripeness_percentage', 0.0))
                            
                            # Fallback to quality_analysis if ripeness_prediction not available
                            if ripeness_pct == 0.0:
                                ripeness_pct = float(quality_analysis.get('ripeness_level', 0.0))
                            
                            # Get surface quality from quality_analysis (same source as other analyses)
                            surface_quality = float(quality_analysis.get('surface_quality', 0.0))
                            variety_name = bell_pepper_data.get('variety', 'Green')
                            variety_key = variety_name.split(' ')[0] if variety_name else 'Green'
                            
                            # Check disease status (same logic as other analyses)
                            is_healthy = True
                            if bell_pepper_data.get('disease_analysis'):
                                disease = bell_pepper_data['disease_analysis']
                                if isinstance(disease, dict):
                                    is_healthy = disease.get('is_healthy', True)
                                elif isinstance(disease, str):
                                    try:
                                        import json
                                        disease_dict = json.loads(disease)
                                        is_healthy = disease_dict.get('is_healthy', True)
                                    except:
                                        is_healthy = True
                            
                            # Determine salad suitability using SAME data sources
                            # Criteria: ripeness >= 60%, surface quality >= 70%, healthy, and Red/Yellow/Orange varieties preferred
                            suitable_for_salad = (
                                ripeness_pct >= 60 and
                                surface_quality >= 70 and
                                is_healthy and
                                variety_key in ['Red', 'Yellow', 'Orange']
                            )
                            
                            # Determine usage recommendations based on SAME ripeness percentage
                            usage_recommendations = []
                            if suitable_for_salad:
                                usage_recommendations.append('salad')
                            
                            # Best for cooking (medium ripeness: 30-80%)
                            if ripeness_pct >= 30 and ripeness_pct < 80:
                                usage_recommendations.append('cooking')
                            
                            # For sauces/seasoning (very ripe >=80% or low surface quality <50%)
                            if ripeness_pct >= 80 or surface_quality < 50:
                                usage_recommendations.append('sauce')
                            
                            # If no specific recommendations, default to cooking
                            if not usage_recommendations:
                                usage_recommendations.append('cooking')
                            
                            bell_pepper_data['usage_recommendations'] = {
                                'suitable_for_salad': suitable_for_salad,
                                'usage_tags': usage_recommendations,
                                'recommendations': {
                                    'salad': suitable_for_salad,
                                    'cooking': 'cooking' in usage_recommendations,
                                    'sauce': 'sauce' in usage_recommendations
                                }
                            }
                            print(f"   [DBG] Usage: ripeness={ripeness_pct:.1f}%, surface={surface_quality:.1f}%, salad={suitable_for_salad}, tags={usage_recommendations}")
                        except Exception as e:
                            print(f"Usage recommendations error: {e}")
                            # Fallback
                            bell_pepper_data['usage_recommendations'] = {
                                'suitable_for_salad': False,
                                'usage_tags': ['cooking'],
                                'recommendations': {
                                    'salad': False,
                                    'cooking': True,
                                    'sauce': False
                                }
                            }
                        
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
            # Track occupied label rectangles to prevent overlap
            occupied_label_rects = []
            
            # No colored overlays needed - using arrows only
            # overlay = np.zeros_like(annotated_image, dtype=np.uint8)
            
            # Process general objects: labels removed as requested (no-op for display)
            # We keep detections for JSON but do not render labels/arrows on the result image.
            pass
            
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
                
                # Use a single global highlight color (BGR) to keep UI consistent with overlays
                highlight_color = np.array([255, 108, 105], dtype=np.float32)  # matches rgba(105,108,255) in CSS (approx)
                # Create soft body tint inside the mask
                mask_u8 = (mask_binary.astype(np.uint8)) * 255 if mask_binary.max() <= 1 else mask_binary.astype(np.uint8)
                body_alpha = 0.25
                if mask_u8.any():
                    body_inds = mask_u8 > 0
                    # Blend color onto annotated image
                    for c in range(3):
                        annotated_image[:, :, c][body_inds] = (
                            (1.0 - body_alpha) * annotated_image[:, :, c][body_inds].astype(np.float32)
                            + body_alpha * highlight_color[c]
                        ).astype(np.uint8)
                    # Create outer glow using dilated mask and Gaussian blur
                    kernel = np.ones((9, 9), np.uint8)
                    dilated = cv2.dilate(mask_u8, kernel, iterations=2)
                    glow = cv2.GaussianBlur(dilated, (0, 0), sigmaX=8, sigmaY=8)
                    glow_alpha = (glow.astype(np.float32) / 255.0) * 0.6  # 0..0.6
                    # Apply glow
                    for c in range(3):
                        annotated_image[:, :, c] = np.clip(
                            (1.0 - glow_alpha) * annotated_image[:, :, c].astype(np.float32)
                            + glow_alpha * highlight_color[c],
                            0,
                            255
                        ).astype(np.uint8)
            
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
                            'crop_url': f'/results/{pepper.crop_path}' if pepper.crop_path else None,
                            # Prefer transparent cutout if it exists on disk (no DB column required)
                            'transparent_url': (
                                f"/results/{pepper.crop_path.replace('.jpg', '_transparent.png')}"
                                if pepper.crop_path and os.path.exists(
                                    os.path.join(app.config['RESULTS_FOLDER'], pepper.crop_path.replace('.jpg', '_transparent.png'))
                                ) else None
                            )
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
    debug_flag = os.getenv('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=5000, debug=debug_flag)