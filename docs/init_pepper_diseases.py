"""
Initialize Pepper Diseases Database
Run this script to populate the pepper diseases database
"""
from app import app
from models import db, PepperDisease
import json

# Common Bell Pepper Diseases
DISEASES_DATA = {
    'Bacterial Leaf Spot': {
        'scientific_name': 'Xanthomonas campestris pv. vesicatoria',
        'description': 'A common bacterial disease causing dark spots on leaves and fruits, leading to defoliation and reduced yield.',
        'images': [
            'https://csassets.static.wvu.edu/o2gpsy/50d2bf3d-125f-4b45-9c03-487959bd8344/0862b40bec913b574f1f05f79f2805c7/figure-2-tattered%20appearance%20on%20the%20affected%20leaves-893x595.jpg',
            'https://plant-pest-advisory.rutgers.edu/wp-content/uploads/2020/08/BLS-pepper-2020-scaled.jpg'
        ],
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
        'visual_indicators': ['Dark spots on leaves', 'Yellow halos', 'Fruit lesions', 'Leaf drop'],
        'affected_parts': 'Leaves, Stems, Fruits',
        'color': '#DC2626',
        'icon': 'fas fa-virus'
    },
    'Phytophthora Blight': {
        'scientific_name': 'Phytophthora capsici',
        'description': 'A devastating oomycete disease affecting all parts of the pepper plant, causing rapid wilting and death.',
        'images': [
            'https://www.koppert.com/content/_processed_/2/f/csm_stem_and_fruit_rot_of_capsicum_phytophthora_capsici_damage_4_koppert_71e51c5003.jpg',
            'https://msu-prod.dotcmscloud.com/uploads/images/7-29-11%20MARY%20pepper-Phytophthora--4.jpg',
            'https://eorganic.info/sites/eorganic.info/files/u424/pepper%20phytophthora%202.jpg'
        ],
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
        'visual_indicators': ['Stem lesions', 'Plant wilting', 'White mold', 'Root rot'],
        'affected_parts': 'Roots, Stems, Leaves, Fruits',
        'color': '#EF4444',
        'icon': 'fas fa-exclamation-triangle'
    },
    'Anthracnose': {
        'scientific_name': 'Colletotrichum spp.',
        'description': 'A fungal disease primarily affecting ripe fruits, causing sunken circular lesions and significant post-harvest losses.',
        'images': [
            'https://media.springernature.com/lw685/springer-static/image/art%3A10.1007%2Fs12600-014-0428-z/MediaObjects/12600_2014_428_Fig1_HTML.gif',
            'https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEifcm_3jxWigeoY1oGG7_E56YxYouVtayJpS9myFoGYiyu0iya9132kRdBBb4CNz1SqWv4KEkcoCdvnHPfKTNPxY_jBxZ-zJ8_ZKp01ViFxDDvcct8PwUQUlFYJ5wdeH953TaGv31bqd84I4Kil_5rO3ZoS6D9JmvUwwuOXoc9aRFaEACUcKAisnPcFVTAO/s799/early%20blight%20in%20pepper.jpg',
            'https://plant-pest-advisory.rutgers.edu/wp-content/uploads/2014/01/Pepper-Anthracnose.jpg'
        ],
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
        'visual_indicators': ['Circular fruit spots', 'Sunken lesions', 'Pink spore masses'],
        'affected_parts': 'Fruits',
        'color': '#F59E0B',
        'icon': 'fas fa-circle-notch'
    },
    'Powdery Mildew': {
        'scientific_name': 'Leveillula taurica',
        'description': 'A fungal disease characterized by white powdery growth on leaves, reducing photosynthesis and plant vigor.',
        'images': [
            'https://www.researchgate.net/profile/Jose-Eladio-Monge-Perez/publication/352425945/figure/fig6/AS:1035168928235523@1623814913728/Figura-6-Mildiu-polvoso-Leveillula-taurica.jpg',
            'https://bsppjournals.onlinelibrary.wiley.com/cms/asset/7d00056c-550a-431a-875c-074e9524d58d/mpp70128-toc-0001-m.jpg',
            'https://bugwoodcloud.org/images/768x512/5627112.jpg'
        ],
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
        'visual_indicators': ['White powdery coating', 'Yellow leaf patches', 'Leaf curling'],
        'affected_parts': 'Leaves',
        'color': '#A855F7',
        'icon': 'fas fa-snowflake'
    },
    'Blossom End Rot': {
        'scientific_name': 'Calcium deficiency disorder',
        'description': 'A physiological disorder caused by calcium deficiency, resulting in dark, sunken areas on the blossom end of fruits.',
        'images': [
            'https://www.yara.co.uk/contentassets/4901610900644364a5eaaf2b4658decf/8359/',
            'https://bugwoodcloud.org/images/768x512/5368827.jpg'
        ],
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
        'visual_indicators': ['Dark spots on fruit bottom', 'Sunken areas', 'Leathery texture'],
        'affected_parts': 'Fruits',
        'color': '#78350F',
        'icon': 'fas fa-dot-circle'
    },
    'Pepper Mosaic Virus': {
        'scientific_name': 'Pepper Mild Mottle Virus / Tobacco Mosaic Virus',
        'description': 'Viral diseases causing mottled, distorted leaves and reduced fruit quality, transmitted mechanically and by aphids.',
        'images': [
            'https://cdn.mos.cms.futurecdn.net/v2/t:480,l:0,cw:1024,ch:576,q:80,w:1024/uxbqnsoovvan7Kw3WwrWVi.jpg',
            'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRADDRk4itAEGsd0jmN8DCE_uB4o7qhlq2DNA&s'
        ],
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
        'visual_indicators': ['Mosaic leaf pattern', 'Leaf distortion', 'Stunted growth'],
        'affected_parts': 'Leaves, Fruits',
        'color': '#10B981',
        'icon': 'fas fa-project-diagram'
    },
    'Gray Mold': {
        'scientific_name': 'Botrytis cinerea',
        'description': 'A fungal disease affecting flowers, fruits, and stems, causing gray fuzzy mold growth and soft rot.',
        'images': [
            'https://d3qz1qhhp9wxfa.cloudfront.net/growingproduce/wp-content/uploads/2018/02/gray-mold_on_bellpepper.jpg',
            'https://res.cloudinary.com/da1cs3mxr/image/upload/v1758015790/wix_images/cwhgdkl9x9gpce6kfznz.jpg'
        ],
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
        'visual_indicators': ['Gray fuzzy mold', 'Brown lesions', 'Soft fruit rot'],
        'affected_parts': 'Flowers, Fruits, Stems',
        'color': '#6B7280',
        'icon': 'fas fa-cloud'
    }
}

