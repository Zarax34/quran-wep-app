# ---------- 1.  IMPORTS  ----------
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy import inspect, func, text, or_, case
from functools import wraps
import re, os, urllib.parse
from fpdf import FPDF
from flask_mail import Mail, Message as MailMessage
from apscheduler.schedulers.background import BackgroundScheduler
import json

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

# Load Quran data from JSON file
with open('quran_data.json', 'r') as f:
    quran_data = json.load(f)
quran_data_map = {item['verse_key']: item for item in quran_data}

surah_names = [
    "الفاتحة", "البقرة", "آل عمران", "النساء", "المائدة", "الأنعام", "الأعراف", "الأنفال", "التوبة", "يونس",
    "هود", "يوسف", "الرعد", "إبراهيم", "الحجر", "النحل", "الإسراء", "الكهف", "مريم", "طه", "الأنبياء",
    "الحج", "المؤمنون", "النور", "الفرقان", "الشعراء", "النمل", "القصص", "العنكبوت", "الروم", "لقمان",
    "السجدة", "الأحزاب", "سبأ", "فاطر", "يس", "الصافات", "ص", "الزمر", "غافر", "فصلت", "الشورى", "الزخرف",
    "الدخان", "الجاثية", "الأحقاف", "محمد", "الفتح", "الحجرات", "ق", "الذاريات", "الطور", "النجم", "القمر",
    "الرحمن", "الواقعة", "الحديد", "المجادلة", "الحشر", "الممتحنة", "الصف", "الجمعة", "المنافقون",
    "التغابن", "الطلاق", "التحريم", "الملك", "القلم", "الحاقة", "المعارج", "نوح", "الجن", "المزمل",
    "المدثر", "القيامة", "الإنسان", "المرسلات", "النبأ", "النازعات", "عبس", "التكوير", "الإنفطار",
    "المطففين", "الإنشقاق", "البروج", "الطارق", "الأعلى", "الغاشية", "الفجر", "البلد", "الشمس", "الليل",
    "الضحى", "الشرح", "التين", "العلق", "القدر", "البينة", "الزلزلة", "العاديات", "القارعة", "التكاثر",
    "العصر", "الهمزة", "الفيل", "قريش", "الماعون", "الكوثر", "الكافرون", "النصر", "المسد", "الإخلاص",
    "الفلق", "الناس"
]

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
    last_memorized_sura = db.Column(db.String(100), default='الفاتحة')
    last_memorized_ayah = db.Column(db.Integer, default=0)
    memorization_direction = db.Column(db.String(50), default='BaqarahToNas') # or 'NasToBaqarah'
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
    social_instagram = db.Column(db.String(200))
    social_facebook = db.Column(db.String(200))
    social_whatsapp = db.Column(db.String(200))
    social_telegram = db.Column(db.String(200))

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

class CenterActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    image = db.Column(db.String(200))
    fee = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    participants = db.relationship('Student', secondary='activity_approval', backref='activities', overlaps="approvals,activity")

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
    date_paid = db.Column(db.Date, nullable=False, default=datetime.now().date)
    notes = db.Column(db.Text)
    student = db.relationship('Student', backref='fees')

class Work(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(200))
    link = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.now)

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
    username = full_name.strip().replace(' ', '_')
    base_username = username
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username}_{counter}"
        counter += 1
    return username

def create_student_username(full_name):
    username = full_name.strip().replace(' ', '_')
    base_username = username
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username}_{counter}"
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
            # The student's name is the part before the first colon
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

                        # Automatic Hifz/Muraja'ah logic
                        is_hifz = False
                        try:
                            last_sura_index = surah_names.index(student.last_memorized_sura)
                            report_sura_index = surah_names.index(surah)

                            if student.memorization_direction == 'BaqarahToNas':
                                if report_sura_index > last_sura_index:
                                    is_hifz = True
                                elif report_sura_index == last_sura_index and from_verse > student.last_memorized_ayah:
                                    is_hifz = True
                            else: # NasToBaqarah
                                if report_sura_index < last_sura_index:
                                    is_hifz = True
                                elif report_sura_index == last_sura_index and to_verse < student.last_memorized_ayah:
                                    is_hifz = True
                        except (ValueError, IndexError):
                            # Default to Hifz if surah not found or other errors
                            is_hifz = True

                        report_type = 'حفظ' if is_hifz else 'مراجعة'

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
    thirty_days_ago = datetime.now().date() - timedelta(days=30)

    # Query to get total attendance and total possible days per student
    # This is more efficient than looping in Python
    results = db.session.query(
        func.sum(case((Attendance.status == 'حاضر', 1), else_=0)).label('total_present'),
        func.count(Attendance.id).label('total_days')
    ).filter(
        Attendance.date >= thirty_days_ago,
        func.strftime('%w', Attendance.date) != '5'  # SQLite: '5' is Friday
    ).first()

    if results and results.total_days > 0:
        return round((results.total_present / results.total_days) * 100, 2)
    return 0

