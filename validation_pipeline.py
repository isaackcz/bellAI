"""
Enhanced Multi-Layer Validation Pipeline for Bell Pepper Detection
Uses pre-trained deep learning models + computer vision to ensure accurate classification
"""

import cv2
import numpy as np
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image

class BellPepperValidationPipeline:
    """
    Multi-stage validation pipeline to filter out false positives (apples, tomatoes, etc.)
    """
    
    def __init__(self):
        """Initialize pre-trained classifier for secondary validation"""
        print("[INFO] Initializing Enhanced Validation Pipeline...")
        
        # Load pre-trained MobileNetV2 (lightweight, fast, accurate)
        # ImageNet has 1000 classes including bell_pepper, apple, orange, etc.
        self.classifier = models.mobilenet_v2(pretrained=True)
        self.classifier.eval()
        
        # Image preprocessing for ImageNet models
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # ImageNet class indices (relevant to our task)
        # These are the actual ImageNet class IDs
        self.PEPPER_CLASSES = [945]  # bell_pepper
        self.SIMILAR_OBJECTS = [
            948,  # Granny Smith (apple)
            949,  # strawberry
            950,  # orange
            951,  # lemon
            952,  # fig
            953,  # pineapple
            954,  # banana
            966,  # cucumber
            967,  # artichoke
        ]
        
        # Class names for debugging
        self.imagenet_classes = self._load_imagenet_classes()
        
        print("[SUCCESS] Pre-trained MobileNetV2 classifier loaded")
    
    def _load_imagenet_classes(self):
        """Load ImageNet class labels"""
        # Simplified - just the ones we care about
        return {
            945: 'bell_pepper',
            948: 'apple',
            949: 'strawberry',
            950: 'orange',
            951: 'lemon',
            952: 'fig',
            953: 'pineapple',
            954: 'banana',
            966: 'cucumber',
            967: 'artichoke',
        }
    
    def validate_with_pretrained_model(self, crop_image, top_k=5):
        """
        Stage 1: Use pre-trained ImageNet model to verify object category
        Returns True if the object could be a bell pepper, False if it's clearly something else
        """
        try:
            # Convert BGR (OpenCV) to RGB (PIL)
            crop_rgb = cv2.cvtColor(crop_image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(crop_rgb)
            
            # Preprocess
            input_tensor = self.transform(pil_image)
            input_batch = input_tensor.unsqueeze(0)  # Add batch dimension
            
            # Run inference
            with torch.no_grad():
                output = self.classifier(input_batch)
            
            # Get top-k predictions
            probabilities = torch.nn.functional.softmax(output[0], dim=0)
            top_probs, top_indices = torch.topk(probabilities, top_k)
            
            # Convert to lists
            top_probs = top_probs.cpu().numpy()
            top_indices = top_indices.cpu().numpy()
            
            # Log predictions for debugging
            print(f"  |-- Pre-trained model predictions:")
            for prob, idx in zip(top_probs, top_indices):
                class_name = self.imagenet_classes.get(idx, f"class_{idx}")
                print(f"     {class_name}: {prob*100:.1f}%")
            
            # Check if bell_pepper is in top predictions with decent confidence
            bell_pepper_score = probabilities[945].item()  # bell_pepper class
            
            # Check for clearly identified non-pepper objects
            for prob, idx in zip(top_probs[:3], top_indices[:3]):  # Check top 3
                if idx in self.SIMILAR_OBJECTS and prob > 0.3:  # High confidence non-pepper
                    class_name = self.imagenet_classes.get(idx, f"class_{idx}")
                    print(f"  |-- [X] Rejected: Identified as {class_name} ({prob*100:.1f}% confidence)")
                    return False
            
            # If bell_pepper is in top-5 OR no strong competing class, allow it through
            if 945 in top_indices[:5]:
                print(f"  |-- [OK] Bell pepper in top-5 predictions ({bell_pepper_score*100:.1f}%)")
                return True
            elif top_probs[0] < 0.5:  # No strong prediction, give benefit of doubt
                print(f"  |-- [OK] No strong competing classification, allowing through")
                return True
            else:
                print(f"  |-- [X] Rejected: Not identified as bell pepper")
                return False
                
        except Exception as e:
            print(f"  |-- [WARNING] Pre-trained model validation error: {e}")
            # On error, allow through (fail-safe)
            return True
    
    def validate_color(self, crop_image):
        """
        Stage 2: Color validation - check for pepper-like colors and reject skin tones
        """
        hsv = cv2.cvtColor(crop_image, cv2.COLOR_BGR2HSV)
        
        # First, check for skin tones and reject them
        lower_skin = np.array([0, 10, 60])
        upper_skin = np.array([25, 150, 255])
        skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)
        skin_percentage = (np.sum(skin_mask > 0) / (crop_image.shape[0] * crop_image.shape[1])) * 100
        
        if skin_percentage > 30:
            print(f"  |-- [X] Rejected: {skin_percentage:.1f}% skin tone detected")
            return False
        
        # Pepper color ranges (more saturated than skin)
        lower_red1 = np.array([0, 80, 80])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 80, 80])
        upper_red2 = np.array([180, 255, 255])
        lower_yellow = np.array([20, 100, 100])
        upper_yellow = np.array([35, 255, 255])
        lower_green = np.array([35, 50, 50])
        upper_green = np.array([85, 255, 255])
        lower_orange = np.array([10, 100, 100])
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
        
        # Require at least 50% pepper-colored pixels
        is_valid = pepper_percentage >= 50.0
        if not is_valid:
            print(f"  |-- [X] Rejected: Only {pepper_percentage:.1f}% pepper-colored pixels")
        else:
            print(f"  |-- [OK] Color validation passed ({pepper_percentage:.1f}% pepper colors)")
        return is_valid
    
    def validate_texture(self, crop_image):
        """
        Stage 3: Texture validation - detect bell pepper's characteristic wavy/lobed shape
        """
        if crop_image.size == 0:
            return False
        
        gray = cv2.cvtColor(crop_image, cv2.COLOR_BGR2GRAY)
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            print(f"  |-- [X] Rejected: No clear contours detected")
            return False
        
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Analyze contour complexity
        perimeter = cv2.arcLength(largest_contour, True)
        area = cv2.contourArea(largest_contour)
        
        if area < 100:
            return True  # Too small to analyze reliably
        
        # Circularity test
        circularity = (4 * np.pi * area) / (perimeter * perimeter) if perimeter > 0 else 0
        
        # Reject very circular objects (apples/tomatoes)
        if circularity > 0.88:
            print(f"  |-- [X] Rejected: Too circular ({circularity:.3f}), likely apple/tomato")
            return False
        
        # Check for blocky shape
        epsilon = 0.02 * perimeter
        approx = cv2.approxPolyDP(largest_contour, epsilon, True)
        num_vertices = len(approx)
        
        if num_vertices < 4:
            print(f"  |-- [X] Rejected: Too simple shape ({num_vertices} vertices)")
            return False
        
        # Texture variance
        std_dev = np.std(gray)
        
        if std_dev < 15:
            print(f"  |-- [X] Rejected: Surface too smooth (std: {std_dev:.1f}), likely apple")
            return False
        
        print(f"  |-- [OK] Texture validation passed (circ={circularity:.2f}, vertices={num_vertices}, std={std_dev:.1f})")
        return True
    
    def validate_shape(self, bbox, image_shape=None):
        """
        Stage 4: Shape validation - check aspect ratio and size
        """
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        
        if width == 0 or height == 0:
            return False
        
        # Minimum size check
        min_dimension = min(width, height)
        if min_dimension < 50:
            print(f"  |-- [X] Rejected: Too small ({min_dimension:.0f}px)")
            return False
        
        # Aspect ratio check
        aspect_ratio = height / width
        if not (0.8 <= aspect_ratio <= 2.0):
            print(f"  |-- [X] Rejected: Invalid aspect ratio ({aspect_ratio:.2f})")
            return False
        
        # Size relative to image
        bbox_area = width * height
        if image_shape is not None:
            img_height, img_width = image_shape[:2]
            if bbox_area > (img_height * img_width * 0.8):
                print(f"  |-- [X] Rejected: Too large relative to image")
                return False
        
        print(f"  |-- [OK] Shape validation passed (aspect={aspect_ratio:.2f})")
        return True
    
    def full_validation(self, crop_image, bbox, image_shape=None):
        """
        Run complete validation pipeline
        Returns: (is_valid, stage_failed)
        """
        print(f"\n  [VALIDATION] Running layered validation pipeline...")
        
        # Stage 1: Pre-trained model validation (most important)
        if not self.validate_with_pretrained_model(crop_image):
            return False, "pretrained_model"
        
        # Stage 2: Shape validation (fast)
        if not self.validate_shape(bbox, image_shape):
            return False, "shape"
        
        # Stage 3: Color validation
        if not self.validate_color(crop_image):
            return False, "color"
        
        # Stage 4: Texture validation
        if not self.validate_texture(crop_image):
            return False, "texture"
        
        print(f"  [SUCCESS] All validation stages passed!")
        return True, None


# Singleton instance
_validation_pipeline = None

def get_validation_pipeline():
    """Get or create validation pipeline instance"""
    global _validation_pipeline
    if _validation_pipeline is None:
        _validation_pipeline = BellPepperValidationPipeline()
    return _validation_pipeline

