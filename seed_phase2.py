"""
Seed database with Phase 2 data (Roles and Subscription Plans)
"""
from app import create_app
from app.extensions import db
from app.models import Role, SubscriptionPlan, Tenant, User

app = create_app()

with app.app_context():
    print("Seeding Phase 2 data...\n")
    
    # ==================== CREATE ROLES ====================
    print("Creating roles...")
    roles_data = [
        {
            'name': 'admin',
            'description': 'System administrator with full access',
            'permissions': {
                'manage_users': True,
                'manage_journals': True,
                'manage_submissions': True,
                'manage_subscriptions': True,
                'view_analytics': True
            }
        },
        {
            'name': 'editor',
            'description': 'Journal editor',
            'permissions': {
                'manage_journals': True,
                'manage_submissions': True,
                'assign_reviewers': True,
                'make_decisions': True
            }
        },
        {
            'name': 'reviewer',
            'description': 'Peer reviewer',
            'permissions': {
                'view_submissions': True,
                'submit_reviews': True
            }
        },
        {
            'name': 'author',
            'description': 'Author/Contributor',
            'permissions': {
                'create_submissions': True,
                'view_own_submissions': True,
                'create_blog_posts': True
            }
        },
        {
            'name': 'user',
            'description': 'Regular user',
            'permissions': {
                'view_journals': True,
                'view_blog_posts': True
            }
        }
    ]
    
    for role_data in roles_data:
        if not Role.query.filter_by(name=role_data['name']).first():
            role = Role(**role_data)
            db.session.add(role)
            print(f"  ✅ Created role: {role_data['name']}")
        else:
            print(f"  ℹ️  Role already exists: {role_data['name']}")
    
    db.session.commit()
    
    # ==================== CREATE SUBSCRIPTION PLANS ====================
    print("\nCreating subscription plans...")
    plans_data = [
        {
            'name': 'Free Trial',
            'slug': 'trial',
            'description': '14-day free trial with basic features',
            'price_monthly': 0.00,
            'price_yearly': 0.00,
            'max_users': 2,
            'max_storage_gb': 1,
            'max_journals': 1,
            'is_active': True
        },
        {
            'name': 'Basic',
            'slug': 'basic',
            'description': 'Perfect for small research teams',
            'price_monthly': 29.99,
            'price_yearly': 299.99,
            'max_users': 5,
            'max_storage_gb': 10,
            'max_journals': 3,
            'is_active': True
        },
        {
            'name': 'Professional',
            'slug': 'professional',
            'description': 'For growing research organizations',
            'price_monthly': 79.99,
            'price_yearly': 799.99,
            'max_users': 20,
            'max_storage_gb': 50,
            'max_journals': 10,
            'is_active': True
        },
        {
            'name': 'Enterprise',
            'slug': 'enterprise',
            'description': 'Unlimited features for large institutions',
            'price_monthly': 199.99,
            'price_yearly': 1999.99,
            'max_users': 999,
            'max_storage_gb': 500,
            'max_journals': 999,
            'is_active': True
        }
    ]
    
    for plan_data in plans_data:
        if not SubscriptionPlan.query.filter_by(slug=plan_data['slug']).first():
            plan = SubscriptionPlan(**plan_data)
            db.session.add(plan)
            print(f"  ✅ Created plan: {plan_data['name']} (${plan_data['price_monthly']}/mo)")
        else:
            print(f"  ℹ️  Plan already exists: {plan_data['name']}")
    
    db.session.commit()
    
    # ==================== CREATE DEFAULT TENANT ====================
    print("\nCreating default tenant...")
    if not Tenant.query.filter_by(subdomain='demo').first():
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
        db.session.commit()
        print(f"  ✅ Created tenant: {tenant.name}")
        
        # ==================== UPDATE ADMIN USER ====================
        print("\nUpdating admin user with roles and tenant...")
        admin_user = User.query.filter_by(email='admin@example.com').first()
        if admin_user:
            # Assign tenant
            admin_user.tenant_id = tenant.id
            
            # Assign admin role
            admin_role = Role.query.filter_by(name='admin').first()
            if admin_role and admin_role not in admin_user.roles:
                admin_user.roles.append(admin_role)
                print(f"  ✅ Assigned 'admin' role to {admin_user.email}")
            
            db.session.commit()
            print(f"  ✅ Updated admin user")
    else:
        print("  ℹ️  Default tenant already exists")
    
    print("\n" + "="*60)
    print("✅ PHASE 2 DATABASE SEEDED SUCCESSFULLY!")
    print("="*60)
    print("\nYou now have:")
    print(f"  • {Role.query.count()} roles")
    print(f"  • {SubscriptionPlan.query.count()} subscription plans")
    print(f"  • {Tenant.query.count()} tenant(s)")
    print(f"  • {User.query.count()} user(s)")
    print("\nLogin credentials:")
    print("  Email: admin@example.com")
    print("  Password: admin123")
    print("  Role: Admin")