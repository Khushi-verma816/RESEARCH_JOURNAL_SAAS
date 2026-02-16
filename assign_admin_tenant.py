"""
Assign admin@example.com to tenant
"""
from app import create_app
from app.extensions import db
from app.models import User, Tenant

app = create_app()

with app.app_context():
    print("Assigning admin user to tenant...\n")
    
    # Get admin user
    user = User.query.filter_by(email='admin@example.com').first()
    
    if not user:
        print("❌ Admin user not found!")
    else:
        print(f"✅ Found user: {user.email}")
        
        # Get Demo tenant
        tenant = Tenant.query.filter_by(subdomain='demo').first()
        
        if not tenant:
            print("❌ Demo tenant not found!")
        else:
            # Assign tenant to user
            user.tenant_id = tenant.id
            db.session.commit()
            
            print(f"✅ Assigned {user.email} to tenant: {tenant.name}")
            print(f"   User tenant_id: {user.tenant_id}")
            print(f"   Roles: {[role.name for role in user.roles]}")
    
    print("\n" + "="*60)
    print("✅ TENANT ASSIGNMENT COMPLETE!")
    print("="*60)
    print("\nLogin credentials:")
    print("  Email: admin@example.com")
    print("  Password: admin123")
    print("  Role: Admin")