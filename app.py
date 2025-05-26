from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
import uuid
from datetime import datetime, date
# from demo_data import create_demo_data

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///education_platform.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize database
from database import db
db.init_app(app)

# Import models and services
from models import User, Parent, Center, Teacher, Child, Category, Program, Schedule, Enrollment, Attendance
from services import GeocodingService

# Role-based authentication decorator
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login'))
            
            if role and session.get('user_role') != role:
                flash('Access denied. Insufficient permissions.', 'danger')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# File upload helper
def save_uploaded_file(file, folder='general'):
    if file and file.filename:
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
        
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
        os.makedirs(upload_path, exist_ok=True)
        
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        return f"{folder}/{filename}"
    return None

# Routes
@app.route('/')
def index():
    """Landing page - redirect based on login status"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['user_role'] = user.role
            session['user_name'] = user.name
            
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html')

@app.route('/register')
def register_choice():
    """Registration type selection page"""
    return render_template('auth/register_choice.html')

@app.route('/register/parent', methods=['GET', 'POST'])
def register_parent():
    """Parent registration"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        if not all([name, email, password]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('auth/register_parent.html')
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please use a different email.', 'danger')
            return render_template('auth/register_parent.html')
        
        try:
            user = User(
                email=email,
                password_hash=generate_password_hash(password),
                name=name,
                phone=phone,
                role='parent'
            )
            db.session.add(user)
            db.session.flush()
            
            parent = Parent(
                user_id=user.id,
                address=address
            )
            db.session.add(parent)
            db.session.commit()
            
            flash(f'Welcome {name}! Your parent account has been created successfully.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            return render_template('auth/register_parent.html')
    
    return render_template('auth/register_parent.html')

@app.route('/register/center', methods=['GET', 'POST'])
def register_center():
    """Education center registration"""
    if request.method == 'POST':
        center_name = request.form.get('center_name')
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        address = request.form.get('address')
        description = request.form.get('description')
        
        if not all([center_name, name, email, password, address]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('auth/register_center.html')
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please use a different email.', 'danger')
            return render_template('auth/register_center.html')
        
        try:
            # Geocode the address
            geocoding_service = GeocodingService()
            coordinates = geocoding_service.geocode_address(address, "Astana", "Kazakhstan")
            
            if not coordinates:
                flash('Could not locate the address. Please provide a more specific address in Astana.', 'warning')
                # Still allow registration but without coordinates
                latitude, longitude = None, None
            else:
                latitude, longitude = coordinates
                flash(f'Address located successfully at coordinates: {latitude:.4f}, {longitude:.4f}', 'info')
            
            user = User(
                email=email,
                password_hash=generate_password_hash(password),
                name=name,
                phone=phone,
                role='center'
            )
            db.session.add(user)
            db.session.flush()
            
            center = Center(
                user_id=user.id,
                center_name=center_name,
                description=description,
                address=address,
                latitude=latitude,
                longitude=longitude
            )
            db.session.add(center)
            db.session.commit()
            
            flash(f'Welcome {center_name}! Your center has been registered successfully. Your teacher invite code is: {center.invite_code}', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            return render_template('auth/register_center.html')
    
    return render_template('auth/register_center.html')

@app.route('/register/teacher', methods=['GET', 'POST'])
def register_teacher():
    """Teacher registration with invite code"""
    if request.method == 'POST':
        invite_code = request.form.get('invite_code')
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        specialization = request.form.get('specialization')
        bio = request.form.get('bio')
        
        if not all([invite_code, name, email, password]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('auth/register_teacher.html')
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please use a different email.', 'danger')
            return render_template('auth/register_teacher.html')
        
        center = Center.query.filter_by(invite_code=invite_code.upper()).first()
        if not center:
            flash('Invalid invite code. Please check with your education center.', 'danger')
            return render_template('auth/register_teacher.html')
        
        try:
            user = User(
                email=email,
                password_hash=generate_password_hash(password),
                name=name,
                phone=phone,
                role='teacher'
            )
            db.session.add(user)
            db.session.flush()
            
            teacher = Teacher(
                user_id=user.id,
                center_id=center.id,
                specialization=specialization,
                bio=bio
            )
            db.session.add(teacher)
            db.session.commit()
            
            flash(f'Welcome {name}! You have successfully joined {center.center_name} as a teacher.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            return render_template('auth/register_teacher.html')
    
    return render_template('auth/register_teacher.html')

@app.route('/dashboard')
@login_required()
def dashboard():
    """Role-based dashboard routing"""
    role = session.get('user_role')
    
    if role == 'parent':
        return redirect(url_for('parent_dashboard'))
    elif role == 'center':
        return redirect(url_for('center_dashboard'))
    elif role == 'teacher':
        return redirect(url_for('teacher_dashboard'))
    else:
        flash('Invalid user role', 'danger')
        return redirect(url_for('logout'))

@app.route('/parent/dashboard')
@login_required(role='parent')
def parent_dashboard():
    """Parent dashboard - search interface with centers and map"""
    parent = Parent.query.filter_by(user_id=session['user_id']).first()
    centers = Center.query.all()
    children = Child.query.filter_by(parent_id=parent.id).all() if parent else []
    
    # Get categories for filtering
    categories = Category.query.filter_by(parent_id=None).all()  # Main categories only
    
    # Get centers with coordinates for map
    map_centers = [center for center in centers if center.latitude and center.longitude]
    
    return render_template('dashboards/parent_dashboard.html', 
                         parent=parent, 
                         centers=centers, 
                         children=children,
                         categories=categories,
                         map_centers=map_centers)

# NEW CHILD MANAGEMENT ROUTES
@app.route('/parent/children')
@login_required(role='parent')
def manage_children():
    """Manage children page"""
    parent = Parent.query.filter_by(user_id=session['user_id']).first()
    children = Child.query.filter_by(parent_id=parent.id).all() if parent else []
    
    return render_template('parent/children.html', children=children)

@app.route('/parent/children/add', methods=['GET', 'POST'])
@login_required(role='parent')
def add_child():
    """Add new child"""
    parent = Parent.query.filter_by(user_id=session['user_id']).first()
    
    if request.method == 'POST':
        name = request.form.get('name')
        birth_date_str = request.form.get('birth_date')
        grade = request.form.get('grade')
        notes = request.form.get('notes')
        
        if not name:
            flash('Child name is required.', 'danger')
            return render_template('parent/add_child.html')
        
        # Handle birth date
        birth_date = None
        if birth_date_str:
            try:
                birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid birth date format.', 'danger')
                return render_template('parent/add_child.html')
        
        # Handle photo upload
        photo_url = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename:
                photo_url = save_uploaded_file(file, 'children')
        
        try:
            child = Child(
                parent_id=parent.id,
                name=name,
                birth_date=birth_date,
                grade=grade,
                notes=notes,
                photo_url=photo_url
            )
            
            db.session.add(child)
            db.session.commit()
            
            flash(f'{child.name} has been added successfully!', 'success')
            return redirect(url_for('manage_children'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error adding child. Please try again.', 'danger')
    
    return render_template('parent/add_child.html')

@app.route('/parent/children/<int:child_id>/edit', methods=['GET', 'POST'])
@login_required(role='parent')
def edit_child(child_id):
    """Edit child information"""
    parent = Parent.query.filter_by(user_id=session['user_id']).first()
    child = Child.query.filter_by(id=child_id, parent_id=parent.id).first()
    
    if not child:
        flash('Child not found.', 'danger')
        return redirect(url_for('manage_children'))
    
    if request.method == 'POST':
        child.name = request.form.get('name')
        child.grade = request.form.get('grade')
        child.notes = request.form.get('notes')
        
        # Handle birth date
        birth_date_str = request.form.get('birth_date')
        if birth_date_str:
            try:
                child.birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid birth date format.', 'danger')
                return render_template('parent/edit_child.html', child=child)
        
        # Handle photo upload
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename:
                child.photo_url = save_uploaded_file(file, 'children')
        
        try:
            db.session.commit()
            flash(f'{child.name} updated successfully!', 'success')
            return redirect(url_for('manage_children'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating child. Please try again.', 'danger')
    
    return render_template('parent/edit_child.html', child=child)

@app.route('/parent/children/<int:child_id>/delete', methods=['POST'])
@login_required(role='parent')
def delete_child(child_id):
    """Delete child"""
    parent = Parent.query.filter_by(user_id=session['user_id']).first()
    child = Child.query.filter_by(id=child_id, parent_id=parent.id).first()
    
    if not child:
        flash('Child not found.', 'danger')
        return redirect(url_for('manage_children'))
    
    try:
        # Check for active enrollments
        active_enrollments = Enrollment.query.filter_by(child_id=child.id, status='active').count()
        if active_enrollments > 0:
            flash(f'Cannot delete {child.name}. Please cancel all active enrollments first.', 'danger')
            return redirect(url_for('manage_children'))
        
        child_name = child.name
        db.session.delete(child)
        db.session.commit()
        flash(f'{child_name} has been removed.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting child. Please try again.', 'danger')
    
    return redirect(url_for('manage_children'))

# ENHANCED ENROLLMENT SYSTEM
@app.route('/enroll/<int:schedule_id>/<int:child_id>', methods=['POST'])
@login_required(role='parent')
def enroll_child(schedule_id, child_id):
    """Enroll child in a program"""
    parent = Parent.query.filter_by(user_id=session['user_id']).first()
    child = Child.query.filter_by(id=child_id, parent_id=parent.id).first()
    schedule = Schedule.query.get_or_404(schedule_id)
    
    if not child:
        return jsonify({'error': 'Child not found'}), 404
    
    # Check if already enrolled
    existing = Enrollment.query.filter_by(
        child_id=child_id, 
        schedule_id=schedule_id,
        status='active'
    ).first()
    
    if existing:
        return jsonify({'error': 'Child is already enrolled in this class'}), 400
    
    # Check age requirements
    if child.birth_date:
        child_age = date.today().year - child.birth_date.year
        if schedule.program.min_age and child_age < schedule.program.min_age:
            return jsonify({'error': f'Child is too young for this program (minimum age: {schedule.program.min_age})'}), 400
        if schedule.program.max_age and child_age > schedule.program.max_age:
            return jsonify({'error': f'Child is too old for this program (maximum age: {schedule.program.max_age})'}), 400
    
    # Check capacity
    current_enrollments = Enrollment.query.filter_by(
        schedule_id=schedule_id,
        status='active'
    ).count()
    
    if current_enrollments >= schedule.max_students:
        return jsonify({'error': 'Class is full'}), 400
    
    # Create enrollment
    try:
        enrollment = Enrollment(
            child_id=child_id,
            schedule_id=schedule_id,
            status='active'
        )
        
        db.session.add(enrollment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{child.name} has been enrolled in {schedule.program.name}!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Enrollment failed. Please try again.'}), 500

@app.route('/enrollment/<int:enrollment_id>/cancel', methods=['POST'])
@login_required(role='parent')
def cancel_enrollment(enrollment_id):
    """Cancel an enrollment"""
    parent = Parent.query.filter_by(user_id=session['user_id']).first()
    enrollment = Enrollment.query.join(Child).filter(
        Enrollment.id == enrollment_id,
        Child.parent_id == parent.id
    ).first()
    
    if not enrollment:
        return jsonify({'error': 'Enrollment not found'}), 404
    
    try:
        enrollment.status = 'cancelled'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Enrollment cancelled for {enrollment.child.name}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to cancel enrollment'}), 500

# API ENDPOINTS FOR MAP FUNCTIONALITY AND CHILD MANAGEMENT

@app.route('/api/centers')
def api_centers():
    """API endpoint to get centers data for map"""
    category_id = request.args.get('category_id')
    search_query = request.args.get('search', '')
    
    # Base query
    query = Center.query
    
    # Filter by category if provided
    if category_id:
        query = query.join(Program).join(Category).filter(
            Category.id == category_id
        ).distinct()
    
    # Search filter
    if search_query:
        query = query.filter(
            Center.center_name.contains(search_query) |
            Center.description.contains(search_query) |
            Center.address.contains(search_query)
        )
    
    centers = query.all()
    
    # Format for JSON response
    centers_data = []
    for center in centers:
        if center.latitude and center.longitude:
            # Get programs for this center
            programs = Program.query.filter_by(center_id=center.id, is_active=True).all()
            
            center_data = {
                'id': center.id,
                'name': center.center_name,
                'description': center.description,
                'address': center.address,
                'latitude': center.latitude,
                'longitude': center.longitude,
                'phone': center.user.phone,
                'programs_count': len(programs),
                'teachers_count': len(center.teachers),
                'programs': [
                    {
                        'id': program.id,
                        'name': program.name,
                        'category': program.category.name,
                        'category_color': program.category.color,
                        'category_icon': program.category.icon,
                        'price': program.get_price_display(),
                        'age_range': program.get_age_range()
                    }
                    for program in programs[:3]  # Limit to first 3 programs
                ]
            }
            centers_data.append(center_data)
    
    return jsonify(centers_data)

@app.route('/api/available-programs/<int:child_id>')
@login_required(role='parent')
def available_programs(child_id):
    """Get available programs for a child"""
    parent = Parent.query.filter_by(user_id=session['user_id']).first()
    child = Child.query.filter_by(id=child_id, parent_id=parent.id).first()
    
    if not child:
        return jsonify({'error': 'Child not found'}), 404
    
    # Get child's age
    child_age = None
    if child.birth_date:
        child_age = date.today().year - child.birth_date.year
    
    # Get all active schedules
    schedules = Schedule.query.filter_by(is_active=True).all()
    
    available_programs = []
    for schedule in schedules:
        # Check if already enrolled
        existing = Enrollment.query.filter_by(
            child_id=child_id,
            schedule_id=schedule.id,
            status='active'
        ).first()
        
        if existing:
            continue
        
        # Check age requirements
        if child_age:
            if schedule.program.min_age and child_age < schedule.program.min_age:
                continue
            if schedule.program.max_age and child_age > schedule.program.max_age:
                continue
        
        # Check capacity
        current_enrollments = Enrollment.query.filter_by(
            schedule_id=schedule.id,
            status='active'
        ).count()
        
        if current_enrollments >= schedule.max_students:
            continue
        
        # Add to available programs
        program_data = {
            'id': schedule.program.id,
            'name': schedule.program.name,
            'short_description': schedule.program.short_description,
            'center_name': schedule.program.center.center_name,
            'category_icon': schedule.program.category.icon,
            'category_color': schedule.program.category.color,
            'price_display': schedule.program.get_price_display(),
            'schedules': [{
                'id': schedule.id,
                'day_name': schedule.get_day_name(),
                'time_range': schedule.get_time_range()
            }]
        }
        
        available_programs.append(program_data)
    
    return jsonify({'programs': available_programs})

@app.route('/api/geocode')
def api_geocode():
    """API endpoint for geocoding addresses"""
    address = request.args.get('address')
    if not address:
        return jsonify({'error': 'Address parameter required'}), 400
    
    geocoding_service = GeocodingService()
    coordinates = geocoding_service.geocode_address(address, "Astana", "Kazakhstan")
    
    if coordinates:
        return jsonify({
            'latitude': coordinates[0],
            'longitude': coordinates[1],
            'success': True
        })
    else:
        return jsonify({
            'error': 'Address not found',
            'success': False
        }), 404

@app.route('/api/distance')
def api_distance():
    """API endpoint to calculate distance between points"""
    try:
        lat1 = float(request.args.get('lat1'))
        lon1 = float(request.args.get('lon1'))
        lat2 = float(request.args.get('lat2'))
        lon2 = float(request.args.get('lon2'))
        
        geocoding_service = GeocodingService()
        distance = geocoding_service.get_distance(lat1, lon1, lat2, lon2)
        
        return jsonify({
            'distance_km': round(distance, 2),
            'distance_text': f"{distance:.1f} km"
        })
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid coordinates'}), 400

@app.route('/center/dashboard')
@login_required(role='center')
def center_dashboard():
    """Center dashboard - manage profile, programs, teachers"""
    center = Center.query.filter_by(user_id=session['user_id']).first()
    teachers = Teacher.query.filter_by(center_id=center.id).all() if center else []
    programs = Program.query.filter_by(center_id=center.id).all() if center else []
    schedules = Schedule.query.join(Program).filter(Program.center_id == center.id).all() if center else []
    
    total_students = 0
    if center:
        total_students = db.session.query(Enrollment).join(Schedule).join(Program).filter(
            Program.center_id == center.id,
            Enrollment.status == 'active'
        ).count()
    
    stats = {
        'programs': len(programs),
        'teachers': len(teachers),
        'students': total_students,
        'classes': len(schedules)
    }
    
    return render_template('dashboards/center_dashboard.html', 
                         center=center, 
                         teachers=teachers, 
                         programs=programs,
                         schedules=schedules[:5],
                         stats=stats)

@app.route('/teacher/dashboard')
@login_required(role='teacher')
def teacher_dashboard():
    """Teacher dashboard - view schedule, students, classes"""
    teacher = Teacher.query.filter_by(user_id=session['user_id']).first()
    center = teacher.center if teacher else None
    schedules = Schedule.query.filter_by(teacher_id=teacher.id, is_active=True).all() if teacher else []
    
    today = date.today()
    today_weekday = today.weekday()
    today_classes = [s for s in schedules if s.day_of_week == today_weekday]
    
    total_students = 0
    if teacher:
        total_students = db.session.query(Enrollment).join(Schedule).filter(
            Schedule.teacher_id == teacher.id,
            Enrollment.status == 'active'
        ).count()
    
    stats = {
        'today_classes': len(today_classes),
        'students': total_students,
        'assigned_classes': len(schedules)
    }
    
    return render_template('dashboards/teacher_dashboard.html', 
                         teacher=teacher, 
                         center=center, 
                         schedules=schedules,
                         today_classes=today_classes,
                         stats=stats)

@app.route('/logout')
def logout():
    """Handle user logout"""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

# PROGRAM MANAGEMENT ROUTES (keep all existing)

@app.route('/center/programs')
@login_required(role='center')
def center_programs():
    """Center program management page"""
    center = Center.query.filter_by(user_id=session['user_id']).first()
    programs = Program.query.filter_by(center_id=center.id).all() if center else []
    categories = Category.query.all()
    
    return render_template('center/programs.html', 
                         center=center, 
                         programs=programs,
                         categories=categories)

@app.route('/center/programs/add', methods=['GET', 'POST'])
@login_required(role='center')
def add_program():
    """Add new program"""
    center = Center.query.filter_by(user_id=session['user_id']).first()
    
    if request.method == 'POST':
        name = request.form.get('name')
        category_id = request.form.get('category_id')
        description = request.form.get('description')
        short_description = request.form.get('short_description')
        price_per_month = request.form.get('price_per_month')
        price_per_session = request.form.get('price_per_session')
        duration_minutes = request.form.get('duration_minutes')
        min_age = request.form.get('min_age')
        max_age = request.form.get('max_age')
        max_students = request.form.get('max_students')
        requirements = request.form.get('requirements')
        benefits = request.form.get('benefits')
        
        if not all([name, category_id]):
            flash('Please fill in program name and select a category.', 'danger')
            return redirect(request.url)
        
        try:
            # Handle photo upload
            photo_url = None
            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename:
                    photo_url = save_uploaded_file(file, 'programs')
            
            program = Program(
                center_id=center.id,
                category_id=int(category_id),
                name=name,
                description=description,
                short_description=short_description,
                price_per_month=float(price_per_month) if price_per_month else None,
                price_per_session=float(price_per_session) if price_per_session else None,
                duration_minutes=int(duration_minutes) if duration_minutes else None,
                min_age=int(min_age) if min_age else None,
                max_age=int(max_age) if max_age else None,
                max_students=int(max_students) if max_students else 20,
                requirements=requirements,
                benefits=benefits,
                photo_url=photo_url
            )
            
            db.session.add(program)
            db.session.commit()
            
            flash(f'Program "{name}" has been added successfully!', 'success')
            return redirect(url_for('center_programs'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while adding the program. Please try again.', 'danger')
    
    categories = Category.query.all()
    return render_template('center/add_program.html', center=center, categories=categories)

@app.route('/center/programs/<int:program_id>/edit', methods=['GET', 'POST'])
@login_required(role='center')
def edit_program(program_id):
    """Edit existing program"""
    center = Center.query.filter_by(user_id=session['user_id']).first()
    program = Program.query.filter_by(id=program_id, center_id=center.id).first()
    
    if not program:
        flash('Program not found.', 'danger')
        return redirect(url_for('center_programs'))
    
    if request.method == 'POST':
        program.name = request.form.get('name')
        program.category_id = int(request.form.get('category_id'))
        program.description = request.form.get('description')
        program.short_description = request.form.get('short_description')
        
        price_per_month = request.form.get('price_per_month')
        program.price_per_month = float(price_per_month) if price_per_month else None
        
        price_per_session = request.form.get('price_per_session')
        program.price_per_session = float(price_per_session) if price_per_session else None
        
        duration_minutes = request.form.get('duration_minutes')
        program.duration_minutes = int(duration_minutes) if duration_minutes else None
        
        min_age = request.form.get('min_age')
        program.min_age = int(min_age) if min_age else None
        
        max_age = request.form.get('max_age')
        program.max_age = int(max_age) if max_age else None
        
        max_students = request.form.get('max_students')
        program.max_students = int(max_students) if max_students else 20
        
        program.requirements = request.form.get('requirements')
        program.benefits = request.form.get('benefits')
        program.is_active = bool(request.form.get('is_active'))
        
        # Handle photo upload
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename:
                program.photo_url = save_uploaded_file(file, 'programs')
        
        try:
            db.session.commit()
            flash(f'Program "{program.name}" has been updated successfully!', 'success')
            return redirect(url_for('center_programs'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the program. Please try again.', 'danger')
    
    categories = Category.query.all()
    return render_template('center/edit_program.html', center=center, program=program, categories=categories)

@app.route('/center/programs/<int:program_id>/delete', methods=['POST'])
@login_required(role='center')
def delete_program(program_id):
    """Delete program"""
    center = Center.query.filter_by(user_id=session['user_id']).first()
    program = Program.query.filter_by(id=program_id, center_id=center.id).first()
    
    if not program:
        flash('Program not found.', 'danger')
        return redirect(url_for('center_programs'))
    
    try:
        # Check for active enrollments
        active_enrollments = db.session.query(Enrollment).join(Schedule).filter(
            Schedule.program_id == program.id,
            Enrollment.status == 'active'
        ).count()
        
        if active_enrollments > 0:
            flash(f'Cannot delete program with {active_enrollments} active enrollments.', 'danger')
            return redirect(url_for('center_programs'))
        
        program_name = program.name
        db.session.delete(program)
        db.session.commit()
        flash(f'Program "{program_name}" has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the program. Please try again.', 'danger')
    
    return redirect(url_for('center_programs'))

# SCHEDULE MANAGEMENT ROUTES (keep all existing)

@app.route('/center/schedules')
@login_required(role='center')
def center_schedules():
    """Center schedule management page"""
    center = Center.query.filter_by(user_id=session['user_id']).first()
    
    schedules = Schedule.query.join(Program).filter(
        Program.center_id == center.id
    ).order_by(Schedule.day_of_week, Schedule.start_time).all() if center else []
    
    programs = Program.query.filter_by(center_id=center.id, is_active=True).all() if center else []
    teachers = Teacher.query.filter_by(center_id=center.id).all() if center else []
    
    return render_template('center/schedules.html', 
                         center=center, 
                         schedules=schedules,
                         programs=programs,
                         teachers=teachers)

@app.route('/center/schedules/add', methods=['GET', 'POST'])
@login_required(role='center')
def add_schedule():
    """Add new class schedule"""
    center = Center.query.filter_by(user_id=session['user_id']).first()
    
    if request.method == 'POST':
        from datetime import time
        
        program_id = request.form.get('program_id')
        teacher_id = request.form.get('teacher_id')
        day_of_week = request.form.get('day_of_week')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        max_students = request.form.get('max_students')
        room_name = request.form.get('room_name')
        notes = request.form.get('notes')
        
        if not all([program_id, teacher_id, day_of_week, start_time_str, end_time_str]):
            flash('Please fill in all required fields.', 'danger')
            return redirect(request.url)
        
        program = Program.query.filter_by(id=program_id, center_id=center.id).first()
        teacher = Teacher.query.filter_by(id=teacher_id, center_id=center.id).first()
        
        if not program or not teacher:
            flash('Invalid program or teacher selection.', 'danger')
            return redirect(request.url)
        
        try:
            start_time = time.fromisoformat(start_time_str)
            end_time = time.fromisoformat(end_time_str)
            
            if start_time >= end_time:
                flash('End time must be after start time.', 'danger')
                return redirect(request.url)
            
            existing_schedules = Schedule.query.filter_by(
                teacher_id=teacher_id,
                day_of_week=day_of_week,
                is_active=True
            ).all()
            
            new_schedule = Schedule(
                program_id=program_id,
                teacher_id=teacher_id,
                day_of_week=int(day_of_week),
                start_time=start_time,
                end_time=end_time,
                max_students=int(max_students) if max_students else program.max_students,
                room_name=room_name,
                notes=notes
            )
            
            for existing in existing_schedules:
                if new_schedule.conflicts_with(existing):
                    flash(f'Schedule conflicts with existing class: {existing.program.name} at {existing.get_time_range()}', 'danger')
                    return redirect(request.url)
            
            db.session.add(new_schedule)
            db.session.commit()
            
            flash(f'Class schedule created successfully for {program.name}!', 'success')
            return redirect(url_for('center_schedules'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the schedule. Please try again.', 'danger')
    
    programs = Program.query.filter_by(center_id=center.id, is_active=True).all() if center else []
    teachers = Teacher.query.filter_by(center_id=center.id).all() if center else []
    
    return render_template('center/add_schedule.html', 
                         center=center, 
                         programs=programs,
                         teachers=teachers)

@app.route('/center/schedules/<int:schedule_id>/edit', methods=['GET', 'POST'])
@login_required(role='center')
def edit_schedule(schedule_id):
    """Edit existing schedule"""
    center = Center.query.filter_by(user_id=session['user_id']).first()
    
    schedule = Schedule.query.join(Program).filter(
        Schedule.id == schedule_id,
        Program.center_id == center.id
    ).first()
    
    if not schedule:
        flash('Schedule not found.', 'danger')
        return redirect(url_for('center_schedules'))
    
    if request.method == 'POST':
        from datetime import time
        
        program_id = request.form.get('program_id')
        teacher_id = request.form.get('teacher_id')
        day_of_week = request.form.get('day_of_week')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        max_students = request.form.get('max_students')
        room_name = request.form.get('room_name')
        notes = request.form.get('notes')
        is_active = bool(request.form.get('is_active'))
        
        try:
            start_time = time.fromisoformat(start_time_str)
            end_time = time.fromisoformat(end_time_str)
            
            if start_time >= end_time:
                flash('End time must be after start time.', 'danger')
                return redirect(request.url)
            
            existing_schedules = Schedule.query.filter(
                Schedule.teacher_id == teacher_id,
                Schedule.day_of_week == day_of_week,
                Schedule.is_active == True,
                Schedule.id != schedule_id
            ).all()
            
            schedule.program_id = program_id
            schedule.teacher_id = teacher_id
            schedule.day_of_week = int(day_of_week)
            schedule.start_time = start_time
            schedule.end_time = end_time
            schedule.max_students = int(max_students) if max_students else schedule.program.max_students
            schedule.room_name = room_name
            schedule.notes = notes
            schedule.is_active = is_active
            
            for existing in existing_schedules:
                if schedule.conflicts_with(existing):
                    flash(f'Schedule conflicts with existing class: {existing.program.name} at {existing.get_time_range()}', 'danger')
                    return redirect(request.url)
            
            db.session.commit()
            flash('Schedule updated successfully!', 'success')
            return redirect(url_for('center_schedules'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the schedule. Please try again.', 'danger')
    
    programs = Program.query.filter_by(center_id=center.id, is_active=True).all()
    teachers = Teacher.query.filter_by(center_id=center.id).all()
    
    return render_template('center/edit_schedule.html', 
                         center=center, 
                         schedule=schedule,
                         programs=programs,
                         teachers=teachers)

@app.route('/center/schedules/<int:schedule_id>/delete', methods=['POST'])
@login_required(role='center')
def delete_schedule(schedule_id):
    """Delete schedule"""
    center = Center.query.filter_by(user_id=session['user_id']).first()
    
    schedule = Schedule.query.join(Program).filter(
        Schedule.id == schedule_id,
        Program.center_id == center.id
    ).first()
    
    if not schedule:
        flash('Schedule not found.', 'danger')
        return redirect(url_for('center_schedules'))
    
    try:
        active_enrollments = Enrollment.query.filter_by(
            schedule_id=schedule_id,
            status='active'
        ).count()
        
        if active_enrollments > 0:
            flash(f'Cannot delete schedule with {active_enrollments} active enrollments. Please cancel enrollments first.', 'danger')
            return redirect(url_for('center_schedules'))
        
        schedule_info = f"{schedule.program.name} - {schedule.get_day_name()} {schedule.get_time_range()}"
        db.session.delete(schedule)
        db.session.commit()
        
        flash(f'Schedule "{schedule_info}" has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the schedule. Please try again.', 'danger')
    
    return redirect(url_for('center_schedules'))

# TEACHER SCHEDULE ROUTES (keep existing)

@app.route('/teacher/schedule')
@login_required(role='teacher')
def teacher_schedule():
    """Teacher schedule view"""
    teacher = Teacher.query.filter_by(user_id=session['user_id']).first()
    
    schedules = Schedule.query.filter_by(
        teacher_id=teacher.id, 
        is_active=True
    ).order_by(Schedule.day_of_week, Schedule.start_time).all() if teacher else []
    
    schedule_by_day = {}
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for day_num, day_name in enumerate(days):
        schedule_by_day[day_name] = [
            s for s in schedules if s.day_of_week == day_num
        ]
    
    return render_template('teacher/schedule.html', 
                         teacher=teacher,
                         schedule_by_day=schedule_by_day,
                         days=days)

@app.route('/teacher/students')
@login_required(role='teacher')
def teacher_students():
    """Teacher's student list"""
    teacher = Teacher.query.filter_by(user_id=session['user_id']).first()
    
    enrollments = Enrollment.query.join(Schedule).filter(
        Schedule.teacher_id == teacher.id,
        Enrollment.status == 'active'
    ).order_by(Schedule.day_of_week, Schedule.start_time).all() if teacher else []
    
    students_by_class = {}
    for enrollment in enrollments:
        schedule = enrollment.schedule
        class_key = f"{schedule.program.name} - {schedule.get_day_name()} {schedule.get_time_range()}"
        
        if class_key not in students_by_class:
            students_by_class[class_key] = {
                'schedule': schedule,
                'students': []
            }
        
        students_by_class[class_key]['students'].append(enrollment)
    
    return render_template('teacher/students.html', 
                         teacher=teacher,
                         students_by_class=students_by_class)

@app.route('/program/<int:program_id>')
def view_program(program_id):
    """Public program detail view"""
    program = Program.query.get_or_404(program_id)
    if not program.is_active:
        flash('This program is currently not available.', 'warning')
        return redirect(url_for('index'))
    
    return render_template('public/program_detail.html', program=program)

@app.route('/center/<int:center_id>')
def view_center(center_id):
    """Public center profile view"""
    center = Center.query.get_or_404(center_id)
    programs = Program.query.filter_by(center_id=center.id, is_active=True).all()
    teachers = Teacher.query.filter_by(center_id=center.id).all()
    
    # Calculate statistics
    active_schedules_count = 0
    unique_categories = set()
    
    for program in programs:
        # Count active schedules
        for schedule in program.schedules:
            if schedule.is_active:
                active_schedules_count += 1
        
        # Collect unique categories
        unique_categories.add(program.category.id)
    
    stats = {
        'programs': len(programs),
        'teachers': len(teachers),
        'active_schedules': active_schedules_count,
        'categories': len(unique_categories)
    }
    
    return render_template('public/center_profile.html', 
                         center=center, 
                         programs=programs,
                         teachers=teachers,
                         stats=stats)

@app.route('/admin/geocode-centers')
def geocode_existing_centers():
    """Utility function to geocode existing centers without coordinates"""
    if not app.debug:
        return "This function is only available in debug mode", 403
    
    geocoding_service = GeocodingService()
    centers = Center.query.filter(Center.latitude.is_(None)).all()
    
    updated_count = 0
    for center in centers:
        try:
            coordinates = geocoding_service.geocode_address(center.address, "Astana", "Kazakhstan")
            if coordinates:
                center.latitude, center.longitude = coordinates
                updated_count += 1
        except Exception as e:
            print(f"Error geocoding {center.center_name}: {e}")
    
    if updated_count > 0:
        db.session.commit()
        return f"Successfully geocoded {updated_count} centers"
    else:
        return "No centers updated"

# Initialize default categories
def init_default_categories():
    """Initialize default categories if none exist"""
    if Category.query.count() == 0:
        sports = Category(name='Sports', description='Physical activities and sports programs', icon='bi-trophy', color='#28a745')
        arts = Category(name='Arts & Crafts', description='Creative and artistic programs', icon='bi-palette', color='#6f42c1')
        academic = Category(name='Academic', description='Educational and academic subjects', icon='bi-book', color='#007bff')
        tech = Category(name='Technology', description='Programming, robotics, and tech skills', icon='bi-cpu', color='#17a2b8')
        music = Category(name='Music', description='Musical instruments and vocal training', icon='bi-music-note', color='#fd7e14')
        language = Category(name='Languages', description='Foreign language learning', icon='bi-translate', color='#20c997')
        
        db.session.add_all([sports, arts, academic, tech, music, language])
        db.session.commit()
        
        martial_arts = Category(name='Martial Arts', parent_id=sports.id, icon='bi-person-arms-up', color='#dc3545')
        team_sports = Category(name='Team Sports', parent_id=sports.id, icon='bi-people', color='#28a745')
        individual_sports = Category(name='Individual Sports', parent_id=sports.id, icon='bi-person', color='#ffc107')
        visual_arts = Category(name='Visual Arts', parent_id=arts.id, icon='bi-brush', color='#6f42c1')
        performing_arts = Category(name='Performing Arts', parent_id=arts.id, icon='bi-mask', color='#e83e8c')
        math = Category(name='Mathematics', parent_id=academic.id, icon='bi-calculator', color='#007bff')
        science = Category(name='Science', parent_id=academic.id, icon='bi-flask', color='#17a2b8')
        
        db.session.add_all([martial_arts, team_sports, individual_sports, visual_arts, performing_arts, math, science])
        db.session.commit()
        
        boxing = Category(name='Boxing', parent_id=martial_arts.id, icon='bi-hand-fist', color='#dc3545')
        karate = Category(name='Karate', parent_id=martial_arts.id, icon='bi-person-arms-up', color='#fd7e14')
        football = Category(name='Football', parent_id=team_sports.id, icon='bi-soccer', color='#28a745')
        
        db.session.add_all([boxing, karate, football])
        db.session.commit()

@app.route('/center/enrollments')
@login_required(role='center')
def center_enrollments():
    """View center enrollments"""
    center = Center.query.filter_by(user_id=session['user_id']).first()
    
    # Get all enrollments for this center's programs
    enrollments = db.session.query(Enrollment).join(Schedule).join(Program).filter(
        Program.center_id == center.id
    ).order_by(Enrollment.created_at.desc()).all() if center else []
    
    # Group by status
    active_enrollments = [e for e in enrollments if e.status == 'active']
    pending_enrollments = [e for e in enrollments if e.status == 'pending']
    cancelled_enrollments = [e for e in enrollments if e.status == 'cancelled']
    
    return render_template('center/enrollments.html',
                         center=center,
                         active_enrollments=active_enrollments,
                         pending_enrollments=pending_enrollments,
                         cancelled_enrollments=cancelled_enrollments)

@app.route('/center/enrollment/<int:enrollment_id>/approve', methods=['POST'])
@login_required(role='center')
def approve_enrollment(enrollment_id):
    """Approve a pending enrollment"""
    center = Center.query.filter_by(user_id=session['user_id']).first()
    enrollment = db.session.query(Enrollment).join(Schedule).join(Program).filter(
        Enrollment.id == enrollment_id,
        Program.center_id == center.id
    ).first()
    
    if not enrollment:
        return jsonify({'error': 'Enrollment not found'}), 404
    
    try:
        enrollment.status = 'active'
        enrollment.approved_by = session['user_id']
        enrollment.approved_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Enrollment approved for {enrollment.child.name}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to approve enrollment'}), 500

@app.route('/parent/enrollments')
@login_required(role='parent')
def parent_enrollments():
    """View parent's children enrollments"""
    parent = Parent.query.filter_by(user_id=session['user_id']).first()
    
    # Get all enrollments for parent's children
    enrollments = db.session.query(Enrollment).join(Child).filter(
        Child.parent_id == parent.id
    ).order_by(Enrollment.created_at.desc()).all() if parent else []
    
    return render_template('parent/enrollments.html',
                         parent=parent,
                         enrollments=enrollments)

# Enhanced API endpoints
@app.route('/api/child/<int:child_id>/enrollments')
@login_required(role='parent')
def api_child_enrollments(child_id):
    """Get enrollments for a specific child"""
    parent = Parent.query.filter_by(user_id=session['user_id']).first()
    child = Child.query.filter_by(id=child_id, parent_id=parent.id).first()
    
    if not child:
        return jsonify({'error': 'Child not found'}), 404
    
    enrollments_data = []
    for enrollment in child.enrollments:
        enrollment_data = {
            'id': enrollment.id,
            'program_name': enrollment.schedule.program.name,
            'center_name': enrollment.schedule.program.center.center_name,
            'schedule': enrollment.get_schedule_info(),
            'status': enrollment.status,
            'enrollment_date': enrollment.enrollment_date.strftime('%Y-%m-%d'),
            'status_display': enrollment.get_status_display(),
            'status_class': enrollment.get_status_badge_class()
        }
        enrollments_data.append(enrollment_data)
    
    return jsonify({'enrollments': enrollments_data})

@app.route('/api/center/<int:center_id>/stats')
def api_center_stats(center_id):
    """Get center statistics"""
    center = Center.query.get_or_404(center_id)
    
    # Calculate stats
    total_programs = Program.query.filter_by(center_id=center.id, is_active=True).count()
    total_teachers = Teacher.query.filter_by(center_id=center.id).count()
    total_students = db.session.query(Enrollment).join(Schedule).join(Program).filter(
        Program.center_id == center.id,
        Enrollment.status == 'active'
    ).count()
    
    # Get recent enrollments
    recent_enrollments = db.session.query(Enrollment).join(Schedule).join(Program).filter(
        Program.center_id == center.id
    ).order_by(Enrollment.created_at.desc()).limit(5).all()
    
    recent_data = []
    for enrollment in recent_enrollments:
        recent_data.append({
            'child_name': enrollment.child.name,
            'program_name': enrollment.schedule.program.name,
            'enrollment_date': enrollment.enrollment_date.strftime('%Y-%m-%d'),
            'status': enrollment.get_status_display()
        })
    
    return jsonify({
        'total_programs': total_programs,
        'total_teachers': total_teachers,
        'total_students': total_students,
        'recent_enrollments': recent_data
    })

# Initialize database tables
def create_tables():
    """Create database tables"""
    with app.app_context():
        db.create_all()
        init_default_categories()

if __name__ == '__main__':
    create_tables()
    app.run(debug=True, host='localhost', port=5000)