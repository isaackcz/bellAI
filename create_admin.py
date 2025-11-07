#!/usr/bin/env python3
from app import app, db
from models import User

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print('✅ Admin user exists')
        print('Email: admin@pepperai.com')
        print('Password: admin123')
    else:
        admin = User(username='admin', email='admin@pepperai.com', full_name='Admin User', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('✅ Admin user created')
        print('Email: admin@pepperai.com')
        print('Password: admin123')
