"""
Initialize Pepper Types and Varieties Database
Run this script to populate the pepper database with hierarchical structure
"""
from app import app
from models import db, PepperType, PepperVariety
import json

# Pepper Types and Varieties Data (organized by ripeness/maturity)
PEPPER_DATA = {
    'Fully Ripened Bell Peppers': {
        'type_info': {
            'description': 'Fully matured bell peppers with peak sweetness and vibrant colors. These peppers have reached their final ripeness stage and offer the sweetest flavor profile.',
            'icon': 'fas fa-medal',
            'color': '#DC2626',
            'order_index': 1
        },
        'varieties': {
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
            'Orange Bell Pepper': {
                'color': '#F97316',
                'description': 'Fully ripened peppers with a fruity, sweet taste and vibrant orange hue.',
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
            }
        }
    },
    'Partially Ripened Bell Peppers': {
        'type_info': {
            'description': 'Mid-maturity bell peppers transitioning from green to their final color. These peppers offer a balance of sweetness and mild flavor.',
            'icon': 'fas fa-sun',
            'color': '#F59E0B',
            'order_index': 2
        },
        'varieties': {
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
            }
        }
    },
    'Unripened Bell Peppers': {
        'type_info': {
            'description': 'Early harvest bell peppers with firm texture and grassy flavor. These are the same peppers before they ripen to other colors.',
            'icon': 'fas fa-leaf',
            'color': '#10B981',
            'order_index': 3
        },
        'varieties': {
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
            }
        }
    },
    'Specialty Bell Peppers': {
        'type_info': {
            'description': 'Rare and specialty bell pepper varieties with unique colors and flavors. These varieties offer visual appeal and distinct taste profiles.',
            'icon': 'fas fa-gem',
            'color': '#7C3AED',
            'order_index': 4
        },
        'varieties': {
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
    }
}

def init_types_and_varieties():
    """Initialize pepper types and varieties in the database"""
    with app.app_context():
        print("🌶️  Initializing Pepper Types and Varieties Database...")
        print("=" * 60)
        
        # Check if data already exists
        existing_types = PepperType.query.count()
        existing_varieties = PepperVariety.query.count()
        
        if existing_types > 0 or existing_varieties > 0:
            print(f"⚠️  Database already contains {existing_types} types and {existing_varieties} varieties.")
            response = input("Do you want to clear and reinitialize? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Cancelled.")
                return
            
            # Clear existing data
            PepperVariety.query.delete()
            PepperType.query.delete()
            db.session.commit()
            print("🗑️  Cleared existing data.")
        
        # Add types and varieties
        total_types = 0
        total_varieties = 0
        
        for type_name, type_data in PEPPER_DATA.items():
            # Create pepper type
            pepper_type = PepperType(
                name=type_name,
                description=type_data['type_info']['description'],
                icon=type_data['type_info']['icon'],
                color=type_data['type_info']['color'],
                order_index=type_data['type_info']['order_index']
            )
            db.session.add(pepper_type)
            db.session.flush()  # Get the ID
            total_types += 1
            print(f"\n📁 Added Type: {type_name}")
            
            # Add varieties under this type
            for variety_name, variety_data in type_data['varieties'].items():
                variety = PepperVariety(
                    type_id=pepper_type.id,
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
                total_varieties += 1
                print(f"   ✅ Added Variety: {variety_name}")
        
        db.session.commit()
        print("\n" + "=" * 60)
        print(f"🎉 Successfully initialized {total_types} pepper types with {total_varieties} varieties!")
        
        # Verify
        final_types = PepperType.query.count()
        final_varieties = PepperVariety.query.count()
        print(f"📊 Total types in database: {final_types}")
        print(f"📊 Total varieties in database: {final_varieties}")

if __name__ == '__main__':
    init_types_and_varieties()

