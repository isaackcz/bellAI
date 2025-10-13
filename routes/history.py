"""
History routes for viewing bell pepper detection history
"""
from flask import render_template, session, redirect, url_for, flash, jsonify, request
from functools import wraps
from models import db, User, BellPepperDetection, AnalysisHistory
from . import history_bp

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@history_bp.route('/history')
@login_required
def history():
    """View all bell pepper detections for the current user"""
    user = User.query.get(session['user_id'])
    
    # Pagination and filters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    # Ensure per_page is a valid value
    if per_page not in [5, 10, 20, 50]:
        per_page = 10
    variety_filter = request.args.get('variety', '')
    quality_filter = request.args.get('quality', '')
    
    # Build query with filters
    peppers_query = BellPepperDetection.query.filter_by(user_id=user.id)
    
    # Apply variety filter
    if variety_filter:
        peppers_query = peppers_query.filter_by(variety=variety_filter)
    
    # Apply quality filter
    if quality_filter == 'excellent':
        peppers_query = peppers_query.filter(BellPepperDetection.quality_score >= 80)
    elif quality_filter == 'good':
        peppers_query = peppers_query.filter(BellPepperDetection.quality_score >= 60, BellPepperDetection.quality_score < 80)
    elif quality_filter == 'fair':
        peppers_query = peppers_query.filter(BellPepperDetection.quality_score >= 40, BellPepperDetection.quality_score < 60)
    elif quality_filter == 'poor':
        peppers_query = peppers_query.filter(BellPepperDetection.quality_score < 40)
    
    # Order by newest first and paginate
    peppers_query = peppers_query.order_by(BellPepperDetection.created_at.desc())
    peppers_pagination = peppers_query.paginate(page=page, per_page=per_page, error_out=False)
    peppers = peppers_pagination.items
    
    # Get statistics
    total_peppers = BellPepperDetection.query.filter_by(user_id=user.id).count()
    avg_quality = db.session.query(db.func.avg(BellPepperDetection.quality_score)).filter_by(user_id=user.id).scalar() or 0
    
    # Quality distribution
    excellent_count = BellPepperDetection.query.filter_by(user_id=user.id).filter(BellPepperDetection.quality_score >= 80).count()
    good_count = BellPepperDetection.query.filter_by(user_id=user.id).filter(BellPepperDetection.quality_score >= 60, BellPepperDetection.quality_score < 80).count()
    fair_count = BellPepperDetection.query.filter_by(user_id=user.id).filter(BellPepperDetection.quality_score >= 40, BellPepperDetection.quality_score < 60).count()
    poor_count = BellPepperDetection.query.filter_by(user_id=user.id).filter(BellPepperDetection.quality_score < 40).count()
    
    # Variety distribution
    variety_stats = db.session.query(
        BellPepperDetection.variety,
        db.func.count(BellPepperDetection.id).label('count')
    ).filter_by(user_id=user.id).group_by(BellPepperDetection.variety).all()
    
    return render_template('history.html',
                         user=user,
                         peppers=peppers,
                         pagination=peppers_pagination,
                         per_page=per_page,
                         total_peppers=total_peppers,
                         avg_quality=round(avg_quality, 1),
                         excellent_count=excellent_count,
                         good_count=good_count,
                         fair_count=fair_count,
                         poor_count=poor_count,
                         variety_stats=variety_stats)

@history_bp.route('/pepper/<int:pepper_id>')
@login_required
def pepper_detail(pepper_id):
    """View detailed information about a specific bell pepper"""
    pepper = BellPepperDetection.query.get_or_404(pepper_id)
    
    # Ensure user owns this pepper
    if pepper.user_id != session['user_id']:
        flash('Access denied.', 'error')
        return redirect(url_for('history.history'))
    
    # Parse JSON fields
    import json
    pepper.advanced_analysis_data = json.loads(pepper.advanced_analysis) if pepper.advanced_analysis else {}
    pepper.disease_analysis_data = json.loads(pepper.disease_analysis) if pepper.disease_analysis else {}
    pepper.recommendations_list = json.loads(pepper.recommendations) if pepper.recommendations else []
    
    return render_template('pepper_detail.html', pepper=pepper)

