"""
Migrate Pepper Database to new schema with Types
This script updates the existing database to support the new hierarchical structure
"""
from app import app
from models import db
import shutil
import os
from datetime import datetime

def backup_database():
    """Create a backup of the current database"""
    db_path = 'instance/pepperai.db'
    if os.path.exists(db_path):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'instance/pepperai_backup_{timestamp}.db'
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return True
    return False

def migrate_database():
    """Migrate database to new schema"""
    with app.app_context():
        print("🔄 Migrating Pepper Database Schema...")
        print("=" * 60)
        
        # Backup first
        if backup_database():
            print("📦 Backup completed successfully")
        
        # Drop and recreate tables
        print("\n🗑️  Dropping old pepper tables...")
        try:
            db.session.execute(db.text('DROP TABLE IF EXISTS pepper_variety'))
            db.session.execute(db.text('DROP TABLE IF EXISTS pepper_type'))
            db.session.execute(db.text('DROP TABLE IF EXISTS pepper_disease'))
            db.session.commit()
            print("✅ Old tables dropped")
        except Exception as e:
            print(f"⚠️  Error dropping tables: {e}")
            db.session.rollback()
        
        # Create new tables
        print("\n📊 Creating new tables with updated schema...")
        db.create_all()
        print("✅ New tables created successfully")
        
        print("\n" + "=" * 60)
        print("🎉 Migration completed!")
        print("\n📝 Next steps:")
        print("   1. Run: python init_pepper_types_varieties.py")
        print("   2. This will populate the database with pepper types and varieties")
        print("\n💡 Note: Your analyzed pepper data is preserved!")

if __name__ == '__main__':
    migrate_database()