def get_student_stats(student_id):
    student = db.session.get(Student, student_id)
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
    circle = db.session.get(Circle, circle_id)
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
    student = db.session.get(Student, student_id)
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
    
    return render_template('guest_dashboard.html',
                         settings=settings,
                         total_students=total_students,
                         total_teachers=total_teachers,
                         total_circles=total_circles,
                         total_reports=total_reports,
                         attendance_stats=attendance_stats,
                         center_attendance_rate=center_attendance_rate)

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
    
    # Student of the Month
    today = datetime.now().date()
    start_of_month = today.replace(day=1)

    # Subquery to count badges per student this month
    subquery = db.session.query(
        StudentBadge.student_id,
        func.count(StudentBadge.id).label('badge_count')
    ).filter(
        StudentBadge.date_awarded >= start_of_month
    ).group_by(StudentBadge.student_id).subquery()

    # Find the max badge count
    max_badge_count_query = db.session.query(func.max(subquery.c.badge_count)).scalar()

    students_of_the_month = []
    if max_badge_count_query:
        # Find all students with that max count
        top_students_ids = db.session.query(subquery.c.student_id).filter(subquery.c.badge_count == max_badge_count_query).all()
        student_ids = [s_id[0] for s_id in top_students_ids]
        students_of_the_month = Student.query.filter(Student.id.in_(student_ids)).all()

    return render_template('dashboard.html',
                         students_of_the_month=students_of_the_month,
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
            last_memorized_sura=request.form.get('last_memorized_sura'),
            last_memorized_ayah=request.form.get('last_memorized_ayah', type=int),
            memorization_direction=request.form.get('memorization_direction'),
            pending_approval=requires_approval()
        )
        db.session.add(student)
        
        # إنشاء وربط ولي الأمر
        parent = get_or_create_parent(name, parent_phone)
        if parent:
            student.parent_id = parent.id
        
        # Create user account for student, ensuring full name is stored for display
        student_username = create_student_username(name)
        student_user = User(username=student_username, password=generate_password_hash(parent_phone or student_phone or '123456'), name=name, role='student')
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
    return render_template('add_student.html', circles=circles, surah_names=surah_names)


@app.route('/upload_students_excel', methods=['GET', 'POST'])
@require_role('admin')
def upload_students_excel():
    if request.method == 'POST':
        # Logic to handle file upload and processing will be added here
        flash('File upload functionality is not yet implemented.', 'info')
        return redirect(url_for('upload_students_excel'))
    return render_template('upload_excel.html')


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
        student.last_memorized_sura = request.form.get('last_memorized_sura')
        student.last_memorized_ayah = request.form.get('last_memorized_ayah', type=int)
        student.memorization_direction = request.form.get('memorization_direction')

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
    return render_template('edit_student.html', student=student, circles=circles, surah_names=surah_names)

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
    from_date_str = request.args.get('from_date')
    to_date_str = request.args.get('to_date')

    query = Report.query

    # If the user is a parent, restrict the query to their children's reports
    if session.get('role') == 'parent':
        parent = Parent.query.filter_by(user_id=session['user_id']).first()
        if parent:
            child_ids = [student.id for student in parent.students]
            query = query.filter(Report.student_id.in_(child_ids))
        else:
            # If for some reason a parent user has no parent object, show no reports
            query = query.filter(Report.id == -1) # No reports will match this

    if from_date_str:
        from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        query = query.filter(Report.date >= from_date)

    if to_date_str:
        to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        query = query.filter(Report.date <= to_date)

    reports = query.order_by(Report.date.desc()).all()
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
        
        student = db.session.get(Student, student_id)
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

        # Automatically mark attendance if not already recorded
        existing_attendance = Attendance.query.filter_by(student_id=student.id, date=date).first()
        if not existing_attendance:
            new_attendance = Attendance(student_id=student.id, date=date, status='حاضر', notes='تم التحضير تلقائياً لوجود تسميع')
            db.session.add(new_attendance)

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

    return render_template('add_report.html', students=students, surah_names=surah_names)

