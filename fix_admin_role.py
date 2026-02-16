"""
Fix: Assign admin role to admin user
"""
from app import create_app
from app.extensions import db
from app.models import User, Role

app = create_app()

with app.app_context():
    print("Fixing admin role assignment...\n")
    
    # Get admin user
    admin_user = User.query.filter_by(email='khushi@gmail.com').first()
    
    if not admin_user:
        print("❌ User not found!")
    else:
        # Get admin role
        admin_role = Role.query.filter_by(name='admin').first()
        
        if not admin_role:
            print("❌ Admin role not found!")
        else:
            # Assign role if not already assigned
            if admin_role not in admin_user.roles:
                admin_user.roles.append(admin_role)
                db.session.commit()
                print(f"✅ Assigned 'admin' role to {admin_user.email}")
            else:
                print(f"ℹ️  {admin_user.email} already has admin role")
    
    print("\n" + "="*60)
    print("✅ ROLE FIX COMPLETE!")
    print("="*60)
    print("\nPlease refresh your browser to see the admin role!")