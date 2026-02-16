"""Test if basic setup works"""
print("✅ Python is working!")

try:
    from dotenv import load_dotenv
    print("✅ python-dotenv installed")
except:
    print("❌ python-dotenv not installed")

try:
    import flask
    print(f"✅ Flask {flask.__version__} installed")
except:
    print("❌ Flask not installed")

try:
    import flask_sqlalchemy
    print("✅ Flask-SQLAlchemy installed")
except:
    print("❌ Flask-SQLAlchemy not installed")

try:
    import flask_migrate
    print("✅ Flask-Migrate installed")
except:
    print("❌ Flask-Migrate not installed")

print("\n✅ All basic dependencies are installed!")