"""
Verify and fix user tenant
"""
from app import create_app
from app.extensions import db
from app.models import User, Tenant

app = create_app()

with app.app_context():
    print("Checking user tenant...\n")
    
    # Get admin user
    user = User.query.filter_by(email='admin@example.com').first()
    
    if not user:
        print("❌ No user found with email admin@example.com")
        print("\nAll users in database:")
        all_users = User.query.all()
        for u in all_users:
            print(f"  - {u.email} (tenant_id: {u.tenant_id})")
    else:
        print(f"✅ Found user: {user.email}")
        print(f"   Current tenant_id: {user.tenant_id}")
        
        if user.tenant_id is None:
            print("\n⚠️  User has no tenant assigned!")
            
            # Get or create tenant
            tenant = Tenant.query.filter_by(subdomain='demo').first()
            
            if not tenant:
                print("\nCreating Demo tenant...")
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
            
            # Assign tenant
            user.tenant_id = tenant.id
            db.session.commit()
            
            print(f"\n✅ Assigned tenant to user")
            print(f"   Tenant: {tenant.name}")
            print(f"   Tenant ID: {user.tenant_id}")
        else:
            tenant = Tenant.query.get(user.tenant_id)
            print(f"   Tenant: {tenant.name if tenant else 'Unknown'}")
            print("\n✅ User already has a tenant!")
    
    print("\n" + "="*60)
    print("✅ VERIFICATION COMPLETE!")
    print("="*60)
    print("\nNext step: LOGOUT and LOGIN again to refresh your session!")