@history_bp.route('/history/ajax')
def history_ajax():
    """AJAX endpoint for real-time filtering and pagination"""
    # Check authentication
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    variety_filter = request.args.get('variety', '')
    quality_filter = request.args.get('quality', '')
    
    # Ensure per_page is valid
    if per_page not in [5, 10, 20, 50]:
        per_page = 10
    
    # Build query with filters
    peppers_query = BellPepperDetection.query.filter_by(user_id=user.id)
    
    if variety_filter:
        peppers_query = peppers_query.filter_by(variety=variety_filter)
    
    if quality_filter == 'excellent':
        peppers_query = peppers_query.filter(BellPepperDetection.quality_score >= 80)
    elif quality_filter == 'good':
        peppers_query = peppers_query.filter(BellPepperDetection.quality_score >= 60, BellPepperDetection.quality_score < 80)
    elif quality_filter == 'fair':
        peppers_query = peppers_query.filter(BellPepperDetection.quality_score >= 40, BellPepperDetection.quality_score < 60)
    elif quality_filter == 'poor':
        peppers_query = peppers_query.filter(BellPepperDetection.quality_score < 40)
    
    # Order and paginate
    peppers_query = peppers_query.order_by(BellPepperDetection.created_at.desc())
    peppers_pagination = peppers_query.paginate(page=page, per_page=per_page, error_out=False)
    peppers = peppers_pagination.items
    
    # Convert peppers to JSON-serializable format
    peppers_data = []
    for pepper in peppers:
        pepper_dict = {
            'id': pepper.id,
            'variety': pepper.variety,
            'quality_score': pepper.quality_score,
            'quality_category': pepper.quality_category,
            'confidence': pepper.confidence,
            'crop_path': pepper.crop_path,
            'color_uniformity': pepper.color_uniformity,
            'size_consistency': pepper.size_consistency,
            'surface_quality': pepper.surface_quality,
            'created_at': pepper.created_at.strftime('%Y-%m-%d %H:%M') if pepper.created_at else None
        }
        peppers_data.append(pepper_dict)
    
    # Pagination info
    pagination_info = {
        'page': peppers_pagination.page,
        'pages': peppers_pagination.pages,
        'per_page': peppers_pagination.per_page,
        'total': peppers_pagination.total,
        'has_prev': peppers_pagination.has_prev,
        'has_next': peppers_pagination.has_next,
        'prev_num': peppers_pagination.prev_num,
        'next_num': peppers_pagination.next_num
    }
    
    return jsonify({
        'peppers': peppers_data,
        'pagination': pagination_info
    })

@history_bp.route('/api/peppers')
@login_required
def api_peppers():
    """API endpoint to get pepper list (for AJAX/future use)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    quality_filter = request.args.get('quality', None)
    
    query = BellPepperDetection.query.filter_by(user_id=session['user_id'])
    
    # Apply quality filter if provided
    if quality_filter == 'excellent':
        query = query.filter(BellPepperDetection.quality_score >= 80)
    elif quality_filter == 'good':
        query = query.filter(BellPepperDetection.quality_score >= 60, BellPepperDetection.quality_score < 80)
    elif quality_filter == 'fair':
        query = query.filter(BellPepperDetection.quality_score >= 40, BellPepperDetection.quality_score < 60)
    elif quality_filter == 'poor':
        query = query.filter(BellPepperDetection.quality_score < 40)
    
    peppers_pagination = query.order_by(BellPepperDetection.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'peppers': [p.to_dict() for p in peppers_pagination.items],
        'total': peppers_pagination.total,
        'pages': peppers_pagination.pages,
        'current_page': page
    })

