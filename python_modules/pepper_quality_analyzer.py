import cv2
import numpy as np
from sklearn.cluster import KMeans
from skimage import measure, feature, filters, segmentation
try:
    from skimage.feature import graycomatrix, graycoprops
except ImportError:
    try:
        from skimage.feature import greycomatrix as graycomatrix, greycoprops as graycoprops
    except ImportError:
        # If neither import works, we'll handle it gracefully
        graycomatrix = None
        graycoprops = None
from skimage.measure import regionprops
from skimage.morphology import remove_small_objects
import math
from typing import Dict, Tuple, List

class BellPepperQualityAnalyzer:
    """
    Advanced Bell Pepper Quality Analysis using Computer Vision
    Analyzes: Color Uniformity, Size Consistency, Surface Quality, Ripeness Level
    """
    
    def __init__(self):
        self.min_pepper_area = 1000  # Minimum area for a valid pepper region
        self.color_clusters = 5      # Number of color clusters for analysis
        
    def preprocess_image(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Preprocess the image and create a mask for the bell pepper
        """
        # Convert to different color spaces for analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        
        # Create mask to isolate bell pepper from background
        # Focus on typical bell pepper colors (green, red, yellow, orange)
        lower_bound = np.array([0, 30, 30])
        upper_bound = np.array([180, 255, 255])
        mask = cv2.inRange(hsv, lower_bound, upper_bound)
        
        # Remove noise and fill gaps
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Find largest contour (main pepper)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            mask = np.zeros_like(mask)
            cv2.fillPoly(mask, [largest_contour], 255)
        
        return hsv, mask
    
    def analyze_color_uniformity(self, image: np.ndarray, mask: np.ndarray) -> float:
        """
        Analyze color uniformity of the bell pepper
        Returns score 0-100 (higher = more uniform)
        """
        # Extract pepper region
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        pepper_pixels = hsv[mask > 0]
        
        if len(pepper_pixels) == 0:
            return 0.0
        
        # Analyze hue uniformity (most important for color consistency)
        hue_values = pepper_pixels[:, 0]
        hue_std = np.std(hue_values)
        
        # Analyze saturation uniformity
        sat_values = pepper_pixels[:, 1]
        sat_std = np.std(sat_values)
        
        # K-means clustering to find dominant colors
        try:
            kmeans = KMeans(n_clusters=min(self.color_clusters, len(pepper_pixels)//10), random_state=42, n_init=10)
            clusters = kmeans.fit_predict(pepper_pixels)
            
            # Calculate cluster distribution uniformity
            unique, counts = np.unique(clusters, return_counts=True)
            cluster_distribution = counts / len(clusters)
            uniformity_entropy = -np.sum(cluster_distribution * np.log2(cluster_distribution + 1e-10))
            max_entropy = np.log2(len(unique))
            cluster_uniformity = uniformity_entropy / max_entropy if max_entropy > 0 else 0
            
        except:
            cluster_uniformity = 0.5
        
        # Combine metrics (lower std = higher uniformity)
        hue_uniformity = max(0, 1 - (hue_std / 50))  # Normalize hue std
        sat_uniformity = max(0, 1 - (sat_std / 100))  # Normalize saturation std
        
        # Final score combining all factors
        color_uniformity_score = (hue_uniformity * 0.5 + sat_uniformity * 0.3 + cluster_uniformity * 0.2) * 100
        return min(100, max(0, color_uniformity_score))
    
    def analyze_size_consistency(self, image: np.ndarray, mask: np.ndarray) -> float:
        """
        Analyze size consistency and shape regularity
        Returns score 0-100 (higher = more consistent)
        """
        # Find contours for shape analysis
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return 0.0
        
        main_contour = max(contours, key=cv2.contourArea)
        
        # Calculate shape metrics
        area = cv2.contourArea(main_contour)
        perimeter = cv2.arcLength(main_contour, True)
        
        if perimeter == 0:
            return 0.0
        
        # Circularity (4π*area/perimeter²) - bell peppers should be somewhat circular
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        circularity_score = min(1.0, circularity)  # Closer to 1 = more circular
        
        # Aspect ratio consistency
        x, y, w, h = cv2.boundingRect(main_contour)
        aspect_ratio = w / h if h > 0 else 0
        # Bell peppers typically have aspect ratio between 0.6-1.4
        ideal_aspect_range = (0.6, 1.4)
        if ideal_aspect_range[0] <= aspect_ratio <= ideal_aspect_range[1]:
            aspect_score = 1.0
        else:
            aspect_score = max(0, 1 - abs(aspect_ratio - 1.0))
        
        # Convexity (how close the shape is to its convex hull)
        hull = cv2.convexHull(main_contour)
        hull_area = cv2.contourArea(hull)
        convexity = area / hull_area if hull_area > 0 else 0
        
        # Combine metrics
        size_consistency_score = (circularity_score * 0.4 + aspect_score * 0.4 + convexity * 0.2) * 100
        return min(100, max(0, size_consistency_score))
    
    def analyze_surface_quality(self, image: np.ndarray, mask: np.ndarray) -> float:
        """
        Analyze surface quality (smoothness, defects, blemishes)
        Returns score 0-100 (higher = better surface quality)
        """
        # Convert to grayscale for texture analysis
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        pepper_region = gray * (mask // 255)
        
        if np.sum(mask) == 0:
            return 0.0
        
        # Texture analysis using Gray Level Co-occurrence Matrix (GLCM)
        texture_score = 0.5  # Default fallback score
        
        if graycomatrix is not None and graycoprops is not None:
            try:
                # Reduce image to 64 levels for faster GLCM computation
                pepper_region_reduced = (pepper_region // 4).astype(np.uint8)
                
                # Calculate GLCM for texture features
                glcm = graycomatrix(pepper_region_reduced, [1], [0, 45, 90, 135], levels=64, symmetric=True, normed=True)
                
                # Extract texture features
                contrast = graycoprops(glcm, 'contrast').mean()
                homogeneity = graycoprops(glcm, 'homogeneity').mean()
                energy = graycoprops(glcm, 'energy').mean()
                correlation = graycoprops(glcm, 'correlation').mean()
                
                # Higher homogeneity and energy = smoother surface
                # Lower contrast = fewer defects
                texture_score = (homogeneity * 0.4 + energy * 0.3 + (1 - min(contrast/100, 1)) * 0.3)
                
            except Exception as e:
                print(f"GLCM analysis failed, using fallback: {e}")
                # Use simpler texture analysis as fallback
                texture_score = self._simple_texture_analysis(pepper_region)
        else:
            # Use alternative texture analysis when GLCM is not available
            texture_score = self._simple_texture_analysis(pepper_region)
        
        # Edge density analysis for defect detection
        edges = cv2.Canny(pepper_region, 30, 100)
        edge_density = np.sum(edges[mask > 0]) / np.sum(mask > 0) if np.sum(mask > 0) > 0 else 0
        edge_score = max(0, 1 - (edge_density / 50))  # Normalize edge density
        
        # Local variance analysis for surface smoothness
        kernel = np.ones((5, 5), np.float32) / 25
        mean_filtered = cv2.filter2D(pepper_region.astype(np.float32), -1, kernel)
        variance = (pepper_region.astype(np.float32) - mean_filtered) ** 2
        local_variance = np.mean(variance[mask > 0]) if np.sum(mask > 0) > 0 else 0
        variance_score = max(0, 1 - (local_variance / 1000))
        
        # Combine surface quality metrics
        surface_quality_score = (texture_score * 0.5 + edge_score * 0.3 + variance_score * 0.2) * 100
        return min(100, max(0, surface_quality_score))
    
    def analyze_ripeness_level(self, image: np.ndarray, mask: np.ndarray) -> float:
        """
        Analyze ripeness level based on color characteristics
        Returns score 0-100 (higher = more ripe)
        """
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        pepper_pixels = hsv[mask > 0]
        
        if len(pepper_pixels) == 0:
            return 0.0
        
        hue_values = pepper_pixels[:, 0]
        sat_values = pepper_pixels[:, 1]
        val_values = pepper_pixels[:, 2]
        
        # Count pixels in different ripeness categories
        total_pixels = len(pepper_pixels)
        
        # Green pixels (unripe)
        green_mask = ((hue_values >= 40) & (hue_values <= 80) & 
                     (sat_values >= 50) & (val_values >= 50))
        green_ratio = np.sum(green_mask) / total_pixels
        
        # Yellow/Orange pixels (medium ripe)
        yellow_mask = ((hue_values >= 10) & (hue_values <= 40) & 
                      (sat_values >= 50) & (val_values >= 50))
        yellow_ratio = np.sum(yellow_mask) / total_pixels
        
        # Red pixels (fully ripe)
        red_mask = (((hue_values >= 0) & (hue_values <= 10)) | 
                   ((hue_values >= 170) & (hue_values <= 180))) & \
                   (sat_values >= 50) & (val_values >= 50)
        red_ratio = np.sum(red_mask) / total_pixels
        
        # Calculate ripeness score
        # Green = 0-30, Yellow = 30-70, Red = 70-100
        ripeness_score = (green_ratio * 15 +     # Green contributes less to ripeness
                         yellow_ratio * 50 +     # Yellow is medium ripeness
                         red_ratio * 85)         # Red is high ripeness
        
        # Boost score if predominantly one color (more uniform ripeness)
        dominant_color_ratio = max(green_ratio, yellow_ratio, red_ratio)
        uniformity_bonus = dominant_color_ratio * 15
        
        final_ripeness_score = min(100, ripeness_score + uniformity_bonus)
        return max(0, final_ripeness_score)
    
    def _simple_texture_analysis(self, pepper_region: np.ndarray) -> float:
        """
        Simple texture analysis fallback when GLCM is not available
        """
        if pepper_region.size == 0:
            return 0.5
        
        # Calculate local standard deviation as texture measure
        kernel_size = 5
        kernel = np.ones((kernel_size, kernel_size), np.float32) / (kernel_size * kernel_size)
        
        # Convert to float for calculations
        img_float = pepper_region.astype(np.float32)
        
        # Calculate local mean
        local_mean = cv2.filter2D(img_float, -1, kernel)
        
        # Calculate local variance
        local_sq_mean = cv2.filter2D(img_float * img_float, -1, kernel)
        local_variance = local_sq_mean - local_mean * local_mean
        
        # Average variance across the region (excluding background)
        mask_region = pepper_region > 0
        if np.sum(mask_region) > 0:
            avg_variance = np.mean(local_variance[mask_region])
            # Lower variance = smoother texture = higher quality
            texture_score = max(0, 1 - (avg_variance / 1000))
        else:
            texture_score = 0.5
        
        return texture_score
    
    def analyze_pepper_quality(self, image: np.ndarray) -> Dict[str, float]:
        """
        Complete quality analysis of a bell pepper image
        Returns dictionary with all quality metrics
        """
        if image is None or image.size == 0:
            return {
                'color_uniformity': 0.0,
                'size_consistency': 0.0, 
                'surface_quality': 0.0,
                'ripeness_level': 0.0,
                'overall_quality': 0.0
            }
        
        # Preprocess image
        hsv, mask = self.preprocess_image(image)
        
        # Analyze each quality aspect
        color_uniformity = self.analyze_color_uniformity(image, mask)
        size_consistency = self.analyze_size_consistency(image, mask)
        surface_quality = self.analyze_surface_quality(image, mask)
        ripeness_level = self.analyze_ripeness_level(image, mask)
        
        # Calculate overall quality score (weighted average)
        overall_quality = (color_uniformity * 0.25 + 
                          size_consistency * 0.25 + 
                          surface_quality * 0.30 + 
                          ripeness_level * 0.20)
        
        return {
            'color_uniformity': round(color_uniformity, 1),
            'size_consistency': round(size_consistency, 1),
            'surface_quality': round(surface_quality, 1),
            'ripeness_level': round(ripeness_level, 1),
            'overall_quality': round(overall_quality, 1)
        }
    
    def get_quality_recommendations(self, metrics: Dict[str, float]) -> List[str]:
        """
        Generate recommendations based on quality metrics
        """
        recommendations = []
        
        if metrics['color_uniformity'] < 60:
            recommendations.append("Consider grading as second quality due to color inconsistency")
        
        if metrics['size_consistency'] < 50:
            recommendations.append("Shape irregularities detected - may affect market value")
        
        if metrics['surface_quality'] < 70:
            recommendations.append("Surface defects detected - inspect for damage or disease")
        
        if metrics['ripeness_level'] < 30:
            recommendations.append("Allow more time to ripen for better market value")
        elif metrics['ripeness_level'] > 85:
            recommendations.append("Optimal ripeness achieved - harvest soon for best quality")
        
        if metrics['overall_quality'] > 80:
            recommendations.append("Excellent quality - suitable for premium market")
        elif metrics['overall_quality'] < 50:
            recommendations.append("Consider alternative uses or processing applications")
        
        if not recommendations:
            recommendations.append("Good quality bell pepper suitable for fresh market")
        
        return recommendations


# Example usage function
def analyze_pepper_from_file(image_path: str) -> Dict:
    """
    Analyze a bell pepper from an image file
    """
    analyzer = BellPepperQualityAnalyzer()
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image from {image_path}")
    
    # Analyze quality
    metrics = analyzer.analyze_pepper_quality(image)
    recommendations = analyzer.get_quality_recommendations(metrics)
    
    return {
        'metrics': metrics,
        'recommendations': recommendations
    }
