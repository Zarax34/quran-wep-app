from app.extensions import db
from flask_login import UserMixin
from datetime import datetime

# Association tables
activity_circles = db.Table('activity_circles',
    db.Column('activity_id', db.Integer, db.ForeignKey('center_activity.id'), primary_key=True),
    db.Column('circle_id', db.Integer, db.ForeignKey('circle.id'), primary_key=True)
)

holiday_circles = db.Table('holiday_circles',
    db.Column('holiday_id', db.Integer, db.ForeignKey('holiday.id'), primary_key=True),
    db.Column('circle_id', db.Integer, db.ForeignKey('circle.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, support, parent
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    fingerprint_id = db.Column(db.String(100), unique=True, nullable=True)
    # Added for PR-01 migration strategy
    password_needs_rehash = db.Column(db.Boolean, default=True)

class Parent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('parent_profile', uselist=False))

class Circle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    teacher_name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    academic_year = db.Column(db.String(10), default='2025')
    category = db.Column(db.String(50), default='شباب') # شباب or أشبال
    requires_approval = db.Column(db.Boolean, default=True)
    teacher = db.relationship('User', backref='circles')

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    student_phone = db.Column(db.String(20))
    parent_phone = db.Column(db.String(20))
    parent_id = db.Column(db.Integer, db.ForeignKey('parent.id'))
    circle_id = db.Column(db.Integer, db.ForeignKey('circle.id'))
    is_active = db.Column(db.Boolean, default=True)
    photo = db.Column(db.String(200))
    academic_year = db.Column(db.String(10), default='2025')
    pending_approval = db.Column(db.Boolean, default=True)
    last_recitation_date = db.Column(db.Date)
    total_verses_since_year_start = db.Column(db.Integer, default=0)
    current_address = db.Column(db.String(200))
    previous_address = db.Column(db.String(200))
    governorate = db.Column(db.String(100))
    date_of_birth = db.Column(db.Date)
    previous_memorization = db.Column(db.String(200))
    enrollment_date = db.Column(db.Date, default=datetime.now().date)
    last_memorized_sura = db.Column(db.String(100), default='الفاتحة')
    last_memorized_ayah = db.Column(db.Integer, default=0)
    memorization_direction = db.Column(db.String(50), default='BaqarahToNas') # or 'NasToBaqarah'
    parent_relationship = db.Column(db.String(50), default='أب')
    circle = db.relationship('Circle', backref='students')
    parent = db.relationship('Parent', backref='students')

class MonthlyPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    plan_type = db.Column(db.String(20), default='حفظ')
    start_surah = db.Column(db.String(100))
    start_verse = db.Column(db.Integer)
    end_surah = db.Column(db.String(100))
    end_verse = db.Column(db.Integer)
    daily_pages = db.Column(db.Float)
    total_pages = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('Student', backref='monthly_plans')

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    circle_id = db.Column(db.Integer, db.ForeignKey('circle.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    surah = db.Column(db.String(100), nullable=False)
    from_verse = db.Column(db.Integer, nullable=False)
    to_verse = db.Column(db.Integer, nullable=False)
    grade = db.Column(db.String(10), nullable=False)
    type = db.Column(db.String(10), default='حفظ')
    notes = db.Column(db.Text)
    academic_year = db.Column(db.String(10), default='2025')
    status = db.Column(db.String(20), default='Approved')
    student = db.relationship('Student', backref='reports')
    teacher = db.relationship('User', backref='reports')
    circle = db.relationship('Circle', backref='reports')

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='حاضر')
    notes = db.Column(db.Text)
    academic_year = db.Column(db.String(10), default='2025')
    student = db.relationship('Student', backref='attendances')

class Holiday(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    reason = db.Column(db.String(200))
    has_attendance = db.Column(db.Boolean, default=False)
    is_recurring = db.Column(db.Boolean, default=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    academic_year = db.Column(db.String(10), default='2025')
    status = db.Column(db.String(20), default='Approved')
    teacher = db.relationship('User', backref='holidays')
    target_circles = db.relationship('Circle', secondary=holiday_circles, backref='holidays')

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(100), default='مركز الإمام حفص')
    site_description = db.Column(db.String(200), default='لتعليم القرآن الكريم')
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(100))
    location_address = db.Column(db.String(300), default='مأرب - شارع الأربعين - خلف مستشفى نيوم')
    location_map_url = db.Column(db.String(500))
    logo = db.Column(db.String(200))
    primary_color = db.Column(db.String(7), default='#2c5aa0')
    secondary_color = db.Column(db.String(7), default='#28a745')
    background_color = db.Column(db.String(7), default='#f8f9fa')
    text_color = db.Column(db.String(7), default='#2c3e50')
    whatsapp_message_template = db.Column(db.Text, default='تقرير {report_type} للتسميع\n\nالطالب: {student_name}\nالحلقة: {circle_name}\nالمعلم: {teacher_name}\nالفترة: من {start_date} إلى {end_date}\n\nالتسميع:\n{reports_details}\n\nإحصائيات الحضور:\n{attendance_stats}\n\n{site_name}')
    support_bank_accounts = db.Column(db.Text, default='بنك الكريمي: 123456789\nبنك الشرق: 987654321\nبنك التضامن: 456789123')
    support_message = db.Column(db.Text, default='نورٌ نُهديه وجيل نربيه')
    dark_mode_enabled = db.Column(db.Boolean, default=False)
    teacher_requires_approval = db.Column(db.Boolean, default=True)
    allow_custom_teacher_name = db.Column(db.Boolean, default=True)
    social_instagram = db.Column(db.String(200))
    social_facebook = db.Column(db.String(200))
    social_whatsapp = db.Column(db.String(200))
    social_telegram = db.Column(db.String(200))
    developer_name = db.Column(db.String(100), default='Your Name')
    developer_link = db.Column(db.String(200), default='https://www.linkedin.com/in/your-linkedin-profile')
    copyright_text = db.Column(db.String(200), default='جميع الحقوق محفوظة')
    login_background = db.Column(db.String(200))
    permissions = db.Column(db.Text, default='{}')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

class Point(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(200))
    date = db.Column(db.Date, default=datetime.now().date)

class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    icon = db.Column(db.String(100))

class StudentBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    date_awarded = db.Column(db.Date, default=datetime.now().date)

class HonorBoard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    rank = db.Column(db.Integer)

class UserLogin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.now)
    ip_address = db.Column(db.String(50))

class EducationalNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    note = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, default=datetime.now().date)

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(200))
    date_posted = db.Column(db.DateTime, default=datetime.now)
    event_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    messages = db.relationship('Message', backref='conversation', lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)

class CenterActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    image = db.Column(db.String(200))
    fee = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    participants = db.relationship('Student', secondary='activity_approval', backref='activities', overlaps="approvals,activity")
    target_circles = db.relationship('Circle', secondary=activity_circles, backref='activities')

class ActivityApproval(db.Model):
    __tablename__ = 'activity_approval'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('center_activity.id'), nullable=False)
    status = db.Column(db.String(20), default='Pending') # Pending, Approved, Rejected
    student = db.relationship('Student', backref='approvals', overlaps="activities,participants")
    activity = db.relationship('CenterActivity', backref='approvals', overlaps="activities,participants,student")

class Alumni(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    graduation_year = db.Column(db.Integer, nullable=False)
    testimonial = db.Column(db.Text)
    photo = db.Column(db.String(200))

class Fee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date_paid = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='Paid') # Paid, Pending
    title = db.Column(db.String(100))
    notes = db.Column(db.Text)

class Work(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(200))
    link = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.now)

class ParentNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('parent.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_read = db.Column(db.Boolean, default=False)

# ===================
# Courses and Tests Models
# ===================
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    teacher = db.relationship('User', backref='courses_taught')
    enrollments = db.relationship('CourseEnrollment', backref='course', lazy='dynamic', cascade="all, delete-orphan")
    tests = db.relationship('Test', backref='course', lazy='dynamic', cascade="all, delete-orphan")

class CourseEnrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='course_enrollments')

class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    test_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    max_score = db.Column(db.Float, nullable=False)
    min_passing_score = db.Column(db.Float, nullable=True)

    scores = db.relationship('TestScore', backref='test', lazy='dynamic', cascade="all, delete-orphan")

class TestScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    recorded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='test_scores')
    recorder = db.relationship('User', backref='recorded_scores')

class Certificate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    certificate_file = db.Column(db.String(255), nullable=True)
    certificate_url = db.Column(db.String(500), nullable=True)

    student = db.relationship('Student', backref='certificates')
    course_info = db.relationship('Course', backref='certificates')
