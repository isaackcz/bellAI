# Pepper Database Setup Guide

## Overview
The Pepper Database uses a hierarchical structure with **Types** and **Varieties**. Bell peppers are organized by ripeness/maturity stages, making it easy to understand the relationships between different colored peppers.

## Database Structure

### Pepper Types (Categories)
- **Fully Ripened Bell Peppers** - Red, Orange varieties
- **Partially Ripened Bell Peppers** - Yellow varieties  
- **Unripened Bell Peppers** - Green varieties
- **Specialty Bell Peppers** - Purple, White varieties

### Pepper Varieties
Each variety belongs to a type and includes detailed information about characteristics, quality standards, uses, storage, and nutrition.

## Initial Setup

### 1. Initialize the Database Tables
The `PepperType` and `PepperVariety` models will be automatically created when you run the Flask app for the first time, as they're included in the models.

### 2. Populate Pepper Types and Varieties
Run the initialization script to populate the database:

```bash
# Activate your virtual environment first
env\Scripts\activate  # On Windows
# or
source env/bin/activate  # On Linux/Mac

# Run the initialization script
python init_pepper_types_varieties.py
```

The script will:
- Create 4 pepper types (Fully Ripened, Partially Ripened, Unripened, Specialty)
- Add 6 bell pepper varieties under appropriate types
- Include detailed information for each variety:
  - Color codes
  - Descriptions
  - Key characteristics
  - Quality standards
  - Culinary uses
  - Storage recommendations
  - Nutritional information

### 3. Verify Setup
After running the script, you should see:
```
🌶️  Initializing Pepper Types and Varieties Database...
============================================================

📁 Added Type: Fully Ripened Bell Peppers
   ✅ Added Variety: Red Bell Pepper
   ✅ Added Variety: Orange Bell Pepper

📁 Added Type: Partially Ripened Bell Peppers
   ✅ Added Variety: Yellow Bell Pepper

📁 Added Type: Unripened Bell Peppers
   ✅ Added Variety: Green Bell Pepper

📁 Added Type: Specialty Bell Peppers
   ✅ Added Variety: Purple Bell Pepper
   ✅ Added Variety: White Bell Pepper

============================================================
🎉 Successfully initialized 4 pepper types with 6 varieties!
📊 Total types in database: 4
📊 Total varieties in database: 6
```

## Features

### Database-Driven Content
- All pepper variety information is stored in the database
- Easy to update or add new varieties
- No hardcoded data in the application

### Dynamic User Statistics
- Shows how many peppers of each variety you've analyzed
- Displays average quality scores per variety
- Integrated with your personal analysis history

### Interactive Detail Views
- Click any pepper card to see full details
- Details are fetched from the database via API
- Includes your personal analysis statistics for that variety

## Adding New Types or Varieties

### Add a New Type with Varieties

1. Open `init_pepper_types_varieties.py`
2. Add a new entry to the `PEPPER_DATA` dictionary with type info and varieties
3. Run the script again and select "yes" to reinitialize

### Add a Variety Programmatically

```python
from app import app
from models import db, PepperType, PepperVariety
import json

with app.app_context():
    # Get the type you want to add to
    specialty_type = PepperType.query.filter_by(name='Specialty Bell Peppers').first()
    
    # Create new variety
    variety = PepperVariety(
        type_id=specialty_type.id,
        name='Brown Bell Pepper',
        color='#8B4513',
        description='Rare variety with unique brown coloration',
        characteristics=json.dumps(['Unique color', 'Earthy flavor']),
        quality_standards=json.dumps({'color': 'Deep brown', 'firmness': 'Firm'}),
        uses=json.dumps(['Roasting', 'Grilling']),
        storage='Refrigerate for 1-2 weeks',
        nutritional_highlights='Rich in antioxidants'
    )
    db.session.add(variety)
    db.session.commit()
```

## Database Schema

### `PepperType` Model
- `id` (Primary Key)
- `name` (Unique)
- `description` (Text)
- `icon` (FontAwesome icon class)
- `color` (Hex color code)
- `order_index` (Display order)
- `created_at` (DateTime)
- `varieties` (Relationship to PepperVariety)

### `PepperVariety` Model
- `id` (Primary Key)
- `type_id` (Foreign Key to PepperType)
- `name` (Unique)
- `color` (Hex color code)
- `description` (Text)
- `characteristics` (JSON list)
- `quality_standards` (JSON dict)
- `uses` (JSON list)
- `storage` (String)
- `nutritional_highlights` (Text)
- `created_at` (DateTime)

## API Endpoints

- `GET /pepper-database` - View all varieties with user statistics
- `GET /pepper-database/variety/<variety_name>` - Get detailed information about a specific variety (JSON API)

All data is fetched dynamically from the database!