@app.route('/collective_report', methods=['GET', 'POST'])
@require_login
def collective_report():
    if request.method == 'POST':
        circle_id = request.form['circle_id']
        date = request.form['date']
        report_text = request.form['report_text']
        confirm = request.form.get('confirm')

        reports_data, attendances_data = improved_parse_collective_report(report_text, circle_id, date)

        if not confirm:
            # First step: Show preview
            reports_for_preview = []
            for rep in reports_data:
                student = db.session.get(Student, rep['student_id'])
                if student:
                    # Create temporary Report objects for rendering in the template
                    temp_report = {
                        'student': student,
                        'surah': rep['surah'],
                        'from_verse': rep['from_verse'],
                        'to_verse': rep['to_verse'],
                        'type': rep['type'],
                        'grade': rep['grade']
                    }
                    reports_for_preview.append(temp_report)

            return render_template('collective_report_preview.html',
                                   reports=reports_for_preview,
                                   circle_id=circle_id,
                                   date=date,
                                   report_text=report_text)

        # Second step: Confirmed, save the data
        for rep in reports_data:
            student = db.session.get(Student, rep['student_id'])
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

                if report.type == 'حفظ':
                    student.last_memorized_sura = report.surah
                    student.last_memorized_ayah = report.to_verse

        for att_data in attendances_data:
            attendance = Attendance(
                student_id=att_data.student_id,
                date=att_data.date,
                status=att_data.status,
                notes=att_data.notes
            )
            db.session.add(attendance)
        
        try:
            db.session.commit()
            flash(f'تم رفع {len(reports_data)} تقرير وتحديث {len(attendances_data)} حضور', 'success')
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
    
    return render_template('edit_report.html', report=report, surah_names=surah_names)

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
            # Check if status changed to absent
            if attendance.status != status and ('غائب' in status):
                if student.parent and student.parent.user_id:
                    notification = Notification(
                        user_id=student.parent.user_id,
                        title='غياب طالب',
                        message=f'تم تسجيل ابنك "{student.name}" كـ "{status}" بتاريخ {date.strftime("%Y-%m-%d")}.'
                    )
                    db.session.add(notification)
            attendance.status = status
            attendance.notes = notes
        else:
            attendance = Attendance(student_id=student.id, date=date, status=status, notes=notes)
            db.session.add(attendance)
            # Notify if absent on first record
            if 'غائب' in status:
                if student.parent and student.parent.user_id:
                    notification = Notification(
                        user_id=student.parent.user_id,
                        title='غياب طالب',
                        message=f'تم تسجيل ابنك "{student.name}" كـ "{status}" بتاريخ {date.strftime("%Y-%m-%d")}.'
                    )
                    db.session.add(notification)
    
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
@app.route('/parent_management')
@require_role('admin')
def parent_management():
    # Join Parent with User to get all necessary details for management
    parents = db.session.query(Parent, User).outerjoin(User, Parent.user_id == User.id).all()
    total_linked_students = Student.query.filter(Student.parent_id.isnot(None)).count()
    return render_template('parent_management.html', parents=parents, total_linked_students=total_linked_students)

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
                        
                        # Create user account with a sanitized username and the original full name for display
                        username = create_parent_username(name)
                        user = User(
                            username=username,
                            password=generate_password_hash(phone),
                            name=name,  # Full name with spaces for display
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
            return redirect(url_for('parent_management'))
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
        
        student = db.session.get(Student, student_id)
        parent = db.session.get(Parent, parent_id)
        
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
    # Only show admins and teachers in user management
    users = User.query.filter(User.role.in_(['admin', 'teacher', 'support'])).all()
    return render_template('users.html', users=users)

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

@app.route('/announcements')
@require_login # Allow all logged in users to view
def announcements():
    all_announcements = Announcement.query.filter_by(is_active=True).order_by(Announcement.date_posted.desc()).all()
    return render_template('announcements.html', announcements=all_announcements)

@app.route('/add_announcement', methods=['GET', 'POST'])
@require_role('admin')
def add_announcement():
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
        flash('تم نشر الإعلان بنجاح!', 'success')
        return redirect(url_for('announcements'))
    return render_template('add_announcement.html')

@app.route('/edit_announcement/<int:announcement_id>', methods=['GET', 'POST'])
@require_role('admin')
def edit_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    if request.method == 'POST':
        announcement.title = request.form['title']
        announcement.content = request.form['content']
        announcement.is_active = 'is_active' in request.form

        image = request.files.get('image')
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            announcement.image = filename

        db.session.commit()
        flash('تم تحديث الإعلان بنجاح!', 'success')
        return redirect(url_for('announcements'))
    return render_template('edit_announcement.html', announcement=announcement)

@app.route('/delete_announcement/<int:announcement_id>')
@require_role('admin')
def delete_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    db.session.delete(announcement)
    db.session.commit()
    flash('تم حذف الإعلان بنجاح.', 'success')
    return redirect(url_for('announcements'))

# ---------- Center Activities Routes ----------
@app.route('/activities')
@require_login
def activities():
    activities = CenterActivity.query.order_by(CenterActivity.date.desc()).all()
    parent = None
    if session.get('role') == 'parent':
        parent = Parent.query.filter_by(user_id=session['user_id']).first()

    return render_template('activities.html',
                         activities=activities,
                         parent=parent)

@app.route('/add_activity', methods=['GET', 'POST'])
@require_role('admin')
def add_activity():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        image = request.files.get('image')
        fee = request.form.get('fee', type=float)
        student_ids = request.form.getlist('student_ids')

        filename = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        activity = CenterActivity(title=title, description=description, date=date, image=filename, fee=fee)
        db.session.add(activity)
        db.session.commit() # Commit to get activity.id

        for student_id in student_ids:
            student = Student.query.get(student_id)
            if student:
                approval = ActivityApproval(student_id=student.id, activity_id=activity.id, status='Pending')
                db.session.add(approval)

        for student_id in student_ids:
            student = Student.query.get(student_id)
            if student:
                approval = ActivityApproval(student_id=student.id, activity_id=activity.id, status='Pending')
                db.session.add(approval)

                # Notify parent
                if student.parent and student.parent.user_id:
                    notification = Notification(
                        user_id=student.parent.user_id,
                        title='دعوة للمشاركة في نشاط',
                        message=f'تمت دعوة ابنك "{student.name}" للمشاركة في نشاط "{title}". يرجى الموافقة أو الرفض.'
                    )
                    db.session.add(notification)

        db.session.commit()
        flash('تم إضافة النشاط وإشعار أولياء الأمور بنجاح!', 'success')
        return redirect(url_for('activities'))

    students = Student.query.filter_by(is_active=True).all()
    return render_template('add_activity.html', students=students)

@app.route('/edit_activity/<int:activity_id>', methods=['GET', 'POST'])
@require_role('admin')
def edit_activity(activity_id):
    activity = CenterActivity.query.get_or_404(activity_id)
    if request.method == 'POST':
        activity.title = request.form['title']
        activity.description = request.form['description']
        activity.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        activity.fee = request.form.get('fee', type=float)

        image = request.files.get('image')
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            activity.image = filename

        db.session.commit()
        flash('تم تعديل النشاط بنجاح!', 'success')
        return redirect(url_for('activities'))

    return render_template('edit_activity.html', activity=activity)

# ---------- Fee Management Routes ----------
@app.route('/fees')
@require_login
def fees():
    fees = Fee.query.order_by(Fee.date_paid.desc()).all()
    return render_template('fees.html', fees=fees)

@app.route('/add_fee', methods=['GET', 'POST'])
@require_login
def add_fee():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        amount = request.form.get('amount', type=float)
        date_paid = datetime.strptime(request.form['date_paid'], '%Y-%m-%d').date() if request.form.get('date_paid') else datetime.now().date()
        notes = request.form.get('notes')

        if not student_id or not amount:
            flash('يرجى ملء جميع الحقول المطلوبة.', 'error')
            return redirect(url_for('add_fee'))

        fee = Fee(student_id=student_id, amount=amount, date_paid=date_paid, notes=notes)
        db.session.add(fee)
        db.session.commit()
        flash('تمت إضافة الرسوم بنجاح!', 'success')
        return redirect(url_for('fees'))

    students = Student.query.filter_by(is_active=True).all()
    return render_template('add_fee.html', students=students)

@app.route('/edit_fee/<int:fee_id>', methods=['GET', 'POST'])
@require_login
def edit_fee(fee_id):
    fee = Fee.query.get_or_404(fee_id)
    if request.method == 'POST':
        fee.student_id = request.form.get('student_id')
        fee.amount = request.form.get('amount', type=float)
        fee.date_paid = datetime.strptime(request.form['date_paid'], '%Y-%m-%d').date() if request.form.get('date_paid') else fee.date_paid
        fee.notes = request.form.get('notes')
        db.session.commit()
        flash('تم تعديل الرسوم بنجاح!', 'success')
        return redirect(url_for('fees'))

    students = Student.query.filter_by(is_active=True).all()
    return render_template('edit_fee.html', fee=fee, students=students)

@app.route('/delete_fee/<int:fee_id>', methods=['POST'])
@require_login
def delete_fee(fee_id):
    fee = Fee.query.get_or_404(fee_id)
    db.session.delete(fee)
    db.session.commit()
    flash('تم حذف الرسوم بنجاح!', 'success')
    return redirect(url_for('fees'))

@app.route('/approve_activity/<int:student_id>/<int:activity_id>', methods=['POST'])
@require_login
def approve_activity(student_id, activity_id):
    if session.get('role') != 'parent':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    parent = Parent.query.filter_by(user_id=session['user_id']).first()
    student = Student.query.get_or_404(student_id)
    activity = CenterActivity.query.get_or_404(activity_id)

    if not parent or student.parent_id != parent.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    if datetime.now().date() > activity.date:
        return jsonify({'success': False, 'message': 'Activity has already passed.'}), 400

    approval = ActivityApproval.query.filter_by(student_id=student_id, activity_id=activity_id).first()
    if not approval:
        return jsonify({'success': False, 'message': 'No approval record found.'}), 404

    status = request.json.get('status')
    if status in ['Approved', 'Rejected']:
        approval.status = status
        db.session.commit()
        return jsonify({'success': True, 'status': approval.status})

    return jsonify({'success': False, 'message': 'Invalid status.'}), 400


@app.route('/delete_activity/<int:activity_id>', methods=['POST'])
@require_role('admin')
def delete_activity(activity_id):
    activity = CenterActivity.query.get_or_404(activity_id)
    db.session.delete(activity)
    db.session.commit()
    flash('تم حذف النشاط بنجاح!', 'success')
    return redirect(url_for('activities'))

# ---------- Alumni Routes ----------
@app.route('/alumni')
def alumni():
    alumni_list = Alumni.query.order_by(Alumni.graduation_year.desc()).all()
    return render_template('alumni.html', alumni_list=alumni_list)

@app.route('/manage_alumni')
@require_role('admin')
def manage_alumni():
    alumni_list = Alumni.query.all()
    return render_template('manage_alumni.html', alumni_list=alumni_list)

@app.route('/add_alumni', methods=['GET', 'POST'])
@require_role('admin')
def add_alumni():
    if request.method == 'POST':
        name = request.form['name']
        graduation_year = request.form['graduation_year']
        testimonial = request.form.get('testimonial')
        photo = request.files.get('photo')

        filename = None
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        alumnus = Alumni(name=name, graduation_year=graduation_year, testimonial=testimonial, photo=filename)
        db.session.add(alumnus)
        db.session.commit()
        flash('تمت إضافة الخريج بنجاح!', 'success')
        return redirect(url_for('manage_alumni'))

    return render_template('add_alumni.html')

@app.route('/edit_alumni/<int:alumni_id>', methods=['GET', 'POST'])
@require_role('admin')
def edit_alumni(alumni_id):
    alumnus = Alumni.query.get_or_404(alumni_id)
    if request.method == 'POST':
        alumnus.name = request.form['name']
        alumnus.graduation_year = request.form['graduation_year']
        alumnus.testimonial = request.form.get('testimonial')

        photo = request.files.get('photo')
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            alumnus.photo = filename

        db.session.commit()
        flash('تم تعديل بيانات الخريج بنجاح!', 'success')
        return redirect(url_for('manage_alumni'))

    return render_template('edit_alumni.html', alumnus=alumnus)

@app.route('/delete_alumni/<int:alumni_id>', methods=['POST'])
@require_role('admin')
def delete_alumni(alumni_id):
    alumnus = Alumni.query.get_or_404(alumni_id)
    db.session.delete(alumnus)
    db.session.commit()
    flash('تم حذف الخريج بنجاح!', 'success')
    return redirect(url_for('manage_alumni'))

# ---------- Our Work Routes ----------
@app.route('/our_work')
def our_work():
    work_list = Work.query.order_by(Work.created_at.desc()).all()
    return render_template('our_work.html', work_list=work_list)

@app.route('/manage_work')
@require_role('admin')
def manage_work():
    work_list = Work.query.all()
    return render_template('manage_work.html', work_list=work_list)

@app.route('/add_work', methods=['GET', 'POST'])
@require_role('admin')
def add_work():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        link = request.form.get('link')
        image = request.files.get('image')

        filename = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        work_item = Work(title=title, description=description, link=link, image=filename)
        db.session.add(work_item)
        db.session.commit()
        flash('تمت إضافة العمل بنجاح!', 'success')
        return redirect(url_for('manage_work'))

    return render_template('add_work.html')

@app.route('/edit_work/<int:work_id>', methods=['GET', 'POST'])
@require_role('admin')
def edit_work(work_id):
    work_item = Work.query.get_or_404(work_id)
    if request.method == 'POST':
        work_item.title = request.form['title']
        work_item.description = request.form['description']
        work_item.link = request.form.get('link')

        image = request.files.get('image')
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            work_item.image = filename

        db.session.commit()
        flash('تم تعديل العمل بنجاح!', 'success')
        return redirect(url_for('manage_work'))

    return render_template('edit_work.html', work_item=work_item)

@app.route('/delete_work/<int:work_id>', methods=['POST'])
@require_role('admin')
def delete_work(work_id):
    work_item = Work.query.get_or_404(work_id)
    db.session.delete(work_item)
    db.session.commit()
    flash('تم حذف العمل بنجاح!', 'success')
    return redirect(url_for('manage_work'))

@app.route('/api/get_page_number', methods=['GET'])
def get_page_number():
    surah_name = request.args.get('surah')
    verse = request.args.get('verse')
    if not surah_name or not verse:
        return jsonify({'error': 'Surah and verse parameters are required'}), 400

    try:
        surah_number = surah_names.index(surah_name) + 1
    except ValueError:
        return jsonify({'error': 'Invalid surah name'}), 404

    verse_key = f"{surah_number}:{verse}"
    verse_data = quran_data_map.get(verse_key)

    if verse_data:
        return jsonify({'page_number': verse_data.get('page_number')})
    else:
        return jsonify({'error': f'Verse not found for key {verse_key}'}), 404

@app.route('/api/get_surah_details', methods=['GET'])
def get_surah_details():
    surah_name = request.args.get('surah')
    if not surah_name:
        return jsonify({'error': 'Surah parameter is required'}), 400

    try:
        surah_number = surah_names.index(surah_name) + 1
    except ValueError:
        return jsonify({'error': 'Invalid surah name'}), 404

    max_verse = 0
    for item in quran_data:
        s_num_str, v_num_str = item['verse_key'].split(':')
        s_num = int(s_num_str)
        if s_num == surah_number:
            v_num = int(v_num_str)
            if v_num > max_verse:
                max_verse = v_num

    if max_verse > 0:
        return jsonify({'verse_count': max_verse})
    else:
        return jsonify({'error': 'Surah not found or has no verses'}), 404

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

@app.route('/block_user/<int:user_id>')
@require_role('admin')
def block_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'تم {"إلغاء حظر" if user.is_active else "حظر"} المستخدم {user.name} بنجاح.', 'success')
    return redirect(request.referrer or url_for('users'))

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
        
        settings_obj.social_instagram = request.form.get('social_instagram')
        settings_obj.social_facebook = request.form.get('social_facebook')
        settings_obj.social_whatsapp = request.form.get('social_whatsapp')
        settings_obj.social_telegram = request.form.get('social_telegram')

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
        # Mark all notifications as read
        Notification.query.filter_by(user_id=parent.user_id, is_read=False).update({'is_read': True})
        db.session.commit()

        notifs = Notification.query.filter_by(user_id=parent.user_id).order_by(Notification.created_at.desc()).all()
        return render_template('notifications.html', notifications=notifs)

    flash('لم يتم العثور على بيانات ولي الأمر', 'error')
    return redirect(url_for('dashboard'))

