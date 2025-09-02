"""
Integration module for disease detection with existing Flask app
"""

import cv2
import numpy as np
from typing import Dict, List, Optional
from .bell_pepper_disease_detector import BellPepperDiseaseDetector

class PepperHealthAnalyzer:
    """
    Complete health analysis combining quality assessment and disease detection
    """
    
    def __init__(self, disease_model_path: Optional[str] = None):
        # Initialize disease detector
        try:
            self.disease_detector = BellPepperDiseaseDetector(disease_model_path)
            print("✅ Disease detector initialized")
        except Exception as e:
            print(f"❌ Disease detector failed to initialize: {e}")
            self.disease_detector = None
    
    def analyze_pepper_health(self, pepper_crop: np.ndarray, quality_metrics: Dict) -> Dict:
        """
        Complete health analysis combining quality and disease detection
        
        Args:
            pepper_crop: Cropped pepper image
            quality_metrics: Quality analysis results from existing system
            
        Returns:
            Combined health analysis results
        """
        result = {
            'quality_analysis': quality_metrics,
            'disease_analysis': None,
            'overall_health_score': 0,
            'health_recommendations': []
        }
        
        # Disease detection
        if self.disease_detector and pepper_crop.size > 0:
            try:
                disease_result = self.disease_detector.detect_disease(pepper_crop)
                result['disease_analysis'] = disease_result
                
                # Calculate overall health score
                quality_score = quality_metrics.get('quality_score', 50)
                disease_confidence = disease_result.get('confidence', 0)
                is_healthy = disease_result.get('is_healthy', False)
                
                if is_healthy:
                    # If healthy, base score on quality metrics
                    health_penalty = 0
                else:
                    # Apply penalty based on disease severity
                    severity = disease_result.get('severity', 'Medium')
                    severity_penalties = {
                        'None': 0,
                        'Medium': 20,
                        'High': 40,
                        'Very High': 60
                    }
                    health_penalty = severity_penalties.get(severity, 30)
                
                # Overall health score (0-100)
                overall_health = max(0, min(100, quality_score - health_penalty))
                result['overall_health_score'] = round(overall_health, 1)
                
                # Generate comprehensive recommendations
                recommendations = self._generate_health_recommendations(
                    quality_metrics, disease_result, overall_health
                )
                result['health_recommendations'] = recommendations
                
            except Exception as e:
                print(f"Disease analysis error: {e}")
                result['disease_analysis'] = {'error': str(e)}
                result['overall_health_score'] = quality_metrics.get('quality_score', 50)
        else:
            # No disease detection available, use quality score
            result['overall_health_score'] = quality_metrics.get('quality_score', 50)
        
        return result
    
    def _generate_health_recommendations(self, quality_metrics: Dict, disease_result: Dict, health_score: float) -> List[str]:
        """Generate comprehensive health recommendations"""
        recommendations = []
        
        # Quality-based recommendations
        if quality_metrics.get('surface_quality', 100) < 70:
            recommendations.append("Surface quality issues detected - inspect for physical damage")
        
        if quality_metrics.get('color_uniformity', 100) < 60:
            recommendations.append("Color inconsistency may indicate uneven ripening or stress")
        
        # Disease-based recommendations
        if not disease_result.get('is_healthy', True):
            disease_name = disease_result.get('disease', 'Unknown')
            treatment = disease_result.get('treatment', '')
            
            recommendations.append(f"Disease detected: {disease_name}")
            if treatment:
                recommendations.append(f"Treatment: {treatment}")
        
        # Overall health recommendations
        if health_score >= 80:
            recommendations.append("Excellent health - suitable for premium market")
        elif health_score >= 60:
            recommendations.append("Good health - monitor for any changes")
        elif health_score >= 40:
            recommendations.append("Fair health - may require intervention")
        else:
            recommendations.append("Poor health - immediate action recommended")
        
        return recommendations
    
    def batch_analyze_peppers(self, pepper_crops: List[np.ndarray], quality_results: List[Dict]) -> Dict:
        """
        Analyze multiple peppers and provide batch insights
        """
        if len(pepper_crops) != len(quality_results):
            raise ValueError("Number of crops must match number of quality results")
        
        individual_results = []
        disease_summary = {}
        health_scores = []
        
        for i, (crop, quality) in enumerate(zip(pepper_crops, quality_results)):
            # Analyze individual pepper
            health_analysis = self.analyze_pepper_health(crop, quality)
            health_analysis['pepper_id'] = f"pepper_{i+1}"
            individual_results.append(health_analysis)
            
            # Track statistics
            health_scores.append(health_analysis['overall_health_score'])
            
            # Track diseases
            disease_analysis = health_analysis.get('disease_analysis')
            if disease_analysis and not disease_analysis.get('error'):
                disease = disease_analysis.get('disease', 'Unknown')
                disease_summary[disease] = disease_summary.get(disease, 0) + 1
        
        # Calculate batch statistics
        avg_health = np.mean(health_scores) if health_scores else 0
        
        # Determine batch risk level
        healthy_count = disease_summary.get('Healthy', 0)
        total_peppers = len(pepper_crops)
        health_percentage = (healthy_count / total_peppers * 100) if total_peppers > 0 else 0
        
        if health_percentage >= 90:
            batch_risk = 'Very Low'
        elif health_percentage >= 75:
            batch_risk = 'Low'
        elif health_percentage >= 50:
            batch_risk = 'Medium'
        elif health_percentage >= 25:
            batch_risk = 'High'
        else:
            batch_risk = 'Critical'
        
        # Generate batch recommendations
        batch_recommendations = []
        
        if batch_risk in ['High', 'Critical']:
            batch_recommendations.append("Immediate inspection and treatment required")
            batch_recommendations.append("Consider quarantine measures")
        
        if 'Mosaic_Virus' in disease_summary:
            batch_recommendations.append("Viral infection detected - implement vector control")
        
        if 'Bacterial_Spot' in disease_summary:
            batch_recommendations.append("Bacterial infection present - apply copper treatment")
        
        return {
            'individual_results': individual_results,
            'batch_statistics': {
                'total_peppers': total_peppers,
                'average_health_score': round(avg_health, 1),
                'health_percentage': round(health_percentage, 1),
                'disease_distribution': disease_summary,
                'batch_risk_level': batch_risk
            },
            'batch_recommendations': batch_recommendations
        }


