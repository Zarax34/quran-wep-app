# ---------- 1.  IMPORTS  ----------
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy import inspect, func, text
from functools import wraps
import re, os, urllib.parse

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

# ---------- 3.  MODELS  ----------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, support, parent
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

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

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    user = db.relationship('User', backref='notifications')

# ---------- 4.  CONTEXT PROCESSOR  ----------
@app.context_processor
def inject_globals():
    settings = Settings.query.first() or Settings()
    current_year = datetime.now().year
    unread_notifications = 0
    if 'user_id' in session and session.get('role') == 'parent':
        parent = Parent.query.filter_by(name=session['name']).first()
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
    username = full_name.strip().replace(' ', ' ')
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
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['name'] = user.name
            flash('تم تسجيل الدخول بنجاح', 'success')
            if user.role == 'parent':
                return redirect(url_for('parent_dashboard'))
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
    
    return render_template('dashboard.html',
                         total_students=total_students,
                         total_teachers=total_teachers,
                         total_circles=total_circles,
                         total_reports=total_reports,
                         attendance_stats=attendance_stats,
                         recent_reports=recent_reports,
                         new_students=new_students,
                         center_attendance_rate=center_attendance_rate,
                         active_circles=active_circles)

# ---------- 8.  STUDENTS ----------
@app.route('/students')
@require_login
def students():
    view_mode = request.args.get('view_mode', 'table')
    selected_circle = request.args.get('circle_id', type=int)
    
    query = Student.query.filter_by(is_active=True)
    if selected_circle:
        query = query.filter_by(circle_id=selected_circle)
    
    students = query.all()
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
            pending_approval=requires_approval()
        )
        db.session.add(student)
        
        # إنشاء وربط ولي الأمر
        parent = get_or_create_parent(name, parent_phone)
        if parent:
            student.parent_id = parent.id
        
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

