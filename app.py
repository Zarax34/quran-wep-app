# ---------- 1.  IMPORTS  ----------
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy import inspect, func, text, or_
from functools import wraps
import re, os, urllib.parse
from fpdf import FPDF
from flask_mail import Mail, Message as MailMessage
from apscheduler.schedulers.background import BackgroundScheduler

# ---------- 2.  FLASK INIT  ----------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quran_center.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
db = SQLAlchemy(app)

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
mail = Mail(app)

# Scheduler for automatic emails
scheduler = BackgroundScheduler()
scheduler.start()

def send_weekly_progress_reports():
    with app.app_context():
        parents = Parent.query.filter(Parent.user.has(email=None)).all()
        for parent in parents:
            students = parent.students
            if not students:
                continue

            # Create a summary for each student
            summary = ""
            for student in students:
                stats = get_student_stats(student.id)
                summary += f"<h3>Progress for {student.name}</h3>"
                summary += f"<p><strong>Monthly Reports:</strong> {stats['monthly_reports']}</p>"
                summary += f"<p><strong>Attendance Rate:</strong> {stats['attendance_rate']}%</p>"
                summary += f"<p><strong>Total Verses Memorized:</strong> {stats['total_verses']}</p>"

            # Send the email
            msg = MailMessage(
                'Weekly Progress Report',
                sender='your-email@gmail.com',
                recipients=[parent.user.email]
            )
            msg.html = f"<h1>Weekly Progress Report</h1>{summary}"
            mail.send(msg)

# Schedule the job to run every Sunday at 6 PM
scheduler.add_job(send_weekly_progress_reports, 'cron', day_of_week='sun', hour=18)

# ---------- 3.  MODELS  ----------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, support, parent
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    fingerprint_id = db.Column(db.String(100), unique=True, nullable=True)

class Parent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

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
    circle = db.relationship('Circle', backref='students')
    parent = db.relationship('Parent', backref='students')

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
    teacher = db.relationship('User', backref='holidays')

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
    developer_name = db.Column(db.String(100), default='Your Name')
    developer_link = db.Column(db.String(200), default='https://www.linkedin.com/in/your-linkedin-profile')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    user = db.relationship('User', backref='notifications')

class Point(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(200))
    date = db.Column(db.Date, default=datetime.now().date)
    student = db.relationship('Student', backref='points')

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
    student = db.relationship('Student', backref='student_badges')
    badge = db.relationship('Badge', backref='student_badges')

class HonorBoard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    rank = db.Column(db.Integer)
    student = db.relationship('Student', backref='honor_board_entries')

class UserLogin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.now)
    ip_address = db.Column(db.String(50))
    user = db.relationship('User', backref='logins')

class EducationalNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    note = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, default=datetime.now().date)
    student = db.relationship('Student', backref='educational_notes')
    teacher = db.relationship('User', backref='educational_notes')

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(200))
    date_posted = db.Column(db.DateTime, default=datetime.now)
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

# ===================
# Center Activities Models
# ===================
class CenterActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activity_type = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    target_students = db.Column(db.Integer)
    details = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    circles = db.relationship('Circle', secondary='center_activity_circle', backref='center_activities')

center_activity_circle = db.Table('center_activity_circle',
    db.Column('activity_id', db.Integer, db.ForeignKey('center_activity.id'), primary_key=True),
    db.Column('circle_id', db.Integer, db.ForeignKey('circle.id'), primary_key=True)
)

# ===================
# Courses and Tests Models
# ===================
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
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
    certificate_file = db.Column(db.String(255), nullable=False) # Stores the path to the PDF file

    student = db.relationship('Student', backref='certificates')
    course_info = db.relationship('Course', backref='certificates')

# ---------- 4.  CONTEXT PROCESSOR  ----------
@app.context_processor
def inject_globals():
    settings = Settings.query.first() or Settings()
    current_year = datetime.now().year
    unread_notifications = 0
    if 'user_id' in session and session.get('role') == 'parent':
        parent = Parent.query.filter_by(user_id=session['user_id']).first()
        if parent and parent.user_id:
            unread_notifications = Notification.query.filter_by(user_id=parent.user_id, is_read=False).count()
    return dict(
        datetime=datetime, now=datetime.now, timedelta=timedelta,
        settings=settings, Report=Report, Attendance=Attendance,
        Holiday=Holiday, Parent=Parent, current_year=current_year,
        unread_notifications=unread_notifications
    )

# ---------- 5.  HELPERS  ----------
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def require_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('يجب تسجيل الدخول أولاً', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def require_role(role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get('role') != role:
                flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator

def create_parent_username(full_name):
    # استخدام مسافات بدلاً من الشرطة السفلية
    username = full_name.strip()
    base_username = username
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username} {counter}"
        counter += 1
    return username

def create_student_username(full_name):
    username = full_name.strip()
    base_username = username
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username} {counter}"
        counter += 1
    return username

def get_or_create_parent(student_name, parent_phone):
    if not parent_phone:
        return None
    phone = re.sub(r'[^\d]', '', parent_phone)
    if not phone.startswith('7') or len(phone) != 9:
        return None
    
    # استخراج اسم ولي الأمر من اسم الطالب (الجزء الثاني والثالث)
    name_parts = student_name.strip().split()
    if len(name_parts) >= 2:
        parent_name = f"{name_parts[1]} {name_parts[2] if len(name_parts) > 2 else ''}".strip()
    else:
        parent_name = student_name
    
    # البحث عن ولي الأمر بالاسم أو رقم الهاتف
    parent = Parent.query.filter_by(name=parent_name).first()
    if parent:
        return parent
    
    parent = Parent.query.filter_by(phone=phone).first()
    if parent:
        return parent
    
    # إنشاء ولي أمر جديد
    parent = Parent(name=parent_name, phone=phone)
    db.session.add(parent)
    
    # إنشاء حساب مستخدم لولي الأمر
    username = create_parent_username(parent_name)
    user = User(username=username, password=generate_password_hash(phone), name=parent_name, role='parent')
    db.session.add(user)
    
    try:
        db.session.commit()
        # ربط Parent بـ User
        parent.user_id = user.id
        db.session.commit()
        return parent
    except Exception as e:
        db.session.rollback()
        print(f"Error creating parent: {e}")
        return None

def find_student_by_name(name, circle_id):
    name_clean = re.sub(r'[^\w\s]', '', name).strip().lower()
    students = Student.query.filter_by(circle_id=circle_id, is_active=True).all()
    for student in students:
        student_name_clean = re.sub(r'[^\w\s]', '', student.name).strip().lower()
        if student_name_clean == name_clean or name_clean in student_name_clean or student_name_clean in name_clean:
            return student
    return None

def improved_parse_collective_report(text, circle_id, date):
    reports, attendances = [], []
    lines = text.split('\n')
    current_date = datetime.strptime(date, '%Y-%m-%d').date()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        clean_line = re.sub(r'^[\d*🔹•\-#\s\.]+', '', line)
        attendance_status = None
        if any(k in line for k in ['✖️', 'غائب بعذر', 'مستأذن', 'غياب', 'غائب']):
            attendance_status = 'غائب بعذر'
        elif '❌' in line or 'غائب بلا عذر' in line:
            attendance_status = 'غائب بلا عذر'
        elif 'هروب' in line.lower() or '🏃' in line:
            attendance_status = 'هروب'
        elif 'لم يسمع' in line.lower():
            attendance_status = 'لم يسمع'
        elif 'متأخر' in line.lower():
            attendance_status = 'متأخر'
        if ':' in clean_line:
            name_part, recitation_part = clean_line.split(':', 1)
            student_name = name_part.strip()
            student = find_student_by_name(student_name, circle_id)
            if student:
                if attendance_status:
                    attendances.append(Attendance(student_id=student.id, date=current_date, status=attendance_status, notes='تم الإضافة من التقرير الجماعي'))
                recitation_clean = recitation_part.strip()
                if recitation_clean and not any(keyword in recitation_clean for keyword in ['✖️', '❌', 'هروب', 'لم يسمع', '🏃']):
                    pattern = r'([^\d\+]+?)\s*(\d+)\s*[-ـ]\s*(\d+)\s*([\+]?)'
                    match = re.search(pattern, recitation_clean)
                    if match:
                        surah = match.group(1).strip()
                        from_verse = int(match.group(2))
                        to_verse = int(match.group(3))
                        has_plus = match.group(4)
                        report_type = 'مراجعة' if (has_plus or 'مراجعة' in recitation_clean.lower() or '+' in recitation_clean) else 'حفظ'
                        grade = 'جيد'
                        if 'ممتاز' in recitation_clean:
                            grade = 'ممتاز'
                        elif 'جيد جدا' in recitation_clean:
                            grade = 'جيد جدا'
                        elif 'مقبول' in recitation_clean:
                            grade = 'مقبول'
                        reports.append({'student_id': student.id, 'surah': surah, 'from_verse': from_verse, 'to_verse': to_verse, 'type': report_type, 'grade': grade})
    return reports, attendances

def get_attendance_stats(student_id, start_date, end_date):
    attendances = Attendance.query.filter(Attendance.student_id == student_id, Attendance.date >= start_date, Attendance.date <= end_date).all()
    valid_attendances = [att for att in attendances if att.date.weekday() != 4]
    stats = {'حاضر': 0, 'غائب بعذر': 0, 'غائب بلا عذر': 0, 'هروب': 0, 'لم يسمع': 0, 'إجمالي الأيام': len(valid_attendances), 'نسبة الحضور': 0}
    for attendance in valid_attendances:
        if attendance.status in stats:
            stats[attendance.status] += 1
    if stats['إجمالي الأيام'] > 0:
        stats['نسبة الحضور'] = round((stats['حاضر'] / stats['إجمالي الأيام']) * 100, 2)
    return stats

