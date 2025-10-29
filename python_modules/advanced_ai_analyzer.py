"""
Advanced AI Analyzer for Bell Peppers
Includes ripeness prediction, shelf life estimation, nutritional analysis, and variety classification
"""

import cv2
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import math

class AdvancedPepperAnalyzer:
    """
    Advanced AI analysis for bell peppers including:
    - Ripeness prediction and timeline
    - Shelf life estimation  
    - Nutritional content analysis
    - Variety classification
    - Market value estimation
    """
    
    def __init__(self):
        self.pepper_varieties = {
            'california_wonder': {
                'shape_ratio': (0.8, 1.2),
                'color_profile': 'green_to_red',
                'size_range': (80, 120),
                'market_value': 1.0
            },
            'king_arthur': {
                'shape_ratio': (0.9, 1.3),
                'color_profile': 'deep_red',
                'size_range': (100, 140),
                'market_value': 1.2
            },
            'yellow_bell': {
                'shape_ratio': (0.85, 1.15),
                'color_profile': 'yellow',
                'size_range': (70, 110),
                'market_value': 1.1
            },
            'orange_bell': {
                'shape_ratio': (0.8, 1.1),
                'color_profile': 'orange',
                'size_range': (75, 115),
                'market_value': 1.15
            },
            'mini_sweet': {
                'shape_ratio': (0.7, 1.0),
                'color_profile': 'mixed',
                'size_range': (30, 60),
                'market_value': 1.3
            }
        }
        
        # Nutritional base values per 100g
        self.base_nutrition = {
            'calories': 31,
            'vitamin_c': 120,  # mg
            'vitamin_a': 3131,  # IU
            'folate': 10,  # mcg
            'potassium': 211,  # mg
            'fiber': 2.5,  # g
            'antioxidants': 100  # relative scale
        }
    
    def analyze_advanced_features(self, pepper_crop: np.ndarray, quality_metrics: Dict) -> Dict:
        """
        Perform comprehensive advanced analysis
        """
        try:
            # Get basic measurements
            height, width = pepper_crop.shape[:2]
            
            # Advanced analyses
            ripeness_analysis = self._analyze_ripeness_prediction(pepper_crop, quality_metrics)
            shelf_life = self._estimate_shelf_life(quality_metrics, ripeness_analysis)
            nutrition = self._analyze_nutritional_content(pepper_crop, quality_metrics, ripeness_analysis)
            variety = self._classify_variety(pepper_crop, quality_metrics)
            market_analysis = self._analyze_market_value(quality_metrics, variety, ripeness_analysis)
            
            return {
                'ripeness_prediction': ripeness_analysis,
                'shelf_life_estimation': shelf_life,
                'nutritional_analysis': nutrition,
                'variety_classification': variety,
                'market_analysis': market_analysis,
                'advanced_recommendations': self._get_advanced_recommendations(
                    ripeness_analysis, shelf_life, nutrition, variety
                )
            }
            
        except Exception as e:
            print(f"Advanced analysis error: {e}")
            return self._get_fallback_analysis()
    
    def _analyze_ripeness_prediction(self, pepper_crop: np.ndarray, quality_metrics: Dict) -> Dict:
        """
        Predict ripeness progression and optimal harvest time
        """
        # Convert to HSV for color analysis
        hsv = cv2.cvtColor(pepper_crop, cv2.COLOR_BGR2HSV)
        
        # Analyze color distribution
        h_mean = np.mean(hsv[:, :, 0])
        s_mean = np.mean(hsv[:, :, 1])
        v_mean = np.mean(hsv[:, :, 2])
        
        # Color-based ripeness classification
        if h_mean > 40 and h_mean < 80:  # Green range
            current_stage = 'unripe'
            ripeness_percent = 20 + (s_mean / 255) * 30
            days_to_optimal = 7 + (50 - ripeness_percent) * 0.2
        elif h_mean > 15 and h_mean < 40:  # Yellow/Orange range
            current_stage = 'ripening'
            ripeness_percent = 50 + (s_mean / 255) * 30
            days_to_optimal = 3 + (80 - ripeness_percent) * 0.1
        elif h_mean < 15 or h_mean > 170:  # Red range
            current_stage = 'ripe'
            ripeness_percent = 80 + (s_mean / 255) * 20
            days_to_optimal = max(0, (100 - ripeness_percent) * 0.05)
        else:
            current_stage = 'transitional'
            ripeness_percent = 60
            days_to_optimal = 2
        
        # Factor in surface quality for ripeness accuracy
        surface_factor = quality_metrics.get('surface_quality', 50) / 100
        ripeness_percent *= (0.7 + 0.3 * surface_factor)
        
        # Predict future stages
        stages_timeline = self._calculate_ripeness_timeline(current_stage, days_to_optimal)
        
        return {
            'current_stage': current_stage,
            'ripeness_percentage': round(ripeness_percent, 1),
            'days_to_optimal_harvest': round(days_to_optimal, 1),
            'color_analysis': {
                'hue_mean': round(h_mean, 1),
                'saturation_mean': round(s_mean, 1),
                'brightness_mean': round(v_mean, 1)
            },
            'stages_timeline': stages_timeline,
            'harvest_recommendation': self._get_harvest_recommendation(ripeness_percent, current_stage)
        }
    
    def _calculate_ripeness_timeline(self, current_stage: str, days_to_optimal: float) -> List[Dict]:
        """
        Calculate timeline of ripeness stages
        """
        timeline = []
        stages = ['unripe', 'ripening', 'ripe', 'overripe']
        current_index = stages.index(current_stage) if current_stage in stages else 0
        
        base_date = datetime.now()
        
        for i, stage in enumerate(stages):
            if i < current_index:
                timeline.append({
                    'stage': stage,
                    'date': 'completed',
                    'days_from_now': 'past'
                })
            elif i == current_index:
                timeline.append({
                    'stage': stage,
                    'date': base_date.strftime('%Y-%m-%d'),
                    'days_from_now': 0
                })
            else:
                days_ahead = days_to_optimal + (i - current_index - 1) * 3
                future_date = base_date + timedelta(days=days_ahead)
                timeline.append({
                    'stage': stage,
                    'date': future_date.strftime('%Y-%m-%d'),
                    'days_from_now': round(days_ahead, 1)
                })
        
        return timeline
    
    def _estimate_shelf_life(self, quality_metrics: Dict, ripeness_analysis: Dict) -> Dict:
        """
        Estimate shelf life based on current condition and storage methods
        """
        base_shelf_life = 7  # days for optimal peppers
        
        # Factors affecting shelf life
        quality_factor = quality_metrics.get('overall_quality', 50) / 100
        surface_factor = quality_metrics.get('surface_quality', 50) / 100
        ripeness_factor = min(1.0, ripeness_analysis['ripeness_percentage'] / 80)
        
        # Calculate shelf life for different storage conditions
        room_temp_days = base_shelf_life * quality_factor * surface_factor * (2 - ripeness_factor)
        refrigerated_days = room_temp_days * 2.5
        optimal_storage_days = room_temp_days * 3.5
        
        # Calculate spoilage progression
        spoilage_rate = self._calculate_spoilage_rate(quality_metrics, ripeness_analysis)
        
        return {
            'room_temperature': {
                'days': round(max(1, room_temp_days), 1),
                'condition_after': self._predict_condition_after(room_temp_days, spoilage_rate)
            },
            'refrigerated': {
                'days': round(max(2, refrigerated_days), 1),
                'condition_after': self._predict_condition_after(refrigerated_days, spoilage_rate * 0.4)
            },
            'optimal_storage': {
                'days': round(max(3, optimal_storage_days), 1),
                'condition_after': self._predict_condition_after(optimal_storage_days, spoilage_rate * 0.3),
                'storage_tips': [
                    'Store in crisper drawer at 45-50°F (7-10°C)',
                    'Maintain 85-90% humidity',
                    'Keep away from ethylene-producing fruits',
                    'Store in perforated plastic bags'
                ]
            },
            'spoilage_indicators': [
                'Soft spots or wrinkling',
                'Color changes (darkening)',
                'Mold growth',
                'Slimy texture',
                'Off odors'
            ]
        }
    
    def _calculate_spoilage_rate(self, quality_metrics: Dict, ripeness_analysis: Dict) -> float:
        """
        Calculate the rate of spoilage per day
        """
        base_rate = 0.1  # 10% quality loss per day baseline
        
        # Higher ripeness = faster spoilage
        ripeness_multiplier = 1 + (ripeness_analysis['ripeness_percentage'] / 100) * 0.5
        
        # Lower surface quality = faster spoilage
        surface_multiplier = 2 - (quality_metrics.get('surface_quality', 50) / 100)
        
        return base_rate * ripeness_multiplier * surface_multiplier
    
    def _predict_condition_after(self, days: float, spoilage_rate: float) -> str:
        """
        Predict condition after specified days
        """
        quality_loss = spoilage_rate * days * 100
        remaining_quality = max(0, 100 - quality_loss)
        
        if remaining_quality > 80:
            return 'Excellent condition'
        elif remaining_quality > 60:
            return 'Good condition'
        elif remaining_quality > 40:
            return 'Fair condition'
        elif remaining_quality > 20:
            return 'Poor condition, use soon'
        else:
            return 'Likely spoiled'
    
    def _analyze_nutritional_content(self, pepper_crop: np.ndarray, quality_metrics: Dict, ripeness_analysis: Dict) -> Dict:
        """
        Estimate nutritional content based on visual analysis
        """
        # Base nutritional values
        nutrition = self.base_nutrition.copy()
        
        # Color affects nutritional content
        hsv = cv2.cvtColor(pepper_crop, cv2.COLOR_BGR2HSV)
        h_mean = np.mean(hsv[:, :, 0])
        
        # Red peppers have more vitamin A and C
        if h_mean < 15 or h_mean > 170:  # Red
            nutrition['vitamin_c'] *= 1.5
            nutrition['vitamin_a'] *= 2.0
            nutrition['antioxidants'] *= 1.8
        elif h_mean > 15 and h_mean < 40:  # Yellow/Orange
            nutrition['vitamin_c'] *= 1.3
            nutrition['vitamin_a'] *= 1.5
            nutrition['antioxidants'] *= 1.4
        # Green peppers keep base values
        
        # Quality affects nutrient retention
        quality_factor = quality_metrics.get('overall_quality', 50) / 100
        for key in ['vitamin_c', 'vitamin_a', 'antioxidants']:
            nutrition[key] *= (0.7 + 0.3 * quality_factor)
        
        # Ripeness affects some nutrients
        ripeness_factor = ripeness_analysis['ripeness_percentage'] / 100
        nutrition['vitamin_c'] *= (0.8 + 0.4 * ripeness_factor)
        nutrition['antioxidants'] *= (0.7 + 0.5 * ripeness_factor)
        
        # Estimate serving size based on pepper size
        estimated_weight = self._estimate_pepper_weight(pepper_crop)
        serving_nutrition = {}
        for key, value in nutrition.items():
            serving_nutrition[key] = round(value * (estimated_weight / 100), 1)
        
        return {
            'per_100g': {k: round(v, 1) for k, v in nutrition.items()},
            'per_pepper': serving_nutrition,
            'estimated_weight_g': estimated_weight,
            'nutritional_highlights': self._get_nutritional_highlights(nutrition, h_mean),
            'health_benefits': self._get_health_benefits(nutrition)
        }
    
    def _estimate_pepper_weight(self, pepper_crop: np.ndarray) -> float:
        """
        Estimate pepper weight based on visual size
        """
        # Calculate pepper area in pixels
        gray = cv2.cvtColor(pepper_crop, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            area_pixels = cv2.contourArea(largest_contour)
            # Rough estimation: 1000 pixels ≈ 100g (this would need calibration)
            estimated_weight = max(50, min(200, area_pixels / 10))
        else:
            estimated_weight = 120  # Average bell pepper weight
        
        return round(estimated_weight, 1)
    
    def _classify_variety(self, pepper_crop: np.ndarray, quality_metrics: Dict) -> Dict:
        """
        Classify bell pepper variety based on visual characteristics
        """
        hsv = cv2.cvtColor(pepper_crop, cv2.COLOR_BGR2HSV)
        h_mean = np.mean(hsv[:, :, 0])
        
        # Calculate shape ratio
        gray = cv2.cvtColor(pepper_crop, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape
        shape_ratio = height / width if width > 0 else 1.0
        
        # Estimate size
        estimated_size = math.sqrt(height * width) / 10  # Rough size estimation
        
        # Color classification
        if h_mean > 40 and h_mean < 80:
            color_type = 'green'
        elif h_mean > 15 and h_mean < 40:
            color_type = 'yellow' if h_mean > 25 else 'orange'
        elif h_mean < 15 or h_mean > 170:
            color_type = 'red'
        else:
            color_type = 'mixed'
        
        # Variety matching
        best_match = 'california_wonder'  # default
        best_score = 0
        
        for variety, characteristics in self.pepper_varieties.items():
            score = 0
            
            # Shape matching
            if characteristics['shape_ratio'][0] <= shape_ratio <= characteristics['shape_ratio'][1]:
                score += 30
            
            # Size matching
            if characteristics['size_range'][0] <= estimated_size <= characteristics['size_range'][1]:
                score += 25
            
            # Color matching
            if color_type in characteristics['color_profile'] or characteristics['color_profile'] == 'mixed':
                score += 35
            
            # Quality bonus
            score += quality_metrics.get('overall_quality', 50) * 0.1
            
            if score > best_score:
                best_score = score
                best_match = variety
        
        return {
            'predicted_variety': best_match,
            'confidence': min(100, best_score),
            'characteristics': {
                'color_type': color_type,
                'shape_ratio': round(shape_ratio, 2),
                'estimated_size_mm': round(estimated_size, 1)
            },
            'variety_info': self.pepper_varieties[best_match],
            'alternative_varieties': self._get_alternative_varieties(best_match, best_score)
        }
    
    def _get_alternative_varieties(self, best_match: str, best_score: float) -> List[Dict]:
        """
        Get alternative variety possibilities
        """
        alternatives = []
        for variety, _ in self.pepper_varieties.items():
            if variety != best_match:
                # Simplified scoring for alternatives
                score = max(0, best_score - 20 + np.random.uniform(-5, 5))
                if score > 30:
                    alternatives.append({
                        'variety': variety,
                        'confidence': round(score, 1)
                    })
        
        return sorted(alternatives, key=lambda x: x['confidence'], reverse=True)[:2]
    
    def _analyze_market_value(self, quality_metrics: Dict, variety_info: Dict, ripeness_analysis: Dict) -> Dict:
        """
        Analyze market value and pricing based on Philippine market
        """
        base_price_per_kg = 180.0  # PHP base price (mid-range retail price)
        
        # Quality multiplier
        quality_multiplier = quality_metrics.get('overall_quality', 50) / 100
        
        # Variety multiplier
        variety_multiplier = variety_info['variety_info']['market_value']
        
        # Ripeness multiplier (ripe peppers are more valuable)
        ripeness_multiplier = 0.7 + 0.4 * (ripeness_analysis['ripeness_percentage'] / 100)
        
        estimated_price = base_price_per_kg * quality_multiplier * variety_multiplier * ripeness_multiplier
        
        # Grade classification
        overall_score = quality_metrics.get('overall_quality', 50)
        if overall_score >= 90:
            grade = 'Premium'
            grade_description = 'Export quality, premium markets'
        elif overall_score >= 75:
            grade = 'Grade A'
            grade_description = 'Retail quality, supermarket grade'
        elif overall_score >= 60:
            grade = 'Grade B'
            grade_description = 'Commercial grade, processing'
        else:
            grade = 'Grade C'
            grade_description = 'Lower grade, food service'
        
        return {
            'estimated_price_per_kg': round(estimated_price, 2),
            'grade': grade,
            'grade_description': grade_description,
            'market_factors': {
                'quality_factor': round(quality_multiplier, 2),
                'variety_factor': round(variety_multiplier, 2),
                'ripeness_factor': round(ripeness_multiplier, 2)
            },
            'market_recommendations': self._get_market_recommendations(grade, estimated_price)
        }
    
    def _get_harvest_recommendation(self, ripeness_percent: float, current_stage: str) -> str:
        """
        Get harvest timing recommendation
        """
        if ripeness_percent < 30:
            return 'Too early - allow more time to develop'
        elif ripeness_percent < 60:
            return 'Early harvest - good for storage and transport'
        elif ripeness_percent < 85:
            return 'Optimal harvest time - peak quality'
        else:
            return 'Harvest immediately - at peak ripeness'
    
    def _get_nutritional_highlights(self, nutrition: Dict, h_mean: float) -> List[str]:
        """
        Get key nutritional highlights
        """
        highlights = []
        
        if nutrition['vitamin_c'] > 100:
            highlights.append(f"Excellent vitamin C source ({nutrition['vitamin_c']:.0f}mg)")
        
        if nutrition['vitamin_a'] > 3000:
            highlights.append(f"High in vitamin A ({nutrition['vitamin_a']:.0f} IU)")
        
        if nutrition['antioxidants'] > 120:
            highlights.append("Rich in antioxidants")
        
        if h_mean < 15 or h_mean > 170:  # Red peppers
            highlights.append("Red peppers have highest nutrient density")
        
        return highlights
    
    def _get_health_benefits(self, nutrition: Dict) -> List[str]:
        """
        Get health benefits based on nutritional content
        """
        benefits = [
            "Supports immune system (Vitamin C)",
            "Promotes eye health (Vitamin A)",
            "Anti-inflammatory properties",
            "Supports heart health",
            "May help reduce cancer risk"
        ]
        
        if nutrition['antioxidants'] > 150:
            benefits.append("Powerful antioxidant protection")
        
        return benefits
    
    def _get_market_recommendations(self, grade: str, price: float) -> List[str]:
        """
        Get market-specific recommendations for Philippine market
        """
        recommendations = []
        
        if grade == 'Premium':
            recommendations.extend([
                "Target high-end supermarkets (SM, Robinsons, Puregold)",
                "Suitable for export to Singapore, Hong Kong",
                "Perfect for premium restaurants and hotels",
                "Consider organic certification for higher margins"
            ])
        elif grade == 'Grade A':
            recommendations.extend([
                "Ideal for major supermarket chains",
                "Good for wet markets and palengke",
                "Suitable for food service industry",
                "Consider vacuum packaging for longer shelf life"
            ])
        elif grade == 'Grade B':
            recommendations.extend([
                "Perfect for food processing companies",
                "Good for wholesale markets (Divisoria, etc.)",
                "Suitable for sari-sari stores",
                "Consider bulk sales to restaurants"
            ])
        else:
            recommendations.extend([
                "Focus on processing markets (sauces, pickles)",
                "Suitable for local food manufacturers",
                "Good for institutional buyers (schools, hospitals)",
                "Consider value-added products (dried, powdered)"
            ])
        
        return recommendations
    
    def _get_advanced_recommendations(self, ripeness_analysis: Dict, shelf_life: Dict, 
                                    nutrition: Dict, variety: Dict) -> List[str]:
        """
        Get comprehensive recommendations
        """
        recommendations = []
        
        # Harvest timing
        days_to_optimal = ripeness_analysis['days_to_optimal_harvest']
        if days_to_optimal > 5:
            recommendations.append(f"Wait {days_to_optimal:.1f} days for optimal harvest")
        elif days_to_optimal > 0:
            recommendations.append("Approaching optimal harvest time")
        else:
            recommendations.append("Harvest immediately for best quality")
        
        # Storage
        optimal_days = shelf_life['optimal_storage']['days']
        recommendations.append(f"Optimal storage can extend shelf life to {optimal_days} days")
        
        # Market timing
        variety_name = variety['predicted_variety'].replace('_', ' ').title()
        recommendations.append(f"Variety: {variety_name} - suitable for premium markets")
        
        # Nutritional value
        if nutrition['per_100g']['vitamin_c'] > 120:
            recommendations.append("High vitamin C content - market as healthy choice")
        
        return recommendations
    
    def _get_fallback_analysis(self) -> Dict:
        """
        Fallback analysis when main analysis fails
        """
        return {
            'ripeness_prediction': {
                'current_stage': 'unknown',
                'ripeness_percentage': 50,
                'days_to_optimal_harvest': 3,
                'harvest_recommendation': 'Unable to determine optimal harvest time'
            },
            'shelf_life_estimation': {
                'room_temperature': {'days': 5, 'condition_after': 'Fair condition'},
                'refrigerated': {'days': 10, 'condition_after': 'Good condition'},
                'optimal_storage': {'days': 14, 'condition_after': 'Excellent condition'}
            },
            'nutritional_analysis': {
                'per_100g': self.base_nutrition,
                'estimated_weight_g': 120,
                'nutritional_highlights': ['Standard bell pepper nutrition']
            },
            'variety_classification': {
                'predicted_variety': 'bell_pepper_general',
                'confidence': 50
            },
            'market_analysis': {
                'estimated_price_per_kg': 180.0,
                'grade': 'Grade B'
            },
            'advanced_recommendations': ['Unable to provide detailed analysis']
        }
