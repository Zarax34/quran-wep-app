import os
import json
from flask import Flask
from flask_mail import Mail
from apscheduler.schedulers.background import BackgroundScheduler
from flask_migrate import Migrate
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
    # In a real app, we might want to do this lazily or in a service
    try:
        with open('quran_data.json', 'r') as f:
            app.quran_data = json.load(f)
            app.quran_data_map = {item['verse_key']: item for item in app.quran_data}
    except FileNotFoundError:
        app.quran_data = []
        app.quran_data_map = {}

    from app.routes import main_bp
    app.register_blueprint(main_bp)

    if not scheduler.running:
        scheduler.start()

    return app
