"""
Settings and User Management Routes
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from functools import wraps
from datetime import datetime
from models import db, User, AnalysisHistory, BellPepperDetection
from sqlalchemy import func

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

def admin_required(f):
    """Decorator to require admin role"""
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

@settings_bp.route('/')
@admin_required
def settings():
    """Settings page with user management"""
    # Get all users
    users = User.query.order_by(User.created_at.desc()).all()
    
    # Get user statistics
    user_stats = []
    for user in users:
        total_analyses = AnalysisHistory.query.filter_by(user_id=user.id).count()
        total_peppers = db.session.query(func.sum(AnalysisHistory.peppers_found)).filter_by(user_id=user.id).scalar() or 0
        avg_quality = db.session.query(func.avg(AnalysisHistory.avg_quality)).filter_by(user_id=user.id).scalar() or 0
        
        user_stats.append({
            'user': user,
            'total_analyses': total_analyses,
            'total_peppers': int(total_peppers),
            'avg_quality': round(avg_quality, 1),
            'last_activity': user.last_login
        })
    
    # Get system statistics
    total_users = User.query.count()
    total_admins = User.query.filter_by(role='admin').count()
    total_regular_users = User.query.filter_by(role='user').count()
    total_system_analyses = AnalysisHistory.query.count()
    total_system_peppers = db.session.query(func.sum(AnalysisHistory.peppers_found)).scalar() or 0
    
    system_stats = {
        'total_users': total_users,
        'total_admins': total_admins,
        'total_regular_users': total_regular_users,
        'total_analyses': total_system_analyses,
        'total_peppers': int(total_system_peppers)
    }
    
    return render_template('settings.html', 
                         user_stats=user_stats,
                         system_stats=system_stats)

@settings_bp.route('/users/create', methods=['POST'])
@admin_required
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        
        # Validation
        required_fields = ['username', 'email', 'password', 'full_name', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        # Check if username or email already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'message': 'Username already exists'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        # Validate password length
        if len(data['password']) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
        
        # Validate role
        if data['role'] not in ['user', 'admin']:
            return jsonify({'success': False, 'message': 'Invalid role'}), 400
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            full_name=data['full_name'],
            role=data['role']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'created_at': user.created_at.isoformat()
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@settings_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    """Get user details"""
    user = User.query.get_or_404(user_id)
    
    # Get user statistics
    total_analyses = AnalysisHistory.query.filter_by(user_id=user.id).count()
    total_peppers = db.session.query(func.sum(AnalysisHistory.peppers_found)).filter_by(user_id=user.id).scalar() or 0
    avg_quality = db.session.query(func.avg(AnalysisHistory.avg_quality)).filter_by(user_id=user.id).scalar() or 0
    
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'stats': {
                'total_analyses': total_analyses,
                'total_peppers': int(total_peppers),
                'avg_quality': round(avg_quality, 1)
            }
        }
    })

@settings_bp.route('/users/<int:user_id>/update', methods=['PUT'])
@admin_required
def update_user(user_id):
    """Update user details"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        # Prevent admin from demoting themselves
        if user.id == session['user_id'] and data.get('role') == 'user':
            return jsonify({'success': False, 'message': 'You cannot demote yourself from admin'}), 400
        
        # Update fields
        if 'username' in data and data['username'] != user.username:
            # Check if new username exists
            if User.query.filter_by(username=data['username']).first():
                return jsonify({'success': False, 'message': 'Username already exists'}), 400
            user.username = data['username']
        
        if 'email' in data and data['email'] != user.email:
            # Check if new email exists
            if User.query.filter_by(email=data['email']).first():
                return jsonify({'success': False, 'message': 'Email already registered'}), 400
            user.email = data['email']
        
        if 'full_name' in data:
            user.full_name = data['full_name']
        
        if 'role' in data and data['role'] in ['user', 'admin']:
            user.role = data['role']
        
        # Update password if provided
        if 'password' in data and data['password']:
            if len(data['password']) < 6:
                return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
            user.set_password(data['password'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User updated successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@settings_bp.route('/users/<int:user_id>/delete', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete a user"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent admin from deleting themselves
        if user.id == session['user_id']:
            return jsonify({'success': False, 'message': 'You cannot delete your own account'}), 400
        
        # Check if user is the last admin
        if user.role == 'admin':
            admin_count = User.query.filter_by(role='admin').count()
            if admin_count <= 1:
                return jsonify({'success': False, 'message': 'Cannot delete the last admin user'}), 400
        
        # Delete user's data
        # Note: SQLAlchemy will handle cascade deletes based on relationships
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'User {username} deleted successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@settings_bp.route('/users/<int:user_id>/analytics', methods=['GET'])
@admin_required
def user_analytics(user_id):
    """Get detailed analytics for a user"""
    user = User.query.get_or_404(user_id)
    
    # Get analysis history
    analyses = AnalysisHistory.query.filter_by(user_id=user.id).order_by(AnalysisHistory.created_at.desc()).limit(10).all()
    
    # Get pepper detections
    peppers = BellPepperDetection.query.filter_by(user_id=user.id).order_by(BellPepperDetection.created_at.desc()).limit(20).all()
    
    # Calculate quality distribution
    quality_categories = db.session.query(
        BellPepperDetection.quality_category,
        func.count(BellPepperDetection.id)
    ).filter_by(user_id=user.id).group_by(BellPepperDetection.quality_category).all()
    
    # Get monthly analysis count (last 6 months)
    from datetime import datetime, timedelta
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    monthly_analyses = db.session.query(
        func.strftime('%Y-%m', AnalysisHistory.created_at).label('month'),
        func.count(AnalysisHistory.id).label('count')
    ).filter(
        AnalysisHistory.user_id == user.id,
        AnalysisHistory.created_at >= six_months_ago
    ).group_by('month').all()
    
    return jsonify({
        'success': True,
        'analytics': {
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'email': user.email
            },
            'recent_analyses': [
                {
                    'id': a.id,
                    'peppers_found': a.peppers_found,
                    'avg_quality': a.avg_quality,
                    'created_at': a.created_at.isoformat()
                } for a in analyses
            ],
            'quality_distribution': {cat: count for cat, count in quality_categories},
            'monthly_trend': [
                {'month': month, 'count': count} for month, count in monthly_analyses
            ]
        }
    })

