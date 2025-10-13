"""
Export routes for exporting bell pepper analysis data
"""
from flask import render_template, session, redirect, url_for, flash, jsonify, request, send_file, Response
from functools import wraps
from models import db, User, BellPepperDetection, AnalysisHistory
from datetime import datetime, timedelta
import json
import csv
import io
from . import export_bp

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@export_bp.route('/export')
@login_required
def export_page():
    """View export data page"""
    user = User.query.get(session['user_id'])
    
    # Get statistics for export preview
    total_peppers = BellPepperDetection.query.filter_by(user_id=user.id).count()
    total_analyses = AnalysisHistory.query.filter_by(user_id=user.id).count()
    
    # Date range info
    first_analysis = AnalysisHistory.query.filter_by(user_id=user.id)\
        .order_by(AnalysisHistory.created_at.asc()).first()
    last_analysis = AnalysisHistory.query.filter_by(user_id=user.id)\
        .order_by(AnalysisHistory.created_at.desc()).first()
    
    date_range = {
        'start': first_analysis.created_at if first_analysis else None,
        'end': last_analysis.created_at if last_analysis else None
    }
    
    return render_template('export.html',
                         user=user,
                         total_peppers=total_peppers,
                         total_analyses=total_analyses,
                         date_range=date_range)

@export_bp.route('/export/csv')
@login_required
def export_csv():
    """Export pepper data as CSV"""
    user = User.query.get(session['user_id'])
    
    # Get filter parameters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    variety = request.args.get('variety')
    quality = request.args.get('quality')
    
    # Build query
    query = BellPepperDetection.query.filter_by(user_id=user.id)
    
    # Apply filters
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(BellPepperDetection.created_at >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            # Add one day to include the entire end date
            date_to_obj = date_to_obj + timedelta(days=1)
            query = query.filter(BellPepperDetection.created_at < date_to_obj)
        except ValueError:
            pass
    
    if variety:
        query = query.filter_by(variety=variety)
    
    if quality:
        if quality == 'excellent':
            query = query.filter(BellPepperDetection.quality_score >= 80)
        elif quality == 'good':
            query = query.filter(BellPepperDetection.quality_score >= 60, 
                               BellPepperDetection.quality_score < 80)
        elif quality == 'fair':
            query = query.filter(BellPepperDetection.quality_score >= 40, 
                               BellPepperDetection.quality_score < 60)
        elif quality == 'poor':
            query = query.filter(BellPepperDetection.quality_score < 40)
    
    peppers = query.order_by(BellPepperDetection.created_at.desc()).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Date', 'Time', 'Variety', 'Confidence', 
        'Quality Score', 'Quality Category', 'Color Uniformity',
        'Size Consistency', 'Surface Quality', 'Ripeness Level',
        'Health Status', 'Recommendations'
    ])
    
    # Write data
    for pepper in peppers:
        # Parse recommendations
        recommendations = json.loads(pepper.recommendations) if pepper.recommendations else []
        recommendations_text = '; '.join(recommendations) if recommendations else 'None'
        
        writer.writerow([
            pepper.id,
            pepper.created_at.strftime('%Y-%m-%d'),
            pepper.created_at.strftime('%H:%M:%S'),
            pepper.variety,
            f"{pepper.confidence:.2f}",
            f"{pepper.quality_score:.1f}",
            pepper.quality_category,
            f"{pepper.color_uniformity:.1f}" if pepper.color_uniformity else 'N/A',
            f"{pepper.size_consistency:.1f}" if pepper.size_consistency else 'N/A',
            f"{pepper.surface_quality:.1f}" if pepper.surface_quality else 'N/A',
            f"{pepper.ripeness_level:.1f}" if pepper.ripeness_level else 'N/A',
            pepper.health_status or 'Unknown',
            recommendations_text
        ])
    
    # Prepare response
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'pepperai_export_{timestamp}.csv'
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

