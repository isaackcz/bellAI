#!/usr/bin/env python3
"""Extract disease data from old database"""
import sqlite3
import json

try:
    conn = sqlite3.connect('instance/pepperai.db')
    cursor = conn.cursor()
    
    # Extract all disease data
    cursor.execute("SELECT * FROM pepper_disease")
    columns = [description[0] for description in cursor.description]
    
    diseases = []
    for row in cursor.fetchall():
        disease_dict = dict(zip(columns, row))
        diseases.append(disease_dict)
    
    print(f"Found {len(diseases)} diseases:")
    for d in diseases:
        print(f"\n{d['name']} ({d['color']})")
        print(f"  Scientific: {d.get('scientific_name', 'N/A')}")
        print(f"  Severity: {d.get('severity', 'N/A')}")
    
    # Save to JSON for easy copy-paste
    with open('diseases_data.json', 'w') as f:
        json.dump(diseases, f, indent=2, default=str)
    
    print(f"\n✅ Disease data saved to diseases_data.json")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

