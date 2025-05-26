from database import db
from datetime import datetime, time
import secrets

class User(db.Model):
    """Base user model for all user types"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False)  # 'parent', 'center', 'teacher'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'

class Parent(db.Model):
    """Parent-specific information"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    address = db.Column(db.String(200))
    
    # Relationship
    user = db.relationship('User', backref=db.backref('parent_profile', uselist=False))
    
    def __repr__(self):
        return f'<Parent {self.user.name}>'

class Center(db.Model):
    """Education center information"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    center_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float)  # Will be populated via geocoding
    longitude = db.Column(db.Float)  # Will be populated via geocoding
    photo_url = db.Column(db.String(255))
    website = db.Column(db.String(255))
    schedule_info = db.Column(db.Text)  # General schedule information
    invite_code = db.Column(db.String(8), unique=True)  # For teacher invitations
    
    # Relationship
    user = db.relationship('User', backref=db.backref('center_profile', uselist=False))

    def __init__(self, **kwargs):
        super(Center, self).__init__(**kwargs)
        if not self.invite_code:
            self.invite_code = self.generate_invite_code()

    def generate_invite_code(self):
        """Generate a unique 8-character invite code for teachers"""
        while True:
            code = secrets.token_hex(4).upper()  # 8 character hex code
            existing = Center.query.filter_by(invite_code=code).first()
            if not existing:
                return code

    def __repr__(self):
        return f'<Center {self.center_name}>'

class Teacher(db.Model):
    """Teacher information"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    center_id = db.Column(db.Integer, db.ForeignKey('center.id'), nullable=False)
    specialization = db.Column(db.String(100))
    bio = db.Column(db.Text)
    hire_date = db.Column(db.Date, default=datetime.utcnow().date)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('teacher_profile', uselist=False))
    center = db.relationship('Center', backref=db.backref('teachers', lazy=True))

    def __repr__(self):
        return f'<Teacher {self.user.name} at {self.center.center_name}>'

class Child(db.Model):
    """Children registered by parents"""
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('parent.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date)
    grade = db.Column(db.String(20))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    parent = db.relationship('Parent', backref=db.backref('children', lazy=True))

    def __repr__(self):
        return f'<Child {self.name}>'

class Category(db.Model):
    """Program categories with nested structure"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    icon = db.Column(db.String(50))  # Bootstrap icon class
    color = db.Column(db.String(7), default='#6c757d')  # Hex color code
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Self-referencing relationship for nested categories
    parent = db.relationship('Category', remote_side=[id], backref='subcategories')
    
    def get_full_path(self):
        """Get full category path like 'Sports → Martial Arts → Boxing'"""
        path = [self.name]
        current = self.parent
        while current:
            path.insert(0, current.name)
            current = current.parent
        return ' → '.join(path)
    
    def get_all_children(self):
        """Get all subcategories recursively"""
        children = list(self.subcategories)
        for child in self.subcategories:
            children.extend(child.get_all_children())
        return children

    def __repr__(self):
        return f'<Category {self.get_full_path()}>'

class Program(db.Model):
    """Educational programs offered by centers"""
    id = db.Column(db.Integer, primary_key=True)
    center_id = db.Column(db.Integer, db.ForeignKey('center.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    short_description = db.Column(db.String(255))
    
    # Program details
    price_per_month = db.Column(db.Float)
    price_per_session = db.Column(db.Float)
    duration_minutes = db.Column(db.Integer)  # Duration of each session
    min_age = db.Column(db.Integer)
    max_age = db.Column(db.Integer)
    max_students = db.Column(db.Integer, default=20)
    
    # Program status
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    
    # Additional info
    requirements = db.Column(db.Text)  # What students need to bring/know
    benefits = db.Column(db.Text)     # What students will learn/gain
    photo_url = db.Column(db.String(255))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    center = db.relationship('Center', backref=db.backref('programs', lazy=True))
    category = db.relationship('Category', backref=db.backref('programs', lazy=True))
    
    def get_age_range(self):
        """Get formatted age range string"""
        if self.min_age and self.max_age:
            return f"{self.min_age}-{self.max_age} years"
        elif self.min_age:
            return f"{self.min_age}+ years"
        elif self.max_age:
            return f"Up to {self.max_age} years"
        return "All ages"
    
    def get_price_display(self):
        """Get formatted price string"""
        prices = []
        if self.price_per_month:
            prices.append(f"{self.price_per_month:,.0f}₸/month")
        if self.price_per_session:
            prices.append(f"{self.price_per_session:,.0f}₸/session")
        return " or ".join(prices) if prices else "Contact for pricing"

    def __repr__(self):
        return f'<Program {self.name} at {self.center.center_name}>'

# NEW MODELS FOR PHASE 4: SCHEDULING SYSTEM

class Schedule(db.Model):
    """Scheduled classes for programs"""
    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    
    # Schedule details
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    
    # Class details
    max_students = db.Column(db.Integer, default=20)
    room_name = db.Column(db.String(100))  # Optional room/location info
    notes = db.Column(db.Text)  # Additional notes about the class
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    start_date = db.Column(db.Date, default=datetime.utcnow().date)  # When this schedule starts
    end_date = db.Column(db.Date)  # Optional end date for temporary schedules
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    program = db.relationship('Program', backref=db.backref('schedules', lazy=True))
    teacher = db.relationship('Teacher', backref=db.backref('schedules', lazy=True))
    
    def get_day_name(self):
        """Get day name from day_of_week number"""
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return days[self.day_of_week]
    
    def get_time_range(self):
        """Get formatted time range"""
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"
    
    def get_duration_minutes(self):
        """Calculate class duration in minutes"""
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        return end_minutes - start_minutes
    
    def conflicts_with(self, other_schedule):
        """Check if this schedule conflicts with another schedule"""
        if self.day_of_week != other_schedule.day_of_week:
            return False
        if self.teacher_id != other_schedule.teacher_id:
            return False
        
        # Check time overlap
        return not (self.end_time <= other_schedule.start_time or 
                   self.start_time >= other_schedule.end_time)
    
    def __repr__(self):
        return f'<Schedule {self.program.name} - {self.get_day_name()} {self.get_time_range()}>'

class Enrollment(db.Model):
    """Student enrollments in scheduled classes"""
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id'), nullable=False)
    
    # Enrollment details
    enrollment_date = db.Column(db.Date, default=datetime.utcnow().date)
    status = db.Column(db.String(20), default='active')  # active, paused, cancelled
    
    # Payment info (basic)
    payment_method = db.Column(db.String(50))  # monthly, per_session, etc.
    notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    child = db.relationship('Child', backref=db.backref('enrollments', lazy=True))
    schedule = db.relationship('Schedule', backref=db.backref('enrollments', lazy=True))
    
    def __repr__(self):
        return f'<Enrollment {self.child.name} in {self.schedule.program.name}>'

class Attendance(db.Model):
    """Attendance tracking for individual classes"""
    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('enrollment.id'), nullable=False)
    class_date = db.Column(db.Date, nullable=False)
    
    # Attendance status
    status = db.Column(db.String(20), default='present')  # present, absent, late, excused
    notes = db.Column(db.Text)  # Optional notes from teacher
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    enrollment = db.relationship('Enrollment', backref=db.backref('attendance_records', lazy=True))
    
    def __repr__(self):
        return f'<Attendance {self.enrollment.child.name} - {self.class_date} ({self.status})>'