# setup.py - Complete setup script for the enhanced education platform
import os
import sys
from app import app, db, init_default_categories

def setup_platform():
    """Complete setup for the education platform"""
    print("🎓 Setting up KidFit Astana Education Platform...")
    
    # Create necessary directories
    print("📁 Creating directories...")
    directories = [
        'static',
        'static/uploads',
        'static/uploads/children',
        'static/uploads/centers', 
        'static/uploads/programs',
        'static/css',
        'static/js',
        'static/images'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"   ✓ Created {directory}")
    
    # Initialize database
    print("\n🗄️ Setting up database...")
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("   ✓ Database tables created")
            
            # Initialize categories
            init_default_categories()
            print("   ✓ Default categories initialized")
            
            # Create demo data
            from demo_data import create_demo_data
            create_demo_data()
            print("   ✓ Demo data created")
            
        except Exception as e:
            print(f"   ❌ Database setup failed: {e}")
            return False
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Demo Accounts Created:")
    print("   Parent: parent@demo.com / demo123")
    print("   Center 1: center@demo.com / demo123")
    print("   Center 2: stars@demo.com / demo123")
    print("   Center 3: sports@demo.com / demo123")
    print("   Teachers: elena@demo.com, sergey@demo.com, assel@demo.com, ivan@demo.com / demo123")
    
    print("\n🚀 Ready to run! Execute: python app.py")
    return True

if __name__ == '__main__':
    setup_platform()

# requirements.txt content
REQUIREMENTS = """
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Werkzeug==2.3.7
requests==2.31.0
"""

# run.py - Development server runner with error handling
from app import app, create_tables
import sys
import os

def check_requirements():
    """Check if all required packages are installed"""
    required_packages = ['flask', 'flask_sqlalchemy', 'werkzeug', 'requests']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print("❌ Missing required packages:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\n💡 Install with: pip install flask flask-sqlalchemy werkzeug requests")
        return False
    return True

