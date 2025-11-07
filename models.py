"""
Database models for PepperAI
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    """User account model"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100))
    role = db.Column(db.String(20), default='user')  # user, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class AnalysisHistory(db.Model):
    """Analysis session history"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_path = db.Column(db.String(200))
    result_path = db.Column(db.String(200))
    peppers_found = db.Column(db.Integer, default=0)
    avg_quality = db.Column(db.Float, default=0.0)
    analysis_data = db.Column(db.Text)  # JSON string - summary
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('analyses', lazy=True))

class BellPepperDetection(db.Model):
    """Individual bell pepper detection records"""
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey('analysis_history.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Detection info
    pepper_id = db.Column(db.String(50))  # e.g., 'pepper_1'
    variety = db.Column(db.String(100))
    confidence = db.Column(db.Float)
    
    # Image paths
    crop_path = db.Column(db.String(200))  # Cropped pepper image
    
    # Quality metrics
    quality_score = db.Column(db.Float)
    quality_category = db.Column(db.String(50))
    color_uniformity = db.Column(db.Float)
    size_consistency = db.Column(db.Float)
    surface_quality = db.Column(db.Float)
    ripeness_level = db.Column(db.Float)
    
    # Advanced analysis (JSON strings)
    advanced_analysis = db.Column(db.Text)  # Ripeness, shelf life, nutrition
    disease_analysis = db.Column(db.Text)  # Disease detection results
    recommendations = db.Column(db.Text)  # Quality recommendations (JSON list)
    
    # Health info
    health_status = db.Column(db.String(50))
    overall_health_score = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis = db.relationship('AnalysisHistory', backref=db.backref('peppers', lazy=True))
    user = db.relationship('User', backref=db.backref('pepper_detections', lazy=True))
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        import json
        return {
            'id': self.id,
            'pepper_id': self.pepper_id,
            'variety': self.variety,
            'confidence': self.confidence,
            'crop_url': f'/results/{self.crop_path}' if self.crop_path else None,
            'quality_analysis': {
                'quality_score': self.quality_score,
                'quality_category': self.quality_category,
                'color_uniformity': self.color_uniformity,
                'size_consistency': self.size_consistency,
                'surface_quality': self.surface_quality,
                'ripeness_level': self.ripeness_level,
                'recommendations': json.loads(self.recommendations) if self.recommendations else []
            },
            'advanced_analysis': json.loads(self.advanced_analysis) if self.advanced_analysis else {},
            'disease_analysis': json.loads(self.disease_analysis) if self.disease_analysis else {},
            'health_status': self.health_status,
            'overall_health_score': self.overall_health_score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class PepperType(db.Model):
    """Bell pepper type/category (e.g., Fully Ripened, Partially Ripened, etc.)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))  # FontAwesome icon class
    color = db.Column(db.String(20))  # Hex color for the category
    order_index = db.Column(db.Integer, default=0)  # For display ordering
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to varieties
    varieties = db.relationship('PepperVariety', backref='pepper_type', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'color': self.color,
            'order_index': self.order_index
        }

