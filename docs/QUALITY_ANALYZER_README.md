# Bell Pepper Quality Analyzer

## Advanced Computer Vision Quality Analysis System

This implementation uses **OpenCV** and **scikit-image** to provide comprehensive bell pepper quality assessment with four key metrics:

### Quality Metrics Analyzed

1. **Color Uniformity** (0-100)
   - Analyzes color consistency across the pepper surface
   - Uses HSV color space analysis and K-means clustering
   - Higher scores indicate more uniform coloring

2. **Size Consistency** (0-100)
   - Evaluates shape regularity and proportions
   - Measures circularity, aspect ratio, and convexity
   - Bell peppers should have consistent, regular shapes

3. **Surface Quality** (0-100)
   - Detects defects, blemishes, and surface irregularities
   - Uses texture analysis (GLCM) and edge detection
   - Higher scores indicate smoother, defect-free surfaces

4. **Ripeness Level** (0-100)
   - Determines ripeness based on color characteristics
   - Analyzes green (unripe), yellow/orange (medium), red (ripe) ratios
   - Higher scores indicate greater ripeness

### Quality Categories

- **Excellent** (80-100): Premium quality, suitable for export
- **Good** (60-79): High quality, suitable for fresh market
- **Fair** (40-59): Medium quality, acceptable for most uses
- **Poor** (0-39): Lower quality, may need processing or alternative uses

### Technical Implementation

#### Libraries Used
- **OpenCV**: Image preprocessing, color analysis, contour detection
- **scikit-image**: Advanced texture analysis, morphological operations
- **scikit-learn**: K-means clustering for color analysis
- **NumPy**: Numerical computations and array operations

#### Key Features
- **Automatic pepper segmentation** from background
- **Multi-scale analysis** with padding for edge effects
- **Robust error handling** with fallback mechanisms
- **Comprehensive recommendations** based on analysis results

### Usage

#### Standalone Usage
```python
from pepper_quality_analyzer import BellPepperQualityAnalyzer
import cv2

# Initialize analyzer
analyzer = BellPepperQualityAnalyzer()

# Load image
image = cv2.imread('bell_pepper.jpg')

# Analyze quality
results = analyzer.analyze_pepper_quality(image)
recommendations = analyzer.get_quality_recommendations(results)

print(f"Quality Metrics: {results}")
print(f"Recommendations: {recommendations}")
```

#### Flask Integration
The analyzer is automatically integrated into the existing Flask application:

1. **Detection**: YOLOv8 detects bell peppers in uploaded images
2. **Cropping**: Detected peppers are cropped with padding
3. **Analysis**: Advanced CV analyzer processes each pepper
4. **Fallback**: ANFIS system provides backup analysis if needed

### Installation

Install required dependencies:
```bash
pip install -r requirements.txt
```

### Algorithm Details

#### Color Uniformity Analysis
- Converts image to HSV color space
- Calculates hue and saturation standard deviation
- Performs K-means clustering to identify dominant colors
- Computes entropy-based uniformity score

#### Size Consistency Analysis
- Extracts contours using morphological operations
- Calculates circularity: 4π×area/perimeter²
- Measures aspect ratio and convexity
- Combines metrics for overall consistency score

#### Surface Quality Analysis
- Gray Level Co-occurrence Matrix (GLCM) for texture features
- Edge detection using Canny algorithm
- Local variance analysis for smoothness assessment
- Defect density calculation

#### Ripeness Level Analysis
- HSV color space segmentation
- Color range classification:
  - Green: H=40-80 (unripe)
  - Yellow/Orange: H=10-40 (medium ripe)
  - Red: H=0-10 or 170-180 (fully ripe)
- Pixel ratio analysis and uniformity bonus

### Performance Notes

- **Processing Time**: ~0.5-2 seconds per pepper (depending on image size)
- **Accuracy**: Optimized for bell pepper characteristics
- **Memory Usage**: Efficient with automatic cleanup
- **Scalability**: Designed for batch processing

### Recommendations System

The analyzer provides contextual recommendations based on quality scores:

- **Quality improvement suggestions**
- **Harvest timing recommendations**
- **Market suitability assessment**
- **Processing alternatives for lower grades**

### Future Enhancements

Potential improvements for the system:
- **Disease detection** integration
- **Variety-specific analysis** parameters
- **Batch processing** optimization
- **Machine learning model** training on quality data