def run_server():
    """Run the development server with proper error handling"""
    print("🎓 KidFit Astana Education Platform")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Ensure database is set up
    try:
        create_tables()
        print("✓ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)
    
    # Check for demo data
    from models import User
    if User.query.count() == 0:
        print("⚠️  No users found. Creating demo data...")
        try:
            from demo_data import create_demo_data
            create_demo_data()
            print("✓ Demo data created")
        except Exception as e:
            print(f"❌ Demo data creation failed: {e}")
            print("💡 You can create demo data later by running: python demo_data.py")
    
    print("\n🌐 Starting development server...")
    print("📍 URL: http://localhost:5000")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        app.run(debug=True, host='localhost', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Server stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Server error: {e}")

if __name__ == '__main__':
    run_server()

# Enhanced README content
README_CONTENT = """
# KidFit Astana - Education Platform

A comprehensive web platform connecting families with education centers in Astana, Kazakhstan.

## 🌟 Features

### For Parents
- **Child Management**: Add children with photos, ages, and details
- **Smart Search**: Find centers on interactive map with filters
- **Easy Enrollment**: One-click enrollment with real-time validation
- **Enrollment Tracking**: Monitor all your children's class enrollments

### For Education Centers  
- **Program Management**: Create and manage educational programs
- **Schedule System**: Flexible class scheduling with conflict detection
- **Enrollment Management**: Approve/manage student enrollments
- **Teacher Coordination**: Invite and manage teaching staff

### For Teachers
- **Schedule View**: See all assigned classes and times
- **Student Management**: View enrolled students and class details
- **Center Integration**: Seamless connection with your education center

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.8+
pip (Python package manager)
```

### Installation & Setup
```bash
# 1. Clone/download the project
cd kidfit-astana

# 2. Install dependencies
pip install flask flask-sqlalchemy werkzeug requests

# 3. Run setup (creates database and demo data)
python setup.py

# 4. Start the server
python run.py
```

### Access the Platform
- **URL**: http://localhost:5000
- **Demo Parent**: parent@demo.com / demo123
- **Demo Center**: center@demo.com / demo123

## 📊 Demo Data Included

- **3 Children**: Emma (8), Alex (12), Maya (7) 
- **3 Centers**: Bright Minds, Future Stars, Active Kids
- **6+ Programs**: Arts, Math, Science, Robotics, Soccer, Athletics
- **4 Teachers**: Specialized instructors for different subjects
- **Active Enrollments**: Children already enrolled in sample programs

## 🎯 Key Functionalities

### Child Management System
- Add/edit children with photos and details
- Age-based program filtering  
- Enrollment history tracking
- Quick enrollment from dashboard

### Interactive Map Features
- Real-time center locations with Leaflet.js
- Address geocoding with OpenStreetMap
- Distance calculation and directions
- Category-based filtering

### Smart Enrollment System
- Age requirement validation
- Class capacity management
- Conflict detection
- Real-time availability updates

### Program & Schedule Management
- Hierarchical category system
- Flexible time scheduling
- Teacher assignment
- Room/location tracking

## 🛠️ Technical Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Frontend**: Bootstrap 5 + vanilla JavaScript
- **Maps**: Leaflet.js with OpenStreetMap tiles
- **Architecture**: Clean MVC pattern with role-based access

## 📁 Project Structure

```
kidfit-astana/
├── app.py                 # Main Flask application
├── models.py              # Database models  
├── services.py            # Business logic services
├── demo_data.py           # Demo data creation
├── setup.py               # Setup script
├── run.py                 # Development server runner
├── templates/             # HTML templates
│   ├── base.html         # Base template with navigation
│   ├── auth/             # Authentication pages
│   ├── dashboards/       # Role-based dashboards  
│   ├── parent/           # Parent-specific pages
│   ├── center/           # Center management pages
│   └── teacher/          # Teacher interface pages
├── static/               # Static files
│   ├── uploads/          # User uploaded files
│   ├── css/              # Custom styles
│   └── js/               # JavaScript files
└── education_platform.db # SQLite database
```

## 🎮 Demo Walkthrough

### Parent Journey
1. **Login**: parent@demo.com / demo123
2. **View Children**: See Emma, Alex, and Maya with their details  
3. **Browse Centers**: Use interactive map to explore centers
4. **Enroll Child**: Quick enroll any child in available programs
5. **Track Enrollments**: Monitor enrollment status and manage

### Center Management
1. **Login**: center@demo.com / demo123
2. **View Dashboard**: See enrollment statistics and program overview
3. **Manage Programs**: Edit existing programs or create new ones
4. **Schedule Classes**: Set up class times and assign teachers
5. **Handle Enrollments**: Approve pending enrollment requests

## 📚 Usage Examples

### Adding a New Child
```python
# Navigate to: /parent/children/add
# Upload photo, enter details, save
# Child immediately available for enrollment
```

### Creating a Program  
```python
# Navigate to: /center/programs/add
# Select category, set pricing, age requirements
# Program appears in search results
```

### Enrolling in a Class
```python
# Click "Enroll" on any child card
# View available programs filtered by age
# One-click enrollment with validation
```

## 🔧 Customization

### Adding New Categories
```python
# In app.py init_default_categories()
new_category = Category(
    name='Music',
    icon='bi-music-note', 
    color='#ff6b6b'
)
```

### Extending User Roles
```python
# In models.py User class
# Add new role types and implement logic
# Update templates and navigation
```

### Map Configuration
```python
# In services.py GeocodingService
# Modify geocoding bounds for different cities
# Add new landmark coordinates
```

## 🎯 Perfect For

- **Educational Technology Projects**: Modern web development showcase
- **Local Business Solutions**: Platform for education centers
- **Learning Web Development**: Clean MVC architecture example
- **Portfolio Projects**: Full-stack application demonstration

## 🚨 Troubleshooting

### Common Issues

**Port Already in Use**
```bash
python run.py --port 5001
```

**Database Errors**
```bash
rm education_platform.db
python setup.py
```

**Missing Modules**
```bash
pip install flask flask-sqlalchemy werkzeug requests
```

### Reset Demo Data
```bash
python setup.py  # Recreates all demo data
```

## 📈 Next Steps

- **Payment Integration**: Stripe/PayPal for program fees
- **Mobile App**: React Native companion app
- **Advanced Analytics**: Center performance metrics  
- **Communication**: In-app messaging system
- **Multi-language**: Kazakh, Russian, English support

---

**Built with ❤️ for the Astana education community**

*This platform demonstrates modern web development practices while solving real-world problems in education management.*
"""

def create_project_files():
    """Create additional project files"""
    
    # Create requirements.txt
    with open('requirements.txt', 'w') as f:
        f.write(REQUIREMENTS.strip())
    
    # Create README.md
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(README_CONTENT.strip())
    
    # Create .gitignore
    gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# Flask
instance/
.webassets-cache

# Database
*.db
*.sqlite

# Uploads
static/uploads/*
!static/uploads/.gitkeep

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
    """
    
    with open('.gitignore', 'w') as f:
        f.write(gitignore_content.strip())
    
    # Create upload directory placeholders
    for directory in ['children', 'centers', 'programs']:
        os.makedirs(f'static/uploads/{directory}', exist_ok=True)
        with open(f'static/uploads/{directory}/.gitkeep', 'w') as f:
            f.write('')
    
    print("📄 Project files created:")
    print("   ✓ requirements.txt")
    print("   ✓ README.md") 
    print("   ✓ .gitignore")
    print("   ✓ Upload directories")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'files':
        create_project_files()
    else:
        print("Usage:")
        print("  python setup.py        # Setup database and demo data")
        print("  python setup.py files  # Create project files")