def init_diseases():
    """Initialize pepper diseases in the database"""
    with app.app_context():
        print("🦠 Initializing Bell Pepper Diseases Database...")
        print("=" * 60)
        
        # Check if diseases already exist
        existing_count = PepperDisease.query.count()
        if existing_count > 0:
            print(f"⚠️  Database already contains {existing_count} diseases.")
            response = input("Do you want to clear and reinitialize? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Cancelled.")
                return
            
            # Clear existing diseases
            PepperDisease.query.delete()
            db.session.commit()
            print("🗑️  Cleared existing diseases.")
        
        # Add diseases
        for disease_name, disease_data in DISEASES_DATA.items():
            disease = PepperDisease(
                name=disease_name,
                scientific_name=disease_data['scientific_name'],
                description=disease_data['description'],
                symptoms=json.dumps(disease_data['symptoms']),
                causes=json.dumps(disease_data['causes']),
                prevention=json.dumps(disease_data['prevention']),
                treatment=json.dumps(disease_data['treatment']),
                severity=disease_data['severity'],
                visual_indicators=json.dumps(disease_data['visual_indicators']),
                affected_parts=disease_data['affected_parts'],
                color=disease_data['color'],
                icon=disease_data['icon'],
                images=json.dumps(disease_data.get('images', []))
            )
            db.session.add(disease)
            severity_icon = '🔴' if disease_data['severity'] == 'severe' else '🟡' if disease_data['severity'] == 'moderate' else '🟢'
            print(f"{severity_icon} Added: {disease_name} ({disease_data['severity'].upper()})")
        
        db.session.commit()
        print("=" * 60)
        print(f"🎉 Successfully initialized {len(DISEASES_DATA)} pepper diseases!")
        
        # Verify
        total = PepperDisease.query.count()
        print(f"📊 Total diseases in database: {total}")
        
        # Summary by severity
        severe = PepperDisease.query.filter_by(severity='severe').count()
        moderate = PepperDisease.query.filter_by(severity='moderate').count()
        mild = PepperDisease.query.filter_by(severity='mild').count()
        print(f"\n📈 By Severity:")
        print(f"   🔴 Severe: {severe}")
        print(f"   🟡 Moderate: {moderate}")
        print(f"   🟢 Mild: {mild}")

if __name__ == '__main__':
    init_diseases()