@app.route('/api/unread_notifications_count')
@require_login
def unread_notifications_count():
    count = 0
    if 'user_id' in session:
        count = Notification.query.filter_by(user_id=session['user_id'], is_read=False).count()
    return jsonify({'count': count})

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
@app.route('/messaging')
@require_login
def messaging():
    if session.get('role') != 'parent':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))
    return render_template('messaging.html')

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

    # Center stats
    center_stats = {
        'total_students': Student.query.filter_by(is_active=True).count(),
        'average_attendance': get_center_attendance_stats(),
        'total_verses_this_month': Report.query.filter(Report.date >= datetime.now().date() - timedelta(days=30)).count()
    }

    # Student of the Month
    today = datetime.now().date()
    start_of_month = today.replace(day=1)
    subquery = db.session.query(
        StudentBadge.student_id,
        func.count(StudentBadge.id).label('badge_count')
    ).filter(
        StudentBadge.date_awarded >= start_of_month
    ).group_by(StudentBadge.student_id).subquery()
    max_badge_count_query = db.session.query(func.max(subquery.c.badge_count)).scalar()
    students_of_the_month = []
    if max_badge_count_query:
        top_students_ids = db.session.query(subquery.c.student_id).filter(subquery.c.badge_count == max_badge_count_query).all()
        student_ids = [s_id[0] for s_id in top_students_ids]
        students_of_the_month = Student.query.filter(Student.id.in_(student_ids)).all()
    
    return render_template('parent_dashboard.html', 
                         students_of_the_month=students_of_the_month,
                         parent=parent, 
                         student_stats=student_stats,
                         total_children=total_children,
                         total_attendance_rate=total_attendance_rate,
                         total_monthly_reports=total_monthly_reports,
                         center_stats=center_stats,
                         honor_students=honor_students)

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
@require_login
def courses():
    # Admin sees all courses, teacher sees only their own
    if session['role'] == 'admin':
        courses_list = Course.query.order_by(Course.created_at.desc()).all()
    else: # teacher
        courses_list = Course.query.filter_by(teacher_id=session['user_id']).order_by(Course.created_at.desc()).all()
    return render_template('courses.html', courses=courses_list)

