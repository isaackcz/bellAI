"""
Create an admin user for PepperAI
Run this script to create an administrator account
"""

from app import app, db, User

def create_admin():
    with app.app_context():
        # Check if admin already exists
        existing_admin = User.query.filter_by(email='admin@pepperai.com').first()
        
        if existing_admin:
            print("❌ Admin user already exists!")
            print(f"   Email: admin@pepperai.com")
            print(f"   Username: {existing_admin.username}")
            return
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@pepperai.com',
            full_name='Administrator',
            role='admin'
        )
        admin.set_password('admin123')  # Default password - CHANGE THIS!
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Admin user created successfully!")
        print("=" * 50)
        print("   Email: admin@pepperai.com")
        print("   Password: admin123")
        print("=" * 50)
        print("⚠️  IMPORTANT: Change the password after first login!")
        print("")

if __name__ == '__main__':
    create_admin()