def get_center_attendance_stats():
    students = Student.query.filter_by(is_active=True).all()
    total_attendance_rate = 0
    students_with_attendance = 0
    for student in students:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        stats = get_attendance_stats(student.id, start_date, end_date)
        if stats['إجمالي الأيام'] > 0:
            total_attendance_rate += stats['نسبة الحضور']
            students_with_attendance += 1
    return round(total_attendance_rate / students_with_attendance, 2) if students_with_attendance > 0 else 0

def get_student_stats(student_id):
    student = Student.query.get(student_id)
    if not student:
        return None
    end_date = datetime.now().date()
    start_date_monthly = end_date - timedelta(days=30)
    monthly_reports = Report.query.filter(Report.student_id == student_id, Report.date >= start_date_monthly, Report.date <= end_date).all()
    monthly_attendance = get_attendance_stats(student_id, start_date_monthly, end_date)
    total_reports = Report.query.filter_by(student_id=student_id).count()
    total_verses = sum(report.to_verse - report.from_verse + 1 for report in monthly_reports)
    return {
        'student': student,
        'monthly_reports': len(monthly_reports),
        'monthly_attendance': monthly_attendance,
        'total_reports': total_reports,
        'total_verses': total_verses,
        'attendance_rate': monthly_attendance['نسبة الحضور']
    }

def create_whatsapp_message(student, reports, report_type, start_date, end_date, teacher_name):
    if not student.parent_phone:
        return None
    phone = re.sub(r'[^\d]', '', student.parent_phone)
    if phone.startswith('967'):
        phone = phone[3:]
    settings = Settings.query.first() or Settings()
    reports_details = ""
    if reports:
        for report in reports:
            reports_details += f"• {report.surah} من الآية {report.from_verse} إلى الآية {report.to_verse} ({report.type}) - {report.grade}\n"
    else:
        reports_details = "لا يوجد تسميع في هذه الفترة\n"
    attendance_stats = get_attendance_stats(student.id, start_date, end_date)
    stats_text = f"• أيام الحضور: {attendance_stats['حاضر']}\n"
    stats_text += f"• أيام الغياب بعذر: {attendance_stats['غائب بعذر']}\n"
    stats_text += f"• أيام الغياب بلا عذر: {attendance_stats['غائب بلا عذر']}\n"
    stats_text += f"• أيام الهروب: {attendance_stats['هروب']}\n"
    stats_text += f"• إجمالي الأيام: {attendance_stats['إجمالي الأيام']}\n"
    stats_text += f"• نسبة الحضور: {attendance_stats['نسبة الحضور']}%"
    message = settings.whatsapp_message_template.format(
        report_type=report_type,
        student_name=student.name,
        circle_name=student.circle.name,
        teacher_name=teacher_name,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        reports_details=reports_details,
        attendance_stats=stats_text,
        site_name=settings.site_name
    )
    encoded_message = urllib.parse.quote(message)
    return f"https://wa.me/967{phone}?text={encoded_message}"

def send_bulk_reports(circle_id, report_type):
    circle = Circle.query.get(circle_id)
    if not circle:
        return 0, 0
    students = Student.query.filter_by(circle_id=circle_id, is_active=True).all()
    sent_count = error_count = 0
    if report_type == 'أسبوعي':
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
    else:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
    for student in students:
        if student.parent_phone:
            reports = Report.query.filter(Report.student_id == student.id, Report.date >= start_date, Report.date <= end_date).all()
            teacher_name = circle.teacher.name if circle.teacher else circle.teacher_name
            whatsapp_url = create_whatsapp_message(student, reports, report_type, start_date, end_date, teacher_name)
            if whatsapp_url:
                sent_count += 1
            else:
                error_count += 1
    return sent_count, error_count

def award_points(student_id, points, reason):
    point_entry = Point(student_id=student_id, points=points, reason=reason)
    db.session.add(point_entry)

def award_badge(student_id, badge_id):
    # Check if the student already has this badge
    existing = StudentBadge.query.filter_by(student_id=student_id, badge_id=badge_id).first()
    if not existing:
        student_badge = StudentBadge(student_id=student_id, badge_id=badge_id)
        db.session.add(student_badge)
        flash(f'تهانينا! لقد حصلت على شارة جديدة!', 'success')

def check_for_badges(student_id):
    student = Student.query.get(student_id)
    if not student:
        return

    # Badge 1: Excellent Reciter (10 'ممتاز' grades)
    excellent_reports = Report.query.filter_by(student_id=student_id, grade='ممتاز').count()
    if excellent_reports >= 10:
        award_badge(student_id, 1) # Assuming badge with id 1 is "Excellent Reciter"

    # Badge 2: Memorizer (500 verses memorized)
    if student.total_verses_since_year_start >= 500:
        award_badge(student_id, 2) # Assuming badge with id 2 is "Memorizer"

    # Badge 3: Perfect Attendance (30 consecutive days)
    thirty_days_ago = datetime.now().date() - timedelta(days=30)
    attendance_count = Attendance.query.filter(
        Attendance.student_id == student_id,
        Attendance.date >= thirty_days_ago,
        Attendance.status == 'حاضر'
    ).count()
    if attendance_count >= 30:
        award_badge(student_id, 3)

    # Badge 4: Course Graduate
    completed_courses = CourseEnrollment.query.join(Course).filter(
        CourseEnrollment.student_id == student_id,
        Course.is_active == False # Assuming inactive courses are completed
    ).count()
    if completed_courses > 0:
        award_badge(student_id, 4)

    # Badge 5: Top Student
    top_scores = TestScore.query.join(Test).filter(
        TestScore.student_id == student_id,
        (TestScore.score / Test.max_score) >= 0.9
    ).count()
    if top_scores > 0:
        award_badge(student_id, 5)

def seed_badges():
    if Badge.query.count() == 0:
        badges = [
            Badge(name='المتقن', description='الحصول على تقدير "ممتاز" 10 مرات', icon='fa-star'),
            Badge(name='الحافظ', description='حفظ 500 وجه منذ بداية العام', icon='fa-award'),
            Badge(name='الحاضر المثالي', description='الحضور لمدة 30 يومًا متتاليًا', icon='fa-calendar-check'),
            Badge(name='خريج الدورة', description='إكمال دورة تدريبية بنجاح', icon='fa-graduation-cap'),
            Badge(name='الطالب المتفوق', description='الحصول على درجة أعلى من 90% في اختبار', icon='fa-trophy')
        ]
        db.session.bulk_save_objects(badges)
        db.session.commit()

def compare_student_performance(student_id):
    today = datetime.now().date()
    # This week
    start_of_this_week = today - timedelta(days=today.weekday())
    end_of_this_week = start_of_this_week + timedelta(days=6)
    # Last week
    end_of_last_week = start_of_this_week - timedelta(days=1)
    start_of_last_week = end_of_last_week - timedelta(days=6)

    verses_this_week = db.session.query(func.sum(Report.to_verse - Report.from_verse + 1)).filter(
        Report.student_id == student_id,
        Report.type == 'حفظ',
        Report.date.between(start_of_this_week, end_of_this_week)
    ).scalar() or 0

    verses_last_week = db.session.query(func.sum(Report.to_verse - Report.from_verse + 1)).filter(
        Report.student_id == student_id,
        Report.type == 'حفظ',
        Report.date.between(start_of_last_week, end_of_last_week)
    ).scalar() or 0

    return verses_this_week, verses_last_week


def requires_approval():
    settings = Settings.query.first() or Settings()
    return settings.teacher_requires_approval

# ---------- 6.  ERROR HANDLERS  ----------
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403

# ---------- 7.  ROUTES  ----------
@app.route('/')
def index():
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(device in user_agent for device in ['mobile', 'android', 'iphone', 'ipad'])
    view_type = request.args.get('view', session.get('view_type', 'mobile' if is_mobile else 'desktop'))
    if view_type != 'auto':
        session['view_type'] = view_type
    if 'user_id' not in session:
        return render_template('guest_dashboard.html')
    if session.get('role') == 'parent':
        return redirect(url_for('parent_dashboard'))
    return redirect(url_for('dashboard'))

@app.route('/guest_dashboard')
def guest_dashboard():
    """لوحة تحكم للزوار (غير المسجلين)"""
    settings = Settings.query.first() or Settings()
    total_students = Student.query.filter_by(is_active=True).count()
    total_teachers = User.query.filter_by(role='teacher', is_active=True).count()
    total_circles = Circle.query.filter_by(is_active=True).count()
    total_reports = Report.query.count()
    
    # إحصائيات الحضور لهذا الأسبوع
    week_start = datetime.now().date() - timedelta(days=datetime.now().weekday())
    attendance_stats = db.session.query(Attendance.status, func.count(Attendance.id)).filter(Attendance.date >= week_start).group_by(Attendance.status).all()
    
    center_attendance_rate = get_center_attendance_stats()
    announcements = Announcement.query.filter_by(is_active=True).order_by(Announcement.date_posted.desc()).all()
    
    return render_template('guest_dashboard.html',
                         settings=settings,
                         total_students=total_students,
                         total_teachers=total_teachers,
                         total_circles=total_circles,
                         total_reports=total_reports,
                         attendance_stats=attendance_stats,
                         center_attendance_rate=center_attendance_rate,
                         announcements=announcements)

@app.route('/set_view/<view_type>')
@require_login
def set_view(view_type):
    if view_type in ['desktop', 'mobile', 'auto']:
        session['view_type'] = view_type
        flash(f'تم تغيير الواجهة إلى {view_type}', 'success')
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/toggle_dark_mode')
@require_login
def toggle_dark_mode():
    session['dark_mode'] = not session.get('dark_mode', False)
    flash('تم تغيير وضع التصفح', 'success')
    return redirect(request.referrer or url_for('index'))

