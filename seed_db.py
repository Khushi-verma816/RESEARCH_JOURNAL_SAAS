"""
Seed database with initial data
"""
from app import create_app
from app.extensions import db
from app.models.user import User

app = create_app()

with app.app_context():
    print("Creating database tables...")
    db.create_all()
    
    print("Checking for existing users...")
    if not User.query.filter_by(email='admin@example.com').first():
        admin = User(
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Created admin user: admin@example.com / admin123")
    else:
        print("ℹ️ Admin user already exists")
    
    print("✅ Database seeded successfully!")
