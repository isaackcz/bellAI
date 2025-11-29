# PepperAI - Bell Pepper Quality Assessment System

PepperAI is an AI-powered system for analyzing bell pepper images to assess quality, detect diseases, and provide comprehensive agricultural insights.

## System Architecture

### High-Level System Flow

```
┌─────────┐
│  User   │
└────┬────┘
     │ Upload Image
     ▼
┌─────────────────────┐
│  Image Upload       │
│  (Flask Route)      │
└────┬────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│  Multi-Stage Detection Pipeline                            │
│                                                             │
│  Stage 1: General Object Detection (YOLO COCO)            │
│    ├─ Detects 80 COCO classes                             │
│    └─ Creates "Forbidden Zones" for non-pepper objects     │
│                                                             │
│  Stage 2: Bell Pepper Detection (YOLO Custom Model)         │
│    ├─ Detects bell peppers                                 │
│    ├─ Filters using forbidden zones                       │
│    └─ Validation Pipeline (shape, color, texture)          │
│                                                             │
│  Stage 3: Quality Analysis                                 │
│    ├─ CV-based Quality Analyzer (primary)                 │
│    │   ├─ Color Uniformity                                │
│    │   ├─ Size Consistency                                │
│    │   ├─ Surface Quality                                │
│    │   └─ Ripeness Level                                  │
│    └─ ANFIS Quality Assessment (fallback)                 │
│                                                             │
│  Stage 3C: Advanced AI Analysis                           │
│    ├─ Ripeness Prediction                                 │
│    ├─ Shelf Life Estimation                               │
│    ├─ Nutritional Analysis                                │
│    ├─ Variety Classification                              │
│    └─ Market Value Analysis                               │
│                                                             │
│  Optional: Disease Detection                               │
│    └─ Health Analysis (if available)                      │
└────┬───────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────┐
│  Database Storage   │
│  ├─ AnalysisHistory │
│  └─ BellPepper       │
│     Detection       │
└────┬────────────────┘
     │
     ▼
┌─────────────────────┐ 
│  Annotated Image    │
│  Generation         │
└────┬────────────────┘
     │
     ▼
┌─────────┐
│  User   │
│ Results │
└─────────┘
```

### Detailed Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         IMAGE PROCESSING PIPELINE                        │
└─────────────────────────────────────────────────────────────────────────┘

1. IMAGE UPLOAD
   ┌──────────────┐
   │ Upload Image │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Save to      │
   │ uploads/     │
   └──────┬───────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. GENERAL OBJECT DETECTION (YOLO COCO - 80 classes)                    │
