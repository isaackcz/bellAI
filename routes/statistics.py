"""
Statistics routes for viewing bell pepper analysis statistics
"""
from flask import render_template, session, redirect, url_for, flash, jsonify, request
from functools import wraps
from models import db, User, BellPepperDetection, AnalysisHistory
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from . import statistics_bp

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@statistics_bp.route('/statistics')
@login_required
def statistics():
    """View comprehensive statistics for the current user"""
    user = User.query.get(session['user_id'])
    
    # Overall Statistics
    total_peppers = BellPepperDetection.query.filter_by(user_id=user.id).count()
    total_analyses = AnalysisHistory.query.filter_by(user_id=user.id).count()
    
    # Average quality score
    avg_quality = db.session.query(func.avg(BellPepperDetection.quality_score))\
        .filter_by(user_id=user.id).scalar() or 0
    
    # Average confidence
    avg_confidence = db.session.query(func.avg(BellPepperDetection.confidence))\
        .filter_by(user_id=user.id).scalar() or 0
    
    # Quality Distribution
    excellent_count = BellPepperDetection.query.filter_by(user_id=user.id)\
        .filter(BellPepperDetection.quality_score >= 80).count()
    good_count = BellPepperDetection.query.filter_by(user_id=user.id)\
        .filter(BellPepperDetection.quality_score >= 60, BellPepperDetection.quality_score < 80).count()
    fair_count = BellPepperDetection.query.filter_by(user_id=user.id)\
        .filter(BellPepperDetection.quality_score >= 40, BellPepperDetection.quality_score < 60).count()
    poor_count = BellPepperDetection.query.filter_by(user_id=user.id)\
        .filter(BellPepperDetection.quality_score < 40).count()
    
    quality_distribution = {
        'excellent': excellent_count,
        'good': good_count,
        'fair': fair_count,
        'poor': poor_count
    }
    
    # Variety Distribution (limit to top 10)
    variety_stats = db.session.query(
        BellPepperDetection.variety,
        func.count(BellPepperDetection.id).label('count'),
        func.avg(BellPepperDetection.quality_score).label('avg_quality')
    ).filter_by(user_id=user.id).group_by(BellPepperDetection.variety)\
        .order_by(func.count(BellPepperDetection.id).desc())\
        .limit(10).all()
    
    # Convert to list of dicts
    variety_data = []
    for variety, count, avg_qual in variety_stats:
        variety_data.append({
            'variety': variety,
            'count': count,
            'avg_quality': round(avg_qual, 1) if avg_qual else 0
        })
    
    # Quality Metrics Averages
    avg_color_uniformity = db.session.query(func.avg(BellPepperDetection.color_uniformity))\
        .filter_by(user_id=user.id).scalar() or 0
    avg_size_consistency = db.session.query(func.avg(BellPepperDetection.size_consistency))\
        .filter_by(user_id=user.id).scalar() or 0
    avg_surface_quality = db.session.query(func.avg(BellPepperDetection.surface_quality))\
        .filter_by(user_id=user.id).scalar() or 0
    
    quality_metrics = {
        'color_uniformity': round(avg_color_uniformity, 1),
        'size_consistency': round(avg_size_consistency, 1),
        'surface_quality': round(avg_surface_quality, 1)
    }
    
    # Temporal Analysis - Last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_peppers = BellPepperDetection.query.filter_by(user_id=user.id)\
        .filter(BellPepperDetection.created_at >= thirty_days_ago).all()
    
    # Group by date
    daily_counts = {}
    for pepper in recent_peppers:
        date_key = pepper.created_at.strftime('%Y-%m-%d')
        if date_key not in daily_counts:
            daily_counts[date_key] = 0
        daily_counts[date_key] += 1
    
    # Fill in missing dates with 0
    temporal_data = []
    for i in range(30):
        date = (datetime.utcnow() - timedelta(days=29-i)).strftime('%Y-%m-%d')
        temporal_data.append({
            'date': date,
            'count': daily_counts.get(date, 0)
        })
    
    # Top Quality Peppers (highest scores)
    top_peppers = BellPepperDetection.query.filter_by(user_id=user.id)\
        .order_by(BellPepperDetection.quality_score.desc())\
        .limit(5).all()
    
    # Recent Activity
    recent_activity = BellPepperDetection.query.filter_by(user_id=user.id)\
        .order_by(BellPepperDetection.created_at.desc())\
        .limit(10).all()
    
    # Disease Statistics (if available)
    healthy_count = BellPepperDetection.query.filter_by(user_id=user.id)\
        .filter(BellPepperDetection.health_status == 'healthy').count()
    diseased_count = BellPepperDetection.query.filter_by(user_id=user.id)\
        .filter(BellPepperDetection.health_status != 'healthy')\
        .filter(BellPepperDetection.health_status != None).count()
    
    health_stats = {
        'healthy': healthy_count,
        'diseased': diseased_count
    }
    
    return render_template('statistics.html',
                         user=user,
                         total_peppers=total_peppers,
                         total_analyses=total_analyses,
                         avg_quality=round(avg_quality, 1),
                         avg_confidence=round(avg_confidence, 2),
                         quality_distribution=quality_distribution,
                         variety_data=variety_data,
                         quality_metrics=quality_metrics,
                         temporal_data=temporal_data,
                         top_peppers=top_peppers,
                         recent_activity=recent_activity,
                         health_stats=health_stats)

@statistics_bp.route('/statistics/api/data')
@login_required
def statistics_api():
    """API endpoint for statistics data (for AJAX updates)"""
    user = User.query.get(session['user_id'])
    
    # Get time period filter
    period = request.args.get('period', '30')  # days
    
    try:
        days = int(period)
    except ValueError:
        days = 30
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get peppers in time period
    peppers = BellPepperDetection.query.filter_by(user_id=user.id)\
        .filter(BellPepperDetection.created_at >= start_date).all()
    
    # Calculate statistics
    total_peppers = len(peppers)
    avg_quality = sum(p.quality_score for p in peppers) / total_peppers if total_peppers > 0 else 0
    
    # Quality distribution
    quality_dist = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}
    for pepper in peppers:
        if pepper.quality_score >= 80:
            quality_dist['excellent'] += 1
        elif pepper.quality_score >= 60:
            quality_dist['good'] += 1
        elif pepper.quality_score >= 40:
            quality_dist['fair'] += 1
        else:
            quality_dist['poor'] += 1
    
    return jsonify({
        'total_peppers': total_peppers,
        'avg_quality': round(avg_quality, 1),
        'quality_distribution': quality_dist,
        'period': days
    })

