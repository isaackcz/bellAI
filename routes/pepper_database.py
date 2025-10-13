"""
Pepper Database routes for viewing bell pepper varieties and information
"""
from flask import render_template, session, redirect, url_for, flash, jsonify, request
from functools import wraps
from models import db, User, BellPepperDetection, PepperType, PepperVariety, PepperDisease
from sqlalchemy import func
from . import pepper_database_bp

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Initialize pepper varieties data (will be moved to database)
PEPPER_VARIETIES_INIT = {
    'Red Bell Pepper': {
        'color': '#DC2626',
        'description': 'Fully ripened bell peppers with a sweet, mild flavor and crisp texture.',
        'characteristics': [
            'Sweetest of all bell pepper varieties',
            'Rich in vitamin C and beta-carotene',
            'Highest sugar content (6-8% Brix)',
            'Best for fresh consumption'
        ],
        'quality_standards': {
            'color': 'Deep red, uniform coloring',
            'firmness': 'Firm and crisp to touch',
            'surface': 'Smooth, glossy skin without blemishes',
            'size': '3-4 inches in diameter'
        },
        'uses': ['Fresh salads', 'Roasting', 'Stuffing', 'Grilling', 'Raw snacking'],
        'storage': 'Refrigerate for 1-2 weeks',
        'nutritional_highlights': 'High in Vitamin C (190% DV), Vitamin A, B6, and antioxidants'
    },
    'Yellow Bell Pepper': {
        'color': '#F59E0B',
        'description': 'Moderately ripened peppers with a tangy-sweet flavor and bright yellow color.',
        'characteristics': [
            'Slightly sweeter than green peppers',
            'Good source of vitamin C',
            'Moderate sugar content (4-6% Brix)',
            'Crisp and juicy texture'
        ],
        'quality_standards': {
            'color': 'Bright yellow, consistent coloring',
            'firmness': 'Firm with slight give',
            'surface': 'Smooth, shiny appearance',
            'size': '3-4 inches in diameter'
        },
        'uses': ['Stir-fries', 'Fajitas', 'Salads', 'Sautéing', 'Pizza toppings'],
        'storage': 'Refrigerate for 1-2 weeks',
        'nutritional_highlights': 'High in Vitamin C (155% DV), folate, and flavonoids'
    },
    'Orange Bell Pepper': {
        'color': '#F97316',
        'description': 'Mid-ripeness peppers with a fruity, sweet taste and vibrant orange hue.',
        'characteristics': [
            'Sweet with subtle fruity notes',
            'Rich in beta-carotene',
            'Medium-high sugar content (5-7% Brix)',
            'Excellent for cooking'
        ],
        'quality_standards': {
            'color': 'Vibrant orange throughout',
            'firmness': 'Firm and crunchy',
            'surface': 'Glossy, unblemished skin',
            'size': '3-4 inches in diameter'
        },
        'uses': ['Roasting', 'Grilling', 'Salsas', 'Smoothies', 'Stews'],
        'storage': 'Refrigerate for 1-2 weeks',
        'nutritional_highlights': 'High in Vitamin C (165% DV), Vitamin A, and antioxidants'
    },
    'Green Bell Pepper': {
        'color': '#10B981',
        'description': 'Unripened bell peppers with a slightly bitter, grassy flavor and firm texture.',
        'characteristics': [
            'Most widely available variety',
            'Slightly bitter, less sweet',
            'Low sugar content (2-4% Brix)',
            'Firmest texture of all varieties'
        ],
        'quality_standards': {
            'color': 'Dark green, uniform coloring',
            'firmness': 'Very firm and crisp',
            'surface': 'Smooth, tight skin',
            'size': '3-4 inches in diameter'
        },
        'uses': ['Cooking', 'Stuffing', 'Stir-fries', 'Fajitas', 'Chili'],
        'storage': 'Refrigerate for 2-3 weeks (longest shelf life)',
        'nutritional_highlights': 'Good source of Vitamin C (120% DV), Vitamin K, and fiber'
    },
    'Purple Bell Pepper': {
        'color': '#7C3AED',
        'description': 'Rare variety with a unique purple color and mild, slightly sweet flavor.',
        'characteristics': [
            'Contains anthocyanins (purple pigments)',
            'Mild, slightly sweet taste',
            'Turns green when cooked',
            'Best consumed raw'
        ],
        'quality_standards': {
            'color': 'Deep purple to violet',
            'firmness': 'Firm with crisp texture',
            'surface': 'Smooth, glossy finish',
            'size': '2.5-3.5 inches in diameter'
        },
        'uses': ['Fresh salads', 'Garnishes', 'Raw platters', 'Pickling'],
        'storage': 'Refrigerate for 1 week',
        'nutritional_highlights': 'High in anthocyanins, Vitamin C (135% DV), antioxidants'
    },
    'White Bell Pepper': {
        'color': '#E5E7EB',
        'description': 'Rare variety with pale color, transitioning from green to red.',
        'characteristics': [
            'Mild, sweet flavor',
            'Less common variety',
            'Transition stage between green and red',
            'Tender texture'
        ],
        'quality_standards': {
            'color': 'Pale white to cream',
            'firmness': 'Moderately firm',
            'surface': 'Smooth, light-colored skin',
            'size': '3-3.5 inches in diameter'
        },
        'uses': ['Salads', 'Garnishes', 'Light cooking', 'Decorative purposes'],
        'storage': 'Refrigerate for 1 week',
        'nutritional_highlights': 'Moderate Vitamin C (100% DV), mild antioxidants'
    }
}

