from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_migrate import Migrate
import logging
import os
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()
DB_NAME = "database.db"

logging.basicConfig(level=logging.INFO)


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'campuscart-secret-key-2025'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    bcrypt.init_app(app)

    from .models import Users, Carts, Notifications, Orders

    migrate = Migrate(app, db)

    # Import blueprints
    from .auth import auth
    from .routes.admin import admin
    from .routes.student import student
    from .routes.ssp import ssp

    # Register blueprints
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(student, url_prefix='/student')
    app.register_blueprint(ssp, url_prefix='/ssp')

    # Setup login manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return Users.query.get(int(id))

    # Create database and required directories
    with app.app_context():
        db.create_all()
        # Ensure uploads directory always exists (critical for Gunicorn/Render deployments)
        upload_folder = os.path.join(app.root_path, 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Create default admin user if it doesn't exist
        admin_email = 'admin@campuscart.com'
        if not Users.query.filter_by(email=admin_email).first():
            hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin_user = Users(
                name='Admin',
                email=admin_email,
                password=hashed_pw,
                role_id=3,
                is_verified=True
            )
            db.session.add(admin_user)
            db.session.commit()

    return app