class PepperDisease(db.Model):
    """Bell pepper diseases and health conditions database"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    scientific_name = db.Column(db.String(150))
    description = db.Column(db.Text)
    
    # Symptoms (JSON string - list of symptoms)
    symptoms = db.Column(db.Text)
    
    # Causes (JSON string - list of causes)
    causes = db.Column(db.Text)
    
    # Prevention methods (JSON string - list)
    prevention = db.Column(db.Text)
    
    # Treatment methods (JSON string - list)
    treatment = db.Column(db.Text)
    
    # Severity level
    severity = db.Column(db.String(20))  # mild, moderate, severe
    
    # Visual characteristics
    visual_indicators = db.Column(db.Text)  # JSON string - list of visual signs
    
    # Additional info
    affected_parts = db.Column(db.String(200))  # e.g., "Leaves, Stems, Fruits"
    color = db.Column(db.String(20))  # Color for UI display
    icon = db.Column(db.String(50))  # FontAwesome icon
    
    # Images (JSON string - list of image URLs)
    images = db.Column(db.Text)  # URLs to disease example images
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        import json
        return {
            'id': self.id,
            'name': self.name,
            'scientific_name': self.scientific_name,
            'description': self.description,
            'symptoms': json.loads(self.symptoms) if self.symptoms else [],
            'causes': json.loads(self.causes) if self.causes else [],
            'prevention': json.loads(self.prevention) if self.prevention else [],
            'treatment': json.loads(self.treatment) if self.treatment else [],
            'severity': self.severity,
            'visual_indicators': json.loads(self.visual_indicators) if self.visual_indicators else [],
            'affected_parts': self.affected_parts,
            'color': self.color,
            'icon': self.icon,
            'images': json.loads(self.images) if self.images else []
        }

class PepperVariety(db.Model):
    """Bell pepper variety information database"""
    id = db.Column(db.Integer, primary_key=True)
    type_id = db.Column(db.Integer, db.ForeignKey('pepper_type.id'), nullable=False)
    name = db.Column(db.String(100), unique=True, nullable=False)
    color = db.Column(db.String(20))  # Hex color code
    description = db.Column(db.Text)
    
    # Characteristics (JSON string - list of characteristics)
    characteristics = db.Column(db.Text)
    
    # Quality Standards (JSON string - dict of standards)
    quality_standards = db.Column(db.Text)
    
    # Uses (JSON string - list of uses)
    uses = db.Column(db.Text)
    
    # Storage and nutrition info
    storage = db.Column(db.String(200))
    nutritional_highlights = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        import json
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'description': self.description,
            'characteristics': json.loads(self.characteristics) if self.characteristics else [],
            'quality_standards': json.loads(self.quality_standards) if self.quality_standards else {},
            'uses': json.loads(self.uses) if self.uses else [],
            'storage': self.storage,
            'nutritional_highlights': self.nutritional_highlights,
            'type_id': self.type_id
        }

class Notification(db.Model):
    """Notifications system for admin-to-user communications"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Sender information
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Recipient options
    recipient_type = db.Column(db.String(20), nullable=False)  # 'all' or 'specific'
    recipient_ids = db.Column(db.Text)  # JSON array of user IDs for specific recipients
    
    # Message properties
    priority = db.Column(db.String(20), default='normal')  # 'low', 'normal', 'high', 'urgent'
    category = db.Column(db.String(50), default='general')  # 'general', 'system', 'update', 'alert'
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scheduled_for = db.Column(db.DateTime)  # For scheduled notifications
    expires_at = db.Column(db.DateTime)  # Optional expiration date
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_draft = db.Column(db.Boolean, default=False)
    
    # Relationships
    sender = db.relationship('User', backref=db.backref('sent_notifications', lazy=True))
    attachments = db.relationship('NotificationAttachment', backref='notification', lazy=True, cascade='all, delete-orphan')
    read_receipts = db.relationship('NotificationRead', backref='notification', lazy=True, cascade='all, delete-orphan')
    
    def get_recipient_list(self):
        """Get list of recipient user IDs"""
        import json
        if self.recipient_type == 'all':
            return [user.id for user in User.query.filter_by(role='user').all()]
        elif self.recipient_ids:
            return json.loads(self.recipient_ids)
        return []
    
    def is_read_by(self, user_id):
        """Check if notification has been read by specific user"""
        return NotificationRead.query.filter_by(
            notification_id=self.id,
            user_id=user_id
        ).first() is not None
    
    def mark_as_read(self, user_id):
        """Mark notification as read by specific user"""
        existing_read = NotificationRead.query.filter_by(
            notification_id=self.id,
            user_id=user_id
        ).first()
        
        if not existing_read:
            read_receipt = NotificationRead(
                notification_id=self.id,
                user_id=user_id
            )
            db.session.add(read_receipt)
            db.session.commit()
    
    def get_read_count(self):
        """Get number of users who have read this notification"""
        return NotificationRead.query.filter_by(notification_id=self.id).count()
    
    def get_total_recipients(self):
        """Get total number of intended recipients"""
        return len(self.get_recipient_list())
    
    def to_dict(self, user_id=None):
        """Convert to dictionary for JSON serialization"""
        import json
        
        data = {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'sender': self.sender.full_name or self.sender.username,
            'sender_id': self.sender_id,
            'recipient_type': self.recipient_type,
            'priority': self.priority,
            'category': self.category,
            'created_at': self.created_at.isoformat(),
            'scheduled_for': self.scheduled_for.isoformat() if self.scheduled_for else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'is_draft': self.is_draft,
            'attachments': [att.to_dict() for att in self.attachments],
            'read_count': self.get_read_count(),
            'total_recipients': self.get_total_recipients()
        }
        
        if user_id:
            data['is_read'] = self.is_read_by(user_id)
            
        return data

class NotificationAttachment(db.Model):
    """File attachments for notifications"""
    id = db.Column(db.Integer, primary_key=True)
    notification_id = db.Column(db.Integer, db.ForeignKey('notification.id'), nullable=True)  # Allow null for pre-uploaded attachments
    
    # File information
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # Size in bytes
    mime_type = db.Column(db.String(100))
    
    # File type classification
    file_type = db.Column(db.String(20))  # 'image', 'document', 'other'
    
    # Metadata
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'file_type': self.file_type,
            'download_url': f'/notifications/attachment/{self.id}',
            'uploaded_at': self.uploaded_at.isoformat()
        }

class NotificationRead(db.Model):
    """Track which users have read which notifications"""
    id = db.Column(db.Integer, primary_key=True)
    notification_id = db.Column(db.Integer, db.ForeignKey('notification.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    read_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate reads
    __table_args__ = (db.UniqueConstraint('notification_id', 'user_id', name='unique_notification_read'),)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('notification_reads', lazy=True))

