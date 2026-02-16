"""
Assign user to Demo tenant
"""
from app import create_app
from app.extensions import db
from app.models import User, Tenant

app = create_app()

with app.app_context():
    print("Assigning user to tenant...\n")
    
    # Get the user
    user = User.query.filter_by(email='khushi@gmail.com').first()
    
    if not user:
        print("❌ User not found!")
    else:
        # Get or create Demo tenant
        tenant = Tenant.query.filter_by(subdomain='demo').first()
        
        if not tenant:
            print("Creating Demo tenant...")
            tenant = Tenant(
                name='Demo Organization',
                subdomain='demo',
                email='admin@demo.com',
                is_active=True,
                max_users=10,
                max_storage_gb=20,
                max_journals=5
            )
            db.session.add(tenant)
            db.session.flush()
            print(f"✅ Created tenant: {tenant.name}")
        
        # Assign user to tenant
        user.tenant_id = tenant.id
        db.session.commit()
        
        print(f"✅ Assigned {user.email} to tenant: {tenant.name}")
        print(f"   User tenant_id: {user.tenant_id}")
    
    print("\n" + "="*60)
    print("✅ TENANT ASSIGNMENT COMPLETE!")
    print("="*60)