@app.route('/add_course', methods=['GET', 'POST'])
@require_login
def add_course():
    if session.get('role') not in ['admin', 'teacher']:
        flash('ليس لديك الصلاحية لإضافة دورات', 'error')
        return redirect(url_for('courses'))

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
@require_login
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    # Authorization check
    if session['role'] == 'teacher' and course.teacher_id != session['user_id']:
        flash('ليس لديك الصلاحية لتعديل هذه الدورة', 'error')
        return redirect(url_for('courses'))

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
@require_login
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    # Authorization check
    if session['role'] == 'teacher' and course.teacher_id != session['user_id']:
        flash('ليس لديك الصلاحية لحذف هذه الدورة', 'error')
        return redirect(url_for('courses'))

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
@require_login
def course_details(course_id):
    course = Course.query.get_or_404(course_id)
    # Authorization check
    if session['role'] == 'teacher' and course.teacher_id != session['user_id']:
        flash('ليس لديك الصلاحية لعرض تفاصيل هذه الدورة', 'error')
        return redirect(url_for('courses'))

    enrolled_students = Student.query.join(CourseEnrollment).filter(CourseEnrollment.course_id == course.id).all()

    # Students not yet enrolled in this course
    enrolled_student_ids = [s.id for s in enrolled_students]
    available_students = Student.query.filter(Student.id.notin_(enrolled_student_ids), Student.is_active==True).all()

    return render_template('course_details.html', course=course, enrolled_students=enrolled_students, available_students=available_students)

