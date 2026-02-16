"""
Create admin user with role and tenant
"""
from app import create_app
from app.extensions import db
from app.models import User, Tenant, Role

app = create_app()

with app.app_context():
    print("Setting up admin user...\n")
    
    # 1. Create or get admin user
    user = User.query.filter_by(email='admin@example.com').first()
    
    if not user:
        print("Creating admin user...")
        user = User(
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            is_active=True
        )
        user.set_password('admin123')
        db.session.add(user)
        db.session.flush()
        print(f"✅ Created user: {user.email}")
    else:
        print(f"✅ User exists: {user.email}")
    
    # 2. Get or create Demo tenant
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
    else:
        print(f"✅ Tenant exists: {tenant.name}")
    
    # 3. Assign tenant to user
    user.tenant_id = tenant.id
    print(f"\n✅ Assigned user to tenant")
    
    # 4. Assign admin role
    admin_role = Role.query.filter_by(name='admin').first()
    
    if admin_role:
        if admin_role not in user.roles:
            user.roles.append(admin_role)
            print(f"✅ Assigned 'admin' role")
        else:
            print(f"✅ User already has 'admin' role")
    else:
        print("❌ Admin role not found in database!")
    
    # 5. Commit everything
    db.session.commit()
    
    print("\n" + "="*60)
    print("✅ ADMIN USER SETUP COMPLETE!")
    print("="*60)
    print("\nUser Details:")
    print(f"  Email: {user.email}")
    print(f"  Password: admin123")
    print(f"  Tenant: {tenant.name}")
    print(f"  Tenant ID: {user.tenant_id}")
    print(f"  Roles: {[role.name for role in user.roles]}")
    print("\nYou can now login and create journals!")