@app.route('/set_academic_year/<year>')
@require_role('admin')
def set_academic_year(year):
    session['academic_year'] = year
    flash(f'تم تغيير السنة الدراسية إلى {year}', 'success')
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, is_active=True).first()
        if user and check_password_hash(user.password, password):
            login_entry = UserLogin(user_id=user.id, ip_address=request.remote_addr)
            db.session.add(login_entry)
            db.session.commit()
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['name'] = user.name
            flash('تم تسجيل الدخول بنجاح', 'success')
            if user.role == 'parent':
                return redirect(url_for('parent_dashboard'))
            elif user.role == 'student':
                return redirect(url_for('student_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    settings = Settings.query.first() or Settings()
    return render_template('login.html', settings=settings)

@app.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('index'))

@app.route('/parent_logout')
def parent_logout():
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@require_login
def dashboard():
    if session.get('role') == 'parent':
        return redirect(url_for('parent_dashboard'))
    
    total_students = Student.query.filter_by(is_active=True).count()
    total_teachers = User.query.filter_by(role='teacher', is_active=True).count()
    total_circles = Circle.query.filter_by(is_active=True).count()
    total_reports = Report.query.count()
    
    week_start = datetime.now().date() - timedelta(days=datetime.now().weekday())
    attendance_stats = db.session.query(Attendance.status, func.count(Attendance.id)).filter(Attendance.date >= week_start).group_by(Attendance.status).all()
    
    recent_reports = Report.query.order_by(Report.date.desc()).limit(10).all()
    new_students = Student.query.filter_by(is_active=True).order_by(Student.id.desc()).limit(5).all()
    center_attendance_rate = get_center_attendance_stats()
    active_circles = Circle.query.filter_by(is_active=True).all()
    announcements = Announcement.query.filter_by(is_active=True).order_by(Announcement.date_posted.desc()).all()
    
    return render_template('dashboard.html',
                         total_students=total_students,
                         total_teachers=total_teachers,
                         total_circles=total_circles,
                         total_reports=total_reports,
                         attendance_stats=attendance_stats,
                         recent_reports=recent_reports,
                         new_students=new_students,
                         center_attendance_rate=center_attendance_rate,
                         active_circles=active_circles,
                         announcements=announcements)

# ---------- 8.  STUDENTS ----------
@app.route('/students')
@require_login
def students():
    view_mode = request.args.get('view_mode', 'table')
    selected_circle = request.args.get('circle_id', type=int)
    search_query = request.args.get('search')
    
    query = Student.query.filter_by(is_active=True)

    # Teacher can only see his students
    if session['role'] == 'teacher':
        teacher_circles = [circle.id for circle in Circle.query.filter_by(teacher_id=session['user_id']).all()]
        query = query.filter(Student.circle_id.in_(teacher_circles))

    if selected_circle:
        query = query.filter_by(circle_id=selected_circle)
    
    if search_query:
        query = query.join(Parent, Student.parent_id == Parent.id, isouter=True).filter(
            or_(
                Student.name.ilike(f'%{search_query}%'),
                Student.student_phone.ilike(f'%{search_query}%'),
                Student.parent_phone.ilike(f'%{search_query}%'),
                Parent.name.ilike(f'%{search_query}%')
            )
        )

    students = query.all() or []
    circles = Circle.query.filter_by(is_active=True).all()
    
    return render_template('students.html', 
                         students=students, 
                         circles=circles, 
                         selected_circle=selected_circle, 
                         view_mode=view_mode)

@app.route('/add_student', methods=['GET', 'POST'])
@require_login
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form.get('age', type=int)
        student_phone = request.form.get('student_phone')
        parent_phone = request.form['parent_phone']
        circle_id = request.form['circle_id']
        photo = request.files.get('photo')
        
        filename = None
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        student = Student(
            name=name,
            age=age,
            student_phone=student_phone,
            parent_phone=parent_phone,
            circle_id=circle_id,
            photo=filename,
            current_address=request.form.get('current_address'),
            previous_address=request.form.get('previous_address'),
            governorate=request.form.get('governorate'),
            date_of_birth=datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d').date() if request.form.get('date_of_birth') else None,
            previous_memorization=request.form.get('previous_memorization'),
            enrollment_date=datetime.strptime(request.form['enrollment_date'], '%Y-%m-%d').date() if request.form.get('enrollment_date') else datetime.now().date(),
            pending_approval=requires_approval()
        )
        db.session.add(student)
        
        # إنشاء وربط ولي الأمر
        parent = get_or_create_parent(name, parent_phone)
        if parent:
            student.parent_id = parent.id
        
        # Create user account for student
        student_username = create_student_username(name)
        student_user = User(username=student_username, password=generate_password_hash(parent_phone), name=name, role='student')
        db.session.add(student_user)

        try:
            db.session.commit()
            flash('تم إضافة الطالب بنجاح', 'success')
            if requires_approval():
                flash('سيتم إرسال الطالب للمسؤول للموافقة عليه', 'info')
            return redirect(url_for('students'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة الطالب: {str(e)}', 'error')
    
    circles = Circle.query.filter_by(is_active=True).all()
    return render_template('add_student.html', circles=circles)

@app.route('/move_student/<int:student_id>', methods=['POST'])
@require_login
def move_student(student_id):
    student = Student.query.get_or_404(student_id)
    new_circle_id = request.form.get('new_circle_id')
    if new_circle_id:
        student.circle_id = new_circle_id
        db.session.commit()
        flash('تم نقل الطالب بنجاح!', 'success')
    else:
        flash('يرجى اختيار حلقة جديدة.', 'error')
    return redirect(url_for('edit_student', student_id=student_id))

@app.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
@require_login
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    if session['role'] == 'teacher':
        teacher_circles = [circle.id for circle in Circle.query.filter_by(teacher_id=session['user_id']).all()]
        if student.circle_id not in teacher_circles:
            flash('ليس لديك الصلاحية لتعديل هذا الطالب', 'error')
            return redirect(url_for('students'))

    if request.method == 'POST':
        student.name = request.form['name']
        student.age = request.form.get('age', type=int)
        student.student_phone = request.form.get('student_phone')
        student.parent_phone = request.form['parent_phone']
        student.circle_id = request.form['circle_id']
        student.current_address = request.form.get('current_address')
        student.previous_address = request.form.get('previous_address')
        student.governorate = request.form.get('governorate')
        student.date_of_birth = datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d').date() if request.form.get('date_of_birth') else None
        student.previous_memorization = request.form.get('previous_memorization')
        student.enrollment_date = datetime.strptime(request.form['enrollment_date'], '%Y-%m-%d').date() if request.form.get('enrollment_date') else student.enrollment_date

        photo = request.files.get('photo')
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            student.photo = filename
        
        try:
            db.session.commit()
            flash('تم تعديل بيانات الطالب بنجاح', 'success')
            return redirect(url_for('students'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تعديل الطالب: {str(e)}', 'error')
    
    circles = Circle.query.filter_by(is_active=True).all()
    return render_template('edit_student.html', student=student, circles=circles)

@app.route('/delete_student/<int:student_id>')
@require_login
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    if session['role'] == 'teacher':
        teacher_circles = [circle.id for circle in Circle.query.filter_by(teacher_id=session['user_id']).all()]
        if student.circle_id not in teacher_circles:
            flash('ليس لديك الصلاحية لحذف هذا الطالب', 'error')
            return redirect(url_for('students'))

    student.is_active = False
    db.session.commit()
    flash('تم حذف الطالب بنجاح', 'success')
    return redirect(url_for('students'))

@app.route('/approve_student/<int:student_id>')
@require_role('admin')
def approve_student(student_id):
    student = Student.query.get_or_404(student_id)
    student.pending_approval = False
    db.session.commit()
    flash('تمت الموافقة على الطالب بنجاح', 'success')
    return redirect(url_for('students'))

@app.route('/delayed_students')
@require_login
def delayed_students():
    today = datetime.now().date()
    query = Student.query.join(Attendance).filter(
        Attendance.status == 'متأخر',
        func.date(Attendance.date) == today
    )

    if session.get('role') == 'teacher':
        teacher_circles = [circle.id for circle in Circle.query.filter_by(teacher_id=session['user_id']).all()]
        query = query.filter(Student.circle_id.in_(teacher_circles))

    delayed_students = query.all()
    return render_template('delayed_students.html', students=delayed_students, today=today)

@app.route('/reject_student/<int:student_id>')
@require_role('admin')
def reject_student(student_id):
    student = Student.query.get_or_404(student_id)
    student.is_active = False
    db.session.commit()
    
    # إرسال إشعار لولي الأمر
    if student.parent and student.parent.user_id:
        notification = Notification(
            user_id=student.parent.user_id,
            title='رفض طالب',
            message=f'تم رفض طالب "{student.name}" من قبل المسؤول.'
        )
        db.session.add(notification)
        db.session.commit()
    
    flash('تم رفض الطالب وإشعار ولي الأمر', 'warning')
    return redirect(url_for('students'))

# ---------- 9.  CIRCLES ----------
@app.route('/circles')
@require_login
def circles():
    circles = Circle.query.filter_by(is_active=True).all()
    return render_template('circles.html', circles=circles)

@app.route('/add_circle', methods=['GET', 'POST'])
@require_login
def add_circle():
    if request.method == 'POST':
        name = request.form['name']
        teacher_id = request.form.get('teacher_id', type=int) or None
        teacher_name = request.form.get('teacher_name') or None
        category = request.form.get('category')
        
        circle = Circle(
            name=name,
            teacher_id=teacher_id,
            teacher_name=teacher_name,
            category=category,
            requires_approval=requires_approval()
        )
        db.session.add(circle)
        
        try:
            db.session.commit()
            flash('تم إضافة الحلقة بنجاح', 'success')
            if requires_approval():
                flash('سيتم إرسال الحلقة للمسؤول للموافقة عليها', 'info')
            return redirect(url_for('circles'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة الحلقة: {str(e)}', 'error')
    
    teachers = User.query.filter_by(role='teacher', is_active=True).all()
    return render_template('add_circle.html', teachers=teachers)

@app.route('/edit_circle/<int:circle_id>', methods=['GET', 'POST'])
@require_login
def edit_circle(circle_id):
    circle = Circle.query.get_or_404(circle_id)
    if request.method == 'POST':
        circle.name = request.form['name']
        circle.teacher_id = request.form.get('teacher_id', type=int) or None
        circle.teacher_name = request.form.get('teacher_name') or None
        circle.category = request.form.get('category')
        
        try:
            db.session.commit()
            flash('تم تعديل الحلقة بنجاح', 'success')
            return redirect(url_for('circles'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تعديل الحلقة: {str(e)}', 'error')
    
    teachers = User.query.filter_by(role='teacher', is_active=True).all()
    return render_template('edit_circle.html', circle=circle, teachers=teachers)

@app.route('/approve_circle/<int:circle_id>')
@require_role('admin')
def approve_circle(circle_id):
    circle = Circle.query.get_or_404(circle_id)
    circle.requires_approval = False
    db.session.commit()
    flash('تمت الموافقة على الحلقة بنجاح', 'success')
    return redirect(url_for('circles'))

def update_honor_board():
    today = datetime.now().date()
    current_month = today.month
    current_year = today.year

    # Delete old entries for the current month to avoid duplicates
    HonorBoard.query.filter_by(month=current_month, year=current_year).delete()

    # Get top 10 students based on points this month
    top_students = db.session.query(
        Student, func.sum(Point.points).label('total_points')
    ).join(Point).filter(
        func.extract('month', Point.date) == current_month,
        func.extract('year', Point.date) == current_year
    ).group_by(Student.id).order_by(func.sum(Point.points).desc()).limit(10).all()

    for i, (student, total_points) in enumerate(top_students):
        honor_entry = HonorBoard(
            student_id=student.id,
            month=current_month,
            year=current_year,
            rank=i + 1
        )
        db.session.add(honor_entry)

    db.session.commit()
    flash('تم تحديث لوحة الشرف بنجاح!', 'success')

@app.route('/honor_board')
@require_login
def honor_board():
    today = datetime.now().date()
    current_month = today.month
    current_year = today.year

    honor_students = HonorBoard.query.filter_by(month=current_month, year=current_year).order_by(HonorBoard.rank).all()

    return render_template('honor_board.html', honor_students=honor_students, month=current_month, year=current_year)

@app.route('/update_honor_board_manual')
@require_role('admin')
def update_honor_board_manual():
    update_honor_board()
    return redirect(url_for('honor_board'))

@app.route('/badges', methods=['GET', 'POST'])
@require_role('admin')
def badges():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        icon = request.form['icon']
        badge = Badge(name=name, description=description, icon=icon)
        db.session.add(badge)
        db.session.commit()
        flash('تمت إضافة الشارة بنجاح!', 'success')
        return redirect(url_for('badges'))

    all_badges = Badge.query.all()
    return render_template('badges.html', badges=all_badges)

@app.route('/reject_circle/<int:circle_id>')
@require_role('admin')
def reject_circle(circle_id):
    circle = Circle.query.get_or_404(circle_id)
    circle.is_active = False
    db.session.commit()
    
    # إرسال إشعار للمعلم
    if circle.teacher_id:
        notification = Notification(
            user_id=circle.teacher_id,
            title='رفض حلقة',
            message=f'تم رفض الحلقة "{circle.name}" من قبل المسؤول.'
        )
        db.session.add(notification)
        db.session.commit()
    
    flash('تم رفض الحلقة وإشعار المعلم', 'warning')
    return redirect(url_for('circles'))

# ---------- 10.  REPORTS ----------
@app.route('/reports')
@require_login
def reports():
    reports = Report.query.order_by(Report.date.desc()).all()
    return render_template('reports.html', reports=reports)

@app.route('/add_report', methods=['GET', 'POST'])
@require_login
def add_report():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        date_str = request.form.get('date')
        surah = request.form.get('surah')
        from_verse_str = request.form.get('from_verse')
        to_verse_str = request.form.get('to_verse')
        type_ = request.form.get('type')
        grade = request.form.get('grade')
        notes = request.form.get('notes')

        if not all([student_id, date_str, surah, from_verse_str, to_verse_str, type_, grade]):
            flash('يرجى ملء جميع الحقول المطلوبة.', 'error')
            return redirect(url_for('add_report'))

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            from_verse = int(from_verse_str)
            to_verse = int(to_verse_str)
        except (ValueError, TypeError):
            flash('تنسيق التاريخ أو أرقام الآيات غير صالح.', 'error')
            return redirect(url_for('add_report'))
        
        student = Student.query.get(student_id)
        if not student:
            flash('الطالب غير موجود', 'error')
            return redirect(url_for('add_report'))
        
        if session['role'] == 'teacher':
            teacher_circles = [circle.id for circle in Circle.query.filter_by(teacher_id=session['user_id']).all()]
            if student.circle_id not in teacher_circles:
                flash('ليس لديك الصلاحية لإضافة تقرير لهذا الطالب', 'error')
                return redirect(url_for('add_report'))

        report = Report(
            student_id=student_id,
            teacher_id=session['user_id'],
            circle_id=student.circle_id,
            date=date,
            surah=surah,
            from_verse=from_verse,
            to_verse=to_verse,
            type=type_,
            grade=grade,
            notes=notes
        )
        db.session.add(report)

        # Update last recitation date
        student.last_recitation_date = date
        
        # Update total verses
        if report.type == 'حفظ':
            student.total_verses_since_year_start += (to_verse - from_verse + 1)

        # Award points based on grade
        points_map = {'ممتاز': 10, 'جيد جدا': 7, 'جيد': 5, 'مقبول': 2}
        points_to_award = points_map.get(grade, 0)
        if points_to_award > 0:
            award_points(student.id, points_to_award, f'تقدير {grade} في تسميع سورة {surah}')

        try:
            db.session.commit()
            
            # Check for badges after committing points
            check_for_badges(student.id)
            db.session.commit()

            # إشعار لولي الأمر عند إضافة تقرير جديد
            if student.parent and student.parent.user_id:
                notification = Notification(
                    user_id=student.parent.user_id,
                    title='تقرير جديد',
                    message=f'تم إضافة تقرير جديد للطالب "{student.name}" بتاريخ {date}.'
                )
                db.session.add(notification)
                db.session.commit()
            
            flash('تم إضافة التقرير بنجاح', 'success')
            return redirect(url_for('reports'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة التقرير: {str(e)}', 'error')

    if session['role'] == 'teacher':
        teacher_circles = [circle.id for circle in Circle.query.filter_by(teacher_id=session['user_id']).all()]
        students = Student.query.filter(Student.circle_id.in_(teacher_circles), Student.is_active==True).all()
    else:
        students = Student.query.filter_by(is_active=True).all()

    return render_template('add_report.html', students=students)

@app.route('/collective_report', methods=['GET', 'POST'])
@require_login
def collective_report():
    if request.method == 'POST':
        circle_id = request.form['circle_id']
        date = request.form['date']
        report_text = request.form['report_text']
        
        reports, attendances = improved_parse_collective_report(report_text, circle_id, date)
        
        for rep in reports:
            student = Student.query.get(rep['student_id'])
            if student:
                report = Report(
                    student_id=rep['student_id'],
                    teacher_id=session['user_id'],
                    circle_id=circle_id,
                    date=datetime.strptime(date, '%Y-%m-%d').date(),
                    surah=rep['surah'],
                    from_verse=rep['from_verse'],
                    to_verse=rep['to_verse'],
                    type=rep['type'],
                    grade=rep['grade']
                )
                db.session.add(report)
        
        for att in attendances:
            db.session.add(att)
        
        try:
            db.session.commit()
            flash(f'تم رفع {len(reports)} تقرير وتحديث {len(attendances)} حضور', 'success')
            return redirect(url_for('reports'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء رفع التقرير الجماعي: {str(e)}', 'error')
    
    circles = Circle.query.filter_by(is_active=True).all()
    return render_template('collective_report.html', circles=circles)

@app.route('/edit_report/<int:report_id>', methods=['GET', 'POST'])
@require_login
def edit_report(report_id):
    report = Report.query.get_or_404(report_id)
    if request.method == 'POST':
        report.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        report.surah = request.form['surah']
        report.from_verse = int(request.form['from_verse'])
        report.to_verse = int(request.form['to_verse'])
        report.type = request.form['type']
        report.grade = request.form['grade']
        report.notes = request.form.get('notes')
        
        try:
            db.session.commit()
            flash('تم تعديل التقرير بنجاح', 'success')
            return redirect(url_for('reports'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تعديل التقرير: {str(e)}', 'error')
    
    return render_template('edit_report.html', report=report)

# ---------- 11.  ATTENDANCE ----------
@app.route('/attendance')
@require_login
def attendance():
    selected_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    selected_circle = request.args.get('circle_id', type=int)
    
    circles = Circle.query.filter_by(is_active=True).all()
    students = []
    
    if selected_circle:
        students = Student.query.filter_by(circle_id=selected_circle, is_active=True).all()
    
    attendance_data = {att.student_id: att for att in Attendance.query.filter_by(date=datetime.strptime(selected_date, '%Y-%m-%d').date()).all()}
    
    return render_template('attendance.html', 
                         students=students, 
                         circles=circles, 
                         selected_date=selected_date, 
                         selected_circle=selected_circle, 
                         attendance_data=attendance_data)

@app.route('/update_attendance', methods=['POST'])
@require_login
def update_attendance():
    date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
    circle_id = request.form.get('circle_id', type=int)
    
    students = Student.query.filter_by(circle_id=circle_id, is_active=True).all()
    
    for student in students:
        status = request.form.get(f'status_{student.id}', 'حاضر')
        notes = request.form.get(f'notes_{student.id}', '')
        
        attendance = Attendance.query.filter_by(student_id=student.id, date=date).first()
        if attendance:
            attendance.status = status
            attendance.notes = notes
        else:
            attendance = Attendance(student_id=student.id, date=date, status=status, notes=notes)
            db.session.add(attendance)
    
    try:
        db.session.commit()
        flash('تم تحديث الحضور بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء تحديث الحضور: {str(e)}', 'error')
    
    return redirect(url_for('attendance', date=date.strftime('%Y-%m-%d'), circle_id=circle_id))

# ---------- 12.  HOLIDAYS ----------
@app.route('/holidays')
@require_login
def holidays():
    holidays = Holiday.query.order_by(Holiday.date).all()
    return render_template('holidays.html', holidays=holidays)

@app.route('/add_holiday', methods=['GET', 'POST'])
@require_login
def add_holiday():
    if request.method == 'POST':
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        reason = request.form['reason']
        has_attendance = bool(request.form.get('has_attendance'))
        is_recurring = bool(request.form.get('is_recurring'))
        
        holiday = Holiday(
            date=date, 
            reason=reason, 
            has_attendance=has_attendance, 
            is_recurring=is_recurring, 
            teacher_id=session['user_id']
        )
        db.session.add(holiday)
        
        try:
            db.session.commit()
            flash('تم إضافة العطلة بنجاح', 'success')
            return redirect(url_for('holidays'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة العطلة: {str(e)}', 'error')
    
    return render_template('add_holiday.html')

@app.route('/delete_holiday/<int:holiday_id>')
@require_login
def delete_holiday(holiday_id):
    holiday = Holiday.query.get_or_404(holiday_id)
    db.session.delete(holiday)
    db.session.commit()
    flash('تم حذف العطلة بنجاح', 'success')
    return redirect(url_for('holidays'))

# ---------- 13.  PARENTS ----------
@app.route('/parents')
@require_role('admin')
def parents():
    parents = Parent.query.all()
    total_linked_students = Student.query.filter(Student.parent_id.isnot(None)).count()
    return render_template('parents.html', parents=parents, total_linked_students=total_linked_students)

@app.route('/add_parents', methods=['GET', 'POST'])
@require_role('admin')
def add_parents():
    if request.method == 'POST':
        parents_text = request.form['parents_text']
        lines = parents_text.split('\n')
        created_count = 0
        
        for line in lines:
            line = line.strip()
            if ':' in line:
                name, phone = line.split(':', 1)
                name = name.strip()
                phone = re.sub(r'[^\d]', '', phone.strip())
                
                if phone.startswith('7') and len(phone) == 9:
                    # التحقق من عدم وجود ولي أمر بنفس الاسم أو رقم الهاتف
                    existing_parent = Parent.query.filter((Parent.name == name) | (Parent.phone == phone)).first()
                    if not existing_parent:
                        parent = Parent(name=name, phone=phone)
                        db.session.add(parent)
                        
                        # إنشاء حساب مستخدم
                        username = name.replace(' ', ' ')  # استخدام مسافات بدلاً من الشرطة السفلية
                        user = User(
                            username=username, 
                            password=generate_password_hash(phone), 
                            name=name, 
                            role='parent'
                        )
                        db.session.add(user)
                        created_count += 1
        
        try:
            db.session.commit()
            
            # ربط أولياء الأمور بحساباتهم
            parents = Parent.query.filter(Parent.user_id.is_(None)).all()
            for parent in parents:
                user = User.query.filter_by(name=parent.name, role='parent').first()
                if user:
                    parent.user_id = user.id
            
            db.session.commit()
            flash(f'تم إضافة {created_count} من أولياء الأمور بنجاح', 'success')
            return redirect(url_for('parents'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة أولياء الأمور: {str(e)}', 'error')
    
    return render_template('add_parents.html')

@app.route('/link_students_to_parents', methods=['GET', 'POST'])
@require_role('admin')
def link_students_to_parents():
    if request.method == 'POST':
        student_id = request.form['student_id']
        parent_id = request.form['parent_id']
        
        student = Student.query.get(student_id)
        parent = Parent.query.get(parent_id)
        
        if student and parent:
            student.parent_id = parent.id
            db.session.commit()
            flash('تم ربط الطالب بولي الأمر بنجاح', 'success')
            return redirect(url_for('link_students_to_parents'))
        else:
            flash('الطالب أو ولي الأمر غير موجود', 'error')
    
    students = Student.query.filter_by(parent_id=None, is_active=True).all()
    parents = Parent.query.all()
    return render_template('link_students_to_parents.html', students=students, parents=parents)

# ---------- 14.  USERS ----------
@app.route('/users')
@require_role('admin')
def users():
    users = User.query.filter(User.role.in_(['admin', 'teacher', 'support'])).all()
    return render_template('users.html', users=users)

@app.route('/student_accounts')
@require_role('admin')
def student_accounts():
    students = User.query.filter_by(role='student').all()
    return render_template('student_accounts.html', students=students)

@app.route('/add_user', methods=['GET', 'POST'])
@require_role('admin')
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        name = request.form['name']
        role = request.form['role']
        email = request.form.get('email')
        
        user = User(username=username, password=password, name=name, role=role, email=email)
        db.session.add(user)
        
        try:
            db.session.commit()
            flash('تم إضافة المستخدم بنجاح', 'success')
            return redirect(url_for('users'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة المستخدم: {str(e)}', 'error')
    
    return render_template('add_user.html')

@app.route('/announcements', methods=['GET', 'POST'])
@require_role('admin')
def announcements():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image = request.files.get('image')

        filename = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        announcement = Announcement(title=title, content=content, image=filename)
        db.session.add(announcement)
        db.session.commit()

        # إرسال إشعارات لأولياء الأمور
        parents = Parent.query.filter(Parent.user_id.isnot(None)).all()
        for parent in parents:
            notification = Notification(
                user_id=parent.user_id,
                title='إعلان جديد',
                message=f'إعلان جديد بعنوان: "{title}"'
            )
            db.session.add(notification)

        db.session.commit()
        flash('تم إضافة الإعلان بنجاح وإرسال الإشعارات!', 'success')
        return redirect(url_for('announcements'))

    all_announcements = Announcement.query.all()
    return render_template('announcements.html', announcements=all_announcements)

@app.route('/api/fingerprint_login', methods=['POST'])
def fingerprint_login():
    fingerprint_id = request.json.get('fingerprint_id')
    if not fingerprint_id:
        return jsonify({'success': False, 'message': 'لم يتم توفير معرف البصمة'}), 400

    user = User.query.filter_by(fingerprint_id=fingerprint_id).first()
    if user:
        # In a real application, you would handle session creation here
        login_entry = UserLogin(user_id=user.id, ip_address=request.remote_addr)
        db.session.add(login_entry)
        db.session.commit()
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        session['name'] = user.name
        return jsonify({'success': True, 'message': f'أهلاً بك يا {user.name}!'})
    else:
        return jsonify({'success': False, 'message': 'البصمة غير مسجلة'}), 404

@app.route('/api/student_details/<int:student_id>')
@require_login
def api_student_details(student_id):
    student = Student.query.get_or_404(student_id)
    reports = Report.query.filter_by(student_id=student_id).order_by(Report.date.desc()).all()

    student_data = {
        'name': student.name,
        'age': student.age,
        'circle': student.circle.name,
        'teacher': student.circle.teacher.name if student.circle.teacher else student.circle.teacher_name,
        'current_address': student.current_address,
        'previous_address': student.previous_address,
        'governorate': student.governorate,
        'date_of_birth': student.date_of_birth.strftime('%Y-%m-%d') if student.date_of_birth else None,
        'previous_memorization': student.previous_memorization,
        'enrollment_date': student.enrollment_date.strftime('%Y-%m-%d') if student.enrollment_date else None,
        'reports': [{
            'date': report.date.strftime('%Y-%m-%d'),
            'surah': report.surah,
            'from_verse': report.from_verse,
            'to_verse': report.to_verse,
            'type': report.type,
            'grade': report.grade
        } for report in reports]
    }
    return jsonify(student_data)

@app.route('/user_logins')
@require_role('admin')
def user_logins():
    logins = UserLogin.query.order_by(UserLogin.login_time.desc()).all()
    return render_template('user_logins.html', logins=logins)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@require_role('admin')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.name = request.form['name']
        user.role = request.form['role']
        user.email = request.form.get('email')
        new_password = request.form.get('password')
        
        if new_password:
            user.password = generate_password_hash(new_password)
        
        try:
            db.session.commit()
            flash('تم تعديل المستخدم بنجاح', 'success')
            return redirect(url_for('users'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تعديل المستخدم: {str(e)}', 'error')
    
    return render_template('edit_user.html', user=user)

# ---------- 15.  SETTINGS ----------
@app.route('/settings', methods=['GET', 'POST'])
@require_role('admin')
def settings():
    settings_obj = Settings.query.first() or Settings()
    
    if request.method == 'POST':
        settings_obj.site_name = request.form['site_name']
        settings_obj.site_description = request.form['site_description']
        settings_obj.contact_phone = request.form.get('contact_phone')
        settings_obj.contact_email = request.form.get('contact_email')
        settings_obj.location_address = request.form.get('location_address', 'مأرب - شارع الأربعين - خلف مستشفى نيوم')
        settings_obj.location_map_url = request.form.get('location_map_url')
        settings_obj.primary_color = request.form['primary_color']
        settings_obj.secondary_color = request.form['secondary_color']
        settings_obj.support_bank_accounts = request.form['support_bank_accounts']
        settings_obj.support_message = request.form.get('support_message', 'نورٌ نُهديه وجيل نربيه')
        settings_obj.whatsapp_message_template = request.form['whatsapp_message_template']
        settings_obj.teacher_requires_approval = bool(request.form.get('teacher_requires_approval'))
        settings_obj.allow_custom_teacher_name = bool(request.form.get('allow_custom_teacher_name'))
        settings_obj.dark_mode_enabled = bool(request.form.get('dark_mode_enabled'))
        settings_obj.developer_name = request.form.get('developer_name', 'Your Name')
        settings_obj.developer_link = request.form.get('developer_link', 'https://www.linkedin.com/in/your-linkedin-profile')
        
        logo = request.files.get('logo')
        if logo and allowed_file(logo.filename):
            filename = secure_filename(logo.filename)
            logo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            settings_obj.logo = filename
        
        try:
            db.session.commit()
            flash('تم حفظ الإعدادات بنجاح', 'success')
            return redirect(url_for('settings'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء حفظ الإعدادات: {str(e)}', 'error')
    
    # إحصائيات النظام
    user_count = User.query.count()
    circle_count = Circle.query.filter_by(is_active=True).count()
    student_count = Student.query.filter_by(is_active=True).count()
    report_count = Report.query.count()
    teacher_count = User.query.filter_by(role='teacher').count()
    support_count = User.query.filter_by(role='support').count()
    parent_count = Parent.query.count()
    weekly_reports_count = Report.query.filter(Report.date >= datetime.now().date() - timedelta(days=7)).count()
    attendance_count = Attendance.query.count()
    holiday_count = Holiday.query.count()
    students_without_parents = Student.query.filter_by(parent_id=None).count()
    
    return render_template('settings.html',
                         settings=settings_obj,
                         user_count=user_count,
                         circle_count=circle_count,
                         student_count=student_count,
                         report_count=report_count,
                         teacher_count=teacher_count,
                         support_count=support_count,
                         parent_count=parent_count,
                         weekly_reports_count=weekly_reports_count,
                         attendance_count=attendance_count,
                         holiday_count=holiday_count,
                         students_without_parents=students_without_parents)

@app.route('/delete_logo')
@require_role('admin')
def delete_logo():
    settings_obj = Settings.query.first()
    if settings_obj and settings_obj.logo:
        try:
            # حذف ملف الشعار
            logo_path = os.path.join(app.config['UPLOAD_FOLDER'], settings_obj.logo)
            if os.path.exists(logo_path):
                os.remove(logo_path)
            
            # حذف المرجع من قاعدة البيانات
            settings_obj.logo = None
            db.session.commit()
            flash('تم حذف الشعار بنجاح', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء حذف الشعار: {str(e)}', 'error')
    
    return redirect(url_for('settings'))

# ---------- 16.  SUPPORT ----------
@app.route('/support')
def support():
    settings_obj = Settings.query.first() or Settings()
    return render_template('support.html', settings=settings_obj)

# ---------- 17.  NOTIFICATIONS ----------
@app.route('/notifications')
@require_login
def notifications():
    if session.get('role') != 'parent':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))
    
    parent = Parent.query.filter_by(user_id=session['user_id']).first()
    if parent and parent.user_id:
        # Mark all unread notifications as read
        unread_notifs = Notification.query.filter_by(user_id=parent.user_id, is_read=False).all()
        for notif in unread_notifs:
            notif.is_read = True
        db.session.commit()

        notifs = Notification.query.filter_by(user_id=parent.user_id).order_by(Notification.created_at.desc()).all()
        return render_template('notifications.html', notifications=notifs)
    
    flash('لم يتم العثور على بيانات ولي الأمر', 'error')
    return redirect(url_for('dashboard'))

# ---------- 18.  WHATSAPP ----------
@app.route('/send_whatsapp_report/<int:student_id>/<report_type>')
@require_login
def send_whatsapp_report(student_id, report_type):
    student = Student.query.get_or_404(student_id)
    
    if report_type == 'أسبوعي':
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
    else:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
    
    reports = Report.query.filter(Report.student_id == student_id, Report.date >= start_date, Report.date <= end_date).all()
    teacher_name = student.circle.teacher.name if student.circle.teacher else student.circle.teacher_name
    
    whatsapp_url = create_whatsapp_message(student, reports, report_type, start_date, end_date, teacher_name)
    
    if whatsapp_url:
        return redirect(whatsapp_url)
    else:
        flash('لا يوجد رقم هاتف لولي الأمر', 'error')
        return redirect(request.referrer or url_for('student_reports', student_id=student_id))

@app.route('/send_bulk_reports_route/<int:circle_id>/<report_type>')
@require_login
def send_bulk_reports_route(circle_id, report_type):
    sent, errors = send_bulk_reports(circle_id, report_type)
    flash(f'تم إرسال {sent} رسالة وحدث خطأ في {errors}', 'success' if errors == 0 else 'warning')
    return redirect(url_for('circles'))

# ---------- 19.  UPLOADED FILES ----------
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ---------- 20.  PARENT DASHBOARD ----------
@app.route('/parent_dashboard')
@require_login
def parent_dashboard():
    if session.get('role') != 'parent':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))
    
    parent = Parent.query.filter_by(user_id=session['user_id']).first()
    if not parent:
        flash('لم يتم العثور على بيانات ولي الأمر', 'error')
        return redirect(url_for('logout'))
    
    students = Student.query.filter_by(parent_id=parent.id, is_active=True).all()
    student_stats = []
    
    for student in students:
        stats = get_student_stats(student.id)
        if stats:
            # Add gamification and educational notes data
            stats['points'] = db.session.query(func.sum(Point.points)).filter_by(student_id=student.id).scalar() or 0
            stats['badges'] = StudentBadge.query.filter_by(student_id=student.id).all()
            stats['notes'] = EducationalNote.query.filter_by(student_id=student.id).order_by(EducationalNote.date.desc()).limit(3).all()
            student_stats.append(stats)
    
    total_children = len(students)
    total_attendance_rate = 0
    total_monthly_reports = 0
    
    for stats in student_stats:
        total_attendance_rate += stats['attendance_rate']
        total_monthly_reports += stats['monthly_reports']
    
    if student_stats:
        total_attendance_rate = total_attendance_rate / len(student_stats)
    
    # Honor board
    honor_students = HonorBoard.query.filter_by(month=datetime.now().month, year=datetime.now().year).order_by(HonorBoard.rank).limit(5).all()

    # Announcements
    announcements = Announcement.query.filter_by(is_active=True).order_by(Announcement.date_posted.desc()).all()

    # Center stats
    center_stats = {
        'total_students': Student.query.filter_by(is_active=True).count(),
        'average_attendance': get_center_attendance_stats(),
        'total_verses_this_month': Report.query.filter(Report.date >= datetime.now().date() - timedelta(days=30)).count()
    }
    
    return render_template('parent_dashboard.html', 
                         parent=parent, 
                         student_stats=student_stats,
                         total_children=total_children,
                         total_attendance_rate=total_attendance_rate,
                         total_monthly_reports=total_monthly_reports,
                         center_stats=center_stats,
                         honor_students=honor_students,
                         announcements=announcements)

# ---------- 21.  STUDENT REPORTS ----------
@app.route('/add_educational_note/<int:student_id>', methods=['POST'])
@require_login
def add_educational_note(student_id):
    if session.get('role') not in ['admin', 'teacher']:
        flash('ليس لديك صلاحية للقيام بهذا الإجراء', 'error')
        return redirect(request.referrer)

    student = Student.query.get_or_404(student_id)
    note_text = request.form.get('note')

    if note_text:
        note = EducationalNote(
            student_id=student_id,
            teacher_id=session['user_id'],
            note=note_text
        )
        db.session.add(note)

        # Send notification to parent
        if student.parent and student.parent.user_id:
            notification = Notification(
                user_id=student.parent.user_id,
                title='ملاحظة تربوية جديدة',
                message=f'أضاف المعلم ملاحظة تربوية جديدة لابنك "{student.name}".'
            )
            db.session.add(notification)

        db.session.commit()
        flash('تمت إضافة الملاحظة بنجاح!', 'success')
    else:
        flash('نص الملاحظة لا يمكن أن يكون فارغًا.', 'error')

    return redirect(url_for('student_reports', student_id=student_id))

@app.route('/student_reports/<int:student_id>')
@require_login
def student_reports(student_id):
    student = Student.query.get_or_404(student_id)
    
    # Teacher can only see his students
    if session.get('role') == 'teacher':
        teacher_circles = [circle.id for circle in Circle.query.filter_by(teacher_id=session['user_id']).all()]
        if student.circle_id not in teacher_circles:
            flash('ليس لديك الصلاحية لعرض تقارير هذا الطالب', 'error')
            return redirect(url_for('students'))

    end_date_weekly = datetime.now().date()
    start_date_weekly = end_date_weekly - timedelta(days=7)
    end_date_monthly = datetime.now().date()
    start_date_monthly = end_date_monthly - timedelta(days=30)
    
    weekly_reports = Report.query.filter(Report.student_id == student_id, Report.date >= start_date_weekly, Report.date <= end_date_weekly).all()
    monthly_reports = Report.query.filter(Report.student_id == student_id, Report.date >= start_date_monthly, Report.date <= end_date_monthly).all()
    
    verses_this_week, verses_last_week = compare_student_performance(student_id)

    total_verses_in_quran = 6236
    progress_percentage = (student.total_verses_since_year_start / total_verses_in_quran) * 100

    return render_template('student_reports.html',
                         student=student,
                         weekly_reports=weekly_reports,
                         monthly_reports=monthly_reports,
                         start_date_weekly=start_date_weekly,
                         end_date_weekly=end_date_weekly,
                         start_date_monthly=start_date_monthly,
                         end_date_monthly=end_date_monthly,
                         verses_this_week=verses_this_week,
                         verses_last_week=verses_last_week,
                         progress_percentage=progress_percentage)

@app.route('/export_student_report/<int:student_id>')
@require_login
def export_student_report(student_id):
    student = Student.query.get_or_404(student_id)
    reports = Report.query.filter_by(student_id=student_id).order_by(Report.date.desc()).all()

    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('NotoNaskhArabic', '', 'NotoNaskhArabic-Regular.ttf', uni=True)
    pdf.set_font('NotoNaskhArabic', '', 12)

    pdf.cell(0, 10, f'تقرير الطالب: {student.name}', 0, 1, 'C')

    for report in reports:
        pdf.cell(0, 10, f"التاريخ: {report.date.strftime('%Y-%m-%d')}", 0, 1)
        pdf.cell(0, 10, f"السورة: {report.surah}", 0, 1)
        pdf.cell(0, 10, f"من الآية {report.from_verse} إلى {report.to_verse}", 0, 1)
        pdf.cell(0, 10, f"النوع: {report.type}", 0, 1)
        pdf.cell(0, 10, f"التقدير: {report.grade}", 0, 1)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())

    response = make_response(pdf.output(dest='S').encode('latin-1'))
    response.headers.set('Content-Disposition', 'attachment', filename=f'report_{student.name}.pdf')
    response.headers.set('Content-Type', 'application/pdf')
    return response

# ---------- 22.  COURSES AND TESTS ----------
@app.route('/courses')
@require_role('admin')
def courses():
    courses_list = Course.query.order_by(Course.created_at.desc()).all()
    return render_template('courses.html', courses=courses_list)

@app.route('/add_course', methods=['GET', 'POST'])
@require_role('admin')
def add_course():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        teacher_id = request.form.get('teacher_id') if session['role'] == 'admin' else session['user_id']

        new_course = Course(
            name=name,
            description=description,
            teacher_id=teacher_id
        )
        db.session.add(new_course)
        try:
            db.session.commit()
            flash('تم إنشاء الدورة بنجاح!', 'success')
            return redirect(url_for('courses'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إنشاء الدورة: {e}', 'error')

    teachers = User.query.filter_by(role='teacher', is_active=True).all()
    return render_template('add_course.html', teachers=teachers)

@app.route('/edit_course/<int:course_id>', methods=['GET', 'POST'])
@require_role('admin')
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)

    if request.method == 'POST':
        course.name = request.form.get('name')
        course.description = request.form.get('description')
        if session['role'] == 'admin':
            course.teacher_id = request.form.get('teacher_id')
        course.is_active = 'is_active' in request.form

        try:
            db.session.commit()
            flash('تم تحديث الدورة بنجاح!', 'success')
            return redirect(url_for('courses'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تحديث الدورة: {e}', 'error')

    teachers = User.query.filter_by(role='teacher', is_active=True).all()
    return render_template('edit_course.html', course=course, teachers=teachers)

@app.route('/delete_course/<int:course_id>')
@require_role('admin')
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)

    try:
        # This will also delete related enrollments and tests due to cascading
        db.session.delete(course)
        db.session.commit()
        flash('تم حذف الدورة بنجاح.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف الدورة: {e}', 'error')

    return redirect(url_for('courses'))

@app.route('/course/<int:course_id>')
@require_role('admin')
def course_details(course_id):
    course = Course.query.get_or_404(course_id)

    enrolled_students = Student.query.join(CourseEnrollment).filter(CourseEnrollment.course_id == course.id).all()

    # Students not yet enrolled in this course
    enrolled_student_ids = [s.id for s in enrolled_students]
    available_students = Student.query.filter(Student.id.notin_(enrolled_student_ids), Student.is_active==True).all()

    return render_template('course_details.html', course=course, enrolled_students=enrolled_students, available_students=available_students)

@app.route('/enroll_student/<int:course_id>', methods=['POST'])
@require_role('admin')
def enroll_student(course_id):
    course = Course.query.get_or_404(course_id)

    student_ids = request.form.getlist('student_ids')
    if not student_ids:
        flash('لم يتم تحديد أي طالب.', 'warning')
        return redirect(url_for('course_details', course_id=course_id))

    for student_id in student_ids:
        # Check if already enrolled
        is_enrolled = CourseEnrollment.query.filter_by(course_id=course_id, student_id=student_id).first()
        if not is_enrolled:
            enrollment = CourseEnrollment(course_id=course_id, student_id=student_id)
            db.session.add(enrollment)

    try:
        db.session.commit()
        flash(f'تم تسجيل {len(student_ids)} طالب بنجاح!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء تسجيل الطلاب: {e}', 'error')

    return redirect(url_for('course_details', course_id=course_id))

@app.route('/unenroll_student/<int:course_id>/<int:student_id>')
@require_role('admin')
def unenroll_student(course_id, student_id):
    enrollment = CourseEnrollment.query.filter_by(course_id=course_id, student_id=student_id).first_or_404()
    course = enrollment.course

    try:
        db.session.delete(enrollment)
        db.session.commit()
        flash('تم إلغاء تسجيل الطالب بنجاح.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء إلغاء التسجيل: {e}', 'error')

    return redirect(url_for('course_details', course_id=course_id))

@app.route('/course/<int:course_id>/tests')
@require_role('admin')
def manage_tests(course_id):
    course = Course.query.get_or_404(course_id)

    return render_template('manage_tests.html', course=course)

@app.route('/add_test/<int:course_id>', methods=['POST'])
@require_role('admin')
def add_test(course_id):
    course = Course.query.get_or_404(course_id)

    name = request.form.get('name')
    test_date = datetime.strptime(request.form.get('test_date'), '%Y-%m-%d')
    max_score = float(request.form.get('max_score'))

    new_test = Test(name=name, course_id=course.id, test_date=test_date, max_score=max_score)
    db.session.add(new_test)
    try:
        db.session.commit()
        flash('تم إضافة الاختبار بنجاح!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء إضافة الاختبار: {e}', 'error')

    return redirect(url_for('manage_tests', course_id=course_id))

@app.route('/edit_test/<int:test_id>', methods=['POST'])
@require_role('admin')
def edit_test(test_id):
    test = Test.query.get_or_404(test_id)

    test.name = request.form.get('name')
    test.test_date = datetime.strptime(request.form.get('test_date'), '%Y-%m-%d')
    test.max_score = float(request.form.get('max_score'))

    try:
        db.session.commit()
        flash('تم تعديل الاختبار بنجاح!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء تعديل الاختبار: {e}', 'error')

    return redirect(url_for('manage_tests', course_id=test.course_id))

@app.route('/delete_test/<int:test_id>')
@require_role('admin')
def delete_test(test_id):
    test = Test.query.get_or_404(test_id)
    course_id = test.course_id

    try:
        db.session.delete(test)
        db.session.commit()
        flash('تم حذف الاختبار بنجاح.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف الاختبار: {e}', 'error')

    return redirect(url_for('manage_tests', course_id=course_id))

@app.route('/record_scores/<int:test_id>', methods=['GET', 'POST'])
@require_role('admin')
def record_scores(test_id):
    test = Test.query.get_or_404(test_id)

    if request.method == 'POST':
        for student in test.course.enrollments:
            score_val = request.form.get(f'score_{student.student.id}')
            if score_val:
                # Check for existing score
                existing_score = TestScore.query.filter_by(test_id=test.id, student_id=student.student.id).first()
                if existing_score:
                    existing_score.score = float(score_val)
                else:
                    new_score = TestScore(
                        test_id=test.id,
                        student_id=student.student.id,
                        score=float(score_val),
                        recorded_by_id=session['user_id']
                    )
                    db.session.add(new_score)
        try:
            db.session.commit()
            flash('تم حفظ الدرجات بنجاح!', 'success')
            return redirect(url_for('manage_tests', course_id=test.course_id))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء حفظ الدرجات: {e}', 'error')

    # Get existing scores to populate the form
    existing_scores = {score.student_id: score for score in test.scores}
    return render_template('record_scores.html', test=test, existing_scores=existing_scores)

# ---------- 22.  PARENT STUDENT DETAILS ----------
@app.route('/student_dashboard')
@require_login
def student_dashboard():
    if session.get('role') != 'student':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))

    user = User.query.get(session['user_id'])
    student = Student.query.filter_by(name=user.name).first()
    if not student:
        flash('لم يتم العثور على بيانات الطالب', 'error')
        return redirect(url_for('logout'))

    return redirect(url_for('student_details', student_id=student.id))

@app.route('/student_details/<int:student_id>')
@require_login
def student_details(student_id):
    student = Student.query.get_or_404(student_id)
    
    # Authorization check
    if session['role'] == 'parent':
        parent = Parent.query.filter_by(user_id=session['user_id']).first()
        if not parent or student.parent_id != parent.id:
            flash('ليس لديك صلاحية لعرض تفاصيل هذا الطالب', 'error')
            return redirect(url_for('parent_dashboard'))
    elif session['role'] == 'student':
        if student.name != session['name']:
            flash('ليس لديك صلاحية لعرض تفاصيل هذا الطالب', 'error')
            return redirect(url_for('student_dashboard'))
    elif session['role'] == 'teacher':
        teacher_circles = [circle.id for circle in Circle.query.filter_by(teacher_id=session['user_id']).all()]
        if student.circle_id not in teacher_circles:
            flash('ليس لديك صلاحية لعرض تفاصيل هذا الطالب', 'error')
            return redirect(url_for('dashboard'))

    stats = get_student_stats(student_id)
    recent_reports = Report.query.filter_by(student_id=student_id).order_by(Report.date.desc()).limit(10).all()
    recent_attendance = Attendance.query.filter_by(student_id=student_id).order_by(Attendance.date.desc()).limit(10).all()
    
    # إحصائيات الحلقة
    circle_stats = {
        'total_students': Student.query.filter_by(circle_id=student.circle_id, is_active=True).count(),
        'average_attendance': 0,
        'average_verses': 0
    }
    
    circle_students = Student.query.filter_by(circle_id=student.circle_id, is_active=True).all()
    total_attendance = 0
    total_verses = 0
    students_with_stats = 0
    
    for circle_student in circle_students:
        student_stats = get_student_stats(circle_student.id)
        if student_stats:
            total_attendance += student_stats['attendance_rate']
            total_verses += student_stats['total_verses']
            students_with_stats += 1
    
    if students_with_stats > 0:
        circle_stats['average_attendance'] = total_attendance / students_with_stats
        circle_stats['average_verses'] = total_verses / students_with_stats
    
    total_verses_in_quran = 6236
    progress_percentage = (student.total_verses_since_year_start / total_verses_in_quran) * 100

    educational_notes = EducationalNote.query.filter_by(student_id=student_id).order_by(EducationalNote.date.desc()).all()

    return render_template('student_details.html',
                         student=student,
                         stats=stats,
                         recent_reports=recent_reports,
                         recent_attendance=recent_attendance,
                         circle_stats=circle_stats,
                         progress_percentage=progress_percentage,
                         educational_notes=educational_notes)

@app.route('/grades', methods=['GET', 'POST'])
@require_login
def grades():
    if request.method == 'POST':
        test_id = request.form.get('test_id')
        student_id = request.form.get('student_id')
        score = request.form.get('score')

        if not all([test_id, student_id, score]):
            flash('يرجى ملء جميع الحقول المطلوبة.', 'error')
            return redirect(url_for('grades'))

        try:
            score = float(score)
        except ValueError:
            flash('الدرجة يجب أن تكون رقمًا.', 'error')
            return redirect(url_for('grades'))

        test_score = TestScore(
            test_id=test_id,
            student_id=student_id,
            score=score,
            recorded_by_id=session['user_id']
        )
        db.session.add(test_score)
        db.session.commit()
        flash('تم حفظ الدرجة بنجاح.', 'success')
        return redirect(url_for('grades'))

    tests = Test.query.all()
    students = Student.query.all()
    return render_template('grades.html', tests=tests, students=students)

@app.route('/certificates', methods=['GET', 'POST'])
@require_role('admin')
def certificates():
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        student_id = request.form.get('student_id')

        if not all([course_id, student_id]):
            flash('يرجى ملء جميع الحقول المطلوبة.', 'error')
            return redirect(url_for('certificates'))

        student = Student.query.get(student_id)
        course = Course.query.get(course_id)

        # Create PDF certificate
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Certificate of Completion', 1, 1, 'C')
        pdf.cell(0, 10, f'This is to certify that {student.name} has successfully completed the course:', 0, 1, 'C')
        pdf.cell(0, 10, course.name, 0, 1, 'C')

        certificate_filename = f"certificate_{student.id}_{course.id}.pdf"
        certificate_path = os.path.join(app.config['UPLOAD_FOLDER'], certificate_filename)
        pdf.output(certificate_path)

        certificate = Certificate(
            student_id=student_id,
            course_id=course_id,
            certificate_file=certificate_filename
        )
        db.session.add(certificate)
        db.session.commit()
        flash('تم إنشاء الشهادة بنجاح.', 'success')
        return redirect(url_for('certificates'))

    courses = Course.query.all()
    students = Student.query.all()
    return render_template('certificates.html', courses=courses, students=students)

# ---------- 23. CENTER ACTIVITIES ----------
@app.route('/center_activities', methods=['GET', 'POST'])
@require_role('admin')
def center_activities():
    if request.method == 'POST':
        activity_type = request.form['activity_type']
        location = request.form['location']
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(request.form['start_time'], '%H:%M').time()
        end_time = datetime.strptime(request.form['end_time'], '%H:%M').time()
        target_students = request.form.get('target_students', type=int)
        details = request.form.get('details')
        circle_ids = request.form.getlist('circle_ids')

        new_activity = CenterActivity(
            activity_type=activity_type,
            location=location,
            date=date,
            start_time=start_time,
            end_time=end_time,
            target_students=target_students,
            details=details
        )

        circles = Circle.query.filter(Circle.id.in_(circle_ids)).all()
        new_activity.circles.extend(circles)

        db.session.add(new_activity)
        db.session.commit()
        flash('تمت إضافة النشاط بنجاح!', 'success')
        return redirect(url_for('center_activities'))

    activities = CenterActivity.query.order_by(CenterActivity.date.desc()).all()
    circles = Circle.query.filter_by(is_active=True).all()
    return render_template('center_activities.html', activities=activities, circles=circles)

@app.route('/view_center_activities')
@require_login
def view_center_activities():
    activities = CenterActivity.query.filter_by(is_active=True).order_by(CenterActivity.date.desc()).all()
    return render_template('view_center_activities.html', activities=activities)

@app.route('/upload_certificate/<int:course_id>/<int:student_id>', methods=['GET', 'POST'])
@require_role('admin')
def upload_certificate(course_id, student_id):
    if request.method == 'POST':
        if 'certificate' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['certificate']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        if file and file.filename.endswith('.pdf'):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Check if a certificate entry already exists
            certificate = Certificate.query.filter_by(student_id=student_id, course_id=course_id).first()
            if certificate:
                certificate.certificate_file = filename
            else:
                certificate = Certificate(
                    student_id=student_id,
                    course_id=course_id,
                    certificate_file=filename
                )
                db.session.add(certificate)

            db.session.commit()
            flash('Certificate uploaded successfully', 'success')
            return redirect(url_for('course_details', course_id=course_id))

    course = Course.query.get_or_404(course_id)
    student = Student.query.get_or_404(student_id)
    return render_template('upload_certificate.html', course=course, student=student)

@app.route('/edit_center_activity/<int:activity_id>', methods=['GET', 'POST'])
@require_role('admin')
def edit_center_activity(activity_id):
    activity = CenterActivity.query.get_or_404(activity_id)
    if request.method == 'POST':
        activity.activity_type = request.form['activity_type']
        activity.location = request.form['location']
        activity.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        activity.start_time = datetime.strptime(request.form['start_time'], '%H:%M').time()
        activity.end_time = datetime.strptime(request.form['end_time'], '%H:%M').time()
        activity.target_students = request.form.get('target_students', type=int)
        activity.details = request.form.get('details')
        circle_ids = request.form.getlist('circle_ids')

        circles = Circle.query.filter(Circle.id.in_(circle_ids)).all()
        activity.circles = circles

        db.session.commit()
        flash('تم تعديل النشاط بنجاح!', 'success')
        return redirect(url_for('center_activities'))

    circles = Circle.query.filter_by(is_active=True).all()
    return render_template('edit_center_activity.html', activity=activity, circles=circles)

@app.route('/my_certificates')
@require_login
def my_certificates():
    if session['role'] == 'parent':
        parent = Parent.query.filter_by(user_id=session['user_id']).first()
        students = parent.students
    elif session['role'] == 'student':
        user = User.query.get(session['user_id'])
        student = Student.query.filter_by(name=user.name).first()
        students = [student] if student else []
    else:
        students = []

    return render_template('my_certificates.html', students=students)

@app.route('/delete_center_activity/<int:activity_id>')
@require_role('admin')
def delete_center_activity(activity_id):
    activity = CenterActivity.query.get_or_404(activity_id)
    db.session.delete(activity)
    db.session.commit()
    flash('تم حذف النشاط بنجاح!', 'success')
    return redirect(url_for('center_activities'))

# ---------- 24.  RUN ----------
def setup_database():
    """Initializes the database, creates tables, and runs simple migrations."""
    with app.app_context():
        # Ensure all tables are created based on the models.
        # This will create tables that don't exist, but won't modify existing ones.
        db.create_all()

        # Simple migration logic to add columns if they are missing.
        # This is for users who have an older version of the database.
        
        # 1. Add 'allow_custom_teacher_name' to 'settings' table
        try:
            # We first try to add the column. If it fails because it already exists, we ignore the error.
            with db.engine.connect() as connection:
                trans = connection.begin()
                connection.execute(text('ALTER TABLE settings ADD COLUMN allow_custom_teacher_name BOOLEAN DEFAULT 1'))
                trans.commit()
            print("INFO: Added 'allow_custom_teacher_name' column to 'settings' table.")
        except Exception as e:
            # Check if the error is due to a duplicate column, which is expected if the DB is up to date.
            if 'duplicate column' in str(e).lower():
                pass # Column already exists, which is fine.
            else:
                print(f"ERROR: Could not add 'allow_custom_teacher_name' column: {e}")

        # 2. Add 'user_id' to 'parent' table
        try:
            with db.engine.connect() as connection:
                trans = connection.begin()
                connection.execute(text('ALTER TABLE parent ADD COLUMN user_id INTEGER'))
                trans.commit()
            print("INFO: Added 'user_id' column to 'parent' table.")
        except Exception as e:
            if 'duplicate column' in str(e).lower():
                pass # Column already exists.
            else:
                print(f"ERROR: Could not add 'user_id' column to 'parent' table: {e}")

        # Seed initial data if it doesn't exist
        # 1. Default settings
        if not Settings.query.first():
            try:
                db.session.add(Settings())
                db.session.commit()
                print("INFO: Created default settings.")
            except Exception as e:
                print(f"ERROR: Could not create default settings: {e}")
                db.session.rollback()

        # 2. Default admin user and badges
        if not User.query.filter_by(role='admin').first():
            try:
                seed_badges()
                admin_user = User(
                    username='admin',
                    password=generate_password_hash('admin123'),
                    name='المسؤول',
                    role='admin'
                )
                db.session.add(admin_user)
                db.session.commit()
                print("INFO: Created default admin user.")
            except Exception as e:
                print(f"ERROR: Could not create default admin user: {e}")
                db.session.rollback()

if __name__ == '__main__':
    setup_database()
    app.run(debug=True, host='0.0.0.0', port=5000)