@app.route('/enroll_student/<int:course_id>', methods=['POST'])
@require_login
def enroll_student(course_id):
    course = Course.query.get_or_404(course_id)
    # Authorization
    if session['role'] == 'teacher' and course.teacher_id != session['user_id']:
        flash('ليس لديك الصلاحية لتسجيل طلاب في هذه الدورة', 'error')
        return redirect(url_for('courses'))

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

            # Notify parent
            student = Student.query.get(student_id)
            if student and student.parent and student.parent.user_id:
                notification = Notification(
                    user_id=student.parent.user_id,
                    title='تسجيل في دورة جديدة',
                    message=f'تم تسجيل ابنك "{student.name}" في دورة "{course.name}".'
                )
                db.session.add(notification)

    try:
        db.session.commit()
        flash(f'تم تسجيل {len(student_ids)} طالب بنجاح!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء تسجيل الطلاب: {e}', 'error')

    return redirect(url_for('course_details', course_id=course_id))

@app.route('/unenroll_student/<int:course_id>/<int:student_id>')
@require_login
def unenroll_student(course_id, student_id):
    enrollment = CourseEnrollment.query.filter_by(course_id=course_id, student_id=student_id).first_or_404()
    course = enrollment.course
    # Authorization
    if session['role'] == 'teacher' and course.teacher_id != session['user_id']:
        flash('ليس لديك الصلاحية لإزالة طلاب من هذه الدورة', 'error')
        return redirect(url_for('courses'))

    try:
        db.session.delete(enrollment)
        db.session.commit()
        flash('تم إلغاء تسجيل الطالب بنجاح.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء إلغاء التسجيل: {e}', 'error')

    return redirect(url_for('course_details', course_id=course_id))