@app.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
@require_login
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == 'POST':
        student.name = request.form['name']
        student.age = request.form.get('age', type=int)
        student.student_phone = request.form.get('student_phone')
        student.parent_phone = request.form['parent_phone']
        student.circle_id = request.form['circle_id']
        
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
        
        circle = Circle(
            name=name,
            teacher_id=teacher_id,
            teacher_name=teacher_name,
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
        student_id = request.form['student_id']
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        surah = request.form['surah']
        from_verse = int(request.form['from_verse'])
        to_verse = int(request.form['to_verse'])
        type_ = request.form['type']
        grade = request.form['grade']
        notes = request.form.get('notes')
        
        student = Student.query.get(student_id)
        if not student:
            flash('الطالب غير موجود', 'error')
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
        
        try:
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
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/add_user', methods=['GET', 'POST'])
@require_role('admin')
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        name = request.form['name']
        role = request.form['role']
        
        user = User(username=username, password=password, name=name, role=role)
        db.session.add(user)
        
        try:
            db.session.commit()
            flash('تم إضافة المستخدم بنجاح', 'success')
            return redirect(url_for('users'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة المستخدم: {str(e)}', 'error')
    
    return render_template('add_user.html')

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@require_role('admin')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.name = request.form['name']
        user.role = request.form['role']
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
    
    parent = Parent.query.filter_by(name=session['name']).first()
    if parent and parent.user_id:
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
    
    parent = Parent.query.filter_by(name=session['name']).first()
    if not parent:
        flash('لم يتم العثور على بيانات ولي الأمر', 'error')
        return redirect(url_for('logout'))
    
    students = Student.query.filter_by(parent_id=parent.id, is_active=True).all()
    student_stats = []
    
    for student in students:
        stats = get_student_stats(student.id)
        if stats:
            student_stats.append(stats)
    
    total_children = len(students)
    total_attendance_rate = 0
    total_monthly_reports = 0
    
    for stats in student_stats:
        total_attendance_rate += stats['attendance_rate']
        total_monthly_reports += stats['monthly_reports']
    
    if student_stats:
        total_attendance_rate = total_attendance_rate / len(student_stats)
    
    # إحصائيات المركز
    center_stats = {
        'total_students': Student.query.filter_by(is_active=True).count(),
        'average_attendance': get_center_attendance_stats(),
        'total_verses_this_month': Report.query.filter(Report.date >= datetime.now().date() - timedelta(days=30)).count()
    }
    
    return render_template('parent_dashboard.html', 
                         parent=parent, 
                         student_stats=student_stats,
                         students=students,
                         total_children=total_children,
                         total_attendance_rate=total_attendance_rate,
                         total_monthly_reports=total_monthly_reports,
                         center_stats=center_stats)

# ---------- 21.  STUDENT REPORTS ----------
@app.route('/student_reports/<int:student_id>')
@require_login
def student_reports(student_id):
    student = Student.query.get_or_404(student_id)
    
    end_date_weekly = datetime.now().date()
    start_date_weekly = end_date_weekly - timedelta(days=7)
    end_date_monthly = datetime.now().date()
    start_date_monthly = end_date_monthly - timedelta(days=30)
    
    weekly_reports = Report.query.filter(Report.student_id == student_id, Report.date >= start_date_weekly, Report.date <= end_date_weekly).all()
    monthly_reports = Report.query.filter(Report.student_id == student_id, Report.date >= start_date_monthly, Report.date <= end_date_monthly).all()
    
    return render_template('student_reports.html',
                         student=student,
                         weekly_reports=weekly_reports,
                         monthly_reports=monthly_reports,
                         start_date_weekly=start_date_weekly,
                         end_date_weekly=end_date_weekly,
                         start_date_monthly=start_date_monthly,
                         end_date_monthly=end_date_monthly)

# ---------- 22.  PARENT STUDENT DETAILS ----------
@app.route('/parent_student_details/<int:student_id>')
@require_login
def parent_student_details(student_id):
    if session.get('role') != 'parent':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))
    
    student = Student.query.get_or_404(student_id)
    parent = Parent.query.filter_by(name=session['name']).first()
    
    if not parent or student.parent_id != parent.id:
        flash('ليس لديك صلاحية لعرض تفاصيل هذا الطالب', 'error')
        return redirect(url_for('parent_dashboard'))
    
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
    
    return render_template('parent_student_details.html',
                         student=student,
                         stats=stats,
                         recent_reports=recent_reports,
                         recent_attendance=recent_attendance,
                         circle_stats=circle_stats)

# ---------- 23.  RUN ----------
if __name__ == '__main__':
    with app.app_context():
        # التحقق من وجود الأعمدة المفقودة وإضافتها إذا لزم الأمر
        inspector = inspect(db.engine)
        
        # التحقق من وجود جدول Settings وإنشاؤه إذا لم يكن موجوداً
        if not inspector.has_table('settings'):
            db.create_all()
            print("تم إنشاء جميع الجداول")
        
        # التحقق من وجود الأعمدة في جدول Settings
        columns = [col['name'] for col in inspector.get_columns('settings')] if inspector.has_table('settings') else []
        
        if 'allow_custom_teacher_name' not in columns:
            try:
                db.session.execute(text('ALTER TABLE settings ADD COLUMN allow_custom_teacher_name BOOLEAN DEFAULT 1'))
                db.session.commit()
                print("تم إضافة العمود allow_custom_teacher_name إلى جدول settings")
            except Exception as e:
                print(f"خطأ أثناء إضافة العمود allow_custom_teacher_name: {e}")
                db.session.rollback()
        
        # التحقق من وجود العمود user_id في جدول Parent
        parent_columns = [col['name'] for col in inspector.get_columns('parent')] if inspector.has_table('parent') else []
        if 'user_id' not in parent_columns:
            try:
                db.session.execute(text('ALTER TABLE parent ADD COLUMN user_id INTEGER'))
                db.session.commit()
                print("تم إضافة العمود user_id إلى جدول parent")
            except Exception as e:
                print(f"خطأ أثناء إضافة العمود user_id: {e}")
                db.session.rollback()
        
        # إنشاء جميع الجداول
        db.create_all()
        
        # إنشاء إعدادات افتراضية إذا لم تكن موجودة
        if not Settings.query.first():
            try:
                default_settings = Settings()
                db.session.add(default_settings)
                db.session.commit()
                print("تم إنشاء الإعدادات الافتراضية")
            except Exception as e:
                print(f"خطأ أثناء إنشاء الإعدادات الافتراضية: {e}")
                db.session.rollback()
        
        # إنشاء مستخدم مسؤول افتراضي إذا لم يكن موجوداً
        if not User.query.filter_by(role='admin').first():
            try:
                admin_user = User(
                    username='admin',
                    password=generate_password_hash('admin123'),
                    name='المسؤول',
                    role='admin'
                )
                db.session.add(admin_user)
                db.session.commit()
                print("تم إنشاء المستخدم المسؤول الافتراضي")
            except Exception as e:
                print(f"خطأ أثناء إنشاء المستخدم المسؤول: {e}")
                db.session.rollback()
    
    # تشغيل التطبيق على الـ IP العام
    app.run(debug=True, host='0.0.0.0', port=5000)
