import os
import json
from flask import Flask, session
from flask_mail import Mail
from apscheduler.schedulers.background import BackgroundScheduler
from flask_migrate import Migrate
from datetime import datetime, timedelta
from app.config import Config
from app.extensions import db

mail = Mail()
migrate = Migrate()
scheduler = BackgroundScheduler()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Load Quran data
    try:
        with open('quran_data.json', 'r') as f:
            app.quran_data = json.load(f)
            app.quran_data_map = {item['verse_key']: item for item in app.quran_data}
    except FileNotFoundError:
        app.quran_data = []
        app.quran_data_map = {}

    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # Global Context Processor
    @app.context_processor
    def inject_globals():
        from app.models import Settings, Parent, Notification, Report, Attendance, Holiday

        try:
            settings = Settings.query.first() or Settings()
        except Exception:
            # Fallback if DB is not ready or accessible
            settings = Settings()
            settings.site_name = "Quran Center" # Default fallback
            settings.primary_color = "#D32F2F"
            settings.secondary_color = "#2E7D32"

        current_year = datetime.now().year
        unread_notifications = 0
        if 'user_id' in session and session.get('role') == 'parent':
            try:
                parent = Parent.query.filter_by(user_id=session['user_id']).first()
                if parent and parent.user_id:
                    unread_notifications = Notification.query.filter_by(user_id=parent.user_id, is_read=False).count()
            except Exception:
                pass

        def check_permission(feature):
            if session.get('role') == 'admin':
                return True
            try:
                import json
                perms = json.loads(settings.permissions or '{}')
            except:
                perms = {}
            return perms.get(feature, True)

        return dict(
            datetime=datetime, now=datetime.now, timedelta=timedelta,
            settings=settings, Report=Report, Attendance=Attendance,
            Holiday=Holiday, Parent=Parent, current_year=current_year,
            unread_notifications=unread_notifications,
            check_permission=check_permission
        )

    if not scheduler.running:
        scheduler.start()

    return app