@app.route('/course/<int:course_id>/tests')
@require_login
def manage_tests(course_id):
    course = Course.query.get_or_404(course_id)
    # Authorization
    if session['role'] == 'teacher' and course.teacher_id != session['user_id']:
        flash('ليس لديك الصلاحية لإدارة اختبارات هذه الدورة', 'error')
        return redirect(url_for('courses'))

    return render_template('manage_tests.html', course=course)

@app.route('/add_test/<int:course_id>', methods=['POST'])
@require_login
def add_test(course_id):
    course = Course.query.get_or_404(course_id)
    # Authorization
    if session['role'] == 'teacher' and course.teacher_id != session['user_id']:
        flash('ليس لديك الصلاحية لإضافة اختبارات لهذه الدورة', 'error')
        return redirect(url_for('courses'))

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
@require_login
def edit_test(test_id):
    test = Test.query.get_or_404(test_id)
    # Authorization
    if session['role'] == 'teacher' and test.course.teacher_id != session['user_id']:
        flash('ليس لديك الصلاحية لتعديل هذا الاختبار', 'error')
        return redirect(url_for('courses'))

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
@require_login
def delete_test(test_id):
    test = Test.query.get_or_404(test_id)
    course_id = test.course_id
    # Authorization
    if session['role'] == 'teacher' and test.course.teacher_id != session['user_id']:
        flash('ليس لديك الصلاحية لحذف هذا الاختبار', 'error')
        return redirect(url_for('courses'))

    try:
        db.session.delete(test)
        db.session.commit()
        flash('تم حذف الاختبار بنجاح.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف الاختبار: {e}', 'error')

    return redirect(url_for('manage_tests', course_id=course_id))

@app.route('/record_scores/<int:test_id>', methods=['GET', 'POST'])
@require_login
def record_scores(test_id):
    test = Test.query.get_or_404(test_id)
    # Authorization
    if session['role'] == 'teacher' and test.course.teacher_id != session['user_id']:
        flash('ليس لديك الصلاحية لتسجيل درجات لهذا الاختبار', 'error')
        return redirect(url_for('courses'))

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
@app.route('/parent/courses')
@require_login
@require_role('parent')
def parent_courses():
    parent = Parent.query.filter_by(user_id=session['user_id']).first()
    if not parent:
        flash('لم يتم العثور على بيانات ولي الأمر', 'error')
        return redirect(url_for('logout'))

    # استعلام لجلب الدورات المسجل فيها أبناء ولي الأمر
    student_ids = [student.id for student in parent.students]

    # جلب الدورات مع الطلاب المسجلين فيها والشهادات
    courses_with_students = db.session.query(
        Course, Student, Certificate
    ).join(
        CourseEnrollment, Course.id == CourseEnrollment.course_id
    ).join(
        Student, Student.id == CourseEnrollment.student_id
    ).outerjoin(
        Certificate, (Certificate.student_id == Student.id) & (Certificate.course_id == Course.id)
    ).filter(
        Student.id.in_(student_ids)
    ).all()

    # تنظيم البيانات للعرض في القالب
    courses_data = {}
    for course, student, certificate in courses_with_students:
        if course.id not in courses_data:
            courses_data[course.id] = {
                'course': course,
                'students': []
            }

        # التأكد من عدم إضافة الطالب أكثر من مرة
        if not any(s['student'].id == student.id for s in courses_data[course.id]['students']):
            courses_data[course.id]['students'].append({
                'student': student,
                'certificate': certificate
            })

    return render_template('parent_courses.html', courses_data=courses_data.values())

