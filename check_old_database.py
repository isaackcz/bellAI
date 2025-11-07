#!/usr/bin/env python3
"""Check what data was in the old database"""
import sqlite3
import json

try:
    conn = sqlite3.connect('instance/pepperai.db')
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"Tables: {tables}")
    
    # Check pepper varieties
    if 'pepper_variety' in tables:
        cursor.execute("SELECT COUNT(*) FROM pepper_variety")
        count = cursor.fetchone()[0]
        print(f"\nPepper Varieties: {count}")
        if count > 0:
            cursor.execute("SELECT name, color FROM pepper_variety LIMIT 10")
            for row in cursor.fetchall():
                print(f"  - {row[0]} ({row[1]})")
    
    # Check pepper types
    if 'pepper_type' in tables:
        cursor.execute("SELECT COUNT(*) FROM pepper_type")
        count = cursor.fetchone()[0]
        print(f"\nPepper Types: {count}")
    
    # Check diseases
    if 'pepper_disease' in tables:
        cursor.execute("SELECT COUNT(*) FROM pepper_disease")
        count = cursor.fetchone()[0]
        print(f"\nDiseases: {count}")
        if count > 0:
            cursor.execute("SELECT name, color FROM pepper_disease LIMIT 10")
            for row in cursor.fetchall():
                print(f"  - {row[0]} ({row[1]})")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")

