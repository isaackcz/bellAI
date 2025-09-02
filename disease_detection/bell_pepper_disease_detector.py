import torch
import torch.nn as nn
import torchvision.transforms as transforms
from torchvision.models import efficientnet_b4, resnet50
import cv2
import numpy as np
from PIL import Image
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional
import albumentations as A
from albumentations.pytorch import ToTensorV2

class BellPepperDiseaseDetector:
    """
    Advanced Bell Pepper Disease Detection using Deep Learning
    Supports: Bacterial Spot, Blossom End Rot, Anthracnose, Mosaic Virus, Healthy
    """
    
    def __init__(self, model_path: Optional[str] = None, device: str = 'auto'):
        self.device = self._get_device(device)
        self.disease_classes = {
            0: 'Healthy',
            1: 'Bacterial_Spot',
            2: 'Blossom_End_Rot', 
            3: 'Anthracnose',
            4: 'Mosaic_Virus',
            5: 'Early_Blight',
            6: 'Late_Blight',
            7: 'Leaf_Curl',
            8: 'Powdery_Mildew'
        }
        
        self.disease_info = {
            'Healthy': {
                'severity': 'None',
                'treatment': 'Continue proper care',
                'description': 'Plant appears healthy with no visible disease symptoms'
            },
            'Bacterial_Spot': {
                'severity': 'High',
                'treatment': 'Copper-based fungicides, remove affected parts',
                'description': 'Small, dark, water-soaked spots on leaves and fruits'
            },
            'Blossom_End_Rot': {
                'severity': 'Medium',
                'treatment': 'Improve calcium uptake, consistent watering',
                'description': 'Dark, sunken lesions on the blossom end of fruits'
            },
            'Anthracnose': {
                'severity': 'High',
                'treatment': 'Fungicides, improve air circulation, remove debris',
                'description': 'Circular, sunken lesions with dark centers on fruits'
            },
            'Mosaic_Virus': {
                'severity': 'Very High',
                'treatment': 'Remove infected plants, control aphid vectors',
                'description': 'Mottled yellow and green patterns on leaves'
            },
            'Early_Blight': {
                'severity': 'Medium',
                'treatment': 'Fungicides, proper spacing, avoid overhead watering',
                'description': 'Dark spots with concentric rings on older leaves'
            },
            'Late_Blight': {
                'severity': 'Very High',
                'treatment': 'Preventive fungicides, remove affected plants',
                'description': 'Water-soaked lesions that turn brown and spread rapidly'
            },
            'Leaf_Curl': {
                'severity': 'Medium',
                'treatment': 'Virus management, remove infected plants',
                'description': 'Upward curling and yellowing of leaves'
            },
            'Powdery_Mildew': {
                'severity': 'Medium',
                'treatment': 'Sulfur or potassium bicarbonate sprays',
                'description': 'White powdery coating on leaves and stems'
            }
        }
        
        # Load or initialize model
        self.model = self._build_model()
        if model_path:
            self._load_model(model_path)
        
        # Setup image preprocessing
        self.transform = self._get_transforms()
        
    def _get_device(self, device: str) -> torch.device:
        """Automatically detect best available device"""
        if device == 'auto':
            if torch.cuda.is_available():
                return torch.device('cuda')
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return torch.device('mps')  # Apple Silicon
            else:
                return torch.device('cpu')
        return torch.device(device)
    
    def _build_model(self) -> nn.Module:
        """Build EfficientNet-based disease detection model"""
        # Use EfficientNet-B4 as backbone for high accuracy
        model = efficientnet_b4(pretrained=True)
        
        # Modify classifier for disease detection
        num_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(0.4),
            nn.Linear(num_features, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, len(self.disease_classes))
        )
        
        return model.to(self.device)
    
    def _get_transforms(self) -> transforms.Compose:
        """Get image preprocessing transforms"""
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
    
    def _load_model(self, model_path: str):
        """Load trained model weights"""
        try:
            checkpoint = torch.load(model_path, map_location=self.device)
            if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                self.model.load_state_dict(checkpoint['model_state_dict'])
            else:
                self.model.load_state_dict(checkpoint)
            self.model.eval()
            print(f"✅ Disease detection model loaded from {model_path}")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            print("Using untrained model - train first for accurate results")
    
    def preprocess_image(self, image: np.ndarray) -> torch.Tensor:
        """Preprocess image for disease detection"""
        # Convert BGR to RGB if needed
        if len(image.shape) == 3 and image.shape[2] == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image
        
        # Convert to PIL Image
        pil_image = Image.fromarray(image_rgb)
        
        # Apply transforms
        tensor_image = self.transform(pil_image)
        return tensor_image.unsqueeze(0).to(self.device)
    
    def detect_disease(self, image: np.ndarray, return_confidence: bool = True) -> Dict:
        """
        Detect disease in bell pepper image
        
        Args:
            image: Input image as numpy array
            return_confidence: Whether to return confidence scores for all classes
            
        Returns:
            Dictionary with disease prediction and metadata
        """
        self.model.eval()
        
        with torch.no_grad():
            # Preprocess image
            input_tensor = self.preprocess_image(image)
            
            # Get prediction
            outputs = self.model(input_tensor)
            probabilities = F.softmax(outputs, dim=1)
            
            # Get top prediction
            confidence, predicted_class = torch.max(probabilities, 1)
            predicted_class = predicted_class.item()
            confidence = confidence.item()
            
            disease_name = self.disease_classes[predicted_class]
            disease_details = self.disease_info[disease_name]
            
            result = {
                'disease': disease_name,
                'confidence': round(confidence * 100, 2),
                'severity': disease_details['severity'],
                'treatment': disease_details['treatment'],
                'description': disease_details['description'],
                'is_healthy': disease_name == 'Healthy'
            }
            
            if return_confidence:
                # Get confidence for all classes
                all_confidences = {}
                for idx, prob in enumerate(probabilities[0]):
                    class_name = self.disease_classes[idx]
                    all_confidences[class_name] = round(prob.item() * 100, 2)
                result['all_confidences'] = all_confidences
            
            return result
    
    def detect_multiple_regions(self, image: np.ndarray, regions: List[Tuple[int, int, int, int]]) -> List[Dict]:
        """
        Detect diseases in multiple regions of an image
        
        Args:
            image: Full image
            regions: List of (x1, y1, x2, y2) bounding boxes
            
        Returns:
            List of detection results for each region
        """
        results = []
        
        for i, (x1, y1, x2, y2) in enumerate(regions):
            # Extract region
            region = image[y1:y2, x1:x2]
            
            if region.size > 0:
                # Detect disease in this region
                detection = self.detect_disease(region)
                detection['region_id'] = i
                detection['bbox'] = (x1, y1, x2, y2)
                results.append(detection)
        
        return results
    
    def get_disease_risk_assessment(self, detections: List[Dict]) -> Dict:
        """
        Assess overall disease risk based on multiple detections
        """
        if not detections:
            return {'risk_level': 'Unknown', 'recommendations': []}
        
        # Count disease types
        disease_counts = {}
        total_detections = len(detections)
        healthy_count = 0
        
        for detection in detections:
            disease = detection['disease']
            disease_counts[disease] = disease_counts.get(disease, 0) + 1
            
            if disease == 'Healthy':
                healthy_count += 1
        
        # Calculate risk level
        health_percentage = (healthy_count / total_detections) * 100
        
        if health_percentage >= 80:
            risk_level = 'Low'
        elif health_percentage >= 60:
            risk_level = 'Medium'
        elif health_percentage >= 40:
            risk_level = 'High'
        else:
            risk_level = 'Critical'
        
        # Generate recommendations
        recommendations = []
        
        if 'Bacterial_Spot' in disease_counts:
            recommendations.append("Apply copper-based fungicide treatment")
            recommendations.append("Improve air circulation around plants")
        
        if 'Mosaic_Virus' in disease_counts:
            recommendations.append("Remove infected plants immediately")
            recommendations.append("Control aphid vectors with insecticides")
        
        if 'Blossom_End_Rot' in disease_counts:
            recommendations.append("Ensure consistent watering schedule")
            recommendations.append("Check soil calcium levels")
        
        if health_percentage < 50:
            recommendations.append("Consider professional plant pathology consultation")
        
        return {
            'risk_level': risk_level,
            'health_percentage': round(health_percentage, 1),
            'disease_distribution': disease_counts,
            'recommendations': recommendations,
            'total_plants_analyzed': total_detections
        }