@app.route('/parent/settings', methods=['GET', 'POST'])
@require_login
@require_role('parent')
def parent_settings():
    user = User.query.get_or_404(session['user_id'])
    parent = Parent.query.filter_by(user_id=session['user_id']).first_or_404()

    if request.method == 'POST':
        # Update user information
        user.username = request.form['username']
        user.name = request.form['name']
        user.email = request.form.get('email')

        # Update password if provided
        new_password = request.form.get('password')
        if new_password:
            user.password = generate_password_hash(new_password)

        # Update parent information
        parent.phone = request.form['phone']

        try:
            db.session.commit()
            flash('تم تحديث إعداداتك بنجاح!', 'success')
            # Update session data in case the name changed
            session['name'] = user.name
            return redirect(url_for('parent_settings'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تحديث الإعدادات: {e}', 'error')

    return render_template('parent_settings.html', user=user, parent=parent)

@app.route('/student_dashboard')
@require_login
def student_dashboard():
    if session.get('role') != 'student':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))

    user = db.session.get(User, session['user_id'])
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

    # Student of the Month
    today = datetime.now().date()
    start_of_month = today.replace(day=1)
    subquery = db.session.query(
        StudentBadge.student_id,
        func.count(StudentBadge.id).label('badge_count')
    ).filter(
        StudentBadge.date_awarded >= start_of_month
    ).group_by(StudentBadge.student_id).subquery()
    max_badge_count_query = db.session.query(func.max(subquery.c.badge_count)).scalar()
    students_of_the_month = []
    if max_badge_count_query:
        top_students_ids = db.session.query(subquery.c.student_id).filter(subquery.c.badge_count == max_badge_count_query).all()
        student_ids = [s_id[0] for s_id in top_students_ids]
        students_of_the_month = Student.query.filter(Student.id.in_(student_ids)).all()

    return render_template('student_details.html',
                         students_of_the_month=students_of_the_month,
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
        reason = request.form.get('reason', 'لإتمام متطلبات الدورة بنجاح') # Default reason

        if not all([course_id, student_id]):
            flash('يرجى ملء جميع الحقول المطلوبة.', 'error')
            return redirect(url_for('certificates'))

        student = db.session.get(Student, student_id)
        course = db.session.get(Course, course_id)

        # Create PDF certificate
        pdf = FPDF()
        pdf.add_page()
        pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
        pdf.set_font('DejaVu', '', 16)

        pdf.cell(0, 20, 'شهادة إتمام دورة', 0, 1, 'C')
        pdf.ln(10)

        pdf.set_font('DejaVu', '', 12)
        pdf.cell(0, 10, f'يشهد مركز الإمام حفص بأن الطالب/ة: {student.name}', 0, 1, 'C')
        pdf.ln(5)

        pdf.cell(0, 10, f'قد أتم بنجاح دورة: "{course.name}"', 0, 1, 'C')
        pdf.ln(5)

        pdf.cell(0, 10, f'وذلك {reason}', 0, 1, 'C')
        pdf.ln(20)

        pdf.cell(0, 10, f'تاريخ الإصدار: {datetime.now().strftime("%Y-%m-%d")}', 0, 1, 'L')
        pdf.cell(0, 10, 'توقيع المدير: ..............................', 0, 1, 'R')


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

# ---------- 23.  RUN ----------
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

        # Add social media columns to 'settings' table if they don't exist
        social_columns = ['social_instagram', 'social_facebook', 'social_whatsapp', 'social_telegram']
        for column in social_columns:
            try:
                with db.engine.connect() as connection:
                    trans = connection.begin()
                    connection.execute(text(f'ALTER TABLE settings ADD COLUMN {column} VARCHAR(200)'))
                    trans.commit()
                print(f"INFO: Added '{column}' column to 'settings' table.")
            except Exception as e:
                if 'duplicate column' in str(e).lower():
                    pass  # Column already exists, which is fine.
                else:
                    print(f"ERROR: Could not add '{column}' column to 'settings' table: {e}")

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
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
