import os
from app import app, db

def setup():
    print("🎓 Setting up KidFit Astana...")
    
    # Create directories
    os.makedirs('static/uploads/children', exist_ok=True)
    os.makedirs('static/uploads/centers', exist_ok=True)
    os.makedirs('static/uploads/programs', exist_ok=True)
    
    with app.app_context():
        # Clean setup
        db.drop_all()
        db.create_all()
        
        # Initialize categories
        from app import init_default_categories
        init_default_categories()
        
        print("✅ Database setup complete!")
        print("🚀 Run: python app.py")

if __name__ == '__main__':
    setup()