@pepper_database_bp.route('/pepper-database')
@login_required
def pepper_database():
    """View bell pepper varieties database organized by type"""
    user = User.query.get(session['user_id'])
    
    # Get all pepper types with their varieties from database
    pepper_types = PepperType.query.order_by(PepperType.order_index).all()
    
    # Organize data by type
    types_data = []
    for pepper_type in pepper_types:
        varieties_list = []
        for variety in pepper_type.varieties:
            varieties_list.append(variety.to_dict())
        
        types_data.append({
            'type_info': pepper_type.to_dict(),
            'varieties': varieties_list
        })
    
    # Get user's variety statistics from database
    user_variety_stats = db.session.query(
        BellPepperDetection.variety,
        func.count(BellPepperDetection.id).label('count'),
        func.avg(BellPepperDetection.quality_score).label('avg_quality')
    ).filter_by(user_id=user.id).group_by(BellPepperDetection.variety).all()
    
    # Create a dictionary for easy lookup
    user_stats_dict = {
        variety: {'count': count, 'avg_quality': round(avg_quality, 1) if avg_quality else 0}
        for variety, count, avg_quality in user_variety_stats
    }
    
    # Total peppers analyzed
    total_analyzed = sum(stats['count'] for stats in user_stats_dict.values())
    
    # Get example peppers for each variety
    example_peppers = {}
    all_varieties = PepperVariety.query.all()
    for variety in all_varieties:
        # Get top 3 highest quality peppers of this variety from the user's data
        examples = BellPepperDetection.query.filter_by(
            user_id=user.id,
            variety=variety.name
        ).filter(
            BellPepperDetection.crop_path.isnot(None)
        ).order_by(
            BellPepperDetection.quality_score.desc()
        ).limit(3).all()
        
        if examples:
            example_peppers[variety.name] = examples
    
    # Get all diseases from database
    diseases = PepperDisease.query.order_by(PepperDisease.severity.desc()).all()
    diseases_data = [disease.to_dict() for disease in diseases]
    
    return render_template('pepper_database.html',
                         user=user,
                         types_data=types_data,
                         user_stats=user_stats_dict,
                         total_analyzed=total_analyzed,
                         example_peppers=example_peppers,
                         diseases=diseases_data)

@pepper_database_bp.route('/pepper-database/variety/<variety_name>')
@login_required
def variety_detail(variety_name):
    """View detailed information about a specific pepper variety"""
    user = User.query.get(session['user_id'])
    
    # Get variety from database
    variety = PepperVariety.query.filter_by(name=variety_name).first()
    
    if not variety:
        return jsonify({'error': 'Pepper variety not found'}), 404
    
    variety_info = variety.to_dict()
    
    # Get user's data for this variety from database
    user_peppers = BellPepperDetection.query.filter_by(
        user_id=user.id,
        variety=variety_name
    ).order_by(BellPepperDetection.created_at.desc()).limit(10).all()
    
    # Calculate statistics for this variety
    total_count = BellPepperDetection.query.filter_by(
        user_id=user.id,
        variety=variety_name
    ).count()
    
    avg_quality = db.session.query(func.avg(BellPepperDetection.quality_score))\
        .filter_by(user_id=user.id, variety=variety_name).scalar() or 0
    
    # Get example peppers with images (top quality examples)
    example_peppers = BellPepperDetection.query.filter_by(
        user_id=user.id,
        variety=variety_name
    ).filter(
        BellPepperDetection.crop_path.isnot(None)
    ).order_by(
        BellPepperDetection.quality_score.desc()
    ).limit(6).all()
    
    return jsonify({
        'variety_name': variety_name,
        'info': variety_info,
        'user_data': {
            'total_analyzed': total_count,
            'average_quality': round(avg_quality, 1),
            'recent_peppers': [
                {
                    'id': p.id,
                    'quality_score': p.quality_score,
                    'created_at': p.created_at.strftime('%Y-%m-%d %H:%M')
                }
                for p in user_peppers
            ],
            'example_peppers': [
                {
                    'id': p.id,
                    'crop_path': p.crop_path,
                    'quality_score': round(p.quality_score, 1),
                    'quality_category': p.quality_category,
                    'created_at': p.created_at.strftime('%b %d, %Y'),
                    'timestamp': p.created_at.timestamp()
                }
                for p in example_peppers
            ]
        }
    })