@export_bp.route('/export/json')
@login_required
def export_json():
    """Export pepper data as JSON"""
    user = User.query.get(session['user_id'])
    
    # Get filter parameters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    variety = request.args.get('variety')
    quality = request.args.get('quality')
    
    # Build query
    query = BellPepperDetection.query.filter_by(user_id=user.id)
    
    # Apply filters (same as CSV)
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(BellPepperDetection.created_at >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            date_to_obj = date_to_obj + timedelta(days=1)
            query = query.filter(BellPepperDetection.created_at < date_to_obj)
        except ValueError:
            pass
    
    if variety:
        query = query.filter_by(variety=variety)
    
    if quality:
        if quality == 'excellent':
            query = query.filter(BellPepperDetection.quality_score >= 80)
        elif quality == 'good':
            query = query.filter(BellPepperDetection.quality_score >= 60, 
                               BellPepperDetection.quality_score < 80)
        elif quality == 'fair':
            query = query.filter(BellPepperDetection.quality_score >= 40, 
                               BellPepperDetection.quality_score < 60)
        elif quality == 'poor':
            query = query.filter(BellPepperDetection.quality_score < 40)
    
    peppers = query.order_by(BellPepperDetection.created_at.desc()).all()
    
    # Build JSON data
    export_data = {
        'export_date': datetime.now().isoformat(),
        'user': user.username,
        'total_records': len(peppers),
        'filters': {
            'date_from': date_from,
            'date_to': date_to,
            'variety': variety,
            'quality': quality
        },
        'data': []
    }
    
    for pepper in peppers:
        pepper_data = {
            'id': pepper.id,
            'pepper_id': pepper.pepper_id,
            'date': pepper.created_at.strftime('%Y-%m-%d'),
            'time': pepper.created_at.strftime('%H:%M:%S'),
            'variety': pepper.variety,
            'confidence': round(pepper.confidence, 2),
            'quality': {
                'score': round(pepper.quality_score, 1),
                'category': pepper.quality_category,
                'color_uniformity': round(pepper.color_uniformity, 1) if pepper.color_uniformity else None,
                'size_consistency': round(pepper.size_consistency, 1) if pepper.size_consistency else None,
                'surface_quality': round(pepper.surface_quality, 1) if pepper.surface_quality else None,
                'ripeness_level': round(pepper.ripeness_level, 1) if pepper.ripeness_level else None
            },
            'health_status': pepper.health_status,
            'recommendations': json.loads(pepper.recommendations) if pepper.recommendations else [],
            'advanced_analysis': json.loads(pepper.advanced_analysis) if pepper.advanced_analysis else {},
            'disease_analysis': json.loads(pepper.disease_analysis) if pepper.disease_analysis else {}
        }
        export_data['data'].append(pepper_data)
    
    # Create JSON file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'pepperai_export_{timestamp}.json'
    
    json_str = json.dumps(export_data, indent=2)
    
    return Response(
        json_str,
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

@export_bp.route('/export/summary')
@login_required
def export_summary():
    """Export summary statistics as JSON"""
    user = User.query.get(session['user_id'])
    
    # Overall statistics
    total_peppers = BellPepperDetection.query.filter_by(user_id=user.id).count()
    total_analyses = AnalysisHistory.query.filter_by(user_id=user.id).count()
    
    avg_quality = db.session.query(db.func.avg(BellPepperDetection.quality_score))\
        .filter_by(user_id=user.id).scalar() or 0
    
    # Quality distribution
    excellent_count = BellPepperDetection.query.filter_by(user_id=user.id)\
        .filter(BellPepperDetection.quality_score >= 80).count()
    good_count = BellPepperDetection.query.filter_by(user_id=user.id)\
        .filter(BellPepperDetection.quality_score >= 60, BellPepperDetection.quality_score < 80).count()
    fair_count = BellPepperDetection.query.filter_by(user_id=user.id)\
        .filter(BellPepperDetection.quality_score >= 40, BellPepperDetection.quality_score < 60).count()
    poor_count = BellPepperDetection.query.filter_by(user_id=user.id)\
        .filter(BellPepperDetection.quality_score < 40).count()
    
    # Variety distribution
    variety_stats = db.session.query(
        BellPepperDetection.variety,
        db.func.count(BellPepperDetection.id).label('count')
    ).filter_by(user_id=user.id).group_by(BellPepperDetection.variety).all()
    
    summary_data = {
        'export_date': datetime.now().isoformat(),
        'user': user.username,
        'summary': {
            'total_peppers': total_peppers,
            'total_analyses': total_analyses,
            'average_quality': round(avg_quality, 1)
        },
        'quality_distribution': {
            'excellent': excellent_count,
            'good': good_count,
            'fair': fair_count,
            'poor': poor_count
        },
        'variety_distribution': {variety: count for variety, count in variety_stats}
    }
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'pepperai_summary_{timestamp}.json'
    
    json_str = json.dumps(summary_data, indent=2)
    
    return Response(
        json_str,
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

