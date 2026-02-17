"""
Fix admin role - assigns admin to ALL users or specific email
"""
from app import create_app
from app.extensions import db
from app.models import User, Role

app = create_app('development')

with app.app_context():
    print("="*60)
    print("ROLE FIX SCRIPT")
    print("="*60)
    
    # Show ALL users in database
    all_users = User.query.all()
    print(f"\nAll users in database ({len(all_users)} found):")
    for u in all_users:
        print(f"  ID: {u.id} | Email: {u.email} | Roles: {[r.name for r in u.roles]}")
    
    # Show ALL roles
    all_roles = Role.query.all()
    print(f"\nAll roles ({len(all_roles)} found):")
    for r in all_roles:
        print(f"  ID: {r.id} | Name: {r.name}")
    
    # Assign admin role to khushi@gmail.com
    user = User.query.filter_by(email='khushi@gmail.com').first()
    
    if user:
        print(f"\n✅ Found user: {user.email}")
        print(f"   Current roles: {[r.name for r in user.roles]}")
        
        # Get admin role
        admin_role = Role.query.filter_by(name='admin').first()
        
        if admin_role:
            if admin_role not in user.roles:
                user.roles.append(admin_role)
                db.session.commit()
                print(f"✅ Admin role assigned to {user.email}!")
            else:
                print(f"✅ Already has admin role!")
            
            print(f"   New roles: {[r.name for r in user.roles]}")
        else:
            print("❌ Admin role not found! Creating it...")
            admin_role = Role(name='admin', description='Administrator')
            db.session.add(admin_role)
            db.session.commit()
            user.roles.append(admin_role)
            db.session.commit()
            print("✅ Admin role created and assigned!")
    else:
        print("\n❌ User khushi@gmail.com not found!")
        print("\nAssigning admin role to ALL users...")
        admin_role = Role.query.filter_by(name='admin').first()
        for u in all_users:
            if admin_role and admin_role not in u.roles:
                u.roles.append(admin_role)
                print(f"  ✅ Assigned admin to: {u.email}")
        db.session.commit()
    
    print("\n" + "="*60)
    print("✅ DONE!")
    print("="*60)
    print("\nRefresh your browser - you should now see admin role!")