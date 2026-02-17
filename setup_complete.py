"""
Complete database setup
"""
import os
from app import create_app
from app.extensions import db
from app.models import User, Role, Tenant
from werkzeug.security import generate_password_hash

def setup():
    app = create_app('development')
    
    with app.app_context():
        instance_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'instance',
            'research_journal.db'
        )
        
        print("="*70)
        print("RESEARCH JOURNAL SAAS - DATABASE SETUP")
        print("="*70)
        print(f"\nDatabase: {instance_path}")
        
        # Delete existing database
        if os.path.exists(instance_path):
            os.remove(instance_path)
            print("✅ Old database deleted")
        
        # Create fresh tables
        print("\n📦 Creating database tables...")
        db.create_all()
        
        if os.path.exists(instance_path):
            print(f"✅ Database created!")
        else:
            print("❌ Database not created!")
            return
        
        # Create roles
        print("\n👥 Creating roles...")
        for name, desc in [
            ('admin', 'Administrator'),
            ('editor', 'Journal editor'),
            ('reviewer', 'Peer reviewer'),
            ('author', 'Manuscript author'),
            ('user', 'Regular user')
        ]:
            role = Role(name=name, description=desc)
            db.session.add(role)
        db.session.commit()
        print("✅ Created 5 roles")
        
        # Create tenant - NO subscription_plan field!
        print("\n🏢 Creating tenant...")
        tenant = Tenant(
            name='Demo Organization',
            subdomain='demo',
            is_active=True
        )
        db.session.add(tenant)
        db.session.commit()
        print("✅ Tenant created")
        
        # Create admin user
        print("\n🔑 Creating admin user...")
        admin_role = Role.query.filter_by(name='admin').first()
        admin = User(
            email='admin@example.com',
            password=generate_password_hash('admin123'),
            first_name='Admin',
            last_name='User',
            tenant_id=tenant.id,
            is_active=True,
            email_verified=True
        )
        admin.roles.append(admin_role)
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created")
        
        print("\n" + "="*70)
        print("✅ DATABASE SETUP COMPLETE!")
        print("="*70)
        print(f"\n📊 Statistics:")
        print(f"  Users:   {User.query.count()}")
        print(f"  Roles:   {Role.query.count()}")
        print(f"  Tenants: {Tenant.query.count()}")
        print(f"\n🔐 Login Credentials:")
        print(f"  Email:    admin@example.com")
        print(f"  Password: admin123")
        print(f"\n🚀 Run: flask run")
        print("="*70)

if __name__ == '__main__':
    setup()