"""Quick project structure setup"""
import os

# Create all directories
dirs = [
    'config', 'app', 'app/models', 'app/routes', 'app/services', 
    'app/utils', 'app/templates', 'app/templates/auth', 
    'app/templates/tenant', 'app/templates/journal', 'app/templates/blog',
    'app/templates/subscription', 'app/templates/ai', 'app/templates/video',
    'app/templates/dashboard', 'app/templates/errors', 'app/static',
    'app/static/css', 'app/static/js', 'app/static/images',
    'tests', 'uploads', 'uploads/manuscripts', 'uploads/images'
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"✅ {d}/")

# Create __init__.py files
inits = [
    'config/__init__.py', 'app/__init__.py', 'app/models/__init__.py',
    'app/routes/__init__.py', 'app/services/__init__.py', 
    'app/utils/__init__.py', 'tests/__init__.py'
]

for f in inits:
    with open(f, 'w') as file:
        file.write('"""\nPackage initialization\n"""\n')
    print(f"✅ {f}")

print("\n✅ Project structure created!")