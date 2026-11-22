import os
from pathlib import Path
from flask import Flask, render_template
from flask_login import LoginManager

from config import config_by_name, Config
from models import db, User, Level, Category, Question
from services.mail_service import mail
from services.seed_data import seed_all_initial_data
from routes.auth import auth_bp
from routes.exam import exam_bp
from routes.admin import admin_bp

def create_app(config_name: str = None) -> Flask:
    """Application factory for English Practice Monolithic web app."""
    if not config_name:
        config_name = os.getenv("FLASK_ENV", "default")

    app = Flask(__name__)
    app_config = config_by_name.get(config_name, Config)
    app.config.from_object(app_config)

    # Ensure upload directory exists
    upload_path = Path(app.config["UPLOAD_FOLDER"])
    upload_path.mkdir(parents=True, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Vui lòng đăng nhập để sử dụng tính năng này."
    login_manager.login_message_category = "warning"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(exam_bp)
    app.register_blueprint(admin_bp)

    # Custom Jinja filters
    @app.template_filter("format_datetime")
    def format_datetime(value, format="%d/%m/%Y %H:%M"):
        if not value:
            return ""
        return value.strftime(format)

    @app.template_filter("score_badge")
    def score_badge(score):
        score_val = float(score) if score is not None else 0.0
        if score_val >= 85:
            return "bg-success"
        elif score_val >= 65:
            return "bg-primary"
        elif score_val >= 50:
            return "bg-warning text-dark"
        else:
            return "bg-danger"

    # Context processors to inject global data
    @app.context_processor
    def inject_global_data():
        return {
            "app_name": "EnglishPractice",
            "app_tagline": "Hệ thống Luyện thi Ngữ pháp Tiếng Anh Thông minh",
        }

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("home/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("home/500.html"), 500

    # CLI command: seed default admin, levels, categories and 30 sample questions
    @app.cli.command("init-db")
    def init_db_cli():
        """Initialize database tables and seed all required data."""
        with app.app_context():
            db.create_all()
            seed_all_initial_data()
            print("Database initialized and all sample data seeded successfully.")

    @app.cli.command("seed-data")
    def seed_data_cli():
        """Force-seed levels, categories, questions, and sample attempts."""
        with app.app_context():
            seed_all_initial_data()
            print("All initial sample data seeded successfully.")

    # Automatically ensure tables and sample questions exist on first request or startup
    with app.app_context():
        try:
            db.create_all()
            # If no questions in DB, seed all sample data immediately
            if Question.query.count() < 10:
                seed_all_initial_data()
        except Exception as ex:
            # Table might not exist yet during migration or initial config
            print(f"[Startup Notice] Auto-seed check: {ex}")

    return app


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        try:
            db.create_all()
            seed_all_initial_data()
        except Exception as ex:
            print(f"[Main Notice] Initial DB check: {ex}")
    
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
