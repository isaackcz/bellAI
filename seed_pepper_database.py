#!/usr/bin/env python3
"""Seed pepper database with initial data"""
from app import app, db
from models import PepperType, PepperVariety, PepperDisease
import json

with app.app_context():
    print("🌶️ Seeding pepper database...")
    
    # Create Pepper Type
    pepper_type = PepperType.query.filter_by(name='Bell Pepper Varieties').first()
    if not pepper_type:
        pepper_type = PepperType(
            name='Bell Pepper Varieties',
            description='Common bell pepper varieties with different ripeness stages',
            icon='fa-pepper-hot',
            color='#16a34a',
            order_index=1
        )
        db.session.add(pepper_type)
        db.session.flush()
        print("✅ Created pepper type: Bell Pepper Varieties")
    else:
        print("✅ Pepper type already exists")
    
    # Pepper Varieties Data
    varieties_data = [
        {
            'name': 'Red Bell Pepper',
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
        {
            'name': 'Yellow Bell Pepper',
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
        {
            'name': 'Orange Bell Pepper',
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
        {
            'name': 'Green Bell Pepper',
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
        {
            'name': 'Purple Bell Pepper',
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
        {
            'name': 'White Bell Pepper',
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
    ]
    
    # Create Pepper Varieties
    created_varieties = 0
    for v_data in varieties_data:
        existing = PepperVariety.query.filter_by(name=v_data['name']).first()
        if not existing:
            variety = PepperVariety(
                type_id=pepper_type.id,
                name=v_data['name'],
                color=v_data['color'],
                description=v_data['description'],
                characteristics=json.dumps(v_data['characteristics']),
                quality_standards=json.dumps(v_data['quality_standards']),
                uses=json.dumps(v_data['uses']),
                storage=v_data['storage'],
                nutritional_highlights=v_data['nutritional_highlights']
            )
            db.session.add(variety)
            created_varieties += 1
            print(f"  ✅ Created variety: {v_data['name']}")
    
    # Diseases Data (from old database)
    diseases_data = [
        {
            'name': 'Bacterial Leaf Spot',
            'scientific_name': 'Xanthomonas campestris pv. vesicatoria',
            'description': 'A common bacterial disease causing dark spots on leaves and fruits, leading to defoliation and reduced yield.',
            'symptoms': [
                'Small, dark brown or black spots on leaves',
                'Yellow halo around spots',
                'Raised, scab-like lesions on fruits',
                'Leaf curling and premature drop',
                'Reduced plant vigor'
            ],
            'causes': [
                'Bacterial infection from contaminated seeds',
                'Spread through water splash and wind',
                'High humidity and warm temperatures (75-86°F)',
                'Overhead irrigation',
                'Infected plant debris'
            ],
            'prevention': [
                'Use disease-free certified seeds',
                'Practice crop rotation (3-4 years)',
                'Avoid overhead watering',
                'Remove and destroy infected plants',
                'Maintain proper plant spacing for air circulation',
                'Disinfect tools between uses'
            ],
            'treatment': [
                'Apply copper-based bactericides',
                'Remove and destroy severely infected plants',
                'Improve air circulation',
                'Reduce leaf wetness duration',
                'Use drip irrigation instead of overhead'
            ],
            'severity': 'severe',
            'visual_indicators': [
                'Dark spots on leaves',
                'Yellow halos',
                'Fruit lesions',
                'Leaf drop'
            ],
            'affected_parts': 'Leaves, Stems, Fruits',
            'color': '#DC2626',
            'icon': 'fas fa-virus',
            'images': [
                'https://csassets.static.wvu.edu/o2gpsy/50d2bf3d-125f-4b45-9c03-487959bd8344/0862b40bec913b574f1f05f79f2805c7/figure-2-tattered%20appearance%20on%20the%20affected%20leaves-893x595.jpg',
                'https://backbonevalleynursery.com/wp-content/uploads/2021/05/pepper-bacterial-leaf-spot2-scaled.jpegjpg',
                'https://plant-pest-advisory.rutgers.edu/wp-content/uploads/2020/08/BLS-pepper-2020-scaled.jpg'
            ]
        },
        {
            'name': 'Phytophthora Blight',
            'scientific_name': 'Phytophthora capsici',
            'description': 'A devastating oomycete disease affecting all parts of the pepper plant, causing rapid wilting and death.',
            'symptoms': [
                'Dark, water-soaked lesions on stems',
                'Sudden wilting of entire plant',
                'White mold growth on affected areas',
                'Root rot with dark, mushy roots',
                'Fruit rot with white cottony growth'
            ],
            'causes': [
                'Soilborne pathogen',
                'Excess moisture and poor drainage',
                'Contaminated irrigation water',
                'High temperatures (77-86°F)',
                'Compacted or heavy clay soils'
            ],
            'prevention': [
                'Improve soil drainage',
                'Use raised beds',
                'Avoid over-watering',
                'Plant resistant varieties',
                'Practice 3-year crop rotation',
                'Use pathogen-free transplants'
            ],
            'treatment': [
                'Remove and destroy infected plants immediately',
                'Apply fungicides (Ridomil, Aliette)',
                'Improve drainage',
                'Reduce irrigation frequency',
                'Avoid working with wet plants'
            ],
            'severity': 'severe',
            'visual_indicators': [
                'Stem lesions',
                'Plant wilting',
                'White mold',
                'Root rot'
            ],
            'affected_parts': 'Roots, Stems, Leaves, Fruits',
            'color': '#EF4444',
            'icon': 'fas fa-exclamation-triangle',
            'images': [
                'https://www.koppert.com/content/_processed_/2/f/csm_stem_and_fruit_rot_of_capsicum_phytophthora_capsici_damage_4_koppert_71e51c5003.jpg',
                'https://msu-prod.dotcmscloud.com/uploads/images/7-29-11%20MARY%20pepper-Phytophthora--4.jpg',
                'https://eorganic.info/sites/eorganic.info/files/u424/pepper%20phytophthora%202.jpg'
            ]
        },
        {
            'name': 'Anthracnose',
            'scientific_name': 'Colletotrichum spp.',
            'description': 'A fungal disease primarily affecting ripe fruits, causing sunken circular lesions and significant post-harvest losses.',
            'symptoms': [
                'Circular, sunken spots on ripe fruits',
                'Dark brown to black lesions',
                'Pink or orange spore masses in lesions',
                'Soft, watery decay',
                'Premature fruit drop'
            ],
            'causes': [
                'Fungal spores spread by rain splash',
                'High humidity and warm temperatures',
                'Wounded or overripe fruits',
                'Poor air circulation',
                'Overhead irrigation'
            ],
            'prevention': [
                'Harvest fruits before full ripening',
                'Avoid fruit injury during handling',
                'Practice crop rotation',
                'Remove plant debris',
                'Provide good air circulation',
                'Use mulch to prevent soil splash'
            ],
            'treatment': [
                'Apply fungicides (Chlorothalonil, Mancozeb)',
                'Remove and destroy infected fruits',
                'Harvest promptly when ripe',
                'Improve plant spacing',
                'Use drip irrigation'
            ],
            'severity': 'moderate',
            'visual_indicators': [
                'Circular fruit spots',
                'Sunken lesions',
                'Pink spore masses'
            ],
            'affected_parts': 'Fruits',
            'color': '#F59E0B',
            'icon': 'fas fa-circle-notch',
            'images': [
                'https://media.springernature.com/lw685/springer-static/image/art%3A10.1007%2Fs12600-014-0428-z/MediaObjects/12600_2014_428_Fig1_HTML.gif',
                'https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEifcm_3jxWigeoY1oGG7_E56YxYouVtayJpS9myFoGYiyu0iya9132kRdBBb4CNz1SqWv4KEkcoCdvnHPfKTNPxY_jBxZ-zJ8_ZKp01ViFxDDvcct8PwUQUlFYJ5wdeH953TaGv31bqd84I4Kil_5rO3ZoS6D9JmvUwwuOXoc9aRFaEACUcKAisnPcFVTAO/s799/early%20blight%20in%20pepper.jpg',
                'https://plant-pest-advisory.rutgers.edu/wp-content/uploads/2014/01/Pepper-Anthracnose.jpg'
            ]
        },
        {
            'name': 'Powdery Mildew',
            'scientific_name': 'Leveillula taurica',
            'description': 'A fungal disease characterized by white powdery growth on leaves, reducing photosynthesis and plant vigor.',
            'symptoms': [
                'White to gray powdery spots on upper leaf surface',
                'Yellow patches on lower leaf surface',
                'Leaf curling and distortion',
                'Premature leaf drop',
                'Stunted plant growth'
            ],
            'causes': [
                'Fungal spores spread by wind',
                'Moderate temperatures (60-80°F)',
                'Low to moderate humidity',
                'Shaded, crowded conditions',
                'Poor air circulation'
            ],
            'prevention': [
                'Plant resistant varieties',
                'Provide adequate plant spacing',
                'Prune for good air flow',
                'Avoid excessive nitrogen fertilization',
                'Remove infected leaves promptly',
                'Use preventive fungicide sprays'
            ],
            'treatment': [
                'Apply sulfur-based fungicides',
                'Use potassium bicarbonate sprays',
                'Remove heavily infected leaves',
                'Improve air circulation',
                'Apply neem oil or horticultural oils'
            ],
            'severity': 'moderate',
            'visual_indicators': [
                'White powdery coating',
                'Yellow leaf patches',
                'Leaf curling'
            ],
            'affected_parts': 'Leaves',
            'color': '#A855F7',
            'icon': 'fas fa-snowflake',
            'images': [
                'https://www.researchgate.net/profile/Jose-Eladio-Monge-Perez/publication/352425945/figure/fig6/AS:1035168928235523@1623814913728/Figura-6-Mildiu-polvoso-Leveillula-taurica.jpg',
                'https://bsppjournals.onlinelibrary.wiley.com/cms/asset/7d00056c-550a-431a-875c-074e9524d58d/mpp70128-toc-0001-m.jpg',
                'https://bugwoodcloud.org/images/768x512/5627112.jpg'
            ]
        },
        {
            'name': 'Blossom End Rot',
            'scientific_name': 'Calcium deficiency disorder',
            'description': 'A physiological disorder caused by calcium deficiency, resulting in dark, sunken areas on the blossom end of fruits.',
            'symptoms': [
                'Dark, water-soaked spots on fruit bottom',
                'Sunken, leathery brown or black areas',
                'Affects developing fruits',
                'Secondary fungal infections possible',
                'Reduced fruit quality and marketability'
            ],
            'causes': [
                'Calcium deficiency in fruits',
                'Inconsistent watering patterns',
                'High salt levels in soil',
                'Excessive nitrogen fertilization',
                'Rapid plant growth',
                'Root damage'
            ],
            'prevention': [
                'Maintain consistent soil moisture',
                'Mulch to regulate soil moisture',
                'Avoid excessive nitrogen fertilizer',
                'Ensure adequate calcium in soil',
                'Use drip irrigation',
                'Maintain proper soil pH (6.0-6.8)'
            ],
            'treatment': [
                'Apply calcium supplements (foliar spray)',
                'Maintain even soil moisture',
                'Remove affected fruits',
                'Adjust fertilization program',
                'Improve irrigation management',
                'Add lime or gypsum to soil if needed'
            ],
            'severity': 'mild',
            'visual_indicators': [
                'Dark spots on fruit bottom',
                'Sunken areas',
                'Leathery texture'
            ],
            'affected_parts': 'Fruits',
            'color': '#78350F',
            'icon': 'fas fa-dot-circle',
            'images': [
                'https://www.yara.co.uk/contentassets/4901610900644364a5eaaf2b4658decf/8359/',
                'https://bugwoodcloud.org/images/768x512/5368827.jpg'
            ]
        },
        {
            'name': 'Pepper Mosaic Virus',
            'scientific_name': 'Pepper Mild Mottle Virus / Tobacco Mosaic Virus',
            'description': 'Viral diseases causing mottled, distorted leaves and reduced fruit quality, transmitted mechanically and by aphids.',
            'symptoms': [
                'Mosaic pattern of light and dark green on leaves',
                'Leaf distortion and puckering',
                'Stunted plant growth',
                'Mottled, deformed fruits',
                'Reduced yield and quality'
            ],
            'causes': [
                'Viral infection spread by aphids',
                'Mechanical transmission through tools',
                'Infected seeds or transplants',
                'Contact with infected plants',
                'Contaminated hands or equipment'
            ],
            'prevention': [
                'Use virus-free certified seeds',
                'Control aphid populations',
                'Remove infected plants immediately',
                'Disinfect tools regularly',
                'Wash hands before handling plants',
                'Avoid tobacco use near plants'
            ],
            'treatment': [
                'No cure - remove infected plants',
                'Control aphid vectors',
                'Use reflective mulches',
                'Plant resistant varieties',
                'Maintain strict sanitation'
            ],
            'severity': 'moderate',
            'visual_indicators': [
                'Mosaic leaf pattern',
                'Leaf distortion',
                'Stunted growth'
            ],
            'affected_parts': 'Leaves, Fruits',
            'color': '#10B981',
            'icon': 'fas fa-project-diagram',
            'images': [
                'https://cdn.mos.cms.futurecdn.net/v2/t:480,l:0,cw:1024,ch:576,q:80,w:1024/uxbqnsoovvan7Kw3WwrWVi.jpg',
                'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRADDRk4itAEGsd0jmN8DCE_uB4o7qhlq2DNA&s'
            ]
        },
        {
            'name': 'Gray Mold',
            'scientific_name': 'Botrytis cinerea',
            'description': 'A fungal disease affecting flowers, fruits, and stems, causing gray fuzzy mold growth and soft rot.',
            'symptoms': [
                'Gray fuzzy mold on plant parts',
                'Brown, water-soaked lesions',
                'Soft rot of fruits',
                'Flower blight and drop',
                'Stem cankers'
            ],
            'causes': [
                'High humidity (above 85%)',
                'Cool temperatures (60-75°F)',
                'Poor air circulation',
                'Dense plant canopy',
                'Wounded plant tissue',
                'Overhead irrigation'
            ],
            'prevention': [
                'Maintain good air circulation',
                'Avoid overhead watering',
                'Remove dead plant material',
                'Prune for better airflow',
                'Control humidity in greenhouses',
                'Handle plants carefully to avoid wounds'
            ],
            'treatment': [
                'Apply fungicides (Botran, Switch)',
                'Remove infected plant parts',
                'Improve ventilation',
                'Reduce humidity',
                'Avoid watering late in day'
            ],
            'severity': 'moderate',
            'visual_indicators': [
                'Gray fuzzy mold',
                'Brown lesions',
                'Soft fruit rot'
            ],
            'affected_parts': 'Flowers, Fruits, Stems',
            'color': '#6B7280',
            'icon': 'fas fa-cloud',
            'images': [
                'https://d3qz1qhhp9wxfa.cloudfront.net/growingproduce/wp-content/uploads/2018/02/gray-mold_on_bellpepper.jpg',
                'https://res.cloudinary.com/da1cs3mxr/image/upload/v1758015790/wix_images/cwhgdkl9x9gpce6kfznz.jpg'
            ]
        }
    ]
    
    # Create Diseases
    created_diseases = 0
    for d_data in diseases_data:
        existing = PepperDisease.query.filter_by(name=d_data['name']).first()
        if not existing:
            disease = PepperDisease(
                name=d_data['name'],
                scientific_name=d_data['scientific_name'],
                description=d_data['description'],
                symptoms=json.dumps(d_data['symptoms']),
                causes=json.dumps(d_data['causes']),
                prevention=json.dumps(d_data['prevention']),
                treatment=json.dumps(d_data['treatment']),
                severity=d_data['severity'],
                visual_indicators=json.dumps(d_data['visual_indicators']),
                affected_parts=d_data['affected_parts'],
                color=d_data['color'],
                icon=d_data['icon'],
                images=json.dumps(d_data['images'])
            )
            db.session.add(disease)
            created_diseases += 1
            print(f"  ✅ Created disease: {d_data['name']}")
    
    db.session.commit()
    
    print(f"\n✅ Pepper database seeded successfully!")
    print(f"   - 1 pepper type created")
    print(f"   - {created_varieties} varieties created")
    print(f"   - {created_diseases} diseases created")