# Flask integration functions
def add_disease_detection_to_flask_result(pepper_data: Dict, pepper_crop: np.ndarray, analyzer: PepperHealthAnalyzer) -> Dict:
    """
    Add disease detection to existing Flask pepper analysis result
    """
    if 'quality_analysis' in pepper_data and analyzer.disease_detector:
        try:
            # Get comprehensive health analysis
            health_analysis = analyzer.analyze_pepper_health(
                pepper_crop, 
                pepper_data['quality_analysis']
            )
            
            # Add disease information to existing result
            pepper_data['disease_analysis'] = health_analysis['disease_analysis']
            pepper_data['overall_health_score'] = health_analysis['overall_health_score']
            pepper_data['health_recommendations'] = health_analysis['health_recommendations']
            
            # Update quality analysis recommendations with health recommendations
            if 'recommendations' in pepper_data['quality_analysis']:
                # Combine quality and health recommendations
                all_recommendations = (
                    pepper_data['quality_analysis']['recommendations'] + 
                    health_analysis['health_recommendations']
                )
                pepper_data['quality_analysis']['recommendations'] = list(set(all_recommendations))
            
        except Exception as e:
            print(f"Disease detection integration error: {e}")
            pepper_data['disease_analysis'] = {'error': str(e)}
    
    return pepper_data


# Training data preparation helper
def prepare_disease_training_data(data_dir: str) -> Dict:
    """
    Helper function to prepare training data for disease detection model
    
    Expected directory structure:
    data_dir/
    ├── Healthy/
    ├── Bacterial_Spot/
    ├── Blossom_End_Rot/
    ├── Anthracnose/
    └── Mosaic_Virus/
    """
    import os
    from torch.utils.data import Dataset
    from PIL import Image
    
    class DiseaseDataset(Dataset):
        def __init__(self, data_dir, transform=None):
            self.data_dir = data_dir
            self.transform = transform
            self.images = []
            self.labels = []
            
            disease_classes = {
                'Healthy': 0,
                'Bacterial_Spot': 1,
                'Blossom_End_Rot': 2,
                'Anthracnose': 3,
                'Mosaic_Virus': 4
            }
            
            for disease, label in disease_classes.items():
                disease_dir = os.path.join(data_dir, disease)
                if os.path.exists(disease_dir):
                    for img_name in os.listdir(disease_dir):
                        if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                            self.images.append(os.path.join(disease_dir, img_name))
                            self.labels.append(label)
        
        def __len__(self):
            return len(self.images)
        
        def __getitem__(self, idx):
            image = Image.open(self.images[idx]).convert('RGB')
            label = self.labels[idx]
            
            if self.transform:
                image = self.transform(image)
            
            return image, label
    
    return DiseaseDataset


# Example usage
if __name__ == "__main__":
    # Initialize health analyzer
    analyzer = PepperHealthAnalyzer()
    
    # Example with dummy data
    pepper_crop = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    quality_metrics = {
        'quality_score': 75.0,
        'color_uniformity': 80.0,
        'size_consistency': 70.0,
        'surface_quality': 75.0,
        'ripeness_level': 80.0
    }
    
    # Analyze health
    health_result = analyzer.analyze_pepper_health(pepper_crop, quality_metrics)
    print("Health Analysis Result:", health_result)
