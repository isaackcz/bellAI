"""
Initialize Pepper Varieties Database
Run this script to populate the pepper varieties database
"""
from app import app
from models import db, PepperVariety
import json

# Pepper Varieties Data
PEPPER_VARIETIES = {
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

def init_varieties():
    """Initialize pepper varieties in the database"""
    with app.app_context():
        print("🌶️  Initializing Pepper Varieties Database...")
        print("=" * 50)
        
        # Check if varieties already exist
        existing_count = PepperVariety.query.count()
        if existing_count > 0:
            print(f"⚠️  Database already contains {existing_count} varieties.")
            response = input("Do you want to clear and reinitialize? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Cancelled.")
                return
            
            # Clear existing varieties
            PepperVariety.query.delete()
            db.session.commit()
            print("🗑️  Cleared existing varieties.")
        
        # Add varieties
        for variety_name, variety_data in PEPPER_VARIETIES.items():
            variety = PepperVariety(
                name=variety_name,
                color=variety_data['color'],
                description=variety_data['description'],
                characteristics=json.dumps(variety_data['characteristics']),
                quality_standards=json.dumps(variety_data['quality_standards']),
                uses=json.dumps(variety_data['uses']),
                storage=variety_data['storage'],
                nutritional_highlights=variety_data['nutritional_highlights']
            )
            db.session.add(variety)
            print(f"✅ Added: {variety_name}")
        
        db.session.commit()
        print("=" * 50)
        print(f"🎉 Successfully initialized {len(PEPPER_VARIETIES)} pepper varieties!")
        
        # Verify
        total = PepperVariety.query.count()
        print(f"📊 Total varieties in database: {total}")

if __name__ == '__main__':
    init_varieties()