│                                                                          │
│   Input: Original Image                                                 │
│   Output:                                                               │
│     ├─ General objects detected                                        │
│     └─ Forbidden zones (non-pepper objects: apple, tomato, etc.)        │
└──────┬──────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. BELL PEPPER DETECTION (YOLO Custom Model)                            │
│                                                                          │
│   For each detection:                                                   │
│     ├─ Check overlap with forbidden zones                               │
│     ├─ Validation Pipeline:                                            │
│     │   ├─ Shape validation (aspect ratio, size)                        │
│     │   ├─ Color validation (pepper color ranges)                     │
│     │   └─ Texture validation (circularity, vertices)                │
│     └─ Crop pepper region                                               │
└──────┬──────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 4. QUALITY ANALYSIS                                                     │
│                                                                          │
│   Primary: CV-based Quality Analyzer                                    │
│     ├─ Image Preprocessing (HSV conversion, masking)                   │
│     ├─ Color Uniformity Analysis                                        │
│     ├─ Size Consistency Analysis                                         │
│     ├─ Surface Quality Analysis (GLCM texture features)                │
│     └─ Ripeness Level Analysis                                          │
│                                                                          │
│   Fallback: ANFIS Quality Assessment                                    │
│     └─ Fuzzy inference system                                           │
└──────┬──────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 5. ADVANCED AI ANALYSIS                                                 │
│                                                                          │
│   ├─ Ripeness Prediction                                                │
│   │   ├─ Current stage (unripe/ripening/ripe)                          │
│   │   ├─ Days to optimal harvest                                       │
│   │   └─ Ripeness timeline                                             │
│   │                                                                      │
│   ├─ Shelf Life Estimation                                              │
│   │   ├─ Room temperature                                               │
│   │   ├─ Refrigerated                                                   │
│   │   └─ Optimal storage                                               │
│   │                                                                      │
│   ├─ Nutritional Analysis                                               │
│   │   ├─ Vitamin C, A, Folate                                          │
│   │   ├─ Antioxidants                                                   │
│   │   └─ Per pepper estimates                                           │
│   │                                                                      │
│   ├─ Variety Classification                                             │
│   │   └─ Match to known varieties                                       │
│   │                                                                      │
│   └─ Market Value Analysis                                              │
│       ├─ Price estimation (PHP/kg)                                      │
│       ├─ Grade classification                                            │
│       └─ Market recommendations                                         │
└──────┬──────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 6. DISEASE DETECTION (Optional)                                         │
│                                                                          │
│   If available:                                                         │
│     ├─ Disease detection (YOLO disease model)                          │
│     ├─ Health status assessment                                        │
│     └─ Treatment recommendations                                        │
└──────┬──────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 7. DATABASE STORAGE                                                     │
│                                                                          │
│   ├─ AnalysisHistory                                                    │
│   │   ├─ User ID                                                        │
│   │   ├─ Image path                                                     │
│   │   ├─ Result path                                                    │
│   │   ├─ Peppers found count                                            │
│   │   └─ Average quality                                                │
│   │                                                                      │
│   └─ BellPepperDetection                                                │
│       ├─ Detection info (variety, confidence)                          │
│       ├─ Quality metrics                                                │
│       ├─ Advanced analysis (JSON)                                       │
│       ├─ Disease analysis (JSON)                                        │
│       └─ Recommendations                                                │
└──────┬──────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 8. ANNOTATED IMAGE GENERATION                                           │
│                                                                          │
│   ├─ Draw labels with arrows                                            │
│   ├─ Color-code by quality score                                       │
│   └─ Save to results/                                                   │
└──────┬──────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 9. RESPONSE TO USER                                                     │
│                                                                          │
│   JSON Response:                                                        │
│     ├─ Result image URL                                                │
│     ├─ General objects list                                            │
│     ├─ Bell peppers list (with full analysis)                          │
│     └─ Summary statistics                                              │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Interaction Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          SYSTEM COMPONENTS                               │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│   Frontend   │
│  (HTML/JS)   │
└──────┬───────┘
       │ HTTP POST /upload
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Flask Application (app.py)                        │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ Routes:                                                            │ │
│  │  ├─ /upload          → Image processing                           │ │
│  │  ├─ /analyze         → Analysis page                               │ │
│  │  ├─ /dashboard       → User dashboard                              │ │
│  │  ├─ /history         → Analysis history                             │ │
│  │  └─ /results/<file>  → Serve result images                         │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ Models (YOLO):                                                      │ │
│  │  ├─ general_detection    → YOLOv8 COCO (80 classes)               │ │
│  │  ├─ bell_pepper_detection → YOLOv8 Custom (bell peppers)          │ │
│  │  └─ validation_pipeline  → Enhanced validation                    │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ Analysis Modules:                                                   │ │
│  │  ├─ pepper_quality_analyzer.py                                    │ │
│  │  │   └─ CV-based quality analysis                                  │ │
│  │  ├─ advanced_ai_analyzer.py                                       │ │
│  │  │   └─ Ripeness, shelf life, nutrition, variety, market           │ │
│  │  ├─ ANFISQualityAssessment (app.py)                               │ │
│  │  │   └─ Fuzzy inference fallback                                   │ │
│  │  └─ disease_detection/ (optional)                                  │ │
│  │      └─ Disease detection integration                              │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ Database (SQLAlchemy):                                              │ │
│  │  ├─ User                                                            │ │
│  │  ├─ AnalysisHistory                                                 │ │
│  │  ├─ BellPepperDetection                                             │ │
│  │  ├─ PepperVariety                                                   │ │
│  │  ├─ PepperDisease                                                   │ │
│  │  └─ Notification                                                    │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. Multi-Model Detection System
- **General Detection**: YOLO COCO model detects 80 object classes
- **Specialized Detection**: Custom YOLO model specifically trained for bell peppers
- **Smart Filtering**: Uses general detection to create "forbidden zones" preventing false positives

### 2. Quality Assessment
- **Color Uniformity**: Analyzes color consistency across the pepper
- **Size Consistency**: Evaluates shape regularity and aspect ratio
- **Surface Quality**: Uses GLCM texture analysis to detect defects
- **Ripeness Level**: Color-based ripeness assessment

### 3. Advanced AI Analysis
- **Ripeness Prediction**: Predicts optimal harvest time
- **Shelf Life Estimation**: Estimates storage duration under different conditions
- **Nutritional Analysis**: Estimates vitamin content and nutritional value
- **Variety Classification**: Identifies pepper variety
- **Market Value Analysis**: Provides pricing and grade recommendations

### 4. Disease Detection (Optional)
- Detects common bell pepper diseases
- Provides health status and treatment recommendations
- Calculates overall health score

### 5. Database & History
- Stores all analysis results
- Tracks individual pepper detections
- Provides history and statistics dashboard

## Technology Stack

- **Backend**: Flask (Python)
- **AI Models**: YOLO (Ultralytics)
- **Computer Vision**: OpenCV, scikit-image
- **Database**: SQLite (SQLAlchemy)
- **Frontend**: HTML, CSS, JavaScript
- **Analysis**: NumPy, scikit-learn

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (create `.env` file):
```
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///instance/pepperai.db
UPLOAD_FOLDER=uploads
RESULTS_FOLDER=results
```

3. Initialize database:
```bash
python setup.py
```

4. Run the application:
```bash
python app.py
```

## Usage

1. **Upload Image**: Navigate to `/analyze` and upload a bell pepper image
2. **Processing**: The system automatically:
   - Detects bell peppers
   - Analyzes quality
   - Provides comprehensive insights
3. **View Results**: Results are displayed with:
   - Annotated image
   - Quality scores
   - Recommendations
   - Advanced analysis data

## System Flow Summary

1. User uploads image via web interface
2. Image is saved to `uploads/` directory
3. Multi-stage detection pipeline processes the image:
   - General object detection identifies non-pepper objects
   - Bell pepper detection finds peppers
   - Validation filters false positives
4. For each detected pepper:
   - Quality analysis calculates metrics
   - Advanced AI provides comprehensive insights
   - Optional disease detection assesses health
5. Results are stored in database
6. Annotated image is generated
7. Results are returned to user

## Notes

- The system uses a **fully automated pipeline** - there is no manual expert review step
- All analysis is performed automatically using AI models and computer vision
- Results are stored immediately in the database for history tracking
- The system supports batch analysis of multiple peppers in a single image