class DiseaseDetectionTrainer:
    """
    Trainer class for custom bell pepper disease detection model
    """
    
    def __init__(self, model: BellPepperDiseaseDetector):
        self.model = model
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = torch.optim.AdamW(
            self.model.model.parameters(),
            lr=0.001,
            weight_decay=0.01
        )
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            patience=5,
            factor=0.5
        )
    
    def train_model(self, train_loader, val_loader, epochs: int = 50, save_path: str = 'disease_model.pth'):
        """
        Train the disease detection model
        """
        best_val_loss = float('inf')
        
        for epoch in range(epochs):
            # Training phase
            self.model.model.train()
            train_loss = 0.0
            
            for batch_idx, (data, target) in enumerate(train_loader):
                data, target = data.to(self.model.device), target.to(self.model.device)
                
                self.optimizer.zero_grad()
                output = self.model.model(data)
                loss = self.criterion(output, target)
                loss.backward()
                self.optimizer.step()
                
                train_loss += loss.item()
            
            # Validation phase
            self.model.model.eval()
            val_loss = 0.0
            correct = 0
            
            with torch.no_grad():
                for data, target in val_loader:
                    data, target = data.to(self.model.device), target.to(self.model.device)
                    output = self.model.model(data)
                    val_loss += self.criterion(output, target).item()
                    pred = output.argmax(dim=1, keepdim=True)
                    correct += pred.eq(target.view_as(pred)).sum().item()
            
            val_accuracy = 100. * correct / len(val_loader.dataset)
            
            print(f'Epoch {epoch+1}/{epochs}: '
                  f'Train Loss: {train_loss/len(train_loader):.4f}, '
                  f'Val Loss: {val_loss/len(val_loader):.4f}, '
                  f'Val Acc: {val_accuracy:.2f}%')
            
            # Save best model
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                torch.save({
                    'model_state_dict': self.model.model.state_dict(),
                    'optimizer_state_dict': self.optimizer.state_dict(),
                    'epoch': epoch,
                    'val_loss': val_loss,
                    'val_accuracy': val_accuracy
                }, save_path)
            
            self.scheduler.step(val_loss)


# Usage example
def analyze_pepper_diseases(image_path: str, model_path: str = None) -> Dict:
    """
    Analyze bell pepper diseases from image file
    """
    # Initialize detector
    detector = BellPepperDiseaseDetector(model_path)
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image from {image_path}")
    
    # Detect disease
    result = detector.detect_disease(image)
    
    return result


# Integration with existing bell pepper detection
def integrate_with_yolo_detection(yolo_results, image: np.ndarray, disease_detector: BellPepperDiseaseDetector) -> List[Dict]:
    """
    Integrate disease detection with YOLO bell pepper detection
    """
    disease_results = []
    
    if hasattr(yolo_results[0], 'boxes') and yolo_results[0].boxes is not None:
        for box in yolo_results[0].boxes:
            # Extract bounding box
            x1, y1, x2, y2 = box.xyxy.cpu().numpy()[0].astype(int)
            
            # Crop pepper region
            pepper_crop = image[y1:y2, x1:x2]
            
            if pepper_crop.size > 0:
                # Detect disease in cropped region
                disease_result = disease_detector.detect_disease(pepper_crop)
                disease_result['bbox'] = (x1, y1, x2, y2)
                disease_results.append(disease_result)
    
    return disease_results
